"""Stage only selected RTC blends, then reopen and derive their native dumps."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / 'tools'))
from blender_workspace import configure
configure('story_cutscenes')
import bpy
from mathutils import Matrix, Quaternion, Vector

OUT = REPO / 'out/story_cutscenes/m03_m08'
ASSETS = Path('D:/Games/FL_MOD/Assets')
OLD = REPO / 'tools/m02_m08_cutscenes/bundle'
RX = Quaternion((1, 0, 0), -1.5708)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scene')
args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else [])
inventory = json.loads((OUT / 'inventory.json').read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(name):
    assert shutil.disk_usage(OUT).free > 2 * 1024**3
    folder = OUT / name
    spec = json.loads((folder / 'spec.json').read_text(encoding='utf-8'))
    live = ASSETS / f'SCENES/{name}.blend'
    source = live if live.exists() else OLD / f'SCENES/{name}.blend'
    if live.exists():
        assert digest(live) == spec['original_blend_sha256'], name
    bpy.ops.wm.open_mainfile(filepath=str(source))
    configure('story_cutscenes')
    meshes = {}
    for char in spec['characters']:
        original = bpy.data.objects.get(spec['old_points'][char]) or bpy.data.objects.get(char)
        if original and original.type == 'MESH':
            meshes[char] = original.data
    if len(meshes) != len(spec['characters']):
        # The established authoring marker is trent_stand.obj for all actors.
        fallback = next(iter(meshes.values()), None)
        if fallback is None:
            bpy.ops.wm.obj_import(filepath='E:/FL/room/trent_stand.obj', forward_axis='Y', up_axis='Z')
            obj = bpy.context.view_layer.objects.active
            fallback = obj.data
            bpy.data.objects.remove(obj, do_unlink=True)
        for char in spec['characters']:
            meshes.setdefault(char, fallback)
    old_spec = json.loads((OLD / f'specs/{name}.json').read_text())
    point_names = set(old_spec['points']) | set(spec['old_points'].values()) | set(spec['points'])
    for obj in list(bpy.context.scene.objects):
        if obj.name in point_names or obj.type == 'EMPTY':
            bpy.data.objects.remove(obj, do_unlink=True)
    for n, p in spec['points'].items():
        owner = n if n in meshes else spec['placements'].get(n)
        obj = bpy.data.objects.new(n, meshes[owner] if owner else None)
        bpy.context.scene.collection.objects.link(obj)
        x, y, z = p.get('pos', [0, 0, 0])
        obj.location = (x, -z, y)
        mx = Matrix(p['orient']) if 'orient' in p else Quaternion(p.get('q_orient', [1, 0, 0, 0])).to_matrix()
        scale = [mx.col[j].length for j in range(3)]
        if mx.determinant() < 0:
            scale[0] *= -1
        rotation = Matrix([[mx[i][j] / scale[j] for j in range(3)] for i in range(3)])
        obj.rotation_mode = 'QUATERNION'
        obj.rotation_quaternion = RX.inverted() @ rotation.to_quaternion().conjugated()
        obj.scale = scale
        obj['role'] = 'character placement' if owner else ('camera' if n in spec['cameras'] else 'marker')
        if not owner:
            obj.empty_display_type = 'CUBE' if n in spec['cameras'] else 'SPHERE'
            obj.empty_display_size = .12 if n in spec['cameras'] else .065
            obj.show_name = True
    # Replace stale executable snapshots, leaving room geometry and its assets.
    for block in list(bpy.data.texts):
        if block.name.endswith('.py') or block.name in ('source.json', 'report.json', 'README'):
            bpy.data.texts.remove(block)
    code = (folder / f'{name}.py').read_text(encoding='utf-8')
    bpy.data.texts.new(f'{name}.py').write(code)
    bpy.context.scene['native_scene_class'] = spec['scene_class']
    bpy.context.scene['export_point_scale'] = True
    bpy.context.scene['source_thn'] = spec['source']
    bpy.context.scene['source_sha256'] = spec['source_sha256']
    bpy.context.scene['source_duration_seconds'] = spec['duration']
    staged = folder / f'{name}.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(staged))
    bpy.ops.wm.open_mainfile(filepath=str(staged))
    configure('story_cutscenes')
    dump, max_pos, max_rot = {}, 0, 0
    for obj in bpy.context.scene.objects:
        obj.rotation_mode = 'QUATERNION'
        quat = RX @ obj.rotation_quaternion
        dump[obj.name] = {'position': list(obj.location), 'orientation': list(quat), 'matrix_scale': list(obj.scale)}
        if obj.name not in spec['points']:
            continue
        p = spec['points'][obj.name]
        pos = Vector((obj.location.x, obj.location.z, -obj.location.y))
        max_pos = max(max_pos, (pos - Vector(p.get('pos', [0, 0, 0]))).length)
        expected = Matrix(p['orient']) if 'orient' in p else Quaternion(p.get('q_orient', [1, 0, 0, 0])).to_matrix()
        actual = quat.conjugated().to_matrix()
        actual = Matrix([[actual[i][j] * obj.scale[j] for j in range(3)] for i in range(3)])
        max_rot = max(max_rot, max(abs(actual[i][j] - expected[i][j]) for i in range(3) for j in range(3)))
    assert max_pos < .03 and max_rot < .0001, (name, max_pos, max_rot)
    for target, char in spec['placements'].items():
        assert bpy.data.objects[target].type == 'MESH'
        assert bpy.data.objects[target].data == bpy.data.objects[char].data
    assert bpy.data.texts[f'{name}.py'].as_string() == code
    (folder / f'{name}.json').write_text(json.dumps(dump, indent=2), encoding='utf-8')
    report = dict(reopened=True, sha256=digest(staged), objects=len(dump),
                  max_position_error=max_pos, max_rotation_error=max_rot,
                  movement_meshes=spec['placements'], source_scene_sha256=digest(folder / f'{name}.py'))
    (folder / 'blender_check.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('VERIFIED', name, len(dump), flush=True)


for name in ([args.scene] if args.scene else inventory['scenes']):
    run(name)
