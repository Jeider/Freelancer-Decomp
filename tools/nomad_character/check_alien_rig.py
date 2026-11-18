import bpy,numpy as np,json
from pathlib import Path
ROOT=Path('D:/work/Freelancer-Decomp/out/nomad_character/alien_rigged')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alien_robot_rigged.blend'))
ob=bpy.data.objects['Alien - skinned original mesh'];scene=bpy.context.scene
cache={}
for frame in [1,30,60,90,120]:
 scene.frame_set(frame);bpy.context.view_layer.update();ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();cache[frame]=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
a=np.load(ROOT/'binding.npz');p=a['source_positions'];low=p[:,2]<.55
assert np.max(np.linalg.norm(cache[60][low]-cache[1][low],axis=1))<1e-5
assert np.max(np.linalg.norm(cache[120]-cache[1],axis=1))<1e-5
assert np.max(np.linalg.norm(cache[60]-cache[1],axis=1))>.1
r={'arm_pose_lower_legs_max_m':float(np.linalg.norm(cache[60][low]-cache[1][low],axis=1).max()),'return_to_rest_error_m':float(np.linalg.norm(cache[120]-cache[1],axis=1).max()),'max_pose_displacement_m':{str(k):float(np.linalg.norm(v-cache[1],axis=1).max()) for k,v in cache.items()}}
(ROOT/'pose_checks.json').write_text(json.dumps(r,indent=2));print(json.dumps(r))
