"""Raise the uniform above a fixed belt; restore native head and dual neck binding."""
import sys,json,gzip,hashlib,math
from pathlib import Path
import bpy,numpy as np
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step08 as s8
import hassler_native_step13 as s13
import hassler_native_step15 as views
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_19';SOURCE=TOP/'step_18/hassler_native_upper.blend'
HEM=.215;STRETCH=.12

def warp(p):
    q=np.array(p,dtype=float);t=float(np.clip((q[2]-HEM)/.085,0,1));q[2]+=STRETCH*max(0,q[2]-HEM)*t*t*(3-2*t);return q

def digest_geometry(ob):
    return hashlib.sha256(np.array([v.co[:] for v in ob.data.vertices],dtype='<f4').tobytes()).hexdigest()

def main():
    OUT.mkdir(exist_ok=True);digest=s13.sha(SOURCE)
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    edit=bpy.data.collections['EDIT — native costume upper study'];rig=bpy.data.objects['RIG — native Rheinland'];head=bpy.data.objects['Hassler head — native unchanged'];body=native.load('body');hd=native.load('head');names=[b['name'] for b in body['bones']]
    protected=[o for o in edit.objects if o.type=='MESH' and o.name.startswith(('00 ','19 ','20 ','21 ','23 '))]+[bpy.data.objects[n] for n in ('Left glove — native unchanged','Right glove — native unchanged')]
    fixed={o.name:digest_geometry(o) for o in protected}
    # Restore the exact native inverse binds and native rest positions: neither
    # head nor neck hardpoint is displaced to compensate for garment proportions.
    native.activate(rig);bpy.ops.object.mode_set(mode='EDIT')
    for b,M in zip(body['bones'],native.bindings(body)):
        rig.data.edit_bones[b['name']].matrix=native.C4@Matrix(M.tolist())
    bpy.ops.object.mode_set(mode='OBJECT')
    for b in body['bones']:rig.data.bones[b['name']]['native_inverse_bind']=b['native_bind']
    T=np.array(body['hardpoints']['hp_head']['matrix'])@np.linalg.inv(hd['hardpoints']['hp_head']['matrix']);N=np.array(body['hardpoints']['hp_neck']['matrix'])@np.linalg.inv(hd['hardpoints']['hp_neck']['matrix']);assert np.max(abs(T-N))<2e-7
    M=native.C4@Matrix(T.tolist())
    for v,p in zip(head.data.vertices,hd['points']):v.co=M@Vector(p)
    head['head_fit_offset_m']=[0,0,0]
    # Deformable2 connects BOTH hp_head (Root) and hp_neck (Neck). Native lower
    # neck vertices follow Spine3 while the cranium follows Body_Head.
    neck_id=next(i for i,b in enumerate(hd['bones']) if b['name']=='Neck');weights=np.zeros((len(hd['points']),len(names)))
    for i,w in enumerate(hd['skin']):
        neck=float(w.get(str(neck_id),0));weights[i,names.index('Spine3')]=neck;weights[i,names.index('Body_Head')]=1-neck
    s8.set_weights(head,weights);head['attachment_preview']='Native dual hp_head + hp_neck; facial bones neutral; lower neck follows Spine3'
    moved={}
    for ob in edit.objects:
        if ob.type!='MESH' or ob in protected:continue
        before=np.array([v.co[:] for v in ob.data.vertices]);normals=np.array([n.vector[:] for n in ob.data.corner_normals])
        for v in ob.data.vertices:v.co=warp(v.co)
        ob.data.update()
        # Transform existing authored split normals by the warp's Jacobian.
        nn=[]
        for loop,no in zip(ob.data.loops,normals):
            p=before[loop.vertex_index];eps=1e-5;dz=(warp(p+[0,0,eps])[2]-warp(p-[0,0,eps])[2])/(2*eps);n=no.copy();n[2]/=dz;n/=max(np.linalg.norm(n),1e-12);nn.append(n)
        ob.data.normals_split_custom_set(nn)
        moved[ob.name]={'vertices_changed':int(np.sum(np.linalg.norm(np.array([v.co[:] for v in ob.data.vertices])-before,axis=1)>1e-8)),'max_raise_m':float(np.max(np.array([v.co.z for v in ob.data.vertices])-before[:,2]))}
    shirt=next(o for o in edit.objects if o.name.startswith('12 '));w=s8.weights(shirt,names)
    # Keep the 48-column chart, but resample the actual native lower neck edge.
    # Use the old seam's exact XY positions: only its prior -35 mm offset goes.
    old_scene_shirt=np.array([v.co[:] for v in shirt.data.vertices])
    previous=json.loads((TOP/'step_18/report.json').read_text(encoding='utf8'))
    # Get the original pre-warp top seam via inverse of the monotone Z warp.
    for i in range(48):
        v=shirt.data.vertices[6*48+i];z=v.co.z;lo,hi=.45,.70
        for _ in range(40):
            mid=(lo+hi)*.5
            if warp([0,0,mid])[2]<z:lo=mid
            else:hi=mid
        v.co.z=(lo+hi)*.5+previous['head_total_drop_m']
    w[:,names.index('Spine3')]+=w[:,names.index('Body_Head')];w[:,names.index('Body_Head')]=0
    w[6*48:7*48]=0;w[6*48:7*48,names.index('Spine3')]=1;s8.set_weights(shirt,w)
    if shirt.data.has_custom_normals:native.activate(shirt);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    shirt.data.update();shirt['neck_seam']='Shared head Neck -> body Spine3 through hp_neck, not Body_Head'
    for ob in protected:assert digest_geometry(ob)==fixed[ob.name],ob.name
    coat=next(o for o in edit.objects if o.name.startswith('10 '));brpath=TOP/'source/bretonia/source/bretonia.json.gz';br=json.loads(gzip.decompress(brpath.read_bytes()));bp=np.array(br['points'])
    report={'parent':str(SOURCE),'parent_sha256':digest,'head_offset_m':0,'head_and_neck_native_bind_restored':True,'uniform_vertical_scale_above_hem':1+STRETCH,'fixed_uniform_hem_z_m':HEM,'unchanged_geometry':fixed,'raised_objects':moved,'bretonia_reference':{'path':str(brpath),'sha256':s13.sha(brpath),'body_sha256':br['sha256'],'upper_collar_y_m':float(bp[:,1].max()),'shoulder_top_y_m':float(bp[(abs(bp[:,0])>.13)&(abs(bp[:,0])<.25)&(bp[:,1]>.45),1].max())},'neck_binding_fix':{'body_head_parent':'Body_Head','lower_neck_parent':'Spine3','runtime_source':'src/Deformable2/Deformable2.cpp:4979 HardpointConnectCallback connects every matching HP, including hp_neck','previous_preview_error':'Head was treated as a rigid single attachment; its neck is attached separately in game'},'game_launched':False}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    scene.frame_set(1);native.activate(coat);scene.cycles.samples=24;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);assert s13.sha(SOURCE)==digest
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;rig=bpy.data.objects['RIG — native Rheinland'];edit=bpy.data.collections['EDIT — native costume upper study'];runtime.cull_materials(edit.objects);views.OUT=OUT
    views.render(scene,'full_front',(0,1,.03),(0,0,1.02),2.13)
    views.render(scene,'collar_close',(-.45,1,.20),(0,.02,1.58),.73)
    views.render(scene,'waist',(0,1,.08),(0,.02,1.15),.59)
    clips=json.loads((TOP/'step_18/ru_scene_clips.json').read_text())['clips']
    for label,key,time in [('ru_idle','Sc_MLBODY_STND_IDLE_BRTH_000LV_xa_05',1.),('ru_crossed','Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06',2.)]:
        runtime.apply_blender(rig,TOP/'step_18/installed_rig.json',clips[key],time);views.render(scene,label,(-.45,1,.12),(0,.02,1.58),.73)
    print(json.dumps({'step':19,'head_offset_m':0,'fixed_objects':len(fixed),'raised':moved},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
