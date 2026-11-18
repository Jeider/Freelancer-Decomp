"""Matched textured and clay relief inspection; operates only on the offline blend."""
import bpy,json,math,bmesh,os
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/base_interiors/rh_biz_01_base/bar/prototype_v1'
os.environ['OPTIX_CACHE_PATH']=str(ROOT/'out/base_interiors/tool_cache/optix')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'bismarck_bar_prototype.blend'))
scene=bpy.context.scene;scene.cycles.samples=32
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception:pass
data=json.loads((OUT/'scene_mesh.json').read_text());b=data['batches'][7]
def cv(p):return Vector((p[0],-p[2],p[1]))
target=np.array([.63,.11]);best=None
for t in np.array(b['vertices']).reshape(-1,3,b['stride']):
 uv=t[:,6:8]
 try:w=np.linalg.solve(np.vstack((uv.T,np.ones(3))),np.r_[target,1])
 except np.linalg.LinAlgError:continue
 if min(w)<-.001:continue
 area=np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))
 if best is None or area>best[0]:best=(area,w@t)
assert best is not None
p=best[1];center=cv(p[:3]);normal=cv(p[3:6]).normalized()
for obj in scene.objects:
 if obj.type!='MESH' or obj.get('native_batch')!=7:continue
 bm=bmesh.new();bm.from_mesh(obj.data)
 remove=[f for f in bm.faces if abs((f.calc_center_median()-center).dot(normal))>.14]
 bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(obj.data);bm.free();obj.data.update()
cam=scene.camera;cam.location=center+normal*1.8+Vector((.35,0,.18));cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(54)
clay=bpy.data.materials.new('Inspection clay');clay.diffuse_color=(.36,.4,.43,1);clay.use_nodes=True;clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.7
ld=bpy.data.lights.new('Inspection grazing light','AREA');ld.energy=40;ld.size=.5;ob=bpy.data.objects.new(ld.name,ld);bpy.context.collection.objects.link(ob);ob.location=center+normal*.8+Vector((.8,.5,.7));ob.rotation_euler=(center-ob.location).to_track_quat('-Z','Y').to_euler()
for light in scene.objects:
 if light.type=='LIGHT' and light!=ob:light.hide_render=True
scene.world.color=(.035,.035,.035)
indices=json.loads((OUT/'prototype_stats.json').read_text())['modified_batches']
for mode in ('before','after'):
 for ob in scene.objects:
  if ob.type!='MESH':continue
  if ob.get('native_batch')!=7:ob.hide_render=True;continue
  if ob.name.startswith('Relief_'):ob.hide_render=mode=='before'
  elif ob.get('native_batch') in indices:ob.hide_render=mode=='after'
 for style in ('texture','clay'):
  scene.view_layers[0].material_override=clay if style=='clay' else None
  scene.render.filepath=str(OUT/f'detail_{style}_{mode}.png');bpy.ops.render.render(write_still=True)
