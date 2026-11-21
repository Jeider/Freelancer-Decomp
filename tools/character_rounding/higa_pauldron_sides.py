"""Compare left and right pauldron shells in the source and the scaled file."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
OUT = ROOT / 'out/character_rounding/higa/uniform_scale/preview'
OUT.mkdir(parents=True, exist_ok=True)


def load(path):
    bpy.ops.wm.open_mainfile(filepath=str(path))
    configure('character_rounding')
    body = bpy.data.objects['Higa - skinned Meshy mesh']
    for mod in list(body.modifiers):
        if mod.type == 'ARMATURE':
            mod.show_viewport = False
            mod.show_render = False
    return body


def stats(body, label):
    mesh = body.data
    pts = np.array([v.co[:] for v in mesh.vertices])
    # pauldron wings, above the chest, outboard
    for sign, name in ((1, 'R'), (-1, 'L')):
        band = (np.sign(pts[:, 0]) == sign) & (np.abs(pts[:, 0]) > 0.08) & (np.abs(pts[:, 0]) < 0.30) & (pts[:, 2] > 1.20) & (pts[:, 2] < 1.62)
        ids = np.flatnonzero(band)
        if not len(ids):
            print(label, name, 'empty')
            continue
        # boundary edges inside the band: edges with only one face, or faces that are long thin spikes
        edge_faces = {}
        spikes = 0
        area = 0.0
        for poly in mesh.polygons:
            v = [mesh.vertices[i].co[:] for i in poly.vertices]
            if not all(band[i] for i in poly.vertices):
                continue
            area += poly.area
            span = np.max(v, axis=0) - np.min(v, axis=0)
            if span[2] < 0.004 and span[0] > 0.03:
                spikes += 1
            for ek in poly.edge_keys:
                edge_faces[ek] = edge_faces.get(ek, 0) + 1
        boundary = sum(1 for n in edge_faces.values() if n == 1)
        sample = pts[ids]
        print(label, name, 'verts', len(ids), 'faces_thin', spikes, 'boundary', boundary,
              'area', round(area, 4),
              'x', round(float(np.abs(sample[:, 0]).min()), 3), round(float(np.abs(sample[:, 0]).max()), 3),
              'z', round(float(sample[:, 2].min()), 3), round(float(sample[:, 2].max()), 3))
    # mirror check: for each right pauldron vert, nearest mirrored left
    right = pts[(pts[:, 0] > 0.10) & (pts[:, 0] < 0.28) & (pts[:, 2] > 1.25) & (pts[:, 2] < 1.58)]
    left = pts[(pts[:, 0] < -0.10) & (pts[:, 0] > -0.28) & (pts[:, 2] > 1.25) & (pts[:, 2] < 1.58)]
    if len(right) and len(left):
        mirrored = right.copy()
        mirrored[:, 0] *= -1
        # chunked nearest
        dmin = []
        step = 4000
        for i in range(0, len(mirrored), step):
            chunk = mirrored[i:i + step]
            d = np.linalg.norm(chunk[:, None, :] - left[None, :, :], axis=2).min(axis=1)
            dmin.append(d)
        dmin = np.concatenate(dmin)
        print(label, 'R-to-mirrored-L mm p50/p95/max',
              round(float(np.median(dmin)) * 1000, 1),
              round(float(np.percentile(dmin, 95)) * 1000, 1),
              round(float(dmin.max()) * 1000, 1),
              'over5mm', int((dmin > 0.005).sum()), 'of', len(dmin))


def clay_shot(body, label, sign):
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
    scene.render.resolution_y = 800
    if scene.world is None:
        scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.45, 0.45, 0.45, 1)
    scene.view_settings.view_transform = 'AgX'
    body.data.materials.clear()
    mat = bpy.data.materials.new('Clay')
    mat.use_nodes = True
    mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (0.78, 0.78, 0.78, 1)
    body.data.materials.append(mat)
    for ob in list(bpy.data.objects):
        if ob.type == 'EMPTY':
            bpy.data.objects.remove(ob, do_unlink=True)
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'PERSP'
    cam.data.lens = 55
    target = Vector((sign * 0.16, -0.02, 1.32))
    cam.location = target + Vector((sign * 0.42, -0.38, 0.16))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    ld = bpy.data.lights.new('Key', 'AREA')
    ld.energy = 180
    ld.size = 0.8
    lamp = bpy.data.objects.new('Key', ld)
    scene.collection.objects.link(lamp)
    lamp.location = cam.location + Vector((0, 0, 0.3))
    lamp.rotation_euler = cam.rotation_euler
    scene.render.filepath = str(OUT / ('%s_%s.png' % (label, 'R' if sign > 0 else 'L')))
    bpy.ops.render.render(write_still=True)


body = load(ROOT / 'out/character_rounding/higa/rigged/higa_kaitlyn_rigged.blend')
stats(body, 'source')
clay_shot(body, 'source', 1)
clay_shot(body, 'source', -1)
body = load(ROOT / 'out/character_rounding/higa/uniform_scale/higa_uniform.blend')
stats(body, 'scaled')
