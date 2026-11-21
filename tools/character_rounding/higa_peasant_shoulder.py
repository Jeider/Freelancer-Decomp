"""Cover the torn Higa shoulder and tuck the peasant sleeve under the pauldron."""
import math
import sys
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
SRC = ROOT / 'out/character_rounding/higa/peasant_arms/higa_peasant_arms.blend'
OUT = SRC


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    sleeves = bpy.data.objects['pl_female1 sleeves']
    for modifier in list(sleeves.modifiers):
        if modifier.type == 'ARMATURE':
            sleeves.modifiers.remove(modifier)
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    drop = []
    for v in bm.verts:
        if 1.30 < v.co.z < 1.50 and 0.075 < abs(v.co.x) < 0.185:
            if any(e.is_boundary for e in v.link_edges) or v.co.z > 1.40:
                drop.append(v)
    bmesh.ops.delete(bm, geom=drop, context='VERTS')
    if 'Higa skin cap' not in body.data.materials:
        slot = bpy.data.materials.new('Higa skin cap')
        slot.use_nodes = True
        body.data.materials.append(slot)
    skin_index = body.data.materials.find('Higa skin cap')
    for sign in (1.0, -1.0):
        center = Vector((sign * 0.125, -0.01, 1.40))
        hub = bm.verts.new(center)
        circle = []
        for i in range(18):
            a = i / 18 * math.tau
            circle.append(bm.verts.new(center + Vector((sign * 0.01, math.sin(a) * 0.07, math.cos(a) * 0.06))))
        for i, _v in enumerate(circle):
            face = bm.faces.new((circle[i], circle[(i + 1) % 18], hub))
            face.material_index = skin_index
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    for v in sleeves.data.vertices:
        if v.co.z < 1.28:
            continue
        f = min((v.co.z - 1.28) / 0.16, 1.0)
        sign = 1.0 if v.co.x > 0 else -1.0
        v.co.z += 0.018 * f
        v.co.x -= sign * 0.012 * f
    sleeves.data.update()
    rig = body.parent
    skin = sleeves.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
    skin.object = rig
    skin.use_deform_preserve_volume = False
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
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
    preview = OUT.parent / 'preview'
    for label, loc, scale in (('front', (0, 3.4, 1.15), 1.15), ('shoulder', (0.7, 1.5, 1.40), 0.48)):
        cam.location = loc
        cam.data.ortho_scale = scale
        cam.rotation_euler = (Vector((0.12 if label == 'shoulder' else 0, 0, 1.15)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    print('saved', OUT)


if __name__ == '__main__':
    main()
