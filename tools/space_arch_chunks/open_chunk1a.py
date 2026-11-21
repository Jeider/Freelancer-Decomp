"""Open the existing cleft and raise one crest. Same 289 triangles."""
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
    bsdf.inputs["Roughness"].default_value = 0.76
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.shade_flat()
    obj.select_set(False)


def bounds(obj):
    points = [obj.matrix_world @ vert.co for vert in obj.data.vertices]
    lo = Vector((min(point[i] for point in points) for i in range(3)))
    hi = Vector((max(point[i] for point in points) for i in range(3)))
    return lo, hi, (lo + hi) * 0.5


def open_cleft(obj):
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    xs = [vert.co.x for vert in bm.verts]
    ys = [vert.co.y for vert in bm.verts]
    zs = [vert.co.z for vert in bm.verts]
    lo = Vector((min(xs), min(ys), min(zs)))
    hi = Vector((max(xs), max(ys), max(zs)))
    center = (lo + hi) * 0.5
    size = hi - lo
    for vert in bm.verts:
        local = Vector((
            (vert.co.x - center.x) / (size.x * 0.5),
            (vert.co.y - center.y) / (size.y * 0.5),
            (vert.co.z - center.z) / (size.z * 0.5),
        ))
        near = math.exp(-((local.x / 0.22) ** 2))
        mouth = max(0.0, 0.35 - local.y)
        cleft = near * mouth
        if cleft > 0.02:
            vert.co.x += math.copysign(cleft * size.x * 0.16, local.x if abs(local.x) > 0.01 else 1.0)
            vert.co.z -= cleft * size.z * 0.20
            vert.co.y -= cleft * size.y * 0.06
        if local.x > 0.25 and local.z > 0.2:
            vert.co.z += (local.x - 0.25) * (local.z - 0.2) * size.z * 0.22
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def look(camera, target):
    constraint = camera.constraints.new("TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"


def render_object(scene, camera, target, obj, folder, names):
    lo, hi, center = bounds(obj)
    radius = max(hi[i] - lo[i] for i in range(3))
    camera.data.ortho_scale = radius * 1.18
    offsets = {
        "front": Vector((0, -radius * 1.6, 0)),
        "side": Vector((radius * 1.6, 0, 0)),
        "top": Vector((0, 0, radius * 1.6)),
        "three_quarter": Vector((radius, -radius * 1.1, radius * 0.32)),
    }
    for name in names:
        target.location = center
        camera.location = center + offsets[name]
        scene.render.filepath = str(folder / name)
        bpy.ops.render.render(write_still=True)


def main():
    clear()
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    source = bpy.context.selected_objects[0]
    source.name = "chunk1a_source"
    rock = source.copy()
    rock.data = source.data.copy()
    rock.name = "chunk1a_open"
    bpy.context.collection.objects.link(rock)
    open_cleft(rock)
    clay(source, (0.45, 0.45, 0.43))
    clay(rock, (0.64, 0.58, 0.50))
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
    sun.data.energy = 4.8
    sun.rotation_euler = (0.72, 0.08, 0.4)
    bpy.ops.object.light_add(type="SUN")
    fill = bpy.context.object
    fill.data.energy = 0.9
    fill.data.color = (0.72, 0.8, 1)
    fill.rotation_euler = (-0.35, 1.05, -1.5)
    camera_data = bpy.data.cameras.new("view")
    camera_data.type = "ORTHO"
    camera_data.clip_start = 1
    camera_data.clip_end = 100000
    camera = bpy.data.objects.new("view", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    target = bpy.data.objects.new("target", None)
    scene.collection.objects.link(target)
    look(camera, target)
    source.hide_render = True
    render_object(scene, camera, target, rock, OUT, ("front", "side", "top", "three_quarter"))
    source.hide_render = False
    lo, hi, _ = bounds(rock)
    gap = (hi.x - lo.x) + 900
    source.location.x -= gap * 0.55
    rock.location.x += gap * 0.45
    frame = bounds(source)[0]
    other = bounds(rock)
    frame_lo = Vector((min(frame[i], other[0][i]) for i in range(3)))
    frame_hi = Vector((max(bounds(source)[1][i], other[1][i]) for i in range(3)))
    center = (frame_lo + frame_hi) * 0.5
    radius = max(frame_hi[i] - frame_lo[i] for i in range(3))
    target.location = center
    camera.data.ortho_scale = radius * 1.05
    camera.location = center + Vector((radius * 0.35, -radius * 0.85, radius * 0.18))
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 780
    scene.render.filepath = str(OUT / "comparison")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(TOPIC / "chunk1a_open_preview.blend"))
    print("triangles", len(rock.data.polygons))
    print("extent", [round(hi[i] - lo[i], 1) for i in range(3)])


if __name__ == "__main__":
    main()
