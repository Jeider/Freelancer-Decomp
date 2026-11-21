"""Report the true arm-cut rings, not every open edge."""
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
SRC = ROOT / 'out/character_rounding/higa/rigged/higa_kaitlyn_rigged.blend'
ARM = {'LUpArm', 'RUpArm', 'LLowArm', 'RLowArm', 'LHand', 'RHand', 'Left__hand_END', 'Right__hand_END'}


def loops(edges):
    unused = set(map(tuple, edges))
    found = []
    while unused:
        a, b = unused.pop()
        seq = [a, b]
        while True:
            nxt = None
            for edge in list(unused):
                if edge[0] == seq[-1]:
                    nxt = edge[1]
                elif edge[1] == seq[-1]:
                    nxt = edge[0]
                if nxt is not None:
                    unused.remove(edge)
                    break
            if nxt is None or nxt == seq[0]:
                break
            seq.append(nxt)
        found.append(seq)
    return found


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    for modifier in list(body.modifiers):
        if modifier.type == 'ARMATURE':
            body.modifiers.remove(modifier)
    names = [g.name for g in body.vertex_groups]
    index = {name: i for i, name in enumerate(names)}
    weights = np.zeros((len(body.data.vertices), len(names)))
    for v in body.data.vertices:
        for g in v.groups:
            if g.group < len(names):
                weights[v.index, g.group] = g.weight
    points = np.array([v.co[:] for v in body.data.vertices])
    neck = body.parent.data.bones['Body_Neck'].head_local.z
    arm_cols = [index[n] for n in ARM if n in index]
    drop = (weights[:, arm_cols].sum(1) > 0.45) | ((points[:, 2] > neck - 0.02) & (np.abs(points[:, 0]) < 0.10)) | (points[:, 2] > neck + 0.06)
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    cut = []
    for e in bm.edges:
        flags = [drop[v.index] for v in e.verts]
        if flags[0] != flags[1] and not drop[e.verts[0].index]:
            cut.append(e.verts[0].index)
        elif flags[0] != flags[1]:
            cut.append(e.verts[1].index)
    # edges wholly on the kept side of the cut
    keep_edges = []
    for e in bm.edges:
        a, b = e.verts
        if drop[a.index] == drop[b.index]:
            continue
        kept = a if not drop[a.index] else b
        other = b if kept is a else a
        if other.co.z > 1.05 and abs(kept.co.x) > 0.05:
            keep_edges.append((kept.index, other.index))
    print('cut verts', len(set(cut)))
    # group kept endpoints by side using the kept vertex
    for sign, label in ((1, 'R'), (-1, 'L')):
        side = [(k, d) for k, d in keep_edges if np.sign(body.data.vertices[k].co.x) == sign]
        co = np.array([body.data.vertices[k].co[:] for k, _ in side]) if side else np.zeros((0, 3))
        if len(co):
            print(label, 'cut edges', len(side), 'center', np.round(co.mean(0), 3), 'z', round(float(co[:, 2].min()), 3), round(float(co[:, 2].max()), 3), 'x', round(float(np.abs(co[:, 0]).min()), 3), round(float(np.abs(co[:, 0]).max()), 3))
    bm.free()


if __name__ == '__main__':
    main()
