"""Migrate current Jacobo/done camera names, retaining the user's scene geometry."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools'))
from blender_workspace import configure
configure('story_cutscenes')
import bpy
from mathutils import Quaternion

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scene', choices=('jacobo', 'done'), required=True)
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
out = REPO / f'out/story_cutscenes/m02_{args.scene}'
spec = json.loads((out / 'spec.json').read_text(encoding='utf-8'))
name = spec['name']
assets = Path('D:/Games/FL_MOD/Assets')
blend = assets / f'SCENES/{name}.blend'
dump_path = assets / f'SCENES/DUMPS/{name}.json'
assert hashlib.sha256(blend.read_bytes()).hexdigest() == spec['original_blend_sha256']
assert hashlib.sha256(dump_path.read_bytes()).hexdigest() == spec['original_dump_sha256']
original_dump = json.loads(dump_path.read_text())
bpy.ops.wm.open_mainfile(filepath=str(blend))
configure('story_cutscenes')
rx = Quaternion((1, 0, 0), -1.5708)


def point(obj):
    return {'position': list(obj.location), 'orientation': list(rx @ obj.rotation_quaternion)}


def error(a, b):
    pos = max(abs(x - y) for x, y in zip(a['position'], b['position']))
    q1, q2 = Quaternion(a['orientation']), Quaternion(b['orientation'])
    rot = min(max(abs(x - y) for x, y in zip(q1, q2)),
              max(abs(x + y) for x, y in zip(q1, q2)))
    return max(pos, rot)


# The blend is the authoring source, including any edits newer than its dump.
before = {}
for obj in bpy.context.scene.objects:
    obj.rotation_mode = 'QUATERNION'
    before[obj.name] = point(obj)
assert set(spec['old_points'].values()) <= set(before)
dump_delta = max(error(before[n], original_dump[n]) for n in spec['old_points'].values())
renames = {old: new for new, old in spec['old_points'].items() if new != old}
renames.update({old: new for old, new in spec['names'].items() if old in before and old != new})
for old, new in renames.items():
    assert new not in bpy.data.objects, (old, new)
    bpy.data.objects[old].name = new

# Retain the character meshes already in the scene; movement destinations must
# share the corresponding mesh rather than becoming empty marker objects.
for target, actor in spec['placements'].items():
    obj, char = bpy.data.objects[target], bpy.data.objects[actor]
    assert char.type == 'MESH', actor
    if obj.type != 'MESH':
        replacement = bpy.data.objects.new(target + '_replacement', char.data)
        for collection in obj.users_collection:
            collection.objects.link(replacement)
        replacement.matrix_world = obj.matrix_world.copy()
        bpy.data.objects.remove(obj, do_unlink=True)
        replacement.name = target
        replacement.rotation_mode = 'QUATERNION'
    else:
        obj.data = char.data

text_name = name + '.py'
if text_name in bpy.data.texts:
    bpy.data.texts.remove(bpy.data.texts[text_name])
bpy.data.texts.new(text_name).write((out / text_name).read_text(encoding='utf-8'))
scene = bpy.context.scene
scene['native_scene_class'] = spec['scene_class']
scene['source_thn'] = spec['source']
scene['source_sha256'] = spec['sha256']
staged = out / blend.name
bpy.ops.wm.save_as_mainfile(filepath=str(staged))
bpy.ops.wm.open_mainfile(filepath=str(staged))
configure('story_cutscenes')
after = {o.name: point(o) for o in bpy.context.scene.objects}
expected = {renames.get(n, n): p for n, p in before.items()}
assert set(after) == set(expected)
max_error = max(error(after[n], expected[n]) for n in expected)
assert max_error < 0.000002, max_error
for target, actor in spec['placements'].items():
    assert bpy.data.objects[target].type == 'MESH'
    assert bpy.data.objects[target].data == bpy.data.objects[actor].data
assert bpy.data.texts[text_name].as_string() == (out / text_name).read_text(encoding='utf-8')
(out / (name + '.json')).write_text(json.dumps(after, indent=2), encoding='utf-8')
report = {'reopened': True, 'sha256': hashlib.sha256(staged.read_bytes()).hexdigest(),
          'objects': len(after), 'renames': renames, 'max_transform_error': max_error,
          'preexisting_blend_dump_delta': dump_delta, 'movement_meshes': spec['placements'],
          'source_scene_sha256': hashlib.sha256((out / text_name).read_bytes()).hexdigest()}
(out / 'blender_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report), flush=True)
