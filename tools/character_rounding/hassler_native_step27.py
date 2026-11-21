"""Restore deltoid/sleeve-cap volume below Hassler's accepted shoulder pads."""
import sys,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step08 as s8
import hassler_native_step13 as s13
import hassler_native_step20 as geometry
import hassler_native_step23 as s23
import hassler_native_step24 as s24
import hassler_runtime_pose as runtime
import hassler_arm_study as study
configure('character_rounding')
TOP=study.TOP;OUT=study.OUT;SOURCE=study.SOURCE

def main():
 bpy.ops.wm.open_mainfile(filepath=str(SOURCE));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24
 edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));coat=next(o for o in edit.objects if o.name.startswith('10 '));me=coat.data
 fixed={o.name:geometry.geometry_hash(o) for o in edit.objects if o.type=='MESH'};rig_hash=s23.rig_hash(rig)
 names=[g.name for g in coat.vertex_groups];old=s8.weights(coat,names);new=old.copy();p=np.array([v.co[:] for v in me.vertices]);q=p.copy();rows=study.sleeve_rows(coat)
 scales=(1.,1.35,1.30,1.12,1.03,1.)
 for rr in rows:
  root=np.array(rr[0]);top=np.array([s23.smooth(.47,.54,z) for z in p[root,2]])
  cap=np.array([s23.smooth(.43,.52,z) for z in p[root,2]])
  for ri,row in enumerate(rr):
   centre=p[row].mean(0)
   q[row]=p[row]+(p[row]-centre)*(scales[ri]-1)*cap[:,None]
   # The upper cap follows the clavicle/pad more closely, blending smoothly
   # into the rotating upper arm. Keep the original underarm and elbow skin.
   amount=(0.,.35,.15,0.,0.,0.)[ri]*top
   for ci,i in enumerate(row):
    new[i]=(1-amount[ci])*old[i]+amount[ci]*old[root[ci]]
    new[i,np.argsort(new[i])[:-4]]=0;new[i]/=new[i].sum()
 changed=np.flatnonzero(np.linalg.norm(q-p,axis=1)>1e-8)
 for i in changed:me.vertices[int(i)].co=q[i]
 s8.set_weights(coat,new);me.update();normals=[n.vector[:] for n in me.corner_normals];changed_set=set(changed)
 for loop in me.loops:
  if loop.vertex_index in changed_set:normals[loop.index]=me.vertices[loop.vertex_index].normal[:]
 me.normals_split_custom_set(normals)
 # Follow any existing sewn piping without changing its material or topology.
 kd=KDTree(len(p))
 for i,point in enumerate(p):kd.insert(Vector(point),i)
 kd.balance();trim_changes=0
 for ob in edit.objects:
  if not ob.name.startswith('11 '):continue
  ww=s8.weights(ob,names)
  for v in ob.data.vertices:
   loc,i,d=kd.find(v.co)
   if d<.004 and i in changed_set:v.co+=Vector(q[i]-p[i]);ww[v.index]=new[i];trim_changes+=1
  if trim_changes:s8.set_weights(ob,ww)
 changed_names=[coat.name]+([next(o.name for o in edit.objects if o.name.startswith('11 '))] if trim_changes else [])
 assert s23.rig_hash(rig)==rig_hash
 for name,digest in fixed.items():
  if name not in changed_names:assert geometry.geometry_hash(bpy.data.objects[name])==digest,name
 report={'parent':str(SOURCE),'parent_sha256':s13.sha(SOURCE),'rig_sha256':rig_hash,'bones_unchanged':True,'ring_radial_scales':scales,'changed_sleeve_vertices':changed.tolist(),'max_move_m':float(np.linalg.norm(q-p,axis=1).max()),'piping_vertices':trim_changes,'changed_objects':changed_names,'preserved_objects':{n:h for n,h in fixed.items() if n not in changed_names},'shared_shoulder_stitches_unchanged':True,'forearm_stitches_unchanged':True,'epaulettes_pads_collar_belt_unchanged':True,'topology_uv_unchanged':True,'new_polygons':0,'game_launched':False}
 (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 coat['step27_sleeve']='Fuller sleeve cap below the unchanged pad; gradual radial ease towards elbow, cap-to-clavicle skin transition.'
 native.activate(coat);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
 bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));runtime.cull_materials(edit.objects)
 study.render(scene,rig,'after');print(json.dumps({k:v for k,v in report.items() if k not in ('changed_sleeve_vertices','preserved_objects')}),flush=True)

if __name__=='__main__':main()
