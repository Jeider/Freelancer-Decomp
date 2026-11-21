"""Reopen the visual prototype and check the real fold, rig and culling."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step04 import TOP,OUT,PARENT,GARMENT,render
from hassler_step03_check import topology
from hassler_step02_check import mesh
configure('character_rounding')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rig_snapshot():
    return {b.name:(np.array(b.matrix_local),list(b['native_inverse_bind']),b.parent.name if b.parent else None)
            for b in bpy.data.objects['RIG — native Rheinland'].data.bones}

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    keep=('Hassler head — native unchanged','Left glove — native unchanged',
          'Right glove — native unchanged','00 Native sleeves and lower body')
    old={n:mesh(bpy.data.objects[n]) for n in keep};bones=rig_snapshot()
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    report=json.loads((OUT/'report.json').read_text(encoding='utf8'));assert sha(PARENT)==report['parent_sha256']
    for name in keep:
        now=mesh(bpy.data.objects[name])
        for key in ('points','uv'):assert np.array_equal(now[key],old[name][key]),(name,key)
        for key in ('faces','weights'):assert now[key]==old[name][key],(name,key)
    now=rig_snapshot();assert set(now)==set(bones) and len(now)==28
    for name,(matrix,bind,parent) in now.items():
        assert np.array_equal(matrix,bones[name][0]) and bind==bones[name][1] and parent==bones[name][2]
    garment=bpy.data.objects[GARMENT];me=garment.data;topo=topology(me)
    assert len(topo['connected_components'])==1 and topo['nonmanifold_edges']==0,topo
    assert topo['boundary_branch_vertices']==0 and len(topo['boundary_loops'])==4,topo
    front=[f.normal.y for f in me.polygons if f.center.y>.12 and .27<f.center.z<.42]
    assert np.mean(front)>.7
    fold=report['fold'];start=min(fold['red_faces'])-2
    bodyverts={v for f in me.polygons[:start] for v in f.vertices}
    foldedverts={v for f in me.polygons[start:] for v in f.vertices}
    shared=bodyverts&foldedverts
    assert set(garment['neckline_join_vertices'])==shared and len(shared)>=60
    red=set(fold['red_faces']);assert red and all(me.polygons[i].material_index==3 for i in red)
    assert not any(f.material_index==3 for f in me.polygons[:start]),'Red must not remain painted on closed chest'
    assert all(me.vertices[v].co.x>0 for i in red for v in me.polygons[i].vertices),'Opening changed sides'
    # Quantify the actual forward clearance, not simply the assigned red colour.
    tree=BVHTree.FromPolygons([v.co[:] for v in me.vertices],[list(f.vertices) for f in me.polygons[:start]])
    clearances=[]
    for i in red:
        p=me.polygons[i].center;hit,no,ti,dist=tree.ray_cast(Vector((p.x,1,p.z)),Vector((0,-1,0)))
        if hit is not None:clearances.append(float(p.y-hit.y))
    assert len(clearances)>=8 and min(clearances)>.002,(len(clearances),clearances)
    edit=bpy.data.collections['EDIT — native costume upper study'];scene=bpy.context.scene;scene.frame_set(1)
    parts={};uvzero={};max_bones=0
    for ob in edit.objects:
        if ob.type!='MESH':continue
        for v in ob.data.vertices:
            weights=[g.weight for g in v.groups if g.weight>0]
            assert abs(sum(weights)-1)<3e-6,(ob.name,v.index,sum(weights));max_bones=max(max_bones,len(weights))
        ob.data.calc_loop_triangles();layer=ob.data.uv_layers.active;zero=0
        for tri in ob.data.loop_triangles:
            a,b,c=[np.array(layer.data[i].uv) for i in tri.loops]
            zero+=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-11
        uvzero[ob.name]=int(zero)
        if ob.name.startswith(('10 ','11 ','12 ','13 ')):
            limbs={g.index for g in ob.vertex_groups if g.name in ('LUpArm','RUpArm','LLowArm','RLowArm','LHand','RHand','LThigh','RThigh')}
            assert all(g.weight<1e-8 for v in ob.data.vertices for g in v.groups if g.group in limbs),ob.name
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());evaluated=ev.to_mesh();evaluated.calc_loop_triangles()
        assert all(np.isfinite(v.co).all() for v in evaluated.vertices)
        parts[ob.name]={'vertices':len(evaluated.vertices),'triangles':len(evaluated.loop_triangles)};ev.to_mesh_clear()
    assert max_bones<=4 and sum(p['vertices'] for p in parts.values())<65535
    assert not any(uvzero.values()),uvzero
    ep=next(o for o in edit.objects if o.name.startswith('14 '))
    assert 'Dietrich' in ep.data.uv_layers.active.name
    assert max(v.co.x for v in ep.data.vertices)>.24 and min(v.co.x for v in ep.data.vertices)<-.24
    for col in bpy.data.collections:
        if col.name.startswith(('ARCHIVE','REFERENCE ART')):assert col.hide_render and col.hide_viewport,col.name
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists(),im.filepath
    for relative in ('source_audit.json','source/dietrich/source_audit.json','source/scrote/source_audit.json'):
        audit=json.loads((TOP/relative).read_text(encoding='utf8'))
        for item in audit['native'].values():assert sha(Path(item['path']))==item['sha256'],item['path']
    scene.frame_set(60);render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(1)
    mat=bpy.data.materials.new('Culling clay 04');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
    bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.37,.40,1)
    geo=n.new('ShaderNodeNewGeometry');trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2])
    l.new(mix.outputs[0],n.get('Material Output').inputs['Surface']);scene.view_layers[0].material_override=mat
    render(scene,'clay_front',(.5,1,.12));render(scene,'clay_back',(.5,-1,.12))
    render(scene,'clay_fold',(.9,1,.12),(.025,.07,1.50),.50)
    scene.view_layers[0].material_override=None
    result={'reopened':True,'blend_sha256':sha(path),'parent_step_03_unchanged':True,
            'head_hands_native_sleeves_lower_body_belt_and_28_bones_unchanged':True,
            'garment_topology':topo,'shared_tunic_fold_vertices':len(shared),
            'red_is_geometry_of_unbuttoned_right_front_not_external_patch':True,
            'red_fold_front_clearance_m':{'samples':len(clearances),'min':min(clearances),'max':max(clearances)},
            'projecting_epaulettes_with_dietrich_uv':True,'outward_front_normal_mean':float(np.mean(front)),
            'max_influences':max_bones,'body_triangles_with_modifiers':sum(v['triangles'] for v in parts.values()),
            'parts':parts,'authored_uv_zero_area_triangles':uvzero,'archive_hidden_in_saved_file':True,
            'source_files_unchanged':True,'actual_culling_previews':True,
            'game_installed':False,'game_animations_validated':False,'phase':'editable garment-construction prototype'}
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
