"""Editable neutral Q13/02 Blender prototype; static form review only."""
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
from rh_concept_b_final_blender import mesh_object,C

OUT=HERE.parents[1]/'out/ship_design/rh_freighter/prototypes/q13_02'
if '--variant' in sys.argv:
    variant=sys.argv[sys.argv.index('--variant')+1]
    assert variant in ('q13_02','q13_03','q13_04')
    OUT=OUT.parent/variant
LABEL=OUT.name.upper().replace('_','-')


def main():
    raw=(OUT/'geometry.json').read_bytes();data=json.loads(raw)
    assert hashlib.sha256(Path(data['source']).read_bytes()).hexdigest()==data['source_sha256']
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    scene=bpy.context.scene
    def material(name,colour,rough=.72):
        m=bpy.data.materials.new(name);m.diffuse_color=(*colour,1);m.use_nodes=True
        p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*colour,1)
        p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=.12
        return m
    for k,col in data['colours'].items():material(str(k),col)
    cockpit=material('Native cockpit / neutral review',(.43,.46,.48))
    glass=material('Native glazing / neutral review',(.11,.20,.24),.28)
    root=bpy.data.collections.new(LABEL+' / shape study');scene.collection.children.link(root)
    subs={}
    for label in ['01 Original cockpit','02 Main hull','03 Intakes','04 Side mechanisms','05 Circular roof','06 Engines']:
        coll=bpy.data.collections.new(label);root.children.link(coll);subs[label]=coll
    stats=[]
    for e in data['objects']:
        obj,slots=mesh_object(e,e['name']);obj.data.name=e['resource'];obj['Prototype']=LABEL+' / geometry only'
        obj['Closed authored solid']=e['closed']
        if e['name'].startswith('Original'):
            label='01 Original cockpit'
            for i in range(len(obj.data.materials)):obj.data.materials[i]=glass if 'glazing' in e['name'] else cockpit
        else:
            bm=bmesh.new();bm.from_mesh(obj.data)
            # Preserve the designed planes, dissolve only export triangulation.
            bmesh.ops.dissolve_limit(bm,angle_limit=math.radians(.05),verts=list(bm.verts),edges=list(bm.edges),delimit={'MATERIAL'})
            bm.to_mesh(obj.data);bm.free();obj.data.update()
            n=e['name'].lower()
            label='06 Engines' if 'engine' in n or 'exhaust' in n else '05 Circular roof' if 'circular' in n or 'roof' in n else '04 Side mechanisms' if 'unit' in n or 'socket' in n else '03 Intakes' if 'vane' in n else '02 Main hull'
        for col in list(obj.users_collection):col.objects.unlink(obj)
        subs[label].objects.link(obj)
        bm=bmesh.new();bm.from_mesh(obj.data)
        boundary=sum(e.is_boundary for e in bm.edges);nonman=sum(not e.is_manifold for e in bm.edges);bm.free()
        if e['closed']:assert not boundary and not nonman,(obj.name,boundary,nonman)
        stats.append(dict(object=obj.name,vertices=len(obj.data.vertices),polygons=len(obj.data.polygons),boundary=boundary))
    scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=40;scene.cycles.use_denoising=True
    scene.render.resolution_x=1600;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
    scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background')
    bg.inputs[0].default_value=(.12,.145,.175,1);bg.inputs[1].default_value=.50
    scene.view_settings.view_transform='AgX'
    stage=bpy.data.collections.new('Review studio');scene.collection.children.link(stage)
    def area(name,loc,power,size):
        l=bpy.data.lights.new(name,'AREA');l.energy=power;l.shape='DISK';l.size=size
        o=bpy.data.objects.new(name,l);stage.objects.link(o);o.location=C@Vector(loc)
        o.rotation_euler=(C@Vector((0,1,0))-o.location).to_track_quat('-Z','Y').to_euler()
    area('Key',(10,15,-7),6000,10);area('Fill',(-12,6,-15),4000,13);area('Rim',(5,13,16),6500,9)
    cd=bpy.data.cameras.new('Form camera');cam=bpy.data.objects.new('Form camera',cd);stage.objects.link(cam);scene.camera=cam
    cd.type='ORTHO';cd.clip_end=500
    def view(direction,center=(0,1.61,.30),scale=28):
        center=C@Vector(center);cam.location=center+(C@Vector(direction)).normalized()*65
        cam.rotation_euler=(center-cam.location).to_track_quat('-Z','Y').to_euler();cd.ortho_scale=scale
    views=[('form_perspective',(1,.7,-1.05),(0,1.61,.3),27),
           ('form_side',(1,0,0),(0,1.61,.3),27),
           ('form_top',(0,1,.00001),(0,1.61,.3),35),
           ('form_rear',(1,.60,1.20),(0,1.61,.3),27),
           ('form_front',(1,.45,-1.4),(0,1,-4.5),18),
           ('form_underside',(1,-.85,-1.05),(0,-.5,.3),27)]
    if '--quick' in sys.argv:views=views[:2]
    if '--remaining' in sys.argv:views=views[2:]
    if '--only' in sys.argv:
        selected=sys.argv[sys.argv.index('--only')+1]
        views=[v for v in views if v[0]==selected]
    for name,direction,center,scale in views:
        if name=='form_underside':area('Underside inspection fill',(4,-12,-5),3000,12)
        view(direction,center,scale);scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
        if name=='form_underside':bpy.data.objects['Underside inspection fill'].hide_render=True
    view((1,.7,-1.05),scale=27)
    for o in bpy.context.selected_objects:o.select_set(False)
    active=bpy.data.objects.get('Faceted shoulder and intake well +1');active.select_set(True);bpy.context.view_layer.objects.active=active
    for screen in bpy.data.screens:
        for a in screen.areas:
            if a.type=='VIEW_3D':
                s=a.spaces.active;s.shading.type='SOLID';s.shading.color_type='MATERIAL';s.shading.light='STUDIO'
                s.shading.show_cavity=True;s.shading.cavity_type='BOTH';s.overlay.show_floor=False
                s.overlay.show_axis_x=False;s.overlay.show_axis_y=False;s.overlay.show_extras=False
                s.region_3d.view_distance=34;s.region_3d.view_location=C@Vector((0,1.61,.3));s.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
    scene['Status']='Visual shape prototype. No automatic simplification. No installation.'
    scene['Source cabin SHA256']=data['cabin_hash'];scene['Geometry SHA256']=hashlib.sha256(raw).hexdigest()
    path=OUT/'rh_freighter_q13_form.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path))
    bpy.ops.wm.open_mainfile(filepath=str(path))
    assert len([o for o in bpy.context.scene.objects if o.type=='MESH'])==len(data['objects'])
    (OUT/'blender_check.json').write_text(json.dumps(dict(geometry_sha256=hashlib.sha256(raw).hexdigest(),blend=str(path),
        saved_and_reopened=True,objects=stats,triangle_count=data['total_triangles'],game_launched=False,installed=False),indent=2),encoding='utf8')
    print('Q13_FORM_READY',path,flush=True)


if __name__=='__main__':main()
