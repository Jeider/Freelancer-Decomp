"""Two-state editable Blender companion for the offline tail/rim prototype."""
import hashlib
import json
import sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_concept_b_final_blender as helper
C=helper.C
OUT=HERE.parents[1]/'out/ship_design/rh_elite/rh_pir_elite/tail_rim'
BLEND=OUT/'rh_pir_elite_tail_rim.blend'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    data=json.loads((OUT/'review_data.json').read_text())
    material_info=json.loads((OUT/'materials.json').read_text())
    assert sha(OUT/'rh_pir_elite_tail_rim.cmp')==data['cmp_sha256']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.file_preview_type='NONE'
    bpy.context.preferences.filepaths.save_version=0
    scene=bpy.context.scene;scene.name='01 - Intact / extended'
    scene['CMP_sha256']=data['cmp_sha256'];scene['Stage']='Visual prototype, LOD0. Game files unchanged.'
    materials={}
    for key,entry in material_info.items():
        mat=bpy.data.materials.new(entry['name']);mat.use_nodes=True;mat.use_backface_culling=True
        mat.diffuse_color=(*entry['colour'][:3],1)
        shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.72
        shader.inputs['Base Color'].default_value=(*entry['colour'][:3],1)
        if entry['image']:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(entry['image'],check_existing=True);tex.image.pack()
            tex.interpolation='Linear'
            multiply=mat.node_tree.nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
            multiply.inputs[2].default_value=(*entry['colour'][:3],1)
            mat.node_tree.links.new(tex.outputs['Color'],multiply.inputs[1]);mat.node_tree.links.new(multiply.outputs[0],shader.inputs['Base Color'])
        materials[int(key)]=mat
    main=bpy.data.collections.new('Intact model');scene.collection.children.link(main)
    def mesh(name,gs,col):
        ob,slots=helper.mesh_object(dict(groups=gs),name)
        for previous in list(ob.users_collection):previous.objects.unlink(ob)
        col.objects.link(ob)
        for i,mid in enumerate(slots):ob.data.materials[i]=materials[mid]
        ob['native_component']=name;return ob
    objects={name:mesh(name,gs,main) for name,gs in data['parts'].items()}
    hpcol=bpy.data.collections.new('Hardpoints - user positions');scene.collection.children.link(hpcol)
    for hp in data['hardpoints'].values():
        ob=bpy.data.objects.new(hp['name'],None);hpcol.objects.link(ob)
        ob.location=C@Vector(hp['position']);ob.rotation_euler=(C@Matrix(hp['orientation'])@C.transposed()).to_euler()
        ob.empty_display_type='ARROWS';ob.empty_display_size=.16;ob['native_name']=hp['name'];ob['native_file']=hp['file']
    hpcol.hide_viewport=True;hpcol.hide_render=True
    broken=bpy.data.scenes.new('02 - Tail destroyed / live rim');broken['CMP_sha256']=data['cmp_sha256']
    broken['Stage']='Only outer tail shell damaged. Drum and complete narrow carrier remain on Root.'
    intact_survivors=bpy.data.collections.new('Surviving original components');broken.collection.children.link(intact_survivors)
    for name,ob in objects.items():
        if name!='Rh_tail_lod1':intact_survivors.objects.link(ob)
    damagecol=bpy.data.collections.new('Surviving tail damage');broken.collection.children.link(damagecol)
    damaged=mesh('Damage_tail',data['damage'],damagecol);damaged['receiving_hp']='DpTail'
    studio=bpy.data.collections.new('Studio');scene.collection.children.link(studio);broken.collection.children.link(studio)
    camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Review camera'));studio.objects.link(camera)
    target=C@Vector((0,1,0));camera.data.type='ORTHO';camera.data.ortho_scale=22
    camera.location=target+(C@Vector((-1,.55,1))).normalized()*40
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    for index,(position,energy,size) in enumerate([((-10,13,8),2200,10),((10,7,-9),1500,9),((0,12,-2),1200,7)]):
        lamp=bpy.data.lights.new('Area '+str(index),'AREA');lamp.energy=energy;lamp.shape='DISK';lamp.size=size
        ob=bpy.data.objects.new(lamp.name,lamp);studio.objects.link(ob);ob.location=C@Vector(position)
        ob.rotation_euler=(target-ob.location).to_track_quat('-Z','Y').to_euler()
    for s in (scene,broken):
        s.camera=camera;s.world=bpy.data.worlds.new(s.name+' world');s.world.color=(.3,.3,.3)
        s.render.engine='CYCLES';s.cycles.samples=16;s.render.resolution_x=1400;s.render.resolution_y=1000;s.render.resolution_percentage=100
    bpy.context.window.scene=scene
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_extras=False;space.overlay.show_floor=False
                space.region_3d.view_rotation=camera.rotation_euler.to_quaternion();space.region_3d.view_location=target
                space.region_3d.view_distance=24;space.region_3d.view_perspective='ORTHO'
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    assert bpy.context.scene.name=='01 - Intact / extended'
    a=bpy.data.scenes['01 - Intact / extended'];d=bpy.data.scenes['02 - Tail destroyed / live rim']
    assert 'Rh_tail_lod1' in a.objects and 'Rh_tail_lod1' not in d.objects
    assert 'Damage_tail' in d.objects and 'Damage_tail' not in a.objects
    assert a.objects['Root'].data==d.objects['Root'].data
    assert len(bpy.data.collections['Hardpoints - user positions'].objects)==79
    assert all(image.packed_file for image in bpy.data.images if image.source=='FILE')
    report=dict(blend_sha256=sha(BLEND),cmp_sha256=data['cmp_sha256'],reopened=True,
        scenes=[a.name,d.name],shared_surviving_root=True,hardpoints=79,extended_pose=True,
        textures_packed_for_offline_review=True,game_libraries_embedded=False)
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('BLENDER READY: intact and damaged scenes; reopened and checked',flush=True)


if __name__=='__main__':main()
