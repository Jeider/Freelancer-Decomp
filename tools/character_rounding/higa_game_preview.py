"""Offline views of the headless game mesh. No game writes."""
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from blender_workspace import configure

configure('character_rounding')
OUT = ROOT / 'out/character_rounding/higa/game_body'
GROUND = 0.96956336


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    configure('character_rounding')
    mesh = np.load(OUT / 'mesh.npz')
    points = mesh['points']
    blender = np.column_stack((points[:, 0], -points[:, 2], points[:, 1] + GROUND))
    faces = np.vstack([mesh['costume'], mesh['skin_cap']]) if len(mesh['skin_cap']) else mesh['costume']
    me = bpy.data.meshes.new('higa')
    me.from_pydata(blender.tolist(), [], faces.tolist())
    me.update()
    ob = bpy.data.objects.new('higa', me)
    bpy.context.collection.objects.link(ob)
    for poly in me.polygons:
        poly.use_smooth = True
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 8
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 700
    scene.render.resolution_y = 1000
    scene.world = bpy.data.worlds.new('Studio')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (0.16, 0.16, 0.16, 1)
    for loc, power in (((-2, 3, 2), 300), ((2, -2, 2), 220)):
        ld = bpy.data.lights.new('L', 'AREA')
        ld.energy = power
        lamp = bpy.data.objects.new('L', ld)
        scene.collection.objects.link(lamp)
        lamp.location = loc
        lamp.rotation_euler = (Vector((0, 0, 0.8)) - lamp.location).to_track_quat('-Z', 'Y').to_euler()
    cam = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera'))
    scene.collection.objects.link(cam)
    scene.camera = cam
    cam.data.type = 'ORTHO'
    cam.data.ortho_scale = 2.1
    preview = OUT / 'preview'
    preview.mkdir(exist_ok=True)
    for label, loc in (('front', (0, 4, 0.8)), ('side', (4, 0, 0.8))):
        cam.location = loc
        cam.rotation_euler = (Vector((0, 0, 0.8)) - cam.location).to_track_quat('-Z', 'Y').to_euler()
        scene.render.filepath = str(preview / (label + '.png'))
        bpy.ops.render.render(write_still=True)
    print('preview', preview)


if __name__ == '__main__':
    main()
