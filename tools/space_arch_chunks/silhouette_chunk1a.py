"""Rebuild chunk1a from the source silhouette, with a deeper canyon. No extra triangles."""
import math
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector

TOPIC = Path(r"D:\work\Freelancer-Decomp\out\space_arch_chunks\chunk1a")
SOURCE = TOPIC / "arch_ast1_source.obj"
OUT = TOPIC / "preview"


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.preferences.filepaths.file_preview_type = "NONE"


def load_points():
    points = []
    for line in SOURCE.read_text(encoding="ascii").splitlines():
        if line.startswith("v "):
            points.append([float(value) for value in line.split()[1:4]])
    return np.array(points, dtype=np.float64)


def outline(band, count, canyon):
    center = band.mean(0)
    delta = band - center
    angle = np.arctan2(delta[:, 1], delta[:, 0])
    radius = np.linalg.norm(delta[:, :2], axis=1)
    order = np.argsort(angle)
    # Keep the real spur and the outer corners; do not average them away.
    chosen = order[np.linspace(0, len(order) - 1, count, dtype=int)]
    points = band[chosen].copy()
    local = points - center
    local_radius = np.linalg.norm(local[:, :2], axis=1)
    cleft = np.exp(-((np.arctan2(local[:, 1], local[:, 0]) + math.pi / 2) / 0.5) ** 2)
    scale = 1.0 - canyon * cleft
    points[:, 0] = center[0] + local[:, 0] * scale
    points[:, 1] = center[1] + local[:, 1] * scale
    points[:, 2] = center[2]
    return points


def build(points):
    lo, hi = points.min(0), points.max(0)
    height = hi[2] - lo[2]
    edges = np.linspace(lo[2], hi[2], 7)
    rings = []
    for index in range(6):
        band = points[(points[:, 2] >= edges[index]) & (points[:, 2] < edges[index + 1] + 1e-4)]
        if len(band) < 12:
            continue
        # Stronger canyon through the middle, none at the foot or the crest.
        weight = math.sin((index + 0.5) / 6 * math.pi)
        rings.append(outline(band, 10, 0.55 * weight))
    if len(rings) < 4:
        raise RuntimeError("not enough source slices")
    bm = bmesh.new()
    verts = [[bm.verts.new(Vector(point)) for point in ring] for ring in rings]
    for lower, upper in zip(verts, verts[1:]):
        count = len(lower)
        for index in range(count):
            nxt = (index + 1) % count
            bm.faces.new((lower[index], upper[index], lower[nxt]))
            bm.faces.new((lower[nxt], upper[index], upper[nxt]))
    for ring, downward in ((verts[0], True), (verts[-1], False)):
        center = bm.verts.new(sum((vert.co for vert in ring), Vector()) / len(ring))
        count = len(ring)
        for index in range(count):
            nxt = (index + 1) % count
            tri = (center, ring[nxt], ring[index]) if downward else (center, ring[index], ring[nxt])
            bm.faces.new(tri)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new("chunk1a_silhouette")
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new("chunk1a_silhouette", mesh)
    bpy.context.collection.objects.link(obj)
    return obj, height


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
    rock, _ = build(load_points())
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    source = bpy.context.selected_objects[0]
    source.name = "chunk1a_source"
    clay(rock, (0.66, 0.60, 0.52))
    clay(source, (0.42, 0.42, 0.40))
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1100
    scene.render.resolution_y = 820
    world = bpy.data.worlds.new("preview")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.13, 0.14, 0.15, 1)
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sun.data.energy = 5
    sun.rotation_euler = (0.65, 0.05, 0.35)
    bpy.ops.object.light_add(type="SUN")
    fill = bpy.context.object
    fill.data.energy = 0.6
    fill.rotation_euler = (-0.3, 1.1, -1.6)
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
    lo, hi, center = bounds([rock])
    radius = max(hi[i] - lo[i] for i in range(3))
    camera_data.ortho_scale = radius * 1.15
    source.hide_render = True
    for name, offset in {
        "front": Vector((0, -radius * 1.5, 0)),
        "side": Vector((radius * 1.5, 0, 0)),
        "top": Vector((0, 0, radius * 1.5)),
        "three_quarter": Vector((radius * 0.95, -radius * 1.05, radius * 0.28)),
    }.items():
        target.location = center
        camera.location = center + offset
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
    print("triangles", len(rock.data.polygons))


if __name__ == "__main__":
    main()
