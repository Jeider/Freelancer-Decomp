"""Verify the exported CMP's full motion, then render/save its textured prototype."""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
from mathutils import Matrix,Vector,Quaternion
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import mesh_object,C
OUT=HERE.parents[1]/'out/ship_design/rh_freighter/prototypes/rig_01'
if '--variant' in sys.argv:
    variant=sys.argv[sys.argv.index('--variant')+1]
    assert variant.replace('_','').isalnum()
    OUT=OUT.parent/variant


def main():
    data=json.loads((OUT/'scene.json').read_text(encoding='utf8'))
    assert hashlib.sha256(Path(data['cmp']).read_bytes()).hexdigest()==data['cmp_sha256']
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    for mid,m in data['materials'].items():
        mat=bpy.data.materials.new(mid);mat.use_nodes=True;mat.use_backface_culling='two' not in m['kind'].lower()
        mat.diffuse_color=(*m['colour'],1);bsdf=mat.node_tree.nodes.get('Principled BSDF')
        bsdf.inputs['Roughness'].default_value=.82;bsdf.inputs['Metallic'].default_value=.10
        if m.get('image_path'):
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(m['image_path'],check_existing=True)
            tex.image.pack();mix=mat.node_tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
            mix.inputs[2].default_value=(*m['colour'],1)
            mat.node_tree.links.new(tex.outputs['Color'],mix.inputs[1]);mat.node_tree.links.new(mix.outputs[0],bsdf.inputs['Base Color'])
        else:
            bsdf.inputs['Base Color'].default_value=(*m['colour'],1);bsdf.inputs['Roughness'].default_value=.30
        mat['External native material']=m['name']
    objs={}
    for entry in data['objects']:
        obj,_=mesh_object(entry,entry['name']);objs[entry['name']]=obj
        obj.data.name=entry['file'];obj['Native file']=entry['file'];obj['Source authoring objects']='; '.join(entry['source_objects'])
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
    def bvh(o):
        return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons],all_triangles=True,epsilon=0)
    fixed=[n for n in objs if '_btn_' not in n and n!='Baydoor_lod1']
    moving=[n for n in objs if '_btn_' in n]
    pose(0,0);fixedtrees={n:bvh(objs[n]) for n in fixed}
    collisions=[]
    for i in range(65):
        phase=i/64;pose(0,2.0943899154663086*phase);door=bvh(objs['Baydoor_lod1'])
        for name,tree in fixedtrees.items():
            hit=door.overlap(tree)
            if hit:collisions.append(dict(kind='baydoor',phase=phase,fixed=name,pairs=len(hit)))
        # Both folded and extended button poses are well inside the roof radius;
        # still check their actual geometry against the rotating shell.
        for w in (0,1):
            pose(w,2.0943899154663086*phase)
            for name in moving:
                hit=door.overlap(bvh(objs[name]))
                if hit:collisions.append(dict(kind='baydoor_vs_button',phase=phase,wing=w,moving=name,pairs=len(hit)))
    for i in range(49):
        phase=i/48;pose(phase,0)
        for name in moving:
            movingtree=bvh(objs[name])
            for fixedname,tree in fixedtrees.items():
                hit=movingtree.overlap(tree)
                if hit:collisions.append(dict(kind='slider',phase=phase,moving=name,fixed=fixedname,pairs=len(hit)))
    pose(0,2.0943899154663086)
    hold_config=json.loads((OUT/'raised_hold_geometry.json').read_text()) if (OUT/'raised_hold_geometry.json').exists() else None
    probe_y=hold_config['new_floor_y']+.5 if hold_config else 0
    wallchecks=[];root=fixedtrees['Root'];origin=C@Vector((0,probe_y,.9))
    for direction,label in [((0,-1,0),'floor'),((1,0,0),'right wall'),((-1,0,0),'left wall'),((0,0,1),'rear wall'),((0,0,-1),'front wall')]:
        ray=C@Vector(direction);pos,normal,index,distance=root.ray_cast(origin,ray,30)
        assert pos is not None,(label,'missing hold wall')
        wallchecks.append(dict(wall=label,hit=list(C.transposed()@pos),front_facing=normal.dot(ray)<0))
    opening=bvh(objs['Baydoor_lod1']).ray_cast(origin,C@Vector((0,1,0)),30)[0]
    report=dict(cmp_sha256=data['cmp_sha256'],baydoor_samples=65,slider_samples=49,collisions=collisions,
        hold_rays=wallchecks,open_door_clears_vertical_axis=opening is None)
    if (OUT/'engine_check.json').exists():
        engine_checks=json.loads((OUT/'engine_check.json').read_text(encoding='utf8'))
        rays=[]
        for e in engine_checks['engines']:
            side=e['side'];cx,cy=e['center_xy'];name='port_engine_lod1' if side<0 else 'starboard_engine_lod1'
            tree=fixedtrees[name];direction=C@Vector((0,0,-1))
            for dx,dy in [(0,0),(.45,.30),(-.45,.30),(.45,-.30),(-.45,-.30)]:
                pos,normal,_,distance=tree.ray_cast(C@Vector((cx+dx,cy+dy,e['mouth_z']+.5)),direction,5)
                assert pos is not None,(name,'missing exhaust backing')
                native=C.transposed()@pos
                assert abs(native.z-e['exhaust_z'])<1e-4 and normal.dot(direction)<-.9,(name,list(native))
                rays.append(dict(part=name,hit=list(native),front_facing=True))
            # Four rays into channel walls prove that the recess has sides.
            throat_center=C@Vector((cx,cy,(e['mouth_z']+e['exhaust_z'])/2))
            for axis in [(1,0,0),(-1,0,0),(0,1,0),(0,-1,0)]:
                ray=C@Vector(axis);pos,normal,_,distance=tree.ray_cast(throat_center,ray,3)
                assert pos is not None and normal.dot(ray)<0,(name,'missing channel wall',axis)
        report['recessed_engine_exhaust_rays']=rays
    if (OUT/'aft_rib_geometry.json').exists():
        # The engines must actually meet the red structural rib, not the old
        # plain rear wall or empty space. Check the mount center and footprint.
        contact=[];direction=C@Vector((0,0,-1))
        for side in (-1,1):
            for dx,dy in [(0,0),(-.36,-.55),(.36,-.55),(-.36,.55),(.36,.55)]:
                origin=C@Vector((side*1.80+dx,-1.12+dy,9.0))
                pos,normal,index,_=root.ray_cast(origin,direction,3)
                assert pos is not None,'missing engine rib attachment'
                native=C.transposed()@pos
                assert abs(native.z-8.51)<1e-4 and normal.dot(direction)<-.99,list(native)
                material=objs['Root'].data.materials[objs['Root'].data.polygons[index].material_index]
                assert material['External native material']=='pir_r_panel02_256'
                contact.append(dict(side=side,point=list(native),surface='red rib',front_facing=True))
        report['engine_rib_contact_samples']=contact
    if (OUT/'aft_chevron_geometry.json').exists():
        shape=json.loads((OUT/'aft_chevron_geometry.json').read_text())
        checks=[];direction=C@Vector((0,0,-1))
        for x in (-1.30,-.685,0,.685,1.30):
            for y in (-1.70,0,1.30):
                pos,normal,index,_=root.ray_cast(C@Vector((x,y,10)),direction,4)
                assert pos is not None,'missing chevron wall'
                native=C.transposed()@pos
                expected=shape['outer_rear_z']-shape['center_recess']*max(0,1-abs(x)/shape['inner_rib_x'])
                assert abs(native.z-expected)<1e-4 and normal.dot(direction)<-.8,(list(native),expected)
                material=objs['Root'].data.materials[objs['Root'].data.polygons[index].material_index]
                expected_material=shape.get('rear_material','pir_r_panel03_256')
                assert material['External native material']==expected_material
                checks.append(dict(hit=list(native),expected_z=expected,material=expected_material,front_facing=True))
        report['aft_chevron_samples']=checks
    if (OUT/'vent_clearance.json').exists():
        # Sample the complete well behind the blades. The inner core must not
        # poke through the brown backing, including its lower diagonal portion.
        poly=[(-6.85,-.67),(-6.85,.80),(-5.35,1.91),(-4.12,1.91),(-4.12,.85),(-5.18,-.02)]
        def inside(z,y):
            signs=[]
            for (az,ay),(bz,by) in zip(poly,poly[1:]+poly[:1]):
                signs.append((bz-az)*(y-ay)-(by-ay)*(z-az))
            return min(signs)>.035 or max(signs)<-.035
        rays=[]
        for side,name in [(-1,'rh_port_side_lod1'),(1,'rh_star_side_lod1')]:
            ray=C@Vector((-side,0,0));shell=fixedtrees[name]
            for iz in range(11):
                z=-6.75+iz*.25
                for iy in range(10):
                    y=-.55+iy*.25
                    if not inside(z,y):continue
                    hit,_,_,_=root.ray_cast(C@Vector((side*4,y,z)),ray,8)
                    if hit is not None:assert side*(C.transposed()@hit).x<=2.581,(side,y,z,'core intrudes into vent')
                    clearance=json.loads((OUT/'vent_clearance.json').read_text())
                    floor_x=clearance['vent_floor_x']
                    hit,n,idx,_=shell.ray_cast(C@Vector((side*(floor_x+.01),y,z)),ray,1)
                    assert hit is not None and abs(abs((C.transposed()@hit).x)-floor_x)<1e-4,(side,y,z,'missing vent backing')
                    mat=objs[name].data.materials[objs[name].data.polygons[idx].material_index]
                    assert mat['External native material']=='pir_r_panel01_256D',(side,y,z,'wrong backing material')
                    assert n.dot(ray)<0
                    rays.append([side,y,z])
        report['brown_vent_backing_samples']=len(rays)
    (OUT/'motion_check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('MOTION_CHECK',len(collisions),'collision records',flush=True)
    assert not collisions,collisions[:8]
    assert all(w['front_facing'] for w in wallchecks) and opening is None
    if '--check-only' in sys.argv:return
    # Native launch: hold folded for 5 s, extend during the final 2 s.
    launch=next(c for c in data['channels'] if c['script']=='sc_launch extend')
    for t,value in zip(launch['times'],launch['values']):pose(value[0],0,1+round(t*30))
    for frame,w,a,label in [(1,0,0,'BASE / native zero pose'),(211,1,0,'LAUNCH END / FLIGHT'),
        (241,1,0,'FOLD'),(301,0,0,'FOLDED'),(331,0,0,'EXTEND'),(391,1,0,'FLIGHT'),
        (421,0,0,'BAY OPEN'),(485,0,2.0943899154663086,'BAY FULLY OPEN'),(515,0,2.0943899154663086,'BAY CLOSE'),(579,0,0,'BASE')]:
        pose(w,a,frame);scene.timeline_markers.new(label,frame=frame)
    # Bake the exact native scalar angle at each frame. Interpolating only
    # two quaternion keys would change angular velocity inside the stroke.
    for i in range(65):
        pose(0,2.0943899154663086*i/64,421+i)
        pose(0,2.0943899154663086*(1-i/64),515+i)
    for obj in objs.values():
        action=obj.animation_data.action
        for layer in action.layers:
            for strip in layer.strips:
                bag=strip.channelbag(obj.animation_data.action_slot)
                if bag:
                    for curve in bag.fcurves:
                        for key in curve.keyframe_points:key.interpolation='LINEAR'
    scene.frame_start=1;scene.frame_end=579;scene.render.fps=30;scene.frame_set(1);pose(0,0)
    # Hardpoint markers stay on the original owner and use its native local frame.
    hpcol=bpy.data.collections.new('Native hardpoints / editable reference');scene.collection.children.link(hpcol)
    build=json.loads((OUT/'build.json').read_text(encoding='utf8'));files={e['file']:e['name'] for e in data['objects']}
    for hp in build['hardpoints'].values():
        marker=bpy.data.objects.new(hp['name'],None);hpcol.objects.link(marker);marker.empty_display_type='ARROWS';marker.empty_display_size=.18
        parent=objs[files[hp['file']]];world=Matrix.Translation(C@Vector(hp['position']))@(C@Matrix(hp['orientation'])@C.transposed()).to_4x4()
        marker.parent=parent;marker.matrix_basis=parent.matrix_world.inverted()@world;marker.hide_render=True
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=32;scene.cycles.use_denoising=True
    scene.render.resolution_x=1500;scene.render.resolution_y=1125;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs[0].default_value=(.12,.145,.175,1);bg.inputs[1].default_value=.6
    scene.view_settings.view_transform='AgX'
    def area(name,loc,power,size):
        li=bpy.data.lights.new(name,'AREA');li.energy=power;li.shape='DISK';li.size=size
        ob=bpy.data.objects.new(name,li);scene.collection.objects.link(ob);ob.location=C@Vector(loc)
        ob.rotation_euler=(C@Vector((0,1,0))-ob.location).to_track_quat('-Z','Y').to_euler()
    area('Key',(10,15,-7),5000,10);area('Fill',(-12,6,-15),3500,13);area('Rim',(5,13,16),5000,9)
    cd=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',cd);scene.collection.objects.link(cam);scene.camera=cam
    cd.type='ORTHO';cd.clip_end=300;center=C@Vector((0,1.61,.3))
    def view(direction,scale=27):
        cam.location=center+(C@Vector(direction)).normalized()*65;cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
    views=[('textured_flight',211,(1,.70,-1.05)),('textured_folded',1,(1,.70,-1.05)),
        ('textured_side',211,(1,0,0)),('textured_bay_open',485,(1,1.3,-1.05)),('textured_rear',211,(1,.65,1.2)),
        ('textured_underside',211,(1,-.85,-1.05))]
    if '--quick' in sys.argv:views=[views[0],views[3]]
    if '--remaining' in sys.argv:views=[v for v in views if v[0] not in ('textured_flight','textured_bay_open')]
    if '--engine-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('textured_rear',211,(1,.65,1.2)),
            ('textured_side',211,(1,0,0)),('textured_top',211,(0,1,0)),
            ('engine_detail',211,(.65,.55,1.1)),('engine_clay',211,(.65,.55,1.1))]
    if '--uv-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('textured_side',211,(1,0,0)),
            ('textured_top',211,(0,1,0)),('textured_underside',211,(.18,-1,-.12)),
            ('textured_rear',211,(1,.65,1.2)),('engine_detail',211,(.65,.55,1.1)),
            ('neck_detail',211,(.15,1,-.4)),('vent_detail',211,(1,.12,-.15)),
            ('textured_bay_open',485,(1,1.3,-1.05))]
    if '--detail-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('textured_side',211,(1,0,0)),
            ('textured_top',211,(0,1,0)),('textured_underside',211,(.18,-1,-.12)),
            ('engine_detail',211,(.65,.55,1.1)),('engine_mount',211,(.2,1,.2)),
            ('engine_mount_side',211,(1,.05,0)),('slider_underside',211,(1,-.32,-.10)),
            ('neck_detail',211,(.15,1,-.4)),('vent_detail',211,(1,.12,-.15)),
            ('contour_detail',211,(1,.15,-.1)),('textured_bay_open',485,(1,1.3,-1.05))]
    if '--b3-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('textured_side',211,(1,0,0)),
            ('textured_top',211,(0,1,0)),('textured_underside',211,(0,-1,-.001)),
            ('engine_detail',211,(.65,.55,1.1)),('engine_mount_side',211,(1,.05,0)),
            ('engine_clay',211,(.65,.55,1.1)),('textured_rear',211,(0,.35,1)),
            ('slider_underside',211,(1,-.32,-.1)),('neck_detail',211,(0,1,-.35)),
            ('vent_detail',211,(1,.12,-.15)),('roof_rail',211,(.55,1,-.25)),
            ('textured_bay_open',485,(1,1.3,-1.05))]
    if '--aft-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('textured_side',211,(1,0,0)),
            ('textured_top',211,(0,1,0)),('textured_rear',211,(0,.35,1)),
            ('engine_detail',211,(.65,.55,1.1)),('engine_mount_side',211,(1,.05,0)),
            ('engine_front_detail',211,(1,.25,-.45)),('aft_rib_detail',211,(1,.18,1)),
            ('textured_bay_open',485,(1,1.3,-1.05))]
    if '--chevron-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('textured_side',211,(1,0,0)),
            ('aft_top',211,(0,1,.001)),('aft_underside',211,(.35,-1,1)),
            ('aft_back',211,(0,.001,1)),('aft_corner_right',211,(1,1,.65)),
            ('aft_corner_left',211,(-1,1,.65)),('engine_front_detail',211,(1,.25,-.45)),
            ('textured_bay_open',485,(1,1.3,-1.05))]
    if '--uv09-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('contour_front',211,(1,.65,-.65)),
            ('aft_back',211,(0,.001,1)),('aft_underside',211,(.35,-1,1)),
            ('aft_corner_right',211,(1,1,.65)),('aft_corner_left',211,(-1,1,.65)),
            ('textured_bay_open',485,(1,1.3,-1.05)),('hold_inside',485,(.12,1,-.20)),
            ('hold_shell',485,(.12,1,-.20))]
    if '--uv10-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('aft_back',211,(0,.001,1)),
            ('aft_top',211,(0,1,.001)),('aft_underside',211,(.35,-1,1)),
            ('aft_gap_right',211,(.2,1,.2)),('aft_gap_left',211,(-.2,1,.2)),
            ('textured_bay_open',485,(1,1.3,-1.05)),('hold_inside',485,(.12,1,-.20))]
    if '--cornice-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('cornice_rear',211,(0,.001,1)),
            ('cornice_corner',211,(.85,.50,1)),('cornice_side',211,(1,.08,.10)),
            ('aft_top',211,(0,1,.001)),('hold_inside',485,(.12,1,-.20))]
    if '--fore-cornice-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('textured_side',211,(1,0,0)),
            ('fore_corner',211,(.85,.55,-1)),('fore_corner_left',211,(-.85,.55,-1)),
            ('fore_front',211,(0,.20,-1)),('fore_side',211,(1,0,0)),('fore_top',211,(0,1,.001))]
    if '--symmetric-cornices-review' in sys.argv:
        views=[('textured_flight',211,(1,.70,-1.05)),('textured_side',211,(1,0,0)),
            ('fore_corner',211,(.85,.55,-1)),('fore_top',211,(0,1,.001)),
            ('cornice_corner',211,(.85,.55,1)),('cornice_rear',211,(0,.20,1)),
            ('cornice_top',211,(0,1,.001)),('cornice_side',211,(1,0,0))]
    if '--only' in sys.argv:
        requested=sys.argv[sys.argv.index('--only')+1].split(',')
        views=[v for v in views if v[0] in requested]
        assert len(views)==len(requested)
    for label,frame,direction in views:
        original_center=center.copy()
        if label.startswith('engine_'):center=C@Vector((0,-.10,9.7))
        if label=='neck_detail':center=C@Vector((0,1.4,-5.7))
        if label=='vent_detail':center=C@Vector((2.9,2.0,-4.9))
        if label.startswith('engine_mount'):center=C@Vector((0,-.10,8.8))
        if label=='slider_underside':center=C@Vector((3.8,2.1,.6))
        if label=='contour_detail':center=C@Vector((3.25,-1.6,.35))
        if label=='roof_rail':center=C@Vector((1.75,6.1,1.0))
        if label=='engine_front_detail':center=C@Vector((1.8,-.28,9.8))
        if label=='aft_rib_detail':center=C@Vector((1.8,-.2,7.6))
        if label in ('aft_top','aft_underside','aft_back'):center=C@Vector((0,-.1,8.0))
        if label.startswith('aft_corner_'):center=C@Vector(((-1 if label.endswith('left') else 1)*2.9,2.3,6.0))
        if label.startswith('aft_gap_'):center=C@Vector(((-1 if label.endswith('left') else 1)*2.45,.6,7.5))
        if label=='contour_front':center=C@Vector((2.9,2.2,-4.5))
        if label.startswith('hold_'):center=C@Vector((0,1.2,.9))
        if label.startswith('cornice_'):center=C@Vector((0,1.30,8.15))
        if label.startswith('cornice_') and '--symmetric-cornices-review' in sys.argv:
            back=json.loads((OUT/'cornice_geometry.json').read_text())
            center=C@Vector((0,1.65,2*back['mirror_plane_z']+7.0))
        if label.startswith('fore_'):center=C@Vector((0,1.65,-7.0))
        scene.frame_set(frame);view(direction)
        if label=='textured_top':cd.ortho_scale=35.5
        if label.startswith('engine_'):cd.ortho_scale=11.5
        if label=='neck_detail':cd.ortho_scale=10
        if label=='vent_detail':cd.ortho_scale=7.8
        if label=='slider_underside':cd.ortho_scale=12.8
        if label=='contour_detail':cd.ortho_scale=17
        if label=='roof_rail':cd.ortho_scale=8
        if label=='engine_front_detail':cd.ortho_scale=7
        if label=='aft_rib_detail':cd.ortho_scale=10
        if label in ('aft_top','aft_underside','aft_back'):cd.ortho_scale=12
        if label.startswith('aft_corner_'):cd.ortho_scale=8
        if label.startswith('aft_gap_'):cd.ortho_scale=5
        if label=='contour_front':cd.ortho_scale=10
        if label.startswith('hold_'):
            cd.ortho_scale=13.5
            area('Cargo inspection light',(0,4,.9),250,3)
        if label.startswith('cornice_'):cd.ortho_scale=9.5
        if label.startswith('cornice_') and '--symmetric-cornices-review' in sys.argv:cd.ortho_scale=10
        if label.startswith('fore_'):cd.ortho_scale=10
        if label=='hold_shell':objs['Baydoor_lod1'].hide_render=True
        if label=='engine_clay':
            clay=bpy.data.materials.new('Engine form review');clay.diffuse_color=(.34,.38,.42,1)
            bpy.context.view_layer.material_override=clay
        if 'underside' in label:area('Bottom fill',(4,-12,-5),2500,12)
        scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
        if 'underside' in label:bpy.data.objects['Bottom fill'].hide_render=True
        if label.startswith('hold_'):
            for ob in scene.objects:
                if ob.name.startswith('Cargo inspection light'):ob.hide_render=True
        if label=='hold_shell':objs['Baydoor_lod1'].hide_render=False
        bpy.context.view_layer.material_override=None;center=original_center
    scene.frame_set(211 if '--review-open' in sys.argv else 1);view((1,.70,-1.05))
    for ob in bpy.context.selected_objects:ob.select_set(False)
    objs['Root'].select_set(True);bpy.context.view_layer.objects.active=objs['Root']
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':
                s=a.spaces.active;s.shading.type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_floor=False
                s.region_3d.view_distance=34;s.region_3d.view_location=center;s.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
    target=OUT/'rh_pir_freighter_prototype.blend';bpy.ops.wm.save_as_mainfile(filepath=str(target));bpy.ops.wm.open_mainfile(filepath=str(target))
    assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==len(data['objects'])
    expected_frame=211 if '--review-open' in sys.argv else 1
    assert bpy.context.scene.frame_current==expected_frame
    report.update(saved_and_reopened=True,blend=str(target),default_pose='flight' if expected_frame==211 else 'folded',installed=False,game_launched=False)
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('RIG_BLENDER_READY',target,flush=True)


if __name__=='__main__':main()
