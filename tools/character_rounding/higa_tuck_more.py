"""Slide the already scaled arms further under the pauldrons. Rigid only."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
SRC = ROOT / 'out/character_rounding/higa/uniform_scale/higa_uniform.blend'
OUT = ROOT / 'out/character_rounding/higa/uniform_scale'
ARM = ('LUpArm', 'LLowArm', 'LHand', 'RUpArm', 'RLowArm', 'RHand')


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    mesh = body.data
    before = len(mesh.vertices)
    for mod in list(body.modifiers):
        if mod.type == 'ARMATURE':
            body.modifiers.remove(mod)
    pts = np.array([v.co[:] for v in mesh.vertices])
    groups = {g.name: g.index for g in body.vertex_groups}
    arm_idx = [groups[n] for n in ARM if n in groups]
    weights = np.zeros(len(pts))
    for v in mesh.vertices:
        weights[v.index] = sum(g.weight for g in v.groups if g.group in arm_idx)
    arm = weights > 0.85
    paul = (weights < 0.15) & (pts[:, 2] > 1.15) & (np.abs(pts[:, 0]) > 0.10)
    for sign in (1.0, -1.0):
        side = arm & (np.sign(pts[:, 0]) == sign)
        top = pts[side]
        top = top[top[:, 2] > np.percentile(top[:, 2], 90)]
        center = top.mean(axis=0)
        plate = pts[paul & (np.sign(pts[:, 0]) == sign)]
        # underside of the plate outboard of the arm stump
        lip = plate[(np.abs(plate[:, 0]) > abs(center[0])) & (plate[:, 2] < center[2] + 0.12)]
        if len(lip) < 20:
            lip = plate[plate[:, 2] < center[2] + 0.10]
        lip_z = float(np.percentile(lip[:, 2], 30))
        lip_x = float(np.percentile(np.abs(lip[:, 0]), 40))
        delta = np.array([sign * (lip_x - abs(center[0]) + 0.02), 0.0, lip_z + 0.03 - center[2]])
        # keep the slide modest so the hand does not leave the body
        delta = np.clip(delta, -0.08, 0.08)
        pts[side] += delta
        print('side', int(sign), 'center', np.round(center, 3), 'delta', np.round(delta, 3), 'lip', round(lip_z, 3), round(lip_x, 3))
    for v, p in zip(mesh.vertices, pts):
        v.co = p
    mesh.update()
    if len(mesh.vertices) != before:
        raise SystemExit('lost verts')
    mod = body.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
    mod.object = body.parent
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
    scene.view_settings.view_transform = 'AgX'
    cam = bpy.data.objects['Camera']
    scene.camera = cam
    preview = OUT / 'preview'
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
    print('verts', len(mesh.vertices))


if __name__ == '__main__':
    main()
