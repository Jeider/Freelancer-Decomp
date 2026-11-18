"""Offline Blender comparison: original, geometry only, preview materials."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector

OUT=Path(__file__).resolve().parents[2]/'out/reichman_body_test_v3'
maps=json.loads((OUT/'preview_materials.json').read_text())
def load(mode,clay=False):
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    path=OUT/('before.json' if mode=='before' else 'after.json')
    if mode=='previous':path=OUT.parent/'reichman_body_test/after.json'
    data=json.loads(path.read_text())
    for group in data['groups']:
        vertices=[];uvs=[];faces=[];normals=[];lookup={}
        for face in group['faces']:
            polygon=[]
            for index in face:
                point=data['point_indices'][index];x,y,z=data['points'][point]
                if point not in lookup:lookup[point]=len(vertices);vertices.append((x,-z,y))
                polygon.append(lookup[point]);uvs.append(data['uv'][data['uv_indices'][index]])
                x,y,z=data['normals'][point];normals.append((x,-z,y))
            faces.append(polygon)
        mesh=bpy.data.meshes.new(group['name']);mesh.from_pydata(vertices,[],faces);mesh.update()
        obj=bpy.data.objects.new(group['name'],mesh);bpy.context.collection.objects.link(obj)
        layer=mesh.uv_layers.new()
        for loop in mesh.loops:layer.data[loop.index].uv=uvs[loop.index]
        for poly in mesh.polygons:poly.use_smooth=True
        mesh.normals_split_custom_set(normals)
        material=bpy.data.materials.new(group['name']);material.use_nodes=True
        nodes=material.node_tree.nodes;links=material.node_tree.links;shader=nodes.get('Principled BSDF')
        shader.inputs['Roughness'].default_value=.72;shader.inputs['Specular IOR Level'].default_value=.18
        shader.inputs['Base Color'].default_value=(.32,.36,.40,1)
        if not clay:
            tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(group['texture'],check_existing=True)
            links.new(tex.outputs['Color'],shader.inputs['Base Color'])
            if mode in ('full','previous'):
                details=maps[group['name']] if mode!='previous' else json.loads((OUT.parent/'reichman_body_test/preview_materials.json').read_text())[group['name']]
                normaltex=nodes.new('ShaderNodeTexImage');normaltex.image=bpy.data.images.load(details['normal'],check_existing=True);normaltex.image.colorspace_settings.name='Non-Color'
                normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.8;links.new(normaltex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],shader.inputs['Normal'])
                surf=nodes.new('ShaderNodeTexImage');surf.image=bpy.data.images.load(details['surface'],check_existing=True);surf.image.colorspace_settings.name='Non-Color'
                split=nodes.new('ShaderNodeSeparateColor');links.new(surf.outputs['Color'],split.inputs['Color'])
                links.new(split.outputs['Red'],shader.inputs['Roughness']);links.new(split.outputs['Green'],shader.inputs['Metallic'])
        mesh.materials.append(material)
    for location,power,size in [((-1.5,2.3,2.5),180,2.0),((1.8,1.4,1.0),100,1.8),((0,-1.8,1.6),130,1.5)]:
        bpy.ops.object.light_add(type='AREA',location=location);lamp=bpy.context.object;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size
        lamp.rotation_euler=(Vector((0,0,.2))-lamp.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();camera=bpy.context.object;bpy.context.scene.camera=camera;camera.data.type='ORTHO'
    return camera

scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1000;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world.color=(.10,.10,.10);scene.view_settings.view_transform='AgX'
views=[('full',(0,3,.10),(0,0,-.15),1.85),('chest',(0,3,.48),(0,0,.40),.65),('quarter',(1.8,3,.9),(0,0,.38),.82),('back',(1.3,-3,.7),(0,0,.34),.95)]
updated='--updated' in sys.argv
for mode in (['geometry','full'] if updated else ['before','geometry','full','previous']):
    camera=load(mode)
    for label,location,target,scale in views:
        camera.location=location;camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
        scene.render.filepath=str(OUT/(mode+'_'+label+'.png'));bpy.ops.render.render(write_still=True)
for mode in (['geometry'] if updated else ['before','geometry','previous']):
    camera=load(mode,True);camera.location=(1.8,3,.9);camera.rotation_euler=(Vector((0,0,.38))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=.82
    scene.render.filepath=str(OUT/(mode+'_clay.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'comparison.blend'))
