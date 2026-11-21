"""New chunk1a topology shrinkwrapped to the original silhouette. Source verts stay put."""
from pathlib import Path

import bpy
from mathutils import Vector

TOPIC = Path(r"D:\work\Freelancer-Decomp\out\space_arch_chunks\chunk1a")
SOURCE = TOPIC / "arch_ast1_source.obj"
OUT = TOPIC / "inspired"


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.context.preferences.filepaths.file_preview_type = "NONE"


def bounds(obj):
    points = [obj.matrix_world @ vert.co for vert in obj.data.vertices]
    lo = Vector((min(point[i] for point in points) for i in range(3)))
    hi = Vector((max(point[i] for point in points) for i in range(3)))
    return lo, hi, (lo + hi) * 0.5


def clay(obj, color, flat):
    material = bpy.data.materials.new(obj.name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.74
    obj.data.materials.append(material)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    if flat:
        bpy.ops.object.shade_flat()
    else:
        bpy.ops.object.shade_smooth()
    obj.select_set(False)


def build(source):
    lo, hi, center = bounds(source)
    size = hi - lo
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=center)
    rock = bpy.context.object
    rock.name = "chunk1a_new"
    rock.scale = size * 0.55
    bpy.ops.object.transform_apply(scale=True)
    wrap = rock.modifiers.new("fit", "SHRINKWRAP")
    wrap.target = source
    wrap.wrap_method = "PROJECT"
    wrap.use_project_x = wrap.use_project_y = wrap.use_project_z = True
    wrap.use_negative_direction = True
    wrap.use_positive_direction = True
    wrap.project_limit = max(size) * 2
    bpy.context.view_layer.objects.active = rock
    rock.select_set(True)
    bpy.ops.object.modifier_apply(modifier="fit")
    rock.select_set(False)
    # Grain only. A few percent of the radius, then clamped back toward the fitted surface.
    fitted = [vert.co.copy() for vert in rock.data.vertices]
    texture = bpy.data.textures.new("grain", "CLOUDS")
    texture.noise_scale = max(size) * 0.08
    texture.noise_depth = 1
    grain = rock.modifiers.new("grain", "DISPLACE")
    grain.texture = texture
    grain.strength = max(size) * 0.012
    grain.mid_level = 0.5
    bpy.context.view_layer.objects.active = rock
    rock.select_set(True)
    bpy.ops.object.modifier_apply(modifier="grain")
    rock.select_set(False)
    for vert, origin in zip(rock.data.vertices, fitted):
        delta = vert.co - origin
        limit = max(size) * 0.02
        if delta.length > limit:
            vert.co = origin + delta.normalized() * limit
    rock.data.update()
    center = sum((vert.co for vert in rock.data.vertices), Vector()) / len(rock.data.vertices)
    radius = max((vert.co - center).length for vert in rock.data.vertices)
    source_radius = max((point - center).length for point in
                        (source.matrix_world @ vert.co for vert in source.data.vertices))
    if radius > source_radius * 1.08:
        raise RuntimeError(f"new mesh left the original mass: {radius:.1f} > {source_radius:.1f}")
    return rock


def main():
    clear()
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    source = bpy.context.selected_objects[0]
    source.name = "chunk1a_source"
    rock = build(source)
    clay(source, (0.42, 0.42, 0.40), True)
    clay(rock, (0.62, 0.56, 0.49), False)
    lo, hi, center = bounds(rock)
    span = max(hi[i] - lo[i] for i in range(3))
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
    fill.data.energy = 0.9
    fill.data.color = (0.75, 0.82, 1)
    fill.rotation_euler = (-0.35, 1.0, -1.4)
    camera_data = bpy.data.cameras.new("view")
    camera_data.type = "ORTHO"
    camera_data.clip_start = 1
    camera_data.clip_end = 100000
    camera_data.ortho_scale = span * 1.2
    camera = bpy.data.objects.new("view", camera_data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    target = bpy.data.objects.new("target", None)
    target.location = center
    scene.collection.objects.link(target)
    constraint = camera.constraints.new("TRACK_TO")
    constraint.target = target
    constraint.track_axis = "TRACK_NEGATIVE_Z"
    constraint.up_axis = "UP_Y"
    source.hide_render = True
    for name, offset in {
        "front": Vector((0, -span * 1.8, 0)),
        "side": Vector((span * 1.8, 0, 0)),
        "top": Vector((0, 0, span * 1.8)),
        "three_quarter": Vector((span * 1.15, -span * 1.25, span * 0.4)),
    }.items():
        camera.location = center + offset
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
    print("triangles", len(rock.data.polygons), "source", len(source.data.polygons))


if __name__ == "__main__":
    main()
