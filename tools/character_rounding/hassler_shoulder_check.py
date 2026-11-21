"""Reopen both sources: constrain shoulder edits and preserve the validated sleeves."""
import sys,json,hashlib,collections
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step23 as s23
import hassler_native_step24 as s24
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_26'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def snapshot(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding')
 edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '))
 return s23.rig_hash(rig),{o.name:{'p':np.array([v.co[:] for v in o.data.vertices]),'attributes':s24.mesh_invariants(o),'faces':[tuple(f.vertices) for f in o.data.polygons],'skin':[[(g.group,g.weight) for g in v.groups] for v in o.data.vertices],'face_uv':{tuple(f.vertices):[[tuple(layer.data[i].uv) for i in f.loop_indices] for layer in o.data.uv_layers] for f in o.data.polygons}} for o in edit.objects if o.type=='MESH'}

def main():
 parent=TOP/'step_25/hassler_native_upper.blend';source=OUT/'hassler_native_upper.blend';sleeves=json.loads((TOP/'step_25/validation.json').read_text())
 assert sleeves['all_passed'] and sleeves['source_blend_sha256']==sha(parent)
 rig0,old=snapshot(parent);rig1,new=snapshot(source);assert rig0==rig1
 changed=[];preserved=[];closed={}
 for name,data in new.items():
  if not name.startswith('17 '):assert data['attributes']==old[name]['attributes'],name
  else:
   assert set(data['faces']).issubset(set(old[name]['faces'])),name
   assert data['skin']==old[name]['skin']
   assert all(uv==old[name]['face_uv'][face] for face,uv in data['face_uv'].items())
  assert np.isfinite(data['p']).all()
  if name.startswith(('14 ','16 ','17 ')):changed.append(name)
  else:
   assert np.array_equal(data['p'],old[name]['p']),name
   preserved.append(name)
  if name.startswith(('14 ','16 ')):
   edges=collections.Counter(tuple(sorted((a,b))) for f in data['faces'] for a,b in zip(f,f[1:]+f[:1]))
   assert all(v==2 for v in edges.values()),(name,collections.Counter(edges.values()))
   closed[name]={'edges':len(edges),'all_edges_have_two_faces':True}
 pad=next(n for n in new if n.startswith('16 '));p0,p1=old[pad]['p'],new[pad]['p'];half=1538
 bottom=[i for i in range(len(p0)) if 475<=i%half<950 or i%half>=950+5*84]
 assert np.array_equal(p0[bottom],p1[bottom]) and np.array_equal(p0[:,2],p1[:,2])
 for side in range(2):
  ii=np.arange(side*half,side*half+475)
  assert np.allclose(np.ptp(p1[ii,:2],axis=0)/np.ptp(p0[ii,:2],axis=0),.72,atol=1e-6)
 ep=next(n for n in new if n.startswith('14 '));e0,e1=old[ep]['p'],new[ep]['p'];core=(abs(e0[:,0])<.245)&(e0[:,1]>=-.052)&(e0[:,1]<=.070)
 assert np.max(abs(e0[core]-e1[core]))<1e-7
 assert np.max(e1[:,2]-e0[:,2])<1e-7 and np.max(e0[:,2]-e1[:,2])>.02
 report={'source_blend_sha256':sha(source),'parent_sha256':sha(parent),'parent_sleeve_validation_sha256':sha(TOP/'step_25/validation.json'),'rig_unchanged':True,'sleeve_geometry_uv_skin_preserved':True,'unchanged_objects':preserved,'changed_objects':changed,'closed_epaulettes_and_pads':closed,'pad_lower_vertices_unchanged':len(bottom),'pad_upper_plan_scale':.72,'central_epaulette_height_unchanged':True,'epaulette_max_drop_m':float(np.max(e0[:,2]-e1[:,2])),'all_passed':True,'reopened':True,'offline_only':True}
 (OUT/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8');print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
