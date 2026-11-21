"""Distance geometry for accepted RH pirate elite; never launch from repo root."""
import json
from pathlib import Path
import sys
import bpy
import bmesh
import numpy as np
import hashlib
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from blender_workspace import configure
configure('ship_design')
sys.path.insert(0,str(HERE))
import rh_concept_b_final_blender as h

OUT=HERE.parents[1]/'out/ship_design/rh_elite/rh_pir_elite/tail_rim/release'


def simplify(groups,label,ratio):
    obj,slots=h.mesh_object(dict(groups=groups),label)
    obj.data.validate(verbose=False,clean_customdata=False)
    before=sum(len(g['corners']) for g in groups)
    if ratio < 1:
        mod=obj.modifiers.new('Distance silhouette','DECIMATE')
        mod.ratio=ratio
        mod.use_collapse_triangulate=True
    evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh=evaluated.to_mesh()
    gs=h.groups_from_mesh(mesh,slots)
    evaluated.to_mesh_clear()
    bpy.data.objects.remove(obj,do_unlink=True)
    after=sum(len(g['corners']) for g in gs)
    assert after and after <= before
    return gs,dict(part=label,before=before,after=after,ratio=ratio)


def main():
    data=json.loads((OUT/'lod_input.json').read_text())
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    levels=[];statistics=[]
    for lv,kept in enumerate(data['preserved'],1):
        report=[]
        for name,groups in data['replacements'].items():
            ratio=(.42 if lv==1 else .23) if name in ('Root','Rh_tail_lod1') else (.7 if lv==1 else .5)
            if 'upperarm' in name:ratio=1
            gs,stats=simplify(groups,name+' LOD'+str(lv),ratio)
            kept[name].extend(gs)
            report.append(stats)
        levels.append(kept)
        statistics.append(dict(level=lv,triangles=sum(len(g['corners']) for gs in kept.values() for g in gs),parts=report))
    damaged={};damage_stats={}
    for zone,gs in data['damage'].items():
        damaged[zone]=[];damage_stats[zone]=[]
        for lv,ratio in ((1,.50),(2,.24)):
            groups,stats=simplify(gs,zone+' damage LOD'+str(lv),ratio)
            damaged[zone].append(groups);damage_stats[zone].append(stats)
    (OUT/'lod_geometry.json').write_text(json.dumps(dict(levels=levels,damage=damaged),separators=(',',':')))
    (OUT/'lod_generation.json').write_text(json.dumps(dict(levels=statistics,damage=damage_stats),indent=2))
    print('LODS READY',[(x['level'],x['triangles']) for x in statistics],flush=True)


def tree(gs):
    points=np.concatenate([np.array(g['corners'])[...,:3].reshape(-1,3) for g in gs])
    return BVHTree.FromPolygons([Vector(p) for p in points],list(np.arange(len(points)).reshape(-1,3)),all_triangles=True)


