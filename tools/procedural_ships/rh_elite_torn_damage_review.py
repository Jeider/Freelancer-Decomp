"""Reopenable offline scenes and attachment checks from exported damage assets."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
import numpy as np
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_elite_torn_damage_blender as a
OUT=a.OUT


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def tree(gs):
    p=np.concatenate([np.array(g['corners'])[:,:,:3].reshape(-1,3) for g in gs])
    return BVHTree.FromPolygons([Vector(v) for v in p],list(np.arange(len(p)).reshape(-1,3)),all_triangles=True)


def main():
    data=json.loads((OUT/'review_data.json').read_text());materials_info=json.loads((OUT/'input.json').read_text())['materials']
    assert sha(OUT/'assets/rh_pir_elite.cmp')==data['cmp_sha256']
    assert sha(OUT/'rh_pir_elite_all_damage_open.cmp')==data['review_sha256']
    a.clear();intact=bpy.context.scene;intact.name='01 - Intact extended'
    materials={}
    for key,entry in materials_info.items():
        mat=bpy.data.materials[key];mat.use_nodes=True;mat.use_backface_culling=True
        mat['shared_material']=entry['name'];shader=mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Roughness'].default_value=.76;shader.inputs['Base Color'].default_value=(*entry['colour'][:3],1)
        if entry['image']:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(entry['image'],check_existing=True);tex.image.pack()
            multiply=mat.node_tree.nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
            multiply.inputs[2].default_value=(*entry['colour'][:3],1)
            mat.node_tree.links.new(tex.outputs['Color'],multiply.inputs[1]);mat.node_tree.links.new(multiply.outputs[0],shader.inputs['Base Color'])
        materials[int(key)]=mat
    intact_objects={n:a.mesh_object(dict(groups=gs),n)[0] for n,gs in data['intact'].items()}
    wounds={};stats={}
    for zone,gs in data['damage'].items():
        ob,_=a.mesh_object(dict(groups=gs),'Damage_'+zone)
        stat=a.topology(ob);wounds[zone]=ob
        intact.collection.objects.unlink(ob)
        cap=tree(gs)
        if 'wing' in zone:
            side=zone.split('_')[0];support=data['intact'][f'Rh_{side}_upperarm']+data['intact']['Root']
        else:support=data['intact']['Root']
        pairs=len(cap.overlap(tree(support)));assert pairs>0,(zone,'no surviving support contact')
        stat['support_triangle_pairs']=pairs
        # Rays from the exposed side of the original exported triangles. A face
        # in front of another overlapping solid is permitted; a back-facing hit isn't.
        front=0;back=0;back_samples=[];slivers=0
        for g in gs:
            for tri in g['corners']:
                p=np.array(tri)[:,:3];n=np.cross(p[1]-p[0],p[2]-p[0]);area2=np.linalg.norm(n)
                # Native float32 triangulation can retain sub-micron strips on
                # a collinear ngon edge. BVH normal selection there is ambiguous.
                if area2 < 2e-6:slivers+=1;continue
                n/=area2
                center=p.mean(0);hit,normal,_,dist=cap.ray_cast(Vector(center+n*.002),Vector(-n),.005)
                if hit is not None:
                    if normal.dot(Vector(n))>.5:front+=1
                    else:
                        back+=1;back_samples.append(dict(center=center.tolist(),normal=n.tolist(),hit_normal=list(normal),distance=dist,material=g['material']))
        if back:
            (OUT/'ray_backfaces.json').write_text(json.dumps(dict(zone=zone,samples=back_samples),indent=2))
        assert back==0,(zone,front,back)
        stat.update(front_facing_rays=front,back_facing_rays=back,numerical_slivers_excluded_from_ray_test=slivers);stats[zone]=stat
    def make_scene(name,destroyed):
        scene=bpy.data.scenes.new(name)
        for part,ob in intact_objects.items():
            omit=any(part=={'tail':'Rh_tail_lod1'}.get(z,'Rh_'+z+'_lod1') or ('wing' in z and part=='Rh_'+z+'_mesh') for z in destroyed)
            if not omit:scene.collection.objects.link(ob)
        for zone in destroyed:scene.collection.objects.link(wounds[zone])
        scene['destroyed_zones']=', '.join(destroyed);return scene
    all_damage=make_scene('02 - All five zones destroyed',list(wounds))
    scenes=[intact,all_damage]+[make_scene(f'{i+3:02} - {zone} destroyed',[zone]) for i,zone in enumerate(wounds)]
    hpcol=bpy.data.collections.new('User hardpoints and recalculated Dp');intact.collection.children.link(hpcol)
    for hp in data['hardpoints'].values():
        ob=bpy.data.objects.new(hp['name'],None);hpcol.objects.link(ob)
        ob.location=a.C@Vector(hp['position']);ob.rotation_euler=(a.C@Matrix(hp['orientation'])@a.C.transposed()).to_euler()
        ob.empty_display_type='ARROWS';ob.empty_display_size=.15;ob['native_owner_file']=hp['file']
    hpcol.hide_viewport=True;hpcol.hide_render=True
    target=a.C@Vector((0,0,0));camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'))
    studio=bpy.data.collections.new('Studio');studio.objects.link(camera)
    camera.data.type='ORTHO';camera.data.ortho_scale=22;camera.location=target+(a.C@Vector((-1,.65,1))).normalized()*40
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    for i,(position,energy,size) in enumerate([((-10,13,8),2400,10),((10,7,-9),1600,9),((0,-10,2),1600,7)]):
        lamp=bpy.data.lights.new('Area '+str(i),'AREA');lamp.energy=energy;lamp.shape='DISK';lamp.size=size
        ob=bpy.data.objects.new(lamp.name,lamp);studio.objects.link(ob);ob.location=a.C@Vector(position)
        ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
    for scene in scenes:
        scene.collection.children.link(studio);scene.camera=camera
        scene.world=bpy.data.worlds.new(scene.name+' world');scene.world.color=(.3,.3,.3)
        scene.render.engine='CYCLES';scene.cycles.samples=16
        scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
        scene['CMP_sha256']=data['cmp_sha256'];scene['Stage']='Offline damage review. LOD0; game unchanged.'
    bpy.context.window.scene=all_damage
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active;sp.shading.type='MATERIAL';sp.overlay.show_extras=False;sp.overlay.show_floor=False
                sp.region_3d.view_rotation=camera.rotation_euler.to_quaternion();sp.region_3d.view_location=target
                sp.region_3d.view_distance=24;sp.region_3d.view_perspective='ORTHO'
    blend=OUT/'rh_pir_elite_damage.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert bpy.context.scene.name=='02 - All five zones destroyed'
    for scene in bpy.data.scenes:
        assert scene['CMP_sha256']==data['cmp_sha256']
        assert scene.objects['Root'].data==bpy.data.scenes['01 - Intact extended'].objects['Root'].data
    assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
    report=dict(blend_sha256=sha(blend),cmp_sha256=data['cmp_sha256'],reopened=True,extended_pose=True,
        scenes=[s.name for s in bpy.data.scenes],damage=stats,packed_review_images=True)
    # Objects are invalidated by reopen; query the collection from the new file.
    report['hardpoints']=len(bpy.data.collections['User hardpoints and recalculated Dp'].objects)
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2)+'\n')
    print('REOPENED seven damage review scenes; every wound closed and attached',flush=True)


if __name__=='__main__':main()
