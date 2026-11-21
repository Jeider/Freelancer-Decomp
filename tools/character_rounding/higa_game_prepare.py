"""Cut the Meshy head, seat limbs on the female joints, export a game mesh.

Standard head mount comes from ku_kym_body_gen. Neck cap is placeholder skin.
No game writes here.
"""
import json
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
TOP = ROOT / 'out/character_rounding/higa'
SRC = TOP / 'rigged/higa_kaitlyn_rigged.blend'
OUT = TOP / 'game_body'
GROUND = 0.96956336


def smoothstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def dominant(ob, names):
    weights = np.zeros((len(ob.data.vertices), len(names)))
    index = {g.index: i for i, g in enumerate(ob.vertex_groups) if g.name in names}
    name_of = {i: names[g.name] for i, g in enumerate(ob.vertex_groups) if g.name in names}
    for v in ob.data.vertices:
        for g in v.groups:
            if g.group in name_of:
                weights[v.index, name_of[g.group]] = g.weight
    return weights


def seat(points, mask, chain):
    """Slide the limb centerline onto the joints without slicing it into bands."""
    if int(mask.sum()) < 30:
        return
    ids = np.flatnonzero(mask)
    order = [np.array(chain[0])]
    for point in chain[1:]:
        point = np.array(point)
        if point[2] < order[-1][2] - 1e-4:
            order.append(point)
    order = np.array(order)
    z = points[ids, 2]
    span = float(order[0, 2] - order[-1, 2])
    t = np.clip((order[0, 2] - z) / max(span, 1e-6), 0, 1)
    samples = np.linspace(0, 1, 16)
    current = np.full((len(samples), 2), np.nan)
    for i, s in enumerate(samples):
        sl = np.abs(t - s) < 0.06
        if int(sl.sum()) >= 6:
            current[i] = np.median(points[ids[sl], :2], axis=0)
    for axis in range(2):
        known = np.isfinite(current[:, axis])
        if int(known.sum()) < 2:
            return
        current[:, axis] = np.interp(samples, samples[known], current[known, axis])
    goal = np.vstack([np.interp(samples, np.linspace(0, 1, len(order)), order[:, i]) for i in range(2)]).T
    delta = goal - current[:, :2]
    blend = smoothstep(0.08, 0.25, t)
    shift = np.vstack([np.interp(t, samples, delta[:, i]) for i in range(2)]).T
    points[ids, :2] += shift * blend[:, None]


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    ob = bpy.data.objects['Higa - skinned Meshy mesh']
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.scene.frame_set(1)
    bones = ob.parent.data.bones
    joints = {b.name: np.array(b.head_local) for b in bones}
    names = [b.name for b in bones]
    name_index = {n: i for i, n in enumerate(names)}
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    neck = joints['Body_Neck'][2]
    delete = []
    for v in bm.verts:
        x, y, z = v.co
        if z > neck - 0.02 and abs(x) < 0.10:
            delete.append(v)
        elif z > neck + 0.06:
            delete.append(v)
    bmesh.ops.delete(bm, geom=delete, context='VERTS')
    boundary = [e for e in bm.edges if e.is_boundary and e.verts[0].co.z > neck - 0.12]
    if boundary:
        bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
    skin_faces = [f for f in bm.faces if f.calc_center_median().z > neck - 0.08 and abs(f.calc_center_median().x) < 0.09]
    if 'Higa skin cap' not in ob.data.materials:
        slot = bpy.data.materials.new('Higa skin cap')
        slot.use_nodes = True
        slot.diffuse_color = (0.72, 0.50, 0.38, 1)
        bs = slot.node_tree.nodes.get('Principled BSDF')
        if bs:
            bs.inputs['Base Color'].default_value = (0.72, 0.50, 0.38, 1)
        ob.data.materials.append(slot)
    skin_index = ob.data.materials.find('Higa skin cap')
    for face in skin_faces:
        face.material_index = skin_index
    bm.to_mesh(me)
    bm.free()
    me.update()
    points = np.array([v.co[:] for v in me.vertices])
    weights = np.zeros((len(points), len(names)))
    for v in me.vertices:
        for g in v.groups:
            group = ob.vertex_groups[g.group]
            if group.name in name_index:
                weights[v.index, name_index[group.name]] = g.weight
    # Width seating is deferred: the first slice shift tore the costume.
    # This pass only removes the head and keeps the fitted limbs.
    for modifier in list(ob.modifiers):
        ob.modifiers.remove(modifier)
    faces_before = len(me.polygons)
    ratio = min(0.10, 42000 / max(faces_before, 1))
    mod = ob.modifiers.new('Game test', 'DECIMATE')
    mod.decimate_type = 'COLLAPSE'
    mod.ratio = ratio
    bpy.ops.object.modifier_apply(modifier=mod.name)
    me = ob.data
    me.calc_loop_triangles()
    # Split only where the material changes. One costume UV plus a skin cap.
    points, normals, uvs, skin, faces = [], [], [], [], {0: [], 1: []}
    lookup = {}
    group_names = [g.name for g in ob.vertex_groups]
    for tri in me.loop_triangles:
        slot = 1 if me.materials[tri.material_index].name == 'Higa skin cap' else 0
        face = []
        for loop_id in tri.loops:
            loop = me.loops[loop_id]
            vi = loop.vertex_index
            n = me.corner_normals[loop_id].vector.normalized()
            uv = me.uv_layers.active.data[loop_id].uv if me.uv_layers else Vector((0.5, 0.5))
            if slot == 1:
                uv = Vector((0.5, 0.5))
            key = (vi, slot, tuple(round(x, 5) for x in n), tuple(round(x, 5) for x in uv))
            if key not in lookup:
                lookup[key] = len(points)
                p = me.vertices[vi].co
                points.append((p.x, p.z - GROUND, -p.y))
                normals.append((n.x, n.z, -n.y))
                uvs.append((uv.x, 1 - uv.y))
                row = np.zeros(len(group_names), np.float32)
                for g in me.vertices[vi].groups:
                    if g.weight > 0.001:
                        row[g.group] = g.weight
                keep = np.argsort(row)[-4:]
                masked = np.zeros_like(row)
                masked[keep] = row[keep]
                masked[masked < 0.002] = 0
                total = masked.sum()
                skin.append(masked / total if total else masked)
            face.append(lookup[key])
        faces[slot].append(face)
    assert len(points) < 65536, len(points)
    np.savez_compressed(OUT / 'mesh.npz', points=np.array(points, np.float32), normals=np.array(normals, np.float32),
                        uv=np.array(uvs, np.float32), weights=np.array(skin, np.float32),
                        costume=np.array(faces[0], np.uint16), skin_cap=np.array(faces.get(1) or [], np.uint16),
                        bone_names=np.array(group_names))
    report = {'points': len(points), 'costume_tris': len(faces[0]), 'skin_tris': len(faces[1]),
              'faces_before_decimate': faces_before, 'installed': False}
    (OUT / 'prepare.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
