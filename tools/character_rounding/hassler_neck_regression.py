"""Measure the real dual-hardpoint neck seam on installed or staged DFM."""
import sys,json,gzip,hashlib,argparse
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'tools/hatcher_hair')]
import contours as c
from hassler_runtime_pose import read_rig,evaluate
from hassler_collar_check import distance
TOP=ROOT/'out/character_rounding/hassler/native_upper'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--dfm',required=True);ap.add_argument('--output',required=True);ap.add_argument('--expect-fixed',action='store_true');args=ap.parse_args();path=Path(args.dfm)
    bones,joints,bind=read_rig(path);base=json.loads(gzip.decompress((TOP.parent/'source/body.json.gz').read_bytes()));head=json.loads(gzip.decompress((TOP.parent/'source/head.json.gz').read_bytes()))
    def attachment(name):
        hp=base['hardpoints'][name];return bind[hp['bone']]@np.array(hp['local'])@np.linalg.inv(np.array(head['hardpoints'][name]['matrix']))
    T=attachment('hp_head');N=attachment('hp_neck');p=np.array(head['points']);edges={}
    for g in head['groups']:
        for f in g['faces']:
            for a,b in zip(f,f[1:]+f[:1]):
                key=tuple(sorted((tuple(np.round(p[a],6)),tuple(np.round(p[b],6)))));edges[key]=edges.get(key,0)+1
    local=np.array([e for e,n in edges.items() if n==1 and max(e[0][1],e[1][1])<-.09]);assert len(local)==10
    hp=np.c_[local.reshape(-1,3),np.ones(20)];head_segments=(hp@T.T)[:,:3].reshape(10,2,3);neck_segments=(hp@N.T)[:,:3].reshape(10,2,3)
    records,_,_=c.as_records(c.read_tree(path.read_bytes())[1][0]);p=np.array([r['p'] for r in records]);ids=np.flatnonzero(distance(p,head_segments)<3e-6);assert len(ids)>=48,len(ids)
    clips=json.loads((TOP/'step_18/ru_scene_clips.json').read_text())['clips'];audits=[]
    for key,clip in clips.items():
        duration=max(frames[-1][0] for frames in clip.values())
        for t in np.linspace(0,duration,9):
            w=evaluate(bones,joints,bind,clip,float(t));skin=[w[b['name']]@np.linalg.inv(bind[b['name']]) for b in bones];q=[]
            for i in ids:q.append(sum(((skin[int(b)]@np.r_[p[i],1])[:3]*v for b,v in records[i]['skin'].items()),np.zeros(3)))
            H=w['Spine3']@np.linalg.inv(bind['Spine3']);target=(np.c_[neck_segments.reshape(-1,3),np.ones(20)]@H.T)[:,:3].reshape(10,2,3);err=float(distance(np.array(q),target).max())
            audits.append({'clip':key,'time':float(t),'neck_gap_m':err})
    maximum=max(a['neck_gap_m'] for a in audits)
    if args.expect_fixed:assert maximum<4e-6,maximum
    result={'dfm':str(path),'dfm_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'uses_separate_hp_head_hp_neck':True,'seam_vertices':len(ids),'max_neck_gap_m':maximum,'passes':maximum<4e-6,'pose_samples':audits}
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='pose_samples'}))

if __name__=='__main__':main()
