"""Matched epaulette views and a compact editable file with native weight groups."""
import sys,json,math,warnings,gzip,hashlib
from pathlib import Path
warnings.filterwarnings('ignore',category=DeprecationWarning)
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from blender_workspace import configure
configure('character_rounding')
OUT=ROOT/'out/character_rounding/epaulettes'
TARGETS=('rh_reichman_body','rh_deidrich_body')
def load(path):return json.loads(gzip.decompress(path.read_bytes()))
def digest(data):return hashlib.sha256(data).hexdigest()


def cv(p):return Vector((p[0],-p[2],p[1]))


def model(data,collection):
    for group in data['groups']:
        vertices=[];polys=[];uv=[];normals=[];lookup={}
        for t in group['faces']:
            face=[]
            for i in t:
                if i not in lookup:lookup[i]=len(vertices);vertices.append(cv(data['points'][data['point_indices'][i]]))
                face.append(lookup[i]);uv.append(data['uv'][data['uv_indices'][i]])
                normals.append(cv(data['normals'][data['point_indices'][i]]))
            polys.append(face)
        mesh=bpy.data.meshes.new(group['name']);mesh.from_pydata(vertices,[],polys);mesh.update()
        ob=bpy.data.objects.new(group['name'],mesh);collection.objects.link(ob)
        layer=mesh.uv_layers.new(name='UV0')
        for loop in mesh.loops:layer.data[loop.index].uv=uv[loop.index]
        for f in mesh.polygons:f.use_smooth=True
        mesh.normals_split_custom_set(normals)
        for bone,name in data['bones'].items():
            vg=ob.vertex_groups.new(name=name)
            for logical,vertex in lookup.items():
                w=data['skin'][logical].get(bone,0)
                if w:vg.add([vertex],w,'REPLACE')
        mat=bpy.data.materials.new(group['name']);mat.use_nodes=True;mat.use_backface_culling=True
        bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65
        bs.inputs['Specular IOR Level'].default_value=.2
        if group['texture']:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(group['texture'],check_existing=True)
            mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
        mesh.materials.append(mat)


