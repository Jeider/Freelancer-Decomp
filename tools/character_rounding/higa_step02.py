"""Higa step 02. Native Kaitlyn volume and skirt flaps, concept pieces as real shells.

Step 01's radial skirt followed arm hits and became a disk. This pass keeps the
native skirt faces, repaints the body from its own atlas, and builds pauldrons
and plates in place. Not installed.
"""
import math
import sys
from collections import Counter
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0, str(Path(__file__).parent))
import higa_build as h

OUT = h.TOP / 'step_02'
PALETTE = {
    'skin': np.array([214, 158, 124], float),
    'black': np.array([38, 34, 32], float),
    'red': np.array([156, 34, 30], float),
    'boot': np.array([24, 24, 28], float),
    'gold': np.array([176, 132, 42], float),
    'silver': np.array([168, 174, 180], float),
    'cyan': np.array([42, 92, 118], float),
}


def paint_material(name, rough, metal):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = False
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    node = mat.node_tree.nodes.new('ShaderNodeVertexColor')
    node.layer_name = 'Higa'
    mat.node_tree.links.new(node.outputs['Color'], bs.inputs['Base Color'])
    return mat


def recolor(rgb, kind):
    lum = float(np.dot(rgb, [0.30, 0.55, 0.15])) / 255
    return np.clip(PALETTE[kind] * (0.42 + 0.85 * lum), 0, 255) / 255


def boundary(faces):
    count = Counter()
    for face in faces:
        for a, b in zip(face, face[1:] + face[:1]):
            count[tuple(sorted((int(a), int(b))))] += 1
    return [edge for edge, n in count.items() if n == 1]


