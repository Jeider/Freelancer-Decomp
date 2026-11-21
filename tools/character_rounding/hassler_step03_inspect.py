import sys,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
from hassler_native_step03 import OUT
configure('character_rounding')
bpy.ops.wm.open_mainfile(filepath=str(OUT/'hassler_native_upper.blend'));configure('character_rounding')
ob=bpy.data.objects['10 Tunic-vest — continuous shell and collar'];me=ob.data
report={}
for label,select in [('front',lambda p:p.y>.12 and .27<p.z<.42),('back',lambda p:p.y<-.07 and .27<p.z<.42)]:
    faces=[f for f in me.polygons if select(f.center)]
    report[label]={'n':len(faces),'normal':np.mean([f.normal[:] for f in faces],axis=0).tolist()}
adj={};graph={}
for f in me.polygons:
    for a,b in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]):
        adj.setdefault(tuple(sorted((a,b))),[]).append(f.index)
        graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
pending=set(graph);components=[]
while pending:
    todo=[next(iter(pending))];found=set()
    while todo:
        v=todo.pop()
        if v in found:continue
        found.add(v);todo.extend(graph[v]-found)
    pending-=found;components.append(len(found))
report.update(components=components,nonmanifold_edges=sum(len(f)>2 for f in adj.values()),boundary_edges=sum(len(f)==1 for f in adj.values()),faces=len(me.polygons),vertices=len(me.vertices))
me.calc_loop_triangles();uv=me.uv_layers.active;bad={}
for tri in me.loop_triangles:
    a,b,c=[np.array(uv.data[i].uv) for i in tri.loops]
    if abs(np.cross(b-a,c-a))<1e-11:bad[tri.material_index]=bad.get(tri.material_index,0)+1
report['degenerate_uv_by_material']=bad
print(json.dumps(report,indent=2),flush=True)
