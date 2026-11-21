"""Validate the saved integrated vest, source preservation and culling views."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step03 import TOP,OUT,PARENT,render,TRIM_RADIUS
from hassler_step02_check import mesh
configure('character_rounding')

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def topology(me):
    adj={};graph={}
    for f in me.polygons:
        for a,b in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]):
            adj.setdefault(tuple(sorted((a,b))),[]).append(f.index)
            graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    def components(graph):
        pending=set(graph);sizes=[]
        while pending:
            todo=[next(iter(pending))];seen=set()
            while todo:
                a=todo.pop()
                if a in seen:continue
                seen.add(a);todo.extend(graph[a]-seen)
            pending-=seen;sizes.append(len(seen))
        return sizes
    border={}
    for (a,b),fs in adj.items():
        if len(fs)==1:border.setdefault(a,set()).add(b);border.setdefault(b,set()).add(a)
    return {'connected_components':components(graph),'nonmanifold_edges':sum(len(fs)>2 for fs in adj.values()),
            'boundary_loops':components(border),'boundary_branch_vertices':sum(len(v)!=2 for v in border.values())}

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    old={ob.name:mesh(ob) for ob in bpy.data.objects if ob.type=='MESH'}
    rig=bpy.data.objects['RIG — native Rheinland']
    old_bones={b.name:(np.array(b.matrix_local),list(b['native_inverse_bind']),b.parent.name if b.parent else None) for b in rig.data.bones}
    base=bpy.data.objects['00 Native elite — original torso and sleeves'];uv=base.data.uv_layers[0]
    belt=[tuple(f.vertices) for f in base.data.polygons if f.material_index==1 and all(uv.data[li].uv.x<.2 for li in f.loop_indices) and all(-.02<base.data.vertices[i].co.z<.3 for i in f.vertices)]
    low=[tuple(f.vertices) for f in base.data.polygons if max(base.data.vertices[i].co.z for i in f.vertices)<=.195]
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    build=json.loads((OUT/'report.json').read_text(encoding='utf8'));assert sha(PARENT)==build['parent_sha256']
    for name in ('Hassler head — native unchanged','Left glove — native unchanged','Right glove — native unchanged'):
        now=mesh(bpy.data.objects[name]);previous=old[name]
        for key in ('points','uv'):assert np.array_equal(now[key],previous[key]),(name,key)
        for key in ('faces','weights'):assert now[key]==previous[key],(name,key)
    rig=bpy.data.objects['RIG — native Rheinland'];assert len(rig.data.bones)==28
    for b in rig.data.bones:
        matrix,bind,parent=old_bones[b.name]
        assert np.array_equal(np.array(b.matrix_local),matrix) and list(b['native_inverse_bind'])==bind
        assert (b.parent.name if b.parent else None)==parent
    base=bpy.data.objects['00 Native sleeves and lower body'];now=mesh(base);previous=old['00 Native elite — original torso and sleeves']
    assert np.array_equal(now['points'],previous['points']) and now['weights']==previous['weights']
    retained={tuple(f.vertices) for f in base.data.polygons};assert all(f in retained for f in belt+low)
    assert set(retained)<=set(tuple(f) for f in previous['faces'])
    garment=bpy.data.objects['10 Tunic-vest — continuous shell and collar'];topo=topology(garment.data)
    for name in ('10 Tunic-vest — continuous shell and collar','11 Red binding — continuous 3 mm seams',
                 '12 Inner shirt — torso and fitted black neck','13 Aiguillette — fitted to tunic volume'):
        ob=bpy.data.objects[name]
        limbs={g.index for g in ob.vertex_groups if g.name in ('LUpArm','RUpArm','LLowArm','RLowArm','LHand','RHand','LThigh','RThigh')}
        assert all(g.weight<1e-8 for v in ob.data.vertices for g in v.groups if g.group in limbs),('Clothing pulled by limb',name)
    assert len(topo['connected_components'])==1,topo
    assert topo['nonmanifold_edges']==0 and topo['boundary_branch_vertices']==0,topo
    assert len(topo['boundary_loops'])==4,topo
    front=[f.normal.y for f in garment.data.polygons if f.center.y>.12 and .27<f.center.z<.42]
    assert np.mean(front)>.7,'Vest normals are inward'
    join=set(garment['neckline_join_vertices']);assert len(join)>=40
    # All collar join vertices belong to both a grey collar face and a torso face.
    for i in join:
        mats={f.material_index for f in garment.data.polygons if i in f.vertices}
        assert 4 in mats and len(mats)>=2,(i,mats)
    scene=bpy.context.scene;scene.frame_set(1);parts={};max_bones=0;uv_zero={}
    for ob in bpy.data.collections['EDIT — native costume upper study'].objects:
        if ob.type!='MESH':continue
        for v in ob.data.vertices:
            weights=[g.weight for g in v.groups if g.weight>0]
            # Historical native unused logical vertices remain in the source mesh.
            assert abs(sum(weights)-1)<3e-6,(ob.name,v.index,sum(weights));max_bones=max(max_bones,len(weights))
        ob.data.calc_loop_triangles();layer=ob.data.uv_layers.active;zero=0
        for tri in ob.data.loop_triangles:
            a,b,c=[np.array(layer.data[i].uv) for i in tri.loops]
            zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        uv_zero[ob.name]=int(zero)
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
        assert all(np.isfinite(v.co).all() for v in me.vertices)
        parts[ob.name]={'vertices':len(me.vertices),'triangles':len(me.loop_triangles)};ev.to_mesh_clear()
    assert max_bones<=4
    assert all(count==0 for count in uv_zero.values()),uv_zero
    assert sum(p['vertices'] for p in parts.values())<65535
    for c in ('ARCHIVE — original references disabled','ARCHIVE — step 02 separate panels','REFERENCE ART — disabled'):
        assert bpy.data.collections[c].hide_render and bpy.data.collections[c].hide_viewport
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists()
    for relative in ('source_audit.json','source/dietrich/source_audit.json','source/scrote/source_audit.json'):
        audit=json.loads((TOP/relative).read_text(encoding='utf8'))
        for entry in audit['native'].values():assert sha(Path(entry['path']))==entry['sha256']
    trim=bpy.data.objects['11 Red binding — continuous 3 mm seams'];assert len(trim.data.vertices)%6==0
    rr=[]
    for i in range(0,len(trim.data.vertices),6):
        ring=np.array([v.co[:] for v in trim.data.vertices[i:i+6]]);rr.extend(np.linalg.norm(ring-ring.mean(0),axis=1))
    radius_error=max(abs(np.array(rr)-TRIM_RADIUS));assert radius_error<1e-7,radius_error
    # Standalone synthetic shoulder lift is a fitting view, not game validation.
    scene.frame_set(60);render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(1)
    mat=bpy.data.materials.new('Culling clay 03');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
    bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.37,.40,1)
    geo=n.new('ShaderNodeNewGeometry');trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2])
    l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);scene.view_layers[0].material_override=mat
    render(scene,'clay_front',(.5,1,.12));render(scene,'clay_back',(.5,-1,.12))
    scene.view_layers[0].material_override=None
    result={'reopened':True,'blend_sha256':sha(path),'parent_step_02_unchanged':True,
            'head_hands_and_28_fitted_bones_unchanged':True,'native_belt_faces_preserved':len(belt),
            'native_lower_faces_preserved':len(low),'retained_native_positions_weights_unchanged':True,
            'garment_topology':topo,'collar_stitch_vertices':len(join),'outward_front_normal_mean':float(np.mean(front)),
            'vest_and_lining_do_not_follow_limb_bones':True,
            'binding_diameter_m':TRIM_RADIUS*2,'binding_radius_error_m':float(radius_error),
            'max_influences':max_bones,'body_triangles_with_modifiers':sum(v['triangles'] for v in parts.values()),
            'parts':parts,'authored_uv_zero_area_triangles':uv_zero,'source_files_unchanged':True,
            'archive_hidden_in_saved_file':True,'actual_culling_previews':True,
            'game_installed':False,'game_animations_validated':False,'phase':'editable shape and garment-construction prototype'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
