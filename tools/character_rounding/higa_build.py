"""Higa step 01: Kaitlyn skeleton and body volume, concept costume, no installation.

Meshy geometry stays an archived reference. The worn surface uses Kaitlyn's
cloth weave and head skin, recolored to the concept, because the Meshy atlas
is an island dump and cannot read as a Freelancer DcDt costume.
"""
import gzip
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
TOP = ROOT / 'out/character_rounding/higa'
OUT = TOP / 'step_01'
TEX = OUT / 'textures'
ART = Path('D:/work/MESHY/higa1')
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
C4 = C.to_4x4()


def load(kind):
    return json.loads(gzip.decompress((TOP / 'source' / (kind + '.json.gz')).read_bytes()))


def game_to_bl(p):
    return C @ Vector(p)


def collection(name, hide=False):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    col.hide_viewport = hide
    col.hide_render = hide
    return col


def activate(ob):
    bpy.ops.object.select_all(action='DESELECT')
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob


def bindings(data):
    result = []
    for bone in data['bones']:
        packed = np.array(bone['native_bind'])
        mat = np.eye(4)
        mat[:3, :3] = packed[:9].reshape(3, 3)
        mat[:3, 3] = packed[9:]
        result.append(np.linalg.inv(mat))
    return result


def material(name, texture, rough, metal):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.use_backface_culling = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    tex = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(str(TEX / texture), check_existing=True)
    mat.node_tree.links.new(tex.outputs['Color'], bs.inputs['Base Color'])
    return mat


def weight_row(raw, count):
    row = np.zeros(count)
    for key, value in raw.items():
        row[int(key)] = value
    return row


def limit4(row):
    row = np.array(row, dtype=float)
    row[row < 0.001] = 0
    if np.count_nonzero(row) > 4:
        row[np.argsort(row)[:-4]] = 0
    total = row.sum()
    return row / total if total else row


def add_skin(ob, weights, names, rig):
    for name in names:
        ob.vertex_groups.new(name=name)
    for i, row in enumerate(weights):
        for j in np.flatnonzero(row > 0):
            ob.vertex_groups[j].add([i], float(row[j]), 'REPLACE')
    mod = ob.modifiers.new('Native linear skin', 'ARMATURE')
    mod.object = rig
    mod.use_deform_preserve_volume = False
    ob.parent = rig


def rig_native(data, col):
    arm = bpy.data.armatures.new('br_kaitlyn_body native skeleton')
    rig = bpy.data.objects.new('RIG — native Bretonia female', arm)
    col.objects.link(rig)
    activate(rig)
    bpy.ops.object.mode_set(mode='EDIT')
    for bone, mat in zip(data['bones'], bindings(data)):
        edit = arm.edit_bones.new(bone['name'])
        edit.length = 0.065
        edit.matrix = C4 @ Matrix(mat.tolist())
    for bone in data['bones']:
        if bone['parent'] and bone['parent'] in arm.edit_bones:
            arm.edit_bones[bone['name']].parent = arm.edit_bones[bone['parent']]
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True
    rig.display_type = 'WIRE'
    arm.display_type = 'STICK'
    for bone in data['bones']:
        arm.bones[bone['name']]['native_inverse_bind'] = bone['native_bind']
    return rig


def finish_mesh(name, points, faces, uvs, mat, col, weights, names, rig):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(p) for p in points], [], faces)
    me.update()
    ob = bpy.data.objects.new(name, me)
    col.objects.link(ob)
    me.materials.append(mat)
    layer = me.uv_layers.new(name='Garment UV')
    for poly in me.polygons:
        poly.use_smooth = True
        for li in poly.loop_indices:
            layer.data[li].uv = uvs[me.loops[li].vertex_index]
    add_skin(ob, weights, names, rig)
    return ob


