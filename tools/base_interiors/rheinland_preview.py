"""Blender previews decoded from staged CMP, with identical before/after lighting."""
import sys,math,os,shutil
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rheinland_audit import *
from blender_workspace import configure as configure_blender_workspace
configure_blender_workspace('base_interiors')

def cv(v):return (v[0],-v[2],v[1])
def vec(d):return np.array([d[str(i)] for i in (1,2,3)])
def preview(model):
    if shutil.disk_usage(ROOT).free < 2*1024**3:
        raise RuntimeError('Less than 2 GiB free: refusing another interior render batch')
    dest=BATCH/model;data=json.loads((dest/'source_scene.json').read_text());validation=json.loads((dest/'validation.json').read_text())
    root=read_tree(Path(data['source']).read_bytes())[1][0];newroot=read_tree((BATCH/'stage'/validation['relative']).read_bytes())[1][0]
    native,kinds=transforms(root);newnative,_=transforms(newroot)
    bpy.ops.wm.read_factory_settings(use_empty=True);scene_=bpy.context.scene
    bpy.context.preferences.filepaths.save_version=0
    bpy.context.preferences.filepaths.file_preview_type='NONE'
    scene_['native_cmp_sha256']=validation['prepared_sha256']
    scene_.render.engine='CYCLES';scene_.cycles.samples=24;scene_.cycles.use_denoising=True
    scene_.render.resolution_x=1280;scene_.render.resolution_y=960;scene_.render.resolution_percentage=100
    scene_.world=bpy.data.worlds.new('Inspection ambient');scene_.world.use_nodes=True;scene_.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.16,.19,.23,1);scene_.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
    scene_.view_settings.view_transform='AgX';scene_.render.use_persistent_data=True
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene_.cycles.device='GPU'
    except Exception:pass
    mats={}
    for key,m in data['materials'].items():
        mat=bpy.data.materials.new(m['name']);mat.use_nodes=True;n=mat.node_tree.nodes;links=mat.node_tree.links;bs=n.get('Principled BSDF');bs.inputs['Roughness'].default_value=.65
        dt=m['textures'].get('Dt_name')
        if dt:
            tex=n.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(dt['path'],check_existing=True)
            uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';links.new(uv.outputs[0],tex.inputs['Vector'])
            links.new(tex.outputs['Color'],bs.inputs['Base Color']);links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.4
        et=m['textures'].get('Et_name')
        if et:
            etex=n.new('ShaderNodeTexImage');etex.image=bpy.data.images.load(et['path'],check_existing=True);uv=n.new('ShaderNodeUVMap');uv.uv_map='UV0';links.new(uv.outputs[0],etex.inputs['Vector']);links.new(etex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.65
        if dt and any(flag in m.get('Type','') for flag in ('Oc','Ot')):
            # Oc may be omitted (native default 1); Ot still selects texture
            # opacity. This matters for the deck's original fan light rays.
            alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';alpha.inputs[1].default_value=float(m.get('Oc',[1.])[0]);links.new(tex.outputs['Alpha'],alpha.inputs[0]);links.new(alpha.outputs[0],bs.inputs['Alpha'])
        if 'Two' not in m.get('Type',''):
            geom=n.new('ShaderNodeNewGeometry');transparent=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');links.new(geom.outputs['Backfacing'],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
        mats[key]=mat
    before_col=bpy.data.collections.new('ARCHIVE - original surfaces - disabled');scene_.collection.children.link(before_col)
    after_col=bpy.data.collections.new('Reviewed replacement geometry');scene_.collection.children.link(after_col)
    originals=[];replacements=[];shared=[];groups_before={};groups_after={}
    changed={(r['part'],r['group']) for r in validation['changed_groups'] if r['source_triangles_with_relief']}
    uses=data['uses'];entities=[]
    for script in uses[0]['scripts']:entities.extend((scene(script).get('entities') or {}).values())
    room=next((e for e in entities if e.get('template_name','').lower().startswith('rh_0') and 'camera' not in e.get('entity_name','').lower()),None)
    offset=vec(room['spatialprops']['pos']) if room else np.zeros(3)
    def mesh_obj(part,gi,g,collection):
        corners=g['corners'];r,p=(newnative if collection==after_col else native)[part]
        v=corners.reshape(-1,corners.shape[-1]).copy();v[:,:3]=v[:,:3]@r+p+offset;v[:,3:6]=v[:,3:6]@r
        faces=np.arange(len(v)).reshape(-1,3);cross=np.cross(v[faces[:,1],:3]-v[faces[:,0],:3],v[faces[:,2],:3]-v[faces[:,0],:3]);flip=np.einsum('ij,ij->i',cross,v[faces,3:6].mean(1))<0;faces[flip]=faces[flip][:,[0,2,1]]
        me=bpy.data.meshes.new(part);me.from_pydata([cv(vv) for vv in v[:,:3]],[],faces.tolist());me.update()
        for slot in range((v.shape[-1]-6)//2):
            layer=me.uv_layers.new(name=f'UV{slot}')
            for loop in me.loops:layer.data[loop.index].uv=(v[loop.vertex_index,6+2*slot],1-v[loop.vertex_index,7+2*slot])
        if me.uv_layers:me.uv_layers.active_index=0
        for poly in me.polygons:poly.use_smooth=True
        me.normals_split_custom_set([cv(v[l.vertex_index,3:6]) for l in me.loops]);me.materials.append(mats[str(g['material'])])
        ob=bpy.data.objects.new(part+'_'+str(gi),me);collection.objects.link(ob);ob['native_part']=part;ob['material_crc']=str(g['material']);return ob
    for part in get_parts(root):
        for gi,g in enumerate(part['groups']):
            is_changed=(part['name'],gi) in changed
            ob=mesh_obj(part['name'],gi,g,before_col if is_changed else scene_.collection)
            if is_changed:originals.append(ob);groups_before[part['name'],gi]=ob
            else:shared.append(ob)
    # Current batch stays under a single block for each original part.
    assert not validation['new_static_parts'],'Preview needs new-part correspondence'
    for part in get_parts(newroot):
        for gi,g in enumerate(part['groups']):
            if (part['name'],gi) not in changed:continue
            ob=mesh_obj(part['name'],gi,g,after_col);replacements.append(ob);groups_after[part['name'],gi]=ob
    for e in entities:
        if 'lightprops' not in e:continue
        props=e['lightprops'];sp=e.get('spatialprops',{});kind='SUN' if props.get('type')==3 else 'POINT'
        ld=bpy.data.lights.new(e['entity_name'],kind);ld.color=vec(props.get('diffuse',{'1':1,'2':1,'3':1}));ld.energy=.6 if kind=='SUN' else (130 if '_bar' in model else 900)
        if kind=='POINT':ld.shadow_soft_size=.3
        ob=bpy.data.objects.new(ld.name,ld);scene_.collection.objects.link(ob);ob.location=cv(vec(sp.get('pos',{'1':0,'2':0,'3':0})))
        if kind=='SUN':ob.rotation_euler=Vector(cv(vec(props['direction']))).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add();cam=bpy.context.object;scene_.camera=cam
    entry=next(e for e in entities if e.get('entity_name','').lower()=='camera_0');sp=entry['spatialprops'];rot=np.array([vec(sp['orient'][str(i)]) for i in (1,2,3)])
    cam.location=cv(vec(sp['pos']));cam.rotation_euler=Matrix([cv(row) for row in rot]).transposed().to_euler();cam.data.angle=math.radians(entry['cameraprops']['fovh']);cam.data.clip_start=.02;cam.data.clip_end=10000
    def toggle(after):
        before_col.hide_render=after;before_col.hide_viewport=after;after_col.hide_render=not after;after_col.hide_viewport=not after
    def shot(name):scene_.render.filepath=str(dest/(name+'.png'));bpy.ops.render.render(write_still=True)
    for mode in ['before','after']:toggle(mode=='after');shot(mode+'_room')
    toggle(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(dest/'rheinland_relief.blend'))
    # A paired close-up of the same actual wall, retaining its whole plane.
    options=[]
    for record in validation['changed_groups']:
        for q in record['inspection_candidates']:options.append((q['size'],record,q))
    _,record,q=max(options,key=lambda x:x[0]);r,p=native[record['part']]
    center=np.array(q['center'])@r+p+offset;normal=np.array(q['normal'])@r;tangent=np.array(q['tangent'])@r;tangent/=np.linalg.norm(tangent);size=q['size']
    cam.location=cv(center+normal*size*1.65+tangent*size*.65);cam.rotation_euler=(Vector(cv(center))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(62)
    for ob in shared:ob.hide_render=True
    for objects in (groups_before,groups_after):
        for key,ob in objects.items():ob.hide_render=key!=(record['part'],record['group'])
    # Slice only the inspection copy to the selected planar placement. The saved
    # full room and staged CMP retain every surface and object.
    import bmesh
    for ob in [groups_before[record['part'],record['group']],groups_after[record['part'],record['group']]]:
        bm=bmesh.new();bm.from_mesh(ob.data)
        remove=[]
        for f in bm.faces:
            v=f.calc_center_median();world=np.array([v.x,v.z,-v.y]);dist=world-center
            if abs(dist@normal)>max(abs(q['depth'])*1.4,size*.015) or np.linalg.norm(dist)>size*2.2:remove.append(f)
        bmesh.ops.delete(bm,geom=remove,context='FACES');bm.to_mesh(ob.data);bm.free();ob.data.update()
    ld=bpy.data.lights.new('Inspection softbox','AREA');ld.energy=180*size*size;ld.shape='DISK';ld.size=size*1.6
    ob=bpy.data.objects.new(ld.name,ld);scene_.collection.objects.link(ob);ob.location=cv(center+normal*size+tangent*size*.6+np.array([0,size*.7,0]));ob.rotation_euler=(Vector(cv(center))-ob.location).to_track_quat('-Z','Y').to_euler()
    clay=bpy.data.materials.new('Neutral geometric inspection');clay.use_nodes=True;clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.25,.3,.34,1);clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.65
    for style in ['textured','clay']:
        scene_.view_layers[0].material_override=clay if style=='clay' else None
        for mode in ['before','after']:toggle(mode=='after');shot(mode+'_'+style)
    dump(dest/'preview.json',dict(prepared_sha256=validation['prepared_sha256'],native_cmp_decoded=True,scope='Offline Blender material/lighting approximation; matched before/after. Close-up isolates one wall plane only.',
        inspected_feature=q['label'],material=record['material'],part=record['part'],saved_full_scene=True,game_launched=False))
    print('Preview complete:',model,flush=True)

if __name__=='__main__':
    models=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else MODELS
    for model in models:preview(model)
