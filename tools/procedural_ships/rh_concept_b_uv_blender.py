"""Edit native UV corners in the finished Blender model and show matched views."""
import hashlib
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as h
OUT=h.OUT.parent/'uv_refinement_01'
C=h.C


def main():
    data=json.loads((OUT/'uv_changes.json').read_text(encoding='utf8'))
    assert hashlib.sha256(Path(data['base_blend']).read_bytes()).hexdigest()==data['base_blend_sha256']
    bpy.ops.wm.open_mainfile(filepath=data['base_blend'])
    scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
    root=bpy.data.objects['Root'];uv=root.data.uv_layers.active
    # Exported LOD0 has one loop per native corner. Match by full triangle positions
    # so a different VMesh material-group order cannot silently target other faces.
    def key(coords):return tuple(sorted(tuple(round(float(v),5) for v in p) for p in coords))
    lookup={}
    for poly in root.data.polygons:
        coords=[C.transposed()@root.data.vertices[root.data.loops[i].vertex_index].co for i in poly.loop_indices]
        lookup.setdefault(key(coords),[]).append(poly)
    resolved=[]
    for e in data['edits']:
        candidates=lookup[key(e['positions'])]
        assert len(candidates)==1
        poly=candidates[0];pairs=[]
        for loop in poly.loop_indices:
            p=C.transposed()@root.data.vertices[root.data.loops[loop].vertex_index].co
            index=min(range(3),key=lambda j:(p-Vector(e['positions'][j])).length)
            assert (p-Vector(e['positions'][index])).length<1e-4
            current=uv.data[loop].uv
            assert (current-Vector((e['before'][index][0],1-e['before'][index][1]))).length<1e-5
            pairs.append((loop,Vector((e['after'][index][0],1-e['after'][index][1]))))
        resolved.extend(pairs)
    scene.render.resolution_x=1400;scene.render.resolution_y=700;scene.cycles.samples=24
    camera=scene.camera;shift=Vector(data['center_shift_native'])
    # Neutral inspection light below the hull; identical for before/after.
    light=bpy.data.lights.new('UV underside inspection','AREA');light.energy=900;light.size=7
    lamp=bpy.data.objects.new('UV underside inspection',light);scene.collection.objects.link(lamp)
    lamp.location=C@(Vector((7,-7,2))+shift)
    lamp.rotation_euler=((C@(Vector((0,-.5,3))+shift))-lamp.location).to_track_quat('-Z','Y').to_euler()
    views=[('side_strip',(1,0,0),(2.05,-.37,3.20),7.5),
           ('bottom_corner',(1,-.75,-.65),(1.25,-.65,2.8),8.5),
           ('underside',(.20,-1,-.12),(0,-1.15,2.8),9.0)]
    def render(name,direction,target,scale):
        strip='side_strip' in name
        scene.render.resolution_y=330 if strip else 700 if name!='overview' else 1000
        dest=C@(Vector(target)+shift);camera.data.type='ORTHO';camera.data.ortho_scale=scale
        camera.location=dest+(C@Vector(direction)).normalized()*35
        # Close inspection clips foreground wing hardware, not the sill itself.
        # The ordinary full-ship views use the normal near plane.
        camera.data.clip_start=34.93 if strip else .1
        camera.rotation_euler=(dest-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    for name,direction,target,scale in views:render('before_'+name,direction,target,scale)
    for loop,value in resolved:uv.data[loop].uv=value
    root.data.update();bpy.context.view_layer.update()
    for name,direction,target,scale in views:render('after_'+name,direction,target,scale)
    lamp.hide_render=True
    scene.render.resolution_y=1000
    render('overview',(1,.7,-1.1),(0,1.5,3.8),23)
    scene['Asset_stage']='UV REVIEW: LOD0 sill/frame/bottom revised; installation suspended'
    scene['UV_review_base_cmp_sha256']=data['base_cmp_sha256']
    scene['UV_review_changed_triangles']=len(data['edits'])
    if 'CMP_sha256' in scene:del scene['CMP_sha256']
    # Old atlases remain hidden until this UV layout is approved and transferred.
    for lv in (1,2):
        col=bpy.data.collections[f'LOD{lv} - distance model']
        col.name+= ' (previous UV - pending transfer)';col.hide_render=True;col.hide_viewport=True
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_extras=False
                space.region_3d.view_location=C@(Vector((0,1.5,3.8))+shift);space.region_3d.view_distance=25
                space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'rh_concept_b_uv_review.blend'))
    print('READY UV REVIEW',len(data['edits']),'triangles',flush=True)


def check_saved():
    data=json.loads((OUT/'uv_changes.json').read_text(encoding='utf8'))
    def snapshot(path):
        bpy.ops.wm.open_mainfile(filepath=str(path));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
        result={}
        for obj in bpy.data.objects:
            if obj.type!='MESH':continue
            coords=[tuple(v.co) for v in obj.data.vertices]
            faces=[(tuple(p.vertices),p.material_index) for p in obj.data.polygons]
            result[obj.name]=dict(geometry=hashlib.sha256(repr((coords,faces)).encode()).hexdigest(),
                                 uv=[tuple(v.uv) for v in obj.data.uv_layers.active.data],
                                 materials=[m.name for m in obj.data.materials],
                                 transform=[list(row) for row in obj.matrix_world])
        return result
    before=snapshot(data['base_blend']);after=snapshot(OUT/'rh_concept_b_uv_review.blend')
    assert before.keys()==after.keys()
    changed=0
    for name,a in before.items():
        b=after[name]
        assert a['geometry']==b['geometry'] and a['materials']==b['materials'] and a['transform']==b['transform'],name
        n=sum(x!=y for x,y in zip(a['uv'],b['uv']))
        if name=='Root':changed=n
        else:assert n==0,name
    assert changed==len(data['edits'])*3,(changed,len(data['edits']))
    assert hashlib.sha256(Path(data['base_cmp']).read_bytes()).hexdigest()==data['base_cmp_sha256']
    report=dict(reopened=True,geometry_materials_transforms_unchanged=True,uv_corners_changed=changed,
                triangles_changed=len(data['edits']),base_cmp_unchanged=True,
                blend_sha256=hashlib.sha256((OUT/'rh_concept_b_uv_review.blend').read_bytes()).hexdigest())
    (OUT/'checks.json').write_text(json.dumps(report,indent=2))
    print('PASS UV BLEND',report,flush=True)


if __name__=='__main__':
    if '--check-only' in sys.argv:check_saved()
    else:main()
