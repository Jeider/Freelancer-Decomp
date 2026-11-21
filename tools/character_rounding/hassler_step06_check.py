"""Reopen and verify left-collar/front continuity and preservation of step 05."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step06 import TOP,OUT,PARENT,GARMENT,render
from hassler_native_step05 import GARMENT as OLD_GARMENT
from hassler_step02_check import mesh
from hassler_step03_check import topology
from hassler_step04_check import rig_snapshot
configure('character_rounding')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    keep=['Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged']
    keep += [o.name for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.name.startswith(('00 ','12 ','13 ','14 '))]
    previous={n:mesh(bpy.data.objects[n]) for n in keep};old=mesh(bpy.data.objects[OLD_GARMENT]);bones=rig_snapshot()
    oldme=bpy.data.objects[OLD_GARMENT].data;oldnormals={};oldmats=[f.material_index for f in oldme.polygons];olduv=[]
    for f in oldme.polygons:olduv.append({oldme.loops[i].vertex_index:np.array(oldme.uv_layers.active.data[i].uv) for i in f.loop_indices})
    for l,n in zip(oldme.loops,oldme.corner_normals):oldnormals.setdefault(l.vertex_index,np.array(n.vector))
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    build=json.loads((OUT/'report.json').read_text(encoding='utf8'));assert sha(PARENT)==build['parent_sha256']
    for name in keep:
        now=mesh(bpy.data.objects[name])
        for k in ('points','uv'):assert np.array_equal(now[k],previous[name][k]),(name,k)
        for k in ('faces','weights'):assert now[k]==previous[name][k],(name,k)
    now=rig_snapshot();assert set(now)==set(bones) and len(now)==28
    for name,(mat,bind,parent) in now.items():assert np.array_equal(mat,bones[name][0]) and bind==bones[name][1] and parent==bones[name][2]
    ob=bpy.data.objects[GARMENT];me=ob.data;data=mesh(ob);changed=set(build['lowered_front_neckline_vertices']);kept=build['retained_parent_face_indices']
    sourceverts={i for fi in kept for i in old['faces'][fi]};unchanged=sorted(sourceverts-changed)
    assert np.array_equal(data['points'][unchanged],old['points'][unchanged])
    for i in sourceverts:assert data['weights'][i]==old['weights'][i],i
    for dst,src in enumerate(kept):
        f=me.polygons[dst];assert set(f.vertices)==set(old['faces'][src]) and f.material_index==oldmats[src]
        uv={me.loops[i].vertex_index:np.array(me.uv_layers.active.data[i].uv) for i in f.loop_indices}
        assert all(np.array_equal(uv[i],q) for i,q in olduv[src].items()),src
    err=[];worst=[]
    for l,n in zip(me.loops,me.corner_normals):
        i=l.vertex_index
        if i in sourceverts and abs(me.vertices[i].co.x)>.17:
            error=float(np.linalg.norm(np.array(n.vector)-oldnormals[i]));err.append(error)
            if error>.002:worst.append((error,i,list(me.vertices[i].co),oldnormals[i].tolist(),list(n.vector)))
    if worst:print('NORMAL_DIFFERENCES',sorted(worst,reverse=True)[:8],flush=True)
    assert max(err)<.002,max(err)
    topo=topology(me);assert len(topo['connected_components'])==1 and topo['nonmanifold_edges']==0 and topo['boundary_branch_vertices']==0,topo
    assert len(topo['boundary_loops'])==2,topo
    edges={}
    for f in me.polygons:
        ids=list(f.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append(f.index)
    for sleeve in build['sleeves']:
        for key in ('shoulder_stitch_vertices','native_forearm_stitch_vertices'):
            ids=sleeve[key]
            for a,b in zip(ids,ids[1:]+ids[:1]):assert len(edges[tuple(sorted((a,b)))])==2
    seam=build['seam'];join=seam['left_collar_to_front_shared_section']
    grey=set(seam['collar_faces']);front=set(seam['front_faces'])
    gv={v for i in grey for v in me.polygons[i].vertices};fv={v for i in front for v in me.polygons[i].vertices}
    assert gv&fv==set(join) and len(join)==6,(len(gv&fv),join)
    for a,b in zip(join,join[1:]):
        fs=edges[tuple(sorted((a,b)))];assert len(fs)==2 and len(set(fs)&grey)==1 and len(set(fs)&front)==1
    assert all(me.polygons[i].material_index==4 for i in grey)
    assert all(me.polygons[i].material_index==1 for i in front)
    offset=build['reverse_material_offset'];solid=next(m for m in ob.modifiers if m.type=='SOLIDIFY')
    assert solid.material_offset==offset and me.materials[1+offset]==me.materials[3]
    normal_y=float(np.mean([me.polygons[i].normal.y for i in seam['red_reverse_faces']]));assert normal_y<-.3,normal_y
    released=np.array(seam['released_right_corner']);fixed=np.array(seam['fixed_right_fastening_reference'])
    assert released[0]>.15 and fixed[2]-released[2]>.04
    edit=bpy.data.collections['EDIT — native costume upper study'];shirt=next(o for o in edit.objects if o.name.startswith('12 '));under=next(o for o in edit.objects if o.name.startswith('15 '))
    shirt.data.calc_loop_triangles();tree=BVHTree.FromPolygons([v.co[:] for v in shirt.data.vertices],[list(t.vertices) for t in shirt.data.loop_triangles],all_triangles=True)
    clearance=[]
    for f in under.data.polygons:
        p=f.center;hit,no,idx,dist=tree.ray_cast(Vector((p.x,.5,p.z)),Vector((0,-1,0)))
        assert hit is not None;clearance.append(float(p.y-hit.y))
    assert max(abs(np.array(clearance)-.0025))<5e-6,(min(clearance),max(clearance))
    scene=bpy.context.scene;scene.frame_set(1);parts={};uvzero={};max_bones=0
    for o in edit.objects:
        if o.type!='MESH':continue
        for v in o.data.vertices:
            ww=[g.weight for g in v.groups if g.weight>0];assert abs(sum(ww)-1)<3e-6,(o.name,v.index,sum(ww));max_bones=max(max_bones,len(ww))
        o.data.calc_loop_triangles();uv=o.data.uv_layers.active;zero=0
        for t in o.data.loop_triangles:
            a,b,c=[np.array(uv.data[i].uv) for i in t.loops]
            zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        uvzero[o.name]=int(zero)
        ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles()
        assert all(np.isfinite(v.co).all() for v in m.vertices)
        parts[o.name]={'vertices':len(m.vertices),'triangles':len(m.loop_triangles)};ev.to_mesh_clear()
    assert max_bones<=4 and sum(p['vertices'] for p in parts.values())<65535
    assert not any(uvzero.values()),uvzero
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport,col.name
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists()
    scene.frame_set(60);render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(30);render(scene,'elbow_pose',(.65,1,.12));scene.frame_set(1)
    mat=bpy.data.materials.new('Culling clay 06');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
    bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.37,.40,1)
    geo=n.new('ShaderNodeNewGeometry');trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    scene.view_layers[0].material_override=mat;render(scene,'clay_fold',(.35,1,.18),(0,.02,1.53),.64);scene.view_layers[0].material_override=None
    result={'reopened':True,'blend_sha256':sha(path),'parent_step_05_unchanged':True,
            'head_hands_28_bones_lower_body_epaulettes_cord_inner_shirt_unchanged':True,
            'retained_parent_faces_uv_materials_weights':len(kept),'unchanged_parent_shell_vertices':len(unchanged),
            'sleeve_normal_max_error':max(err),'shoulder_and_forearm_stitches_closed':True,'garment_topology':topo,
            'left_collar_to_front_shared_vertices':len(join),'left_collar_to_front_shared_edges':len(join)-1,
            'right_free_corner_drop_from_authored_fastening_reference_m':float(fixed[2]-released[2]),
            'gold_front_red_reverse_verified':True,'front_reverse_normal_y':normal_y,
            'red_lining_clearance_from_shirt_m':{'samples':len(clearance),'min':min(clearance),'max':max(clearance)},
            'max_influences':max_bones,'authored_uv_zero_area_triangles':uvzero,
            'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'parts':parts,
            'archive_and_guides_hidden_in_saved_file':True,'actual_culling_previews':True,
            'game_installed':False,'game_animations_validated':False}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
