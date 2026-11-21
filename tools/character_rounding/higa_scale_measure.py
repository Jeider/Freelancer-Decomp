"""Compare Meshy Higa proportions with the peasant body. Print only."""
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
FBX = next(Path('D:/work/MESHY/higa1').glob('*.fbx'))
BLEND = ROOT / 'out/character_rounding/higa/peasant_arms/higa_peasant_arms.blend'
GROUND = 0.96956336


def bounds(pts, label):
    pts = np.asarray(pts)
    print(label, 'n', len(pts),
          'x', np.round(pts[:, 0].min(), 3), np.round(pts[:, 0].max(), 3),
          'y', np.round(pts[:, 1].min(), 3), np.round(pts[:, 1].max(), 3),
          'z', np.round(pts[:, 2].min(), 3), np.round(pts[:, 2].max(), 3))


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    configure('character_rounding')
    bpy.ops.import_scene.fbx(filepath=str(FBX))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    raw = np.vstack([np.array([v.co[:] for v in o.data.vertices]) for o in meshes])
    bounds(raw, 'meshy raw')
    extent = raw.max(0) - raw.min(0)
    print('meshy extent', np.round(extent, 3), 'up axis', int(np.argmax(extent)))
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    sleeves = bpy.data.objects['pl_female1 sleeves']
    for ob in (body, sleeves):
        for mod in list(ob.modifiers):
            if mod.type == 'ARMATURE':
                ob.modifiers.remove(mod)
    hp = np.array([v.co[:] for v in body.data.vertices])
    sp = np.array([v.co[:] for v in sleeves.data.vertices])
    bounds(hp, 'higa blend')
    bounds(sp, 'sleeves')
    # Pauldron: high lateral gold, not the neck cap.
    paul = hp[(hp[:, 2] > 1.36) & (np.abs(hp[:, 0]) > 0.10) & (np.abs(hp[:, 0]) < 0.32)]
    if len(paul):
        print('pauldron n', len(paul), 'z', round(float(paul[:, 2].min()), 3), round(float(paul[:, 2].max()), 3),
              'x', round(float(np.abs(paul[:, 0]).min()), 3), round(float(np.abs(paul[:, 0]).max()), 3))
    chest = hp[(hp[:, 2] > 1.15) & (hp[:, 2] < 1.35) & (np.abs(hp[:, 0]) < 0.16)]
    print('higa chest half x', round(float(np.percentile(np.abs(chest[:, 0]), 95)), 3) if len(chest) else 'none')
    print('sleeve top z', round(float(sp[:, 2].max()), 3), 'cuff z', round(float(sp[:, 2].min()), 3))
    hip = hp[(hp[:, 2] > 0.85) & (hp[:, 2] < 1.05) & (np.abs(hp[:, 0]) < 0.12)]
    print('higa hip band z mean', round(float(hip[:, 2].mean()), 3) if len(hip) else 'none', 'n', len(hip))
    print('peasant shoulder joint z', round(0.426 + GROUND, 3), 'neck z', round(0.529 + GROUND, 3), 'mesh top z', round(0.511 + GROUND, 3))


if __name__ == '__main__':
    main()
