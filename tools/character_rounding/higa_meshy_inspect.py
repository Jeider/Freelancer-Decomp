"""Orthographic views of the supplied Higa Meshy FBX. No game writes."""
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
ART = Path('D:/work/MESHY/higa1')
OUT = ROOT / 'out/character_rounding/higa/meshy_source'


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    configure('character_rounding')
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.import_scene.fbx(filepath=str(next(ART.glob('*.fbx'))))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for ob in meshes:
        bpy.context.view_layer.objects.active = ob
        ob.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        ob.select_set(False)
    pts = np.array([tuple(o.matrix_world @ v.co) for o in meshes for v in o.data.vertices])
    lo, hi = pts.min(0), pts.max(0)
    report = {
        'objects': [{'name': o.name, 'vertices': len(o.data.vertices),
                     'polygons': len(o.data.polygons),
                     'materials': [m.name if m else '' for m in o.data.materials]} for o in meshes],
        'bounds': [lo.tolist(), hi.tolist()],
        'size': (hi - lo).tolist(),
    }
    (OUT / 'inspect.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    scene = bpy.context.scene
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
    scene.render.resolution_y = 1000
    scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.16, 0.16, 0.16, 1)
    scene.view_settings.view_transform = 'AgX'
    center = (lo + hi) * 0.5
    for loc, power in (((-2, 3, 2), 350), ((2, 1, 1.5), 180), ((0, -3, 2), 300)):
        ld = bpy.data.lights.new('Softbox', 'AREA')
        ld.energy = power
        ld.size = 2
        ob = bpy.data.objects.new(ld.name, ld)
        scene.collection.objects.link(ob)
        ob.location = Vector(center) + Vector(loc)
        ob.rotation_euler = (Vector(center) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = float(max(hi - lo) * 1.15)
    for label, direction in (('plus_y', (0, 1, 0)), ('minus_y', (0, -1, 0)), ('plus_x', (1, 0, 0))):
        cam.location = Vector(center) + Vector(direction) * 6
        cam.rotation_euler = (-Vector(direction)).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(OUT / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    print(json.dumps(report))


if __name__ == '__main__':
    main()
