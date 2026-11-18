"""Matched native/new comparisons and compact editable Blender scenes."""
import argparse
import gzip
import json
import os
from pathlib import Path
import sys
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from blender_workspace import configure as configure_blender_workspace
configure_blender_workspace('character_rounding')
OUT=ROOT/'out/character_rounding/contours_2k'
ap=argparse.ArgumentParser();ap.add_argument('--name',action='append');ap.add_argument('--details',action='store_true')
ap.add_argument('--view',action='append')
ap.add_argument('--package',choices=['contours_2k','bracer_starts','hero_bodies'],default='contours_2k')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
OUT=OUT.parent/args.package
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=12 if args.details or args.view else 8
scene.render.resolution_x=1100 if args.details or args.view else 960
scene.render.resolution_y=780 if args.details or args.view else 680
scene.render.resolution_percentage=100
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    if any(d.type=='OPTIX' for d in prefs.devices):
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
except Exception as error:print('CPU render fallback:',error,flush=True)
scene.world.color=(.13,.13,.13);scene.view_settings.view_transform='AgX'
bpy.context.preferences.filepaths.save_version=0


def clear():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for collection in list(bpy.data.collections):
        if collection.name!='Collection':bpy.data.collections.remove(collection)
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    for text in list(bpy.data.texts):
        if text.name.startswith('README - native DFM metadata'):bpy.data.texts.remove(text)


def model(data, collection, select=lambda g,t:True, clay=False, clips=()):
    result=[]
    for group in data['groups']:
        tris=[t for t in group['faces'] if select(group,t)]
        if not tris:continue
        points=[];faces=[];uv=[];normals=[];lookup={}
        for tri in tris:
            face=[]
            for index in tri:
                if index not in lookup:
                    lookup[index]=len(points);x,y,z=data['points'][data['point_indices'][index]];points.append((x,-z,y))
                face.append(lookup[index]);uv.append(data['uv'][data['uv_indices'][index]])
                x,y,z=data['normals'][data['point_indices'][index]];normals.append((x,-z,y))
            faces.append(face)
        me=bpy.data.meshes.new(group['name']);me.from_pydata(points,[],faces);me.update()
        ob=bpy.data.objects.new(group['name'],me);collection.objects.link(ob);result.append(ob)
        uvmap=me.uv_layers.new(name='UV0')
        for loop in me.loops:uvmap.data[loop.index].uv=uv[loop.index]
        for f in me.polygons:f.use_smooth=True
        me.normals_split_custom_set(normals)
        for bone,name in data.get('bones',{}).items():
            vg=ob.vertex_groups.new(name=name)
            for logical,vertex in lookup.items():
                w=data['skin'][logical].get(bone,0)
                if w:vg.add([vertex],w,'REPLACE')
        mat=bpy.data.materials.new(group['name']);mat.use_nodes=True
        bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.72
        bs.inputs['Specular IOR Level'].default_value=.18;bs.inputs['Base Color'].default_value=(.38,.43,.48,1)
        if not clay and group['texture']:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(group['texture'],check_existing=True)
            mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        if clips:
            nodes=mat.node_tree.nodes;links=mat.node_tree.links
            coords=nodes.new('ShaderNodeTexCoord');xyz=nodes.new('ShaderNodeSeparateXYZ');links.new(coords.outputs['Object'],xyz.inputs[0])
            mask=None
            for axis,operation,value in clips:
                test=nodes.new('ShaderNodeMath');test.operation=operation;links.new(xyz.outputs[axis],test.inputs[0]);test.inputs[1].default_value=value
                if mask is None:mask=test.outputs[0]
                else:
                    product=nodes.new('ShaderNodeMath');product.operation='MULTIPLY';links.new(mask,product.inputs[0]);links.new(test.outputs[0],product.inputs[1]);mask=product.outputs[0]
            transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
            links.new(mask,mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(bs.outputs[0],mix.inputs[2])
            links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
        me.materials.append(mat)
    return result


def collection(name):
    c=bpy.data.collections.new(name);scene.collection.children.link(c);return c


def setup(direction):
    for loc,power,size in [((-2,3,3),260,3),((3,2,1),130,2),((0,-3,2),180,2)]:
        bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.data.energy=power;ob.data.size=size
        ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=direction);cam=bpy.context.object;cam.data.type='ORTHO'
    cam.rotation_euler=(-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    return cam


def comparison(folder,before,after,label):
    clear();clay=label.endswith('_clay');kind=label.removesuffix('_clay')
    clips=[]
    if kind=='cuff':clips=[('X','GREATER_THAN',.19),('Z','GREATER_THAN',-.11),('Z','LESS_THAN',.22)]
    if kind=='bracer_start':
        r=json.loads((folder/'report.json').read_text());profile=next(p for p in r['profiles'] if p['side']==1);y=profile['center'][1]
        clips=[('X','GREATER_THAN',.17),('Z','GREATER_THAN',y-.07),('Z','LESS_THAN',y+.08)]
    if kind=='epaulette':clips=[('X','GREATER_THAN',.125),('Z','GREATER_THAN',.47)]
    if kind=='vest':clips=[('X','GREATER_THAN',-.235),('X','LESS_THAN',.235),('Z','GREATER_THAN',.16)]
    if kind in ('upper_edges','upper_back'):clips=[('X','GREATER_THAN',-.245),('X','LESS_THAN',.245),('Z','GREATER_THAN',.40)]
    def select(data):
        def chosen(g,t):
            if kind=='belt':return g['name']=='hatcher_body_4'
            return True
        return chosen
    a=model(before,collection('BEFORE'),select(before),clay,clips)
    b=model(after,collection('AFTER'),select(after),clay,clips)
    direction=Vector((.8,4,-1.6)) if kind=='cuff' else Vector((.7,4,1.8)) if kind=='bracer_start' else Vector((.7,4,.5)) if kind in ('epaulette','belt','vest') else Vector((0,4,.12))
    if kind=='back':direction=Vector((0,-4,.12))
    if kind=='upper_edges':direction=Vector((.5,4,2.7))
    if kind=='upper_back':direction=Vector((.5,-4,2.7))
    cam=setup(direction);q=cam.rotation_euler.to_quaternion();right=q@Vector((1,0,0));up=q@Vector((0,1,0))
    def inside(p):
        return all((p['XYZ'.index(axis)]>value if op=='GREATER_THAN' else p['XYZ'.index(axis)]<value) for axis,op,value in clips)
    allpoints=[v.co for ob in a+b for v in ob.data.vertices if inside(v.co)]
    assert allpoints,'Empty detail: '+label
    center=Vector([(min(p[i] for p in allpoints)+max(p[i] for p in allpoints))/2 for i in range(3)])
    width=max(p.dot(right) for p in allpoints)-min(p.dot(right) for p in allpoints)
    height=max(p.dot(up) for p in allpoints)-min(p.dot(up) for p in allpoints)
    gap=width*.6+.012
    for obs,sign in ((a,-1),(b,1)):
        for ob in obs:ob.location=-center+right*(gap*sign)
    cam.data.ortho_scale=max(height*scene.render.resolution_x/scene.render.resolution_y*1.13,(2*gap+width)*1.12)
    scene.render.filepath=str(folder/(label+'.png'));bpy.ops.render.render(write_still=True)


def save_editable(folder,before,after,report):
    clear();native=collection('SOURCE - native geometry');edited=collection('EDIT - hero body' if args.package=='hero_bodies' else 'EDIT - contours 2k')
    model(before,native);objects=model(after,edited)
    native.hide_viewport=True;native.hide_render=True
    cam=setup(Vector((0,4,.12)));cam.location.z=-.15;cam.data.ortho_scale=2.0
    text=bpy.data.texts.new('README - native DFM metadata')
    text.write(json.dumps(dict(report=report,native_bones=after['bones'],
        note='Editable rest-pose meshes with UVs, normals and native weight groups. No animation rig. Source collection is hidden. Textures are linked to the existing shared exports.'),indent=2))
    for ob in bpy.context.selected_objects:ob.select_set(False)
    for ob in objects:ob.select_set(True)
    if objects:bpy.context.view_layer.objects.active=objects[0]
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_distance=2.2;area.spaces.active.region_3d.view_location=(0,0,-.15)
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/('hero_body.blend' if args.package=='hero_bodies' else 'contours_2k.blend')),compress=True)


