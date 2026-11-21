"""Culled rays through the former inner-collar gap, on real DFM LODs/poses."""
import sys,json,gzip,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'tools/hatcher_hair')]
import contours as c
import hassler_runtime_pose as runtime
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'game'

def read(path,level):
    root=c.read_tree(Path(path).read_bytes())[1][0];mesh=c.child(c.child(root,'MultiLevel'),f'Mesh{level}');geo=c.child(mesh,'Geometry')
    p=c.arr(geo,'Points','<f4',3).astype(float);first=c.arr(geo,'Point_bone_first','<u4').ravel();counts=c.arr(geo,'Point_bone_count','<u4').ravel();ids=c.arr(geo,'Bone_id_chain','<u4').ravel();weights=c.arr(geo,'Bone_weight_chain','<f4').ravel()
    skin=[{int(b):float(w) for b,w in zip(ids[f:f+k],weights[f:f+k])} for f,k in zip(first,counts)]
    group=next(g for g in c.child(mesh,'Face_groups').children if g.children and c.blob(g,'Material_name').rstrip(b'\0')==b'rh_hassler_14')
    return p,skin,np.array(c.triangles(group))

def pose(p,skin,trans):
    out=np.zeros_like(p)
    for b in range(len(trans)):
        ids=np.array([i for i,w in enumerate(skin) if b in w],dtype=int)
        if len(ids):out[ids]+=((np.c_[p[ids],np.ones(len(ids))]@trans[b].T)[:,:3]*np.array([skin[i][b] for i in ids])[:,None])
    return out

def hits(points,faces,origins,directions,limit):
    a=points[faces[:,0]];e1=points[faces[:,1]]-a;e2=points[faces[:,2]]-a;result=[]
    for origin,direction in zip(origins,directions):
        h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h)
        inv=1/np.where(abs(det)>1e-15,det,1);s=origin-a;u=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1);v=q@direction*inv;t=np.einsum('ij,ij->i',e2,q)*inv
        valid=(det>1e-10)&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(t>=0)&(t<=limit)
        result.append(float(t[valid].min()) if valid.any() else None)
    return result

def main():
    build=json.loads((OUT/'native_build.json').read_text(encoding='utf8'));current=Path(build['dfm']);sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(current)==build['sha256']
    export=json.loads((OUT/'export.json').read_text(encoding='utf8'));p,skin,faces=read(current,0)
    offset=0
    for part in export['lods'][0]['parts']:
        if part['object'].startswith('24 '):break
        offset+=part['vertices']
    lining=faces[(faces.min(axis=1)>=offset)&(faces.max(axis=1)<offset+part['vertices'])]
    # First 496 triangles are the replacement facing before solidify. These
    # samples are specifically BELOW the former collar root, in the old gap.
    samples=lining[[j*8+k for j in range(1,61,3) for k in (4,5,6,7)]]
    baseline=Path('D:/Games/FL_MOD/DATA/CHARACTERS/BODIES/rh_hassler_body.dfm');oldp,oldskin,oldfaces=read(baseline,0)
    old_report_path=OUT/'collar_opacity_validation.json';previous_verified=False;history_path=None
    if old_report_path.exists():
        prior=json.loads(old_report_path.read_text(encoding='utf8'))
        installed_history=OUT/'history'/(sha(baseline)[:16]+'_collar_opacity.json')
        if prior['native_dfm_sha256']!=sha(baseline) and installed_history.exists():
            prior=json.loads(installed_history.read_text(encoding='utf8'))
        previous_verified=prior['native_dfm_sha256']==sha(baseline) and prior['all_passed']
        if previous_verified:
            history_path=OUT/'history'/(sha(baseline)[:16]+'_collar_opacity.json');history_path.parent.mkdir(exist_ok=True)
            if not history_path.exists():history_path.write_bytes(old_report_path.read_bytes())
    bones,joints,bind=runtime.read_rig(current);clips=json.loads((TOP/'step_18/ru_scene_clips.json').read_text())['clips'];cases=[('rest',None,0)]
    for name,clip in clips.items():
        end=max(x[-1][0] for x in clip.values())
        cases.extend((name,clip,float(t)) for t in np.linspace(0,end,5))
    reports=[];baseline_misses=None;lods=[read(current,i) for i in range(5)]
    for name,clip,time in cases:
        world=bind if clip is None else runtime.evaluate(bones,joints,bind,clip,time)
        trans=[world[b['name']]@np.linalg.inv(bind[b['name']]) for b in bones]
        actual=pose(p,skin,trans);tri=actual[samples];centres=tri.mean(axis=1);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);normal/=np.linalg.norm(normal,axis=1)[:,None]
        inward=np.c_[-centres[:,0],np.full(len(centres),.10),-centres[:,2]]
        normal[np.einsum('ij,ij->i',normal,inward)<0]*=-1
        origins=centres+normal*.008;directions=-normal
        if name=='rest':
            oldhits=hits(oldp,oldfaces,origins,directions,.0095);baseline_misses=sum(v is None for v in oldhits)
            if not previous_verified:assert baseline_misses>20,('Regression must reproduce the previous missing facing',baseline_misses)
        for level in range(5):
            lp,ls,lf=lods[level];posed=pose(lp,ls,trans);found=hits(posed,lf,origins,directions,.0095);missing=sum(v is None for v in found)
            assert missing==0,(name,time,level,missing)
            reports.append({'clip':name,'time':time,'lod':level,'rays':len(samples),'misses':missing,'max_hit_distance_m':max(found)})
    result={'native_dfm_sha256':build['sha256'],'previous_dfm_sha256':sha(baseline),'previous_missing_facing_rays':baseline_misses,'rays_per_case':len(samples),'pose_lod_cases':len(reports),'backface_culling':True,'all_passed':True,'cases':reports,'offline_only':True}
    result['previous_already_verified']=previous_verified
    if history_path:result['previous_validation']=str(history_path)
    (OUT/'collar_opacity_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))

if __name__=='__main__':main()
