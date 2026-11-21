"""Shorten both epaulettes front-to-back, retaining the accepted shoulder height."""
import sys, json, hashlib
from pathlib import Path
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tools'), str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step13 as s13
import hassler_native_step15 as views
import hassler_native_step20 as geometry
import hassler_native_step23 as previous
import hassler_runtime_pose as runtime

configure('character_rounding')
TOP = native.OUT / 'native_upper'
OUT = TOP / 'step_24'
SOURCE = TOP / 'step_23/hassler_native_upper.blend'
DEPTH_SCALE = .72


def mesh_invariants(ob):
    me = ob.data
    data = {
        'faces': [(list(f.vertices), f.material_index) for f in me.polygons],
        'uv': [[list(q.uv) for q in layer.data] for layer in me.uv_layers],
        'skin': [[(g.group, g.weight) for g in v.groups] for v in me.vertices],
        'group_names': [g.name for g in ob.vertex_groups],
    }
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def deform(ob, amount, centre):
    me = ob.data
    before = np.array([v.co[:] for v in me.vertices])
    normals = np.array([n.vector[:] for n in me.corner_normals])
    gradients = {}
    changed = []

    def delta(i, p):
        return (1 - DEPTH_SCALE) * (p[1] - centre) * amount(i, p)

    for v, p in zip(me.vertices, before):
        d = delta(v.index, p)
        if abs(d) < 1e-10:
            continue
        v.co.y -= d
        changed.append(v.index)
        gradient = []
        for axis in range(3):
            e = np.zeros(3)
            e[axis] = 1e-5
            gradient.append((delta(v.index, p+e)-delta(v.index, p-e)) / 2e-5)
        jacobian = np.eye(3)
        jacobian[1] -= gradient
        assert np.linalg.det(jacobian) > .6, (ob.name, v.index)
        gradients[v.index] = np.linalg.inv(jacobian).T
    me.update()
    if me.has_custom_normals:
        nn = []
        for loop, normal in zip(me.loops, normals):
            n = gradients.get(loop.vertex_index, np.eye(3)) @ normal
            n /= max(np.linalg.norm(n), 1e-12)
            nn.append(n)
        me.normals_split_custom_set(nn)
    after = np.array([v.co[:] for v in me.vertices])
    assert np.array_equal(before[:, [0, 2]], after[:, [0, 2]])
    return {
        'vertices_changed': len(changed),
        'before_bounds': [before.min(0).tolist(), before.max(0).tolist()],
        'after_bounds': [after.min(0).tolist(), after.max(0).tolist()],
        'max_front_back_move_m': float(abs(after[:, 1] - before[:, 1]).max()),
        'height_and_width_unchanged': True,
    }


def render_views(scene, prefix):
    views.OUT = OUT
    views.render(scene, prefix+'_front', (0, 1, 0), (0, 0, 1.4), 1.1)
    views.render(scene, prefix+'_shoulder', (-.8, 1, .65), (.18, .015, 1.55), .49)
    views.render(scene, prefix+'_profile', (-1, .04, .35), (.19, .01, 1.55), .42)


def main():
    OUT.mkdir(exist_ok=True)
    digest = s13.sha(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    configure('character_rounding')
    scene = bpy.context.scene
    scene.frame_set(1)
    scene.cycles.samples = 24
    edit = next(c for c in bpy.data.collections if c.name.startswith('EDIT '))
    rig = next(o for o in bpy.data.objects if o.name.startswith('RIG '))
    before_rig = previous.rig_hash(rig)
    objects = [o for o in edit.objects if o.type == 'MESH']
    fixed = {o.name: geometry.geometry_hash(o) for o in objects}
    invariants = {o.name: mesh_invariants(o) for o in objects}
    runtime.cull_materials(objects)
    if '--no-render' not in sys.argv:
        render_views(scene, 'before')
    ep = next(o for o in objects if o.name.startswith('14 '))
    depth = np.array([v.co.y for v in ep.data.vertices])
    centre = float((depth.min()+depth.max())/2)
    changes = {}
    for ob in objects:
        if ob.name.startswith(('14 ', '16 ')):
            factor = lambda i, p: 1.
        elif ob.name.startswith('17 '):
            # The sewn collar anchor stays fixed; the shoulder anchor follows
            # the board exactly, with the original interpolation across cloth.
            factor = lambda i, p: (0., .25, .6, 1.)[i % 4]
        elif ob.name.startswith(('10 ', '11 ', '13.')):
            factor = lambda i, p: previous.smooth(.14, .20, abs(p[0])) * previous.smooth(.43, .55, p[2])
        else:
            continue
        changes[ob.name] = deform(ob, factor, centre)
    for ob in objects:
        assert mesh_invariants(ob) == invariants[ob.name], ob.name
        if ob.name not in changes:
            assert geometry.geometry_hash(ob) == fixed[ob.name], ob.name
    assert previous.rig_hash(rig) == before_rig
    refs = json.loads((TOP/'source/shoulder_fit_study/native_reference_geometry.json').read_text())
    reference_depths = {k: float(np.ptp(np.array(v['points_blender'])[:, 1])) for k, v in refs.items()}
    new_depth = float(np.ptp([v.co.y for v in ep.data.vertices]))
    assert abs(new_depth / float(np.ptp(depth)) - DEPTH_SCALE) < 1e-6
    assert min(reference_depths.values()) < new_depth < max(reference_depths.values())
    report = {
        'parent': str(SOURCE), 'parent_sha256': digest,
        'authoring_axis': 'Blender Y (native/game Z): chest to back',
        'front_back_scale': DEPTH_SCALE, 'reduction_percent': 100*(1-DEPTH_SCALE),
        'front_back_centre_m': centre, 'old_depth_m': float(np.ptp(depth)),
        'new_depth_m': new_depth, 'native_reference_depths_m': reference_depths,
        'changed_geometry': changes, 'height_and_width_unchanged': True,
        'native_skeleton_before_after_sha256': before_rig, 'bones_unchanged': True,
        'topology_uv_skin_unchanged': True, 'new_polygons': 0,
        'right_collar_end_closure_preserved': True,
        'unchanged_geometry': {n: h for n, h in fixed.items() if n not in changes},
        'game_launched': False,
    }
    ep['step24_depth_scale'] = DEPTH_SCALE
    ep['step24_note'] = 'Shortened from chest to back only. Accepted width/height, closed rolled hem, UVs and native bones retained.'
    (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    native.activate(ep)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'), compress=True)
    assert s13.sha(SOURCE) == digest
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'))
    configure('character_rounding')
    scene = bpy.context.scene
    if '--no-render' not in sys.argv:
        render_views(scene, 'after')
    print(json.dumps({k: v for k, v in report.items() if k not in ('changed_geometry', 'unchanged_geometry')}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
