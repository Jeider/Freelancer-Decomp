"""Blender inspection scene for the Q13 CMP, without installation or game launch."""
import json
import math
import sys
from pathlib import Path
import hashlib
import bpy
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import mesh_object,C
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/prototypes/q13_01'


def main():
    data=json.loads((OUT/'scene.json').read_text(encoding='utf8'))
    assert hashlib.sha256(Path(data['cmp']).read_bytes()).hexdigest()==data['cmp_sha256']
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    for mid,m in data['materials'].items():
        mat=bpy.data.materials.new(mid);mat.use_nodes=True;mat.use_backface_culling='two' not in m['kind'].lower()
        mat.diffuse_color=(*m['colour'],1);bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Roughness'].default_value=.80;bsdf.inputs['Metallic'].default_value=.10
        if m.get('image_path'):
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(m['image_path'],check_existing=True)
            mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
            mix.inputs[2].default_value=(*m['colour'],1)
            mat.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);mat.node_tree.links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        else:
            bsdf.inputs['Base Color'].default_value=(.11,.22,.27,1);bsdf.inputs['Roughness'].default_value=.32
        mat['Native material']=m['name']
    objs={}
    for entry in data['objects']:
        obj,slots=mesh_object(entry,entry['name']);objs[entry['name']]=obj
        obj['Native file']=entry['file'];obj['Prototype']='Q13 / LOD0'
    for e in data['objects']:
        if e['joint']['parent']:objs[e['name']].parent=objs[e['joint']['parent']]
    def pose(wing,door,frame=None):
        for e in data['objects']:
            j=e['joint'];obj=objs[e['name']];r=Matrix(j['rotation']);t=Vector(j['origin']);value=0
            if j['kind']=='rev':value=door
            if j['kind']=='pris':value=wing
            if j['kind']=='rev':r=Quaternion(Vector(j['axis']).normalized(),value).to_matrix()@r
            if j['kind'] in ('rev','pris'):t-=r@Vector(j['offset'])
            if j['kind']=='pris':t+=Vector(j['axis'])*value
            obj.location=C@t;obj.rotation_mode='QUATERNION';obj.rotation_quaternion=(C@r@C.transposed()).to_quaternion()
            if frame is not None:
                obj.keyframe_insert('location',frame=frame);obj.keyframe_insert('rotation_quaternion',frame=frame)
        bpy.context.view_layer.update()
    wing_duration=next(c['duration'] for c in data['channels'] if c['script'].lower()=='sc_extend wing')
    end=161+round(wing_duration*30)
    for frame,w,a,label in [(1,1,0,'FLIGHT / native cylinders extended'),(33,1,0,'OPEN BAY'),
            (97,1,2.0943899154663086,'BAY OPEN / 120 degrees'),(161,1,0,'CLOSE BAY'),(end,0,0,'BASE / cylinders stowed')]:
        pose(w,a,frame);scene.timeline_markers.new(label,frame=frame)
    for obj in objs.values():
        action=obj.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(obj.animation_data.action_slot)
                if bag:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR'
    scene.frame_start=1;scene.frame_end=end;scene.render.fps=30;scene.frame_set(1);pose(1,0)
    # Dense geometric sweep of the shutter, with its actual source pivot and axis.
    # Report intersection pairs; a negative result is a mesh-surface test, not a physics proof.
    def bvh(o):
        return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],
            [tuple(p.vertices) for p in o.data.polygons],all_triangles=True,epsilon=0)
    intersections=[]
    for i in range(61):
        pose(1,2.0943899154663086*i/60);door=bvh(objs['Baydoor_lod1'])
        for name in ('Root','rh_port_side_lod1','rh_star_side_lod1','port_engine_lod1','starboard_engine_lod1'):
            hits=door.overlap(bvh(objs[name]))
            if hits:intersections.append(dict(phase=i/60,part=name,triangle_pairs=len(hits)))
    pose(1,0)
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True
    scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.19,.22,.26,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.55
    scene.view_settings.view_transform='AgX'
    def area(name,loc,power,size):
        li=bpy.data.lights.new(name,'AREA');li.energy=power;li.shape='DISK';li.size=size
        o=bpy.data.objects.new(name,li);scene.collection.objects.link(o);o.location=C@Vector(loc)
        o.rotation_euler=((C@Vector((0,1,0)))-o.location).to_track_quat('-Z','Y').to_euler()
    area('Large key',(5,17,-13),4800,14);area('Front fill',(-14,7,-10),3200,16);area('Rear rim',(6,11,16),4500,12)
    cd=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',cd);scene.collection.objects.link(cam);scene.camera=cam
    cd.type='ORTHO';cd.ortho_scale=29;cd.clip_end=300
    center=C@Vector((0,1.61,.30))
    def view(direction,scale=29):
        cam.location=center+(C@Vector(direction)).normalized()*55
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
    clay=bpy.data.materials.new('Neutral form inspection');clay.diffuse_color=(.36,.39,.42,1);clay.use_nodes=True
    clay.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.36,.39,.42,1)
    clay.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9
    for name,direction,material in [('blender_perspective',(1,.68,-1.05),None),('blender_clay',(1,.68,-1.05),clay),
            ('blender_side',(1,0,0),None),('blender_top',(0,1,.00001),None)]:
        view(direction);scene.view_layers[0].material_override=material
        scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    scene.view_layers[0].material_override=None
    scene.frame_set(97);pose(1,2.0943899154663086);view((1,1.2,-1.05))
    scene.render.filepath=str(OUT/'blender_bay_open.png');bpy.ops.render.render(write_still=True)
    scene.frame_set(1);pose(1,0);view((1,.68,-1.05))
    # Save the useful modeling view, not a camera-only workspace.
    for obj in bpy.context.selected_objects:obj.select_set(False)
    objs['Root'].select_set(True);bpy.context.view_layer.objects.active=objs['Root']
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':
                a.spaces.active.shading.type='MATERIAL';a.spaces.active.region_3d.view_distance=34
                a.spaces.active.region_3d.view_location=center;a.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
    target=OUT/'rh_freighter_q13.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target))
    bpy.ops.wm.open_mainfile(filepath=str(target))
    assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==len(data['objects'])
    report=dict(cmp_sha256=data['cmp_sha256'],blend=str(target),reopened=True,
        mesh_objects=len(data['objects']),shutter_sweep_samples=61,shutter_intersections=intersections,
        renders='offline Blender / native CMP geometry',game_launched=False)
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2))
    print('BLENDER_Q13_READY',len(intersections),'shutter intersection records',flush=True)


if __name__=='__main__':main()
