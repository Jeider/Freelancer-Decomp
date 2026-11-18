"""Matched Blender comparisons and an editable rigged offline LOD prototype."""
import hashlib
import json
import sys
import math
from pathlib import Path
import bpy
from mathutils import Vector,Matrix
sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as h
C=h.C;BASE=h.OUT.parent/'final_v2';OUT=BASE/'lod_refinement'


def main():
    data=json.loads((OUT/'blender_data.json').read_text())
    if '--check-only' in sys.argv:
        check(data);return
    mats=json.loads((h.OUT/'review_data.json').read_text())['materials']
    atlas=json.loads((OUT/'atlas.json').read_text())
    bpy.ops.wm.open_mainfile(filepath=str(BASE/'rh_concept_b.blend'))
    scene=bpy.context.scene;scene.frame_set(211);scene.cycles.samples=16
    scene.render.resolution_x=960;scene.render.resolution_y=640;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB'
    scene.render.film_transparent=False
    cols=[next(c for c in bpy.data.collections if c.name.startswith('LOD'+str(i)+' -')) for i in range(3)]
    def show(level):
        for i,c in enumerate(cols):c.hide_render=i!=level;c.hide_viewport=i!=level
    camera=scene.camera;target=C@Vector((0,.3420197108,-.0880785727))
    def render(label,direction):
        camera.data.type='ORTHO';camera.data.ortho_scale=26 if label.endswith('_top') else 19.5
        camera.location=target+(C@Vector(direction)).normalized()*40
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
        if label.endswith('_top'):
            camera.rotation_euler=(camera.rotation_euler.to_matrix()@Matrix.Rotation(math.pi/2,3,'Z')).to_euler()
        scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
    views={'side':(1,0,0),'iso':(1,.65,-1.15),'top':(0,1,.0001)}
    if '--top-only' in sys.argv:views={'top':views['top']}
    for level in range(3):
        show(level)
        for view,direction in views.items():
            label=('near' if level==0 else 'before_lod'+str(level))+'_'+view
            if view=='top' or not (OUT/(label+'.png')).exists():render(label,direction)
    material=bpy.data.materials.new(atlas['material']);material.use_nodes=True;material.use_backface_culling=True
    bs=material.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.88
    bs.inputs['Specular IOR Level'].default_value=.2
    tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(OUT/'rh_b_projection_lod.png'),check_existing=True);tex.image.pack()
    material.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    for level in (1,2):
        for name,groups in data['levels'][level].items():
            o=bpy.data.objects[name+'_LOD'+str(level)]
            work,slots=h.mesh_object(dict(groups=groups),'PhotoLOD temporary')
            for i,key in enumerate(slots):
                work.data.materials[i]=material if key==atlas['material_crc'] else bpy.data.materials[mats[str(key)]['name']]
            o.data=work.data;bpy.data.objects.remove(work,do_unlink=True)
        cols[level].name='LOD'+str(level)+' - baked projections'
        show(level)
        for view,direction in views.items():render('after_lod'+str(level)+'_'+view,direction)
    show(0);scene.frame_set(1)
    camera.data.ortho_scale=19.5
    camera.location=target+(C@Vector((1,.65,-1.15))).normalized()*40
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene['CMP_sha256']=data['cmp_sha256'];scene['Asset_stage']='Offline projection LOD prototype; no game installation'
    scene['LOD_source']='60 orthographic Blender photographs of this exact near model; separate external MAT'
    blend=OUT/'rh_concept_b.blend';bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    check(data)


def check(data):
    blend=OUT/'rh_concept_b.blend';bpy.ops.wm.open_mainfile(filepath=str(blend))
    cols=[next(c for c in bpy.data.collections if c.name.startswith('LOD'+str(i)+' -')) for i in range(3)]
    assert bpy.context.scene['CMP_sha256']==data['cmp_sha256']
    assert bpy.context.scene.frame_current==1
    assert len(bpy.data.collections['Hardpoints - user placement and unique damage anchors'].objects)==79
    error=0
    for c in cols:c.hide_viewport=False
    bpy.context.view_layer.update()
    for pose,frame in (('rest',1),('unfolded',211)):
        bpy.context.scene.frame_set(frame+1)
        bpy.context.scene.frame_set(frame)
        for level in range(3):
            for name,expected in data['poses'][pose].items():
                o=bpy.data.objects[name if level==0 else name+'_LOD'+str(level)]
                r=C@Matrix(expected['rotation'])@C.transposed();p=C@Vector(expected['position'])
                part_error=max((o.matrix_world.translation-p).length,max(abs(o.matrix_world[i][j]-r[i][j]) for i in range(3) for j in range(3)))
                if part_error>2e-5:print('POSE ERROR',pose,level,name,part_error,flush=True)
                error=max(error,part_error)
    assert error<2e-5,error
    bpy.context.scene.frame_set(1)
    for i,c in enumerate(cols):c.hide_viewport=i!=0
    report=dict(blend_sha256=hashlib.sha256(blend.read_bytes()).hexdigest(),cmp_sha256=data['cmp_sha256'],
        reopened=True,hardpoints=79,max_pose_error=error,texture_packed=True,default_frame=1)
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2))
    print('PROJECTION REVIEW READY',report,flush=True)


if __name__=='__main__':main()
