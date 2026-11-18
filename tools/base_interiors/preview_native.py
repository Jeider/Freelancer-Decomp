"""Offline render after decoding the staged CMP; never launch Freelancer."""
import sys,math
from pathlib import Path
import bpy
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from native_common import *

bpy.ops.wm.open_mainfile(filepath=str(PROTO/'bismarck_material_relief.blend'))
root=read_tree(DataFolder(root=STAGE).data_path(REL).read_bytes())[1][0]
parts=get_parts(root)
groups=next(p for p in parts if p['name']=='Root')['groups']
for p in parts:
    if p['name'].startswith('BizRelief'):groups+=p['groups']
stats=json.loads((PROTO/'prototype_stats.json').read_text())
source=json.loads((PROTO/'scene_mesh.json').read_text())
for i in stats['changed_batches']:
    name=source['materials'][str(groups[i]['material'])]['name'].split('.')[0].lower()
    ob=bpy.data.objects[name+'_contour_relief'];mat=ob.data.materials[0]
    c=groups[i]['corners'].reshape(-1,10)
    mesh=bpy.data.meshes.new(name+'_native_roundtrip')
    mesh.from_pydata([(v[0],-v[2],v[1]) for v in c],[],np.arange(len(c)).reshape(-1,3).tolist());mesh.update()
    for slot in range(2):
        uv=mesh.uv_layers.new(name=f'Native UV{slot}')
        for loop in mesh.loops:uv.data[loop.index].uv=(c[loop.vertex_index,6+slot*2],1-c[loop.vertex_index,7+slot*2])
    mesh.uv_layers.active_index=0
    for p in mesh.polygons:p.use_smooth=True
    mesh.normals_split_custom_set([(v[3],-v[5],v[4]) for v in c]);mesh.materials.append(mat);ob.data=mesh
scene=bpy.context.scene;scene.cycles.samples=24
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    scene.cycles.device='GPU'
except Exception:pass
cam=scene.camera
def cv(v):return Vector((v[0],-v[2],v[1]))
cam.location=(-2,1.5,7);cam.rotation_euler=(Vector((11.77,1.5,7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(68)
scene.render.filepath=str(OUT/'native_arch_room.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'native_roundtrip.blend'))
# Match the reviewed wall-only camera/light; foreground machinery is archived
# only for this inspection render, never removed from the CMP or saved blend.
import bmesh
for ob in scene.objects:
    if ob.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(ob.data)
    bmesh.ops.delete(bm,geom=[f for f in bm.faces if not 11.48<f.calc_center_median().x<12.06],context='FACES')
    bm.to_mesh(ob.data);bm.free();ob.data.update()
light=bpy.data.lights.new('Wall inspection soft light','AREA');light.energy=700;light.size=5
ob=bpy.data.objects.new(light.name,light);scene.collection.objects.link(ob);ob.location=(5,-3,10);ob.rotation_euler=(Vector((11.77,1.5,7))-ob.location).to_track_quat('-Z','Y').to_euler()
scene.render.filepath=str(OUT/'native_arch_wall.png');bpy.ops.render.render(write_still=True)
print('Native CMP roundtrip rendered; original embedded material bytes retained in CMP (Blender material approximation only).')
