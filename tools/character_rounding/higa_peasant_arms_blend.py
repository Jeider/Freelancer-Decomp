"""Place rounded peasant sleeves on Higa. Shape and skeleton scale stay native."""
import json
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
TOP = ROOT / 'out/character_rounding/higa'
SRC = TOP / 'kym_arms/higa_kym_arms.blend'
OUT = TOP / 'peasant_arms'
GROUND = 0.96956336


def game_to_bl(p):
    return (float(p[0]), float(-p[2]), float(p[1] + GROUND))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    rig = body.parent
    for ob in list(bpy.data.objects):
        if ob.type == 'MESH' and ob is not body:
            bpy.data.objects.remove(ob, do_unlink=True)
    arms = np.load(OUT / 'arms.npz')
    materials = json.loads((OUT / 'materials.json').read_text(encoding='utf8'))
    me = bpy.data.meshes.new('peasant sleeves')
    me.from_pydata([game_to_bl(p) for p in arms['points']], [], arms['faces'].tolist())
    me.update()
    uv = me.uv_layers.new(name='Native UV')
    for poly in me.polygons:
        poly.use_smooth = True
        poly.material_index = int(arms['face_material'][poly.index])
        for li in poly.loop_indices:
            uv.data[li].uv = arms['uv'][me.loops[li].vertex_index]
    for mat in materials:
        slot = bpy.data.materials.new(mat['name'])
        slot.use_nodes = True
        slot.use_backface_culling = True
        if mat['texture']:
            tex = slot.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image = bpy.data.images.load(mat['texture'], check_existing=True)
            slot.node_tree.links.new(tex.outputs['Color'], slot.node_tree.nodes['Principled BSDF'].inputs['Base Color'])
        me.materials.append(slot)
    sleeves = bpy.data.objects.new('pl_female1 sleeves', me)
    bpy.context.collection.objects.link(sleeves)
    bone_names = [str(n) for n in arms['bone_names']]
    for name in bone_names:
        sleeves.vertex_groups.new(name=name)
    for i, row in enumerate(arms['weights']):
        for j in np.flatnonzero(row > 0.001):
            sleeves.vertex_groups[j].add([i], float(row[j]), 'REPLACE')
    bpy.context.view_layer.objects.active = sleeves
    sleeves.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode='OBJECT')
    skin = sleeves.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
    skin.object = rig
    skin.use_deform_preserve_volume = False
    sleeves.parent = rig
    # Pauldron lip only, 1.5 cm above the native sleeve top.
    raised = 0
    for v in body.data.vertices:
        if 1.42 < v.co.z < 1.50 and 0.15 < abs(v.co.x) < 0.26 and abs(v.co.y) < 0.06:
            v.co.z += 0.015
            raised += 1
    body.data.update()
    print('pauldron lip', raised, 'sleeve verts', len(sleeves.data.vertices))
    blend = OUT / 'higa_peasant_arms.blend'
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
    scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.14, 0.14, 0.14, 1)
    scene.view_settings.view_transform = 'AgX'
    for loc, power in (((-2.2, 3.2, 2.4), 340), ((2.4, 1.4, 1.8), 180)):
        ld = bpy.data.lights.new('Softbox', 'AREA')
        ld.energy = power
        ld.size = 2.2
        lamp = bpy.data.objects.new(ld.name, ld)
        scene.collection.objects.link(lamp)
        lamp.location = loc
        lamp.rotation_euler = (Vector((0, 0, 0.9)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    preview = OUT / 'preview'
    preview.mkdir(exist_ok=True)
    for label, loc, scale in (
            ('front', (0, 3.4, 1.15), 1.15),
            ('side', (3.4, 0.15, 1.15), 1.15),
            ('shoulder', (0.7, 1.5, 1.40), 0.48)):
        cam.location = loc
        cam.data.ortho_scale = scale
        cam.rotation_euler = (Vector((0.12 if label == 'shoulder' else 0, 0, 1.15)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    print('BLEND', blend)


if __name__ == '__main__':
    main()
