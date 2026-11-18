"""Matched before/after renders of offline Mesh0 studies, never AI mockups."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).resolve().parents[2]/'out/character_rounding/li'
records=json.loads((OUT/'inventory.json').read_text())
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=12
scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.render.resolution_percentage=100
scene.world.color=(.12,.12,.12);scene.view_settings.view_transform='AgX'
def model(data,offset,clay):
 for group in data['groups']:
  verts=[];faces=[];normals=[];uv=[];lookup={}
  for tri in group['faces']:
   f=[]
   for index in tri:
    pt=data['point_indices'][index];x,y,z=data['points'][pt]
    if pt not in lookup:lookup[pt]=len(verts);verts.append((x+offset,-z,y))
    f.append(lookup[pt]);x,y,z=data['normals'][pt];normals.append((x,-z,y));uv.append(data['uv'][data['uv_indices'][index]])
   faces.append(f)
  me=bpy.data.meshes.new(group['name']);me.from_pydata(verts,[],faces);me.update()
  ob=bpy.data.objects.new(group['name'],me);bpy.context.collection.objects.link(ob)
  layer=me.uv_layers.new()
  for loop in me.loops:layer.data[loop.index].uv=uv[loop.index]
  for face in me.polygons:face.use_smooth=True
  me.normals_split_custom_set(normals)
  mat=bpy.data.materials.new(group['name']);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.72
  bs.inputs['Base Color'].default_value=(.32,.38,.43,1)
  if not clay and group['texture']:
   tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(group['texture'],check_existing=True);mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
  me.materials.append(mat)
def setup():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for pos,power,size in [((-2,3,3),350,3),((3,2,1),180,2),((0,-2,2),250,2)]:
  bpy.ops.object.light_add(type='AREA',location=pos);lamp=bpy.context.object;lamp.data.energy=power;lamp.data.size=size;lamp.rotation_euler=(Vector((0,0,0))-lamp.location).to_track_quat('-Z','Y').to_euler()
 bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';return cam
for rec in records:
 if '--hatcher-only' in sys.argv and rec['name']!='li_hatcher_body':continue
 folder=OUT/rec['name'];before=json.loads((folder/'before.json').read_text());body=rec['kind']=='BODIES'
 after=json.loads((folder/'after.json').read_text()) if body else None
 variants=[('comparison',False),('detail_clay',True)] if body else [('reference',False)]
 if rec['name']=='li_hatcher_body':variants+=[('belt',False),('belt_clay',True)]
 for label,clay in variants:
  path=folder/(label+'.png')
  if path.exists() and '--hatcher-only' not in sys.argv and not ('--refresh-bodies' in sys.argv and body and rec['name']!='li_hatcher_body'):continue
  cam=setup();detail=label!='comparison' and body;belt=label.startswith('belt')
  offset=.52 if not detail else (.27 if belt else .40)
  model(before,-offset if body else 0,clay)
  if body:model(after,offset,clay)
  center=.04 if belt else (.31 if detail else (-.18 if body else .08))
  cam.location=(0,4,center+.12);cam.rotation_euler=(Vector((0,0,center))-cam.location).to_track_quat('-Z','Y').to_euler()
  cam.data.ortho_scale=(1.15 if belt else 1.8) if detail else (2.5 if body else .48)
  scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
  print('PREVIEW',rec['name'],label,flush=True)
  if belt and not clay:bpy.ops.wm.save_as_mainfile(filepath=str(folder/'belt_comparison.blend'))
