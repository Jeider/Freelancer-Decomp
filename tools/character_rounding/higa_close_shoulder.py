"""Cap the shoulder opening and seat the sleeve inside it. Pauldrons stay."""
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
OUT = SRC.parent


def loops(edges):
    unused = set(map(tuple, edges))
    found = []
    while unused:
        a, b = unused.pop()
        seq = [a, b]
        while True:
            nxt = None
            for edge in list(unused):
                if edge[0] == seq[-1]:
                    nxt = edge[1]
                elif edge[1] == seq[-1]:
                    nxt = edge[0]
                if nxt is not None:
                    unused.remove(edge)
                    break
            if nxt is None or nxt == seq[0]:
                break
            seq.append(nxt)
        found.append(seq)
    return found


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SRC))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    sleeves = bpy.data.objects['pl_female1 sleeves']
    rig = body.parent
    for ob in (body, sleeves):
        for mod in list(ob.modifiers):
            if mod.type == 'ARMATURE':
                ob.modifiers.remove(mod)
    if 'Higa skin cap' not in body.data.materials:
        slot = bpy.data.materials.new('Higa skin cap')
        slot.use_nodes = True
        bs = slot.node_tree.nodes.get('Principled BSDF')
        if bs:
            bs.inputs['Base Color'].default_value = (0.45, 0.30, 0.24, 1)
        body.data.materials.append(slot)
    skin_index = body.data.materials.find('Higa skin cap')
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    boundary = []
    for e in bm.edges:
        if not e.is_boundary:
            continue
        c = (e.verts[0].co + e.verts[1].co) / 2
        if 1.22 < c.z < 1.48 and 0.07 < abs(c.x) < 0.23:
            boundary.append((e.verts[0].index, e.verts[1].index))
    print('shoulder boundary edges', len(boundary))
    filled = 0
    for seq in loops(boundary):
        co = np.array([bm.verts[i].co[:] for i in seq])
        center = co.mean(0)
        # Only the arm opening: a local loop, not a pauldron rim that runs to the wing tip.
        if not (8 <= len(seq) <= 400 and 1.20 < center[2] < 1.50 and 0.06 < abs(center[0]) < 0.24):
            print('skip loop', len(seq), np.round(center, 3))
            continue
        hub = bm.verts.new(Vector(center) + Vector((0, 0.01, -0.01)))
        bm.verts.ensure_lookup_table()
        existing = {i: bm.verts[i] for i in seq}
        for i, a in enumerate(seq):
            b = seq[(i + 1) % len(seq)]
            try:
                face = bm.faces.new((existing[a], existing[b], hub))
                face.material_index = skin_index
                filled += 1
            except ValueError:
                pass
        print('filled loop', len(seq), 'at', np.round(center, 3))
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    # Pull the sleeve cap back and up into that socket.
    for v in sleeves.data.vertices:
        if v.co.z < 1.22:
            continue
        t = min((v.co.z - 1.22) / 0.20, 1.0)
        t = t * t
        sign = 1.0 if v.co.x > 0 else -1.0
        v.co.z += 0.03 * t
        v.co.y += 0.03 * t
        v.co.x -= sign * 0.02 * t
    sleeves.data.update()
    for ob in (body, sleeves):
        mod = ob.modifiers.new('Native Kaitlyn skin', 'ARMATURE')
        mod.object = rig
        mod.use_deform_preserve_volume = False
    print('faces filled', filled)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'higa_peasant_scaled.blend'))
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
    for label, loc, scale in (
            ('front', (0, 3.4, 1.15), 1.15),
            ('side', (3.4, 0.15, 1.15), 1.15),
            ('shoulder', (0.65, 1.45, 1.38), 0.46)):
        cam.location = loc
        cam.data.ortho_scale = scale
        cam.rotation_euler = (Vector((0.08 if label == 'shoulder' else 0, 0, 1.12)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
