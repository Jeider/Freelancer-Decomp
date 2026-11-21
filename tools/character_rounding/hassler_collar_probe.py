"""Inspect the installed collar's construction and actual Wilham collar chart."""
import sys,json,gzip,collections
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_step12 as s12
import hassler_native_step15 as render
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_18';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(TOP/'step_17/hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
edit=bpy.data.collections['EDIT — native costume upper study'];coat=next(o for o in edit.objects if o.name.startswith('10 '));shirt=next(o for o in edit.objects if o.name.startswith('12 '))
faces,rows=s12.collar_rows(coat);indices={v for f in faces for v in coat.data.polygons[f].vertices}
r={'collar_rows':[[list(coat.data.vertices[i].co) for i in row] for row in rows], 'materials':[(i,m.name) for i,m in enumerate(coat.data.materials)],'modifiers':[{k:getattr(m,k,None) for k in ('name','type','thickness','offset','material_offset','material_offset_rim','use_flip_normals','use_even_offset','show_viewport','show_render')} for m in coat.modifiers], 'collar_material_counts':dict(collections.Counter(coat.data.polygons[f].material_index for f in faces)), 'shirt_modifiers':[(m.name,m.type) for m in shirt.modifiers]}
ev=coat.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
r['evaluated_collar']=[{'material':m.name,'faces':len([f for f in me.polygons if f.material_index==i]),'upper_faces':len([f for f in me.polygons if f.material_index==i and f.center.z>.52])} for i,m in enumerate(me.materials)];ev.to_mesh_clear()
d=json.loads(gzip.decompress((TOP/'source/wilham.json.gz').read_bytes()));p=np.array(d['points']);uv=np.array(d['uv']);donor=[]
for gi,g in enumerate(d['groups']):
 for t in g['faces']:
  if gi<2 and all(uv[i,0]>.79 and p[i,1]>.45 for i in t):donor.append({'group':gi,'vertices':t,'positions':p[t].tolist(),'uv':uv[t].tolist()})
r['wilham_collar']=donor
(OUT/'probe.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:v for k,v in r.items() if k not in ('collar_rows','wilham_collar','evaluated_collar')},ensure_ascii=False),flush=True)
# Cycles does not implement material.use_backface_culling: make backfaces
# transparent explicitly for a faithful one-sided offline check.
for ob in edit.objects:
 if ob.type!='MESH':continue
 for mat in ob.data.materials:
  if not mat or not mat.use_nodes or mat.get('probe_culling'):continue
  mat['probe_culling']=True;n=mat.node_tree.nodes;l=mat.node_tree.links;out=n.get('Material Output');socket=out.inputs['Surface'].links[0].from_socket
  geo=n.new('ShaderNodeNewGeometry');mix=n.new('ShaderNodeMixShader');trans=n.new('ShaderNodeBsdfTransparent');l.new(geo.outputs['Backfacing'],mix.inputs[0]);l.new(socket,mix.inputs[1]);l.new(trans.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface'])
render.OUT=OUT;scene.cycles.samples=24
render.render(scene,'before_culled',(-.45,1,.20),(0,.02,1.56),.73)
import hassler_runtime_pose as runtime
clips=json.loads((OUT/'ru_scene_clips.json').read_text())['clips']
runtime.apply_blender(bpy.data.objects['RIG — native Rheinland'],OUT/'installed_rig.json',clips['Sc_MLBODY_STND_CROSS_ARMS_000LV_xa_06'],2.0)
render.render(scene,'before_ru_pose',(-.45,1,.12),(0,.02,1.56),.73)
print('SHIRT RINGS',[[min(v.co.z for v in shirt.data.vertices[i*48:(i+1)*48]),max(v.co.z for v in shirt.data.vertices[i*48:(i+1)*48])] for i in range(7)],flush=True)
