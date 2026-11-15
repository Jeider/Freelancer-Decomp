"""Build a source-based Blender scene, reopen it, and export its actual dump."""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT = Path(__file__).resolve().parent
spec = json.loads((ROOT / 'blender_spec.json').read_text())
OUT = ROOT / 'm01_berlin.blend'
RX_NEG = Quaternion((1, 0, 0), -1.5708)
RX_POS = RX_NEG.inverted()
bpy.ops.wm.read_factory_settings(use_empty=True)


def mesh(path):
    # Identity import axes: original OBJ coordinates are Freelancer Y-up.
    bpy.ops.wm.obj_import(filepath=str(path), forward_axis='Y', up_axis='Z')
    objects = list(bpy.context.selected_objects)
    assert len(objects) == 1, (path, len(objects))
    obj = objects[0]
    assert obj.rotation_euler.to_matrix().is_identity
    return obj


source = mesh(Path('E:/FL/room/trent_stand.obj'))
character_mesh = source.data
bpy.data.objects.remove(source, do_unlink=True)
room = mesh(Path('E:/FL/room/rh_berlin_bar.obj'))
room.name = 'rh_berlin_bar'
room.rotation_mode = 'QUATERNION'
room.rotation_quaternion = RX_POS
room.location = (0, 0, 0)
room.hide_select = True

for name, spatial in spec['points'].items():
    character = name.startswith('Char_') or name in spec['character_markers']
    obj = bpy.data.objects.new(name, character_mesh if character else None)
    bpy.context.scene.collection.objects.link(obj)
    if not character:
        obj.empty_display_type = 'CUBE' if name in spec['cameras'] else 'SPHERE'
        obj.empty_display_size = 0.12 if name in spec['cameras'] else 0.065
        obj.show_name = True
    pos = spatial['pos']
    obj.location = (pos[0], -pos[2], pos[1])
    if 'orient' in spatial:
        fl_quat = Matrix(spatial['orient']).to_quaternion()
    else:
        fl_quat = Quaternion(spatial.get('q_orient', (1, 0, 0, 0)))
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = RX_POS @ fl_quat.conjugated()
    obj['source_thn'] = 'm01_berlin_bar.thn'
    obj['role'] = 'character position' if character else ('camera' if name in spec['cameras'] else 'marker')

# Make the authored area immediately visible on opening the blend.
bpy.ops.object.select_all(action='DESELECT')
bpy.data.objects['Char_trent'].select_set(True)
bpy.context.view_layer.objects.active = bpy.data.objects['Char_trent']
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_location = Vector((0.5, -3, 1.2))
            area.spaces.active.region_3d.view_distance = 9
            area.spaces.active.clip_end = 1000

bpy.context.scene['source_thn'] = 'DATA/SCRIPTS/MOD/m01_berlin_bar.thn'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT))
bpy.ops.wm.open_mainfile(filepath=str(OUT))
dump = {}
for obj in bpy.context.scene.objects:
    obj.rotation_mode = 'QUATERNION'
    quat = RX_NEG @ obj.rotation_quaternion
    dump[obj.name] = {'position':list(obj.location), 'orientation':list(quat)}
    if obj.name in spec['points']:
        original = spec['points'][obj.name]
        restored = Vector((obj.location.x, obj.location.z, -obj.location.y))
        assert (restored - Vector(original['pos'])).length < 1e-5, obj.name
        expected = Matrix(original['orient']) if 'orient' in original else Quaternion(original['q_orient']).to_matrix()
        actual = quat.conjugated().to_matrix()
        assert max(abs(actual[i][j] - expected[i][j]) for i in range(3) for j in range(3)) < 1e-5, obj.name
for name in spec['character_markers']:
    assert bpy.data.objects[name].type == 'MESH'
    assert bpy.data.objects[name].data == bpy.data.objects['Char_trent'].data
assert 'cam_dbg' not in dump and 'offscreen' not in dump
(ROOT / 'm01_berlin.json').write_text(json.dumps(dump, indent=2), encoding='utf-8')
print(f'BLENDER VERIFIED: {len(dump)} objects; positions/orientations match THN; dump read from saved blend.')
