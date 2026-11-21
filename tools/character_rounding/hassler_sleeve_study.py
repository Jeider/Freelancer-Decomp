"""Inspect sleeve-to-torso joints in the user's native RU hands-on-hips pose."""
import sys,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_runtime_pose as runtime
import hassler_native_step15 as views
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_25'

def main():
    bpy.ops.wm.open_mainfile(filepath=str(TOP/'step_24/hassler_native_upper.blend'));configure('character_rounding')
    scene=bpy.context.scene;scene.frame_set(1);scene.cycles.samples=24;views.OUT=OUT
    edit=next(c for c in bpy.data.collections if c.name.startswith('EDIT '));rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));coat=next(o for o in edit.objects if o.name.startswith('10 '));me=coat.data
    runtime.cull_materials(edit.objects)
    report={'materials':[(i,m.name) for i,m in enumerate(me.materials)],'roots':[], 'vertices':[]}
    for root in json.loads(coat['shoulder_stitch_vertices']):
        report['roots'].append([{'id':i,'p':list(me.vertices[i].co),'w':{coat.vertex_groups[g.group].name:g.weight for g in me.vertices[i].groups}} for i in root])
    report['mesh']={'p':[list(v.co) for v in me.vertices],'skin':[{coat.vertex_groups[g.group].name:g.weight for g in v.groups} for v in me.vertices],'faces':[(f.material_index,list(f.vertices)) for f in me.polygons],'uv':[[list(me.uv_layers[0].data[i].uv) for i in f.loop_indices] for f in me.polygons]}
    (OUT/'sleeve_study.json').write_text(json.dumps(report,ensure_ascii=False),encoding='utf8')
    clips=json.loads((OUT/'ru_sleeve_clips.json').read_text())['clips'];clip=clips['Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01']
    for t in (0.,1.,3.):
        runtime.apply_blender(rig,TOP/'game/rig_for_preview.json',clip,t)
        views.render(scene,f'before_hip_{int(t)}',(.85,1,.03),(0,0,1.32),1.04)
    from hassler_native_upper import weights
    data=native.load('body');col=native.collection('REFERENCE native sleeve pose')
    body=native.native_mesh(data,'Native RH elite reference',col)
    native.add_skin(body,weights(data),[b['name'] for b in data['bones']],rig)
    edit.hide_render=True
    runtime.cull_materials(col.objects)
    views.render(scene,'native_hip',(.85,1,.03),(0,0,1.32),1.04)
    print(json.dumps({'root_vertices':[len(r) for r in report['roots']],'polygons':len(me.polygons)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
