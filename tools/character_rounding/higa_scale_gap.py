"""Where the peasant sleeve top sits relative to the Higa pauldron."""
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
BLEND = ROOT / 'out/character_rounding/higa/peasant_arms/higa_peasant_arms.blend'


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    sleeves = bpy.data.objects['pl_female1 sleeves']
    for ob in (body, sleeves):
        for mod in ob.modifiers:
            if mod.type == 'ARMATURE':
                ob.modifiers.remove(mod)
    hp = np.array([v.co[:] for v in body.data.vertices])
    sp = np.array([v.co[:] for v in sleeves.data.vertices])
    for sign, label in ((1, 'R'), (-1, 'L')):
        side = sp[np.sign(sp[:, 0]) == sign]
        top = side[side[:, 2] > np.percentile(side[:, 2], 92)]
        c = top.mean(0)
        print(label, 'sleeve top center', np.round(c, 3), 'n', len(top), 'x', np.round(top[:, 0].min(), 3), np.round(top[:, 0].max(), 3), 'y', np.round(top[:, 1].min(), 3), np.round(top[:, 1].max(), 3))
        d = np.linalg.norm(hp - c, axis=1)
        near = hp[d < 0.04]
        print('  higa within 4cm', len(near))
        if len(near):
            print('  those z', round(float(near[:, 2].min()), 3), round(float(near[:, 2].max()), 3), 'y', round(float(near[:, 1].min()), 3), round(float(near[:, 1].max()), 3))
        order = np.argsort(d)[:5]
        for i in order:
            print('  nearest', np.round(hp[i], 3), 'dist', round(float(d[i]), 3))
        # pauldron plate near this x
        plate = hp[(np.sign(hp[:, 0]) == sign) & (np.abs(hp[:, 0] - c[0]) < 0.04) & (hp[:, 2] > 1.30)]
        if len(plate):
            print('  plate at arm x: z', round(float(plate[:, 2].min()), 3), round(float(plate[:, 2].max()), 3), 'y', round(float(plate[:, 1].min()), 3), round(float(plate[:, 1].max()), 3), 'n', len(plate))


if __name__ == '__main__':
    main()
