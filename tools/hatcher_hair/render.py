"""Headless Blender preview of the actual exported DFM triangles and UVs."""
import bpy, json, sys
from pathlib import Path
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]
source=Path(args[0]).resolve(); data=json.loads(source.read_text())
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
for group in data['groups']:
    vertices=[]; uvs=[]; faces=[]; lookup={}; normals=[]
    for face in group['faces']:
        indices=[]
        for index in face:
            p=data['points'][data['point_indices'][index]]
            point=data['point_indices'][index]
            if 'normals' in data:
                n=data['normals'][point];normals.append((n[0],-n[2],n[1]))
            if point not in lookup:
                lookup[point]=len(vertices);vertices.append((p[0],-p[2],p[1]))
            indices.append(lookup[point])
            u,v=data['uv'][data['uv_indices'][index]]; uvs.append((u,v))
        faces.append(indices)
    mesh=bpy.data.meshes.new(group['name']);mesh.from_pydata(vertices,[],faces);mesh.update()
    obj=bpy.data.objects.new(group['name'],mesh);bpy.context.collection.objects.link(obj)
    uv=mesh.uv_layers.new()
    for loop in mesh.loops:uv.data[loop.index].uv=uvs[loop.index]
    for poly in mesh.polygons:poly.use_smooth=True
    if normals:mesh.normals_split_custom_set(normals)
    mat=bpy.data.materials.new(group['name']);mat.use_nodes=True
    shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.72
    shader.inputs['Specular IOR Level'].default_value=.18
    if group.get('texture'):
        image=mat.node_tree.nodes.new('ShaderNodeTexImage');image.image=bpy.data.images.load(group['texture'])
        mat.node_tree.links.new(image.outputs['Color'],shader.inputs['Base Color'])
    else:shader.inputs['Base Color'].default_value=(.025,.015,.01,1)
    mesh.materials.append(mat)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24
scene.render.resolution_x=700;scene.render.resolution_y=850;scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12);scene.view_settings.view_transform='Standard'
for loc,power,size in [((-.3,-.5,.5),12,.45),((.4,-.2,.15),5,.35),((0,.3,.4),10,.3)]:
    bpy.ops.object.light_add(type='AREA',location=loc);lamp=bpy.context.object;lamp.data.energy=power*.25;lamp.data.shape='DISK';lamp.data.size=size
    lamp.rotation_euler=(Vector((0,0,.025))-lamp.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();camera=bpy.context.object;scene.camera=camera
camera.data.type='ORTHO';camera.data.ortho_scale=.36
for label,loc in [('front',(0,-.8,.02)),('side',(.8,0,.02)),('threequarter',(.55,-.65,.03)),('opposite_side',(-.8,0,.02)),('opposite_threequarter',(-.55,-.65,.03))]:
    camera.location=loc;camera.rotation_euler=(Vector((0,0,.02))-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(source.with_name(source.stem+'_'+label+'.png'))
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(source.with_suffix('.blend')))

