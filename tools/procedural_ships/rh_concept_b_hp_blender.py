"""Editable Blender companion and culled offline previews for HP handoff."""
import hashlib
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector,Matrix

sys.path.insert(0,str(Path(__file__).resolve().parent))
import rh_concept_b_final_blender as h
C=h.C
OUT=h.OUT.parent/'hardpoint_prototype_01'
BLEND=OUT/'rh_concept_b_prototype.blend'


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    engines_only='--engines-only' in sys.argv
    report=json.loads((OUT/'prototype.json').read_text(encoding='utf8'))
    if BLEND.exists():
        previous=json.loads((OUT/'blender_check.json').read_text())
        assert digest(BLEND)==previous['blend_sha256'],'User-modified Blender file; preserve manual edits'
    bpy.ops.wm.open_mainfile(filepath=report['source_blend'])
    scene=bpy.context.scene;scene.frame_set(1)
    payload=json.loads((OUT/'geometry.json').read_text())
    mats=json.loads((h.OUT/'review_data.json').read_text())['materials']
    for groups in payload.values():
        for group in groups:
            info=mats[str(group['material'])]
            if bpy.data.materials.get(info['name']):continue
            assert info['texture'] is None,'Missing textured material in the source Blender file'
            mat=bpy.data.materials.new(info['name']);mat.use_nodes=True
            rgba=tuple(info['colour'][:3])+(1,)
            mat.diffuse_color=rgba
            shader=mat.node_tree.nodes.get('Principled BSDF')
            shader.inputs['Base Color'].default_value=rgba
            shader.inputs['Roughness'].default_value=.85
    for col in list(bpy.data.collections):
        if col.name.startswith(('LOD1 -','LOD2 -','Damage caps','Debris caps')):
            for o in list(col.objects):bpy.data.objects.remove(o,do_unlink=True)
            bpy.data.collections.remove(col)
    hpcol_name='Hardpoints - native local transforms'
    hpcol=bpy.data.collections[hpcol_name]
    if 'hardpoint_nodes' in report:
        # The current CMP is authoritative after the user's manual HP edits.
        # Keep duplicate damage-anchor names distinct by their component owner.
        for o in list(hpcol.objects):bpy.data.objects.remove(o,do_unlink=True)
        for item in report['hardpoint_nodes']:
            o=bpy.data.objects.new(item['name']+' @ '+item['owner'],None);hpcol.objects.link(o)
            o.parent=bpy.data.objects[item['owner']]
            o.location=C@Vector(item['position'])
            o.rotation_euler=(C@Matrix(item['orientation'])@C.transposed()).to_euler()
            o['native_name']=item['name'];o['native_kind']=item['kind']
            o.empty_display_type='ARROWS';o.empty_display_size=.30;o.show_name=True
    hpcol.hide_viewport=False;hpcol.hide_render=True
    for o in hpcol.objects:o.hide_set(False)
    bpy.context.view_layer.update()
    hp_before={o.name:(tuple(o.matrix_world),o.parent.name if o.parent else None) for o in hpcol.objects}
    for mat in bpy.data.materials:
        mat.use_backface_culling=True
        if not mat.use_nodes:continue
        for n in mat.node_tree.nodes:
            if n.name.startswith('Texture blend:'):n.inputs[0].default_value=1
        out=next((n for n in mat.node_tree.nodes if n.type=='OUTPUT_MATERIAL' and n.is_active_output),None)
        if not out or not out.inputs['Surface'].links:continue
        # Cycles ignores viewport's culling flag; explicitly discard back faces.
        source=out.inputs['Surface'].links[0].from_socket
        mix=mat.node_tree.nodes.new('ShaderNodeMixShader');mix.name='Prototype native backface culling'
        geo=mat.node_tree.nodes.new('ShaderNodeNewGeometry')
        transparent=mat.node_tree.nodes.new('ShaderNodeBsdfTransparent')
        mat.node_tree.links.new(geo.outputs['Backfacing'],mix.inputs[0])
        mat.node_tree.links.new(source,mix.inputs[1])
        mat.node_tree.links.new(transparent.outputs[0],mix.inputs[2])
        mat.node_tree.links.new(mix.outputs[0],out.inputs['Surface'])
    camera=scene.camera;camera.data.clip_start=.005
    scene.render.resolution_x=1000;scene.render.resolution_y=800
    scene.render.resolution_percentage=100;scene.cycles.samples=16
    scene.render.image_settings.file_format='PNG'
    shift=Vector(report['center_shift_native'])
    def view(direction,target,scale,perspective=False):
        target=C@(Vector(target)+shift)
        camera.data.type='PERSP' if perspective else 'ORTHO'
        camera.data.ortho_scale=scale;camera.data.lens=22 if perspective else 50
        camera.location=target+C@Vector(direction)*(1 if perspective else 5)
        camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    def render(name,direction,target,scale,perspective=False):
        view(direction,target,scale,perspective)
        scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
    # Same cameras before/after; comparisons expose back faces rather than hiding them.
    cabin_target=(0,.591818-.35,2.70-4.82)
    def engine_view(name):
        saved={name:bpy.data.objects[name].hide_render for name in payload}
        for objname in payload:bpy.data.objects[objname].hide_render='_engine_' not in objname.lower()
        render(name,(1,.65,1.15),(0,-1.55,8.7),7.8)
        for objname,hidden in saved.items():bpy.data.objects[objname].hide_render=hidden
    if engines_only:
        engine_view('engines_before')
    else:
        render('cabin_before',(.06,0,-1.65),cabin_target,3,True)
        render('frame_before',(0,.15,-1.5),(0,5.4,6.4),4.1)
    for name,groups in payload.items():
        obj=bpy.data.objects[name]
        generated,slots=h.mesh_object(dict(groups=groups),name+' prototype data')
        for i,key in enumerate(slots):
            matname=mats[str(key)]['name']
            mat=bpy.data.materials.get(matname)
            assert mat is not None,matname
            generated.data.materials[i]=mat
        obj.data=generated.data
        bpy.data.objects.remove(generated,do_unlink=True)
        obj.hide_render=False;obj.hide_set(False)
    bpy.context.view_layer.update()
    assert all((tuple(o.matrix_world),o.parent.name if o.parent else None)==hp_before[o.name] for o in hpcol.objects)
    # Validate the coordinate system using every uniquely named native hardpoint.
    errors=[]
    for o in hpcol.objects:
        name=o.get('native_name','').lower()
        if name not in report['hardpoints'] or name=='dpbreak':continue
        hp=report['hardpoints'][name]
        error=(C.transposed()@o.matrix_world.translation-Vector(hp['position'])).length
        assert error<.00005,(name,error)
        errors.append(error)
    if not engines_only:
        render('cabin_after',(.06,0,-1.65),cabin_target,3,True)
        render('frame_after',(0,.15,-1.5),(0,5.4,6.4),4.1)
    engine_view('engines_after')
    render('tail_detail',(1,.35,1.3),(0,2.4,11.7),8)
    render('prototype_overview',(1,.65,1.15),(0,1.5,3.8),23)
    scene['Asset_stage']='LOD0 prototype for user HP editing; SUR and destruction update deferred'
    scene['CMP_sha256']=report['cmp_sha256']
    for key in ('LOD_triangle_counts',):
        if key in scene:del scene[key]
    # Keep editable markers easily accessible but visually uncluttered on opening.
    hpcol.hide_viewport=False
    for o in hpcol.objects:
        o.empty_display_type='ARROWS';o.empty_display_size=.30;o.show_in_front=True
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL'
                space.overlay.show_extras=False;space.overlay.show_floor=False
                space.region_3d.view_perspective='PERSP'
                space.region_3d.view_rotation=camera.rotation_euler.to_quaternion()
                space.region_3d.view_location=C@(Vector((0,1.5,3.8))+shift)
                space.region_3d.view_distance=25
    bpy.ops.object.select_all(action='DESELECT')
    scene.render.filepath=str(OUT/'prototype_overview.png')
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    assert bpy.context.scene['CMP_sha256']==report['cmp_sha256']
    assert all(o.parent is not None for o in bpy.data.collections[hpcol_name].objects)
    checks=dict(blend=str(BLEND),blend_sha256=digest(BLEND),reopened=True,
                hardpoints_preserved=True,max_hp_position_error=max(errors),hp_count=len(hp_before),
                triangles=report['triangles'],backface_culling_preview=True)
    (OUT/'blender_check.json').write_text(json.dumps(checks,indent=2))
    assert all(digest(p)==sha for p,sha in report['sources'].items())
    print('PROTOTYPE READY',BLEND,checks,flush=True)


if __name__=='__main__':main()