def main():
    for name in TARGETS:
        folder=OUT/name;report=json.loads((folder/'report.json').read_text())
        before=load(folder/'before.json.gz');after=load(folder/'after.json.gz')
        bpy.ops.wm.read_factory_settings(use_empty=True);configure('character_rounding');scene=bpy.context.scene
        scene['geometry_sha256']=report['geometry_sha256'];scene['source_sha256']=report['source_sha256']
        scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True
        scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
        scene.world=bpy.data.worlds.new('Studio');scene.world.use_nodes=True
        scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.13,.13,.13,1)
        scene.view_settings.view_transform='AgX'
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        if any(d.use for d in prefs.devices):scene.cycles.device='GPU'
        old=bpy.data.collections.new('ARCHIVE - installed body - disabled');new=bpy.data.collections.new('EDIT - epaulettes')
        scene.collection.children.link(old);scene.collection.children.link(new);model(before,old);model(after,new)
        for loc,power,size in [((-1,2,2),100,1.6),((2,1,1),70,1.2),((0,-2,1.5),100,1.5)]:
            ld=bpy.data.lights.new('Softbox','AREA');ld.energy=power;ld.size=size
            ob=bpy.data.objects.new(ld.name,ld);scene.collection.objects.link(ob);ob.location=loc
            ob.rotation_euler=(cv((0,.45,0))-ob.location).to_track_quat('-Z','Y').to_euler()
        cam=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));scene.collection.objects.link(cam);scene.camera=cam
        cam.data.type='ORTHO';cam.data.clip_start=.001
        clay=bpy.data.materials.new('Diagnostic clay');clay.use_nodes=True
        clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.36,.40,.44,1)
        shots=[('upper_front',(0,.46,0),(0,1,.15),.72),('upper_back',(0,.46,0),(0,-1,.2),.72),
               ('right_front',(.216,.55,0),(.65,1,.55),.30),('right_top',(.216,.55,0),(.25,.25,1),.30),
               ('right_rear',(.216,.55,0),(.6,-1,.4),.30),('left_front',(-.216,.55,0),(-.65,1,.55),.30)]
        for label,center,direction,scale in shots:
            target=cv(center);direction=Vector(direction).normalized();cam.location=target+direction*1.2
            cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
            for style in ('textured','clay'):
                scene.view_layers[0].material_override=clay if style=='clay' else None
                for mode in ('before','after'):
                    old.hide_viewport=old.hide_render=mode=='after';new.hide_viewport=new.hide_render=mode=='before'
                    scene.render.filepath=str(folder/f'{label}_{style}_{mode}.png');bpy.ops.render.render(write_still=True)
        old.hide_viewport=old.hide_render=True;new.hide_viewport=new.hide_render=False;scene.view_layers[0].material_override=None
        target=cv((0,.46,0));direction=Vector((0,1,.15)).normalized();cam.location=target+direction*1.2
        cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.72
        metadata=bpy.data.texts.new('README - native DFM data')
        metadata.write(json.dumps(dict(report=report,note='Editable meshes with native UV0 and weight groups, no animation rig. Current textures linked to shared authoring exports. Original collection disabled in viewport and render.'),indent=2))
        blend=folder/'epaulettes.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend),compress=True)
        bpy.ops.wm.open_mainfile(filepath=str(blend));configure('character_rounding')
        old=bpy.data.collections['ARCHIVE - installed body - disabled'];new=bpy.data.collections['EDIT - epaulettes']
        assert old.hide_render and old.hide_viewport and not new.hide_render and not new.hide_viewport
        assert sum(len(ob.data.polygons) for ob in new.objects)==report['triangles_after']
        assert all(Path(bpy.path.abspath(im.filepath)).exists() for im in bpy.data.images if im.source=='FILE')
        (folder/'preview_validation.json').write_text(json.dumps(dict(geometry_sha256=report['geometry_sha256'],blend_sha256=digest(blend.read_bytes()),
            reopened=True,original_hidden_in_viewport_and_render=True,views=[s[0] for s in shots],offline_only=True),indent=2))
        print('PREVIEW_COMPLETE',name,flush=True)


def culling_preview():
    for name in TARGETS:
        folder=OUT/name;report=json.loads((folder/'preview_validation.json').read_text())
        bpy.ops.wm.open_mainfile(filepath=str(folder/'epaulettes.blend'));configure('character_rounding')
        scene=bpy.context.scene;assert scene['geometry_sha256']==report['geometry_sha256']
        mat=bpy.data.materials.new('True back-face culling diagnostic');mat.use_nodes=True
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
        bs.inputs['Base Color'].default_value=(.36,.40,.44,1)
        geo=nodes.new('ShaderNodeNewGeometry');transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
        links.new(geo.outputs['Backfacing'],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2])
        links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface']);scene.view_layers[0].material_override=mat
        for label,direction in [('front',(.65,1,.3)),('rear',(.65,-1,.3))]:
            target=cv((.216,.55,0));direction=Vector(direction).normalized();cam=scene.camera
            cam.location=target+direction*1.2;cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.30
            scene.render.filepath=str(folder/f'culling_{label}.png');bpy.ops.render.render(write_still=True)
        (folder/'culling_validation.json').write_text(json.dumps(dict(geometry_sha256=report['geometry_sha256'],
            actual_backface_transparency=True,views=['culling_front.png','culling_rear.png'],blend_unchanged=True),indent=2))
        assert digest((folder/'epaulettes.blend').read_bytes())==report['blend_sha256']
        print('CULLING_PREVIEW_COMPLETE',name,flush=True)


if __name__=='__main__':
    if '--culling-only' in sys.argv:culling_preview()
    else:main()
