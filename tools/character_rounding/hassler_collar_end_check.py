"""Verify the actual right-side opening is opaque in native DFM geometry."""
import sys,json,hashlib
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'tools/hatcher_hair')]
import contours as c
import hassler_runtime_pose as runtime
from hassler_collar_opacity_check import read,pose,hits
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'game'

def first_hits(p,faces,origins,directions,limit):
    a=p[faces[:,0]];e1=p[faces[:,1]]-a;e2=p[faces[:,2]]-a;found=[]
    for origin,direction in zip(origins,directions):
        h=np.cross(np.broadcast_to(direction,e2.shape),e2);det=np.einsum('ij,ij->i',e1,h);inv=1/np.where(abs(det)>1e-15,det,1)
        s=origin-a;u=np.einsum('ij,ij->i',s,h)*inv;q=np.cross(s,e1);v=q@direction*inv;t=np.einsum('ij,ij->i',e2,q)*inv
        good=(det>1e-10)&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1+1e-6)&(t>=0)&(t<=limit)
        ids=np.flatnonzero(good)
        found.append(None if not len(ids) else (int(ids[np.argmin(t[ids])]),float(t[ids].min())))
    return found

def key(points):return tuple(sorted(tuple(np.round(v,6)) for v in points))

def main():
    build=json.loads((OUT/'native_build.json').read_text(encoding='utf8'));path=Path(build['dfm']);sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest();assert sha(path)==build['sha256']
    source=json.loads((TOP/'step_22/report.json').read_text(encoding='utf8'));border=source['boundary_vertices'];bp=np.array(source['border_points_blender']);bp=bp[:,[0,2,1]];bp[:,2]*=-1
    wanted={key([bp[border.index(i)] for i in f]) for f in source['new_triangles']}
    lods=[read(path,i) for i in range(5)];p,skin,faces=lods[0];cap=np.array([f for f in faces if key(p[f]) in wanted]);assert len(cap)==source['new_triangle_count'],len(cap)
    bary=np.array([[.6,.2,.2],[.2,.6,.2],[.2,.2,.6],[1/3,1/3,1/3]])
    directions=np.array([[-.65,.12,-1],[-1,.2,-.5],[-.3,.12,-1]],dtype=float);directions/=np.linalg.norm(directions,axis=1)[:,None]
    targets=np.einsum('bc,fcd->fbd',bary,p[cap]).reshape(-1,3)
    centres=np.tile(targets,(len(directions),1));view=np.repeat(directions,len(targets),axis=0);origins=centres+view*.35
    old=Path('D:/Games/FL_MOD/DATA/CHARACTERS/BODIES/rh_hassler_body.dfm');oldp,oldskin,oldcollar=read(old,0)
    prior_path=OUT/'collar_end_validation.json';previous_verified=False;history_path=None
    if prior_path.exists():
        prior=json.loads(prior_path.read_text(encoding='utf8'))
        installed_history=OUT/'history'/(sha(old)[:16]+'_collar_end.json')
        if prior['native_dfm_sha256']!=sha(old) and installed_history.exists():
            prior=json.loads(installed_history.read_text(encoding='utf8'))
        previous_verified=prior['native_dfm_sha256']==sha(old) and prior['all_passed'] and prior['backface_culling']
        if previous_verified:
            history_path=OUT/'history'/(sha(old)[:16]+'_collar_end.json');history_path.parent.mkdir(exist_ok=True)
            if not history_path.exists():history_path.write_bytes(prior_path.read_bytes())
    root=c.read_tree(old.read_bytes())[1][0];groups=c.child(c.child(c.child(root,'MultiLevel'),'Mesh0'),'Face_groups');allfaces=[];materials=[]
    for g in groups.children:
        if not g.children:continue
        ff=c.triangles(g);allfaces.extend(ff);materials.extend([c.blob(g,'Material_name').rstrip(b'\0').decode()]*len(ff))
    oldhits=first_hits(oldp,np.array(allfaces),origins,-view,.8)
    # Keep rays where the old opening visibly shows another material. This
    # explicitly tests the shoulder/gold visible through the missing side cap.
    previously_open=[i for i,h in enumerate(oldhits) if h is not None and materials[h[0]]!='rh_hassler_14' and h[1]>.347]
    if previous_verified:
        # After the original fix has been installed, retain a real geometric
        # regression against that verified cap rather than requiring a hole.
        assert not previously_open,('Previously verified side cap reopened',len(previously_open))
        selected=[i for i,h in enumerate(oldhits) if h is not None and materials[h[0]]=='rh_hassler_14' and .347<h[1]<.353]
        assert len(selected)>=60,('Insufficient verified side-cap coverage',len(selected))
    else:
        selected=previously_open
        assert len(selected)>=6,('Must reproduce visible right-shoulder opening',len(selected))
    before_materials={}
    for i in previously_open:
        mat=materials[oldhits[i][0]];before_materials[mat]=before_materials.get(mat,0)+1
    bones,joints,bind=runtime.read_rig(path);clips=json.loads((TOP/'step_18/ru_scene_clips.json').read_text())['clips'];cases=[('rest',None,0)]
    for name,clip in clips.items():
        end=max(frames[-1][0] for frames in clip.values());cases.extend((name,clip,float(t)) for t in np.linspace(0,end,5))
    audits=[]
    for name,clip,time in cases:
        world=bind if clip is None else runtime.evaluate(bones,joints,bind,clip,time);trans=[world[b['name']]@np.linalg.inv(bind[b['name']]) for b in bones]
        actual=pose(p,skin,trans);target=np.einsum('bc,fcd->fbd',bary,actual[cap]).reshape(-1,3);target=np.tile(target,(len(directions),1))[selected];vv=view[selected];origin=target+vv*.35
        for level,(lp,ls,lf) in enumerate(lods):
            posed=pose(lp,ls,trans);found=hits(posed,lf,origin,-vv,.353);missing=sum(x is None for x in found);assert missing==0,(level,name,time,missing)
            audits.append({'lod':level,'clip':name,'time':time,'side_opening_rays':len(selected),'misses':missing})
    result={'native_dfm_sha256':build['sha256'],'previous_dfm_sha256':sha(old),'region':'wearer-right end of collar; formerly visible shoulder behind the short lapel','new_cap_triangles':len(cap),'previous_rays_reaching_other_materials':len(previously_open),'previous_visible_materials':before_materials,'rays_per_case':len(selected),'previous_already_verified':previous_verified,'pose_lod_cases':len(audits),'backface_culling':True,'all_passed':True,'cases':audits,'offline_only':True}
    if history_path:result['previous_validation']=str(history_path)
    (OUT/'collar_end_validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='cases'}))

if __name__=='__main__':main()
