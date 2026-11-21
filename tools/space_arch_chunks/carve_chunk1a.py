"""Open the source cleft into a cave and thicken the spur. Triangle count stays at or below 289."""
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


def local_of(co, center, size):
    return Vector((
        (co.x - center.x) / (size.x * 0.5),
        (co.y - center.y) / (size.y * 0.5),
        (co.z - center.z) / (size.z * 0.5),
    ))


def carve(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bm.faces.ensure_lookup_table()
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    lo = Vector((min(xs), min(ys), min(zs)))
    hi = Vector((max(xs), max(ys), max(zs)))
    center = (lo + hi) * 0.5
    size = hi - lo
    opening = []
    for face in bm.faces:
        point = local_of(face.calc_center_median(), center, size)
        normal = face.normal
        in_notch = abs(point.x) < 0.22 and -0.55 < point.y < 0.08 and -0.05 < point.z < 0.55
        facing_out = normal.z > 0.15 or normal.y < -0.2
        if in_notch and facing_out:
            opening.append(face)
    if len(opening) < 8:
        raise RuntimeError(f"cleft selection too small: {len(opening)}")
    bmesh.ops.delete(bm, geom=opening, context="FACES")
    # A short lip, so the mouth has thickness instead of a paper edge.
    boundary = [edge for edge in bm.edges if edge.is_boundary]
    extruded = bmesh.ops.extrude_edge_only(bm, edges=boundary)
    new_verts = [item for item in extruded["geom"] if isinstance(item, bmesh.types.BMVert)]
    for vert in new_verts:
        point = local_of(vert.co, center, size)
        vert.co += Vector((point.x * size.x * 0.03, -size.y * 0.04, -size.z * 0.03))
    # Thicken the thin spur without shortening it.
    for vert in bm.verts:
        point = local_of(vert.co, center, size)
        if point.z < -0.35 and abs(point.x) < 0.35:
            vert.co.x += math.copysign(size.x * 0.03, point.x if abs(point.x) > 0.02 else 1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()
    return len(opening)


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


def bounds(objects):
    points = [obj.matrix_world @ vert.co for obj in objects for vert in obj.data.vertices]
    lo = Vector((min(point[i] for point in points) for i in range(3)))
    hi = Vector((max(point[i] for point in points) for i in range(3)))
    return lo, hi, (lo + hi) * 0.5


def main():
    clear()
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    source = bpy.context.selected_objects[0]
    source.name = "chunk1a_source"
    rock = source.copy()
    rock.data = source.data.copy()
    rock.name = "chunk1a_carved"
    bpy.context.collection.objects.link(rock)
    removed = carve(rock)
    clay(source, (0.46, 0.46, 0.44))
    clay(rock, (0.62, 0.57, 0.50))
    lo, hi, _ = bounds([rock])
    gap = (hi.x - lo.x) + 700
    source.location.x -= gap * 0.55
    rock.location.x += gap * 0.45
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
    sun.rotation_euler = (0.8, 0.15, 0.5)
    bpy.ops.object.light_add(type="SUN")
    fill = bpy.context.object
    fill.data.energy = 0.8
    fill.data.color = (0.7, 0.78, 1)
    fill.rotation_euler = (-0.4, 1.1, -1.6)
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
    rock_lo, rock_hi, rock_center = bounds([rock])
    radius = max(rock_hi[i] - rock_lo[i] for i in range(3))
    camera_data.ortho_scale = radius * 1.2
    source.hide_render = True
    views = {
        "front": Vector((0, -radius * 1.7, 0)),
        "side": Vector((radius * 1.7, 0, 0)),
        "top": Vector((0, 0, radius * 1.7)),
        "three_quarter": Vector((radius * 1.1, -radius * 1.2, radius * 0.4)),
    }
    for name, offset in views.items():
        target.location = rock_center
        camera.location = rock_center + offset
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
    source.hide_render = False
    frame_lo, frame_hi, frame_center = bounds([source, rock])
    target.location = frame_center
    camera_data.ortho_scale = max(frame_hi[i] - frame_lo[i] for i in range(3)) * 1.08
    camera.location = frame_center + Vector((radius * 0.9, -radius * 1.15, radius * 0.3))
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 780
    scene.render.filepath = str(OUT / "comparison")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(TOPIC / "chunk1a_carve_preview.blend"))
    print("removed", removed, "triangles", len(rock.data.polygons), "source", len(source.data.polygons))


if __name__ == "__main__":
    main()
