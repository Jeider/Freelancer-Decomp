"""Verify/reopen step 01 and make small native/clay comparisons."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).parent))
from blender_workspace import configure
import hassler_build as native
from hassler_native_upper import OUT,TOP
configure('character_rounding')

def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    scene=bpy.context.scene;scene.frame_set(1);data=native.load('body');rig=bpy.data.objects['RIG — native Rheinland']
    assert len(rig.data.bones)==28
    for b in data['bones']:
        assert np.array_equal(np.asarray(rig.data.bones[b['name']]['native_inverse_bind']),b['native_bind'])
        parent=rig.data.bones[b['name']].parent;assert (parent.name if parent else None)==b['parent']
    base=bpy.data.objects['00 Native elite — original torso and sleeves'];mapping=list(base['native_vertex_map'])
    ps=np.array([native.C@Vector(data['points'][i]) for i in mapping]);actual=np.array([v.co[:] for v in base.data.vertices])
    assert np.max(abs(ps-actual))<1e-7
    for v,i in zip(base.data.vertices,mapping):
        actual_weights={str(g.group):g.weight for g in v.groups};wanted=data['skin'][i]
        assert actual_weights.keys()==wanted.keys()
        assert all(abs(actual_weights[k]-wanted[k])<1e-7 for k in wanted)
    retained={tuple(mapping[i] for i in f.vertices) for f in base.data.polygons}
    low=[tuple(t) for g in data['groups'] for t in g['faces'] if max(data['points'][i][1] for i in t)<=.18]
    assert all(t in retained for t in low)
    for kind,hp,name in [('head','hp_head','Hassler head — native unchanged'),('left_hand','hp_left b','Left glove — native unchanged'),('right_hand','hp_right b','Right glove — native unchanged')]:
        d=native.load(kind);ob=bpy.data.objects[name];transform=native.C4@Matrix((np.array(data['hardpoints'][hp]['matrix'])@np.linalg.inv(np.array(d['hardpoints'][hp]['matrix']))).tolist())
        assert np.max(abs(np.array([transform@Vector(p) for p in d['points']])-np.array([v.co[:] for v in ob.data.vertices])))<1e-6
    ep=native.load('epaulettes');ob=bpy.data.objects['02 Epaulettes — Reichman source geometry'];em=list(ob['native_vertex_map'])
    wanted=np.array([native.C@Vector(ep['points'][i]) for i in em]);wanted[:,0]+=np.where(wanted[:,0]>0,.012,-.012);wanted[:,2]+=.015
    assert np.max(abs(wanted-np.array([v.co[:] for v in ob.data.vertices])))<1e-7
    assert all(np.linalg.norm(np.array(ob.data.uv_layers[0].data[l.index].uv)-ep['uv'][em[l.vertex_index]])<1e-7 for l in ob.data.loops)
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=bpy.data.collections['ARCHIVE — original references disabled']
    assert archive.hide_render and archive.hide_viewport
    parts={};max_influences=0
    for ob in edit.objects:
        if ob.type!='MESH':continue
        for v in ob.data.vertices:
            weights=[g.weight for g in v.groups if g.weight>0];max_influences=max(max_influences,len(weights));assert abs(sum(weights)-1)<2e-6
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
        assert all(np.isfinite(v.co).all() for v in me.vertices);parts[ob.name]={'evaluated_triangles':len(me.loop_triangles),'vertices':len(me.vertices)};ev.to_mesh_clear()
    assert max_influences<=4,max_influences
    for im in bpy.data.images:
        if im.source=='FILE' and im.users and not im.packed_file:assert Path(bpy.path.abspath(im.filepath)).exists(),im.filepath
    audit=json.loads((TOP/'source_audit.json').read_text())
    for info in list(audit['native'].values())+list(audit['user_inputs'].values()):assert digest(Path(info['path']))==info['sha256']
    cam=scene.camera;d=Vector((0,1,0));cam.location=Vector((0,0,1.47))+d*4;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.02
    edit.hide_render=True;archive.hide_render=False;archive.hide_viewport=False
    for ob in archive.objects:ob.hide_render=ob.name!='Original rh_male_elite body'
    scene.render.filepath=str(OUT/'native_before.png');bpy.ops.render.render(write_still=True)
    edit.hide_render=False;archive.hide_render=archive.hide_viewport=True
    # Actual back-face rejection for a geometry-only review.
    mat=bpy.data.materials.new('Culling clay');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
    bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.37,.40,1)
    geo=n.new('ShaderNodeNewGeometry');transparent=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(transparent.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    scene.view_layers[0].material_override=mat
    for label,direction in [('clay_front',(.5,1,.15)),('clay_back',(.5,-1,.15))]:
        d=Vector(direction).normalized();cam.location=Vector((0,0,1.47))+d*4;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override=None
    report={'reopened':True,'blend_sha256':digest(path),'native_skeleton_preserved':True,'base_vertices_weights_unchanged':True,
            'native_lower_faces_unchanged':len(low),'native_head_hands_unchanged':True,'epaulettes_source_verified':True,
            'max_influences':max_influences,'body_triangles_with_modifiers':sum(p['evaluated_triangles'] for p in parts.values()),'objects':parts,
            'archive_hidden_in_saved_file':True,'source_files_unchanged':True,'actual_backface_culling_previews':True,
            'game_installed':False,'game_animations_validated':False,'visual_stage_only':True}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');assert digest(path)==report['blend_sha256']
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
