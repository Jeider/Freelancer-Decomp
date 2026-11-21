"""Offline F14 shape review from the same triangles exported to static CMP."""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import mesh_object,C

OUT=HERE.parents[1]/'out/ship_design/rh_fighter/prototypes/f14_01'
if '--variant' in sys.argv:
    variant=sys.argv[sys.argv.index('--variant')+1]
    assert variant in ('f14_01','f14_02','f14_03','f14_uv_01','f01_body_01','f01_uv_01','f01_uv_02','f01_uv_03')
    OUT=OUT.parent/variant


def main():
    raw=(OUT/'geometry.json').read_bytes();data=json.loads(raw)
    if '--textured' in sys.argv:data['preview_name_prefix']='textured'
    textured=data.get('preview_name_prefix')=='textured'
    for path,digest in data['sources'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    for key,m in data['materials'].items():
        mat=bpy.data.materials.new(key);mat.use_nodes=True;mat.use_backface_culling=True
        name=m.get('name','').lower()
        colour=(.35,.38,.40,1)
        if 'glass' in name:colour=(.07,.16,.21,1)
        elif 'dark' in name or name.endswith('d'):colour=(.15,.17,.18,1)
        mat.diffuse_color=colour
        p=mat.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value=colour;p.inputs['Roughness'].default_value=.62
        p.inputs['Metallic'].default_value=.15
        mat['Native material']=m.get('name',key)
        if m.get('image_path'):
            n=mat.node_tree.nodes.new('ShaderNodeTexImage')
            n.image=bpy.data.images.load(m['image_path'],check_existing=True);n.image.pack()
            n.label='Native UV reference only; clay form review';n.location=(-400,-250)
            if textured:
                n.label=m.get('texture','Native texture')
                multiply=mat.node_tree.nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY'
                multiply.inputs[0].default_value=1;rgba=tuple(m.get('colour',[1,1,1]))+(1,)
                multiply.inputs[2].default_value=rgba
                mat.node_tree.links.new(n.outputs['Color'],multiply.inputs[1])
                mat.node_tree.links.new(multiply.outputs[0],p.inputs['Base Color'])
        elif textured:
            p.inputs['Base Color'].default_value=tuple(m.get('colour',[.2,.2,.2]))+(1,)
        if textured:
            p.inputs['Roughness'].default_value=.78;p.inputs['Metallic'].default_value=0
        if '--cull' in sys.argv and 'two' not in m.get('kind','').lower():
            nt=mat.node_tree;geo=nt.nodes.new('ShaderNodeNewGeometry')
            transparent=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader')
            nt.links.new(geo.outputs['Backfacing'],mix.inputs[0]);nt.links.new(p.outputs['BSDF'],mix.inputs[1])
            nt.links.new(transparent.outputs[0],mix.inputs[2])
            nt.links.new(mix.outputs[0],nt.nodes.get('Material Output').inputs['Surface'])
    root=bpy.data.collections.new('F14 / editable shape prototype');scene.collection.children.link(root)
    cols={};objs={};stats=[]
    for e in data['objects']:
        cat=e['category']
        if cat not in cols:
            cols[cat]=bpy.data.collections.new(cat);root.children.link(cols[cat])
        precision=data.get('position_decimals',9 if textured else 5) if e['name'] not in ('Native_cabin','glass_lod1') else 5
        obj,slots=mesh_object(e,e['name'],position_decimals=precision);objs[e['name']]=obj
        for c in list(obj.users_collection):c.objects.unlink(obj)
        cols[cat].objects.link(obj)
        obj['Stage']='Static extended visual prototype; articulated rig comes after form approval'
        obj['Native material CRCs']=str(slots)
        bm=bmesh.new();bm.from_mesh(obj.data)
        volume=bm.calc_volume(signed=True)
        if e['authored_closed'] and '--diagnose' not in sys.argv:
            assert all(ed.is_manifold and ed.is_contiguous for ed in bm.edges),obj.name
            assert volume>0,(obj.name,volume)
        stats.append(dict(name=obj.name,triangles=len(obj.data.polygons),
            signed_volume=volume,
            boundary_edges=sum(ed.is_boundary for ed in bm.edges),
            inconsistent_winding_edges=sum(ed.is_manifold and not ed.is_contiguous for ed in bm.edges),
            nonmanifold_edges=sum(not ed.is_manifold for ed in bm.edges)))
        bm.free()
    motions=data.get('motion',{})
    door=objs.get('BayDoor_lod1')
    travel=C@Vector((0,.29331333136,3.35259188712))
    def matrix(motion,phase):
        def smooth(x):
            x=min(max(x,0),1);return x*x*(3-2*x)
        slide_start=motion.get('slide_start',0)
        slide=smooth((phase-slide_start)/(motion.get('slide_end',.30)-slide_start)) if motion['kind']=='wing' else phase
        start=motion.get('turn_start',.25)
        turn=smooth((phase-start)/(motion.get('turn_end',1)-start)) if motion['kind']=='wing' else smooth(phase)
        p=C@Vector(motion['pivot']);axis=C@Vector(motion['axis'])
        rotation=Matrix.Rotation(math.radians(motion['angle_degrees'])*turn,4,axis)
        delta=C@Vector(motion.get('translation',[0,0,0]))*slide
        return Matrix.Translation(p+delta)@rotation@Matrix.Translation(-p)
    def set_pose(cargo=0,wing=0):
        if not motions:door.location=travel*cargo
        for name,m in motions.items():objs[name].matrix_world=matrix(m,cargo if m['kind']=='door' else wing)
    def bvh(obj,delta=Vector((0,0,0)),transform=None):
        return BVHTree.FromPolygons([(transform@v.co if transform is not None else v.co+delta) for v in obj.data.vertices],
            [tuple(p.vertices) for p in obj.data.polygons],all_triangles=True,epsilon=0)
    door_names={n for n,m in motions.items() if m['kind']=='door'} if motions else {'BayDoor_lod1'}
    fixed={n:bvh(o) for n,o in objs.items() if n not in door_names}
    collisions=[];wing_collisions=[];root_contacts=[]
    if motions:
        all_fixed={n:bvh(o) for n,o in objs.items()}
        for kind,steps,report in [('door',31,collisions),('wing',61,wing_collisions)]:
            names=[n for n,m in motions.items() if m['kind']==kind]
            for step in range(steps):
                phase=step/(steps-1)
                current={n:bvh(objs[n],transform=matrix(motions[n],phase)) for n in names}
                for n in names:
                    for other,o in objs.items():
                        if other==n:continue
                        pairs=current[n].overlap(current.get(other,all_fixed[other]))
                        if not pairs:continue
                        # Sliding/rotating tongue is intentionally seated inside
                        # the covered carrier. Other hull contacts are failures.
                        carrier=n.replace('_swept_wing','_covered_root')
                        contacts=motions[n].get('contacts',[carrier])
                        if kind=='wing' and other in contacts:
                            root_contacts.append(dict(phase=phase,part=n,object=other,count=len(pairs)));continue
                        samples=[]
                        for moving_face,fixed_face in pairs[:3]:
                            poly=o.data.polygons[fixed_face]
                            samples.append([list(C.transposed()@o.data.vertices[ix].co) for ix in poly.vertices])
                        report.append(dict(phase=phase,part=n,object=other,count=len(pairs),fixed_face_samples=samples))
    else:
        for step in range(31):
            moving=bvh(door,travel*(step/30))
            for name,tree in fixed.items():
                pairs=moving.overlap(tree)
                if pairs:
                    samples=[]
                    for moving_face,fixed_face in pairs[:4]:
                        mesh=objs[name].data;poly=mesh.polygons[fixed_face]
                        samples.append([list(C.transposed()@mesh.vertices[ix].co) for ix in poly.vertices])
                    collisions.append(dict(phase=step/30,object=name,count=len(pairs),fixed_face_samples=samples))
    if collisions:
        (OUT/'lid_collision_debug.json').write_text(json.dumps(collisions,indent=2),encoding='utf8')
    if motions:
        (OUT/'motion_check.json').write_text(json.dumps(dict(door_collisions=collisions,wing_collisions=wing_collisions,
            intentional_carrier_contacts=root_contacts),indent=2),encoding='utf8')
    # Front-facing floor and wall hits from inside the open cargo aperture.
    rays=[]
    probes=data.get('cargo_ray_probes',[((0,1,-2.3),(0,-1,0)),((0,0,-2.3),(1,0,0)),
                             ((0,0,-2.3),(-1,0,0)),((0,0,-2.3),(0,0,-1))])
    for origin,direction in probes:
        ro=C@Vector(origin);rd=C@Vector(direction)
        hits=[]
        for name,tree in fixed.items():
            loc,norm,index,dist=tree.ray_cast(ro,rd,20)
            if loc is not None:hits.append((dist,name,list(C.transposed()@loc),norm.dot(rd)))
        hit=min(hits)
        assert hit[3]<0,(origin,hit)
        rays.append(dict(origin=origin,hit=hit))
    scene.render.engine='CYCLES';scene.cycles.device='CPU'
    scene.cycles.samples=20;scene.cycles.use_denoising=True
    scene.render.resolution_x=1400;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value=(.075,.09,.11,1);bg.inputs[1].default_value=.65
    scene.view_settings.view_transform='AgX'
    studio=bpy.data.collections.new('Review studio');scene.collection.children.link(studio)
    center=C@Vector((0,.35,-1.25))
    def area(name,loc,power,size):
        l=bpy.data.lights.new(name,'AREA');l.energy=power;l.shape='DISK';l.size=size
        o=bpy.data.objects.new(name,l);studio.objects.link(o);o.location=C@Vector(loc)
        o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    area('Key',(8,13,-11),2700,8);area('Fill',(-10,6,-5),1900,9)
    area('Rear rim',(5,10,11),3100,7);area('Belly fill',(0,-9,2),900,7)
    cd=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',cd)
    studio.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.clip_end=200
    points=[v.co for o in objs.values() for v in o.data.vertices]
    def view(direction,zoom=1):
        cam.location=center+(C@Vector(direction)).normalized()*35
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        inv=cam.rotation_euler.to_matrix().transposed()
        ps=[inv@(v-center) for v in points]
        w=max(p.x for p in ps)-min(p.x for p in ps);h=max(p.y for p in ps)-min(p.y for p in ps)
        cd.ortho_scale=max(w,h*1.4)*1.18*zoom
    views=[('form_front_34',(1,.65,-1.2)),('form_rear_34',(-1,.55,1.3)),
           ('form_side',(1,0,0)),('form_top',(0,1,.00001)),
           ('form_rear',(0,.00001,1)),('form_hold',(1,1.4,-.3))]
    if OUT.name in ('f14_02','f14_03','f14_uv_01','f01_body_01','f01_uv_01','f01_uv_02','f01_uv_03'):
        views[0]=('form_front_34',(1,.65,-.90));views[1]=('form_rear_34',(-1,.65,1.0))
        views.append(('form_belly',(1,-.65,-.60)))
    if textured:views.append(('form_other_side',(-1,.10,-.15)))
    if motions:views.extend([('form_folded',(1,.35,-1.2) if OUT.name in ('f01_uv_02','f01_uv_03') else (1,1.1,-.90)),('form_bottom',(0,-1,.00001))])
    if '--quick' in sys.argv:views=views[:2]
    if '--check-only' in sys.argv:views=[]
    if '--only' in sys.argv:
        selected=sys.argv[sys.argv.index('--only')+1].split(',');views=[v for v in views if v[0] in selected]
    for name,direction in views:
        set_pose(cargo=1 if name=='form_hold' else 0,wing=1 if name=='form_folded' else 0)
        view(direction);output_name=name.replace('form_',data.get('preview_name_prefix','form')+'_')
        scene.render.filepath=str(OUT/(output_name+'.png'))
        bpy.ops.render.render(write_still=True)
    if textured and '--quick' not in sys.argv and '--check-only' not in sys.argv and '--only' not in sys.argv:
        set_pose()
        for name,target,direction,scale in [
            ('detail_flank',(1.25,.15,-1.15),(1,.25,-.18),6.7),
            ('detail_engines',(0,-1.25,3.05),(1,.45,1.8),6.8),
            ('detail_roof',(0,1,-1.45),(.25,1,-.10),8.2),
            ('detail_underside',(0,-1.2,-.9),(-.4,-1,.2),8.5),
            ('detail_rear',(0,.35,3.5),(.1,.12,1),6.2),
            ('detail_engine_profile',(1.81,-1.49,2.9),(1,.2,-.20),3.5),
            ('detail_drum_front',(0,1.8,2.4),(.25,.28,-1),4.0),
            ('detail_carriage',(1.75,-.92,-.75),(1,.3,-.15),3.8)]:
            target=C@Vector(target);cam.location=target+(C@Vector(direction)).normalized()*35
            cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
            scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    set_pose()
    # Separate inspectable scene with opened native cargo lid. Other mesh data are shared.
    opened=scene.copy();opened.name='02 Cargo lid open'
    if door:
        replacement=door.copy();replacement.data=door.data;replacement.location=travel
    # Scene.copy shares collections: a fresh collection keeps door visibility independent.
    for co in list(opened.collection.children):opened.collection.children.unlink(co)
    oc=bpy.data.collections.new('Cargo inspection assembly');opened.collection.children.link(oc)
    for o in scene.objects:
        if o==door:oc.objects.link(replacement)
        elif o.name in door_names:
            replacement=o.copy();replacement.matrix_world=matrix(motions[o.name],1);oc.objects.link(replacement)
        else:oc.objects.link(o)
    scene.name='01 Extended form'
    if motions:
        folded=bpy.data.scenes.new('03 Wing folding study')
        folded.world=scene.world;folded.camera=cam
        fc=bpy.data.collections.new('Wing folding assembly');folded.collection.children.link(fc)
        for o in scene.objects:
            if o.name in motions and motions[o.name]['kind']=='wing':
                replacement=o.copy();replacement.matrix_world=matrix(motions[o.name],1);fc.objects.link(replacement)
            else:fc.objects.link(o)
        # Animate copies so static review scenes remain unambiguous.
        animated=bpy.data.scenes.new('04 Motion study - timeline')
        animated.world=scene.world;animated.camera=cam;animated.frame_end=240;animated.render.fps=30
        ac=bpy.data.collections.new('Articulated prototype');animated.collection.children.link(ac)
        for o in scene.objects:
            if o.name not in motions:ac.objects.link(o);continue
            replacement=o.copy();replacement.animation_data_clear();ac.objects.link(replacement)
            m=motions[o.name]
            for frame in range(1,241):
                if m['kind']=='door':phase=min((frame-1)/36,(73-frame)/36)
                else:phase=min((frame-90)/60,(240-frame)/60)
                phase=min(max(phase,0),1);replacement.matrix_world=matrix(m,phase)
                replacement.keyframe_insert('location',frame=frame);replacement.keyframe_insert('rotation_euler',frame=frame)
        animated.frame_set(1)
        hpcol=bpy.data.collections.new('Prototype hardpoints');scene.collection.children.link(hpcol)
        for h in data.get('hardpoints',[]):
            o=bpy.data.objects.new(h['name'],None);hpcol.objects.link(o);o.location=C@Vector(h['position'])
            o.empty_display_type='ARROWS';o.empty_display_size=.35;o.show_name=True
            o['Owner']=h['owner'];o['Prototype mount']=True
    view((1,.65,-1.2))
    bpy.context.window.scene=scene
    for o in bpy.context.selected_objects:o.select_set(False)
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':
                s=a.spaces.active;s.shading.type='MATERIAL' if textured else 'SOLID';s.shading.color_type='MATERIAL'
                s.shading.show_cavity=True;s.shading.cavity_type='BOTH';s.shading.show_backface_culling=True
                s.overlay.show_floor=False;s.overlay.show_axis_x=False;s.overlay.show_axis_y=False;s.overlay.show_extras=False
                s.region_3d.view_distance=19;s.region_3d.view_location=center
                s.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
    scene['Geometry source SHA256']=hashlib.sha256(raw).hexdigest()
    buried=data['drum']['submerged_height_fraction']
    scene['Drum buried / exposed']=f'{100*buried:.2f} / {100*(1-buried):.2f} percent of diameter at local roof Y=1.55'
    if data.get('placement'):
        scene['Rear placement']=json.dumps(data['placement'])
    scene['Status']=data.get('stage','Static form prototype, original cockpit; UV placeholders; no game deployment')
    if '--diagnose' not in sys.argv:assert not collisions,'Cargo lid intersects the authored hull'
    if '--diagnose' not in sys.argv:assert not wing_collisions,'Wing study intersects the authored hull'
    path=OUT/data.get('blend_basename','rh_pir_fighter_f14_form.blend')
    bpy.ops.wm.save_as_mainfile(filepath=str(path));bpy.ops.wm.open_mainfile(filepath=str(path))
    assert len([o for o in bpy.data.scenes['01 Extended form'].objects if o.type=='MESH'])==len(data['objects'])
    report=dict(geometry_sha256=hashlib.sha256(raw).hexdigest(),blend=str(path),saved_and_reopened=True,
                objects=stats,native_lid_sweep_phases=31,lid_collisions=collisions,
                cargo_front_facing_rays=rays,
                static_form_only=not bool(motions),wing_study_phases=61 if motions else 0,
                wing_collisions=wing_collisions,intentional_carrier_contacts=root_contacts,
                installed=False,game_launched=False)
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('F14_READY',path,'lid collisions',len(collisions),flush=True)


if __name__=='__main__':main()
