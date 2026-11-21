import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step06 import OUT,GARMENT,render
from hassler_step03_check import topology
configure('character_rounding');bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding')
scene=bpy.context.scene;scene.frame_set(1);deps=bpy.context.evaluated_depsgraph_get();data=[]
for x,z in [(.067,.511),(.041,.474),(.061,.488),(.082,.53),(.01,.438)]:
    hit,p,n,idx,ob,m=scene.ray_cast(deps,Vector((x,2,z+.975662)),Vector((0,-1,0)))
    material=ob.data.polygons[idx].material_index if hit and idx<len(ob.data.polygons) else None
    data.append({'xz':[x,z],'object':ob.name if hit else None,'face':idx,'material':material,'hit':list(p) if hit else None})
print(json.dumps({'hits':data,'topology':topology(bpy.data.objects[GARMENT].data)},indent=2),flush=True)
if '--views' in sys.argv:
    edit=bpy.data.collections['EDIT — native costume upper study']
    shirt=next(o for o in edit.objects if o.name.startswith('12 '));under=next(o for o in edit.objects if o.name.startswith('15 '))
    shirt.hide_render=True;render(scene,'debug_without_shirt',(0,1,0),(0,0,1.47),1.02);shirt.hide_render=False
    under.hide_render=True;render(scene,'debug_without_underlap',(0,1,0),(0,0,1.47),1.02)
