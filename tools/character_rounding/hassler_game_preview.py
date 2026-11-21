"""Reopen decoded native geometry and DDS diffuse maps, check attachments, render."""
import sys,json,gzip
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step15 as s
from hassler_native_step13 import sha
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'game'

def main():
    if '--arm-only' in sys.argv:
        path=OUT/'rh_hassler_body.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
        import hassler_arm_study as arm
        import hassler_runtime_pose as runtime
        cols=[next(c for c in bpy.data.collections if c.name.startswith(f'GAME LOD{i} ')) for i in range(5)]
        for i,col in enumerate(cols):col.hide_render=col.hide_viewport=i!=0
        runtime.cull_materials(cols[0].objects);rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));arm.OUT=OUT;arm.render(scene,rig,'game_arm')
        clip,t=arm.clips()['crossed'];runtime.apply_blender(rig,OUT/'rig_for_preview.json',clip,t);s.OUT=OUT
        s.render(scene,'game_arm_other',(-.85,1,.12),(0,0,1.42),.96)
        validation=json.loads((OUT/'preview_validation.json').read_text(encoding='utf8'));assert sha(path)==validation['preview_blend_sha256'];validation['arm_previews']=['game_arm_'+k+'.png' for k in ('rest','crossed','hips','idle','other')];(OUT/'preview_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return
    if '--right-end-only' in sys.argv:
        path=OUT/'rh_hassler_body.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);s.OUT=OUT
        import hassler_runtime_pose as runtime
        cols=[next(c for c in bpy.data.collections if c.name.startswith(f'GAME LOD{i} ')) for i in range(5)]
        for i,col in enumerate(cols):col.hide_render=col.hide_viewport=i!=0
        runtime.cull_materials(cols[0].objects)
        s.render(scene,'game_collar_right_end',(-.65,1,.12),(.10,.09,1.58),.34)
        s.render(scene,'game_shoulders_front',(0,1,0),(0,0,1.4),1.1)
        s.render(scene,'game_shoulder_depth',(-.8,1,.65),(.18,.015,1.55),.49)
        s.render(scene,'game_shoulder_profile',(-1,.04,.35),(.19,.01,1.55),.42)
        s.render(scene,'game_shoulder_other_profile',(1,.04,.35),(-.19,.01,1.55),.42)
        for i,col in enumerate(cols):col.hide_render=col.hide_viewport=i!=4
        runtime.cull_materials(cols[4].objects)
        s.render(scene,'game_collar_right_end_lod4',(-.65,1,.12),(.10,.09,1.58),.34)
        validation=json.loads((OUT/'preview_validation.json').read_text(encoding='utf8'));assert sha(path)==validation['preview_blend_sha256'];validation['right_end_previews']=['game_collar_right_end.png','game_shoulders_front.png','game_collar_right_end_lod4.png'];(OUT/'preview_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return
    if '--lining-only' in sys.argv:
        path=OUT/'rh_hassler_body.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);s.OUT=OUT
        import hassler_runtime_pose as runtime
        cols=[next(c for c in bpy.data.collections if c.name.startswith(f'GAME LOD{i} ')) for i in range(5)]
        for i,col in enumerate(cols):col.hide_render=col.hide_viewport=i!=0
        runtime.cull_materials(cols[0].objects)
        head=next(o for o in bpy.data.objects if o.name.startswith('Hassler head '));head.hide_render=True;scene.render.film_transparent=True
        s.render(scene,'game_collar_lining',(-.45,1,.35),(0,.02,1.58),.59)
        head.hide_render=False;scene.render.film_transparent=False
        s.render(scene,'game_collar_other_side',(.6,1,.2),(0,.02,1.58),.73)
        for i,col in enumerate(cols):col.hide_render=col.hide_viewport=i!=4
        runtime.cull_materials(cols[4].objects)
        s.render(scene,'game_collar_lowest',(-.45,1,.12),(0,.02,1.58),.73)
        validation=json.loads((OUT/'preview_validation.json').read_text(encoding='utf8'));assert sha(path)==validation['preview_blend_sha256'];validation['lining_previews']=['game_collar_lining.png','game_collar_other_side.png','game_collar_lowest.png'];(OUT/'preview_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return
    if '--lowest-only' in sys.argv:
        path=OUT/'rh_hassler_body.blend';bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);s.OUT=OUT
        for i in range(5):bpy.data.collections[f'GAME LOD{i} — rh_hassler_body'].hide_render=i!=4
        s.render(scene,'game_lowest',(.5,1,.04),(0,0,.99),2.08)
        validation=json.loads((OUT/'preview_validation.json').read_text(encoding='utf8'));assert sha(path)==validation['preview_blend_sha256'];validation['lowest_lod_preview']='game_lowest.png';(OUT/'preview_validation.json').write_text(json.dumps(validation,ensure_ascii=False,indent=2)+'\n',encoding='utf8');return
    report=json.loads((OUT/'native_build.json').read_text(encoding='utf8'));assert sha(Path(report['dfm']))==report['sha256']
    bpy.ops.wm.open_mainfile(filepath=report['source_blend']);configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    rig=bpy.data.objects['RIG — native Rheinland'];source=native.load('body');head=native.load('head')
    newbind=json.loads((OUT/'export.json').read_text(encoding='utf8'))['native_inverse_bind']
    for n,b in newbind.items():assert np.array_equal(rig.data.bones[n]['native_inverse_bind'],b)
    # Verify the shared head attachment predicts the exact approved head placement.
    oldbone=next(b for b in source['bones'] if b['name']=='Body_Head');oldB=native.bindings({'bones':[oldbone]})[0]
    newB=native.bindings({'bones':[{'native_bind':newbind['Body_Head']}]})[0]
    newhp=newB@np.linalg.inv(oldB)@np.array(source['hardpoints']['hp_head']['matrix'])
    transform=native.C4@Matrix((newhp@np.linalg.inv(np.array(head['hardpoints']['hp_head']['matrix']))).tolist())
    predicted=np.array([transform@Vector(p) for p in head['points']]);actual=np.array([v.co[:] for v in bpy.data.objects['Hassler head — native unchanged'].data.vertices]);head_error=float(np.linalg.norm(predicted-actual,axis=1).max());assert head_error<2e-6
    edit=bpy.data.collections['EDIT — native costume upper study'];edit.hide_render=edit.hide_viewport=True
    names=[b['name'] for b in source['bones']];mats={m['name']:m for m in report['materials']};collections=[]
    for level in range(5):
        data=json.loads(gzip.decompress((OUT/f'decoded_mesh{level}.json.gz').read_bytes()));data['uv']=[[u,1-v] for u,v in data['uv']]
        for g in data['groups']:g['texture']=str(OUT/'decoded'/(mats[g['name']]['game_texture']+'.png'))
        col=native.collection(f'GAME LOD{level} — rh_hassler_body');collections.append(col);ob=native.native_mesh(data,f'rh_hassler_body LOD{level}',col)
        weights=np.zeros((len(data['points']),len(names)))
        for i,row in enumerate(data['skin']):
            for bone,w in row.items():weights[i,int(bone)]=w
        native.add_skin(ob,weights,names,rig)
        for slot,g in zip(ob.data.materials,data['groups']):
            settings=mats[g['name']];bs=slot.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=settings['roughness'];bs.inputs['Metallic'].default_value=settings['metallic']
            for n in slot.node_tree.nodes:
                if n.type=='TEX_IMAGE':n.image.pack()
        col.hide_render=col.hide_viewport=level!=0
    text=bpy.data.texts.new('GAME EXPORT — rh_hassler_body');text.write(json.dumps(report,ensure_ascii=False,indent=2))
    scene.frame_set(1);path=OUT/'rh_hassler_body.blend';bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');scene=bpy.context.scene;s.OUT=OUT
    import hassler_runtime_pose as runtime
    runtime.cull_materials(bpy.data.collections['GAME LOD0 — rh_hassler_body'].objects)
    s.render(scene,'game_full',(0,1,.03),(0,0,.99),2.08);s.render(scene,'game_waist',(0,1,.08),(0,.02,1.15),.59)
    s.render(scene,'game_collar',(-.45,1,.20),(0,.02,1.58),.73)
    s.render(scene,'game_collar_inside',(0,-1,.7),(0,0,1.56),.55)
    clips=json.loads((TOP/'step_18/ru_scene_clips.json').read_text())['clips'];rig=bpy.data.objects['RIG — native Rheinland'];action=rig.animation_data.action
    for label,key,time in [('game_ru_idle','Sc_MLBODY_STND_IDLE_BRTH_000LV_xa_05',1.),('game_ru_crossed','Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06',2.)]:
        runtime.apply_blender(rig,OUT/'rig_for_preview.json',clips[key],time)
        s.render(scene,label,(-.45,1,.12),(0,.02,1.58),.73)
    hips=json.loads((TOP/'step_25/ru_sleeve_clips.json').read_text())['clips']['Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01']
    runtime.apply_blender(rig,OUT/'rig_for_preview.json',hips,1.27)
    s.render(scene,'game_ru_hands_hips',(.85,1,.03),(0,0,1.32),1.04)
    s.render(scene,'game_ru_hands_hips_other',(-.85,1,.03),(0,0,1.32),1.04)
    rig.animation_data.action=action;scene.frame_set(1)
    a=bpy.data.collections['GAME LOD0 — rh_hassler_body'];a.hide_render=True;bpy.data.collections['GAME LOD1 — rh_hassler_body'].hide_render=False;s.render(scene,'game_low',(0,1,.03),(0,0,.99),2.08)
    bpy.data.collections['GAME LOD1 — rh_hassler_body'].hide_render=True;bpy.data.collections['GAME LOD3 — rh_hassler_body'].hide_render=False;s.render(scene,'game_far',(.5,1,.04),(0,0,.99),2.08)
    result={'native_dfm_sha256':report['sha256'],'preview_blend_sha256':sha(path),'native_head_attachment_error_m':head_error,'source_blend_sha256':report['source_blend_sha256'],'separate_head_and_neck_attachments':True,'dds_decoded_for_preview':True,'reopened':True,'lods':report['lods'],'game_launched':False}
    (OUT/'preview_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print('NATIVE PREVIEW',head_error,flush=True)

if __name__=='__main__':main()
