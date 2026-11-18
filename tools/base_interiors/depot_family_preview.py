"""Editable regional CMP previews with all door repetitions and whole walls."""
import sys,json,math,shutil
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from blender_workspace import configure
configure('base_interiors')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from depot_family_audit import paths,REGIONS
from native_common import sha,dump


def cv(v):return Vector((float(v[0]),-float(v[2]),float(v[1])))


def make_mesh(group,t,material,collection,suffix=''):
    key=group['key'];v=t.reshape(-1,t.shape[-1]);faces=np.arange(len(v)).reshape(-1,3)
    cross=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3])
    flip=np.einsum('ij,ij->i',cross,t[:,:,3:6].mean(1))<0
    faces[flip]=faces[flip][:,[0,2,1]]
    mesh=bpy.data.meshes.new(key+suffix)
    mesh.from_pydata([cv(p) for p in v[:,:3]],[],faces.tolist());mesh.update()
    for slot in range(group.get('uv_sets',(v.shape[-1]-6)//2)):
        uv=mesh.uv_layers.new(name=f'UV{slot}')
        for loop in mesh.loops:
            row=v[loop.vertex_index];uv.data[loop.index].uv=(row[6+slot*2],1-row[7+slot*2])
    if mesh.uv_layers:mesh.uv_layers.active_index=0
    for p in mesh.polygons:p.use_smooth=True
    mesh.normals_split_custom_set([cv(v[l.vertex_index,3:6]) for l in mesh.loops])
    mesh.materials.append(material)
    ob=bpy.data.objects.new(key+suffix,mesh);collection.objects.link(ob)
    ob['native_group_key']=key;ob['native_part']=group['part'];ob['material_crc']=group['material']
    return ob


def preview(region):
    out,live,original,_=paths(region);build=out/'modeled'
    assert shutil.disk_usage(out).free>2*1024**3
    info=json.loads((out/'surfaces.json').read_text())
    native=json.loads((build/'native_validation.json').read_text())
    assert sha(Path(native['cmp']).read_bytes())==native['exported_sha256']
    old=np.load(out/'original_geometry.npz');new=np.load(build/'exported_geometry.npz')
    changed={g['group'] for g in json.loads((build/'geometry_validation.json').read_text())['groups']}
    bpy.ops.wm.read_factory_settings(use_empty=True);configure('base_interiors')
    scene=bpy.context.scene
    scene['native_cmp_sha256']=native['exported_sha256']
    scene['source_cmp']=str(live);scene['source_sha256']=native['installed_source_sha256']
    scene['review_status']='Exported native geometry, current regional artwork. Offline inspection lighting.'
    scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
    scene.render.resolution_percentage=100;scene.render.use_persistent_data=True
    scene.view_settings.view_transform='AgX';scene.view_settings.exposure=.5
    scene.world=bpy.data.worlds.new('Inspection ambient');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.compute_device_type='OPTIX';prefs.get_devices()
    for device in prefs.devices:device.use=device.type=='OPTIX'
    if any(d.use for d in prefs.devices):scene.cycles.device='GPU'
    archive=bpy.data.collections.new('ARCHIVE - original walls - disabled')
    relief=bpy.data.collections.new('Wall and door relief - exported CMP')
    unchanged=bpy.data.collections.new('Unchanged structure and mechanisms')
    for collection in (archive,relief,unchanged):scene.collection.children.link(collection)
    materials={}
    for key,source in info['materials'].items():
        mat=bpy.data.materials.new(source['name']);mat.use_nodes=True
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF')
        bs.inputs['Roughness'].default_value=.8
        dt=source['textures'].get('Dt_name')
        if dt:
            tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(out/dt['path']),check_existing=True)
            uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UV0';links.new(uv.outputs[0],tex.inputs['Vector'])
            links.new(tex.outputs['Color'],bs.inputs['Base Color']);links.new(tex.outputs['Color'],bs.inputs['Emission Color'])
            bs.inputs['Emission Strength'].default_value=.25
            if 'Ot' in source['type']:links.new(tex.outputs['Alpha'],bs.inputs['Alpha'])
        if 'Two' not in source['type']:
            geo=nodes.new('ShaderNodeNewGeometry');transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
            links.new(geo.outputs['Backfacing'],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2])
            links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
        materials[key]=mat
    for g in info['groups']:
        make_mesh(g,new[g['key']],materials[g['material']],relief if g['key'] in changed else unchanged,'_relief' if g['key'] in changed else '')
        if g['key'] in changed:make_mesh(g,old[g['key']],materials[g['material']],archive,'_original')
    clay=bpy.data.materials.new('Neutral clay');clay.use_nodes=True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.38,.43,.48,1)
    clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9
    light=bpy.data.lights.new('Inspection softbox','AREA');light.shape='DISK'
    lamp=bpy.data.objects.new(light.name,light);scene.collection.objects.link(lamp)
    cam=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));scene.collection.objects.link(cam);scene.camera=cam
    cam.data.clip_start=.02;cam.data.clip_end=1000

    def toggle(after):
        archive.hide_render=after;archive.hide_viewport=after
        relief.hide_render=not after;relief.hide_viewport=not after

    def point(position,target,scale,fov):
        cam.location=cv(position);q=cv(target)
        cam.rotation_euler=(q-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(fov)
        lamp.location=cam.location+Vector((scale*.6,0,scale*.4))
        lamp.rotation_euler=(q-lamp.location).to_track_quat('-Z','Y').to_euler()
        light.energy=45*scale*scale;light.size=scale*.5

    walls=[
        ('west_wall',(-3,2.4,0),(-12,2.4,0),7,64),
        ('north_wide',(0,2.8,6),(0,2.8,-8.2),12,86),
        ('south_wide',(0,2.8,-6),(0,2.8,8.2),12,86),
        ('west_oblique',(-5,3,3.8),(-11.2,2.5,0),7,72),
    ]
    doors=[]
    for zsign,side in [(-1,'north'),(1,'south')]:
        for xsign,label in [(-1,'left'),(1,'right')]:
            x=xsign*5.43
            doors.append((f'door_{side}_{label}',(x+.2,1.43,zsign*5.7),(x,1.34,zsign*9.796),2.8,46))
    doors.append(('companion',(-2.57,1.35,-6.1),(-2.57,1.28,-9.796),2.4,43))
    if region=='br':
        doors.append(('companion_south',(2.57,1.35,6.1),(2.57,1.28,9.796),2.4,43))
    for name,position,target,scale,fov in walls+doors:
        portrait=name.startswith(('door_','companion'))
        scene.render.resolution_x=840 if portrait else 1120;scene.render.resolution_y=1120 if portrait else 840
        cam.data.sensor_fit='VERTICAL' if portrait else 'AUTO';point(position,target,scale,fov)
        for style in ('textured','clay'):
            scene.view_layers[0].material_override=clay if style=='clay' else None
            for mode in ('before','after'):
                toggle(mode=='after');scene.render.filepath=str(build/f'{name}_{style}_{mode}.png')
                bpy.ops.render.render(write_still=True)
        print('REVIEWED_VIEW',region,name,flush=True)
    scene.view_layers[0].material_override=None;toggle(True)
    scene.render.resolution_x=1120;scene.render.resolution_y=840;cam.data.sensor_fit='AUTO'
    point(*walls[0][1:]);bpy.ops.file.pack_all()
    blend=build/f'{region}_depot_deck_relief.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.wm.open_mainfile(filepath=str(blend));configure('base_interiors')
    archive=bpy.data.collections['ARCHIVE - original walls - disabled']
    relief=bpy.data.collections['Wall and door relief - exported CMP']
    assert archive.hide_render and archive.hide_viewport and not relief.hide_render and not relief.hide_viewport
    visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not any(c.hide_render for c in o.users_collection)]
    assert sum(len(o.data.polygons) for o in visible)==native['result_triangles']
    assert bpy.context.scene['native_cmp_sha256']==native['exported_sha256']
    assert all(im.packed_file for im in bpy.data.images if im.type=='IMAGE' and im.source=='FILE')
    assert sha(live.read_bytes())==native['installed_source_sha256']
    assert sha(original.read_bytes())==native['original_fl_nd_sha256']
    dump(build/'preview_validation.json',dict(cmp_sha256=native['exported_sha256'],blend_sha256=sha(blend.read_bytes()),
        blend=str(blend),reopened=True,originals_hidden_in_viewport_and_render=True,textures_packed=True,
        visible_triangles=native['result_triangles'],views=[s[0] for s in walls],door_views=[s[0] for s in doors],
        sources_unchanged=True,scope='Offline neutral diagnostic lighting with current diffuse artwork; not in-game captures.'))
    print('PREVIEW_COMPLETE',region,flush=True)


if __name__=='__main__':
    regions=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else list(REGIONS)
    for region in regions:
        assert region in REGIONS
        preview(region)
