"""Reopen the delivered scene and verify viewport/render replacement consistency."""
import bpy,json,sys
from pathlib import Path
VERSION=sys.argv[sys.argv.index('--output-version')+1] if '--output-version' in sys.argv else 'prototype_v4'
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/base_interiors/rh_biz_01_base/bar'/VERSION
bpy.ops.wm.open_mainfile(filepath=str(OUT/'bismarck_material_relief.blend'))
stats=json.loads((OUT/'prototype_stats.json').read_text());replaced=set(stats['changed_batches'])
archive=bpy.data.collections.get('ARCHIVE - original replaced surfaces - disabled')
assert archive and archive.hide_render and archive.hide_viewport
assert len(archive.objects)==len(replaced)
for ob in archive.objects:assert ob.hide_render and not ob.visible_get(),ob.name
active=[ob for ob in bpy.context.scene.objects if ob.type=='MESH' and ob.visible_get()]
for name in stats['material_triangles']:
 matches=[ob for ob in active if ob.name==name+'_contour_relief']
 assert len(matches)==1,name
 assert not matches[0].hide_render
for ob in active:assert ob.get('native_batch') not in replaced,ob.name
report={'saved_scene_reopened':True,'archived_originals':len(archive.objects),'all_replaced_originals_disabled_in_viewport_and_render':True,'one_active_replacement_per_material':True}
(OUT/'saved_scene_validation.json').write_text(json.dumps(report,indent=2))
if VERSION=='prototype_v8':
 import numpy as np
 data=json.loads((OUT/'scene_mesh.json').read_text());registration={}
 for index,name in ((13,'r_bar_09'),(17,'r_bar_15')):
  batch=data['batches'][index];tris=np.array(batch['vertices']).reshape(-1,3,batch['stride']);tris=tris[np.max(abs(tris[:,:,0]-11.76827),axis=1)<.025]
  mesh=bpy.data.objects[name+'_contour_relief'].data;uv=mesh.uv_layers.active.data;errors=[]
  for loop in mesh.loops:
   p=mesh.vertices[loop.vertex_index].co
   if abs(p.x-11.76827)>.1:continue
   q=np.array([uv[loop.index].uv.x,1-uv[loop.index].uv.y]);native=np.array([p.x,p.z,-p.y]);dist=[]
   for t in tris:
    try:w=np.linalg.solve(np.vstack((t[:,6:8].T,np.ones(3))),np.r_[q,1])
    except np.linalg.LinAlgError:continue
    if min(w)<-1e-4:continue
    dist.append(float(np.linalg.norm((w@t[:,:3]-native)[1:])))
   if dist:errors.append(min(dist))
  assert len(errors)>100,(name,len(errors))
  assert max(errors)<.0002,(name,max(errors))
  registration[name]={'tested_corners':len(errors),'max_tangential_error_world_units':max(errors)}
 (OUT/'uv_registration_validation.json').write_text(json.dumps(registration,indent=2))
scene=bpy.context.scene;scene.render.engine='BLENDER_WORKBENCH';scene.display.shading.light='STUDIO';scene.display.shading.color_type='SINGLE';scene.display.shading.single_color=(.55,.55,.55);scene.render.filepath=str(OUT/'viewport_solid.png');bpy.ops.render.render(write_still=True)
print('Saved scene viewport visibility checks passed.')
from mathutils import Vector
import math
scene.render.engine='CYCLES';scene.cycles.samples=24
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception:pass
cam=scene.camera;cam.location=(1,18,6);cam.rotation_euler=(Vector((1,4.85,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(72)
for mode in ('before','after'):
 archive.hide_render=mode=='after'
 for ob in archive.objects:ob.hide_render=mode=='after'
 for ob in active:
  if ob.name.endswith('_contour_relief'):ob.hide_render=mode=='before'
 scene.render.filepath=str(OUT/(mode+'_seating_fascia.png'));bpy.ops.render.render(write_still=True)
# Do not save the temporary comparison visibility state over the verified blend.
if VERSION in ('prototype_v6','prototype_v7','prototype_v8'):
 import bmesh
 # Isolate the architectural wall plane; foreground canopy parts otherwise occlude it.
 for ob in scene.objects:
  if ob.type!='MESH':continue
  bm=bmesh.new();bm.from_mesh(ob.data)
  remove=[f for f in bm.faces if not 11.48<f.calc_center_median().x<12.06]
  bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(ob.data);bm.free();ob.data.update()
 cam.location=(-2,1.5,7);cam.rotation_euler=(Vector((11.77,1.5,7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(68)
 light=bpy.data.lights.new('Wall inspection soft light','AREA');light.energy=700;light.size=5
 ob=bpy.data.objects.new(light.name,light);scene.collection.objects.link(ob);ob.location=(5,-3,10);ob.rotation_euler=(Vector((11.77,1.5,7))-ob.location).to_track_quat('-Z','Y').to_euler()
 for mode in ('before','after'):
  archive.hide_render=mode=='after'
  for ob in archive.objects:ob.hide_render=mode=='after'
  for ob in active:
   if ob.name.endswith('_contour_relief'):ob.hide_render=mode=='before'
  scene.view_layers[0].material_override=None;scene.render.filepath=str(OUT/(mode+'_arch_wall.png'));bpy.ops.render.render(write_still=True)
 clay=bpy.data.materials.new('Wall inspection clay');clay.use_nodes=True;clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.3,.34,.38,1);clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.75
 for mode in ('before','after'):
  archive.hide_render=mode=='after'
  for ob in archive.objects:ob.hide_render=mode=='after'
  for ob in active:
   if ob.name.endswith('_contour_relief'):ob.hide_render=mode=='before'
  scene.view_layers[0].material_override=clay;scene.render.filepath=str(OUT/(mode+'_arch_clay.png'));bpy.ops.render.render(write_still=True)
