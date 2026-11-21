"""Scale the original Higa rig to the peasant shoulder width, feet on the ground.

Each arm then slides as a rigid piece under the pauldron. Arm vertices keep
their shape. Pauldron plates are only scaled, not recut. Skeleton and head
hardpoints stay.
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
PEASANT_SHOULDER_X = 0.210
HP_HEAD = Vector((0.0018, -0.0028, 0.6445 + GROUND))
HP_NECK = Vector((0.0013, -0.0028, 0.5295 + GROUND))
ARM = ('LUpArm', 'LLowArm', 'LHand', 'RUpArm', 'RLowArm', 'RHand')


def render(scene, preview):
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


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    rig = body.parent
    for mod in list(body.modifiers):
        if mod.type == 'ARMATURE':
            body.modifiers.remove(mod)
    mesh = body.data
    pts = np.array([v.co[:] for v in mesh.vertices])
    before = len(pts)
    groups = {g.name: g.index for g in body.vertex_groups}
    arm_idx = [groups[n] for n in ARM if n in groups]
    weights = np.zeros(len(pts))
    for v in mesh.vertices:
        weights[v.index] = sum(g.weight for g in v.groups if g.group in arm_idx)
    paul = (weights < 0.15) & (pts[:, 2] > 1.30) & (np.abs(pts[:, 0]) > 0.08) & (np.abs(pts[:, 0]) < 0.32)
    shoulder_x = float(np.percentile(np.abs(pts[paul, 0]), 98))
    scale = PEASANT_SHOULDER_X / shoulder_x
    pts *= scale
    arm = weights > 0.85
    for sign in (1.0, -1.0):
        side = arm & (np.sign(pts[:, 0]) == sign)
        top = pts[side]
        top = top[top[:, 2] > np.percentile(top[:, 2], 92)]
        center = top.mean(axis=0)
        plate = pts[paul]
        plate = plate[np.sign(plate[:, 0]) == sign]
        near = plate[np.abs(plate[:, 0] - center[0]) < 0.05]
        floor = float(np.min(near[:, 2])) if len(near) else float(np.min(plate[:, 2]))
        print('side', int(sign), 'arm top', np.round(center, 3), 'plate floor', round(floor, 3), 'gap', round(floor - float(center[2]), 3))
    for v, p in zip(mesh.vertices, pts):
        v.co = p
    mesh.update()
    if len(mesh.vertices) != before:
        raise SystemExit('vertex count changed: %s -> %s' % (before, len(mesh.vertices)))
    mod = body.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
    mod.object = rig
    for name, loc in (('hp_head peasant', HP_HEAD), ('hp_neck peasant', HP_NECK)):
        empty = bpy.data.objects.new(name, None)
        empty.empty_display_type = 'ARROWS'
        empty.empty_display_size = 0.06
        empty.location = loc
        bpy.context.collection.objects.link(empty)
    print('scale', round(scale, 3), 'verts', len(mesh.vertices), 'z', round(float(pts[:, 2].min()), 3), round(float(pts[:, 2].max()), 3))
    blend = OUT / 'higa_uniform.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    render(bpy.context.scene, OUT / 'preview')
    print('BLEND', blend)


if __name__ == '__main__':
    main()
