"""Reopen the drawn tunic opening, verify sides, hinges and retained rig."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step07 import TOP,OUT,PARENT,BASE,GARMENT,LINING,render
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
    previous={n:mesh(bpy.data.objects[n]) for n in keep};bones=rig_snapshot()
    old=mesh(bpy.data.objects[OLD_GARMENT]);oldme=bpy.data.objects[OLD_GARMENT].data;oldnormals={};oldmats=[f.material_index for f in oldme.polygons];olduv=[]
    for f in oldme.polygons:olduv.append({oldme.loops[i].vertex_index:np.array(oldme.uv_layers.active.data[i].uv) for i in f.loop_indices})
    for l,n in zip(oldme.loops,oldme.corner_normals):oldnormals.setdefault(l.vertex_index,np.array(n.vector))
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    build=json.loads((OUT/'report.json').read_text(encoding='utf8'))
    assert sha(PARENT)==build['parent_sha256'] and sha(BASE)==build['geometry_base_sha256']
    for name in keep:
        now=mesh(bpy.data.objects[name])
        for k in ('points','uv'):assert np.array_equal(now[k],previous[name][k]),(name,k)
        for k in ('faces','weights'):assert now[k]==previous[name][k],(name,k)
    now=rig_snapshot();assert len(now)==28 and set(now)==set(bones)
    for n,(m,b,p) in now.items():assert np.array_equal(m,bones[n][0]) and b==bones[n][1] and p==bones[n][2]
    ob=bpy.data.objects[GARMENT];me=ob.data;data=mesh(ob);kept=build['cut']['retained_base_faces']
    for dst,src in kept:
        f=me.polygons[dst];assert set(f.vertices)==set(old['faces'][src]) and f.material_index==oldmats[src]
        uv={me.loops[i].vertex_index:np.array(me.uv_layers.active.data[i].uv) for i in f.loop_indices}
        assert all(np.array_equal(uv[i],q) for i,q in olduv[src].items()),src
        for i in f.vertices:
            assert np.array_equal(data['points'][i],old['points'][i]),i
            assert all(abs(a[1]-b[1])<2e-7 and a[0]==b[0] for a,b in zip(data['weights'][i],old['weights'][i])),i
    err=[]
    for l,n in zip(me.loops,me.corner_normals):
        i=l.vertex_index
        if i in oldnormals and abs(me.vertices[i].co.x)>.19:err.append(float(np.linalg.norm(np.array(n.vector)-oldnormals[i])))
    assert max(err)<.002,max(err)
    topo=topology(me);print('TOPOLOGY',topo,flush=True)
    assert len(topo['connected_components'])==1 and topo['nonmanifold_edges']==0 and topo['boundary_branch_vertices']==0,topo
    edges={}
    for f in me.polygons:
        ids=list(f.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):edges.setdefault(tuple(sorted((a,b))),[]).append(f.index)
    for sleeve in build['sleeves']:
        for key in ('shoulder_stitch_vertices','native_forearm_stitch_vertices'):
            ids=sleeve[key]
            for a,b in zip(ids,ids[1:]+ids[:1]):assert len(edges[tuple(sorted((a,b)))])==2
    flap=build['flap'];ff=set(flap['faces']);cf=set(build['cut']['collar_faces']);hinge=flap['hinge_vertices']
    fv={v for i in ff for v in me.polygons[i].vertices};cv={v for i in cf for v in me.polygons[i].vertices}
    assert not fv&cv,('Flap wrongly attached to collar',fv&cv)
    for a,b in zip(hinge,hinge[1:]):
        fs=edges[tuple(sorted((a,b)))];assert len(fs)==2 and len(ff&set(fs))==1,(a,b,fs)
    assert all(me.polygons[i].material_index==1 for i in ff)
    count=build['reverse_material_offset'];solid=next(m for m in ob.modifiers if m.type=='SOLIDIFY')
    assert solid.material_offset==count and me.materials[1+count]==me.materials[3]
    normal_y=float(np.mean([me.polygons[i].normal.y for i in flap['red_reverse_faces']]));assert normal_y<-.3,normal_y
    low=min(me.vertices[i].co.z for i in flap['free_edge_vertices']);assert .34<low<.37,low
    # First-hit material checks include the solidified reverse and other body
    # layers; they test visibility, not merely the assigned source materials.
    scene=bpy.context.scene;scene.frame_set(1);edit=bpy.data.collections['EDIT — native costume upper study'];deps=bpy.context.evaluated_depsgraph_get()
    trees=[]
    for o in edit.objects:
        if o.type!='MESH':continue
        ev=o.evaluated_get(deps);m=ev.to_mesh();m.calc_loop_triangles()
        trees.append((o.name,BVHTree.FromPolygons([v.co[:] for v in m.vertices],[list(t.vertices) for t in m.loop_triangles],all_triangles=True),
                      [m.materials[t.material_index].name for t in m.loop_triangles]))
        ev.to_mesh_clear()
    rays=[]
    for label,x,z,expected in [('black throat',0,.53,'black inner shirt'),('black open chest',.035,.495,'black inner shirt'),
                                ('upper red cloth',.12,.49,'red cloth'),('hanging red reverse',.085,.38,'red cloth'),('gold lower facing',.04,.32,'front brocade')]:
        hits=[]
        for name,tree,mats in trees:
            p,n,i,d=tree.ray_cast(Vector((x,.7,z)),Vector((0,-1,0)))
            if p is not None:hits.append((d,name,mats[i],list(p)))
        hit=min(hits);assert expected in hit[2],(label,hit)
        rays.append({'region':label,'object':hit[1],'material':hit[2],'point':hit[3]})
    # Look outward from the air gap between chest and flap: the opposite
    # visible surface must be actual gold, not another red double-sided face.
    _,tree,mats=next(t for t in trees if t[0]==GARMENT)
    p,n,i,d=tree.ray_cast(Vector((.085,.20,.38)),Vector((0,1,0)))
    assert p is not None and 'front brocade' in mats[i],(p,mats[i] if i is not None else None)
    rays.append({'region':'gold reverse viewed from air gap','object':GARMENT,'material':mats[i],'point':list(p)})
    parts={};uvzero={};influences=0
    for o in edit.objects:
        if o.type!='MESH':continue
        for v in o.data.vertices:
            w=[g.weight for g in v.groups if g.weight>0];assert abs(sum(w)-1)<3e-6,(o.name,v.index,sum(w));influences=max(influences,len(w))
        o.data.calc_loop_triangles();uv=o.data.uv_layers.active;zero=0
        for t in o.data.loop_triangles:
            a,b,c=[np.array(uv.data[i].uv) for i in t.loops]
            zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        uvzero[o.name]=int(zero)
        ev=o.evaluated_get(deps);m=ev.to_mesh();m.calc_loop_triangles();assert all(np.isfinite(v.co).all() for v in m.vertices)
        parts[o.name]={'vertices':len(m.vertices),'triangles':len(m.loop_triangles)};ev.to_mesh_clear()
    print('UV',uvzero,flush=True)
    assert not any(uvzero.values()),uvzero
    assert influences<=4 and sum(p['vertices'] for p in parts.values())<65535
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE')):assert col.hide_render and col.hide_viewport,col.name
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists()
    result={'reopened':True,'blend_sha256':sha(path),'parent_06_and_base_05_unchanged':True,
            'head_hands_rig_lower_body_epaulettes_cord_black_shirt_unchanged':True,'retained_base_faces_uv_materials':len(kept),
            'sleeve_normal_max_error':max(err),'sleeve_stitches_closed':True,'garment_topology':topo,
            'gold_facing_hinge_edges':len(hinge)-1,'flap_collar_shared_vertices':0,'gold_front_red_reverse_verified':True,
            'reverse_normal_y':normal_y,'lowest_free_edge_local_z':low,'visible_material_rays':rays,
            'max_skin_influences':influences,'uv_zero_area_triangles':uvzero,'parts':parts,
            'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),
            'archive_hidden_viewport_and_render':True,'game_installed':False,'game_animations_validated':False}
    if '--no-render' not in sys.argv:
        scene.frame_set(60);render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(30);render(scene,'elbow_pose',(.65,1,.12));scene.frame_set(1)
        mat=bpy.data.materials.new('Culling clay 07');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
        bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.37,.40,1)
        geo=n.new('ShaderNodeNewGeometry');trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
        l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
        scene.view_layers[0].material_override=mat;render(scene,'clay_fold',(.35,1,.18),(.065,.02,1.45),.5);scene.view_layers[0].material_override=None
        result['preview_blend_sha256']=sha(path)
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
