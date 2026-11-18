"""Sparse explicit relief meshes; original room triangles remain untouched."""
import json,sys,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
OLD=ROOT/'out/base_interiors/rh_biz_01_base/bar/prototype_v1'
DEST=OLD.parent/'prototype_v2';DEST.mkdir(exist_ok=True)
data=json.loads((OLD/'scene_mesh.json').read_text())
# Native matrices act on column vectors. Convert to the row-vector exporter convention.
def transforms(transpose):
 result={'Root':(np.eye(3),np.zeros(3))};pending=data['joints'].copy()
 while pending:
  for j in pending[:]:
   if j['parent'] not in result:continue
   pm,pp=result[j['parent']];r=np.array(j['rot']);r=r.T if transpose else r
   result[j['name']]=(r@pm,np.array(j['pos'])@pm+pp);pending.remove(j)
 return result
old,new=transforms(False),transforms(True)
for b in data['batches']:
 if b['part']=='Root':continue
 om,op=old[b['part']];nm,np_=new[b['part']];v=np.array(b['vertices'])
 v[:,:3]=(v[:,:3]-op)@om.T@nm+np_;v[:,3:6]=v[:,3:6]@om.T@nm;b['vertices']=v.tolist()
(DEST/'scene_mesh.json').write_text(json.dumps(data))
for f in ('Rh_01_Bar_ambi_int_01.json','Rh_01_Bar_hardpoint_01.json','source.json'):(DEST/f).write_bytes((OLD/f).read_bytes())
# Reuse only the source-scene reconstruction, never the dense displacement stage.
code=(ROOT/'tools/base_interiors/prototype.py').read_text().split('views=')[0]
exec(compile(code.replace('prototype_v1','prototype_v2'),str(ROOT/'tools/base_interiors/prototype.py'),'exec'))
for key,m in data['materials'].items():
 if not m['name'].startswith('light_blue'):continue
 mat=mats[key];nodes=mat.node_tree.nodes;links=mat.node_tree.links
 tex=next(n for n in nodes if n.type=='TEX_IMAGE');em=nodes.new('ShaderNodeEmission');links.new(tex.outputs['Color'],em.inputs['Color']);em.inputs['Strength'].default_value=1
 alpha=nodes.new('ShaderNodeMath');alpha.operation='MULTIPLY';links.new(tex.outputs['Alpha'],alpha.inputs[0]);alpha.inputs[1].default_value=m['Oc'][0]
 transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');links.new(alpha.outputs[0],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(em.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])

added=[];records=[]
def supported(batch,center,basis,mid,points,tolerance=.04):
 tris=np.array(batch['vertices']).reshape(-1,3,batch['stride'])
 for uv in points:
  expected=center+(np.array(uv)-mid)@basis;found=False
  for t in tris:
   try:w=np.linalg.solve(np.vstack((t[:,6:8].T,np.ones(3))),np.r_[uv,1])
   except np.linalg.LinAlgError:continue
   if min(w)>=-.004 and np.linalg.norm(w@t[:,:3]-expected)<tolerance:found=True;break
  if not found:return False
 return True
def placements(batch,uv):
 seen=[]
 for t in np.array(batch['vertices']).reshape(-1,3,batch['stride']):
  try:w=np.linalg.solve(np.vstack((t[:,6:8].T,np.ones(3))),np.r_[uv,1]);basis=np.linalg.solve(t[1:,6:8]-t[0,6:8],t[1:,:3]-t[0,:3])
  except np.linalg.LinAlgError:continue
  if min(w)<-.001:continue
  center=w@t[:,:3]
  if any(np.linalg.norm(center-p)<.025 for p in seen):continue
  normal=w@t[:,3:6];normal/=np.linalg.norm(normal);seen.append(center)
  yield center,basis,normal
def mesh(label,verts,faces,uvs,key):
 me=bpy.data.meshes.new(label);me.from_pydata([convert(v) for v in verts],[],faces);me.update();layer=me.uv_layers.new(name='Native UV0')
 for loop in me.loops:layer.data[loop.index].uv=(uvs[loop.vertex_index][0],1-uvs[loop.vertex_index][1])
 for p in me.polygons:p.use_smooth=True
 ob=bpy.data.objects.new(label,me);bpy.context.collection.objects.link(ob);me.materials.append(mats[key]);added.append(ob)
 records.append({'name':label,'triangles':sum(len(f)-2 for f in faces)})
def ring(batch,uv,radius):
 for k,(center,basis,normal) in enumerate(placements(batch,uv)):
  boundary=[np.array(uv)+radius*1.14*np.array([math.cos(a),math.sin(a)]) for a in np.linspace(0,2*math.pi,17)[:-1]]
  if not supported(batch,center,basis,np.array(uv),boundary,.12):continue
  # Smooth annular cross section; no grid, no displacement or staircase contour.
  verts=[];uvs=[];faces=[];segments=64
  for scale,h in ((1.14,.002),(1.10,.06),(1.04,.14),(.94,.14),(.86,.06),(.82,.002)):
   for i in range(segments):
    delta=radius*scale*np.array([math.cos(i*2*math.pi/segments),math.sin(i*2*math.pi/segments)])
    verts.append(center+delta@basis+normal*h);uvs.append(np.array(uv)+delta)
  for j in range(5):
   for i in range(segments):
    f=(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i)
    if np.dot(np.cross(verts[f[1]]-verts[f[0]],verts[f[2]]-verts[f[0]]),normal)<0:f=f[::-1]
    faces.append(f)
  mesh('Raised_ring_'+str(len(added)),verts,faces,uvs,batch['material'])
