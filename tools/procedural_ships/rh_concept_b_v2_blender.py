"""Offline folded-rest/unfolded-physics authoring file and contour previews."""
import hashlib
import json
from pathlib import Path
import sys
import math
import bpy
from mathutils import Matrix,Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as h
C=h.C;OUT=h.OUT.parent/'final_v2';BLEND=OUT/'rh_concept_b.blend'


def main():
    data=json.loads((OUT/'blender_data.json').read_text())
    build=json.loads((OUT/'build.json').read_text())
    mats=json.loads((h.OUT/'review_data.json').read_text())['materials']
    bpy.ops.wm.open_mainfile(filepath=str(h.OUT.parent/'hardpoint_prototype_01/rh_concept_b_prototype.blend'))
    scene=bpy.context.scene
    for o in list(bpy.data.objects):
        if o.type not in ('CAMERA','LIGHT'):bpy.data.objects.remove(o,do_unlink=True)
    for col in list(bpy.data.collections):
        if not col.objects and not col.children:bpy.data.collections.remove(col)
    def collection(name):
        col=bpy.data.collections.new(name);scene.collection.children.link(col);return col
    def relocate(o,col):
        for old in list(o.users_collection):old.objects.unlink(o)
        col.objects.link(o)
    def rotate(axis,a):return Matrix.Rotation(a,3,Vector(axis))
    objects=[];cols=[]
    for level,parts in enumerate(data['levels']):
        col=collection('LOD'+str(level)+(' - near model' if level==0 else ' - solid outer forms'));cols.append(col);mapping={}
        for name,groups in parts.items():
            o,slots=h.mesh_object(dict(groups=groups),name if level==0 else name+'_LOD'+str(level));relocate(o,col)
            for i,key in enumerate(slots):o.data.materials[i]=bpy.data.materials[mats[str(key)]['name']]
            mapping[name]=o;o['native_part']=name;o['LOD']=level
        for name,o in mapping.items():
            joint=data['joints'][name]
            if joint['parent']:o.parent=mapping[joint['parent']]
            o.location=C@Vector(joint['origin']);o.rotation_mode='QUATERNION'
            o.rotation_quaternion=(C@Matrix(joint['rotation'])@C.transposed()).to_quaternion()
            o.keyframe_insert('rotation_quaternion',frame=1)
        def keys(script,offset,reverse=False):
            for item in data['scripts'][script]:
                o=mapping[item['child']];joint=data['joints'][item['child']]
                values=item['keys'];end=values[-1][0]
                for time,angle in values:
                    frame=1+30*(offset+(end-time if reverse else time))
                    o.rotation_quaternion=(C@rotate(joint['axis'],angle)@Matrix(joint['rotation'])@C.transposed()).to_quaternion()
                    o.keyframe_insert('rotation_quaternion',frame=frame)
        keys('sc_launch extend',0)
        keys('sc_extend wing',7)
        keys('sc_extend wing',9,True)
        keys('sc_open baydoor',11)
        keys('sc_open baydoor',13,True)
        col.hide_render=level>0;col.hide_viewport=level>0;objects.append(mapping)
    hpcol=collection('Hardpoints - user placement and unique damage anchors');hpcol.hide_render=True
    for item in data['hardpoints']:
        o=bpy.data.objects.new(item['name']+' @ '+item['owner'],None);hpcol.objects.link(o)
        o.parent=objects[0][item['owner']];o.location=C@Vector(item['position'])
        o.rotation_euler=(C@Matrix(item['orientation'])@C.transposed()).to_euler()
        o.empty_display_type='ARROWS';o.empty_display_size=.25;o.show_name=True;o.show_in_front=True
        o['native_name']=item['name'];o['native_kind']=item['kind']
    wirecol=collection('Wireframe - static unfolded exterior contours')
    curve=bpy.data.curves.new('Native VMeshWire lines','CURVE');curve.dimensions='3D';curve.bevel_depth=.012;curve.resolution_u=1
    for a,b in json.loads((OUT/'wire_manifest.json').read_text())['lines']:
        sp=curve.splines.new('POLY');sp.points.add(1)
        for point,xyz in zip(sp.points,(a,b)):point.co=(* (C@Vector(xyz)),1)
    wireobj=bpy.data.objects.new('Unfolded VMeshWire',curve);wirecol.objects.link(wireobj)
    mat=bpy.data.materials.new('Wire cyan');mat.use_nodes=True
    out=mat.node_tree.nodes.get('Material Output');emit=mat.node_tree.nodes.new('ShaderNodeEmission')
    emit.inputs['Color'].default_value=(.18,.85,1,1);emit.inputs['Strength'].default_value=.8
    mat.node_tree.links.new(emit.outputs[0],out.inputs['Surface']);curve.materials.append(mat)
    wirecol.hide_render=True;wirecol.hide_viewport=True
    collision=collection('SUR - static unfolded hulls and shield');collision.hide_render=True
    for idx,item in enumerate(json.loads((OUT/'sur_preview.json').read_text())):
        me=bpy.data.meshes.new('SUR geometry');me.from_pydata([C@Vector(p) for p in item['points']],[],item['faces']);me.update()
        o=bpy.data.objects.new(('Shield HpMount' if item['shield'] else item['name'])+' '+str(idx),me);collision.objects.link(o)
        o.display_type='WIRE';o.hide_render=True;o.color=(.1,.6,1,1) if item['shield'] else (1,.4,.1,1)
        o['static_unfolded']=True
    collision.hide_viewport=True
    scene.render.resolution_x=1100;scene.render.resolution_y=900;scene.render.resolution_percentage=100
    scene.cycles.samples=16;camera=scene.camera;shift=Vector(build['center_shift_native'])
    def view(direction,target,scale):
        target=C@(Vector(target)+shift);camera.data.type='ORTHO';camera.data.ortho_scale=scale
        camera.location=target+(C@Vector(direction)).normalized()*40
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    def render(name,direction=(1,.65,1.15),target=(0,1.5,3.8),scale=23):
        view(direction,target,scale);scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    scene.frame_set(1);render('model_folded')
    scene.frame_set(211);render('model_unfolded')
    render('original_chin',(1,-.65,-1.2),(0,-.9,-3.75),6)
    cols[0].hide_render=True;cols[1].hide_render=False;cols[1].hide_viewport=False
    clay=bpy.data.materials.new('Solid LOD review');clay.diffuse_color=(.3,.36,.4,1)
    scene.view_layers[0].material_override=clay;render('solid_lod_unfolded')
    scene.view_layers[0].material_override=None;cols[1].hide_render=True;cols[1].hide_viewport=True
    wirecol.hide_render=False;wirecol.hide_viewport=False
    render('wire_unfolded',scale=25);render('wire_side',(1,0,0),scale=25);render('wire_top',(0,1,0),scale=25)
    wirecol.hide_render=True;wirecol.hide_viewport=True;cols[0].hide_render=False
    scene.frame_set(1);scene.frame_end=430;scene.render.fps=30
    scene.timeline_markers.clear()
    for name,frame in (('Folded rest / base',1),('Launch unfolds',151),('Unfolded',211),('Folded',271),('Unfolded again',331),('Bay open',369)):
        scene.timeline_markers.new(name,frame=frame)
    scene['CMP_sha256']=data['cmp_sha256'];scene['SUR_pose']='Static unfolded, independent of visual folding'
    scene['Wire_pose']='Static unfolded exterior contours, authored from solid LOD'
    scene['Asset_stage']='Offline v2; user hardpoints retained; no game installation'
    view((1,.65,1.15),(0,1.5,3.8),23)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                s=area.spaces.active;s.shading.type='MATERIAL';s.overlay.show_extras=False;s.overlay.show_floor=False
                s.region_3d.view_rotation=camera.rotation_euler.to_quaternion();s.region_3d.view_location=C@(Vector((0,1.5,3.8))+shift);s.region_3d.view_distance=25
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    assert bpy.context.scene.frame_current==1
    assert bpy.context.scene['CMP_sha256']==data['cmp_sha256']
    assert len(bpy.data.collections['Hardpoints - user placement and unique damage anchors'].objects)==len(data['hardpoints'])
    pose_error=0.
    for label,frame in (('rest',1),('unfolded',211)):
        bpy.context.scene.frame_set(frame)
        for name,expected in data['poses'][label].items():
            matrix=bpy.data.objects[name].matrix_world
            wanted=C@Matrix(expected['rotation'])@C.transposed()
            position=C@Vector(expected['position'])
            pose_error=max(pose_error,max(abs(matrix[i][j]-wanted[i][j]) for i in range(3) for j in range(3)),
                           (matrix.translation-position).length)
    assert pose_error<2e-5,pose_error
    bpy.context.scene.frame_set(1)
    report=dict(blend=str(BLEND),blend_sha256=hashlib.sha256(BLEND.read_bytes()).hexdigest(),reopened=True,
                cmp_sha256=data['cmp_sha256'],default_frame='folded',native_hardpoints=len(data['hardpoints']),
                max_native_pose_error=pose_error)
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2))
    print('V2 BLENDER READY',BLEND,flush=True)


if __name__=='__main__':main()
