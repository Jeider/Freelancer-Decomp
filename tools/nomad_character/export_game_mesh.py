import bpy,numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]/'out/nomad_character'
OUT=ROOT/'game_body_v3';OUT.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alien_rigged_v3/alien_robot_rigged.blend'))
bpy.context.scene.frame_set(1);ob=bpy.data.objects['Alien - skinned original mesh'];me=ob.data
me.calc_loop_triangles();p=np.array([v.co[:] for v in me.vertices]);p=np.column_stack((p[:,0],p[:,2]-.9762919,-p[:,1]))
# Preserve split normals and UV seams as separate native points if necessary.
points=[];normals=[];uvs=[];skin=[];faces=[];lookup={};names=[g.name for g in ob.vertex_groups]
for tri in me.loop_triangles:
 face=[]
 for loop_id in tri.loops:
  loop=me.loops[loop_id];vi=loop.vertex_index;n=me.corner_normals[loop_id].vector.normalized();assert n.length>.99;n=(n.x,n.z,-n.y)
  uv=me.uv_layers.active.data[loop_id].uv;uv=(uv.x,1-uv.y)
  influences=tuple(sorted((g.group,float(g.weight)) for g in me.vertices[vi].groups if g.weight>0))
  key=(vi,tuple(round(x,7) for x in n),tuple(round(x,7) for x in uv))
  if key not in lookup:
   lookup[key]=len(points);points.append(p[vi]);normals.append(n);uvs.append(uv);skin.append(influences)
  face.append(lookup[key])
 faces.append(face)
weights=np.zeros((len(points),len(names)))
for i,row in enumerate(skin):
 for bone,w in row:weights[i,bone]=w
assert len(points)<65536
np.savez(OUT/'mesh.npz',points=points,normals=normals,uv=uvs,faces=faces,weights=weights,bone_names=names)
print('Exported native-coordinate mesh:',len(points),'points,',len(faces),'triangles')
