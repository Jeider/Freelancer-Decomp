"""Validate the exported neckline against the shared head in native RU-scene poses."""
import sys,json,gzip,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'tools/hatcher_hair')]
import contours as c
import hassler_runtime_pose as runtime
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'game'

def distance(points,segments):
    result=np.full(len(points),np.inf)
    for a,b in segments:
        d=b-a;t=np.clip((points-a)@d/(d@d),0,1);result=np.minimum(result,np.linalg.norm(points-a-t[:,None]*d,axis=1))
    return result

def main():
    report=json.loads((OUT/'native_build.json').read_text(encoding='utf8'));dfm=Path(report['dfm']);assert hashlib.sha256(dfm.read_bytes()).hexdigest()==report['sha256']
    bones,joints,bind=runtime.read_rig(dfm);base=json.loads(gzip.decompress((TOP.parent/'source/body.json.gz').read_bytes()));head=json.loads(gzip.decompress((TOP.parent/'source/head.json.gz').read_bytes()))
    old=next(b for b in base['bones'] if b['name']=='Body_Head')['native_bind'];M=np.eye(4);M[:3,:3]=np.array(old[:9]).reshape(3,3);M[:3,3]=old[9:]
    hp=bind['Body_Head']@M@np.array(base['hardpoints']['hp_head']['matrix']);T=hp@np.linalg.inv(np.array(head['hardpoints']['hp_head']['matrix']))
    N=np.array(base['hardpoints']['hp_neck']['matrix'])@np.linalg.inv(np.array(head['hardpoints']['hp_neck']['matrix']))
    assert np.max(abs(T-N))<2e-7,'Head and neck must both retain native attachment positions'
    p=(np.c_[head['points'],np.ones(len(head['points']))]@T.T)[:,:3];edges={}
    for g in head['groups']:
        for f in g['faces']:
            for a,b in zip(f,f[1:]+f[:1]):
                key=tuple(sorted((tuple(np.round(p[a],6)),tuple(np.round(p[b],6)))));edges[key]=edges.get(key,0)+1
    segments=np.array([e for e,n in edges.items() if n==1 and max(e[0][1],e[1][1])<.62]);assert len(segments)==10
    mesh=json.loads(gzip.decompress((OUT/'decoded_mesh0.json.gz').read_bytes()));p=np.array(mesh['points']);ids=np.flatnonzero(distance(p,segments)<3e-6);assert len(ids)>=48,len(ids)
    clips=json.loads((TOP/'step_18/ru_scene_clips.json').read_text())['clips'];audits=[]
    for key,clip in clips.items():
        duration=max(frames[-1][0] for frames in clip.values())
        for time in np.linspace(0,duration,9):
            world=runtime.evaluate(bones,joints,bind,clip,float(time));Ts=[world[b['name']]@np.linalg.inv(bind[b['name']]) for b in bones];q=np.zeros((len(ids),3))
            for k,i in enumerate(ids):
                for bi,w in mesh['skin'][i].items():q[k]+=(Ts[int(bi)]@np.r_[p[i],1])[:3]*w
            # Actual head Neck is independently connected to body Spine3 by
            # hp_neck. The former rigid-Body_Head test missed the in-game gap.
            H=world['Spine3']@np.linalg.inv(bind['Spine3']);ss=(np.c_[segments.reshape(-1,3),np.ones(20)]@H.T)[:,:3].reshape(10,2,3)
            error=float(distance(q,ss).max());assert error<4e-6,(key,time,error)
            audits.append({'clip':key,'time':float(time),'neck_seam_max_error_m':error})
    # Real geometry has two opposed faces; the saved materials cannot hide a
    # missing lining by turning back-face culling off.
    material=next(m for m in report['materials'] if 'actual collar facing' in m['source_material'])['name']
    faces=np.array(next(g['faces'] for g in mesh['groups'] if g['name']==material));a,b,d=p[faces[:,0]],p[faces[:,1]],p[faces[:,2]];normal=np.cross(b-a,d-a);area=np.linalg.norm(normal,axis=1);normal/=np.maximum(area[:,None],1e-15)
    collar_area=float(area.sum()/2);assert collar_area>.02 and len(faces)>1000
    centres=(a+b+d)/3;dist=np.linalg.norm(centres[:,None]-centres[None,:],axis=2);opposed=normal@normal.T<-.80
    pairs=np.any(opposed&(dist<.006)&(area[:,None]>.65*area[None,:])&(area[:,None]<1.5*area[None,:]),axis=1);paired_area=float(area[pairs].sum()/area.sum());assert paired_area>.95,paired_area
    all_lods=[]
    for level in range(5):
        md=json.loads(gzip.decompress((OUT/f'decoded_mesh{level}.json.gz').read_bytes()));ps=np.array(md['points']);seam=np.flatnonzero(distance(ps,segments)<3e-6);assert len(seam)>=48,(level,len(seam))
        spine=next(i for i,bone in enumerate(bones) if bone['name']=='Spine3')
        assert all(md['skin'][i].get(str(spine),0)>.99999 for i in seam),(level,'Wrong neck attachment')
        all_lods.append({'lod':level,'neck_seam_vertices':len(seam),'follows_body_hp_neck':True})
    result={'native_dfm_sha256':report['sha256'],'neck_seam_vertices_checked':len(ids),'native_sphere_joint_poses_checked':len(audits),'max_neck_seam_error_m':max(v['neck_seam_max_error_m'] for v in audits),'pose_samples':audits,'collar_faces':len(faces),'collar_surface_area_m2':collar_area,'collar_area_with_opposed_inner_outer_surface_fraction':paired_area,'all_lod_neck_bindings':all_lods,'head_total_offset_m':report['head_offset_m'],'head_neck_separate_attachments':True,'shared_head_file_modified':False,'offline_only':True}
    (OUT/'collar_validation.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='pose_samples'}))

if __name__=='__main__':main()
