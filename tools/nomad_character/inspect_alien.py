import bpy,json
from pathlib import Path
from mathutils import Vector
root=Path('D:/work/Freelancer-Decomp/out/nomad_character');bpy.ops.wm.open_mainfile(filepath=str(root/'alien/alien.blend'))
r={'objects':[],'images':[]}
for ob in bpy.data.objects:
 item={'name':ob.name,'type':ob.type}
 if ob.type=='MESH':
  p=[ob.matrix_world@v.co for v in ob.data.vertices]
  item.update(vertices=len(p),triangles=sum(len(f.vertices)-2 for f in ob.data.polygons),bounds=[[min(v[i] for v in p) for i in range(3)],[max(v[i] for v in p) for i in range(3)]],vertex_groups=[g.name for g in ob.vertex_groups],modifiers=[m.type for m in ob.modifiers],materials=[m.name if m else None for m in ob.data.materials])
 r['objects'].append(item)
for im in bpy.data.images:r['images'].append({'name':im.name,'path':im.filepath,'packed':bool(im.packed_file),'size':list(im.size)})
out=root/'alien_inspection';out.mkdir(exist_ok=True);(out/'inventory.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
