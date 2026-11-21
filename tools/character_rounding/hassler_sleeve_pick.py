import sys,json
from pathlib import Path
import bpy,numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_runtime_pose as runtime
configure('character_rounding')
TOP=native.OUT/'native_upper';OUT=TOP/'step_25'
bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding')
scene=bpy.context.scene;rig=next(o for o in bpy.data.objects if o.name.startswith('RIG '));clip=json.loads((OUT/'ru_sleeve_clips.json').read_text())['clips']['Sc_MLBODY_STND_FSTHIPB_HSEC_RLEASE_000LV_XA_01'];runtime.apply_blender(rig,TOP/'game/rig_for_preview.json',clip,3.)
cam=scene.camera;d=Vector((.85,1,.03)).normalized();cam.location=Vector((0,0,1.32))+d*4;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.04;bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
out=[]
for x,y in [(391,465),(399,480),(409,448),(428,416),(365,465),(410,488)]:
 origin=cam.matrix_world@Vector(((x/1000-.5)*1.04,(.5-y/1000)*1.04,0));hit,loc,n,fi,ob,matrix=scene.ray_cast(deps,origin,-d)
 if not hit:continue
 ev=ob.evaluated_get(deps);me=ev.to_mesh();f=me.polygons[fi] if fi<len(me.polygons) else None
 out.append({'pixel':[x,y],'object':ob.name,'face':fi,'point':list(loc),'normal':list(n),'material':me.materials[f.material_index].name if f else None,'verts':list(f.vertices) if f else None,'base_count':len(ob.data.vertices),'rest_verts':[(i,list(ob.data.vertices[i].co),{ob.vertex_groups[g.group].name:g.weight for g in ob.data.vertices[i].groups}) for i in f.vertices if i<len(ob.data.vertices)] if f else []});ev.to_mesh_clear()
(OUT/'pixel_pick.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8');print(json.dumps(out,ensure_ascii=False),flush=True)
