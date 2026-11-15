"""Create every blend, reopen it, then derive and verify its position dump."""
import json
from pathlib import Path
import sys
import bpy
from mathutils import Matrix, Quaternion, Vector

ROOT=Path(__file__).resolve().parent/'bundle'
DEST=ROOT/'SCENES'
DEST.mkdir(exist_ok=True)
(DEST/'DUMPS').mkdir(exist_ok=True)
ROOM=Path('E:/FL/room')
RX_NEG=Quaternion((1,0,0),-1.5708)
RX_POS=RX_NEG.inverted()

def mesh(path):
    bpy.ops.wm.obj_import(filepath=str(path),forward_axis='Y',up_axis='Z')
    objects=list(bpy.context.selected_objects)
    if len(objects)>1:
        bpy.context.view_layer.objects.active=objects[0]
        bpy.ops.object.join()
    return bpy.context.view_layer.objects.active

results={}
for file in sorted((ROOT/'specs').glob('*.json')):
    spec=json.loads(file.read_text())
    name=spec['name']
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source=mesh(ROOM/'trent_stand.obj')
    char_mesh=source.data
    bpy.data.objects.remove(source,do_unlink=True)
    meshes={}
    for n,p in spec['points'].items():
        character=n in spec['characters'] or n in spec['character_markers']
        obj=bpy.data.objects.new(n,char_mesh if character else None)
        bpy.context.scene.collection.objects.link(obj)
        pos=p.get('pos',[0,0,0])
        obj.location=(pos[0],-pos[2],pos[1])
        fl_quat=Matrix(p['orient']).to_quaternion() if 'orient' in p else Quaternion(p.get('q_orient',[1,0,0,0]))
        obj.rotation_mode='QUATERNION'
        obj.rotation_quaternion=RX_POS @ fl_quat.conjugated()
        if not character:
            obj.empty_display_type='CUBE' if n in spec['cameras'] else 'SPHERE'
            obj.empty_display_size=0.12 if n in spec['cameras'] else 0.065
            obj.show_name=True
        obj['role']='character placement' if character else ('camera' if n in spec['cameras'] else 'marker')
        obj['source_thn']=spec['source']
    if spec.get('room_mesh'):
        room=mesh(Path(spec['room_mesh']))
        room.name='ROOM_'+Path(spec['room_mesh']).stem
        room.rotation_mode='QUATERNION'
        room.rotation_quaternion=RX_POS
        room.location=(0,0,0)
        room.hide_select=True
    bpy.context.scene['source_thn']=spec['source']
    bpy.context.scene['room_mesh_status']=spec.get('room_mesh','No matching exported room mesh; placements only')
    bpy.context.scene['source_duration_seconds']=spec['duration']
    # Embedded source and Python make the reconstruction reviewable from Blender.
    for source_path,label in [(ROOT/name/'source.json','source.json'),
                              (ROOT/'Pythonlancer/story/cutscenes/story_scenes'/f'{name}.py',f'{name}.py'),
                              (ROOT/name/'report.json','report.json')]:
        block=bpy.data.texts.new(label); block.write(source_path.read_text(encoding='utf-8'))
    focus=next((bpy.data.objects[n] for n in spec['characters'] if n in bpy.data.objects),None)
    if focus:
        bpy.ops.object.select_all(action='DESELECT')
        focus.select_set(True); bpy.context.view_layer.objects.active=focus
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type=='VIEW_3D':
                    area.spaces.active.region_3d.view_location=focus.location
                    area.spaces.active.region_3d.view_distance=12
    bpy.ops.wm.save_as_mainfile(filepath=str(DEST/f'{name}.blend'))
    bpy.ops.wm.open_mainfile(filepath=str(DEST/f'{name}.blend'))
    dump={}
    error=0
    for obj in bpy.context.scene.objects:
        obj.rotation_mode='QUATERNION'
        quat=RX_NEG @ obj.rotation_quaternion
        dump[obj.name]={'position':list(obj.location),'orientation':list(quat)}
        if obj.name in spec['points']:
            p=spec['points'][obj.name]
            restored=Vector((obj.location.x,obj.location.z,-obj.location.y))
            delta=(restored-Vector(p.get('pos',[0,0,0]))).length
            error=max(error,delta)
            assert delta<0.03,(name,obj.name,delta)
            assert obj.type==('MESH' if obj.name in spec['characters'] or obj.name in spec['character_markers'] else 'EMPTY')
    (DEST/'DUMPS'/f'{name}.json').write_text(json.dumps(dump,indent=2),encoding='utf-8')
    results[name]={'objects':len(dump),'max_position_error':error,'reopened':True}
    print('VERIFIED',name,len(dump),flush=True)
(ROOT/'blender_results.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
