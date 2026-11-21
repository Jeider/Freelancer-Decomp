"""Check the fuller sleeve cap, sewn boundaries and native pose volume."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step08 as s8
import hassler_native_step23 as s23
import hassler_native_step24 as s24
import hassler_arm_study as study
import hassler_runtime_pose as runtime
configure('character_rounding');TOP=study.TOP;OUT=study.OUT
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));coat=next(o for o in edit.objects if o.name.startswith('10 '));names=[g.name for g in coat.vertex_groups]
 data={o.name:{'p':np.array([v.co[:] for v in o.data.vertices]),'attributes':s24.mesh_invariants(o)} for o in edit.objects if o.type=='MESH'}
 return {'data':data,'coat':coat.name,'names':names,'skin':s8.weights(coat,names),'faces':[(tuple(f.vertices),f.material_index) for f in coat.data.polygons],'uv':[[tuple(q.uv) for q in layer.data] for layer in coat.data.uv_layers],'rows':study.sleeve_rows(coat),'rig':s23.rig_hash(rig)}

def area(p):return float(np.linalg.norm(np.cross(p,np.roll(p,-1,axis=0)).sum(0))*.5)

def main():
 source=OUT/'hassler_native_upper.blend';old=snapshot(study.SOURCE);new=snapshot(source);report=json.loads((OUT/'report.json').read_text(encoding='utf8'))
 assert old['rig']==new['rig']==report['rig_sha256'];assert old['faces']==new['faces'] and old['uv']==new['uv'];assert old['rows']==new['rows']
 for name,data in new['data'].items():
  if name!=new['coat']:
   assert np.array_equal(data['p'],old['data'][name]['p']) and data['attributes']==old['data'][name]['attributes'],name
 p0=old['data'][old['coat']]['p'];p1=new['data'][new['coat']]['p'];w0=old['skin'];w1=new['skin'];changed=set(report['changed_sleeve_vertices']);fixed=sorted(set(range(len(p0)))-changed)
 assert np.array_equal(p0[fixed],p1[fixed]);assert np.max(abs(w1.sum(1)-1))<1e-6 and np.max((w1>1e-7).sum(1))<=4
 assert np.max(abs(w1[fixed]-w0[fixed]))<1e-6
 edgecounts={}
 for face,mat in new['faces']:
  for a,b in zip(face,face[1:]+face[:1]):key=tuple(sorted((a,b)));edgecounts[key]=edgecounts.get(key,0)+1
 for rr in new['rows']:
  for row in (rr[0],rr[-1]):
   assert np.array_equal(p0[row],p1[row]);assert np.max(abs(w1[row]-w0[row]))<1e-6
   for a,b in zip(row,row[1:]+row[:1]):assert edgecounts[tuple(sorted((a,b)))]==2
 bones,joints,bind=runtime.read_rig(TOP/'game/rig_for_preview.json');C=np.array(native.C4);Ci=np.linalg.inv(C);cases=[('rest',None,0.)]
 for label,(clip,_) in study.clips().items():
  duration=max(frames[-1][0] for frames in clip.values());cases.extend((label,clip,float(t)) for t in np.linspace(0,duration,7))
 results=[]
 for label,clip,t in cases:
  world=bind if clip is None else runtime.evaluate(bones,joints,bind,clip,t);mats=np.array([C@world[n]@np.linalg.inv(bind[n])@Ci for n in new['names']])
  def pose(p,w):
   M=np.einsum('vb,bij->vij',w,mats);return np.einsum('vij,vj->vi',M[:,:3,:3],p)+M[:,:3,3]
  a,b=pose(p0,w0),pose(p1,w1);assert np.isfinite(b).all()
  for rr in new['rows']:
   ratios=[area(b[row])/area(a[row]) for row in rr[1:3]]
   assert min(ratios)>1.15,(label,t,ratios)
   results.append({'pose':label,'time':t,'side':'R' if p0[rr[0][0],0]>0 else 'L','upper_ring_area_ratios':ratios})
 result={'source_blend_sha256':sha(source),'parent_sha256':sha(study.SOURCE),'rig_unchanged':True,'sewn_boundaries_unchanged':True,'forearms_and_torso_preserved':True,'epaulettes_pads_collar_belt_preserved':True,'uv_topology_unchanged':True,'new_polygons':0,'minimum_upper_ring_area_ratio':min(min(r['upper_ring_area_ratios']) for r in results),'pose_cases':len(cases),'results':results,'all_passed':True,'reopened':True,'offline_only':True}
 (OUT/'validation.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k!='results'}),flush=True)

if __name__=='__main__':main()
