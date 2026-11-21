"""Fit the Higa Meshy mesh onto the Kaitlyn skeleton the way the alien was rigged.

The mesh and its texture stay. Limb centerlines move onto the native joints;
transverse radii stay. No costume plates, no game install.
"""
import gzip
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
ART = Path('D:/work/MESHY/higa1')
TOP = ROOT / 'out/character_rounding/higa'
OUT = TOP / 'rigged'
GROUND = 0.96956336
C = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))


def smooth(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    result = {k: v * (1 - t) for k, v in a.items()}
    for k, v in b.items():
        result[k] = result.get(k, 0) + v * t
    return result


def load_skeleton():
    data = json.loads(gzip.decompress((TOP / 'source/body.json.gz').read_bytes()))
    joints = {}
    for bone in data['bones']:
        packed = np.array(bone['native_bind'])
        inverse = np.eye(4)
        inverse[:3, :3] = packed[:9].reshape(3, 3)
        inverse[:3, 3] = packed[9:]
        game = np.linalg.inv(inverse)[:3, 3]
        joints[bone['name']] = C @ Vector(game) + Vector((0, 0, GROUND))
    return data, joints


def orient(ob):
    pts = np.array([v.co[:] for v in ob.data.vertices])
    extent = pts.max(0) - pts.min(0)
    up = int(np.argmax(extent))
    lateral = int(np.argmax(np.where(np.arange(3) == up, -1, extent)))
    forward = ({0, 1, 2} - {up, lateral}).pop()
    axis = pts[:, up]
    low = axis < np.percentile(axis, 12)
    high = axis > np.percentile(axis, 88)
    # Feet are the bimodal end. A single head cluster is the other end.
    def split(mask):
        values = pts[mask, lateral]
        return float(np.percentile(values, 90) - np.percentile(values, 10))
    if split(high) > split(low):
        up_sign = -1
    else:
        up_sign = 1
    z = up_sign * pts[:, up]
    feet = z < np.percentile(z, 8)
    calves = (z > np.percentile(z, 14)) & (z < np.percentile(z, 28))
    toe = pts[feet, forward].mean() - pts[calves, forward].mean()
    forward_sign = 1 if toe >= 0 else -1
    # Target: X lateral, Y front, Z up.
    src = np.zeros((len(pts), 3))
    src[:, 0] = pts[:, lateral]
    src[:, 1] = forward_sign * pts[:, forward]
    src[:, 2] = up_sign * pts[:, up]
    src[:, 2] -= src[:, 2].min()
    return src, {'up': up, 'lateral': lateral, 'forward': forward, 'up_sign': up_sign, 'forward_sign': forward_sign}


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.import_scene.fbx(filepath=str(next(ART.glob('*.fbx'))))
    for image in bpy.data.images:
        candidate = ART / Path(image.filepath.replace('\\', '/')).name
        if candidate.exists():
            image.filepath = str(candidate)
            image.reload()
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert meshes, 'Meshy FBX has no mesh'
    bpy.ops.object.select_all(action='DESELECT')
    for ob in meshes:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    if len(meshes) > 1:
        bpy.ops.object.join()
    body = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for mod in list(body.modifiers):
        if mod.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    oriented, axes = orient(body)
    for v, p in zip(body.data.vertices, oriented):
        v.co = p
    body.data.update()
    skeleton, joints = load_skeleton()
    names = [b['name'] for b in skeleton['bones']]
    indices = {n: i for i, n in enumerate(names)}
    original = np.array([v.co[:] for v in body.data.vertices])
    height = float(original[:, 2].max())
    target_top = float(joints['Body_Head'].z) + 0.20
    scale = target_top / height
    original *= scale
    for v, p in zip(body.data.vertices, original):
        v.co = p
    # Center the torso on X without moving the pose's left/right identity.
    hip = original[:, 2] < joints['LowerTorso'].z
    original[:, 0] -= original[hip, 0].mean()

    def radius_at(z0, band=0.04):
        sl = original[np.abs(original[:, 2] - z0) < band]
        if len(sl) < 20:
            return 0.1
        return float(np.percentile(np.abs(sl[:, 0]), 90))

    z = original[:, 2]
    # Source landmarks from the scaled mesh, monotonic from feet to crown.
    zsource = [0, height * scale * .08, height * scale * .32, height * scale * .52,
               height * scale * .62, height * scale * .72, height * scale * .78,
               height * scale * .84, height * scale * .90, height * scale]
    ztarget = [0, joints['RFoot'].z, joints['RLowLeg'].z, joints['RThigh'].z,
               joints['LowerTorso'].z, joints['UpperTorso'].z, joints['RUpArm'].z,
               joints['Body_Neck'].z, joints['Body_Head'].z, target_top]
    # Arms: lateral components below the shoulder, grown through real edges.
    neighbors = [set() for _ in original]
    for edge in body.data.edges:
        a, b = edge.vertices
        neighbors[a].add(b)
        neighbors[b].add(a)
    shoulder_z = height * scale * .78
    eligible = z < shoulder_z
    seen, arm = set(), np.zeros(len(original))
    seeds = np.flatnonzero(eligible & (np.abs(original[:, 0]) > radius_at(shoulder_z) + 0.06))
    for start in seeds:
        if start in seen:
            continue
        todo, comp = [int(start)], []
        seen.add(start)
        while todo:
            i = todo.pop()
            comp.append(i)
            for j in neighbors[i]:
                if eligible[j] and j not in seen:
                    seen.add(j)
                    todo.append(j)
        pts = original[comp]
        if len(comp) > 80 and abs(pts[:, 0].mean()) > 0.18 and pts[:, 2].min() > height * scale * .35:
            arm[comp] = 1
    edges = np.array([tuple(e.vertices) for e in body.data.edges])
    u = np.concatenate((edges[:, 0], edges[:, 1]))
    v = np.concatenate((edges[:, 1], edges[:, 0]))
    conductance = 1 / np.maximum(np.linalg.norm(original[u] - original[v], axis=1), 0.001)
    den = np.bincount(u, weights=conductance, minlength=len(original))
    fixed = arm > 0
    for _ in range(80):
        average = np.bincount(u, weights=conductance * arm[v], minlength=len(original)) / np.maximum(den, 1e-9)
        arm[~fixed] = average[~fixed]
        arm[z > shoulder_z + 0.05] = 0

    weights = np.zeros((len(original), len(names)))
    fitted = []
    for i, p in enumerate(original):
        x, y, zz = p
        side = 'R' if x >= 0 else 'L'
        ax = abs(x)
        leg = 1 - smooth(joints['RThigh'].z - 0.04, joints['LowerTorso'].z, zz)
        if zz > joints['RFoot'].z:
            leg *= smooth(0.03, 0.09, ax)
        arm_w = float(arm[i])
        torso = mix({'MAXRoot': 1}, {'LowerTorso': 1}, smooth(joints['RThigh'].z, joints['LowerTorso'].z + 0.04, zz))
        torso = mix(torso, {'UpperTorso': 1}, smooth(joints['LowerTorso'].z, joints['UpperTorso'].z, zz))
        torso = mix(torso, {'Spine3': 1}, smooth(joints['UpperTorso'].z, joints['Spine3'].z, zz))
        neck = mix({'Spine3': 1}, {'Body_Neck': 1}, smooth(joints['Spine3'].z, joints['Body_Neck'].z, zz))
        neck = mix(neck, {'Body_Head': 1}, smooth(joints['Body_Neck'].z, joints['Body_Head'].z + 0.04, zz))
        torso = mix(torso, neck, smooth(joints['UpperTorso'].z, joints['Spine3'].z, zz))
        lw = mix({side + 'Foot': 1}, {side + 'LowLeg': 1}, smooth(joints['RFoot'].z, joints['RLowLeg'].z - 0.08, zz))
        lw = mix(lw, {side + 'Thigh': 1}, smooth(joints['RLowLeg'].z, joints['RThigh'].z - 0.06, zz))
        hand_z = joints[side + 'Hand'].z
        elbow_z = joints[side + 'LowArm'].z
        shoulder = joints[side + 'UpArm'].z
        aw = mix({side + 'Hand': 1}, {side + 'LowArm': 1}, smooth(hand_z, elbow_z - 0.05, zz))
        aw = mix(aw, {side + 'UpArm': 1}, smooth(elbow_z, shoulder - 0.04, zz))
        w = mix(mix(torso, lw, leg * (1 - arm_w)), aw, arm_w)
        for name, value in w.items():
            weights[i, indices[name]] = value
        q = p.copy()
        q[2] = float(np.interp(zz, zsource, ztarget))
        src_leg = np.array([
            np.sign(x) * np.interp(zz, [zsource[1], zsource[2], zsource[3]], [0.10, 0.11, 0.12]),
            np.interp(zz, [zsource[1], zsource[2], zsource[3]], [0.02, 0.0, 0.0]), q[2]])
        dst_leg = np.array([
            np.interp(zz, [zsource[1], zsource[2], zsource[3]], [joints[side + 'Foot'].x, joints[side + 'LowLeg'].x, joints[side + 'Thigh'].x]),
            np.interp(zz, [zsource[1], zsource[2], zsource[3]], [joints[side + 'Foot'].y, joints[side + 'LowLeg'].y, joints[side + 'Thigh'].y]), q[2]])
        q[:2] += (dst_leg - src_leg)[:2] * leg * (1 - arm_w)
        src_arm = np.array([
            np.sign(x) * np.interp(zz, [zsource[4], zsource[5], zsource[6]], [0.28, 0.24, 0.20]),
            0, 0])
        dst_arm = np.array([
            np.interp(zz, [zsource[4], zsource[5], zsource[6]], [joints[side + 'Hand'].x, joints[side + 'LowArm'].x, joints[side + 'UpArm'].x]),
            np.interp(zz, [zsource[4], zsource[5], zsource[6]], [joints[side + 'Hand'].y, joints[side + 'LowArm'].y, joints[side + 'UpArm'].y]), 0])
        q[:2] += (dst_arm - src_arm)[:2] * arm_w
        fitted.append(q)
    fitted = np.array(fitted)
    # Meshy is a T-pose. The alien fit moves that centerline onto the hanging joints.
    shoulder_line = height * scale * 0.78
    arm[:] = 0
    arm_seed = (np.abs(original[:, 2] - shoulder_line) < 0.14) & (np.abs(original[:, 0]) > 0.36)
    seen = set()
    for start in np.flatnonzero(arm_seed):
        if int(start) in seen:
            continue
        todo, comp = [int(start)], []
        seen.add(int(start))
        while todo:
            i = todo.pop()
            comp.append(i)
            for j in neighbors[i]:
                if j in seen:
                    continue
                if abs(original[j, 0]) > 0.17 and shoulder_line - 0.10 < original[j, 2] < shoulder_line + 0.08:
                    seen.add(j)
                    todo.append(j)
        if len(comp) > 80 and abs(original[comp, 0].mean()) > 0.3:
            arm[comp] = 1

    def bone_frame(a, b):
        along = b - a
        length = float(np.linalg.norm(along))
        along = along / max(length, 1e-8)
        side = np.cross(along, (0, 0, 1))
        if np.linalg.norm(side) < 1e-4:
            side = np.cross(along, (0, 1, 0))
        side = side / np.linalg.norm(side)
        up = np.cross(side, along)
        return along, side, up

    for sign, side in ((1, 'R'), (-1, 'L')):
        member = np.flatnonzero((arm > 0.5) & (np.sign(original[:, 0]) == sign))
        if len(member) < 50:
            continue
        hand_x = float(np.percentile(np.abs(original[member, 0]), 98))
        root_x = 0.22
        length = max(hand_x - root_x, 0.05)
        center_y = float(np.median(original[member, 1]))
        center_z = float(np.median(original[member, 2]))
        chain = [np.array(joints[side + n]) for n in ('UpArm', 'LowArm', 'Hand')]
        for i in member:
            t = float(np.clip((abs(original[i, 0]) - root_x) / length, 0, 1))
            if t < 0.48:
                u = t / 0.48
                a, b = chain[0], chain[1]
            else:
                u = (t - 0.48) / 0.52
                a, b = chain[1], chain[2]
            along, side_axis, up_axis = bone_frame(a, b)
            center = a * (1 - u) + b * u
            offset_y = original[i, 1] - center_y
            offset_z = original[i, 2] - center_z
            fitted[i] = center + side_axis * offset_y + up_axis * offset_z
            if t < 0.15:
                w = {side + 'UpArm': 0.7, side + 'CollarBone': 0.3}
            elif t < 0.48:
                w = {side + 'UpArm': 1 - (t - 0.15) / 0.33, side + 'LowArm': (t - 0.15) / 0.33}
            elif t < 0.86:
                w = {side + 'LowArm': 1}
            else:
                w = {side + 'LowArm': 1 - (t - 0.86) / 0.14, side + 'Hand': (t - 0.86) / 0.14}
            weights[i] = 0
            for name, value in w.items():
                weights[i, indices[name]] = value
    for i, w in enumerate(weights):
        keep = np.argsort(w)[-4:]
        mask = np.zeros(len(w))
        mask[keep] = w[keep]
        mask[mask < 0.002] = 0
        total = mask.sum()
        weights[i] = mask / total if total else mask
    for v, p in zip(body.data.vertices, fitted):
        v.co = p
    body.data.update()
    body.name = 'Higa - skinned Meshy mesh'

    arm_count = int((arm > 0.5).sum())
    armature = bpy.data.armatures.new('br_kaitlyn_body native skeleton')
    rig = bpy.data.objects.new('RIG - br_kaitlyn_body', armature)
    bpy.context.collection.objects.link(rig)
    bpy.ops.object.select_all(action='DESELECT')
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    for bone in skeleton['bones']:
        edit = armature.edit_bones.new(bone['name'])
        packed = np.array(bone['native_bind'], float)
        game = np.eye(4)
        game[:3, :3] = packed[:9].reshape(3, 3)
        game[:3, 3] = packed[9:]
        bind = np.linalg.inv(game)
        m = C.to_4x4() @ Matrix(bind.tolist())
        m.translation = joints[bone['name']]
        edit.matrix = m
        edit.length = 0.065
    for bone in skeleton['bones']:
        if bone['parent']:
            armature.edit_bones[bone['name']].parent = armature.edit_bones[bone['parent']]
    bpy.ops.object.mode_set(mode='OBJECT')
    rig.show_in_front = True
    for bone in skeleton['bones']:
        armature.bones[bone['name']]['native_inverse_bind'] = bone['native_bind']
    for name in names:
        body.vertex_groups.new(name=name)
    for i, w in enumerate(weights):
        for j in np.flatnonzero(w):
            body.vertex_groups[names[j]].add([i], float(w[j]), 'REPLACE')
    mod = body.modifiers.new('Native Kaitlyn skin - linear blend', 'ARMATURE')
    mod.object = rig
    mod.use_deform_preserve_volume = False
    body.parent = rig

    def pose(frame, rotations):
        for bone in rig.pose.bones:
            bone.rotation_mode = 'QUATERNION'
            bone.rotation_quaternion = Quaternion((1, 0, 0, 0))
        for name, axis, degrees in rotations:
            bone = rig.pose.bones[name]
            local = armature.bones[name].matrix_local.to_3x3().inverted() @ Vector(axis)
            bone.rotation_quaternion = Quaternion(local, math.radians(degrees))
        for bone in rig.pose.bones:
            bone.keyframe_insert('rotation_quaternion', frame=frame)

    scene = bpy.context.scene
    pose(1, [])
    pose(30, [('LLowArm', (1, 0, 0), 65), ('RLowArm', (1, 0, 0), 45)])
    pose(60, [('LThigh', (1, 0, 0), 25), ('LLowLeg', (1, 0, 0), -50)])
    pose(90, [])
    scene.frame_start = 1
    scene.frame_end = 90
    scene.frame_set(1)
    assert np.isfinite(fitted).all() and np.max(np.abs(weights.sum(1) - 1)) < 1e-5
    assert (np.sum(weights > 0, 1) <= 4).all()
    blend = OUT / 'higa_kaitlyn_rigged.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
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
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1100
    scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.14, 0.14, 0.14, 1)
    scene.view_settings.view_transform = 'AgX'
    for loc, power in (((-2.4, 3.2, 2.2), 380), ((2.2, 1.2, 1.6), 200), ((0.2, -3.4, 2.0), 320)):
        ld = bpy.data.lights.new('Softbox', 'AREA')
        ld.energy = power
        ld.size = 2.4
        lamp = bpy.data.objects.new(ld.name, ld)
        scene.collection.objects.link(lamp)
        lamp.location = loc
        lamp.rotation_euler = (Vector((0, 0, 0.85)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.05
    preview = OUT / 'preview'
    preview.mkdir(exist_ok=True)
    for label, frame, loc in (('rest_front', 1, (0, 4.5, 0.85)), ('rest_side', 1, (4.5, 0, 0.85)),
                              ('rest_back', 1, (0, -4.5, 0.85)), ('elbows', 30, (0, 4.5, 0.85))):
        scene.frame_set(frame)
        cam.location = loc
        cam.rotation_euler = (Vector((0, 0, 0.85)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    scene.frame_set(1)
    np.savez_compressed(OUT / 'binding.npz', positions=fitted, weights=weights, bone_names=np.array(names))
    report = {
        'method': 'alien rig fit, not Hassler panels',
        'mesh': body.name,
        'vertices': len(body.data.vertices),
        'scale': scale,
        'axes': axes,
        'arm_vertices': arm_count,
        'installed': False,
        'blend': str(blend),
    }
    (OUT / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report))


if __name__ == '__main__':
    main()
