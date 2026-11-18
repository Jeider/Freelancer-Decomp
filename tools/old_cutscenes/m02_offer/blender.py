"""Create the scene's fresh authoring blend and export its reopened points."""
import hashlib
import argparse
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools'))
from blender_workspace import configure
configure('story_cutscenes')

import bpy
from mathutils import Matrix, Quaternion, Vector

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scene', choices=('offer', 'accept'), default='offer')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
OUT = REPO / f'out/story_cutscenes/m02_{args.scene}'
spec = json.loads((OUT / 'spec.json').read_text())
name = spec['name']
bpy.ops.wm.read_factory_settings(use_empty=True)
configure('story_cutscenes')
rx = Quaternion((1, 0, 0), -1.5708)
bpy.ops.wm.obj_import(filepath='E:/FL/room/trent_stand.obj', forward_axis='Y', up_axis='Z')
imported = list(bpy.context.selected_objects)
if len(imported) > 1:
    bpy.context.view_layer.objects.active = imported[0]
    bpy.ops.object.join()
dummy = bpy.context.view_layer.objects.active
char_mesh = dummy.data
bpy.data.objects.remove(dummy, do_unlink=True)

collections = {}
for label in ('01 Characters', '02 Movement positions', '03 Cameras', '04 Look and IK', '05 Props'):
    collection = bpy.data.collections.new(label)
    bpy.context.scene.collection.children.link(collection)
    collections[label] = collection
for n, point in spec['points'].items():
    is_character = n in spec['characters'] or n in spec['placements']
    label = ('01 Characters' if n in spec['characters'] else
             '02 Movement positions' if n in spec['placements'] else
             '03 Cameras' if n.startswith('cam_') else
             '05 Props' if n.startswith(('Prop_', 'prop_', 'vfx_')) else '04 Look and IK')
    obj = bpy.data.objects.new(n, char_mesh if is_character else None)
    collections[label].objects.link(obj)
    x, y, z = point['pos']
    obj.location = (x, -z, y)
    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = rx.inverted() @ Matrix(point['orient']).to_quaternion().conjugated()
    if not is_character:
        obj.empty_display_type = 'CUBE' if n in spec['cameras'] else 'SPHERE'
        obj.empty_display_size = 0.12 if n in spec['cameras'] else 0.06
        obj.show_name = True

scene = bpy.context.scene
scene.render.fps = 30
scene.frame_end = round(spec['duration'] * 30)
for line in spec['dialogue']:
    scene.timeline_markers.new(f"{line['index']} {line['actor']} (source)", frame=round(line['start'] * 30))
scene['source_thn'] = spec['source']
scene['source_sha256'] = spec['sha256']
scene['room'] = 'rh_battleship_bar.cmp; matching OBJ not available'
bpy.data.texts.new(name + '.py').write((OUT / (name + '.py')).read_text(encoding='utf-8'))
bpy.ops.object.select_all(action='DESELECT')
focus = bpy.data.objects['Char_trent']
focus.select_set(True)
bpy.context.view_layer.objects.active = focus
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == 'VIEW_3D':
            area.spaces.active.region_3d.view_location = focus.location
            area.spaces.active.region_3d.view_distance = 8

target = OUT / (name + '.blend')
bpy.ops.wm.save_as_mainfile(filepath=str(target))
bpy.ops.wm.open_mainfile(filepath=str(target))
dump = {}
max_position_error = max_orientation_error = 0
assert {o.name for o in bpy.context.scene.objects} == set(spec['points'])
for obj in bpy.context.scene.objects:
    q = rx @ obj.rotation_quaternion
    dump[obj.name] = {'position': list(obj.location), 'orientation': list(q)}
    original = spec['points'][obj.name]
    pos = Vector((obj.location.x, obj.location.z, -obj.location.y))
    max_position_error = max(max_position_error, (pos - Vector(original['pos'])).length)
    restored = q.conjugated().to_matrix()
    max_orientation_error = max(max_orientation_error, max(abs(restored[i][j] - original['orient'][i][j])
                                                         for i in range(3) for j in range(3)))
    assert obj.type == ('MESH' if obj.name in spec['characters'] + spec['placements'] else 'EMPTY')
assert max_position_error < 0.0001 and max_orientation_error < 0.0001, (max_position_error, max_orientation_error)
(OUT / (name + '.json')).write_text(json.dumps(dump, indent=2), encoding='utf-8')
report = {'objects': len(dump), 'reopened': True, 'position_error': max_position_error,
          'orientation_error': max_orientation_error, 'sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
(OUT / 'blender_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(report, flush=True)
