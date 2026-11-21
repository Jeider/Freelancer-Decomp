"""Inspect the actual waist geometry before fitting the Scrote-style belt."""
import sys,json,gzip
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step13 as s
configure('character_rounding')
OUT=s.TOP/'source/belt_study';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(s.OUT/'hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
ob=bpy.data.objects['00 Native lower body and belt'];uv=ob.data.uv_layers[0];p=np.array([v.co[:] for v in ob.data.vertices])
faces=[f for f in ob.data.polygons if f.material_index==1 and all(uv.data[li].uv.x<.2 for li in f.loop_indices) and all(-.02<p[i,2]<.3 for i in f.vertices)]
ids=sorted({i for f in faces for i in f.vertices});q=p[ids]
coat=bpy.data.objects[s.GARMENT];hem=np.array([v.co[:] for v in coat.data.vertices if v.co.z<.24])
d=json.loads(gzip.decompress((s.TOP/'source/scrote/source/scrote.json.gz').read_bytes()));dp=np.array(d['points']);duv=np.array(d['uv']);ff=[(i,t) for i,t in enumerate(d['groups'][0]['faces']) if dp[t,1].max()<.20 and dp[t,1].min()>.10 and duv[t,1].max()<.14]
result={'parent':str(s.OUT/'hassler_native_upper.blend'),'parent_sha256':s.sha(s.OUT/'hassler_native_upper.blend'),'belt_faces':[f.index for f in faces],'belt_vertices':ids,'belt_points':q.tolist(),'belt_bounds':[q.min(0).tolist(),q.max(0).tolist()],'belt_levels':np.unique(np.round(q[:,2],5)).tolist(),'coat_low_bounds':[hem.min(0).tolist(),hem.max(0).tolist()],'scrote_native_faces':[i for i,t in ff],'scrote_belt_bounds':[dp[sorted({i for _,f in ff for i in f})].min(0).tolist(),dp[sorted({i for _,f in ff for i in f})].max(0).tolist()]}
(OUT/'geometry.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in result.items() if k not in ('belt_points','belt_vertices','belt_faces')}),flush=True)
s.OUT=OUT;s.render(scene,'before_front',(0,1,.08),(0,.02,1.15),.59);s.render(scene,'before_side',(1,0,.1),(0,.02,1.15),.59)