def rail(batch,a,b,width,height):
 mid=(np.array(a)+b)/2
 for center,basis,normal in placements(batch,mid):
  a=np.array(a);b=np.array(b);direction=b-a;side=np.array([-direction[1],direction[0]]);side/=np.linalg.norm(side)
  if not supported(batch,center,basis,mid,[p+side*width*s for p in (a,mid,b) for s in (-1,1)]):continue
  verts=[];uvs=[]
  # Eight vertices, including chamfered edges.
  for point in (a,b):
   for s,h in ((-1,.002),(-.7,height),(.7,height),(1,.002)):
    uv=point+side*width*s;uvs.append(uv);verts.append(center+(uv-mid)@basis+normal*h)
  faces=[]
  for i in range(3):
   f=(i,i+4,i+5,i+1)
   if np.dot(np.cross(verts[f[1]]-verts[f[0]],verts[f[2]]-verts[f[0]]),normal)<0:f=f[::-1]
   faces.append(f)
  faces.extend(((0,1,2,3),(7,6,5,4)))
  mesh('Raised_strip_'+str(len(added)),verts,faces,uvs,batch['material'])
for batch in data['batches']:
 name=data['materials'][batch['material']]['name'].split('.')[0].lower()
 if name=='detailmap_r_bar_03':
  for uv,r in (((.633,.11),.084),((.6,.342),.075),((.946,.345),.062),((.833,.565),.075)):ring(batch,uv,r)
  for a,b in (((.018,.025),(.018,.405)),((.404,.025),(.404,.405)),((.012,.429),(.44,.429)),((.49,.432),(.987,.432)),((.49,.655),(.987,.655))):rail(batch,a,b,.008,.08)
  for v,a,b in ((.07,.566,.71),(.122,.554,.711),(.17,.58,.69)):
   rail(batch,(a,v),(b,v),.004,.075)
 if name=='detailmap_r_bar_08':
  for v in (.252,.393,.535):
   for a,b in zip(np.linspace(.02,.60,9)[:-1],np.linspace(.02,.60,9)[1:]):rail(batch,(a,v),(b,v),.009,.08)
views={'overview':((-11,7,10),(0,4,0),65),'counter':((-7,3.6,5),(0,2,-.6),65)}
for mode in ('before','after'):
 for ob in added:ob.hide_render=mode=='before'
 for name,args in views.items():shot(mode+'_'+name,*args)
# Isolated technical panel, matched view and lighting, with optional neutral material.
batch=data['batches'][7];uv=np.array([.633,.11]);boundary=[uv+.084*1.14*np.array([math.cos(a),math.sin(a)]) for a in np.linspace(0,2*math.pi,17)[:-1]]
options=[q for q in placements(batch,uv) if supported(batch,q[0],q[1],uv,boundary,.12)];center,basis,normal=max(options,key=lambda q:np.linalg.norm(q[1]))
position=center+normal*2.6+basis[0]/np.linalg.norm(basis[0])*.8
for ob in scene.objects:
 if ob.type=='MESH' and ob not in added:ob.hide_render=ob.get('native_batch')!=7
clay=bpy.data.materials.new('Neutral inspection');clay.use_nodes=True;clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.22,.25,.28,1);clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.65
# Keep backface behaviour of the original room for isolated-panel views.
nodes=clay.node_tree.nodes;links=clay.node_tree.links;geo=nodes.new('ShaderNodeNewGeometry');tr=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');links.new(geo.outputs['Backfacing'],mix.inputs[0]);links.new(nodes.get('Principled BSDF').outputs[0],mix.inputs[1]);links.new(tr.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
for mode in ('before','after'):
 for ob in added:ob.hide_render=mode=='before'
 for style in ('texture','clay'):
  scene.view_layers[0].material_override=clay if style=='clay' else None
  shot('detail_'+style+'_'+mode,position,center,58)
scene.view_layers[0].material_override=None
for ob in scene.objects:
 if ob.type=='MESH':ob.hide_render=False
stats={'original_triangles':sum(b['triangles'] for b in data['batches']),'added_triangles':sum(r['triangles'] for r in records),'added_objects':records,'original_mesh_unchanged':True,'installed':False,'fan_fix':'Transpose native joint matrices; preserve original light mesh and UV, Two-sided alpha Oc=0.65'}
(OUT/'prototype_stats.json').write_text(json.dumps(stats,indent=2))
shot('after_overview',*views['overview']);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bismarck_bar_sparse.blend'))