for folder in sorted(OUT.iterdir()):
    if not (folder/'report.json').exists() or (args.name and folder.name not in args.name):continue
    report=json.loads((folder/'report.json').read_text());cache=folder/'render_source.json'
    before=json.loads(gzip.decompress((folder/'before.json.gz').read_bytes()));after=json.loads(gzip.decompress((folder/'after.json.gz').read_bytes()))
    labels=['front','back']
    if args.details:
        labels+=['cuff','cuff_clay']
        if folder.name=='li_hatcher_body':labels+=['vest','vest_clay','belt','belt_clay']
        if folder.name=='rh_reichman_body':labels+=['epaulette','epaulette_clay']
    if args.view:labels=args.view
    previous=json.loads(cache.read_text()) if cache.exists() else {}
    same=previous.get('framing_revision')==2 and previous.get('sha256')==report['output_sha256']
    detail_ok=previous.get('detail_clipping_revision')==1 or all(v in ('front','back') for v in labels)
    if same and set(labels)<=set(previous.get('views',[])) and detail_ok:continue
    for label in labels:
        if same and label in previous.get('views',[]) and (label in ('front','back') or detail_ok):continue
        comparison(folder,before,after,label)
    save_editable(folder,before,after,report)
    views=sorted(set(labels+previous.get('views',[]))) if same else labels
    cache.write_text(json.dumps(dict(sha256=report['output_sha256'],views=views,original_on_left=True,offline_only=True,framing_revision=2,detail_clipping_revision=1)))
    print('CONTOUR_PREVIEW',folder.name,flush=True)
