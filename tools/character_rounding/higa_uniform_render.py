import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
path = ROOT / 'out/character_rounding/higa/uniform_scale/higa_uniform.blend'
bpy.ops.wm.open_mainfile(filepath=str(path))
configure('character_rounding')
body = bpy.data.objects['Higa - skinned Meshy mesh']
print('verts', len(body.data.vertices))
scene = bpy.context.scene
scene.frame_set(1)
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.cycles.use_denoising = True
try:
    prefs = bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type = 'OPTIX'
    prefs.get_devices()
    for d in prefs.devices:
        d.use = d.type == 'OPTIX'
    if any(d.use for d in prefs.devices):
        scene.cycles.device = 'GPU'
except Exception:
    pass
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
if scene.world is None:
    scene.world = bpy.data.worlds.new('Studio')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.14, 0.14, 0.14, 1)
scene.view_settings.view_transform = 'AgX'
for loc, power in (((-2.2, 3.2, 2.4), 340), ((2.4, 1.4, 1.8), 180)):
    ld = bpy.data.lights.new('Softbox', 'AREA')
    ld.energy = power
    ld.size = 2.2
    lamp = bpy.data.objects.new(ld.name, ld)
    scene.collection.objects.link(lamp)
    lamp.location = loc
    lamp.rotation_euler = (Vector((0, 0, 0.9)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
scene.collection.objects.link(cam)
scene.camera = cam
cam.data.type = 'ORTHO'
preview = ROOT / 'out/character_rounding/higa/uniform_scale/preview'
preview.mkdir(exist_ok=True)
shots = {
    'front': ((0, 4.2, 0.85), 1.9),
    'side': ((4.2, 0.2, 0.85), 1.9),
    'shoulder': ((1.2, 1.5, 1.15), 0.55),
}
for label, (loc, ortho) in shots.items():
    cam.location = loc
    cam.data.ortho_scale = ortho
    target_z = 0.9 if label != 'shoulder' else 1.15
    cam.rotation_euler = (Vector((0, 0, target_z)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(preview / (label + '.png'))
    bpy.ops.render.render(write_still=True)
