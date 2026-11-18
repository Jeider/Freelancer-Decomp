import bpy,numpy as np,json
from pathlib import Path
ROOT=Path('D:/work/Freelancer-Decomp/out/nomad_character/alien_rigged_v2')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alien_robot_rigged.blend'))
ob=bpy.data.objects['Alien - skinned original mesh'];scene=bpy.context.scene
cache={}
for frame in [1,30,60,90,120]:
 scene.frame_set(frame);bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();cache[frame]=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
a=np.load(ROOT/'binding.npz');p=a['source_positions'];low=p[:,2]<.55
forearm=(np.abs(p[:,0])>.25)&(p[:,2]>.70)&(p[:,2]<1.17)
names=a['bone_names'].tolist();allowed=[i for i,n in enumerate(names) if n in ['LHand','RHand','LLowArm','RLowArm','LUpArm','RUpArm']]
foreign=1-a['weights'][forearm][:,allowed].sum(axis=1)
assert np.max(abs(foreign))<1e-6
edges=np.array([tuple(e.vertices) for e in ob.data.edges]);edges=edges[forearm[edges].all(axis=1)]
base_lengths=np.linalg.norm(cache[1][edges[:,0]]-cache[1][edges[:,1]],axis=1)
lengths=np.linalg.norm(cache[60][edges[:,0]]-cache[60][edges[:,1]],axis=1)
ratios=lengths[base_lengths>.001]/base_lengths[base_lengths>.001]
print('Forearm edge stretch percentiles/max',np.percentile(ratios,[50,95,99,100]))
assert ratios.max()<4

assert np.max(np.linalg.norm(cache[60][low]-cache[1][low],axis=1))<1e-5
assert np.max(np.linalg.norm(cache[120]-cache[1],axis=1))<1e-5
assert np.max(np.linalg.norm(cache[60]-cache[1],axis=1))>.1
r={'forearm_foreign_weight_max':float(abs(foreign).max()),'forearm_edge_stretch_max':float(ratios.max()),'arm_pose_lower_legs_max_m':float(np.linalg.norm(cache[60][low]-cache[1][low],axis=1).max()),'return_to_rest_error_m':float(np.linalg.norm(cache[120]-cache[1],axis=1).max()),'max_pose_displacement_m':{str(k):float(np.linalg.norm(v-cache[1],axis=1).max()) for k,v in cache.items()}}
(ROOT/'pose_checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
