"""Inspect the actual authored collar section and surrounding surfaces."""
import sys,json
from pathlib import Path
import bpy
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step12 as s12
configure('character_rounding')
TOP=ROOT/'out/character_rounding/hassler/native_upper'
bpy.ops.wm.open_mainfile(filepath=str(TOP/'step_19/hassler_native_upper.blend'))
configure('character_rounding');bpy.context.scene.frame_set(1)
edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '))
coat=next(o for o in edit.objects if o.name.startswith('10 '))
shirt=next(o for o in edit.objects if o.name.startswith('12 '))
faces,rows=s12.collar_rows(coat)
out=TOP/'step_20';out.mkdir(exist_ok=True)
report={'rows':[[list(coat.data.vertices[i].co) for i in r] for r in rows],
        'row_ids':rows,'face_ids':faces,
        'shirt_rings':[[list(v.co) for v in shirt.data.vertices[i:i+48]] for i in range(0,len(shirt.data.vertices),48)],
        'objects':[{'name':o.name,'vertices':len(o.data.vertices),'modifiers':[{'name':m.name,'type':m.type,'enabled':m.show_render,'offset':getattr(m,'offset',None),'thickness':getattr(m,'thickness',None)} for m in o.modifiers]} for o in edit.objects if o.type=='MESH']}
(out/'collar_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(json.dumps({'rows':len(rows),'samples':report['rows'][::4],'objects':report['objects']},ensure_ascii=False),flush=True)
if '--render' in sys.argv:
    import hassler_runtime_pose as runtime
    import hassler_native_step15 as views
    runtime.cull_materials(edit.objects);views.OUT=out
    scene=bpy.context.scene;scene.cycles.samples=16
    scene.render.film_transparent=True
    views.render(scene,'before_front',(-.45,1,.12),(0,.02,1.58),.73)
    head=next(o for o in bpy.data.objects if o.name.startswith('Hassler head '));head.hide_render=True
    views.render(scene,'before_nohead',(-.45,1,.35),(0,.02,1.58),.59)
    views.render(scene,'before_nohead_back',(0,-1,.45),(0,0,1.55),.55)
