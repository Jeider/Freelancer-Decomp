"""Replace crooked Higa arms with ku_kym_body sleeves. Hands stay separate."""
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
OUT = TOP / 'kym_arms'
GROUND = 0.96956336
ARM = {'LUpArm', 'RUpArm', 'LLowArm', 'RLowArm', 'LHand', 'RHand', 'Left__hand_END', 'Right__hand_END'}


def game_to_bl(p):
    return (p[0], -p[2], p[1] + GROUND)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    rig = body.parent
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.select_all(action='DESELECT')
    body.select_set(True)
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
    arm_cols = [index[n] for n in ARM if n in index]
    points = np.array([v.co[:] for v in body.data.vertices])
    neck = rig.data.bones['Body_Neck'].head_local.z
    drop = (weights[:, arm_cols].sum(1) > 0.45) | ((points[:, 2] > neck - 0.02) & (np.abs(points[:, 0]) < 0.10)) | (points[:, 2] > neck + 0.06)
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    bmesh.ops.delete(bm, geom=[bm.verts[i] for i in np.flatnonzero(drop)], context='VERTS')
    boundary = [e for e in bm.edges if e.is_boundary and e.verts[0].co.z > neck - 0.12]
    if boundary:
        bmesh.ops.holes_fill(bm, edges=boundary, sides=0)
    if 'Higa skin cap' not in body.data.materials:
        slot = bpy.data.materials.new('Higa skin cap')
        slot.use_nodes = True
        bs = slot.node_tree.nodes.get('Principled BSDF')
        if bs:
            bs.inputs['Base Color'].default_value = (0.72, 0.50, 0.38, 1)
        body.data.materials.append(slot)
    skin_index = body.data.materials.find('Higa skin cap')
    for face in bm.faces:
        center = face.calc_center_median()
        if center.z > neck - 0.08 and abs(center.x) < 0.09:
            face.material_index = skin_index
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    mod = body.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
    mod.object = rig
    mod.use_deform_preserve_volume = False

    arms = np.load(OUT / 'arms.npz')
    materials = json.loads((OUT / 'materials.json').read_text(encoding='utf8'))
    me = bpy.data.meshes.new('ku_kym sleeves')
    verts = [game_to_bl(p) for p in arms['points']]
    me.from_pydata(verts, [], arms['faces'].tolist())
    me.update()
    layer = me.uv_layers.new(name='Native UV')
    for poly in me.polygons:
        poly.use_smooth = True
        poly.material_index = int(arms['face_material'][poly.index])
        for li in poly.loop_indices:
            layer.data[li].uv = arms['uv'][me.loops[li].vertex_index]
    for mat in materials:
        slot = bpy.data.materials.new(mat['name'])
        slot.use_nodes = True
        if mat['texture']:
            tex = slot.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = bpy.data.images.load(mat['texture'], check_existing=True)
            slot.node_tree.links.new(tex.outputs['Color'], slot.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        me.materials.append(slot)
    sleeves = bpy.data.objects.new('ku_kym sleeves — as authored', me)
    bpy.context.collection.objects.link(sleeves)
    bone_names = [str(n) for n in arms['bone_names']]
    for name in bone_names:
        sleeves.vertex_groups.new(name=name)
    for i, row in enumerate(arms['weights']):
        for j in np.flatnonzero(row > 0.001):
            sleeves.vertex_groups[j].add([i], float(row[j]), 'REPLACE')
    skin = sleeves.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
    skin.object = rig
    skin.use_deform_preserve_volume = False
    sleeves.parent = rig
    blend = OUT / 'higa_kym_arms.blend'
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
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1100
    scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.14, 0.14, 0.14, 1)
    scene.view_settings.view_transform = 'AgX'
    for loc, power in (((-2.4, 3.2, 2.2), 360), ((2.2, 1.2, 1.6), 180), ((0.2, -3.2, 2.0), 280)):
        ld = bpy.data.lights.new('Softbox', 'AREA')
        ld.energy = power
        ld.size = 2.2
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
    for label, loc in (('front', (0, 4.5, 0.85)), ('side', (4.5, 0, 0.85)), ('back', (0, -4.5, 0.85))):
        cam.location = loc
        cam.rotation_euler = (Vector((0, 0, 0.85)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    print('BLEND', blend, 'body_verts', len(body.data.vertices), 'sleeve_verts', len(me.vertices))


if __name__ == '__main__':
    main()
