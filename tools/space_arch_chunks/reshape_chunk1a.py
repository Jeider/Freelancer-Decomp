"""Reshape chunk1a at the source triangle count and render a clay preview.

No game files are written. The new form keeps the source origin and bounding box.
"""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

TOPIC = Path(r"D:\work\Freelancer-Decomp\out\space_arch_chunks\chunk1a")
SOURCE = TOPIC / "arch_ast1_source.obj"
OUT = TOPIC / "preview"


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    prefs = bpy.context.preferences.filepaths
    prefs.save_version = 0
    prefs.file_preview_type = "NONE"


def clay(name):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.58, 0.54, 0.48, 1)
    bsdf.inputs["Roughness"].default_value = 0.78
    return material


def bounds(obj):
    points = [obj.matrix_world @ v.co for v in obj.data.vertices]
    lo = Vector((min(p[i] for p in points) for i in range(3)))
    hi = Vector((max(p[i] for p in points) for i in range(3)))
    return lo, hi, (lo + hi) * 0.5


def look(camera, target):
    constraint = camera.constraints.new("TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"


def reshape(obj):
    mesh = obj.data
    bm = bmesh.new()
    bm.from_mesh(mesh)
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    lo = Vector((min(xs), min(ys), min(zs)))
    hi = Vector((max(xs), max(ys), max(zs)))
    center = (lo + hi) * 0.5
    size = hi - lo
    # The source cleft is a shallow top notch. Open it into a side-readable
    # canyon, pull one lip into a brow, and turn the thin spur into a stump.
    # Vertices only: the triangle count does not change.
    for vertex in bm.verts:
        local = Vector((
            (vertex.co.x - center.x) / (size.x * 0.5),
            (vertex.co.y - center.y) / (size.y * 0.5),
            (vertex.co.z - center.z) / (size.z * 0.5),
        ))
        cleft = math.exp(-((local.x / 0.16) ** 2)) * max(0.0, -local.y) ** 0.65
        vertex.co.z -= cleft * size.z * 0.28
        vertex.co.x += math.copysign(cleft * size.x * 0.10, local.x if abs(local.x) > 1e-4 else 1.0)
        brow = max(0.0, local.y) * max(0.0, local.z + 0.15) * max(0.0, -local.x)
        vertex.co.y += brow * size.y * 0.16
        vertex.co.z += brow * size.z * 0.05
        if local.x > 0.62:
            vertex.co.x = center.x + (0.62 + (local.x - 0.62) * 0.28) * size.x * 0.5
        if local.z < -0.45 and local.x * local.x + local.y * local.y > 0.15:
            vertex.co.x = center.x + local.x * size.x * 0.5 * 0.72
            vertex.co.y = center.y + local.y * size.y * 0.5 * 0.72
            vertex.co.z = center.z + max(local.z, -0.72) * size.z * 0.5
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()


def render_views(obj, folder, center, radius, scale):
    folder.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    camera = scene.camera
    camera.data.ortho_scale = scale
    views = {
        "front": Vector((center.x, center.y - radius * 2.6, center.z)),
        "side": Vector((center.x + radius * 2.6, center.y, center.z)),
        "top": Vector((center.x, center.y, center.z + radius * 2.8)),
        "three_quarter": Vector((center.x + radius * 1.7, center.y - radius * 1.9, center.z + radius * 0.55)),
    }
    for name, location in views.items():
        camera.location = location
        scene.render.filepath = str(folder / name)
        bpy.ops.render.render(write_still=True)


def main():
    clear()
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    source = bpy.context.selected_objects[0]
    source.name = "chunk1a_source"
    new = source.copy()
    new.data = source.data.copy()
    new.name = "chunk1a_reshaped"
    bpy.context.collection.objects.link(new)
    reshape(new)
    for obj, material_name in ((source, "source_clay"), (new, "new_clay")):
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.shade_flat()
        obj.data.materials.clear()
        obj.data.materials.append(clay(material_name))
        obj.select_set(False)
    lo, hi, center = bounds(new)
    radius = max(hi[i] - lo[i] for i in range(3)) * 0.62
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 820
    world = bpy.data.worlds.new("preview")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.15, 0.16, 0.17, 1)
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sun.data.energy = 4.2
    sun.rotation_euler = (0.85, 0.15, 0.55)
    bpy.ops.object.light_add(type="SUN")
    fill = bpy.context.object
    fill.data.energy = 1.4
    fill.data.color = (0.72, 0.8, 1)
    fill.rotation_euler = (-0.35, 0.9, -1.4)
    camera_data = bpy.data.cameras.new("view")
    camera_data.type = "ORTHO"
    camera_data.clip_start = 1
    camera_data.clip_end = 100000
    camera = bpy.data.objects.new("view", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    target = bpy.data.objects.new("target", None)
    target.location = center
    scene.collection.objects.link(target)
    look(camera, target)
    source.hide_render = True
    render_views(new, OUT, center, radius, max(hi[i] - lo[i] for i in range(3)) * 1.28)
    # Same camera, source beside the new rock, for the comparison frame.
    gap = (hi.x - lo.x) * 1.25
    source.location.x -= gap * 0.5
    new.location.x += gap * 0.5
    source.hide_render = False
    both_lo, both_hi, both_center = bounds(new)
    src_lo, src_hi, _ = bounds(source)
    frame_lo = Vector((min(both_lo.x, src_lo.x), min(both_lo.y, src_lo.y), min(both_lo.z, src_lo.z)))
    frame_hi = Vector((max(both_hi.x, src_hi.x), max(both_hi.y, src_hi.y), max(both_hi.z, src_hi.z)))
    target.location = (frame_lo + frame_hi) * 0.5
    camera.data.ortho_scale = max(frame_hi[i] - frame_lo[i] for i in range(3)) * 1.08
    camera.location = target.location + Vector((radius * 1.5, -radius * 1.8, radius * 0.45))
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 780
    scene.render.filepath = str(OUT / "comparison")
    bpy.ops.render.render(write_still=True)
    blend = TOPIC / "chunk1a_reshape_preview.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    print("triangles", len(new.data.polygons), len(source.data.polygons))
    print("new_extent", [round(hi[i] - lo[i], 1) for i in range(3)])
    print("preview", OUT)


if __name__ == "__main__":
    main()