def review():
    data=json.loads((OUT/'review_data.json').read_text())
    mats=json.loads((OUT/'review_materials.json').read_text())
    sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    assert data['cmp_sha256']==sha(OUT/'assets/rh_pir_elite.cmp')
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.file_preview_type='NONE'
    bpy.context.preferences.filepaths.save_version=0
    for key,e in mats.items():
        mat=bpy.data.materials.new(key);mat.use_nodes=True;mat.use_backface_culling=True
        mat['shared_material']=e['name'];mat.diffuse_color=(*e['colour'][:3],1)
        shader=mat.node_tree.nodes.get('Principled BSDF');shader.inputs['Roughness'].default_value=.76
        shader.inputs['Base Color'].default_value=(*e['colour'][:3],1)
        if e['image']:
            tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(e['image'],check_existing=True);tex.image.pack()
            mult=mat.node_tree.nodes.new('ShaderNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1
            mult.inputs[2].default_value=(*e['colour'][:3],1)
            mat.node_tree.links.new(tex.outputs['Color'],mult.inputs[1]);mat.node_tree.links.new(mult.outputs[0],shader.inputs['Base Color'])
    camera=bpy.data.objects.new('Review camera',bpy.data.cameras.new('Lens'))
    studio=bpy.data.collections.new('Studio');studio.objects.link(camera)
    camera.data.type='ORTHO';camera.data.ortho_scale=22
    target=h.C@Vector((0,0,0));camera.location=target+(h.C@Vector((-1,.65,1))).normalized()*40
    camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    for i,(pos,energy) in enumerate([((-10,13,8),2400),((10,7,-9),1600),((0,-10,2),1600)]):
        light=bpy.data.lights.new('Area '+str(i),'AREA');light.energy=energy;light.size=10
        obj=bpy.data.objects.new(light.name,light);studio.objects.link(obj);obj.location=h.C@Vector(pos)
        obj.rotation_euler=(target-obj.location).to_track_quat('-Z','Y').to_euler()
    removed={'Rh_tail_lod1','Rh_port_engine_lod1','Rh_starboard_engine_lod1',
             'Rh_port_wing_lod1','Rh_starboard_wing_lod1','Rh_port_wing_mesh','Rh_starboard_wing_mesh'}
    scenes=[];checks=[]
    for level,parts in enumerate(data['levels']):
        intact=bpy.data.scenes.new(f'{level*2+1:02} - LOD{level} intact extended')
        bpy.context.window.scene=intact
        objects={name:h.mesh_object(dict(groups=gs),name+f' LOD{level}')[0] for name,gs in parts.items()}
        damaged=bpy.data.scenes.new(f'{level*2+2:02} - LOD{level} all damage')
        bpy.context.window.scene=damaged
        for name,obj in objects.items():
            if name not in removed:damaged.collection.objects.link(obj)
        for zone,levels in data['damage'].items():h.mesh_object(dict(groups=levels[level]),zone+f' damage LOD{level}')
        surviving=[g for name,gs in parts.items() if name not in removed for g in gs]
        surviving += [g for lv in data['damage'].values() for g in lv[level]]
        bv=tree(surviving);rays=[]
        for x in (-.35,0,.35):
            for y in (.25,1.65,2.25):
                hit,normal,index,dist=bv.ray_cast(Vector((x,y,10)),Vector((0,0,-1)),2.02)
                assert hit is None,('Tail hole closed',level,x,y,list(hit))
                rays.append([x,y])
        checks.append(dict(level=level,opening_rays_clear=rays))
        for scene in (intact,damaged):
            scene.collection.children.link(studio);scene.camera=camera
            scene.world=bpy.data.worlds.new(scene.name+' world');scene.world.color=(.3,.3,.3)
            scene.render.engine='CYCLES';scene.cycles.samples=16
            scene['CMP_sha256']=data['cmp_sha256'];scene['Stage']='Offline release review; saved from exported CMP/3DB'
            scenes.append(scene)
    bpy.context.window.scene=scenes[0]
    hpcol=bpy.data.collections.new('User hardpoints - preserved');scenes[0].collection.children.link(hpcol)
    for hp in data['hardpoints'].values():
        obj=bpy.data.objects.new(hp['name'],None);hpcol.objects.link(obj)
        obj.location=h.C@Vector(hp['position']);obj.rotation_euler=(h.C@Matrix(hp['orientation'])@h.C.transposed()).to_euler()
        obj.empty_display_type='ARROWS';obj.empty_display_size=.15
    hpcol.hide_viewport=True;hpcol.hide_render=True
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL';space.overlay.show_extras=False;space.overlay.show_floor=False
                space.region_3d.view_rotation=camera.rotation_euler.to_quaternion();space.region_3d.view_location=target
                space.region_3d.view_distance=24;space.region_3d.view_perspective='ORTHO'
    initial=bpy.data.scenes.get('Scene')
    if initial and not len(initial.objects):bpy.data.scenes.remove(initial)
    blend=OUT/'rh_pir_elite_release.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.wm.open_mainfile(filepath=str(blend))
    assert len(bpy.data.scenes)==6 and len(bpy.data.collections['User hardpoints - preserved'].objects)==79
    assert all(s['CMP_sha256']==data['cmp_sha256'] for s in bpy.data.scenes)
    assert all(im.packed_file for im in bpy.data.images if im.source=='FILE')
    (OUT/'blender_check.json').write_text(json.dumps(dict(cmp_sha256=data['cmp_sha256'],blend_sha256=sha(blend),
        reopened=True,scenes=list(bpy.data.scenes.keys()),hardpoints=79,tail_opening_all_lods=checks),indent=2)+'\n')
    print('REOPENED release Blender; tail opening clear in all 3 exported LODs',flush=True)


if __name__=='__main__':review() if '--review' in sys.argv else main()
