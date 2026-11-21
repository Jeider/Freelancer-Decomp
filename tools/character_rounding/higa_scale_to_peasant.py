"""Lower Higa pauldrons onto the peasant sleeves and close the socket."""
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
SRC = ROOT / 'out/character_rounding/higa/peasant_arms/higa_peasant_arms.blend'
OUT = ROOT / 'out/character_rounding/higa/peasant_scaled'


def smooth(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    sleeves = bpy.data.objects['pl_female1 sleeves']
    rig = body.parent
    for ob in (body, sleeves):
        for mod in list(ob.modifiers):
            if mod.type == 'ARMATURE':
                ob.modifiers.remove(mod)
    # Peasant shoulder caps end near z=1.46 and x=0.21. Drop only the wings onto the arm.
    for v in body.data.vertices:
        lateral = float(smooth(0.08, 0.16, abs(v.co.x)))
        height = float(smooth(1.28, 1.42, v.co.z))
        if lateral * height < 0.01:
            continue
        v.co.z -= 0.09 * lateral * height
        v.co.x *= 1 - 0.10 * lateral * height
    body.data.update()
    me = bpy.data.meshes.new('shoulder socket')
    verts, faces = [], []
    rings, segs = 6, 16
    for sign in (1.0, -1.0):
        base = len(verts)
        for step in range(rings):
            f = step / (rings - 1)
            center = Vector((sign * (0.105 + 0.07 * f), 0.01 - 0.04 * f, 1.30 + 0.06 * f))
            radius = 0.068 - 0.012 * f
            for i in range(segs):
                a = i / segs * math.tau
                verts.append(center + Vector((sign * math.cos(a) * 0.012, math.sin(a) * radius, math.cos(a) * radius)))
        for step in range(rings - 1):
            for i in range(segs):
                a = base + step * segs + i
                b = base + step * segs + (i + 1) % segs
                faces.append((a, b, b + segs, a + segs))
        # Close the inner end so the torso cavity is not open.
        hub = len(verts)
        verts.append((sign * 0.105, 0.01, 1.30))
        for i in range(segs):
            faces.append((base + i, base + (i + 1) % segs, hub))
    me.from_pydata(verts, [], faces)
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    socket = bpy.data.objects.new('shoulder socket', me)
    bpy.context.collection.objects.link(socket)
    mat = sleeves.data.materials[0] if sleeves.data.materials else bpy.data.materials.new('socket')
    socket.data.materials.append(mat)
    for name in ('RUpArm', 'LUpArm', 'RCollarBone', 'LCollarBone', 'UpperTorso'):
        if name not in [g.name for g in socket.vertex_groups]:
            socket.vertex_groups.new(name=name)
    for v in socket.data.vertices:
        side = 'R' if v.co.x > 0 else 'L'
        socket.vertex_groups[side + 'UpArm'].add([v.index], 0.45, 'REPLACE')
        socket.vertex_groups[side + 'CollarBone'].add([v.index], 0.35, 'REPLACE')
        socket.vertex_groups['UpperTorso'].add([v.index], 0.20, 'REPLACE')
    socket.parent = rig
    for ob in (body, sleeves, socket):
        mod = ob.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
        mod.object = rig
        mod.use_deform_preserve_volume = False
    blend = OUT / 'higa_peasant_scaled.blend'
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
    if scene.world is None:
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
            ('shoulder', (0.65, 1.45, 1.36), 0.46)):
        cam.location = loc
        cam.data.ortho_scale = scale
        cam.rotation_euler = (Vector((0.08 if label == 'shoulder' else 0, 0, 1.12)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    print('BLEND', blend)


if __name__ == '__main__':
    main()
