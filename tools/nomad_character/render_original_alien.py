import bpy,bmesh,json
from pathlib import Path
from mathutils import Vector
ROOT=Path('D:/work/Freelancer-Decomp/out/nomad_character');OUT=ROOT/'alien_inspection'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'alien/alien.blend'))
ob=bpy.data.objects['mesh_node'];ob.hide_set(False);ob.hide_render=False
for obj in bpy.data.objects:
 if obj!=ob:obj.hide_render=True
bm=bmesh.new();bm.from_mesh(ob.data)
report={'boundary_edges':sum(e.is_boundary for e in bm.edges),'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'loose_vertices':sum(not v.link_faces for v in bm.verts),'components':[]}
visited=set()
for v in bm.verts:
 if v in visited:continue
 stack=[v];visited.add(v);size=0
 while stack:
  curr=stack.pop();size+=1
  for e in curr.link_edges:
   other=e.other_vert(curr)
   if other not in visited:visited.add(other);stack.append(other)
 report['components'].append(size)
bm.free();report['components'].sort(reverse=True)
(OUT/'topology.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Inspection studio');scene.world.color=(.07,.07,.07);scene.view_settings.view_transform='AgX'
for loc,power,size in [((-3,-4,4),420,3),((3,-1,2.5),300,2.5),((1,3,3),550,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);lamp=bpy.context.object;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size;lamp.rotation_euler=(Vector((0,0,1))-lamp.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.12
for name,loc in [('front',(0,5,.95)),('side',(5,0,.95)),('back',(0,-5,.95))]:
 cam.location=loc;cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
