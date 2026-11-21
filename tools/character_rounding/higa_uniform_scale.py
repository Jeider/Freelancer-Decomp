"""Uniform-scale the original Higa rig to the peasant shoulder width.

Skeleton and head hardpoints stay. Arms are the original mesh, not reshaped.
"""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
SRC = ROOT / 'out/character_rounding/higa/rigged/higa_kaitlyn_rigged.blend'
OUT = ROOT / 'out/character_rounding/higa/uniform_scale'
GROUND = 0.96956336
# Peasant shoulder caps reach x=0.21. Head mount stays on the unscaled bone.
PEASANT_SHOULDER_X = 0.210
HP_HEAD = Vector((0.0018, -0.0028, 0.6445 + GROUND))
HP_NECK = Vector((0.0013, -0.0028, 0.5295 + GROUND))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    rig = body.parent
    for mod in list(body.modifiers):
        if mod.type == 'ARMATURE':
            body.modifiers.remove(mod)
    pts = np.array([v.co[:] for v in body.data.vertices])
    paul = pts[(pts[:, 2] > 1.36) & (np.abs(pts[:, 0]) > 0.10) & (np.abs(pts[:, 0]) < 0.32)]
    shoulder_x = float(np.percentile(np.abs(paul[:, 0]), 98)) if len(paul) else 0.249
    scale = PEASANT_SHOULDER_X / shoulder_x
    # Pivot is the shoulder line, so the arm-to-pauldron connection is not sheared.
    pivot = np.array([0.0, 0.0, 1.396])
    scaled = pivot + (pts - pivot) * scale
    for v, p in zip(body.data.vertices, scaled):
        v.co = p
    body.data.update()
    mod = body.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
    mod.object = rig
    mod.use_deform_preserve_volume = False
    for name, loc in (('hp_head peasant', HP_HEAD), ('hp_neck peasant', HP_NECK)):
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = 0.06
        empty.location = loc
        bpy.context.collection.objects.link(empty)
    print('shoulder_x', round(shoulder_x, 3), 'scale', round(scale, 3))
    print('z', round(float(scaled[:, 2].min()), 3), round(float(scaled[:, 2].max()), 3))
    print('pauldron x', round(float(np.percentile(np.abs(scaled[(scaled[:, 2] > 1.30) & (np.abs(scaled[:, 0]) > 0.08), 0]), 98)), 3))
    blend = OUT / 'higa_uniform.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
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
    cam.data.ortho_scale = 1.7
    preview = OUT / 'preview'
    preview.mkdir(exist_ok=True)
    for label, loc in (('front', (0, 4.2, 1.05)), ('side', (4.2, 0.2, 1.05))):
        cam.location = loc
        cam.rotation_euler = (Vector((0, 0, 1.05)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    print('BLEND', blend)


if __name__ == '__main__':
    main()
