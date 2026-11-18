"""Render and reopen the actual exported depot replacement geometry."""
import sys,json,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from blender_workspace import configure
configure('base_interiors')
sys.path.insert(0,str(Path(__file__).resolve().parent))
from depot_surface_audit import OUT,ORIGINAL,CURRENT
from native_common import sha

BUILD=OUT/'modeled'


def cv(v):return Vector((float(v[0]),-float(v[2]),float(v[1])))


def main():
    validation=json.loads((BUILD/'native_validation.json').read_text())
    assert sha(Path(validation['cmp']).read_bytes())==validation['exported_sha256']
    geometry=np.load(BUILD/'exported_geometry.npz')
    stats=json.loads((BUILD/'geometry_validation.json').read_text())
    changed={g['group'] for g in stats['groups']}
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'depot_original_review.blend'))
    bpy.context.preferences.filepaths.save_version=0
    bpy.context.preferences.filepaths.file_preview_type='NONE'
    scene=bpy.context.scene
    scene['review_status']='Actual modeled relief decoded from exported CMP; not installed.'
    scene['native_cmp_sha256']=validation['exported_sha256']
    original=bpy.data.collections.new('ARCHIVE - original wall surfaces - disabled')
    modeled=bpy.data.collections.new('Modeled wall relief - exported CMP')
    scene.collection.children.link(original);scene.collection.children.link(modeled)
    for key in sorted(changed):
        old=next(o for o in scene.objects if o.type=='MESH' and o.name.startswith(key+'__'))
        t=geometry[key];v=t.reshape(-1,t.shape[-1]);faces=np.arange(len(v)).reshape(-1,3)
        n=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3])
        flip=np.einsum('ij,ij->i',n,t[:,:,3:6].mean(1))<0;faces[flip]=faces[flip][:,[0,2,1]]
        mesh=bpy.data.meshes.new(key+'_modeled');mesh.from_pydata([cv(p) for p in v[:,:3]],[],faces.tolist());mesh.update()
        for slot in range((v.shape[-1]-6)//2):
            uv=mesh.uv_layers.new(name=f'UV{slot}')
            for loop in mesh.loops:
                row=v[loop.vertex_index];uv.data[loop.index].uv=(row[6+2*slot],1-row[7+2*slot])
        if mesh.uv_layers:mesh.uv_layers.active_index=0
        for p in mesh.polygons:p.use_smooth=True
        mesh.normals_split_custom_set([cv(v[l.vertex_index,3:6]) for l in mesh.loops])
        mesh.materials.append(old.data.materials[0])
        ob=bpy.data.objects.new(old.name+'_relief',mesh);modeled.objects.link(ob)
        ob['native_group_key']=key;ob['native_cmp_sha256']=validation['exported_sha256']
        for collection in list(old.users_collection):collection.objects.unlink(old)
        original.objects.link(old)
    def toggle(after):
        original.hide_render=after;original.hide_viewport=after
        modeled.hide_render=not after;modeled.hide_viewport=not after
    cam=scene.camera;lamp=bpy.data.objects['Inspection softbox'];light=lamp.data
    clay=bpy.data.materials.new('Relief inspection clay');clay.use_nodes=True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.38,.43,.48,1)
    clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9
    scene.cycles.samples=20
    try:
        prefs=bpy.context.preferences.addons['cycles'].preferences
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for device in prefs.devices:device.use=device.type=='OPTIX'
        if any(device.use for device in prefs.devices):scene.cycles.device='GPU'
    except Exception:pass
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.45
    def point(position,target,scale,fov):
        cam.location=cv(position);q=cv(target)
        cam.rotation_euler=(q-cam.location).to_track_quat('-Z','Y').to_euler()
        cam.data.angle=math.radians(fov)
        # Identical broad, off-axis lighting before and after.
        lamp.location=cam.location+Vector((scale*.6,0,scale*.4))
        lamp.rotation_euler=(q-lamp.location).to_track_quat('-Z','Y').to_euler()
        light.energy=45*scale*scale;light.size=scale*.5
    shots=[
        ('west_wall',(-3,2.4,0),(-12,2.4,0),7,64),
        ('north_wall',(-3,2.5,0),(-3,2.5,-8.2),8,64),
        ('south_wall',(-3,2.5,0),(-3,2.5,8.2),8,64),
        ('north_wide',(0,2.8,6),(0,2.8,-8.2),12,86),
        ('south_wide',(0,2.8,-6),(0,2.8,8.2),12,86),
        ('west_oblique',(-5,3.0,3.8),(-11.2,2.5,0),7,72),
    ]
    for name,position,target,scale,fov in shots:
        point(position,target,scale,fov)
        for style in ('textured','clay'):
            scene.view_layers[0].material_override=clay if style=='clay' else None
            for mode in ('before','after'):
                toggle(mode=='after');scene.render.filepath=str(BUILD/f'{name}_{style}_{mode}.png')
                bpy.ops.render.render(write_still=True)
        print('REVIEWED_VIEW',name,flush=True)
    scene.view_layers[0].material_override=None;toggle(True)
    door_views=[]
    if (BUILD/'door_detail/before_geometry.npz').exists():
        from depot_door_preview import render_doors
        door_views=render_doors(BUILD,scene,modeled,point,clay)
    point((-3,2.4,0),(-12,2.4,0),7,64)
    bpy.ops.wm.save_as_mainfile(filepath=str(BUILD/'rh_depot_deck_relief.blend'))
    bpy.ops.wm.open_mainfile(filepath=str(BUILD/'rh_depot_deck_relief.blend'))
    archive=bpy.data.collections['ARCHIVE - original wall surfaces - disabled']
    active=bpy.data.collections['Modeled wall relief - exported CMP']
    assert archive.hide_render and archive.hide_viewport and not active.hide_render and not active.hide_viewport
    if door_views:
        previous=bpy.data.collections['ARCHIVE - before detailed doors - disabled']
        assert previous.hide_render and previous.hide_viewport
    visible=[o for o in bpy.context.scene.objects if o.type=='MESH' and not any(c.hide_render for c in o.users_collection)]
    assert sum(len(o.data.polygons) for o in visible)==validation['result_triangles']
    assert bpy.context.scene['native_cmp_sha256']==validation['exported_sha256']
    assert sha(ORIGINAL.read_bytes())==validation['original_fl_nd_sha256']
    assert sha(CURRENT.read_bytes())==validation['installed_source_sha256']
    report=dict(cmp_sha256=validation['exported_sha256'],blend_sha256=sha((BUILD/'rh_depot_deck_relief.blend').read_bytes()),
        reopened=True,originals_hidden_in_viewport_and_render=True,visible_triangles=validation['result_triangles'],
        views=[s[0] for s in shots],door_views=door_views,sources_unchanged=True,
        scope='Offline matched lighting; exported CMP geometry with current artwork. Original FL_ND geometry is before. Not an in-game lighting comparison.')
    (BUILD/'preview_validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print('PREVIEW_COMPLETE',flush=True)


if __name__=='__main__':main()
