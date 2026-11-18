"""Build and inspect an isolated Blender prototype; never export/install game assets."""
import hashlib
import json
from pathlib import Path
import sys
import bpy
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as h
C=h.C
OUT=h.OUT.parent/'tail_prototype_01'
BLEND=OUT/'rh_concept_b_tail_prototype.blend'


def main():
    data=json.loads((OUT/'prototype_data.json').read_text(encoding='utf8'))
    materials=json.loads((h.OUT/'review_data.json').read_text())['materials']
    bpy.ops.wm.open_mainfile(filepath=str(h.OUT/'rh_concept_b_rigged.blend'))
    scene=bpy.context.scene;scene.frame_set(1)
    bpy.context.view_layer.update()
    source_names=[e['name'] for e in json.loads((h.OUT/'blender_scene.json').read_text())['objects']]
    main_parts=[bpy.data.objects[n] for n in source_names]
    def mesh_hash(o):return hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
    original_hashes={o.name:mesh_hash(o) for o in main_parts}
    # Old LODs are not representations of this prototype. Keep only the near rig.
    for col in list(bpy.data.collections):
        if col.name.startswith(('LOD1 -','LOD2 -')):
            for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
            bpy.data.collections.remove(col)
    for o in main_parts:o.hide_render=False;o.hide_set(False)
    damagecol=bpy.data.collections['Damage caps - enable with detached part hidden']
    damagecol.hide_render=True;damagecol.hide_viewport=True
    for o in damagecol.objects:o.hide_render=True
    tail=bpy.data.objects['Rh_tail_lod1']
    newcol=bpy.data.collections.new('Prototype - middle tail housing and four pylons');scene.collection.children.link(newcol)
    def add(entry):
        o,slots=h.mesh_object(entry,entry['name'])
        for col in list(o.users_collection):col.objects.unlink(o)
        newcol.objects.link(o)
        for i,key in enumerate(slots):o.data.materials[i]=bpy.data.materials[materials[str(key)]['name']]
        o.parent=tail;o.matrix_parent_inverse=tail.matrix_world.inverted()
        o['source']='Original rh_pir_elite LOD0, native UV preserved'
        o['damage_owner']='Rh_tail_lod1: middle upright only'
        return o
    additions=[add(e) for e in data['objects']]
    hpcol=bpy.data.collections['Hardpoints - native local transforms']
    for hp in data['hardpoints']:
        o=next(o for o in hpcol.objects if o.get('native_name')==hp['name'])
        o.parent=tail;o.matrix_parent_inverse=tail.matrix_world.inverted()
        o.location=C@Vector(hp['position'])
        o.rotation_euler=(C@Matrix(hp['orientation'])@C.transposed()).to_euler()
        o.name=hp['name']+' @ Rh_tail_lod1'
        o['prototype_relocated']=True
    anchor=bpy.data.objects.new('Ship origin - recentered as original',None);scene.collection.objects.link(anchor)
    anchor.empty_display_type='PLAIN_AXES';anchor.empty_display_size=1.3
    for o in [*main_parts,*list(damagecol.objects)]:
        if o.parent is None:o.parent=anchor
    shift=C@Vector(data['center_shift_native']);anchor.location=shift
    scene.frame_set(1);bpy.context.view_layer.update()
    assert all(original_hashes[o.name]==mesh_hash(o) for o in main_parts),'Existing geometry must remain unchanged'
    for mat in bpy.data.materials:
        if not mat.use_nodes:continue
        for n in mat.node_tree.nodes:
            if n.name.startswith('Texture blend:'):n.inputs[0].default_value=1
    scene['Asset_stage']='BLENDER PROTOTYPE: middle tail housing only; native export pending visual review'
    scene['Prototype_base_cmp_sha256']=data['base_cmp_sha256']
    scene['Prototype_original_cmp_sha256']=data['original_sha256']
    scene['Prototype_added_triangles']=data['added_triangles']
    scene['Prototype_center_translation_native']=data['center_shift_native']
    scene['Prototype_unchanged_mesh_hashes']=json.dumps(original_hashes)
    if 'CMP_sha256' in scene:del scene['CMP_sha256']
    scene.render.resolution_x=1200;scene.render.resolution_y=900
    scene.cycles.samples=20;scene.render.resolution_percentage=100
    camera=scene.camera
    def view(direction,target,scale):
        dest=C@Vector(target)+shift;camera.data.type='ORTHO';camera.data.ortho_scale=scale
        camera.location=dest+(C@Vector(direction)).normalized()*45
        camera.rotation_euler=(dest-camera.location).to_track_quat('-Z','Y').to_euler()
    def render(name,direction,target,scale):
        view(direction,target,scale);scene.render.filepath=str(OUT/(name+'.png'))
        bpy.ops.render.render(write_still=True)
    render('prototype_side',(1,0,0),(0,1.6,3.8),22)
    render('prototype_rear',(0,.05,1),(0,2.5,11.8),8.7)
    render('prototype_tail_detail',(1,.5,1.3),(0,2.4,11.5),8.0)
    render('prototype_overview',(1,.65,1.15),(0,1.5,3.8),23)
    # The added shell/pylons are part of the removable middle upright.
    for o in [tail,*additions]:o.hide_render=True
    damagecol.hide_render=False;damagecol.hide_viewport=False
    cap=bpy.data.objects['Damage_tail'];cap.hide_render=False
    render('prototype_tail_destroyed',(1,.5,1.3),(0,2.4,10.8),9)
    for o in [tail,*additions]:o.hide_render=False
    cap.hide_render=True;damagecol.hide_render=True;damagecol.hide_viewport=True
    view((1,.65,1.15),(0,1.5,3.8),23)
    # Open the saved file already framed, with textures and without old LOD overlays.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL'
                space.overlay.show_extras=False;space.overlay.show_floor=False
                space.region_3d.view_perspective='PERSP'
                space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
                space.region_3d.view_location=C@Vector((0,1.5,3.8))+shift
                space.region_3d.view_distance=25
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active=additions[0];additions[0].select_set(True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report=dict(blend=str(BLEND),added_triangles=data['added_triangles'],native_sources_unchanged=True,
                existing_meshes_unchanged=original_hashes,center_translation_native=data['center_shift_native'],
                relocated_hardpoints=[p['name'] for p in data['hardpoints']],
                damage='Middle upright and its new housing/pylons detach together. Upper/lower frame and drum survive.')
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('READY BLENDER TAIL PROTOTYPE',BLEND,flush=True)


def check_saved():
    data=json.loads((OUT/'prototype_data.json').read_text(encoding='utf8'))
    report=json.loads((OUT/'blender_check.json').read_text(encoding='utf8'))
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
    for name,expected in report['existing_meshes_unchanged'].items():
        o=bpy.data.objects[name]
        got=hashlib.sha256(repr(([tuple(v.co) for v in o.data.vertices],[tuple(p.vertices) for p in o.data.polygons])).encode()).hexdigest()
        assert got==expected,name
    shift=C@Vector(data['center_shift_native'])
    newcol=bpy.data.collections['Prototype - middle tail housing and four pylons']
    assert len(newcol.objects)==5 and not newcol.hide_viewport and not newcol.hide_render
    # Hidden collections are excluded from Blender's evaluated dependency graph.
    bpy.data.collections['Hardpoints - native local transforms'].hide_viewport=False
    bpy.context.view_layer.update()
    distances=[]
    for hp in data['hardpoints']:
        o=next(o for o in bpy.data.objects if o.get('native_name')==hp['name'])
        assert o.parent.name=='Rh_tail_lod1'
        assert (o.matrix_world.translation-(C@Vector(hp['position'])+shift)).length<1e-5,(hp['name'],list(o.matrix_world.translation),list(C@Vector(hp['position'])+shift))
        best=1e9
        for pylon in newcol.objects:
            if not pylon.name.endswith('pylon'):continue
            tree=BVHTree.FromPolygons([pylon.matrix_world@v.co for v in pylon.data.vertices],
                                     [tuple(p.vertices) for p in pylon.data.polygons],all_triangles=True)
            best=min(best,tree.find_nearest(o.matrix_world.translation)[3])
        assert best<.025,(hp['name'],best)
        distances.append(dict(name=hp['name'],surface_distance=best))
    for path,key in ((data['base_cmp'],'base_cmp_sha256'),(data['original'],'original_sha256'),(data['shared_mat'],'shared_mat_sha256')):
        assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==data[key],path
    objects=[bpy.data.objects[n] for n in report['existing_meshes_unchanged']]+list(newcol.objects)
    coords=[C.transposed()@(o.matrix_world@v.co) for o in objects for v in o.data.vertices]
    center=[(min(p[i] for p in coords)+max(p[i] for p in coords))*.5 for i in range(3)]
    assert max(abs(center[i]-data['original_bounds_center'][i]) for i in range(3))<.001
    for col in bpy.data.collections:
        if col.name.startswith(('Damage caps','Debris caps')):assert col.hide_render and col.hide_viewport
    report.update(reopened_blend_validated=True,hardpoint_surface_distances=distances,
                  bounds_center_native=center,blend_sha256=hashlib.sha256(BLEND.read_bytes()).hexdigest())
    (OUT/'blender_check.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('PASS REOPENED: meshes unchanged, 4 mounts on pylons, sources unchanged, recentered hierarchy',flush=True)


if __name__=='__main__':
    if '--check-only' in sys.argv:check_saved()
    else:main()
