"""Blender form review of B04's actual exported triangles. Offline only."""
import hashlib
import json
import sys
from pathlib import Path

import bpy
import bmesh
from mathutils import Matrix, Vector, Quaternion
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import mesh_object,C

OUT=HERE.parents[1]/'out/ship_design/bw_family/elite/prototypes/b04_01'
FORM_ONLY=False
REAR_PRIORITY=False


def write(name,value):
    (OUT/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def main():
    raw=(OUT/'geometry.json').read_bytes();data=json.loads(raw)
    for path,digest in data['sources'].items():
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene;scene.name='B04 ELITE | shape review'
    for key,m in data['materials'].items():
        mat=bpy.data.materials.new(key);mat.use_nodes=True;mat.use_backface_culling=True
        name=m['name'].lower();colour=(.42,.47,.50,1)
        if FORM_ONLY:
            colour=(.49,.475,.435,1)
            if name=='pir_bw_panel_128':colour=(.43,.22,.075,1)
        if 'glass' in name:colour=(.065,.145,.18,1)
        elif name.endswith('d') or 'grill' in name:colour=(.105,.13,.145,1)
        elif 'engine' in name:colour=(.28,.32,.34,1)
        mat.diffuse_color=colour;mat['Native material']=m['name']
        nt=mat.node_tree;p=nt.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value=colour;p.inputs['Roughness'].default_value=.62
        p.inputs['Metallic'].default_value=.12
        if m.get('image_path'):
            tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(m['image_path'],check_existing=True)
            tex.image.pack();tex.label='Provisional native UV; not connected for shape review'
        if 'two' not in m.get('kind','').lower():
            geo=nt.nodes.new('ShaderNodeNewGeometry');transparent=nt.nodes.new('ShaderNodeBsdfTransparent')
            mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(geo.outputs['Backfacing'],mix.inputs[0])
            nt.links.new(p.outputs['BSDF'],mix.inputs[1]);nt.links.new(transparent.outputs[0],mix.inputs[2])
            nt.links.new(mix.outputs[0],nt.nodes.get('Material Output').inputs['Surface'])
    root=bpy.data.collections.new('B04 | editable form');scene.collection.children.link(root)
    cats={};objs={};stats=[];entries={}
    for e in data['objects']:
        category=e['category']
        if category not in cats:
            cats[category]=bpy.data.collections.new(category);root.children.link(cats[category])
        obj,slots=mesh_object(e,e['name'],position_decimals=5);objs[e['name']]=obj;entries[e['name']]=e
        if e.get('smooth_angle_degrees'):
            # Curved 04 surfaces are real tessellated geometry. Smooth only
            # their shallow joins; preserve cavity lips and authored creases.
            import math
            for poly in obj.data.polygons:poly.use_smooth=True
            obj.data.set_sharp_from_angle(angle=math.radians(e['smooth_angle_degrees']))
        for col in list(obj.users_collection):col.objects.unlink(obj)
        cats[category].objects.link(obj)
        obj['Native semantic owner']=e['owner'];obj['Stage']='Static form rework / unapproved' if FORM_ONLY else 'First shape prototype / unapproved'
        if category=='Native rig helpers':obj.hide_render=True;obj.hide_set(True)
        bm=bmesh.new();bm.from_mesh(obj.data)
        stats.append(dict(name=obj.name,triangles=len(obj.data.polygons),signed_volume=bm.calc_volume(signed=True),
                          boundary_edges=sum(ed.is_boundary for ed in bm.edges),
                          inconsistent_edges=sum(ed.is_manifold and not ed.is_contiguous for ed in bm.edges)))
        bm.free()
    def matrix(m,phase):
        if m['kind']=='wing':return Matrix.Translation(C@Vector(m['translation'])*phase)
        q=Matrix(m['rotation']).to_quaternion()
        r=Quaternion((1,0,0,0)).slerp(q,phase).to_matrix()
        pivot=C@Vector(m['pivot']);br=C@r@C.transposed()
        return Matrix.Translation(pivot)@br.to_4x4()@Matrix.Translation(-pivot)
    def pose(wing=0,cargo=0):
        for name,obj in objs.items():
            m=data['motion'].get(entries[name]['owner'])
            obj.matrix_world=matrix(m,wing if m['kind']=='wing' else cargo) if m else Matrix.Identity(4)
        bpy.context.view_layer.update()
    def bvh(obj,transform=None):
        return BVHTree.FromPolygons([(transform@v.co if transform is not None else v.co) for v in obj.data.vertices],
            [tuple(p.vertices) for p in obj.data.polygons],all_triangles=True,epsilon=0)
    visible={n:o for n,o in objs.items() if entries[n]['category']!='Native rig helpers'}
    trees={n:bvh(o) for n,o in visible.items()};contacts=[]
    for kind in ['wing','cargo']:
        for i in range(11):
            phase=i/10
            moving={n:matrix(data['motion'][entries[n]['owner']],phase) for n in visible
                    if entries[n]['owner'] in data['motion'] and data['motion'][entries[n]['owner']]['kind']==kind}
            for n,transform in moving.items():
                current=bvh(visible[n],transform)
                for other,tree in trees.items():
                    if other==n or other in moving:continue
                    overlap=current.overlap(tree)
                    if overlap:contacts.append(dict(kind=kind,phase=phase,moving=n,fixed=other,pairs=len(overlap)))
    # Check first front-facing hit from inside the cargo aperture.
    rays=[]
    for origin,direction in data['cargo_ray_probes']:
        ro=C@Vector(origin);rd=C@Vector(direction);hits=[]
        for n,tree in trees.items():
            if entries[n]['owner'].startswith('baydoor'):continue
            loc,normal,index,distance=tree.ray_cast(ro,rd,10)
            if loc is not None:hits.append((distance,n,list(C.transposed()@loc),normal.dot(rd)))
        assert hits,origin
        hit=min(hits);assert hit[3]<-.01,(origin,hit)
        rays.append(dict(origin=origin,direction=direction,hit=hit))
    write('blender_validation.json',dict(geometry_sha256=hashlib.sha256(raw).hexdigest(),objects=stats,
                                        sampled_motion_contacts=contacts,cargo_inward_ray_hits=rays,
                                        render_backface_culling=True))

    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=16
    scene.cycles.use_denoising=True
    scene.render.resolution_x=1600 if REAR_PRIORITY else 1280;scene.render.resolution_y=1200 if REAR_PRIORITY else 960;scene.render.resolution_percentage=100
    if REAR_PRIORITY:scene.cycles.samples=32
    scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value=(.055,.068,.085,1);bg.inputs[1].default_value=.55
    scene.view_settings.view_transform='AgX'
    studio=bpy.data.collections.new('Review studio');scene.collection.children.link(studio)
    center=C@Vector((0,-1.9,-3.0))
    def area(name,loc,power,size):
        l=bpy.data.lights.new(name,'AREA');l.energy=power;l.shape='DISK';l.size=size
        o=bpy.data.objects.new(name,l);studio.objects.link(o);o.location=C@Vector(loc)
        o.rotation_euler=(center-o.location).to_track_quat('-Z','Y').to_euler()
    area('Key',(8,14,-11),3400,9);area('Fill',(-12,7,-6),2200,10)
    area('Rear',(3,11,12),3400,7);area('Lower',(-5,-12,-1),1300,8)
    cd=bpy.data.cameras.new('Review camera');cam=bpy.data.objects.new('Review camera',cd)
    studio.objects.link(cam);scene.camera=cam;cd.type='ORTHO';cd.clip_end=300
    def view(direction):
        cam.location=center+(C@Vector(direction)).normalized()*40
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler()
        inv=cam.rotation_euler.to_matrix().transposed()
        points=[inv@(o.matrix_world@v.co-center) for o in visible.values() if not o.hide_render for v in o.data.vertices]
        lo=Vector([min(p[i] for p in points) for i in range(3)])
        hi=Vector([max(p[i] for p in points) for i in range(3)])
        shift=cam.rotation_euler.to_matrix()@Vector(((lo.x+hi.x)/2,(lo.y+hi.y)/2,0))
        cam.location+=shift;cd.ortho_scale=max(hi.x-lo.x,(hi.y-lo.y)*4/3)*1.14
    views=[('form_front_34',(1,.65,-1.10),0,0),('form_rear_34',(-1,.55,1.3),0,0),
           ('form_side',(1,0,0),0,0),('form_top',(0,1,.000001),0,0),
           ('form_rear',(0,0,1),0,0),('form_belly',(1,-.8,-1),0,0),
           ('form_folded',(1,.55,-1.1),1,0),('form_hold',(.7,1.6,-.5),0,1)]
    if FORM_ONLY:
        views=[('form_front_34',(-1,.70,-1.10),0,0),('form_rear_34',(1,.65,1.3),0,0),
               ('form_side',(-1,0,0),0,0),('form_top',(0,1,.000001),0,0),
               ('form_rear',(0,0,1),0,0),('form_belly',(-1,-.8,-1),0,0),
               ('form_hold',(-.5,1.5,-.25),0,0)]
    if REAR_PRIORITY:
        views=[('form_rear_34',(-1,.64,1.25),0,0),('form_front_34',(-1,.62,-1.10),0,0),
               ('form_rear',(0,0,1),0,0),('form_top',(0,1,.000001),0,0),
               ('form_side',(-1,0,0),0,0),('form_belly',(-1,-.8,1.1),0,0),
               ('form_hold',(-.5,1.5,-.25),0,0),('form_upper_rear_34',(-1,.64,1.25),0,0)]
    if '--quick' in sys.argv:views=views[:2]
    if '--only' in sys.argv:
        selected=sys.argv[sys.argv.index('--only')+1].split(',');views=[v for v in views if v[0] in selected]
    if '--check-only' in sys.argv:views=[]
    for name,direction,fold,door in views:
        hidden=[]
        if name=='form_upper_rear_34':
            for n,o in visible.items():
                if 'lower' in n.lower() or 'pyramid' in n.lower():hidden.append(o);o.hide_render=True
        pose(fold,door);view(direction)
        if FORM_ONLY and name=='form_hold':
            for n,o in objs.items():
                if entries[n]['owner'].startswith('baydoor'):o.hide_render=True
        scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
        for o in hidden:o.hide_render=False
        if FORM_ONLY and name=='form_hold':
            for n,o in objs.items():
                if entries[n]['owner'].startswith('baydoor'):o.hide_render=False
    # The review timeline is a convenience; original native script data in CMP
    # remain the authority, including launch timing and native folded zero pose.
    for frame,fold,door in ([(1,0,0)] if FORM_ONLY else [(1,0,0),(61,1,0),(81,0,0),(101,0,1)]):
        pose(fold,door)
        for n,obj in objs.items():
            if entries[n]['owner'] not in data['motion']:continue
            obj.rotation_mode='QUATERNION'
            obj.keyframe_insert('location',frame=frame);obj.keyframe_insert('rotation_quaternion',frame=frame)
    for frame,label in ([(1,'FLIGHT / static form review')] if FORM_ONLY else [(1,'FLIGHT / shape review'),(61,'WINGS STOWED'),(81,'FLIGHT'),(101,'CARGO OPEN')]):
        scene.timeline_markers.new(label,frame=frame)
    scene.frame_start=1;scene.frame_end=1 if FORM_ONLY else 101;scene.frame_set(1);pose();view((-1,.64,1.25) if REAR_PRIORITY else ((-1,.70,-1.10) if FORM_ONLY else (1,.65,-1.10)))
    for screen in bpy.data.screens:
        for area_ui in screen.areas:
            if area_ui.type=='VIEW_3D':
                space=area_ui.spaces.active;space.clip_end=300;space.shading.type='MATERIAL'
                space.region_3d.view_distance=26;space.region_3d.view_location=center
                space.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bw_pir_elite_b04.blend'))
    # Reopen the saved scene; confirm it actually contains the accepted output.
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'bw_pir_elite_b04.blend'))
    assert bpy.context.scene.frame_current==1
    assert all(n in bpy.data.objects for n in objs)
    write('blend_readback.json',dict(path=(OUT/'bw_pir_elite_b04.blend').as_posix(),
        sha256=hashlib.sha256((OUT/'bw_pir_elite_b04.blend').read_bytes()).hexdigest(),
        object_count=len(objs),reopened=True,default_pose='flight',frames=dict(flight=1) if FORM_ONLY else dict(flight=1,stowed=61,bay_open=101)))
    print('BW B04 BLENDER REVIEW COMPLETE',flush=True)


if __name__=='__main__':main()
