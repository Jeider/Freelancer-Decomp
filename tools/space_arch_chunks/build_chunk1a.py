"""Author a new chunk1a silhouette inside the source bounds. No added triangle budget."""
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

TOPIC = Path(r"D:\work\Freelancer-Decomp\out\space_arch_chunks\chunk1a")
SOURCE = TOPIC / "arch_ast1_source.obj"
OUT = TOPIC / "preview"
# Source OBJ bounds: Blender X=FL X, Y=FL Z, Z=-FL Y.
BOX_MIN = Vector((-1884.0, -1457.8, -569.8))
BOX_MAX = Vector((2331.9, 1646.4, 3933.5))


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.preferences.filepaths.file_preview_type = "NONE"


def wrap(delta):
    return (delta + math.pi) % (2 * math.pi) - math.pi


def ring_points(height, scale, cleft, shelf, shear, offset):
    count = 14
    points = []
    for index in range(count):
        angle = (index / count) * math.tau
        bite = math.exp(-(wrap(angle + math.pi / 2) / 0.42) ** 2)
        radius = scale * (1.0 - cleft * bite)
        x = math.cos(angle) * radius + offset[0]
        y = math.sin(angle) * radius + offset[1]
        if abs(wrap(angle)) < 0.55:
            x = shear
        if abs(wrap(angle - math.pi / 2)) < 0.7 and shelf:
            y += shelf
            x -= shelf * 0.35
        points.append((x, y, height))
    return points


def place(point):
    size = BOX_MAX - BOX_MIN
    return Vector((
        BOX_MIN.x + (point[0] + 1.0) * 0.5 * size.x,
        BOX_MIN.y + (point[1] + 1.0) * 0.5 * size.y,
        BOX_MIN.z + point[2] * size.z,
    ))


def build():
    # Large planes only: a canyon, a flat break, a brow and a thick tooth.
    slices = [
        (0.08, 0.78, 0.15, 0.0, 0.55, (0.04, -0.08)),
        (0.24, 0.92, 0.42, 0.0, 0.62, (0.08, 0.02)),
        (0.42, 1.00, 0.72, 0.18, 0.58, (-0.04, 0.10)),
        (0.58, 0.90, 0.78, 0.34, 0.50, (0.02, 0.16)),
        (0.74, 0.70, 0.62, 0.08, 0.42, (-0.06, 0.04)),
        (0.90, 0.42, 0.35, 0.0, 0.28, (0.05, -0.02)),
    ]
    bm = bmesh.new()
    rings = []
    for height, scale, cleft, shelf, shear, offset in slices:
        verts = [bm.verts.new(place(point)) for point in ring_points(height, scale, cleft, shelf, shear, offset)]
        rings.append(verts)
    for lower, upper in zip(rings, rings[1:]):
        count = len(lower)
        for index in range(count):
            nxt = (index + 1) % count
            bm.faces.new((lower[index], upper[index], lower[nxt]))
            bm.faces.new((lower[nxt], upper[index], upper[nxt]))
    for ring, downward in ((rings[0], True), (rings[-1], False)):
        center = bm.verts.new(sum((vert.co for vert in ring), Vector()) / len(ring))
        count = len(ring)
        for index in range(count):
            nxt = (index + 1) % count
            tri = (center, ring[nxt], ring[index]) if downward else (center, ring[index], ring[nxt])
            bm.faces.new(tri)
    # Thick broken tooth, not a needle. Four faces, still inside the box.
    tooth = rings[0][8:12]
    drop = (BOX_MAX.z - BOX_MIN.z) * 0.16
    dropped = [bm.verts.new(vert.co + Vector((40, -80, -drop))) for vert in tooth]
    for index in range(len(tooth) - 1):
        bm.faces.new((tooth[index], dropped[index], tooth[index + 1]))
        bm.faces.new((tooth[index + 1], dropped[index], dropped[index + 1]))
    tip = bm.verts.new(sum((vert.co for vert in dropped), Vector()) / len(dropped) + Vector((0, -60, -drop * 0.35)))
    for index in range(len(dropped)):
        nxt = (index + 1) % len(dropped)
        bm.faces.new((dropped[index], tip, dropped[nxt]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("chunk1a_form")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("chunk1a_form", mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def clay(obj, color):
    material = bpy.data.materials.new(obj.name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.8
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
    rock = build()
    clay(rock, (0.62, 0.58, 0.52))
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    source = bpy.context.selected_objects[0]
    source.name = "chunk1a_source"
    clay(source, (0.48, 0.48, 0.46))
    lo, hi, _ = bounds([rock])
    gap = (hi.x - lo.x) + 900
    source.location.x -= gap * 0.55
    rock.location.x += gap * 0.45
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1200
    scene.render.resolution_y = 860
    world = bpy.data.worlds.new("preview")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.14, 0.15, 0.16, 1)
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sun.data.energy = 5
    sun.rotation_euler = (0.7, 0.1, 0.4)
    bpy.ops.object.light_add(type="SUN")
    fill = bpy.context.object
    fill.data.energy = 1.1
    fill.data.color = (0.7, 0.78, 1)
    fill.rotation_euler = (-0.5, 1.0, -1.5)
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
    views = {
        "front": rock_center + Vector((0, -radius * 1.8, 0)),
        "side": rock_center + Vector((radius * 1.8, 0, 0)),
        "top": rock_center + Vector((0, 0, radius * 1.8)),
        "three_quarter": rock_center + Vector((radius * 1.15, -radius * 1.25, radius * 0.35)),
    }
    camera_data.ortho_scale = radius * 1.22
    source.hide_render = True
    for name, location in views.items():
        target.location = rock_center
        camera.location = location
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
    source.hide_render = False
    frame_lo, frame_hi, frame_center = bounds([source, rock])
    target.location = frame_center
    camera_data.ortho_scale = max(frame_hi[i] - frame_lo[i] for i in range(3)) * 1.12
    camera.location = frame_center + Vector((radius, -radius * 1.3, radius * 0.25))
    scene.render.resolution_x = 1500
    scene.render.resolution_y = 820
    scene.render.filepath = str(OUT / "comparison")
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(TOPIC / "chunk1a_form_preview.blend"))
    print("triangles", len(rock.data.polygons), "source", len(source.data.polygons))
    print("extent", [round(rock_hi[i] - rock_lo[i], 1) for i in range(3)])


if __name__ == "__main__":
    main()
