"""Reopen the rigged CMP export; organize LODs/HPs/damage and render real states."""
import json
import hashlib
import sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as h
OUT,C=h.OUT,h.C


def main():
    data=json.loads((OUT/'review_data.json').read_text());rig=json.loads((OUT/'blender_scene.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'rh_concept_b_rigged.blend'))
    scene=bpy.context.scene
    assert scene['CMP_sha256']==data['cmp_sha256']
    objects={e['name']:bpy.data.objects[e['name']] for e in rig['objects']}
    def coll(name):
        old=bpy.data.collections.get(name)
        if old:return old
        c=bpy.data.collections.new(name);scene.collection.children.link(c);return c
    def move(obj,col):
        for c in list(obj.users_collection):c.objects.unlink(obj)
        col.objects.link(obj)
    near=coll('LOD0 - near model')
    for o in objects.values():move(o,near)
    levelcols=[near];levelobjects=[objects]
    for level,entries in enumerate(data['lods'],1):
        col=coll(f'LOD{level} - distance model');obs={}
        for e in entries:
            o,slots=h.mesh_object(e,e['name']+f'_LOD{level}');move(o,col);obs[e['name']]=o
            for i,key in enumerate(slots):
                info=data['materials'][str(key)]
                mat=bpy.data.materials.get(info['name'])
                if mat is None:
                    mat=bpy.data.materials.new(info['name']);mat.use_nodes=True
                    bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.62
                    bsdf.inputs['Metallic'].default_value=.22
                    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/info['texture']));tex.image.pack()
                    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color']);mat.diffuse_color=(.5,.4,.3,1)
                o.data.materials[i]=mat
        for e in rig['objects']:
            o=obs[e['name']];source=objects[e['name']]
            if source.parent:o.parent=obs[source.parent.name]
            o.location=source.location.copy();o.rotation_mode='QUATERNION';o.rotation_quaternion=source.rotation_quaternion.copy()
            if source.animation_data:o.animation_data_create();o.animation_data.action=source.animation_data.action
            o['CMP_component']=e['file'];o['LOD']=level
        col.hide_render=True;col.hide_viewport=True;levelcols.append(col);levelobjects.append(obs)
    hpcol=coll('Hardpoints - native local transforms');hpcol.hide_render=True
    for item in data['hardpoints']:
        o=bpy.data.objects.new(item['name']+' @ '+item['owner'],None);hpcol.objects.link(o)
        o.parent=objects[item['owner']];o.location=C@Vector(item['position'])
        o.rotation_euler=(C@Matrix(item['orientation'])@C.transposed()).to_euler()
        o.empty_display_type='ARROWS';o.empty_display_size=.20;o.show_name=True
        o['native_name']=item['name'];o['native_kind']=item['kind']
    hpcol.hide_viewport=True
    damagecol=coll('Damage caps - enable with detached part hidden');damages={}
    debriscol=coll('Debris caps - attached to detached components');debriscol.hide_render=True;debriscol.hide_viewport=True
    for d in data['damages']:
        o,slots=h.mesh_object(dict(groups=d['world_groups']),'Damage_'+d['zone']);move(o,damagecol)
        for i,key in enumerate(slots):
            info=data['materials'][str(key)];mat=bpy.data.materials.get(info['name'])
            if mat is None:
                mat=bpy.data.materials.new(info['name']);mat.use_nodes=True
                bsdf=mat.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.85
                bsdf.inputs['Base Color'].default_value=(*info['colour'],1)
                if info['texture']:
                    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/info['texture']));tex.image.pack()
                    mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
            o.data.materials[i]=mat
        damages[d['zone']]=o;o['removed_component']=d['part'];o.hide_render=True
        debris,slots=h.mesh_object(dict(groups=d['debris_groups']),'Debris_'+d['zone']);move(debris,debriscol)
        for i,key in enumerate(slots):debris.data.materials[i]=bpy.data.materials[data['materials'][str(key)]['name']]
        debris.parent=objects[d['part']]
        attach=next(hp for hp in data['hardpoints'] if hp['owner']==d['part'] and hp['name']=='DpBreak')
        debris.location=C@Vector(attach['position'])
    damagecol.hide_render=True;damagecol.hide_viewport=True
    scene.frame_set(1);bpy.context.view_layer.update()
    # Distance of physical mounts from their owning mesh, with genuine local coords.
    trees={name:BVHTree.FromPolygons([v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],all_triangles=True) for name,o in objects.items()}
    mountcheck=[]
    physical=('hpweapon','hptorpedo','hpmiscgun','hpthruster','hpturret','hpengine','hpcm','hpmine','hprunninglight','hpcontrail','hpdocklight')
    for item in data['hardpoints']:
        if not item['name'].lower().startswith(physical):continue
        point=C@Vector(item['position']);nearest,_,_,distance=trees[item['owner']].find_nearest(point)
        mountcheck.append(dict(name=item['name'],owner=item['owner'],distance=float(distance)))
    (OUT/'mount_distances.json').write_text(json.dumps(mountcheck,indent=2))
    scene['Asset_stage']='Final offline assembly: three LODs, forward fold, independent cargo doors, damage and hardpoints'
    scene['CMP_sha256']=data['cmp_sha256'];scene['LOD_triangle_counts']=[sum(len(o.data.polygons) for o in obs.values()) for obs in levelobjects]
    for name,frame in (('Open',1),('Folding',25),('Folded',73),('Unfolding',97),('Bay opening',169),('Bay open',201),('Bay closing',225)):
        scene.timeline_markers.new(name,frame=frame)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rh_concept_b_rigged.blend'))
    scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.cycles.samples=16
    camera=scene.camera;camera.data.ortho_scale=23
    shift=Vector(json.loads((OUT/'assembly.json').read_text()).get('center_shift_native',[0,0,0]))
    def render(name,direction=(1,.70,-1.15),frame=1,scale=23,target=(0,1.8,3.5)):
        scene.frame_set(frame);camera.data.ortho_scale=scale
        dest=C@(Vector(target)+shift);camera.location=dest+(C@Vector(direction)).normalized()*40
        camera.rotation_euler=(dest-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    render('finished_open');render('finished_side',(1,0,0));render('finished_folded',frame=84)
    render('finished_tail',(1,.5,1.3),scale=8.0,target=(0,2.4,11.5))
    for lv in range(3):
        for i,col in enumerate(levelcols):col.hide_render=i!=lv;col.hide_viewport=i!=lv
        render(f'lod{lv}')
    for i,col in enumerate(levelcols):col.hide_render=i!=0;col.hide_viewport=i!=0
    light=bpy.data.lights.new('Cargo inspection','AREA');light.energy=180;light.size=2
    lamp=bpy.data.objects.new('Cargo inspection',light);scene.collection.objects.link(lamp)
    lamp.location=C@(Vector((0,6,3.6))+shift);lamp.rotation_euler=((C@(Vector((0,0,3.6))+shift))-lamp.location).to_track_quat('-Z','Y').to_euler()
    render('cargo_open',(.2,2,-.5),frame=210,scale=9,target=(0,1.6,3.6));lamp.hide_render=True
    damagecol.hide_render=False;damagecol.hide_viewport=False
    for d in data['damages']:
        obj=objects[d['part']];obj.hide_render=True;damages[d['zone']].hide_render=False
        render('damage_'+d['zone'],(1,.70,1.15) if 'tail' in d['zone'] else (1,-.30,1) if 'engine' in d['zone'] else (1,.70,-1.15))
        if d['zone']=='tail':render('damage_tail_close',(.7,.9,1.3),scale=6.5,target=(0,2.3,11.4))
        obj.hide_render=False;damages[d['zone']].hide_render=True
    for d in data['damages']:objects[d['part']].hide_render=True;damages[d['zone']].hide_render=False
    render('damage_all',(1,.60,1.15))
    for d in data['damages']:objects[d['part']].hide_render=False;damages[d['zone']].hide_render=True
    damagecol.hide_render=True;damagecol.hide_viewport=True
    scene.frame_set(1);camera.data.ortho_scale=23
    dest=C@(Vector((0,1.5,3.8))+shift)
    camera.location=dest+(C@Vector((1,.65,1.15))).normalized()*40
    camera.rotation_euler=(dest-camera.location).to_track_quat('-Z','Y').to_euler()
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_extras=False
                space.region_3d.view_location=dest;space.region_3d.view_distance=25
                space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rh_concept_b_rigged.blend'))
    print('READY REVIEW',scene['LOD_triangle_counts'],flush=True)


if __name__=='__main__':main()
