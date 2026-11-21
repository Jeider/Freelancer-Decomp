"""Saved/reopened production Blender, textured LOD and torn-assembly review."""
import sys,json,hashlib,math
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import bpy,numpy as np
from mathutils import Matrix,Vector
import rh_fighter_final_blender as helper
from rh_concept_b_final_blender import mesh_object,C
OUT=helper.OUT;DATA=json.loads((OUT/'review.json').read_text(encoding='utf8'))
helper.DATA=DATA

def matrix(rt):
    r,t=rt;result=(C@Matrix(r)@C.transposed()).to_4x4();result.translation=C@Vector(t);return result

def setup(scene):
    scene.render.engine='CYCLES';scene.cycles.samples=12;scene.cycles.use_denoising=True
    scene.render.resolution_x=1100;scene.render.resolution_y=850;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False;scene.view_settings.view_transform='Standard';scene.view_settings.look='None'
    scene.world=bpy.data.worlds.new(scene.name+' world');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.24,.27,.30,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.6
    for i,(loc,power,size) in enumerate([((2,12,-5),1700,9),((-9,3,1),1100,8),((0,7,9),1400,7)]):
        light=bpy.data.lights.new(scene.name+' softbox '+str(i),'AREA');light.energy=power;light.shape='DISK';light.size=size
        ob=bpy.data.objects.new(light.name,light);scene.collection.objects.link(ob);ob.location=C@Vector(loc);ob.rotation_euler=(-ob.location).to_track_quat('-Z','Y').to_euler()
    camera=bpy.data.objects.new(scene.name+' camera',bpy.data.cameras.new(scene.name+' lens'));scene.collection.objects.link(camera);scene.camera=camera;camera.data.type='ORTHO';camera.data.ortho_scale=14.3;camera.data.clip_end=250
    return camera

def render(scene,name,direction,scale=14.3,center=(0,-.3,-1.5)):
    center=np.array(center)-DATA.get('origin_offset',[0,0,0])
    bpy.context.window.scene=scene;camera=scene.camera;target=C@Vector(center);camera.location=target+C@Vector(direction)*2;camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=scale
    scene.render.filepath=str(OUT/'review'/name)
    if '--skip-renders' not in sys.argv and ('--damage-review' not in sys.argv or name.startswith('damage')):bpy.ops.render.render(write_still=True)

