"""Measure current shoulder boards and their actual cloth clearance."""
import sys,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step07 as s7
configure('character_rounding')
OUT=s7.TOP/'source/upper_finish_study';OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(s7.OUT/'hassler_native_upper.blend'));configure('character_rounding')
edit=bpy.data.collections['EDIT — native costume upper study'];report={}
for ob in edit.objects:
    p=np.array([v.co[:] for v in ob.data.vertices]);row={'name':ob.name,'vertices':len(p),'faces':len(ob.data.polygons),'min':p.min(0).tolist(),'max':p.max(0).tolist()}
    if ob.name.startswith(('13 ','14 ')):
        row['materials']=[m.name for m in ob.data.materials]
        row['modifiers']=[{'type':m.type,'thickness':getattr(m,'thickness',None),'offset':getattr(m,'offset',None),'material_offset':getattr(m,'material_offset',None)} for m in ob.modifiers]
        row['weights']={g.name:round(sum(a.weight for v in ob.data.vertices for a in v.groups if a.group==g.index),3) for g in ob.vertex_groups}
        row['side_bounds']=[{'side':sign,'min':p[p[:,0]*sign>0].min(0).tolist(),'max':p[p[:,0]*sign>0].max(0).tolist()} for sign in (-1,1)] if ob.name.startswith('14 ') else []
    report[ob.name]=row
(OUT/'current_geometry.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(report,indent=2),flush=True)
head=bpy.data.objects['Hassler head — native unchanged'];p=np.array([v.co[:] for v in head.data.vertices]);edges={}
for f in head.data.polygons:
    ids=list(f.vertices)
    for a,b in zip(ids,ids[1:]+ids[:1]):
        key=tuple(sorted((tuple(np.round(p[a],6)),tuple(np.round(p[b],6)))))
        edges[key]=edges.get(key,0)+1
boundary=[e for e,n in edges.items() if n==1 and max(e[0][2],e[1][2])<.62]
info={'head_bounds':[p.min(0).tolist(),p.max(0).tolist()],'lower_neck_boundary':boundary,
      'head_materials':[m.name for m in head.data.materials]}
(OUT/'neck.json').write_text(json.dumps(info,indent=2),encoding='utf8');print('NECK',json.dumps(info),flush=True)
shirt=next(o for o in edit.objects if o.name.startswith('12 '));shirt.hide_render=True
scene=bpy.context.scene;scene.cycles.samples=24;s7.OUT=OUT
s7.render(scene,'native_neck_exposed',(0,1,.1),(0,.01,1.57),.52)