def solid_grid(samples, nu, nv, thickness):
    """samples[v][u] = (point, outward, weight). Returns outer+inner shell."""
    points, weights, uvs, faces = [], [], [], []
    index = {}

    def add(p, w, uv):
        key = tuple(np.round(p, 5))
        if key in index:
            return index[key]
        index[key] = len(points)
        points.append(p)
        weights.append(limit4(w))
        uvs.append(uv)
        return index[key]

    outer = [[None] * nu for _ in range(nv)]
    for v in range(nv):
        for u in range(nu):
            p, n, w = samples[v][u]
            outer[v][u] = add(p + n * thickness * 0.5, w, ((u + .5) / nu, (v + .5) / nv))
    for v in range(nv - 1):
        for u in range(nu - 1):
            a, b = outer[v][u], outer[v][u + 1]
            c, d = outer[v + 1][u + 1], outer[v + 1][u]
            faces += [(a, b, c), (a, c, d)]
    inner = [[None] * nu for _ in range(nv)]
    for v in range(nv):
        for u in range(nu):
            p, n, w = samples[v][u]
            inner[v][u] = add(p - n * thickness * 0.5, w, ((u + .5) / nu, (v + .5) / nv))
    for v in range(nv - 1):
        for u in range(nu - 1):
            a, b = inner[v][u], inner[v][u + 1]
            c, d = inner[v + 1][u + 1], inner[v + 1][u]
            faces += [(a, c, b), (a, d, c)]
    return points, faces, uvs, np.array(weights)


def face_weight(hit, tri, points, weights):
    p = [Vector(points[i]) for i in tri]
    area = np.array([
        (p[1] - p[0]).cross(p[2] - p[0]).length,
        (p[2] - p[1]).cross(p[0] - p[1]).length,
        (p[0] - p[2]).cross(p[1] - p[2]).length,
    ])
    # Barycentric from projected areas of the three opposite triangles.
    b = np.array([
        (p[1] - Vector(hit)).cross(p[2] - Vector(hit)).length,
        (p[2] - Vector(hit)).cross(p[0] - Vector(hit)).length,
        (p[0] - Vector(hit)).cross(p[1] - Vector(hit)).length,
    ])
    if b.sum() < 1e-8:
        b = np.ones(3)
    b /= b.sum()
    return limit4(b @ weights[list(tri)])


# Filled after the body mesh exists.
tree_points = None


