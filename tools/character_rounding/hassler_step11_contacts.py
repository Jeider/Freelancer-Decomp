"""Small editable-shape contact diagnostic, never changes a blend."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step11 as s
import hassler_step08_check as c
configure('character_rounding')
bpy.ops.wm.open_mainfile(filepath=str(s.OUT/'hassler_native_upper.blend'));configure('character_rounding');bpy.context.scene.frame_set(1)
data={key:c.evaluated(bpy.data.objects[name]) for key,name in [('gold',s.EPAULETTES),('pad',s.PAD),('coat',s.GARMENT),('join',s.GUSSET)]}
result={}
for a,b in [('gold','pad'),('gold','gold'),('pad','pad'),('gold','coat'),('join','join'),('join','coat')]:
    aa,bb=data[a],data[b];pairs=aa['tree'].overlap(bb['tree'])
    if a==b:pairs=[(i,j) for i,j in pairs if i<j and not set(aa['faces'][i])&set(bb['faces'][j])]
    if a=='join' and b=='join':
        count=len(bpy.data.objects[s.GUSSET].data.vertices);pairs=[(i,j) for i,j in pairs if not {v%count for v in aa['faces'][i]}&{v%count for v in bb['faces'][j]}]
    if b=='coat':pairs=[(i,j) for i,j in pairs if bb['material_indices'][j] in (4,15,22,33)]
    result[a+'/'+b]=[{'a':i,'b':j,'ca':np.mean(aa['p'][aa['faces'][i]],axis=0).tolist(),'cb':np.mean(bb['p'][bb['faces'][j]],axis=0).tolist()} for i,j in pairs]
coat=bpy.data.objects[s.GARMENT];prior=json.loads((s.TOP/'step_07/report.json').read_text(encoding='utf8'));faces=prior['cut']['collar_faces']
result['collar_front_outer']=[{'face':i,'vertices':[list(coat.data.vertices[j].co) for j in coat.data.polygons[i].vertices]} for i in faces if i in faces[4::5] and coat.data.polygons[i].center.y>.055]
print('CONTACTS',json.dumps({key:len(rr) for key,rr in result.items()}),flush=True)
result['blend_sha256']=hashlib.sha256((s.OUT/'hassler_native_upper.blend').read_bytes()).hexdigest()
(s.OUT/'contacts.json').write_text(json.dumps(result,indent=2),encoding='utf8')
