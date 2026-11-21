"""Clay views of the source chunk1a. Working files stay in the topic cache."""
import bpy
from pathlib import Path

TOPIC = Path(r"D:\work\Freelancer-Decomp\out\space_arch_chunks\chunk1a")
SOURCE = TOPIC / "arch_ast1_source.obj"
OUT = TOPIC / "source_preview"


def clear():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    prefs = bpy.context.preferences.filepaths
    prefs.save_version = 0
    prefs.file_preview_type = "NONE"


def main():
    clear()
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.obj_import(filepath=str(SOURCE))
    rock = bpy.context.selected_objects[0]
    rock.name = "chunk1a_source"
    bpy.context.view_layer.objects.active = rock
    bpy.ops.object.shade_smooth()
    material = bpy.data.materials.new("clay")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.55, 0.50, 0.44, 1)
    bsdf.inputs["Roughness"].default_value = 0.72
    rock.data.materials.append(material)
    points = [rock.matrix_world @ v.co for v in rock.data.vertices]
    lo = [min(p[i] for p in points) for i in range(3)]
    hi = [max(p[i] for p in points) for i in range(3)]
    center = [(lo[i] + hi[i]) * 0.5 for i in range(3)]
    radius = max((hi[i] - lo[i]) for i in range(3)) * 0.65
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 0))
    sun = bpy.context.object
    sun.data.energy = 3.5
    sun.rotation_euler = (0.9, 0.2, 0.6)
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 0))
    fill = bpy.context.object
    fill.data.energy = 1.2
    fill.data.color = (0.75, 0.82, 1)
    fill.rotation_euler = (-0.4, 0.8, -1.2)
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.film_transparent = False
    world = bpy.data.worlds.new("preview")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.16, 0.17, 0.18, 1)
    background.inputs["Strength"].default_value = 1
    views = {
        "front": ((center[0], center[1] - radius * 2.4, center[2]), (1.15, 0, 0)),
        "side": ((center[0] + radius * 2.4, center[1], center[2]), (1.15, 0, 1.5708)),
        "top": ((center[0], center[1], center[2] + radius * 2.6), (0, 0, 0)),
        "three_quarter": ((center[0] + radius * 1.7, center[1] - radius * 1.9, center[2] + radius * 0.7), (1.05, 0, 0.75)),
    }
    camera_data = bpy.data.cameras.new("view")
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = max(hi[i] - lo[i] for i in range(3)) * 1.25
    camera_data.clip_start = 1
    camera_data.clip_end = 100000
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
    for name, (location, rotation) in views.items():
        camera.location = location
        scene.render.filepath = str(OUT / name)
        bpy.ops.render.render(write_still=True)
    print("source_triangles", len(rock.data.polygons))
    print("preview", OUT)


if __name__ == "__main__":
    main()
