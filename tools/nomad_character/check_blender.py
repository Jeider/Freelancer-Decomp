import bpy,json,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
OUT=Path(__file__).resolve().parents[2]/'out/nomad_character'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'nomad_robot_prototype.blend'))
rig=bpy.data.objects['RIG - robot_body_a'];source=json.loads((OUT/'robot_skeleton.json').read_text())
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
assert len(rig.data.bones)==len(source['bones'])==30
for bone in source['bones']:
 actual=rig.data.bones[bone['name']]
 assert (actual.head_local-(C@Vector(bone['position'])+Vector((0,0,.9762919)))).length<1e-5
 assert (actual.parent.name if actual.parent else None)==bone['parent']
objects=[ob for ob in bpy.data.objects if ob.type=='MESH']
for ob in objects:
 assert any(m.type=='ARMATURE' and m.object==rig for m in ob.modifiers)
 for v in ob.data.vertices:
  assert all(math.isfinite(x) for x in v.co)
  assert abs(sum(g.weight for g in v.groups)-1)<1e-6
for name,angle in [('LLowArm',-.5),('RLowArm',-.35),('Body_Head',.18),('LLowLeg',.18)]:
 bone=rig.pose.bones[name];axis=bone.matrix.to_3x3().inverted()@Vector((1,0,0))
 bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion(axis,angle)
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
for ob in objects:
 evaluated=ob.evaluated_get(deps);me=evaluated.to_mesh()
 assert all(all(math.isfinite(x) for x in v.co) for v in me.vertices)
 evaluated.to_mesh_clear()
bpy.context.scene.render.filepath=str(OUT/'joint_test.png');bpy.ops.render.render(write_still=True)
for bone in rig.pose.bones:bone.matrix_basis.identity()
bpy.context.view_layer.update()
# Keep the supplied artwork in the Blender file, for further modelling.
refs=bpy.data.collections.new('REFERENCES - toggle viewport to show');bpy.context.scene.collection.children.link(refs)
for i in range(13,20):
 path=Path('H:/FL/EXP/VIDEO_EXP/NO')/('n%d.JPG'%i)
 if not path.exists():continue
 image=bpy.data.images.load(str(path));image.pack()
 ob=bpy.data.objects.new('Art n%d'%i,None);refs.objects.link(ob);ob.empty_display_type='IMAGE';ob.data=image
 ob.empty_display_size=2;ob.location=(2.5+(i-13)*1.8,0,1);ob.rotation_euler=(math.pi/2,0,0);ob.hide_render=True
refs.hide_viewport=True;refs.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'nomad_robot_prototype.blend'))
report=dict(native_joint_positions_verified=True,native_hierarchy_verified=True,weights_normalized=True,finite_geometry_in_test_pose=True,game_animation_tested=False,organic_weight_blending_complete=False)
(OUT/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
