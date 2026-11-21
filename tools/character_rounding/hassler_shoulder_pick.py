"""Locate visible collar-junction protrusions in the matched shoulder views."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
configure('character_rounding')
OUT=native.OUT/'native_upper/step_26'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding')
scene=bpy.context.scene;cam=scene.camera;out=[]
for d,target,pixels in [((-1,.04,.35),(.19,.01,1.55),[(740,744),(725,732),(556,710),(684,718)]),((1,.04,.35),(-.19,.01,1.55),[(257,740),(277,749),(725,587),(716,570),(745,603)])]:
 d=Vector(d).normalized();cam.location=Vector(target)+d*4;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=.42;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
 for x,y in pixels:
  origin=cam.matrix_world@Vector(((x/1000-.5)*.42,(.5-y/1000)*.42,0));hit,loc,n,fi,ob,matrix=scene.ray_cast(deps,origin,-d)
  if not hit:continue
  ev=ob.evaluated_get(deps);me=ev.to_mesh();f=me.polygons[fi]
  out.append({'pixel':[x,y],'direction':list(d),'object':ob.name,'face':fi,'point':list(loc),'vertices':list(f.vertices),'rest':[(i,list(ob.data.vertices[i].co)) for i in f.vertices if i<len(ob.data.vertices)]});ev.to_mesh_clear()
join=next(o for o in bpy.data.objects if o.name.startswith('17 ') and o in next(c for c in bpy.data.collections if c.name.startswith('EDIT ')).objects[:])
report={'picks':out,'join_rows':[[list(v.co) for v in join.data.vertices[i:i+4]] for i in range(0,len(join.data.vertices),4)]}
(OUT/'junction_audit.json').write_text(json.dumps(report,indent=2),encoding='utf8');print(json.dumps(out),flush=True)
