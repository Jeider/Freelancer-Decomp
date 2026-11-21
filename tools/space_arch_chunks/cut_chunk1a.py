"""Cut a real canyon through the source cleft. No triangle budget above the source."""
import math
from pathlib import Path

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


def bounds(obj):
    points = [obj.matrix_world @ vert.co for vert in obj.data.vertices]
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
    rock.name = "chunk1a_cut"
    bpy.context.collection.objects.link(rock)
    lo, hi, center = bounds(rock)
    size = hi - lo
    bpy.ops.mesh.primitive_cube_add(location=center + Vector((0, -size.y * 0.08, size.z * 0.08)))
    cutter = bpy.context.object
    cutter.scale = (size.x * 0.045, size.y * 0.42, size.z * 0.34)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    bpy.context.view_layer.objects.active = rock
    rock.select_set(True)
    modifier = rock.modifiers.new("canyon", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter
    modifier.solver = "FLOAT"
    bpy.ops.object.modifier_apply(modifier="canyon")
    cutter.hide_render = True
    bpy.context.view_layer.objects.active = rock
    dissolve = rock.modifiers.new("planes", "DECIMATE")
    dissolve.decimate_type = "DISSOLVE"
    dissolve.angle_limit = math.radians(6)
    bpy.ops.object.modifier_apply(modifier="planes")
    clay(source, (0.45, 0.45, 0.43))
    clay(rock, (0.63, 0.58, 0.51))
    rock_lo, rock_hi, rock_center = bounds(rock)
    gap = (rock_hi.x - rock_lo.x) + 800
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
    sun.rotation_euler = (0.75, 0.1, 0.45)
    bpy.ops.object.light_add(type="SUN")
    fill = bpy.context.object
    fill.data.energy = 0.7
    fill.rotation_euler = (-0.4, 1.0, -1.4)
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
    radius = max(rock_hi[i] - rock_lo[i] for i in range(3))
    camera_data.ortho_scale = radius * 1.2
    source.hide_render = True
    for name, offset in {
        "front": Vector((0, -radius * 1.7, 0)),
        "side": Vector((radius * 1.7, 0, 0)),
        "top": Vector((0, 0, radius * 1.7)),
        "three_quarter": Vector((radius * 1.05, -radius * 1.15, radius * 0.35)),
    }.items():
        target.location = rock_center
        camera.location = rock_center + offset
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
    source.hide_render = False
    frame_lo, frame_hi, frame_center = bounds(source)
    other_lo, other_hi, _ = bounds(rock)
    frame_lo = Vector((min(frame_lo[i], other_lo[i]) for i in range(3)))
    frame_hi = Vector((max(frame_hi[i], other_hi[i]) for i in range(3)))
    frame_center = (frame_lo + frame_hi) * 0.5
    target.location = frame_center
    camera_data.ortho_scale = max(frame_hi[i] - frame_lo[i] for i in range(3)) * 1.08
    camera.location = frame_center + Vector((radius * 0.85, -radius * 1.1, radius * 0.28))
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 780
    scene.render.filepath = str(OUT / "comparison")
    bpy.ops.render.render(write_still=True)
    print("triangles", len(rock.data.polygons), "source", len(source.data.polygons))


if __name__ == "__main__":
    main()