def sample_ring(tree, faces, points, weights, z, arc0, arc1, nu, push):
    row = []
    for u, a in enumerate(np.linspace(arc0, arc1, nu)):
        outward = Vector((math.sin(a), math.cos(a), 0))
        origin = Vector((0, 0, z)) + outward * 0.55
        hit, normal, ti, dist = tree.ray_cast(origin, -outward, 0.8)
        if hit is None:
            hit, normal, ti, dist = tree.find_nearest(Vector((0, 0, z)) + outward * 0.12)
        if hit is None:
            hit = outward * 0.14
            hit.z = z
            w = weights.mean(0)
        else:
            w = face_weight(hit, faces[ti], points, weights)
        row.append((np.array(hit) + np.array(outward) * push, np.array(outward), limit4(w)))
    return row


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    body = load('body')
    names = [b['name'] for b in body['bones']]
    count = len(names)
    rigcol = collection('RIG — native Bretonia female')
    worn = collection('EDIT — Higa costume')
    parts = collection('REFERENCE — native head and hands')
    archive = collection('ARCHIVE — native body (disabled)', hide=True)
    rig = rig_native(body, rigcol)

    mats = {
        'skin': material('higa_skin', 'higa_skin.png', 0.62, 0),
        'black': material('higa_black_cloth', 'higa_black.png', 0.88, 0),
        'red': material('higa_red_cloth', 'higa_red.png', 0.82, 0),
        'gold': material('higa_gold', 'higa_gold.png', 0.38, 0.75),
        'silver': material('higa_silver', 'higa_silver.png', 0.32, 0.82),
        'boot': material('higa_boot', 'higa_boot.png', 0.42, 0.12),
    }
    points = np.array([game_to_bl(p) for p in body['points']])
    normals = np.array([game_to_bl(n) for n in body['normals']])
    weights = np.array([weight_row(s, count) for s in body['skin']])
    faces = [tuple(t) for g in body['groups'] for t in g['faces']]
    global tree_points
    tree_points = points
    tree = BVHTree.FromPolygons(points.tolist(), faces, all_triangles=True)

    def region(i):
        c = points[list(faces[i])].mean(0)
        x, y, z = c
        if z < -0.16 and abs(x) < 0.18:
            return 'boot'
        if -0.28 < z < 0.12 and abs(x) > 0.105 and abs(x) < 0.20 and abs(y) < 0.16:
            return 'black'
        if 0.0 < z < 0.14 and abs(x) < 0.11 and y > -0.02:
            return 'red'
        if z > 0.39 and 0.06 < abs(x) < 0.22:
            return 'gold'
        return 'skin'

    buckets = {k: [] for k in mats}
    for i, face in enumerate(faces):
        buckets[region(i)].append(face)
    # One object per worn region so materials stay simple and culling is honest.
    uvs = [(0.35 + p[0] * 1.4, 0.2 + p[2] * 0.8) for p in points]
    for key, group in buckets.items():
        if group:
            finish_mesh('00 body ' + key, points, group, uvs, mats[key], worn, weights, names, rig)

    # Rear and side skirt. Open at the front, attached on the native hip surface.
    skirt = []
    for v, z in enumerate(np.linspace(0.08, -0.26, 9)):
        skirt.append(sample_ring(tree, faces, points, weights, z, math.radians(55), math.radians(305), 28, 0.006))
    sp, sf, su, sw = solid_grid(skirt, 28, 9, 0.004)
    finish_mesh('15 rear skirt', sp, sf, su, mats['black'], worn, sw, names, rig)
    # Gold hem and side borders, plus the three concept cords.
    def ribbon(rows, mat, label, lift=0.004):
        samples = []
        for row in rows:
            samples.append([(p + n * lift, n, w) for p, n, w in row])
        if len(samples) < 2:
            return
        rp, rf, ru, rw = solid_grid(samples, len(samples[0]), len(samples), 0.003)
        finish_mesh(label, rp, rf, ru, mat, worn, rw, names, rig)
    ribbon([[row[0], row[1]] for row in skirt], mats['gold'], '15a skirt side a', 0.003)
    ribbon([[row[-2], row[-1]] for row in skirt], mats['gold'], '15b skirt side b', 0.003)
    ribbon(skirt[-2:], mats['gold'], '15c skirt hem', 0.003)
    for idx, (row, color) in enumerate(zip((2, 4, 6), ('red', 'silver', 'gold'))):
        ribbon(skirt[row:row + 2], mats[color], f'15d stripe {idx}', 0.002)

    # Five silver waist plates, front and sides only. Back stays open for the straps.
    for i, z in enumerate(np.linspace(0.185, 0.075, 5)):
        plate = [sample_ring(tree, faces, points, weights, z + dz, math.radians(-75), math.radians(75), 18, 0.008)
                 for dz in (-0.006, 0.006)]
        pp, pf, pu, pw = solid_grid(plate, 18, 2, 0.004)
        finish_mesh(f'13 waist plate {i}', pp, pf, pu, mats['silver' if i else 'gold'], worn, pw, names, rig)

    # Black bodice over the chest, stopping below the neck joint.
    bodice = []
    for v, z in enumerate(np.linspace(0.30, 0.45, 5)):
        opening = 0.22 + 0.18 * (v / 4)
        bodice.append(sample_ring(tree, faces, points, weights, z, -opening, opening, 14, 0.005))
    bp, bf, bu, bw = solid_grid(bodice, 14, 5, 0.004)
    finish_mesh('10 bodice', bp, bf, bu, mats['black'], worn, bw, names, rig)
    ribbon([bodice[0], bodice[1]], mats['gold'], '11 bodice hem')
    ribbon([[bodice[v][6], bodice[v][7]] for v in range(5)], mats['red'], '11b bodice lace')

    # Pauldrons rise above the native shoulder flaps. Old flaps remain as the shoulder volume.
    for side, sign in (('L', -1), ('R', 1)):
        samples = []
        for v in range(6):
            row = []
            rise = (v / 5) ** 1.4
            z = 0.40 + 0.15 * rise
            x0 = sign * (0.07 + 0.13 * rise)
            for u, y in enumerate(np.linspace(-0.07, 0.08, 7)):
                target = Vector((x0, y * (1 - 0.25 * rise), z))
                outward = Vector((sign, 0, 0.35)).normalized()
                hit, normal, ti, dist = tree.ray_cast(target + outward * 0.25, -outward, 0.5)
                if hit is None:
                    hit, w = target, weights[0]
                else:
                    w = face_weight(hit, faces[ti], points, weights)
                lifted = np.array(hit) + np.array((sign * 0.01 * rise, 0, 0.012 * rise))
                row.append((lifted, np.array(outward), w))
            samples.append(row)
        pp, pf, pu, pw = solid_grid(samples, 7, 6, 0.006)
        finish_mesh(f'14 pauldron {side}', pp, pf, pu, mats['gold'], worn, pw, names, rig)
        ribbon(samples[-2:], mats['black'], f'14b pauldron rim {side}', 0.002)

    # Two red back straps. They cross above the open waist, not through the skirt.
    for label, x0, x1 in (('a', -0.06, 0.07), ('b', 0.06, -0.07)):
        samples = []
        for v, t in enumerate(np.linspace(0, 1, 8)):
            z = 0.44 - 0.24 * t
            x = x0 + (x1 - x0) * t
            origin = Vector((x, -0.20, z))
            hit, normal, ti, dist = tree.ray_cast(origin, Vector((0, 1, 0)), 0.4)
            if hit is None:
                hit, w = Vector((x, -0.08, z)), weights[0]
            else:
                w = face_weight(hit, faces[ti], points, weights)
            outward = Vector((0, -1, 0))
            samples.append([
                (np.array(hit + outward * 0.004 + Vector((-0.006, 0, 0))), np.array(outward), w),
                (np.array(hit + outward * 0.004 + Vector((0.006, 0, 0))), np.array(outward), w),
            ])
        rp, rf, ru, rw = solid_grid(samples, 2, 8, 0.003)
        finish_mesh('18 back strap ' + label, rp, rf, ru, mats['red'], worn, rw, names, rig)

    # Gold arm bands and boot cuffs follow the native limbs.
    def cuff(z, x, radius, name, matname):
        samples = []
        for v, dz in enumerate((-0.008, 0.008)):
            row = []
            for u, a in enumerate(np.linspace(0, math.tau, 12, endpoint=False)):
                outward = Vector((math.cos(a), math.sin(a), 0))
                center = Vector((x, 0, z + dz))
                hit, normal, ti, dist = tree.ray_cast(center + outward * 0.2, -outward, 0.25)
                if hit is None:
                    hit, w = center + outward * radius, weights[0]
                else:
                    w = face_weight(hit, faces[ti], points, weights)
                row.append((np.array(hit) + np.array(outward) * 0.004, np.array(outward), w))
            row.append(row[0])
            samples.append(row)
        cp, cf, cu, cw = solid_grid(samples, len(samples[0]), 2, 0.003)
        finish_mesh(name, cp, cf, cu, mats[matname], worn, cw, names, rig)
    cuff(0.30, -0.17, 0.05, '17 armband L', 'gold')
    cuff(0.30, 0.17, 0.05, '17 armband R', 'gold')
    cuff(-0.18, -0.10, 0.06, '16 boot cuff L', 'gold')
    cuff(-0.18, 0.10, 0.06, '16 boot cuff R', 'gold')

    def attached(kind, hp, bone, label):
        data = load(kind)
        t = np.array(body['hardpoints'][hp]['matrix']) @ np.linalg.inv(np.array(data['hardpoints'][hp]['matrix']))
        m = C4 @ Matrix(t.tolist())
        ps = [m @ Vector(p) for p in data['points']]
        fs = [tuple(f) for g in data['groups'] for f in g['faces']]
        uv = data['uv']
        w = np.zeros((len(ps), count))
        w[:, names.index(bone)] = 1
        me = bpy.data.meshes.new(label)
        me.from_pydata(ps, [], fs)
        me.update()
        ob = bpy.data.objects.new(label, me)
        parts.objects.link(ob)
        layer = me.uv_layers.new(name='Native UV')
        for poly in me.polygons:
            poly.use_smooth = True
            for li in poly.loop_indices:
                layer.data[li].uv = uv[me.loops[li].vertex_index]
        for group in data['groups']:
            slot = bpy.data.materials.new(group['name'] + ' native')
            slot.use_nodes = True
            slot.use_backface_culling = True
            if group['texture']:
                tex = slot.node_tree.nodes.new('ShaderNodeTexImage')
                tex.image = bpy.data.images.load(group['texture'], check_existing=True)
                slot.node_tree.links.new(tex.outputs['Color'], slot.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
            me.materials.append(slot)
        # Face order matches the group walk above only when one material is used.
        # Reassign by the original group ranges so eyes and teeth keep their maps.
        start = 0
        for group in data['groups']:
            n = len(group['faces'])
            for poly in me.polygons[start:start + n]:
                poly.material_index = me.materials.find(group['name'] + ' native')
            start += n
        add_skin(ob, w, names, rig)
        ob['source_sha256'] = data['sha256']
        ob['attachment_hardpoint'] = hp
        return ob

    attached('head', 'hp_head', 'Body_Head', 'head — native unchanged')
    attached('left_hand', 'hp_left b', 'LHand', 'left hand — native unchanged')
    attached('right_hand', 'hp_right b', 'RHand', 'right hand — native unchanged')

    # Full native body, disabled in both viewport and render, for the next edit.
    native = finish_mesh('ARCHIVE native body', points, faces, uvs, mats['skin'], archive, weights, names, rig)
    native.hide_set(True)
    native.hide_render = True

    if any(ART.glob('*.fbx')):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(next(ART.glob('*.fbx'))))
        meshy = collection('ARCHIVE — Meshy reference (disabled)', hide=True)
        imported = [o for o in bpy.data.objects if o not in before and o.type == 'MESH']
        if imported:
            verts = np.array([o.matrix_world @ v.co for o in imported for v in o.data.vertices])
            lo, hi = verts.min(0), verts.max(0)
            scale = 1.55 / max(hi[2] - lo[2], 1e-6)
            for ob in imported:
                for c in list(ob.users_collection):
                    c.objects.unlink(ob)
                meshy.objects.link(ob)
                ob.scale = (scale, scale, scale)
                ob.location = (3.2, 0, -lo[2] * scale)
            meshy.hide_viewport = True
            meshy.hide_render = True

    blend = OUT / 'higa_step_01.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    prefs = bpy.context.preferences.addons['cycles'].preferences
    try:
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
        ld = bpy.data.lights.new('Softbox', 'AREA')
        ld.energy = power
        ld.size = 2.5
        ob = bpy.data.objects.new(ld.name, ld)
        scene.collection.objects.link(ob)
        ob.location = loc
        ob.rotation_euler = (Vector((0, 0, 0.1)) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.15
    preview = OUT / 'preview'
    preview.mkdir(exist_ok=True)
    shots = {}
    for label, loc in (('front', (0, 3.2, 0.05)), ('back', (0, -3.2, 0.05)), ('side', (3.2, 0, 0.05))):
        cam.location = loc
        cam.rotation_euler = (Vector((0, 0, 0.05)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
        shots[label] = str(preview / (label + '.png'))
    report = {
        'step': '01',
        'installed': False,
        'blend': str(blend),
        'skeleton': 'br_kaitlyn_body',
        'skeleton_sha256': body['sha256'],
        'head_hands': 'native, rigid hardpoint preview',
        'meshy': 'archived reference only; island atlas not used as the worn texture',
        'regions': {k: len(v) for k, v in buckets.items()},
        'previews': shots,
    }
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
