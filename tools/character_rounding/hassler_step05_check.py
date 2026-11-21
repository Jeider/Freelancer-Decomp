"""Saved prototype checks: sewn sleeves, two cloth pieces, lining, UV and rig."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step05 import TOP,OUT,PARENT,GARMENT,render
from hassler_step03_check import topology
from hassler_step02_check import mesh
from hassler_step04_check import rig_snapshot
configure('character_rounding')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    keep=('Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged')
    old={n:mesh(bpy.data.objects[n]) for n in keep};bones=rig_snapshot()
    oldbase=bpy.data.objects['00 Native sleeves and lower body'];oldlower=mesh(oldbase);uv=oldbase.data.uv_layers.active
    belt=[tuple(f.vertices) for f in oldbase.data.polygons if f.material_index==1 and all(uv.data[li].uv.x<.2 for li in f.loop_indices) and all(-.02<oldbase.data.vertices[i].co.z<.3 for i in f.vertices)]
    lower=[tuple(f.vertices) for f in oldbase.data.polygons if max(oldbase.data.vertices[i].co.z for i in f.vertices)<-.04]
    limbs={g.index for g in oldbase.vertex_groups if g.name in ('LUpArm','RUpArm','LLowArm','RLowArm','LHand','RHand')}
    cuffs=[]
    for f in oldbase.data.polygons:
        if f.material_index!=3:continue
        score=sum(g.weight for i in f.vertices for g in oldbase.data.vertices[i].groups if g.group in limbs)/len(f.vertices)
        if score<.01:continue
        cuffs.append(([oldbase.data.vertices[i].co[:] for i in f.vertices],[uv.data[li].uv[:] for li in f.loop_indices]))
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    build=json.loads((OUT/'report.json').read_text(encoding='utf8'));assert sha(PARENT)==build['parent_sha256']
    for name in keep:
        now=mesh(bpy.data.objects[name])
        for k in ('points','uv'):assert np.array_equal(now[k],old[name][k]),(name,k)
        for k in ('faces','weights'):assert now[k]==old[name][k],(name,k)
    now=rig_snapshot();assert len(now)==28 and set(now)==set(bones)
    for name,(matrix,bind,parent) in now.items():
        assert np.array_equal(matrix,bones[name][0]) and bind==bones[name][1] and parent==bones[name][2]
    base=bpy.data.objects['00 Native lower body and belt'];current=mesh(base)
    assert np.array_equal(current['points'],oldlower['points']) and current['weights']==oldlower['weights']
    retained={tuple(f.vertices) for f in base.data.polygons}
    assert all(f in retained for f in belt+lower),(len(belt),len(lower))
    garment=bpy.data.objects[GARMENT];me=garment.data;topo=topology(me)
    assert me.has_custom_normals and build['native_sleeve_normals_transferred_vertices']>100
    assert len(topo['connected_components'])==1 and topo['nonmanifold_edges']==0,topo
    assert topo['boundary_branch_vertices']==0 and len(topo['boundary_loops'])==2,topo
    adjacent={}
    for f in me.polygons:
        ids=list(f.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):adjacent[tuple(sorted((a,b)))]=adjacent.get(tuple(sorted((a,b))),0)+1
    for sleeve in build['sleeves']:
        for key in ('shoulder_stitch_vertices','native_forearm_stitch_vertices'):
            ids=sleeve[key]
            for a,b in zip(ids,ids[1:]+ids[:1]):assert adjacent.get(tuple(sorted((a,b))))==2,(key,a,b)
    flap=build['flap'];collar=build['collar']
    flapverts={v for i in flap['faces'] for v in me.polygons[i].vertices}
    collarverts={v for i in collar['faces'] for v in me.polygons[i].vertices}
    assert not flapverts&collarverts,'Grey collar and chest flap still joined directly'
    assert all(me.polygons[i].material_index==1 for i in flap['faces'])
    assert all(me.polygons[i].material_index==4 for i in collar['faces'])
    offset=build['reverse_material_offset'];solid=next(m for m in garment.modifiers if m.type=='SOLIDIFY')
    assert solid.material_offset==offset and me.materials[1+offset]==me.materials[3]
    turned_normal=float(np.mean([me.polygons[i].normal.y for i in flap['red_faces']]))
    assert turned_normal<-.4,turned_normal
    assert collar['wearer_right_tip'][2]>max(me.vertices[i].co.z for i in flap['free_edge_vertices'])+.015
    # Bracer source triangles retain positions, material and loop UVs after
    # welding the original lower sleeves into the coat object.
    kd=KDTree(len(me.vertices))
    for v in me.vertices:kd.insert(v.co,v.index)
    kd.balance();native_faces={tuple(sorted(f.vertices)):f for f in me.polygons if f.material_index==10}
    max_cuff_error=0
    for points,uvs in cuffs:
        ids=[]
        for p in points:
            co,i,dist=kd.find(Vector(p));assert dist<1e-6,dist;max_cuff_error=max(max_cuff_error,dist);ids.append(i)
        f=native_faces[tuple(sorted(ids))]
        byvertex={me.loops[li].vertex_index:np.array(me.uv_layers.active.data[li].uv) for li in f.loop_indices}
        for i,q in zip(ids,uvs):assert np.max(abs(byvertex[i]-q))<1e-6
    under=next(o for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.name.startswith('15 '))
    under_tree=BVHTree.FromPolygons([v.co[:] for v in under.data.vertices],[list(f.vertices) for f in under.data.polygons])
    distances=[]
    for i in flap['red_faces']:
        p=me.polygons[i].center;hit,no,ti,dist=under_tree.ray_cast(Vector((p.x,.5,p.z)),Vector((0,-1,0)))
        if hit is not None:distances.append(float(p.y-hit.y))
    assert len(distances)>=10 and min(distances)>.005,distances
    scene=bpy.context.scene;scene.frame_set(1);edit=bpy.data.collections['EDIT — native costume upper study'];parts={};uvzero={};max_bones=0
    for ob in edit.objects:
        if ob.type!='MESH':continue
        for v in ob.data.vertices:
            ww=[g.weight for g in v.groups if g.weight>0]
            assert abs(sum(ww)-1)<3e-6,(ob.name,v.index,sum(ww));max_bones=max(max_bones,len(ww))
        ob.data.calc_loop_triangles();uv=ob.data.uv_layers.active;zero=0
        for tri in ob.data.loop_triangles:
            a,b,c=[np.array(uv.data[i].uv) for i in tri.loops]
            zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        uvzero[ob.name]=int(zero)
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());mm=ev.to_mesh();mm.calc_loop_triangles()
        assert all(np.isfinite(v.co).all() for v in mm.vertices)
        parts[ob.name]={'vertices':len(mm.vertices),'triangles':len(mm.loop_triangles)};ev.to_mesh_clear()
    assert max_bones<=4 and sum(p['vertices'] for p in parts.values())<65535
    assert not any(uvzero.values()),uvzero
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE ART')):assert col.hide_render and col.hide_viewport,col.name
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists()
    for relative in ('source_audit.json','source/dietrich/source_audit.json','source/scrote/source_audit.json'):
        audit=json.loads((TOP/relative).read_text(encoding='utf8'))
        for item in audit['native'].values():assert sha(Path(item['path']))==item['sha256']
    scene.frame_set(60);render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(30);render(scene,'elbow_pose',(.65,1,.12));scene.frame_set(1)
    mat=bpy.data.materials.new('Culling clay 05');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
    bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.37,.40,1)
    geo=n.new('ShaderNodeNewGeometry');trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    scene.view_layers[0].material_override=mat
    render(scene,'clay_front',(.5,1,.12));render(scene,'clay_fold',(.9,1,.12),(.025,.07,1.50),.50)
    scene.view_layers[0].material_override=None
    result={'reopened':True,'blend_sha256':sha(path),'parent_step_04_unchanged':True,
            'head_hands_and_28_bones_unchanged':True,'native_belt_faces_preserved':len(belt),'native_lower_faces_preserved':len(lower),
            'native_cuff_faces_positions_uv_preserved':len(cuffs),'cuff_position_rounding_error_m':max_cuff_error,
            'garment_topology':topo,'closed_shoulder_and_forearm_stitches':[len(s['shoulder_stitch_vertices']) for s in build['sleeves']],
            'native_sleeve_shading_transferred_vertices':build['native_sleeve_normals_transferred_vertices'],
            'collar_and_gold_flap_have_distinct_free_edges_and_no_shared_vertices':True,
            'gold_front_red_reverse_material_verified':True,'turned_flap_normal_y':turned_normal,
            'red_underlap_clearance_m':{'samples':len(distances),'min':min(distances),'max':max(distances)},
            'max_influences':max_bones,'body_triangles_with_modifiers':sum(v['triangles'] for v in parts.values()),
            'parts':parts,'authored_uv_zero_area_triangles':uvzero,'archive_hidden_in_saved_file':True,
            'source_files_unchanged':True,'actual_culling_previews':True,'game_installed':False,'game_animations_validated':False}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
