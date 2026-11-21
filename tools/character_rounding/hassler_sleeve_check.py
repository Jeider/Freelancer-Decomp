"""Reopened source checks for sewn sleeve continuity, rig and native poses."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step08 as s8
import hassler_native_step23 as s23
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_25'

def main():
    source=OUT/'hassler_native_upper.blend';digest=hashlib.sha256(source.read_bytes()).hexdigest()
    bpy.ops.wm.open_mainfile(filepath=str(source));configure('character_rounding')
    rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));coat=next(o for o in edit.objects if o.name.startswith('10 '));me=coat.data
    build=json.loads((OUT/'report.json').read_text(encoding='utf8'));before=json.loads((OUT/'sleeve_study.json').read_text(encoding='utf8'))['mesh']
    names=[g.name for g in coat.vertex_groups];new=s8.weights(coat,names);old=np.array([[w.get(n,0) for n in names] for w in before['skin']]);roots=json.loads(coat['shoulder_stitch_vertices']);ends=json.loads(coat['forearm_stitch_vertices'])
    assert len(me.vertices)==len(before['p'])
    assert [(f.material_index,list(f.vertices)) for f in me.polygons]==[(m,v) for m,v in before['faces']]
    adjacent=[set() for _ in me.vertices];edgefaces={}
    for f in me.polygons:
        vs=list(f.vertices)
        for a,b in zip(vs,vs[1:]+vs[:1]):
            adjacent[a].add(b);adjacent[b].add(a);edge=tuple(sorted((a,b)));edgefaces[edge]=edgefaces.get(edge,0)+1
    blocked=set(i for row in roots for i in row);side_reports=[]
    for root,end in zip(roots,ends):
        for a,b in zip(root,root[1:]+root[:1]):assert edgefaces[tuple(sorted((a,b)))]==2
        component=set(end);todo=list(end)
        while todo:
            for j in adjacent[todo.pop()]-blocked-component:component.add(j);todo.append(j)
        rows=[list(root)];visited=set(root)
        for _ in range(5):
            row=[]
            for i in rows[-1]:
                nextids=adjacent[i]&component-visited;assert len(nextids)==1;row.append(next(iter(nextids)))
            rows.append(row);visited.update(row)
        assert set(rows[-1])==set(end)
        side='R' if me.vertices[root[0]].co.x>0 else 'L';bone=names.index(side+'UpArm');old_values=old[np.array(rows),bone];new_values=new[np.array(rows),bone]
        old_jump=float(abs(np.diff(old_values,axis=0)).max());new_jump=float(abs(np.diff(new_values,axis=0)).max())
        assert new_jump<.32 and new_jump<old_jump
        assert np.min(np.diff(new_values,axis=0))>-.001
        assert np.max(abs(new[root]-old[root]))<1e-6 and np.max(abs(new[end]-old[end]))<1e-6
        side_reports.append({'side':side,'closed_shared_stitches':len(root),'old_max_upper_arm_weight_step':old_jump,'new_max_upper_arm_weight_step':new_jump,'monotone_torso_to_upper_arm':True})
    assert s23.rig_hash(rig)==build['rig_sha256']
    ep=next(o for o in edit.objects if o.name.startswith('14 '));p=np.array([v.co[:] for v in ep.data.vertices]);depth=json.loads((TOP/'step_24/report.json').read_text())
    assert abs(np.ptp(p[:,1])-depth['new_depth_m'])<1e-7
    positions=np.array([v.co[:] for v in me.vertices]);finite=True;bones,joints,bind=runtime.read_rig(TOP/'game/rig_for_preview.json');C=np.array(native.C4);Ci=np.linalg.inv(C)
    clips=json.loads((OUT/'ru_sleeve_clips.json').read_text())['clips'];cases=[]
    for name,clip in clips.items():
        for t in np.linspace(0,max(f[-1][0] for f in clip.values()),9):
            world=runtime.evaluate(bones,joints,bind,clip,float(t));mats=np.array([C@world[n]@np.linalg.inv(bind[n])@Ci for n in names]);M=np.einsum('vb,bij->vij',new,mats);posed=np.einsum('vij,vj->vi',M[:,:3,:3],positions)+M[:,:3,3];assert np.isfinite(posed).all()
            cases.append({'clip':name,'time':float(t),'finite':True})
    report={'source_blend_sha256':digest,'topology_unchanged':True,'sewn_shoulders':side_reports,'rig_unchanged':True,'epaulette_depth_m':float(np.ptp(p[:,1])),'pose_samples':cases,'all_passed':True,'offline_only':True}
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in report.items() if k!='pose_samples'}),flush=True)

if __name__=='__main__':main()
