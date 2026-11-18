"""Blender background presentation of the actual revision-02 CMP export, no extra geometry."""
import argparse
import json
import hashlib
import math
from pathlib import Path
import sys

import bpy
from mathutils import Matrix, Vector, Quaternion

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure as configure_blender_workspace
configure_blender_workspace('ship_design')
sys.path.insert(0,str(HERE))
from rh_redesign_paths import CONCEPT_B_DETAIL as OUT


def main():
    global OUT
    parser=argparse.ArgumentParser()
    parser.add_argument('--video',action='store_true')
    parser.add_argument('--revision',type=int,choices=(2,3,4,5,6,7,8,9),default=2)
    parser.add_argument('--video-only',action='store_true')
    parser.add_argument('--cabin-only',action='store_true')
    parser.add_argument('--shape-only',action='store_true')
    parser.add_argument('--save-only',action='store_true')
    parser.add_argument('--prototype',action='store_true',help='Only a few static form views; no movie')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    if args.revision==3:
        from rh_redesign_paths import CONCEPT_B_FORM
        OUT=CONCEPT_B_FORM
    elif args.revision==4:
        from rh_redesign_paths import CONCEPT_B_PROFILE
        OUT=CONCEPT_B_PROFILE
    elif args.revision==5:
        from rh_redesign_paths import CONCEPT_B_VOLUME
        OUT=CONCEPT_B_VOLUME
    elif args.revision==6:
        from rh_redesign_paths import CONCEPT_B_ATTACHMENTS
        OUT=CONCEPT_B_ATTACHMENTS
    elif args.revision==7:
        from rh_redesign_paths import CONCEPT_B_COMPACT
        OUT=CONCEPT_B_COMPACT
    elif args.revision==8:
        from rh_redesign_paths import CONCEPT_B_SOCKETS
        OUT=CONCEPT_B_SOCKETS
    elif args.revision==9:
        from rh_redesign_paths import CONCEPT_B_MODEL
        OUT=CONCEPT_B_MODEL/'final_v1'
    data=json.loads((OUT/'blender_scene.json').read_text(encoding='utf8'))
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=40
    if args.prototype:scene.cycles.samples=16
    scene.cycles.use_denoising=True
    scene.render.threads_mode='FIXED'
    scene.render.threads=8
    scene.render.resolution_x=1400
    scene.render.resolution_y=1100
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.view_settings.view_transform='AgX'
    scene.world.color=(.25,.25,.25)
    scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.29,.32,.36,1)
    scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.55
    # Freelancer's +Y up, -Z forward -> Blender's +Z up, +Y forward.
    C=Matrix(((1,0,0),(0,0,-1),(0,1,0)))
    materials={}
    toggles=[]
    for key,info in data['materials'].items():
        name=info['name'].lower()
        mat=bpy.data.materials.new(info['name'])
        mat.use_nodes=True
        bsdf=mat.node_tree.nodes.get('Principled BSDF')
        clay=(.40,.43,.405,1)
        if name.endswith('256d') or 'dark' in name or 'metal' in name:clay=(.145,.17,.16,1)
        if 'engine_grill' in name:clay=(.09,.105,.10,1)
        if 'glass' in name:clay=(.045,.12,.18,1)
        mat.diffuse_color=clay
        bsdf.inputs['Base Color'].default_value=clay
        bsdf.inputs['Roughness'].default_value=.62 if 'glass' not in name else .27
        bsdf.inputs['Metallic'].default_value=.22 if 'glass' not in name else .25
        if args.revision>=3:
            # Match one-sided game geometry in Cycles too, not just viewport culling.
            mat.use_backface_culling=True
            geometry=mat.node_tree.nodes.new('ShaderNodeNewGeometry')
            transparent=mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
            cull=mat.node_tree.nodes.new('ShaderNodeMixShader')
            mat.node_tree.links.new(geometry.outputs['Backfacing'],cull.inputs[0])
            mat.node_tree.links.new(bsdf.outputs[0],cull.inputs[1])
            mat.node_tree.links.new(transparent.outputs[0],cull.inputs[2])
            mat.node_tree.links.new(cull.outputs[0],mat.node_tree.nodes.get('Material Output').inputs['Surface'])
        texfile=OUT/info['texture'] if info['texture'] else None
        if texfile and texfile.is_file():
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex.image=bpy.data.images.load(str(texfile))
            tex.image.pack()
            mix=mat.node_tree.nodes.new('ShaderNodeMixRGB')
            mix.name='Texture blend: 0 geometry review, 1 original texture'
            mix.label='0 = geometry review; 1 = original texture'
            mix.inputs[0].default_value=0
            mix.inputs[1].default_value=clay
            color=tex.outputs['Color']
            if args.revision>=6:
                dc=mat.node_tree.nodes.new('ShaderNodeMixRGB')
                dc.name='Native material diffuse multiplier'
                dc.blend_type='MULTIPLY';dc.inputs[0].default_value=1
                dc.inputs[2].default_value=(*info['colour'],1)
                mat.node_tree.links.new(color,dc.inputs[1]);color=dc.outputs['Color']
            mat.node_tree.links.new(color,mix.inputs[2])
            mat.node_tree.links.new(mix.outputs['Color'],bsdf.inputs['Base Color'])
            toggles.append(mix)
        elif args.revision>=6:
            bsdf.inputs['Base Color'].default_value=(*info['colour'],1)
        materials[key]=mat
    objects={}
    for entry in data['objects']:
        verts=[];normals=[];uvs=[];faces=[];face_mats=[];slots=[]
        for group in entry['groups']:
            slot=len(slots);slots.append(materials[str(group['material'])])
            for tri in group['corners']:
                ids=[]
                for corner in tri:
                    ids.append(len(verts))
                    verts.append(tuple(C@Vector(corner[:3])))
                    normals.append(tuple(C@Vector(corner[3:6])))
                    uvs.append((corner[6],1-corner[7]))
                faces.append(ids);face_mats.append(slot)
        geometry=bpy.data.meshes.new(entry['name']+'_LOD0')
        geometry.from_pydata(verts,[],faces)
        geometry.update()
        for mat in slots:geometry.materials.append(mat)
        uv=geometry.uv_layers.new(name='Original_UV')
        for polygon,slot in zip(geometry.polygons,face_mats):
            polygon.material_index=slot
            polygon.use_smooth=True
            for index in polygon.loop_indices:
                uv.data[index].uv=uvs[geometry.loops[index].vertex_index]
        geometry.normals_split_custom_set_from_vertices(normals)
        obj=bpy.data.objects.new(entry['name'],geometry)
        scene.collection.objects.link(obj)
        objects[entry['name']]=obj
        obj['CMP_component']=entry['file']
    for entry in data['objects']:
        obj=objects[entry['name']];joint=entry['joint']
        if joint['parent']:obj.parent=objects[joint['parent']]
        obj.location=C@Vector(joint['origin'])
        obj.rotation_mode='QUATERNION'
        obj.rotation_quaternion=(C@Matrix(joint['rotation'])@C.transposed()).to_quaternion()
        obj['hinge_axis_game']=joint['axis']
    scene.render.fps=24
    scene.frame_start=1
    scene.frame_end=288 if args.revision>=3 else 192
    byname={e['name']:e for e in data['objects']}
    def interpolated(keys,t):
        if t<=keys[0][0]:return keys[0][1]
        for a,b in zip(keys,keys[1:]):
            if t<=b[0]:
                f=(t-a[0])/(b[0]-a[0])
                return a[1]*(1-f)+b[1]*f
        return keys[-1][1]
    def phase_at(frame):
        if frame<25:p=1
        elif frame<73:p=1-(frame-25)/48
        elif frame<97:p=0
        elif frame<145:p=(frame-97)/48
        else:p=1
        return 1-p if args.revision>=3 else p
    for frame in range(1,scene.frame_end+1):
        phase=phase_at(frame)
        tracks=[(t,phase) for t in data['animation']]
        if args.revision>=3:
            door_phase=max(0,min(1,(frame-169)/32)) if frame<225 else max(0,1-(frame-225)/32)
            tracks.extend((t,door_phase) for t in data['doors'])
        for track,track_phase in tracks:
            obj=objects[track['object']];joint=byname[track['object']]['joint']
            angle=interpolated(track['keys'],track_phase*track['keys'][-1][0])
            axis=C@Vector(joint['axis'])
            original=(C@Matrix(joint['rotation'])@C.transposed()).to_quaternion()
            obj.rotation_quaternion=Quaternion(axis,angle)@original
            obj.keyframe_insert('rotation_quaternion',frame=frame)
    for obj in objects.values():
        if obj.animation_data:
            # The dense quaternion samples already come from the native CMP keys.
            for layer in obj.animation_data.action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        for curve in bag.fcurves:
                            for k in curve.keyframe_points:k.interpolation='LINEAR'
    scene['Notes']='Actual CMP LOD0 geometry. No subdivision or render-only detail. Metal texture is bay interior only.'
    scene['Triangle_count']=sum(len(o.data.polygons) for o in objects.values())
    scene['CMP_sha256']=hashlib.sha256((OUT/('rh_concept_b.cmp' if args.revision==9 else 'rh_concept_b_lod0.cmp')).read_bytes()).hexdigest()
    scene['Preview']='Frames 1-24 open; 25-73 fold; 73-97 folded; 97-145 unfold; revision 03: 169-201 bay opens, 225-257 closes.'
    # Background-only studio lights. The exported ship mesh itself is untouched.
    def area(name,where,energy,size,target=(0,0,0)):
        light=bpy.data.lights.new(name,'AREA');light.energy=energy;light.shape='DISK';light.size=size
        obj=bpy.data.objects.new(name,light);scene.collection.objects.link(obj)
        obj.location=C@Vector(where)
        obj.rotation_euler=((C@Vector(target))-obj.location).to_track_quat('-Z','Y').to_euler()
    area('Key',(8,14,-8),2600,9)
    area('Fill',(-10,7,-4),1600,10)
    area('Rim',(3,11,10),2900,8)
    camera_data=bpy.data.cameras.new('Review_camera')
    camera=bpy.data.objects.new('Review_camera',camera_data)
    scene.collection.objects.link(camera);scene.camera=camera
    full_scale=29.0 if args.revision>=4 else 21.0
    full_target=(0,2,2) if args.revision>=4 else (0,1,-.25)
    camera_data.type='ORTHO';camera_data.ortho_scale=full_scale
    target=C@Vector(full_target)
    def point_camera(direction,distance=35):
        camera.location=target+C@Vector(direction).normalized()*distance
        turn=(target-camera.location).to_track_quat('-Z','Y')
        if args.revision>=4 and direction[1]>.99 and abs(direction[0])<.001 and abs(direction[2])<.001:
            turn=turn@Quaternion((0,0,1),math.pi)  # TOP reference has the nose up.
        camera.rotation_euler=turn.to_euler()
    point_camera((1,.66,-1.20))
    scene.frame_set(1)
    if args.revision>=3:
        for toggle in toggles:toggle.inputs[0].default_value=1
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rh_concept_b_rigged.blend'))
    if args.save_only:
        print('READY_BLEND',OUT,flush=True)
        return
    for toggle in toggles:toggle.inputs[0].default_value=0
    def render(name,frame=1,direction=(1,.66,-1.20),distance=35):
        scene.frame_set(frame);point_camera(direction,distance)
        scene.render.filepath=str(OUT/name)
        bpy.ops.render.render(write_still=True)
    if args.prototype:
        render('geometry_open.png')
        render('geometry_side.png',1,(1,0,0))
        if args.revision==8:render('geometry_top.png',1,(0,1,-.0001))
        else:render('geometry_top_folded.png',84,(0,1,-.0001))
        for toggle in toggles:toggle.inputs[0].default_value=1
        render('textured_open.png')
        if args.revision>=6:
            render('textured_side.png',1,(1,0,0))
            if args.revision>=7:
                render('textured_rear.png',1,(0,.01,1))
                render('textured_top.png',1,(0,1,-.0001))
            area('Underside_review',(4,-9,-3),1900,8,(0,-1,3))
            render('textured_bottom.png',1,(.45,-1,-.65))
            target=C@Vector((1.8205 if args.revision>=7 else 3.15,-1.55,8.7));camera_data.ortho_scale=5.6
            for name,obj in objects.items():obj.hide_render='starboard_engine' not in name.lower()
            render('engine_detail.png',1,(1,-.1,-.1) if args.revision==8 else (-1,-.10,1) if args.revision>=7 else (1,-.25,-1))
            for obj in objects.values():obj.hide_render=False
            bpy.data.objects['Underside_review'].hide_render=True
            target=C@Vector((0,2.32 if args.revision>=7 else 3.18,8.41));camera_data.ortho_scale=9.8
            render('drum_detail.png',1,(1,.25,-.18))
            target=C@Vector((0,.2,-1.5));camera_data.ortho_scale=9.2
            render('cabin_transition.png',1,(1,.42,-.80))
            if args.revision==8:
                target=C@Vector((2.05,-.32,3.20));camera_data.ortho_scale=7.4
                render('side_sill.png',1,(1,.06,-.1))
                target=C@Vector((3.0,-.5,8.0));camera_data.ortho_scale=5.0
                render('wing_socket.png',1,(1,.5,-.9))
                target=C@Vector((0,.2,-1.2));camera_data.ortho_scale=8.5
                render('neck_front.png',1,(0,.70,-1))
                render('neck_bottom.png',1,(.20,-1,-.25))
                target=C@Vector((1.35,-.35,6.9));camera_data.ortho_scale=4.2
                render('tail_engine_join.png',1,(1,.24,-.75))
        print('READY_PROTOTYPE',OUT,flush=True)
        return
    if args.cabin_only:
        target=C@Vector((0,-.6,-6.0));camera_data.ortho_scale=5.7
        render('cabin_rear_culling.png',1,(1,.50,1),4.2)
        return
    if not args.video_only:
        render('geometry_open.png')
        render('geometry_folded.png',84)
        render('geometry_side.png',1,(1,0,0) if args.revision==4 else (1,.10,.001))
        if args.shape_only:
            render('geometry_top_open.png',1,(0,1,-.0001))
            render('geometry_top_folded.png',84,(0,1,-.0001))
            print('READY_SHAPE',OUT,flush=True)
            return
        for toggle in toggles:toggle.inputs[0].default_value=1
        render('textured_open.png')
        for toggle in toggles:toggle.inputs[0].default_value=0
        if args.revision>=3:
            render('geometry_top_open.png',1,(0,1,-.0001))
            render('geometry_top_folded.png',84,(0,1,-.0001))
            target=C@Vector((0,-.6,-6.0));camera_data.ortho_scale=5.7
            render('cabin_rear_culling.png',1,(1,.50,1),4.2)
            cargo_center=(0,1,3.62) if args.revision==4 else (0,.6,.53)
            target=C@Vector(cargo_center);camera_data.ortho_scale=6.7 if args.revision==4 else 5.0
            # A diagnostic inspection lamp makes the real floor/walls legible.
            cargo_z=cargo_center[2]
            area('Cargo_review_light',(0,7,cargo_z),350,3,(0,-1,cargo_z))
            for name,obj in objects.items():obj.hide_render=name!='Root'
            render('cargo_hidden_doors_culling.png',1,(.15,3,-.45),8)
            for name,obj in objects.items():obj.hide_render=name not in ('Root','BayDoor01_lod1','BayDoor02_lod1')
            render('cargo_open_culling.png',210,(.15,3,-.45),8)
            for obj in objects.values():obj.hide_render=False
            bpy.data.objects['Cargo_review_light'].hide_render=True
            target=C@Vector(full_target);camera_data.ortho_scale=full_scale
    if args.video:
        # Workbench makes the mechanics movie inexpensive; stills above use path tracing.
        scene.render.engine='BLENDER_WORKBENCH'
        scene.display.shading.light='STUDIO'
        scene.display.shading.studiolight_rotate_z=.45
        scene.display.shading.color_type='MATERIAL'
        scene.display.shading.show_shadows=True
        scene.display.shading.show_cavity=True
        scene.display.shading.cavity_type='BOTH'
        scene.display.shading.curvature_ridge_factor=1.3
        scene.display.shading.curvature_valley_factor=1.2
        scene.display.shading.background_type='WORLD'
        scene.world.color=(.04,.045,.055)
        scene.render.resolution_x=1000;scene.render.resolution_y=800
        frames=OUT/'animation_frames';frames.mkdir(exist_ok=True)
        for frame in range(1,scene.frame_end+1):
            scene.frame_set(frame)
            point_camera((1,.66,-1.20))
            scene.render.filepath=str(frames/f'{frame:04}.png')
            bpy.ops.render.render(write_still=True)
            if frame%24==0:print('ANIMATION',frame,'/',scene.frame_end,flush=True)
    print('READY_BLENDER',OUT,flush=True)


if __name__=='__main__':main()
