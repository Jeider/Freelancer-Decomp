"""Bridge the visible arm-to-chest gap. Does not cut the pauldron."""
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
SRC = ROOT / 'out/character_rounding/higa/peasant_scaled/higa_peasant_scaled.blend'


def add_tube(verts, faces, start, end, radius, segs=16):
    base = len(verts)
    axis = end - start
    length = axis.length
    axisn = axis / length
    helper = Vector((0, 0, 1)) if abs(axisn.z) < 0.9 else Vector((1, 0, 0))
    side = axisn.cross(helper).normalized()
    up = side.cross(axisn).normalized()
    rings = 5
    for step in range(rings):
        p = start.lerp(end, step / (rings - 1))
        for i in range(segs):
            a = i / segs * math.tau
            verts.append(p + side * math.cos(a) * radius + up * math.sin(a) * radius)
    for step in range(rings - 1):
        for i in range(segs):
            a = base + step * segs + i
            b = base + step * segs + (i + 1) % segs
            faces.append((a, b, b + segs, a + segs))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    sleeves = bpy.data.objects['pl_female1 sleeves']
    rig = sleeves.parent
    old = bpy.data.objects.get('shoulder bridge')
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    verts, faces = [], []
    for sign in (1.0, -1.0):
        add_tube(
            verts, faces,
            Vector((sign * 0.10, -0.01, 1.33)),
            Vector((sign * 0.20, -0.03, 1.35)),
            0.062)
        add_tube(
            verts, faces,
            Vector((sign * 0.12, 0.02, 1.38)),
            Vector((sign * 0.18, -0.04, 1.40)),
            0.055)
    me = bpy.data.meshes.new('shoulder bridge')
    me.from_pydata(verts, [], faces)
    me.update()
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new('shoulder bridge', me)
    bpy.context.collection.objects.link(ob)
    if sleeves.data.materials:
        ob.data.materials.append(sleeves.data.materials[0])
    ob.parent = rig
    for name in ('RUpArm', 'LUpArm', 'UpperTorso'):
        ob.vertex_groups.new(name=name)
    for v in ob.data.vertices:
        side = 'R' if v.co.x > 0 else 'L'
        ob.vertex_groups[side + 'UpArm'].add([v.index], 0.6, 'REPLACE')
        ob.vertex_groups['UpperTorso'].add([v.index], 0.4, 'REPLACE')
    mod = ob.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
    mod.object = rig
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
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    for loc, power in (((2.2, 1.6, 1.8), 220),):
        ld = bpy.data.lights.new('Softbox', 'AREA')
        ld.energy = power
        lamp = bpy.data.objects.new(ld.name, ld)
        scene.collection.objects.link(lamp)
        lamp.location = loc
    preview = SRC.parent / 'preview'
    for label, loc, scale in (('side', (3.2, 0.1, 1.2), 0.7), ('shoulder', (0.85, 1.15, 1.38), 0.38)):
        cam.location = loc
        cam.data.ortho_scale = scale
        cam.rotation_euler = (Vector((0.12, 0, 1.34)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
