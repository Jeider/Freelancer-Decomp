"""Locate any free cloth contacts in the step12 review, without changing it."""
import sys,json,hashlib
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step12 as s
import hassler_step08_check as c
configure('character_rounding');path=s.OUT/'hassler_native_upper.blend'
bpy.ops.wm.open_mainfile(filepath=str(path));configure('character_rounding');bpy.context.scene.frame_set(1)
check=json.loads((s.OUT/'validation.json').read_text(encoding='utf8'))['pose_audits'][0];join=c.evaluated(bpy.data.objects[s.GUSSET]);coat=c.evaluated(bpy.data.objects[s.GARMENT]);rows=[]
for i,j,distance in check['gold_join_collar']['free_contacts']:
    rows.append({'pair':[i,j],'distance':distance,'join_center':np.mean(join['p'][join['faces'][i]],axis=0).tolist(),'coat_center':np.mean(coat['p'][coat['faces'][j]],axis=0).tolist(),'join_vertices':join['faces'][i]})
result={'blend_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'free_join_collar':rows}
report=json.loads((s.OUT/'report.json').read_text(encoding='utf8'));changed=set(report['tailoring']['sleeve_vertices']);count=len(bpy.data.objects[s.GARMENT].data.vertices)
def sleeve_pairs(d):return {(i,j) for i,j in d['tree'].overlap(d['tree']) if i<j and d['material_indices'][i]==d['material_indices'][j]==0 and (set(d['faces'][i])|set(d['faces'][j]))&changed and not {v%count for v in d['faces'][i]}&{v%count for v in d['faces'][j]}}
current=sleeve_pairs(coat)
result['cord_coat_contacts']={}
for name in [o.name for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.name.startswith('13.')]:
    cord=c.evaluated(bpy.data.objects[name]);pairs=cord['tree'].overlap(coat['tree'])
    result['cord_coat_contacts'][name]=[{'coat_triangle':j,'material':int(coat['material_indices'][j]),'center':np.mean(coat['p'][coat['faces'][j]],axis=0).tolist()} for i,j in pairs[:8]]
bpy.context.scene.frame_set(120);turned=c.evaluated(bpy.data.objects[s.GARMENT]);current_turn=sleeve_pairs(turned)
bpy.ops.wm.open_mainfile(filepath=str(s.PARENT));configure('character_rounding');bpy.context.scene.frame_set(1);old=next(o for o in bpy.data.collections['EDIT — native costume upper study'].objects if o.name.startswith('10 '));baseline=sleeve_pairs(c.evaluated(old))
bpy.context.scene.frame_set(120);base_turn=sleeve_pairs(c.evaluated(old))
result['turn_baseline_count']=len(base_turn);result['turn_new']=[{'pair':[i,j],'center':np.mean(turned['p'][turned['faces'][i]],axis=0).tolist()} for i,j in sorted(current_turn-base_turn)]
result['turn_new_rest_vertices']=[{'pair':[i,j],'points_a':coat['p'][coat['faces'][i]].tolist(),'points_b':coat['p'][coat['faces'][j]].tolist()} for i,j in sorted(current_turn-base_turn)]
result['sleeve_baseline_count']=len(baseline);result['sleeve_current_count']=len(current);result['sleeve_new']=[{'pair':[i,j],'a':np.mean(coat['p'][coat['faces'][i]],axis=0).tolist(),'b':np.mean(coat['p'][coat['faces'][j]],axis=0).tolist()} for i,j in sorted(current-baseline)]
(s.OUT/'contacts.json').write_text(json.dumps(result,indent=2),encoding='utf8');print(json.dumps(result),flush=True)
