"""Show whether the stepped pauldron underside is already in the source rig."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
OUT = ROOT / 'out/character_rounding/higa/uniform_scale/preview'
OUT.mkdir(parents=True, exist_ok=True)


def shot(path, label):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    for mod in list(body.modifiers):
        if mod.type == 'ARMATURE':
            mod.show_viewport = False
            mod.show_render = False
    pts = np.array([v.co[:] for v in body.data.vertices])
    # right pauldron, the stacked lip the user photographed
    band = (pts[:, 0] > 0.08) & (pts[:, 0] < 0.28) & (pts[:, 2] > 1.15) & (pts[:, 2] < 1.55) & (pts[:, 1] > -0.08) & (pts[:, 1] < 0.08)
    sample = pts[band]
    if len(sample):
        # cluster by Z to see stacked shells
        z = np.round(sample[:, 2], 3)
        uniq = np.unique(z)
        gaps = np.diff(np.sort(uniq))
        print(label, 'verts', int(band.sum()), 'z', round(float(sample[:, 2].min()), 3), round(float(sample[:, 2].max()), 3),
              'unique z mm', len(uniq), 'gaps>3mm', int((gaps > 0.003).sum()))
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
    scene.render.resolution_y = 900
    if scene.world is None:
        scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.55, 0.55, 0.55, 1)
    scene.view_settings.view_transform = 'AgX'
    body.data.materials.clear()
    mat = bpy.data.materials.new('Clay')
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.75, 0.75, 0.75, 1)
    body.data.materials.append(mat)
    for ob in list(bpy.data.objects):
        if ob.type == 'EMPTY':
            bpy.data.objects.remove(ob, do_unlink=True)
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'PERSP'
    cam.data.lens = 50
    # match the user's rear-three-quarter close-up of the right pauldron
    cam.location = (0.55, -0.55, 1.45)
    cam.rotation_euler = (Vector((0.12, -0.02, 1.28)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    ld = bpy.data.lights.new('Key', 'AREA')
    ld.energy = 250
    ld.size = 1.2
    lamp = bpy.data.objects.new('Key', ld)
    scene.collection.objects.link(lamp)
    lamp.location = (0.8, -1.2, 1.8)
    lamp.rotation_euler = (Vector((0.12, 0, 1.28)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    scene.render.filepath = str(OUT / (label + '_pauldron.png'))
    bpy.ops.render.render(write_still=True)


shot(ROOT / 'out/character_rounding/higa/rigged/higa_kaitlyn_rigged.blend', 'source')
shot(ROOT / 'out/character_rounding/higa/uniform_scale/higa_uniform.blend', 'scaled')
