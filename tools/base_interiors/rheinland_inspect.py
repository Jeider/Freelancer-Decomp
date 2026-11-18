"""Reopen saved native previews; inspect every altered material with raking light."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rheinland_preview import *

def inspect(model):
    dest=BATCH/model;validation=json.loads((dest/'validation.json').read_text())
    source=json.loads((dest/'source_scene.json').read_text());root=read_tree(Path(source['source']).read_bytes())[1][0]
    trans,_=transforms(root);out=dest/'inspection';out.mkdir(exist_ok=True)
    bpy.ops.wm.open_mainfile(filepath=str(dest/'rheinland_relief.blend'))
    assert bpy.context.scene['native_cmp_sha256']==validation['prepared_sha256']
    before=bpy.data.collections['ARCHIVE - original surfaces - disabled'];after=bpy.data.collections['Reviewed replacement geometry']
    assert before.hide_render and before.hide_viewport and not after.hide_render and not after.hide_viewport
    checked=dict(prepared_sha256=validation['prepared_sha256'],saved_originals_hidden_in_viewport_and_render=True,source_model_unmodified=sha(Path(source['source']).read_bytes())==source['sha256'])
    before.hide_viewport=False;after.hide_viewport=False
    scene_=bpy.context.scene;scene_.cycles.samples=20;scene_.render.resolution_x=960;scene_.render.resolution_y=720
    cam=scene_.camera
    for ob in scene_.objects:
        if ob.type in ('MESH','LIGHT'):ob.hide_render=True
    scene_.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.35
    # The full-room blend retains the original approximate preview illumination.
    # Only these diagnostic copies use a single low-angle inspection light.
    ld=bpy.data.lights.new('Raking inspection light','AREA');ld.shape='DISK'
    lamp=bpy.data.objects.new(ld.name,ld);scene_.collection.objects.link(lamp)
    clay=bpy.data.materials.new('Relief clay');clay.use_nodes=True
    bs=clay.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.22,.26,.29,1);bs.inputs['Roughness'].default_value=.85
    records=[];seen=set()
    for rec in validation['changed_groups']:
        if not rec['inspection_candidates'] or rec['material'] in seen:continue
        seen.add(rec['material']);q=rec['inspection_candidates'][0];r,p=trans[rec['part']]
        a=next(o for o in before.objects if o.name==rec['part']+'_'+str(rec['group']))
        b=next(o for o in after.objects if o.name.startswith(a.name+'.'))
        center=np.array(q['center'])@r+p;normal=np.array(q['normal'])@r
        # Offset between imported model and native transform (Bremen's THN).
        native_group=next(pp for pp in get_parts(root) if pp['name']==rec['part'])['groups'][rec['group']]
        vv=a.data.vertices[0].co;actual=np.array([vv.x,vv.z,-vv.y]);center+=actual-(native_group['corners'][0,0,:3]@r+p)
        tangent=np.array(q['tangent'])@r;tangent-=normal*np.dot(tangent,normal);tangent/=np.linalg.norm(tangent)
        up=np.cross(normal,tangent);size=q['size']
        # Show neighbouring repeats as well as the seed; never crop away an
        # inconvenient neighbouring material placement to imply full coverage.
        target=Vector(cv(center));clear=False
        for distance in (2.5,1.6,1.,.65,.35):
            cam.location=cv(center+normal*size*distance+tangent*size*min(.7,distance*.28))
            ray=target-cam.location
            hit,point,_,_=a.ray_cast(cam.location,ray.normalized(),distance=ray.length+size*.01)
            if hit and (point-target).length<max(.002,size*.002):
                clear=True;break
        assert clear,(model,rec['material'],'Selected inspection feature is occluded')
        cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(62)
        lamp.location=cv(center+normal*size*.9+tangent*size*1.7+up*size*.8);lamp.rotation_euler=(Vector(cv(center))-lamp.location).to_track_quat('-Z','Y').to_euler()
        ld.energy=25*size*size;ld.size=size*.45
        a.hide_render=False;b.hide_render=False
        i=len(records);stem=f'{i:02d}'
        # Keep the complete selected material group. Other groups are hidden
        # only in this diagnostic view; the saved full scene keeps all of them.
        for mode in ('before','after','clay'):
            before.hide_render=mode!='before';after.hide_render=mode=='before'
            scene_.view_layers[0].material_override=clay if mode=='clay' else None
            scene_.render.filepath=str(out/(stem+'_'+mode+'.png'));bpy.ops.render.render(write_still=True)
        a.hide_render=True;b.hide_render=True
        records.append(dict(material=rec['material'],feature=q['label'],part=rec['part'],stem=stem,unoccluded_feature_ray=True))
    checked.update(materials=records,whole_material_groups_retained=True)
    dump(dest/'inspection.json',checked);print('Inspected:',model,len(records),flush=True)

if __name__=='__main__':
    for model in (sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else MODELS):inspect(model)
