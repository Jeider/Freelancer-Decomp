import bpy,numpy as np
from pathlib import Path
p=Path('D:/work/Freelancer-Decomp/out/nomad_character');bpy.ops.wm.open_mainfile(filepath=str(p/'alien/alien.blend'));o=bpy.data.objects['mesh_node'];a=np.array([o.matrix_world@v.co for v in o.data.vertices]);adj=[[] for _ in a]
for e in o.data.edges:
 x,y=e.vertices;adj[x].append(y);adj[y].append(x)
for limit in [1.15,1.22,1.32,1.4]:
 eligible=a[:,2]<limit;seen=set();out=[]
 for i in np.flatnonzero(eligible):
  if i in seen:continue
  todo=[int(i)];seen.add(i);part=[]
  while todo:
   j=todo.pop();part.append(j)
   for k in adj[j]:
    if eligible[k] and k not in seen:seen.add(k);todo.append(k)
  if len(part)>20:out.append((len(part),a[part].min(0).round(3).tolist(),a[part].max(0).round(3).tolist()))
 print(limit,out)
