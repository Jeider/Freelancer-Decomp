"""Locate shoulder contacts by actual evaluated triangles and material."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step09 as s9
from hassler_step08_check import evaluated
configure('character_rounding');bpy.ops.wm.open_mainfile(filepath=str(s9.OUT/'hassler_native_upper.blend'));configure('character_rounding');bpy.context.scene.frame_set(1)
ep=evaluated(bpy.data.objects[s9.EPAULETTES]);coat=evaluated(bpy.data.objects[s9.GARMENT]);pad=evaluated(bpy.data.objects[s9.PAD]);result={}
raw=bpy.data.objects[s9.GARMENT].data;prior=json.loads((s9.TOP/'step_07/report.json').read_text(encoding='utf8'));ff=[list(raw.polygons[i].vertices) for i in prior['cut']['collar_faces'][:5]];ids=[ff[0][0]]+[f[1] for f in ff]
print('COLLAR FIRST ROW',[(i,list(raw.vertices[i].co)) for i in ids],flush=True)
for label,a,b in [('ep_coat',ep,coat),('pad_ep',pad,ep)]:
    pairs=a['tree'].overlap(b['tree']);rows=[]
    for i,j in pairs:
        rows.append({'a_tri':i,'b_tri':j,'a_mat':a['material_indices'][i],'b_mat':b['material_indices'][j],'a_center':np.mean(a['p'][a['faces'][i]],axis=0).tolist(),'b_center':np.mean(b['p'][b['faces'][j]],axis=0).tolist(),'a_vertices':a['faces'][i],'b_vertices':b['faces'][j]})
    result[label]=rows;print(label,'count',len(rows),'materials',sorted(set((r['a_mat'],r['b_mat']) for r in rows)),flush=True)
    print(json.dumps(rows[:12]),flush=True)
result['blend_sha256']=hashlib.sha256((s9.OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()
(s9.OUT/'contacts.json').write_text(json.dumps(result,indent=2),encoding='utf8')
for label,ob in [('new',bpy.data.objects[s9.GARMENT]),('old',bpy.data.objects['10 Sewn uniform — finished shoulder fit'])]:
    d=evaluated(ob);pairs=d['tree'].overlap(d['tree']);bad=[]
    for i,j in pairs:
        if i>=j or d['material_indices'][i]!=4 or d['material_indices'][j]!=4 or set(d['faces'][i])&set(d['faces'][j]):continue
        bad.append((i,j,np.mean(d['p'][d['faces'][i]],axis=0).tolist()))
        if label=='new':print('SELF TRIANGLES',d['faces'][i],d['p'][d['faces'][i]].tolist(),d['faces'][j],d['p'][d['faces'][j]].tolist(),flush=True)
    print('COLLAR SELF',label,len(bad),bad[:10],flush=True)
