"""Reopen both authoring steps and validate the intended local changes."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step02 import TOP,OUT,PARENT,HEAD_DROP,sha,render
configure('character_rounding')

def mesh(ob):
    return {'points':np.array([v.co[:] for v in ob.data.vertices]),
            'faces':[list(p.vertices) for p in ob.data.polygons],
            'weights':[[(g.group,g.weight) for g in v.groups] for v in ob.data.vertices],
            'uv':np.array([v.uv[:] for v in ob.data.uv_layers[0].data])}

def main():
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding')
    previous={ob.name:mesh(ob) for ob in bpy.data.objects if ob.type=='MESH'}
    rig=bpy.data.objects['RIG — native Rheinland']
    bones={b.name:{'matrix':np.array(b.matrix_local),'bind':list(b['native_inverse_bind']),
                   'parent':b.parent.name if b.parent else None} for b in rig.data.bones}
    path=OUT/'hassler_native_upper.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
    report=json.loads((OUT/'report.json').read_text(encoding='utf8'));assert sha(PARENT)==report['parent_sha256']
    rig=bpy.data.objects['RIG — native Rheinland'];assert len(rig.data.bones)==28
    for b in rig.data.bones:
        old=bones[b.name];assert (b.parent.name if b.parent else None)==old['parent']
        expected=old['matrix'].copy()
        if b.name in ('Body_Head','Head_End'):expected[2,3]-=HEAD_DROP
        assert np.max(abs(np.array(b.matrix_local)-expected))<2e-6,(b.name,np.array(b.matrix_local)-expected)
        if b.name not in ('Body_Head','Head_End'):assert list(b['native_inverse_bind'])==old['bind']
    fixed=['00 Native elite — original torso and sleeves','Left glove — native unchanged','Right glove — native unchanged',
           '02 Epaulettes — Reichman source geometry']
    for name in fixed:
        now=mesh(bpy.data.objects[name]);old=previous[name]
        for key in ('points','uv'):assert np.array_equal(now[key],old[key]),(name,key)
        for key in ('weights','faces'):assert now[key]==old[key],(name,key)
    hname='Hassler head — native unchanged';head=mesh(bpy.data.objects[hname]);old=previous[hname]
    difference=head['points']-old['points'];assert np.max(abs(difference-np.array([0,0,-HEAD_DROP])))<1e-7
    assert head['faces']==old['faces'] and head['weights']==old['weights'] and np.array_equal(head['uv'],old['uv'])
    base=previous[fixed[0]]['points'];old_insert=previous['00 Native neck insert — recoloured black']['points']
    keys=lambda points:{tuple(np.round(p,5)) for p in points}
    seams=keys(base)&keys(old_insert);new_insert=keys(mesh(bpy.data.objects['00 Native neck insert — recoloured black'])['points'])
    assert seams<=new_insert,('Neck/torso attachment opened',seams-new_insert)
    edit=bpy.data.collections['EDIT — native costume upper study'];parts={};influences=0;degenerate_uv={}
    bpy.context.scene.frame_set(1)
    for ob in edit.objects:
        if ob.type!='MESH':continue
        for v in ob.data.vertices:
            w=[g.weight for g in v.groups if g.weight>0];influences=max(influences,len(w));assert abs(sum(w)-1)<3e-6
        ob.data.calc_loop_triangles();layer=ob.data.uv_layers.active
        count=0
        for t in ob.data.loop_triangles:
            a,b,c=[np.array(layer.data[i].uv) for i in t.loops]
            if abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))<1e-10:count+=1
        degenerate_uv[ob.name]=count
        ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
        assert all(np.isfinite(v.co).all() for v in me.vertices)
        parts[ob.name]={'vertices':len(me.vertices),'triangles':len(me.loop_triangles)};ev.to_mesh_clear()
    assert influences<=4
    assert sum(p['vertices'] for p in parts.values())<65535
    for c in ('ARCHIVE — original references disabled','REFERENCE ART — disabled'):
        assert bpy.data.collections[c].hide_render and bpy.data.collections[c].hide_viewport
    for image in bpy.data.images:
        if image.source=='FILE' and image.users and not image.packed_file:assert Path(bpy.path.abspath(image.filepath)).exists(),image.filepath
    for audit_path in (TOP/'source_audit.json',TOP/'source/dietrich/source_audit.json'):
        audit=json.loads(audit_path.read_text(encoding='utf8'))
        for entry in audit['native'].values():assert sha(Path(entry['path']))==entry['sha256']
    ep=bpy.data.objects['02 Epaulettes — Reichman source geometry'];mat=ep.data.materials[0]
    image=next(n.image for n in mat.node_tree.nodes if n.type=='TEX_IMAGE')
    assert Path(bpy.path.abspath(image.filepath)).name=='360594c6b5ce8545.png'
    # Sample the painted field at triangle interiors, not just the UV bounds.
    gold=bpy.data.materials['Hassler brocade — Dietrich native front cloth']
    im=next(n.image for n in gold.node_tree.nodes if n.type=='TEX_IMAGE');w,h=im.size
    pixels=np.empty(w*h*4,dtype=np.float32);im.pixels.foreach_get(pixels);pixels=pixels.reshape(h,w,4)
    off_field=[]
    for name in ('03 Chest gold facing','05 Left shoulder gold facing','07 Back Y facing'):
        ob=bpy.data.objects[name];layer=ob.data.uv_layers.active
        for ti,tri in enumerate(ob.data.loop_triangles):
            uv=np.array([layer.data[i].uv[:] for i in tri.loops])
            for bary in ((1/3,1/3,1/3),(.8,.1,.1),(.1,.8,.1),(.1,.1,.8)):
                u,v=np.array(bary)@uv;rgba=pixels[min(h-1,int(v*h)),min(w-1,int(u*w))]
                if rgba[2]>rgba[0]*1.05:off_field.append((name,ti))
    assert not off_field,('Blue donor uniform entered gold patch',off_field)
    result={'reopened':True,'blend_sha256':sha(path),'parent_step_01_unchanged':True,
            'body_hands_epaulette_geometry_unchanged':True,'head_shape_unchanged':True,'head_drop_m':HEAD_DROP,
            'head_pivot_and_end_shifted_m':HEAD_DROP,'other_26_bones_unchanged':True,
            'neck_attachment_positions_preserved':len(seams),'max_bone_influences':influences,
            'body_triangles_with_modifiers':sum(p['triangles'] for p in parts.values()),'parts':parts,
            'authored_uv_zero_area_triangles':degenerate_uv,'dietrich_epaulette_texture_verified':True,
            'gold_chart_blue_region_samples':len(off_field),'source_files_unchanged':True,
            'archive_hidden_in_saved_file':True,'game_installed':False,'game_animations_validated':False}
    # Transparent backfacing shader gives a real culling review in offline Cycles.
    mat=bpy.data.materials.new('Culling clay');mat.use_nodes=True;n=mat.node_tree.nodes;l=mat.node_tree.links
    bs=n.get('Principled BSDF');bs.inputs['Base Color'].default_value=(.32,.37,.40,1)
    geo=n.new('ShaderNodeNewGeometry');trans=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader')
    l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(bs.outputs[0],mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2])
    l.new(mix.outputs[0],n.get('Material Output').inputs['Surface'])
    scene=bpy.context.scene;scene.view_layers[0].material_override=mat
    render(scene,'clay_neck',(.4,1,.15),(0,0,1.55),.65)
    scene.view_layers[0].material_override=None
    assert sha(path)==result['blend_sha256']
    (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
    print(json.dumps(result,indent=2),flush=True)

if __name__=='__main__':main()
