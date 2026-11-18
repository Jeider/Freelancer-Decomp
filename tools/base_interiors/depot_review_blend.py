"""Editable original depot and matched texture/clay wall inspections; no export."""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from blender_workspace import configure
configure('base_interiors')
sys.path.insert(0, str(Path(__file__).resolve().parent))
from depot_surface_audit import OUT, ORIGINAL, CURRENT
from native_common import sha


def cv(v):
    return Vector((float(v[0]), -float(v[2]), float(v[1])))


def main():
    report = json.loads((OUT / 'surfaces.json').read_text(encoding='utf8'))
    pins = json.loads((OUT / 'sources.json').read_text(encoding='utf8'))
    assert sha(ORIGINAL.read_bytes()) == pins['original_sha256']
    assert sha(CURRENT.read_bytes()) == pins['installed_sha256']
    arrays = np.load(OUT / 'original_geometry.npz')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene['geometry_source'] = str(ORIGINAL)
    scene['geometry_sha256'] = pins['original_sha256']
    scene['material_source_sha256'] = pins['installed_sha256']
    scene['review_status'] = 'Original geometry only. Wall candidates are not approved relief contours.'
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1120
    scene.render.resolution_y = 840
    scene.render.resolution_percentage = 100
    scene.render.use_persistent_data = True
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.exposure = .5
    scene.world = bpy.data.worlds.new('Neutral inspection ambient')
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.24, .27, .30, 1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value = .7
    try:
        prefs = bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type = 'OPTIX'
        prefs.get_devices()
        for device in prefs.devices:
            device.use = device.type == 'OPTIX'
        if any(device.use for device in prefs.devices):
            scene.cycles.device = 'GPU'
    except Exception:
        pass
    architecture = bpy.data.collections.new('Original architecture - FL_ND')
    mechanisms = bpy.data.collections.new('Unchanged cranes and props - FL_ND')
    scene.collection.children.link(architecture)
    scene.collection.children.link(mechanisms)
    materials = {}
    for key, source in report['materials'].items():
        mat = bpy.data.materials.new(source['name'])
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bs = nodes.get('Principled BSDF')
        bs.inputs['Roughness'].default_value = .8
        dt = source['textures'].get('Dt_name')
        if dt:
            tex = nodes.new('ShaderNodeTexImage')
            tex.image = bpy.data.images.load(str(OUT / dt['path']), check_existing=True)
            uv = nodes.new('ShaderNodeUVMap')
            uv.uv_map = 'UV0'
            links.new(uv.outputs[0], tex.inputs['Vector'])
            links.new(tex.outputs['Color'], bs.inputs['Base Color'])
            links.new(tex.outputs['Color'], bs.inputs['Emission Color'])
            bs.inputs['Emission Strength'].default_value = .25
            if 'Ot' in source['type']:
                links.new(tex.outputs['Alpha'], bs.inputs['Alpha'])
        if 'Two' not in source['type']:
            geo = nodes.new('ShaderNodeNewGeometry')
            transparent = nodes.new('ShaderNodeBsdfTransparent')
            mix = nodes.new('ShaderNodeMixShader')
            links.new(geo.outputs['Backfacing'], mix.inputs[0])
            links.new(bs.outputs[0], mix.inputs[1])
            links.new(transparent.outputs[0], mix.inputs[2])
            links.new(mix.outputs[0], nodes.get('Material Output').inputs['Surface'])
        materials[key] = mat
    face_patch = {}
    for p in report['patches']:
        for group, indices in p['groups'].items():
            for ti in indices:
                face_patch[group, ti] = int(p['id'][1:])
    objects = {}
    for group in report['groups']:
        t = arrays[group['key']]
        vertices = t.reshape(-1, t.shape[-1])
        faces = np.arange(len(vertices)).reshape(-1, 3)
        cross = np.cross(t[:, 1, :3] - t[:, 0, :3], t[:, 2, :3] - t[:, 0, :3])
        flip = np.einsum('ij,ij->i', cross, t[:, :, 3:6].mean(1)) < 0
        faces[flip] = faces[flip][:, [0, 2, 1]]
        mesh = bpy.data.meshes.new(group['key'])
        mesh.from_pydata([cv(v) for v in vertices[:, :3]], [], faces.tolist())
        mesh.update()
        for slot in range((vertices.shape[-1] - 6) // 2):
            uv = mesh.uv_layers.new(name=f'UV{slot}')
            for loop in mesh.loops:
                row = vertices[loop.vertex_index]
                uv.data[loop.index].uv = (row[6 + slot * 2], 1 - row[7 + slot * 2])
        if mesh.uv_layers:
            mesh.uv_layers.active_index = 0
        for poly in mesh.polygons:
            poly.use_smooth = True
        mesh.normals_split_custom_set([cv(vertices[loop.vertex_index, 3:6]) for loop in mesh.loops])
        attr = mesh.attributes.new('audit_planar_patch_id', 'INT', 'FACE')
        for i in range(len(mesh.polygons)):
            attr.data[i].value = face_patch.get((group['key'], i), -1)
        mesh.materials.append(materials[group['material']])
        label = report['materials'][group['material']]['number']
        ob = bpy.data.objects.new(group['key'] + '__M' + label, mesh)
        ob['native_part'] = group['part']
        ob['native_group'] = group['group']
        ob['material_crc'] = group['material']
        (architecture if group['part'] in ('Root', 'room') else mechanisms).objects.link(ob)
        objects[group['key']] = ob
    clay = bpy.data.materials.new('Neutral clay - geometry inspection only')
    clay.use_nodes = True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.38, .43, .48, 1)
    clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .9
    light = bpy.data.lights.new('Inspection softbox', 'AREA')
    light.shape = 'DISK'
    lamp = bpy.data.objects.new(light.name, light)
    scene.collection.objects.link(lamp)
    camera = bpy.data.objects.new('Review camera', bpy.data.cameras.new('Review camera'))
    scene.collection.objects.link(camera)
    scene.camera = camera
    camera.data.clip_start = .02
    camera.data.clip_end = 1000

    def point(position, target, scale, fov=64):
        camera.location = cv(position)
        target = cv(target)
        camera.rotation_euler = (target - camera.location).to_track_quat('-Z', 'Y').to_euler()
        camera.data.type = 'PERSP'
        camera.data.angle = math.radians(fov)
        lamp.location = camera.location + Vector((scale * .5, 0, scale * .4))
        lamp.rotation_euler = (target - lamp.location).to_track_quat('-Z', 'Y').to_euler()
        light.energy = 45 * scale * scale
        light.size = scale * .7

    point((5.5, 3.5, 0), (-6, 1.5, 0), 9)
    # Pack current texture images so the editable baseline is self-contained.
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'depot_original_review.blend'))
    saved_path = OUT / 'depot_original_review.blend'
    assert sum(len(o.data.polygons) for o in objects.values()) == 7267
    views = []
    shots = [
        ('west_wall', (-3, 2.4, 0), (-12, 2.4, 0), 7, 64),
        ('north_wall', (-3, 2.5, 0), (-3, 2.5, -8.2), 8, 64),
        ('south_wall', (-3, 2.5, 0), (-3, 2.5, 8.2), 8, 64),
        ('east_wall', (-1, 2.8, 0), (7.8, 4.6, 0), 8, 64),
        ('north_wide', (0, 2.8, 6), (0, 2.8, -8.2), 12, 86),
        ('south_wide', (0, 2.8, -6), (0, 2.8, 8.2), 12, 86),
    ]
    for name, position, target, scale, fov in shots:
        point(position, target, scale, fov)
        for mode in ('textured', 'clay'):
            scene.view_layers[0].material_override = clay if mode == 'clay' else None
            scene.render.filepath = str(OUT / f'{name}_{mode}.png')
            bpy.ops.render.render(write_still=True)
        views.append(dict(name=name, position=position, target=target, all_original_objects_retained=True))
    # Reload the actual saved deliverable, not merely the temporary render scene.
    bpy.ops.wm.open_mainfile(filepath=str(saved_path))
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    assert sum(len(o.data.polygons) for o in meshes) == 7267
    assert all(not o.hide_render and not o.hide_viewport for o in meshes)
    assert all(im.packed_file for im in bpy.data.images if im.type == 'IMAGE' and im.source == 'FILE')
    assert sha(ORIGINAL.read_bytes()) == pins['original_sha256']
    assert sha(CURRENT.read_bytes()) == pins['installed_sha256']
    (OUT / 'blend_review.json').write_text(json.dumps(dict(
        saved_blend=str(saved_path), sha256=sha(saved_path.read_bytes()),
        reopened=True, original_triangle_count=7267, all_original_objects_visible=True,
        textures_packed=True, sources_unchanged=True, views=views,
        scope='Offline original geometry with current diffuse artwork. Neutral diagnostic light, no game shader, no claims of exact in-game appearance.'), indent=2) + '\n', encoding='utf8')
    print('DEPOT_REVIEW_COMPLETE', flush=True)


if __name__ == '__main__':
    main()
