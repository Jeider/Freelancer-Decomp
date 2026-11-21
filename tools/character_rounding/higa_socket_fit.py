"""Fill the measured shoulder opening with an arm continuation."""
import math
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
SRC = ROOT / 'out/character_rounding/higa/peasant_scaled/higa_peasant_scaled.blend'


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    sleeves = bpy.data.objects['pl_female1 sleeves']
    rig = body.parent
    old = bpy.data.objects.get('shoulder socket')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    for ob in (body, sleeves):
        for mod in list(ob.modifiers):
            if mod.type == 'ARMATURE':
                ob.modifiers.remove(mod)
    bm = bmesh.new()
    bm.from_mesh(body.data)
    holes = []
    for e in bm.edges:
        if not e.is_boundary:
            continue
        c = (e.verts[0].co + e.verts[1].co) / 2
        if 1.20 < c.z < 1.50 and 0.06 < abs(c.x) < 0.24:
            holes.append(c)
    bm.free()
    holes = np.array([(c.x, c.y, c.z) for c in holes]) if holes else np.zeros((0, 3))
    print('hole edges', len(holes))
    me = bpy.data.meshes.new('shoulder socket')
    verts, faces = [], []
    segs = 18
    for sign in (1.0, -1.0):
        side = holes[np.sign(holes[:, 0]) == sign] if len(holes) else np.zeros((0, 3))
        if len(side):
            center = side.mean(0)
            print('hole', sign, np.round(center, 3), 'span', np.round(side.max(0) - side.min(0), 3))
        else:
            center = np.array([sign * 0.16, -0.02, 1.36])
        sleeve = np.array([v.co[:] for v in sleeves.data.vertices])
        arm = sleeve[(np.sign(sleeve[:, 0]) == sign) & (sleeve[:, 2] > 1.28)]
        arm_c = arm.mean(0) if len(arm) else np.array([sign * 0.18, -0.03, 1.34])
        start = Vector((float(arm_c[0]), float(arm_c[1]), float(arm_c[2] - 0.02)))
        end = Vector((float(center[0] * 0.82), float(center[1]), float(center[2] + 0.03)))
        base = len(verts)
        rings = 8
        for step in range(rings):
            f = step / (rings - 1)
            p = start.lerp(end, f)
            radius = 0.085 - 0.01 * f
            for i in range(segs):
                a = i / segs * math.tau
                verts.append(p + Vector((sign * math.cos(a) * 0.02, math.sin(a) * radius, math.cos(a) * radius)))
        for step in range(rings - 1):
            for i in range(segs):
                a = base + step * segs + i
                b = base + step * segs + (i + 1) % segs
                faces.append((a, b, b + segs, a + segs))
        hub = len(verts)
        verts.append(end)
        last = base + (rings - 1) * segs
        for i in range(segs):
            faces.append((last + i, last + (i + 1) % segs, hub))
    me.from_pydata(verts, [], faces)
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    socket = bpy.data.objects.new('shoulder socket', me)
    bpy.context.collection.objects.link(socket)
    if sleeves.data.materials:
        socket.data.materials.append(sleeves.data.materials[0])
    for name in ('RUpArm', 'LUpArm', 'RCollarBone', 'LCollarBone', 'UpperTorso'):
        socket.vertex_groups.new(name=name)
    for v in socket.data.vertices:
        side = 'R' if v.co.x > 0 else 'L'
        socket.vertex_groups[side + 'UpArm'].add([v.index], 0.5, 'REPLACE')
        socket.vertex_groups[side + 'CollarBone'].add([v.index], 0.3, 'REPLACE')
        socket.vertex_groups['UpperTorso'].add([v.index], 0.2, 'REPLACE')
    socket.parent = rig
    for ob in (body, sleeves, socket):
        mod = ob.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
        mod.object = rig
        mod.use_deform_preserve_volume = False
    bpy.ops.wm.save_as_mainfile(filepath=str(SRC))
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
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
    scene.render.resolution_y = 1000
    if scene.world is None:
        scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
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
    preview = SRC.parent / 'preview'
    for label, loc, scale in (('side', (3.2, 0.15, 1.15), 1.05), ('shoulder', (0.7, 1.4, 1.38), 0.42)):
        cam.location = loc
        cam.data.ortho_scale = scale
        cam.rotation_euler = (Vector((0.05 if label == 'shoulder' else 0, 0, 1.12)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
