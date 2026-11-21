"""Measure how the original Higa arms meet the pauldrons. No file writes."""
import sys
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
SRC = ROOT / 'out/character_rounding/higa/rigged/higa_kaitlyn_rigged.blend'
ARM = ('LUpArm', 'LLowArm', 'LHand', 'RUpArm', 'RLowArm', 'RHand')


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    mesh = body.data
    pts = np.array([v.co[:] for v in mesh.vertices])
    print('verts', len(pts), 'z', round(float(pts[:, 2].min()), 3), round(float(pts[:, 2].max()), 3))
    groups = {g.name: g.index for g in body.vertex_groups}
    arm_idx = [groups[n] for n in ARM if n in groups]
    weights = np.zeros(len(pts))
    for v in mesh.vertices:
        weights[v.index] = sum(g.weight for g in v.groups if g.group in arm_idx)
    arm = weights > 0.85
    torso = weights < 0.15
    print('arm>0.85', int(arm.sum()), 'torso<0.15', int(torso.sum()), 'blend', int(((weights >= 0.15) & (weights <= 0.85)).sum()))
    for sign, name in ((1, 'R'), (-1, 'L')):
        side = arm & (np.sign(pts[:, 0]) == sign)
        top = pts[side]
        print(name, 'arm', int(side.sum()), 'x', np.round(top[:, 0].min(), 3), np.round(top[:, 0].max(), 3),
              'z', np.round(top[:, 2].min(), 3), np.round(top[:, 2].max(), 3))
        high = top[top[:, 2] > np.percentile(top[:, 2], 95)]
        print('  top5', np.round(high.mean(axis=0), 3))
    paul = torso & (pts[:, 2] > 1.30) & (np.abs(pts[:, 0]) > 0.08) & (np.abs(pts[:, 0]) < 0.32)
    print('pauldron torso', int(paul.sum()), 'x', round(float(np.percentile(np.abs(pts[paul, 0]), 98)), 3) if paul.any() else None,
          'z', np.round(pts[paul, 2].min(), 3) if paul.any() else None, np.round(pts[paul, 2].max(), 3) if paul.any() else None)
    # boundary edges between arm and torso
    cut = 0
    for poly in mesh.polygons:
        ids = list(poly.vertices)
        flags = arm[ids]
        if flags.any() and not flags.all():
            cut += 1
    print('faces crossing arm cut', cut)


if __name__ == '__main__':
    main()
