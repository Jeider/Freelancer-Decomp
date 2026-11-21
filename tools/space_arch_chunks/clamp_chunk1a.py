"""Deepen the existing cleft without moving any vertex outside the source box."""
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
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.preferences.filepaths.file_preview_type = "NONE"


def clay(obj, color):
    material = bpy.data.materials.new(obj.name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.78
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_flat()
    obj.select_set(False)


def bounds_of(obj):
    points = [vert.co for vert in obj.data.vertices]
    lo = Vector((min(point[i] for point in points) for i in range(3)))
    hi = Vector((max(point[i] for point in points) for i in range(3)))
    return lo, hi


def deepen(obj):
    lo, hi = bounds_of(obj)
    center = (lo + hi) * 0.5
    size = hi - lo
    limit = max(size) * 0.04
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    moved = 0
    for vert in bm.verts:
        local = Vector((
            (vert.co.x - center.x) / (size.x * 0.5),
            (vert.co.y - center.y) / (size.y * 0.5),
            (vert.co.z - center.z) / (size.z * 0.5),
        ))
        # Only the existing mouth, and only a short step inward.
        weight = math.exp(-((local.x / 0.28) ** 2)) * max(0.0, 0.15 - local.y)
        if weight < 0.05:
            continue
        vert.co.z -= min(weight * size.z * 0.08, limit)
        vert.co.y += min(weight * size.y * 0.03, limit * 0.5)
        for axis in range(3):
            vert.co[axis] = min(hi[axis], max(lo[axis], vert.co[axis]))
        moved += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    new_lo, new_hi = bounds_of(obj)
    if any(new_lo[i] < lo[i] - 0.1 or new_hi[i] > hi[i] + 0.1 for i in range(3)):
        raise RuntimeError("vertex left the source box")
    return moved, limit


def main():
    clear()
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    source = bpy.context.selected_objects[0]
    source.name = "chunk1a_source"
    rock = source.copy()
    rock.data = source.data.copy()
    rock.name = "chunk1a_clamped"
    bpy.context.collection.objects.link(rock)
    moved, limit = deepen(rock)
    clay(rock, (0.62, 0.57, 0.50))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 820
    world = bpy.data.worlds.new("preview")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.14, 0.15, 0.16, 1)
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sun.data.energy = 4.5
    sun.rotation_euler = (0.7, 0.1, 0.4)
    camera_data = bpy.data.cameras.new("view")
    camera_data.type = "ORTHO"
    camera_data.clip_start = 1
    camera_data.clip_end = 100000
    camera = bpy.data.objects.new("view", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    target = bpy.data.objects.new("target", None)
    scene.collection.objects.link(target)
    constraint = camera.constraints.new("TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    lo, hi = bounds_of(rock)
    center = (lo + hi) * 0.5
    radius = max(hi[i] - lo[i] for i in range(3))
    camera_data.ortho_scale = radius * 1.15
    source.hide_render = True
    for name, offset in {
        "three_quarter": Vector((radius * 0.9, -radius, radius * 0.28)),
        "side": Vector((radius * 1.4, 0, 0)),
    }.items():
        target.location = center
        camera.location = center + offset
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
    print("moved", moved, "limit", round(limit, 1), "triangles", len(rock.data.polygons))


if __name__ == "__main__":
    main()