def main():
    helper.clear();helper.materials();(OUT/'review').mkdir(exist_ok=True)
    main=bpy.context.scene;main.name='01 Animated ship - flight at frame 49';objects={}
    for e in DATA['objects']:objects[e['name']]=mesh_object(e,e['name'])[0]
    for e in DATA['objects']:
        ob=objects[e['name']];ob['cmp_semantic_object']=e['name']
        if e['parent']:ob.parent=objects[e['parent']]
    for frame,poses in DATA['frames'].items():
        for e in DATA['objects']:
            ob=objects[e['name']];world=matrix(poses[e['name'].lower()]);parent=matrix(poses[e['parent'].lower()]) if e['parent'] else Matrix.Identity(4)
            ob.matrix_basis=parent.inverted()@world;ob.rotation_mode='QUATERNION'
            ob.keyframe_insert(data_path='location',frame=int(frame));ob.keyframe_insert(data_path='rotation_quaternion',frame=int(frame))
    for h in DATA['hardpoints'].values():
        ob=bpy.data.objects.new(h['name'],None);main.collection.objects.link(ob);ob.empty_display_type='ARROWS';ob.empty_display_size=.12;ob.hide_render=True
        ob.parent=objects[h['owner']];ob.matrix_basis=matrix([h['orientation'],h['position']]);ob['hardpoint_kind']=h['kind']
    main.frame_start=1;main.frame_end=205;main.render.fps=24;main.frame_set(49);setup(main)
    for frame,name in [(1,'Folded / zero'),(49,'Flight'),(97,'Folded'),(145,'Flight'),(175,'Cargo open'),(205,'Cargo closed')]:main.timeline_markers.new(name,frame=frame)
    render(main,'flight_front.png',(10,6,-12));render(main,'flight_rear.png',(10,5,12));render(main,'flight_side.png',(15,0,0),14.3)
    render(main,'neck_detail.png',(4,3,-9),4.8,(0,.40,-4.45))
    render(main,'mounts_bottom.png',(3,-8,6),5.2,(0,-2.23,2.83))
    render(main,'mounts_uv_detail.png',(0,-10,1.5),3.5,(0,-2.44,2.42))
    render(main,'mounts_rear.png',(4,1,9),7.3,(0,-1.3,2.92))
    main.frame_set(1);render(main,'folded_front.png',(10,6,-12));main.frame_set(175);render(main,'cargo_open.png',(9,11,-9));main.frame_set(49)
    for level,parts in enumerate(DATA['levels'],1):
        scene=bpy.data.scenes.new('0'+str(level+1)+' LOD '+str(level)+' - flight');bpy.context.window.scene=scene
        for name,gs in parts.items():mesh_object(dict(groups=gs),name+' LOD'+str(level))
        setup(scene);render(scene,'lod'+str(level)+'_front.png',(10,6,-12));render(scene,'lod'+str(level)+'_rear.png',(10,5,12))
    scene=bpy.data.scenes.new('04 Torn survivors - static flight');bpy.context.window.scene=scene
    for e in DATA['objects']:
        if '_wing_' in e['name'] or e['name'].endswith('_engine_lod1'):continue
        mesh_object(e,e['name']+' surviving')
    for e in DATA['damage']:mesh_object(e,'Torn '+e['name'])
    setup(scene);render(scene,'damage_front.png',(10,6,-12));render(scene,'damage_rear.png',(10,4,12));render(scene,'damage_bottom.png',(10,-7,9))
    for lv,parts in enumerate(DATA['levels'],1):
        scene=bpy.data.scenes.new('0'+str(5+lv)+' Torn survivors LOD '+str(lv));bpy.context.window.scene=scene
        for name,gs in parts.items():
            if '_wing_' in name or name.endswith('_engine_lod1'):continue
            mesh_object(dict(groups=gs),name+' surviving LOD'+str(lv))
        for e in DATA['damage']:mesh_object(dict(groups=e['levels'][lv]),'Torn '+e['name']+' LOD'+str(lv))
        setup(scene);render(scene,'damage_lod'+str(lv)+'_rear.png',(10,4,12));render(scene,'damage_lod'+str(lv)+'_bottom.png',(10,-7,9))
    scene=bpy.data.scenes.new('05 Equipment placement - example models');bpy.context.window.scene=scene
    for e in DATA['objects']:mesh_object(e,e['name']+' equipment view')
    for e in DATA.get('equipment_examples',[]):mesh_object(e,e['name'])
    setup(scene);render(scene,'equipment_bottom.png',(4,-7,9),7.8,(0,-2,3.05));render(scene,'equipment_rear.png',(-6,2,10),8,(0,-1.5,2.92))
    bpy.context.window.scene=main;main.frame_set(49)
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    bpy.context.preferences.filepaths.save_version=0;bpy.context.preferences.filepaths.file_preview_type='NONE'
    path=OUT/'rh_pir_fighter.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
    main=bpy.data.scenes['01 Animated ship - flight at frame 49'];bpy.context.window.scene=main;error=0
    for frame in (1,25,49,70,97,145,160,175,205):
        main.frame_set(frame)
        for e in DATA['objects']:
            actual=main.objects[e['name']].matrix_world;expected=matrix(DATA['frames'][str(frame)][e['name'].lower()]);error=max(error,float(np.max(abs(np.array(actual)-np.array(expected)))))
    assert error<2e-5,error
    main.frame_set(49);hp_error=0
    for h in DATA['hardpoints'].values():
        actual=main.objects[h['name']].matrix_world;expected=matrix([h['orientation'],h['position']]);hp_error=max(hp_error,float(np.max(abs(np.array(actual)-np.array(expected)))))
    assert hp_error<2e-5,hp_error
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    (OUT/'blend_check.json').write_text(json.dumps(dict(file=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest(),cmp_sha256=DATA['cmp_sha256'],saved_reopened=True,frame=49,matrix_samples=9*len(DATA['objects']),max_matrix_error=error,hardpoints_checked=len(DATA['hardpoints']),max_hp_matrix_error=hp_error,scenes=[s.name for s in bpy.data.scenes]),indent=2))
    print('REVIEW BLEND VERIFIED',error,flush=True)

if __name__=='__main__':main()
