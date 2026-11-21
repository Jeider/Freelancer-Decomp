"""Local contact diagnostics for shoulder cord routing."""
import sys,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step08 import OUT,GARMENT,EPAULETTES
from hassler_step08_check import evaluated
configure('character_rounding');bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding');bpy.context.scene.frame_set(1)
coat=evaluated(bpy.data.objects[GARMENT]);rep=json.loads((OUT/'report.json').read_text(encoding='utf8'))
ep=bpy.data.objects[EPAULETTES];pad=next(o for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.name.startswith('16 '));ed=evaluated(ep);pd=evaluated(pad)
ev=ep.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();mats=[t.material_index for t in me.loop_triangles];ev.to_mesh_clear()
pairs=pd['tree'].overlap(ed['tree']);print('PAD/GOLD MATERIALS',{m:sum(mats[j]==m for i,j in pairs) for m in set(mats)},flush=True)
print('PAD/GOLD POSITIONS',[(i,j,mats[j],np.mean(pd['p'][pd['faces'][i]],axis=0).tolist()) for i,j in pairs[:10]],flush=True)
if '--pad-only' in sys.argv:raise SystemExit(0)
for r in rep['cords']:
    cord=evaluated(bpy.data.objects[r['name']]);pairs=cord['tree'].overlap(coat['tree']);print(r['name'],flush=True)
    print('CENTERLINE',[(i,r['centers'][i]) for i in range(10,18)],flush=True)
    print('CROSSINGS',[(i,j,coat['p'][coat['faces'][j]].tolist(),cord['p'][cord['faces'][i]].tolist()) for i,j in pairs[:4]],flush=True)