def skirt_mask(points, normals, faces):
    c = points[faces].mean(1)
    n = normals[faces].mean(1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    x, y, z = c[:, 0], c[:, 1], c[:, 2]
    return (z > -0.30) & (z < 0.14) & (np.abs(x) > 0.09) & (np.abs(x) < 0.19) & (np.abs(y) < 0.12) & (
        (n[:, 0] * np.sign(x) > 0.25) | (n[:, 1] < -0.15))


def chest_mask(points, normals, faces):
    c = points[faces].mean(1)
    n = normals[faces].mean(1)
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-9
    return (c[:, 2] > 0.30) & (c[:, 2] < 0.47) & (c[:, 1] > 0.02) & (n[:, 1] > 0.35) & (np.abs(c[:, 0]) < 0.11)


def offset_faces(src, faces, normals, weights, distance):
    mapping = {}
    points, out_n, out_w, out_f = [], [], [], []
    for face in faces:
        tri = []
        for i in face:
            if i not in mapping:
                mapping[i] = len(points)
                points.append(src[i] + normals[i] * distance)
                out_n.append(normals[i])
                out_w.append(weights[i])
            tri.append(mapping[i])
        out_f.append(tuple(tri))
    return np.array(points), np.array(out_n), np.array(out_w), out_f, mapping


def edge_strip(points, normals, weights, edges, direction, width, color):
    verts, cols, w, faces = [], [], [], []
    for a, b in edges:
        n = (normals[a] + normals[b]) * 0.5
        n = n / (np.linalg.norm(n) + 1e-9)
        shift = n * 0.004 + direction * width
        base = len(verts)
        verts += [points[a], points[b], points[b] + shift, points[a] + shift]
        cols += [color] * 4
        w += [weights[a], weights[b], weights[b], weights[a]]
        faces += [(base, base + 1, base + 2), (base, base + 2, base + 3)]
    return np.array(verts), faces, np.array(w), np.array(cols)


def painted(ob, loop_rgb):
    me = ob.data
    layer = me.color_attributes.new('Higa', 'BYTE_COLOR', 'CORNER')
    for i, rgb in enumerate(loop_rgb):
        layer.data[i].color = (*rgb, 1)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    h.configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    body = h.load('body')
    names = [b['name'] for b in body['bones']]
    count = len(names)
    rig = h.rig_native(body, h.collection('RIG — native Bretonia female'))
    worn = h.collection('EDIT — Higa costume')
    parts = h.collection('REFERENCE — native head and hands')
    h.collection('ARCHIVE — native body (disabled)', hide=True)
    points = np.array([h.game_to_bl(p) for p in body['points']])
    normals = np.array([h.game_to_bl(n) for n in body['normals']])
    normals /= np.linalg.norm(normals, axis=1, keepdims=True) + 1e-9
    weights = np.array([h.weight_row(s, count) for s in body['skin']])
    faces = np.array([t for g in body['groups'] for t in g['faces']])
    paint = np.load(OUT / 'paint.npz')
    loop_rgb = paint['rgb'].copy()
    skirt = np.flatnonzero(paint['skirt'])
    chest = np.flatnonzero(paint['chest'])
    for index, face in enumerate(faces):
        center = points[face].mean(0)
        if center[2] < -0.16 and abs(center[0]) < 0.18:
            loop_rgb[index * 3:index * 3 + 3] = (0.07, 0.07, 0.08)
        elif center[2] > 0.38 and 0.05 < abs(center[0]) < 0.22:
            loop_rgb[index * 3:index * 3 + 3] = (0.10, 0.09, 0.08)
        elif index in set(skirt.tolist()):
            loop_rgb[index * 3:index * 3 + 3] = (0.05, 0.045, 0.04)
    me = bpy.data.meshes.new('00 body')
    me.from_pydata(points.tolist(), [], [tuple(t) for t in faces])
    me.update()
    body_ob = bpy.data.objects.new('00 body', me)
    worn.objects.link(body_ob)
    uv = me.uv_layers.new(name='Native UV')
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            uv.data[li].uv = body['uv'][me.loops[li].vertex_index]
    me.normals_split_custom_set([tuple(normals[loop.vertex_index]) for loop in me.loops])
    painted(body_ob, loop_rgb)
    body_ob.data.materials.append(paint_material('higa_body_paint', 0.72, 0))
    h.add_skin(body_ob, weights, names, rig)

    mats = {k: h.material('higa_' + k, 'higa_' + ('boot' if k == 'boot' else k) + '.png', r, m)
            for k, r, m in (('gold', 0.36, 0.78), ('silver', 0.30, 0.84), ('red', 0.8, 0), ('black', 0.86, 0))}
    # Textures were authored as higa_skin/black/red/gold/silver/boot. Silver plates use silver.
    sp, sn, sw, sf, smap = offset_faces(points, faces[skirt], normals, weights, 0.005)
    # Drop only the hem, so the panel hangs instead of sticking out horizontally.
    hem = sp[:, 2] < np.percentile(sp[:, 2], 28)
    sp[hem, 2] -= 0.035
    sp[hem] += sn[hem] * 0.012
    stripe = np.tile((0.05, 0.045, 0.04), (len(sp), 1))
    for z0, kind in ((-0.02, 'red'), (-0.08, 'cyan'), (-0.15, 'gold')):
        stripe[np.abs(sp[:, 2] - z0) < 0.012] = PALETTE[kind] / 255
    skirt_ob = h.finish_mesh('15 rear skirt', sp, sf, [(0.5, 0.5)] * len(sp), mats['black'], worn, sw, names, rig)
    sme = skirt_ob.data
    painted(skirt_ob, [stripe[sme.loops[li].vertex_index] for poly in sme.polygons for li in poly.loop_indices])
    skirt_ob.data.materials.clear()
    skirt_ob.data.materials.append(paint_material('higa_skirt_paint', 0.84, 0))
    edges = [(smap[a], smap[b]) for a, b in boundary(faces[skirt]) if a in smap and b in smap]
    bv, bf, bw, bc = edge_strip(sp, sn, sw, edges, np.array([0, 0, -1.0]), 0.008, PALETTE['gold'] / 255)
    border = h.finish_mesh('15a skirt border', bv, bf, [(0.2, 0.8)] * len(bv), mats['gold'], worn, bw, names, rig)
    painted(border, bc.repeat(len(border.data.loops) // max(len(bc), 1) or 1, axis=0)[:len(border.data.loops)]
            if False else [bc[border.data.loops[li].vertex_index] for li in range(len(border.data.loops))])
    border.data.materials.clear()
    border.data.materials.append(paint_material('higa_gold_paint', 0.36, 0.7))

    # Bodice and pauldrons face the camera. An offset of the raw chest triangles
    # crumpled, and a sideways plate read as a spike.
    torso = names.index('UpperTorso')
    def plate_grid(samples, nu, nv, label, color, rough, metal):
        pp, pf, pu, pw = h.solid_grid(samples, nu, nv, 0.005)
        ob = h.finish_mesh(label, pp, pf, pu, mats['gold'], worn, pw, names, rig)
        painted(ob, [color] * len(ob.data.loops))
        ob.data.materials.clear()
        ob.data.materials.append(paint_material(label + ' paint', rough, metal))
        return ob
    bodice = []
    bw = np.zeros(count); bw[torso] = 1
    for v in range(5):
        row = []
        for u in range(12):
            x = -0.09 + 0.18 * u / 11
            z = 0.31 + 0.15 * v / 4
            neck = max(0, 1 - abs(x) / 0.045)
            z -= 0.045 * neck * (v / 4)
            y = 0.125 + 0.012 * math.cos(x / 0.09 * math.pi)
            row.append((np.array([x, y, z]), np.array([0, 1, 0.15]), bw))
        bodice.append(row)
    plate_grid(bodice, 12, 5, '10 bodice', (0.06, 0.05, 0.045), 0.78, 0.05)
    plate_grid([bodice[0], bodice[1]], 12, 2, '11 bodice hem', PALETTE['gold'] / 255, 0.34, 0.75)
    for side, sign, bone in (('L', -1, 'LCollarBone'), ('R', 1, 'RCollarBone')):
        samples = []
        bone_w = np.zeros(count)
        bone_w[names.index(bone)] = 0.7
        bone_w[names.index(side[0] + 'UpArm')] = 0.3
        for v in range(5):
            row = []
            for u in range(8):
                across = u / 7
                rise = v / 4
                x = sign * (0.055 + 0.155 * across)
                z = 0.38 + 0.02 * across + 0.14 * rise * (0.35 + 0.65 * across)
                y = 0.045 - 0.02 * rise
                color_n = np.array([0, 1, 0.2])
                row.append((np.array([x, y, z]), color_n, bone_w))
            samples.append(row)
        plate_grid(samples, 8, 5, f'14 pauldron {side}', PALETTE['gold'] / 255, 0.34, 0.8)
        plate_grid([samples[-1], [(p + np.array([sign * 0.01, 0, 0.012]), n, w) for p, n, w in samples[-1]]],
                   8, 2, f'14b rim {side}', (0.08, 0.07, 0.06), 0.7, 0.1)

    # Front waist plates only, clamped inside the hip so they cannot reach the arms.
    tree = BVHTree.FromPolygons(points.tolist(), [tuple(t) for t in faces], all_triangles=True)
    h.tree_points = points
    for i, z in enumerate(np.linspace(0.175, 0.055, 5)):
        row_a, row_b = [], []
        for a in np.linspace(-1.05, 1.05, 16):
            outward = Vector((math.sin(a), math.cos(a), 0))
            origin = Vector((0, 0.02, z)) + outward * 0.28
            hit, normal, ti, dist = tree.ray_cast(origin, -outward, 0.25)
            if hit is None or abs(hit.x) > 0.145 or hit.y < 0.02:
                hit = Vector((0.11 * math.sin(a), 0.085 * math.cos(a), z))
                w = weights[int(np.argmin(np.linalg.norm(points - np.array(hit), axis=1)))]
            else:
                w = h.face_weight(hit, faces[ti], points, weights)
            base = np.array(hit) + np.array(outward) * 0.006
            row_a.append((base + np.array([0, 0, -0.006]), np.array(outward), w))
            row_b.append((base + np.array([0, 0, 0.006]), np.array(outward), w))
        pp, pf, pu, pw = h.solid_grid([row_a, row_b], 16, 2, 0.003)
        plate = h.finish_mesh(f'13 waist {i}', pp, pf, pu, mats['silver'], worn, pw, names, rig)
        tint = PALETTE['gold'] / 255 if i == 0 else PALETTE['silver'] / 255
        painted(plate, [tint] * len(plate.data.loops))
        plate.data.materials.clear()
        plate.data.materials.append(paint_material(f'higa_plate_{i}', 0.3, 0.8))

    def ring(center, axis, name, radius=0.045):
        axis = axis / (np.linalg.norm(axis) + 1e-9)
        helper = np.array([0, 0, 1.0]) if abs(axis[2]) < 0.9 else np.array([1, 0, 0.0])
        u = np.cross(axis, helper); u /= np.linalg.norm(u); v = np.cross(axis, u)
        samples = []
        for dz in (-0.007, 0.007):
            row = []
            for a in np.linspace(0, math.tau, 14, endpoint=False):
                outward = math.cos(a) * u + math.sin(a) * v
                p = center + axis * dz + outward * radius
                row.append((p, outward, weights[int(np.argmin(np.linalg.norm(points - p, axis=1)))]))
            row.append(row[0])
            samples.append(row)
        pp, pf, pu, pw = h.solid_grid(samples, len(samples[0]), 2, 0.003)
        ob = h.finish_mesh(name, pp, pf, pu, mats['gold'], worn, pw, names, rig)
        painted(ob, [PALETTE['gold'] / 255] * len(ob.data.loops))
        ob.data.materials.clear()
        ob.data.materials.append(paint_material(name + ' paint', 0.34, 0.75))
    for sign, up, low in ((-1, np.array([-0.166, 0.427, 0.016]), np.array([-0.234, 0.194, 0.028])),
                          (1, np.array([0.161, 0.426, 0.016]), np.array([0.240, 0.195, 0.027]))):
        up_b, low_b = h.C @ Vector(up), h.C @ Vector(low)
        ring(np.array(up_b.lerp(low_b, 0.38)), np.array(low_b - up_b), f'17 armband {sign}')
        ring(np.array([sign * 0.098, 0.01, -0.18]), np.array([0, 0, 1.0]), f'16 boot cuff {sign}', 0.055)

    # Back straps follow the open back, above the skirt.
    for label, x0, x1 in (('a', -0.05, 0.06), ('b', 0.05, -0.06)):
        samples = []
        for t in np.linspace(0, 1, 8):
            z = 0.43 - 0.22 * t
            x = x0 + (x1 - x0) * t
            origin = Vector((x, -0.22, z))
            hit, normal, ti, dist = tree.ray_cast(origin, Vector((0, 1, 0)), 0.35)
            if hit is None:
                hit = Vector((x, -0.07, z))
                w = weights[0]
            else:
                w = h.face_weight(hit, faces[ti], points, weights)
            outward = np.array([0, -1, 0.0])
            samples.append([(np.array(hit) + outward * 0.004 + np.array([-0.005, 0, 0]), outward, w),
                            (np.array(hit) + outward * 0.004 + np.array([0.005, 0, 0]), outward, w)])
        pp, pf, pu, pw = h.solid_grid(samples, 2, 8, 0.003)
        strap = h.finish_mesh('18 strap ' + label, pp, pf, pu, mats['red'], worn, pw, names, rig)
        painted(strap, [PALETTE['red'] / 255] * len(strap.data.loops))
        strap.data.materials.clear()
        strap.data.materials.append(paint_material('higa_strap_' + label, 0.78, 0))

    def attached(kind, hp, bone, label):
        data = h.load(kind)
        m = h.C4 @ __import__('mathutils').Matrix((np.array(body['hardpoints'][hp]['matrix'])
            @ np.linalg.inv(np.array(data['hardpoints'][hp]['matrix']))).tolist())
        ps = [m @ Vector(p) for p in data['points']]
        fs = [tuple(f) for g in data['groups'] for f in g['faces']]
        w = np.zeros((len(ps), count)); w[:, names.index(bone)] = 1
        mesh = bpy.data.meshes.new(label)
        mesh.from_pydata(ps, [], fs); mesh.update()
        ob = bpy.data.objects.new(label, mesh); parts.objects.link(ob)
        layer = mesh.uv_layers.new(name='Native UV')
        for poly in mesh.polygons:
            poly.use_smooth = True
            for li in poly.loop_indices:
                layer.data[li].uv = data['uv'][mesh.loops[li].vertex_index]
        for group in data['groups']:
            slot = bpy.data.materials.new(group['name'] + ' native')
            slot.use_nodes = True
            slot.use_backface_culling = True
            if group['texture']:
                tex = slot.node_tree.nodes.new('ShaderNodeTexImage')
                tex.image = bpy.data.images.load(group['texture'], check_existing=True)
                slot.node_tree.links.new(tex.outputs['Color'], slot.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
            mesh.materials.append(slot)
        start = 0
        for group in data['groups']:
            for poly in mesh.polygons[start:start + len(group['faces'])]:
                poly.material_index = mesh.materials.find(group['name'] + ' native')
            start += len(group['faces'])
        h.add_skin(ob, w, names, rig)
    attached('head', 'hp_head', 'Body_Head', 'head — native unchanged')
    attached('left_hand', 'hp_left b', 'LHand', 'left hand — native unchanged')
    attached('right_hand', 'hp_right b', 'RHand', 'right hand — native unchanged')

    blend = OUT / 'higa_step_02.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
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
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1200
    scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.13, 0.13, 0.13, 1)
    scene.view_settings.view_transform = 'AgX'
    for loc, power in (((-2.5, 3.5, 2.2), 400), ((2.5, 2, 1.5), 220), ((0.4, -3.5, 2), 380)):
        ld = bpy.data.lights.new('Softbox', 'AREA'); ld.energy = power; ld.size = 2.5
        ob = bpy.data.objects.new(ld.name, ld); scene.collection.objects.link(ob); ob.location = loc
        ob.rotation_euler = (Vector((0, 0, 0.1)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera')); scene.collection.objects.link(cam)
    scene.camera = cam; cam.data.type = 'ORTHO'; cam.data.ortho_scale = 2.15
    preview = OUT / 'preview'; preview.mkdir(exist_ok=True)
    for label, loc in (('front', (0, 3.2, 0.05)), ('back', (0, -3.2, 0.05)), ('side', (3.2, 0, 0.05))):
        cam.location = loc
        cam.rotation_euler = (Vector((0, 0, 0.05)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    print('STEP02', blend, 'skirt_faces', int(len(skirt)), 'chest_faces', int(len(chest)))


if __name__ == '__main__':
    main()
