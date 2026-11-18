"""Editable extended intact prototype, reopened validation and wing sweep."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0, str(HERE))
import rh_concept_b_final_blender as h
C = h.C
BASE = HERE.parents[1]/'out/ship_design/rh_elite/rh_pir_elite/tail_rim'
OUT = BASE/'revision_02'
BLEND = OUT/'rh_pir_elite_tail_mounts.blend'
NAME = 'rh_pir_elite_tail_mounts'
SCENE_NAME = 'Intact - extended - revision 02'


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def tree(groups, transform=None):
    vs = []
    for g in groups:
        for tri in g['corners']:
            for v in tri:
                p = Vector(v[:3])
                if transform:p = Matrix(transform['rotation'])@p+Vector(transform['position'])
                vs.append(p)
    return BVHTree.FromPolygons(vs, [tuple(range(i, i+3)) for i in range(0, len(vs), 3)], all_triangles=True, epsilon=0)


def motion(data):
    inputs = json.loads((OUT/'motion_input.json').read_text())
    results = {}
    for label, parts in (('before', inputs['source_parts']), ('after', data['parts'])):
        fixed = {name:tree(parts[name]) for name in inputs['fixed_parts']}
        hits = []
        for pose in inputs['poses']:
            for name, delta in pose['transforms'].items():
                wing = tree(parts[name], delta)
                for other, target in fixed.items():
                    pairs = wing.overlap(target)
                    if pairs:hits.append(dict(phase=pose['phase'], wing=name, other=other, triangle_pairs=len(pairs)))
        results[label] = hits
    report = dict(cmp_sha256=data['cmp_sha256'], phases=65, **results)
    (OUT/'motion_check.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print('WING SWEEP', {k:len(v) for k, v in results.items()}, flush=True)


def connections(data):
    geometry = json.loads((OUT/'geometry.json').read_text())
    def select(groups, condition):
        result = []
        for g in groups:
            tris = [tri for tri in g['corners'] if condition([sum(v[k] for v in tri)/3 for k in range(3)])]
            if tris:result.append(dict(g, corners=tris))
        return result
    checks = []
    shell = tree(geometry['tail_shell'])
    for side in (-1, 1):
        for upper in (False, True):
            gs = select(geometry['tail_pylons'], lambda p:side*p[0] > 0 and (p[1] > 1) == upper)
            hits = len(tree(gs).overlap(shell)); assert hits > 0, ('floating pylon', side, upper)
            checks.append(dict(kind='tail_pylon', side=side, upper=upper, intersections=hits))
        engine = tree(data['parts']['Rh_port_engine_lod1' if side == -1 else 'Rh_starboard_engine_lod1'])
        for rear in (False, True):
            gs = select(geometry['supports'], lambda p:side*p[0] > 0 and (p[2] > 5) == rear)
            support = tree(gs); hits = len(support.overlap(engine)); assert hits > 0, ('support misses engine', side, rear)
            hull_hits = len(support.overlap(tree(json.loads((OUT/'motion_input.json').read_text())['source_parts']['Root'])))
            assert hull_hits > 0, ('support misses hull/frame', side, rear)
            checks.append(dict(kind='engine_support', side=side, rear=rear, engine_intersections=hits, hull_intersections=hull_hits))
    deck = tree(geometry['flattened_deck'])
    for x in (-.48, -.25, 0, .25, .48):
        for z in (2.55, 3.2, 4.2, 5.2, 5.88):
            loc, normal, _, _ = deck.ray_cast(Vector((x, 6, z)), Vector((0, -1, 0)), 3)
            assert loc is not None and normal.y > .999 and abs(loc.y-4.80070289) < 2e-5
    (OUT/'connection_check.json').write_text(json.dumps(dict(cmp_sha256=data['cmp_sha256'],
        connections=checks, flat_deck_front_ray_samples=25), indent=2)+'\n', encoding='utf8')
    print('CONNECTIONS', len(checks), 'and 25 deck rays verified', flush=True)


def main():
    data = json.loads((OUT/'review_data.json').read_text())
    assert sha(OUT/(NAME+'.cmp')) == data['cmp_sha256']
    if BLEND.exists() and (OUT/'blender_check.json').exists():
        previous = json.loads((OUT/'blender_check.json').read_text())
        assert sha(BLEND) == previous['blend_sha256'], 'Preserve manual Blender edits before rebuilding'
    motion(data)
    connections(data)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.file_preview_type = 'NONE'
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene; scene.name = SCENE_NAME
    scene['CMP_sha256'] = data['cmp_sha256']; scene['stage'] = 'Intact shape review only. Damage, SUR and distant LODs deferred.'
    materials = {}
    for key, entry in json.loads((BASE/'materials.json').read_text()).items():
        mat = bpy.data.materials.new(entry['name']); mat.use_nodes = True; mat.use_backface_culling = True
        mat.diffuse_color = (*entry['colour'][:3], 1)
        shader = mat.node_tree.nodes.get('Principled BSDF'); shader.inputs['Roughness'].default_value = .72
        shader.inputs['Base Color'].default_value = (*entry['colour'][:3], 1)
        if entry['image']:
            tex = mat.node_tree.nodes.new('ShaderNodeTexImage'); tex.image = bpy.data.images.load(entry['image'], check_existing=True); tex.image.pack()
            multiply = mat.node_tree.nodes.new('ShaderNodeMixRGB'); multiply.blend_type = 'MULTIPLY'; multiply.inputs[0].default_value = 1
            multiply.inputs[2].default_value = (*entry['colour'][:3], 1)
            mat.node_tree.links.new(tex.outputs['Color'], multiply.inputs[1]); mat.node_tree.links.new(multiply.outputs[0], shader.inputs['Base Color'])
        materials[int(key)] = mat
    model = bpy.data.collections.new('Intact model'); scene.collection.children.link(model)
    for name, groups in data['parts'].items():
        ob, slots = h.mesh_object(dict(groups=groups), name)
        for col in list(ob.users_collection):col.objects.unlink(ob)
        model.objects.link(ob); ob['native_component'] = name
        for i, mid in enumerate(slots):ob.data.materials[i] = materials[mid]
    hpcol = bpy.data.collections.new('Hardpoints'); scene.collection.children.link(hpcol)
    for hp in data['hardpoints'].values():
        ob = bpy.data.objects.new(hp['name'], None); hpcol.objects.link(ob)
        ob.location = C@Vector(hp['position']); ob.rotation_euler = (C@Matrix(hp['orientation'])@C.transposed()).to_euler()
        ob.empty_display_type = 'ARROWS'; ob.empty_display_size = .16; ob['native_owner_file'] = hp['file']
    hpcol.hide_viewport = True; hpcol.hide_render = True
    studio = bpy.data.collections.new('Studio'); scene.collection.children.link(studio)
    camera = bpy.data.objects.new('Camera', bpy.data.cameras.new('Camera')); studio.objects.link(camera)
    target = C@Vector((0, .4, 0)); camera.data.type = 'ORTHO'; camera.data.ortho_scale = 23
    camera.location = target+(C@Vector((-1, .55, 1))).normalized()*40
    camera.rotation_euler = (target-camera.location).to_track_quat('-Z', 'Y').to_euler(); scene.camera = camera
    for index, (pos, energy, size) in enumerate([((-10, 13, 8), 2200, 10), ((10, 7, -9), 1500, 9), ((0, 12, -2), 1200, 7)]):
        lamp = bpy.data.lights.new('Area '+str(index), 'AREA'); lamp.energy = energy; lamp.shape = 'DISK'; lamp.size = size
        ob = bpy.data.objects.new(lamp.name, lamp); studio.objects.link(ob); ob.location = C@Vector(pos)
        ob.rotation_euler = (target-ob.location).to_track_quat('-Z', 'Y').to_euler()
    scene.world = bpy.data.worlds.new('World'); scene.world.color = (.3, .3, .3)
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 16
    scene.render.resolution_x = 1400; scene.render.resolution_y = 1000; scene.render.resolution_percentage = 100
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active; space.shading.type = 'MATERIAL'; space.overlay.show_extras = False; space.overlay.show_floor = False
                space.region_3d.view_rotation = camera.rotation_euler.to_quaternion(); space.region_3d.view_location = target
                space.region_3d.view_distance = 24; space.region_3d.view_perspective = 'ORTHO'
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    assert len(bpy.data.scenes) == 1 and len(bpy.data.collections['Hardpoints'].objects) == 79
    assert len(bpy.data.collections['Intact model'].objects) == len(data['parts'])
    assert all(im.packed_file for im in bpy.data.images if im.source == 'FILE')
    report = dict(blend_sha256=sha(BLEND), cmp_sha256=data['cmp_sha256'], reopened=True, hardpoints=79,
                  extended_pose=True, intact_only=True, textures_packed_for_offline_review=True)
    (OUT/'blender_check.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf8')
    print('BLENDER SAVED AND REOPENED', BLEND, flush=True)


if __name__ == '__main__':main()
