"""Close-up door comparisons against the preceding modeled wall prototype."""
import bpy,numpy as np
from mathutils import Vector


def cv(v):return Vector((float(v[0]),-float(v[2]),float(v[1])))


def render_doors(build,scene,modeled,point,clay):
    source=np.load(build/'door_detail/before_geometry.npz')
    archive=bpy.data.collections.new('ARCHIVE - before detailed doors - disabled')
    scene.collection.children.link(archive)
    active=[]
    for key in source.files:
        current=next(o for o in modeled.objects if o.get('native_group_key')==key)
        active.append(current)
        t=source[key];v=t.reshape(-1,t.shape[-1]);faces=np.arange(len(v)).reshape(-1,3)
        n=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3])
        flip=np.einsum('ij,ij->i',n,t[:,:,3:6].mean(1))<0;faces[flip]=faces[flip][:,[0,2,1]]
        mesh=bpy.data.meshes.new(key+'_before_door_detail');mesh.from_pydata([cv(p) for p in v[:,:3]],[],faces.tolist());mesh.update()
        for slot in range((v.shape[-1]-6)//2):
            layer=mesh.uv_layers.new(name=f'UV{slot}')
            for loop in mesh.loops:
                row=v[loop.vertex_index];layer.data[loop.index].uv=(row[6+2*slot],1-row[7+2*slot])
        if mesh.uv_layers:mesh.uv_layers.active_index=0
        for p in mesh.polygons:p.use_smooth=True
        mesh.normals_split_custom_set([cv(v[l.vertex_index,3:6]) for l in mesh.loops])
        mesh.materials.append(current.data.materials[0])
        ob=bpy.data.objects.new(key+'_before_door_detail',mesh);archive.objects.link(ob)
    archive.hide_render=True;archive.hide_viewport=True
    old_size=(scene.render.resolution_x,scene.render.resolution_y)
    scene.render.resolution_x=840;scene.render.resolution_y=1120
    camera=scene.camera;old_fit=camera.data.sensor_fit;camera.data.sensor_fit='VERTICAL'
    shots=[]
    for side,z in [('north',-1),('south',1)]:
        for label,x in [('left',-5.43),('right',5.43)]:
            shots.append((f'door_{side}_{label}',(x+.20,1.43,z*5.7),(x,1.34,z*9.796),2.8,46,'entry'))
    shots.extend([
        ('door_oblique',(-4.85,1.6,-6.8),(-5.43,1.34,-9.796),2.5,48,'entry'),
        ('door_companion',(-2.57,1.35,-6.1),(-2.57,1.28,-9.796),2.4,43,'companion'),
    ])
    records=[]
    for name,position,target,scale,fov,kind in shots:
        point(position,target,scale,fov)
        for style in ('textured','clay'):
            scene.view_layers[0].material_override=clay if style=='clay' else None
            for mode in ('before','after'):
                before=mode=='before'
                archive.hide_render=not before
                for ob in active:ob.hide_render=before
                scene.render.filepath=str(build/'door_detail'/f'{name}_{style}_{mode}.png')
                bpy.ops.render.render(write_still=True)
        records.append(dict(name=name,kind=kind,position=position,target=target,
            comparison='Previous modeled walls versus additional detailed doors',all_other_geometry_preserved=True))
        print('DOOR_VIEW',name,flush=True)
    for ob in active:ob.hide_render=False
    archive.hide_render=True;archive.hide_viewport=True
    scene.view_layers[0].material_override=None
    scene.render.resolution_x,scene.render.resolution_y=old_size
    camera.data.sensor_fit=old_fit
    return records
