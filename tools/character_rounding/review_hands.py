"""Native-animation validation, matched renders and editable hand armatures."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import sys
import bpy
import numpy as np
from mathutils import Matrix,Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).resolve().parent))
from blender_workspace import configure
configure('character_rounding')
from hand_animations import bindings,pose,skin
OUT=ROOT/'out/character_rounding/hands'
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)));C4=C.to_4x4()
ap=argparse.ArgumentParser();ap.add_argument('--name',action='append');ap.add_argument('--render',action='store_true');ap.add_argument('--gloves',action='store_true')
args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ANIMATIONS=OUT
if args.gloves:OUT=ROOT/'out/character_rounding/gloves'


def read(path):return json.loads(gzip.decompress(path.read_bytes()))


def make(data,title):
    col=bpy.data.collections.new(title);bpy.context.scene.collection.children.link(col)
    arm=bpy.data.armatures.new(title);rig=bpy.data.objects.new(title+' rig',arm);col.objects.link(rig)
    bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
    bind=bindings(data)
    for b,B in zip(data['bones'],bind):
        eb=arm.edit_bones.new(b['name']);eb.length=.014;eb.matrix=C4@Matrix(B.tolist())
    for b in data['bones']:
        if b['parent']:arm.edit_bones[b['name']].parent=arm.edit_bones[b['parent']]
    bpy.ops.object.mode_set(mode='OBJECT');rig.select_set(False);rig.show_in_front=True
    pts=[C@Vector(p) for p in data['points']];tris=[t for g in data['groups'] for t in g['faces']]
    mesh=bpy.data.meshes.new(title);mesh.from_pydata(pts,[],[[data['point_indices'][i] for i in t] for t in tris]);mesh.update()
    ob=bpy.data.objects.new(title+' mesh',mesh);col.objects.link(ob);ob.parent=rig
    uv=mesh.uv_layers.new(name='UV0')
    for p,t in zip(mesh.polygons,tris):
        p.use_smooth=True
        for loop,i in zip(p.loop_indices,t):uv.data[loop].uv=data['uv'][data['uv_indices'][i]]
    for i,b in enumerate(data['bones']):
        vg=ob.vertex_groups.new(name=b['name'])
        for v,w in enumerate(data['skin']):
            if w.get(str(i),0):vg.add([v],w[str(i)],'REPLACE')
    mod=ob.modifiers.new('Native linear skin','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False
    mat=bpy.data.materials.new(title);mat.use_nodes=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.72
    tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(data['groups'][0]['texture'],check_existing=True)
    mat.node_tree.nodes.active=tex
    mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(mat)
    for b in data['bones']:arm.bones[b['name']]['native_inverse_bind']=b['native_bind']
    return col,rig,ob


def apply_pose(rig,data,world,frame=None):
    bind=bindings(data);ids={b['name']:i for i,b in enumerate(data['bones'])}
    for i,b in enumerate(data['bones']):
        parent=ids.get(b['parent'])
        local=world[i] if parent is None else np.linalg.inv(world[parent])@world[i]
        rest=bind[i] if parent is None else np.linalg.inv(bind[parent])@bind[i]
        pb=rig.pose.bones[b['name']];pb.rotation_mode='QUATERNION';pb.matrix_basis=Matrix((np.linalg.inv(rest)@local).tolist())
        if frame is not None:
            for prop in ('location','rotation_quaternion','scale'):pb.keyframe_insert(prop,frame=frame)
    bpy.context.view_layer.update()


def validate(data,clips):
    p=np.array(data['points']);all_ids={b['name'] for b in data['bones']};tested=0;frames=0;reach=0
    for name,clip in clips.items():
        if not set(clip)<=all_ids:continue
        times=sorted({row[0] for channel in clip.values() for row in channel})
        for t in times:
            moved=skin(data,pose(data,clip,t));assert np.isfinite(moved).all(),(name,t)
            assert np.max(np.linalg.norm(moved,axis=1))<.4,(name,t)
            reach=max(reach,float(np.max(np.linalg.norm(moved-p,axis=1))));frames+=1
        tested+=1
    assert tested>=20,tested
    rest=skin(data,bindings(data));error=float(np.max(abs(rest-p)));assert error<1e-6
    return dict(native_clips=tested,native_sample_times=frames,rest_error_m=error,max_animated_displacement_m=reach)


def main(folder):
    original=read(folder/'source.json.gz');edited=read(folder/'edited.json.gz')
    clips=read(ANIMATIONS/('animations_'+('female' if 'female' in edited.get('geometry_family',folder.name) else 'male')+'.json.gz'))
    report=validate(edited,clips)
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    for c in list(bpy.data.collections):
        if c.name!='Collection':bpy.data.collections.remove(c)
    source=make(original,'SOURCE - original LOD1');active=make(edited,'EDIT - anatomical LOD0')
    scene=bpy.context.scene;scene.frame_start=1;scene.frame_end=120
    selected=[('REST',None,0)]
    valid={n:c for n,c in clips.items() if set(c)<={b['name'] for b in edited['bones']}}
    for label,needle in [('FIST','FIST'),('GRIP','GUN_'),('POINT','POINT_')]:
        match=next(((n,c) for n,c in valid.items() if needle in n),None)
        if match:
            n,c=match;times=sorted({t for rows in c.values() for t,q in rows})
            t=max(times,key=lambda t:sum(1-abs(float(__import__('hand_animations').sample(rows,t)[0])) for rows in c.values()))
            selected.append((label,c,t))
    assert len(selected)==4
    for j,(label,clip,t) in enumerate(selected):
        frame=1+j*30;scene.frame_set(frame);scene.timeline_markers.new(label,frame=frame)
        for data,(_,rig,ob) in ((original,source),(edited,active)):
            world=bindings(data) if clip is None else pose(data,clip,t)
            apply_pose(rig,data,world,frame)
            deps=bpy.context.evaluated_depsgraph_get();evaluated=ob.evaluated_get(deps);mesh=evaluated.to_mesh()
            actual=np.array([v.co[:] for v in mesh.vertices]);expected=skin(data,world)@np.array(C).T
            error=float(np.max(abs(actual-expected)));evaluated.to_mesh_clear()
            if error>=2e-6:
                print('Skin discrepancy',folder.name,label,ob.name,flush=True)
                for i,b in enumerate(data['bones']):
                    e=float(np.max(abs(np.array(rig.pose.bones[b['name']].matrix)-np.array(C4)@world[i])))
                    rest=float(np.max(abs(np.array(rig.data.bones[b['name']].matrix_local)-np.array(C4)@bindings(data)[i])))
                    if e>1e-5:print(b['name'],'pose',e,'rest',rest,flush=True)
            assert error<2e-6,(folder.name,label,error)
    report['blender_native_skin_agrees']=True
    if args.render:
        scene.render.engine='BLENDER_WORKBENCH';scene.render.resolution_x=1200;scene.render.resolution_y=720;scene.render.resolution_percentage=100
        sh=scene.display.shading;sh.light='STUDIO';sh.studio_light='paint.sl';sh.color_type='SINGLE';sh.single_color=(.58,.48,.38)
        sh.show_cavity=True;sh.cavity_type='BOTH';sh.show_shadows=True
        bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.clip_start=.001
        direction=Vector((1,-.25,.16));cam.location=direction;cam.rotation_euler=(-direction).to_track_quat('-Z','Y').to_euler()
        right=cam.rotation_euler.to_quaternion()@Vector((1,0,0));up=cam.rotation_euler.to_quaternion()@Vector((0,1,0))
        for j,(label,_,_) in enumerate(selected):
            scene.frame_set(1+j*30)
            source[1].location=right*(-.105);active[1].location=right*.105
            bpy.context.view_layer.update();allp=[]
            for col,rig,ob in (source,active):
                ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();allp.extend(ob.matrix_world@v.co for v in me.vertices);ev.to_mesh_clear()
            center=Vector([(min(p[i] for p in allp)+max(p[i] for p in allp))*.5 for i in range(3)]);cam.location=center+direction
            cam.data.ortho_scale=max(max(p.dot(right) for p in allp)-min(p.dot(right) for p in allp),
                (max(p.dot(up) for p in allp)-min(p.dot(up) for p in allp))*1200/720)*1.15
            scene.render.filepath=str(folder/('compare_'+label.lower()+'.png'));bpy.ops.render.render(write_still=True)
            if label=='REST':
                sh.color_type='TEXTURE';scene.render.filepath=str(folder/'compare_texture.png');bpy.ops.render.render(write_still=True);sh.color_type='SINGLE'
        source[1].location=(0,0,0);active[1].location=(0,0,0)
    source[0].hide_viewport=True;source[0].hide_render=True
    scene.frame_set(1);bpy.context.view_layer.objects.active=active[2]
    for ob in bpy.context.selected_objects:ob.select_set(False)
    active[2].select_set(True)
    for area in bpy.context.screen.areas:
        if area.type=='VIEW_3D':area.spaces.active.region_3d.view_distance=.35;area.spaces.active.region_3d.view_location=(0,0,.07)
    txt=bpy.data.texts.new('README - hand authoring');txt.write(json.dumps(dict(source=original['source'],source_sha256=original['sha256'],
        anatomy=edited['authoring'],validation=report,note='EDIT is the new LOD0. SOURCE is the untouched original, hidden in viewport/render. Native skeleton, UVs and weight groups. Timeline: native rest/fist/grip/point sample poses; in-between interpolation is a review convenience, not a game clip.'),indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(folder/'hand.blend'),compress=True)
    report['edited_sha256']=hashlib.sha256((folder/'edited.json.gz').read_bytes()).hexdigest()
    report['game_launched']=False;(folder/'validation.json').write_text(json.dumps(report,indent=2));print(folder.name,report,flush=True)


for folder in sorted(OUT.iterdir()):
    if (folder/'edited.json.gz').exists() and (not args.name or folder.name in args.name):main(folder)
