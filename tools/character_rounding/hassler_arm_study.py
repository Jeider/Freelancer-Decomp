"""Measure sleeve rings against the pad in native rest/crossed/hips poses."""
import sys,json,shutil
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step08 as s8
import hassler_native_step15 as views
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_27';SOURCE=TOP/'step_26/hassler_native_upper.blend'

def sleeve_rows(coat):
 roots=json.loads(coat['shoulder_stitch_vertices']);ends=json.loads(coat['forearm_stitch_vertices']);adj=[set() for _ in coat.data.vertices]
 for f in coat.data.polygons:
  ids=list(f.vertices)
  for a,b in zip(ids,ids[1:]+ids[:1]):adj[a].add(b);adj[b].add(a)
 blocked=set(i for row in roots for i in row);result=[]
 for root,end in zip(roots,ends):
  component=set(end);todo=list(end)
  while todo:
   for j in adj[todo.pop()]-blocked-component:component.add(j);todo.append(j)
  rows=[list(root)];visited=set(root)
  for _ in range(5):
   row=[]
   for i in rows[-1]:
    ids=adj[i]&component-visited;assert len(ids)==1;row.append(next(iter(ids)))
   rows.append(row);visited.update(row)
  assert set(rows[-1])==set(end);result.append(rows)
 return result

def clips():
 cross=json.loads((TOP/'step_18/ru_scene_clips.json').read_text())['clips']
 hips=json.loads((TOP/'step_25/ru_sleeve_clips.json').read_text())['clips']
 return {'crossed':(cross['Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06'],2.),'hips':(hips['Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01'],1.27),'idle':(cross['Sc_MLBODY_STND_IDLE_BRTH_000LV_xa_05'],1.)}

def render(scene,rig,prefix):
 views.OUT=OUT;action=rig.animation_data.action
 views.render(scene,prefix+'_rest',(.85,1,.12),(0,0,1.42),.96)
 for label,(clip,time) in clips().items():
  runtime.apply_blender(rig,TOP/'game/rig_for_preview.json',clip,time)
  views.render(scene,prefix+'_'+label,(.85,1,.12),(0,0,1.42),.96)
 rig.animation_data.action=action;scene.frame_set(1)

def main():
 OUT.mkdir(exist_ok=True)
 for f,n in [('M7hm8H','user_crossed.png'),('jq4eHB','user_standing.png')]:
  dest=OUT/n
  if not dest.exists():shutil.copyfile('C:/Users/Freel/AppData/Local/Temp/codex-clipboard-'+f+'.png',dest)
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24
 edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));coat=next(o for o in edit.objects if o.name.startswith('10 '));pad=next(o for o in edit.objects if o.name.startswith('16 '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '))
 rows=sleeve_rows(coat);names=[g.name for g in coat.vertex_groups];p=np.array([v.co[:] for v in coat.data.vertices]);w=s8.weights(coat,names);pp=np.array([v.co[:] for v in pad.data.vertices]);pw=s8.weights(pad,names)
 bones,joints,bind=runtime.read_rig(TOP/'game/rig_for_preview.json');C=np.array(native.C4);Ci=np.linalg.inv(C);stats=[]
 for label,(clip,t) in {'rest':(None,0),**clips()}.items():
  world=bind if clip is None else runtime.evaluate(bones,joints,bind,clip,t);mats=np.array([C@world[n]@np.linalg.inv(bind[n])@Ci for n in names])
  def pose(p,w):
   M=np.einsum('vb,bij->vij',w,mats);return np.einsum('vij,vj->vi',M[:,:3,:3],p)+M[:,:3,3]
  q=pose(p,w);padq=pose(pp,pw)
  for rr in rows:
   side='R' if p[rr[0][0],0]>0 else 'L';stats.append({'pose':label,'side':side,'rings':[{'centre':q[r].mean(0).tolist(),'min':q[r].min(0).tolist(),'max':q[r].max(0).tolist(),'arm_weight_mean':float(w[r,names.index(side+'UpArm')].mean())} for r in rr],'pad_min':padq[pp[:,0]*(1 if side=='R' else -1)>0].min(0).tolist(),'pad_max':padq[pp[:,0]*(1 if side=='R' else -1)>0].max(0).tolist()})
 (OUT/'arm_study.json').write_text(json.dumps({'rows':rows,'stats':stats,'p':p.tolist(),'weights':w.tolist(),'pad_points':pp.tolist(),'pad_weights':pw.tolist(),'bone_names':names},indent=2),encoding='utf8')
 print(json.dumps(stats),flush=True)
 runtime.cull_materials(edit.objects);render(scene,rig,'before')

if __name__=='__main__':main()
