"""Identify geometry in the fixed right-collar close-up, without rendering."""
import sys,json
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from blender_workspace import configure
configure('character_rounding')
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'out/character_rounding/hassler/native_upper/step_22/hassler_native_upper.blend'));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
d=Vector((-.65,1,.12)).normalized();rot=(-d).to_track_quat('-Z','Y').to_matrix();target=Vector((.10,.09,1.58));dg=bpy.context.evaluated_depsgraph_get()
for x,y in [(455,615),(473,605),(450,630),(470,625),(445,600)]:
    origin=target+d*4+rot@Vector(((x/1000-.5)*.34,(.5-y/1000)*.34,0))
    for _ in range(20):
        hit,pos,no,fi,ob,matrix=scene.ray_cast(dg,origin,-d)
        if not hit:break
        if no.dot(d)>0:break
        origin=pos-d*.00001
    if hit:print(json.dumps({'pixel':[x,y],'object':ob.name,'face':fi,'local_position':list(matrix.inverted()@pos)},ensure_ascii=False),flush=True)
