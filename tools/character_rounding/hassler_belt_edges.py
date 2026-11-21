"""Read-only boundary audit for the native trousers below the new belt."""
import sys,json
from pathlib import Path
import bpy,numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_native_step14 as s
configure('character_rounding');bpy.ops.wm.open_mainfile(filepath=str(s.OUT/'hassler_native_upper.blend'));configure('character_rounding')
ob=bpy.data.objects[s.BASE];adj={};p=np.array([v.co[:] for v in ob.data.vertices]);key=lambda i:tuple(np.round(p[i],5))
for f in ob.data.polygons:
    ids=list(f.vertices)
    for a,b in zip(ids,ids[1:]+ids[:1]):adj.setdefault(tuple(sorted((key(a),key(b)))),[]).append([a,b])
edges=[v[0] for k,v in adj.items() if len(v)==1 and min(p[v[0],2])>.05]
print(json.dumps([{'ids':e,'points':p[e].tolist()} for e in edges]),flush=True)
(s.OUT/'trouser_boundary.json').write_text(json.dumps(edges),encoding='utf8')
