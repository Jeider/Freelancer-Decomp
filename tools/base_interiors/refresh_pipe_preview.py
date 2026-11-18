import bpy,json,ast,math,numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/base_interiors/rh_biz_01_base/bar/prototype_v5'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'bismarck_material_relief.blend'))
tree=ast.parse((ROOT/'tools/base_interiors/relief_v2.py').read_text());exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='placements'],type_ignores=[]),__file__,'exec'))
data=json.loads((OUT/'scene_mesh.json').read_text());batch=data['batches'][9];target=np.array([.42,.615]);center,basis,normal=max(placements(batch,target),key=lambda q:np.linalg.norm(q[1]));outline=np.array([[.27,.25],[.57,.25],[.57,.98],[.27,.98]])
size=np.linalg.norm((outline-target)@basis,axis=1).max()*2;pos=center+normal*size*1.5+basis[0]/np.linalg.norm(basis[0])*size*.42
def cv(p):return Vector((p[0],-p[2],p[1]))
scene=bpy.context.scene;cam=scene.camera;cam.location=cv(pos);cam.rotation_euler=(cv(center)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(56)
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception:pass
archive=bpy.data.collections.get('ARCHIVE - original replaced surfaces - disabled');archive.hide_render=False
clay=bpy.data.materials.get('Neutral relief inspection')
for mode in ('before','after'):
 for ob in scene.objects:
  if ob.type=='MESH':ob.hide_render=not (ob.get('native_batch')==9 and mode=='before' or ob.name=='r_bar_05_contour_relief' and mode=='after')
 for style in ('texture','clay'):
  scene.view_layers[0].material_override=clay if style=='clay' else None;scene.render.filepath=str(OUT/f'r_bar_05_{style}_{mode}.png');bpy.ops.render.render(write_still=True)
