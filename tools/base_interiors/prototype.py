"""Actual current Bismarck bar geometry and an editable offline relief study."""
import bpy,sys,json,math,os
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'out/base_interiors/rh_biz_01_base/bar/prototype_v1'
data=json.loads((OUT/'scene_mesh.json').read_text());scene=bpy.context.scene
def vec(d):return np.array([d[str(i)] for i in range(1,4)])
def convert(p):return (p[0],-p[2],p[1])
def matrix(d):return np.array([vec(d[str(i)]) for i in range(1,4)])
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.resolution_x=1280;scene.render.resolution_y=720;scene.render.resolution_percentage=100
scene.render.use_persistent_data=True;scene.view_settings.view_transform='AgX';scene.world.color=(.055,.055,.055)
cache=ROOT/'out/base_interiors/tool_cache/optix';cache.mkdir(exist_ok=True);os.environ['OPTIX_CACHE_PATH']=str(cache)
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for d in prefs.devices:d.use=d.type=='OPTIX'
 scene.cycles.device='GPU'
except Exception:pass
mats={}
for key,m in data['materials'].items():
 mat=bpy.data.materials.new(m['name']);mat.use_nodes=True;nodes=mat.node_tree.nodes;links=mat.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.68
 dt=m['textures'].get('Dt_name')
 if dt:
  tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(dt['path'],check_existing=True);links.new(tex.outputs['Color'],bs.inputs['Base Color']);links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=.35
 et=m['textures'].get('Et_name')
 if et:
  tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(et['path'],check_existing=True);links.new(tex.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=1.7
 elif 'Ec' in m:
  bs.inputs['Emission Strength'].default_value=.8
 geom=nodes.new('ShaderNodeNewGeometry');transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');links.new(geom.outputs['Backfacing'],mix.inputs[0]);links.new(bs.outputs[0],mix.inputs[1]);links.new(transparent.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],nodes.get('Material Output').inputs['Surface'])
 mats[key]=mat
objects=[]
for index,b in enumerate(data['batches']):
 v=np.array(b['vertices']);verts=np.column_stack((v[:,0],-v[:,2],v[:,1]));faces=np.arange(len(v)).reshape(-1,3)
 normals=np.column_stack((v[:,3],-v[:,5],v[:,4]));cross=np.cross(verts[faces[:,1]]-verts[faces[:,0]],verts[faces[:,2]]-verts[faces[:,0]]);flip=np.einsum('ij,ij->i',cross,normals[faces].mean(1))<0;faces[flip]=faces[flip][:,[0,2,1]]
 me=bpy.data.meshes.new(b['part']);me.from_pydata(verts.tolist(),[],faces.tolist());me.update();uv=me.uv_layers.new(name='Native UV0')
 for loop in me.loops:uv.data[loop.index].uv=(v[loop.vertex_index,6],1-v[loop.vertex_index,7])
 for poly in me.polygons:poly.use_smooth=True
 me.normals_split_custom_set([normals[loop.vertex_index] for loop in me.loops])
 ob=bpy.data.objects.new(str(index)+'_'+b['part'],me);bpy.context.collection.objects.link(ob);me.materials.append(mats[b['material']]);ob['native_part']=b['part'];ob['native_batch']=index;objects.append(ob)
ambient=json.loads((OUT/'Rh_01_Bar_ambi_int_01.json').read_text())
for e in ambient['entities'].values():
 if not 'lightprops' in e:continue
 p=e['lightprops'];sp=e['spatialprops'];kind='SUN' if p['type']==3 else 'POINT';ld=bpy.data.lights.new(e['entity_name'],kind);ld.color=vec(p['diffuse']).tolist();ld.energy=1 if kind=='SUN' else 180;ld.shadow_soft_size=.12 if kind=='POINT' else 0
 ob=bpy.data.objects.new(e['entity_name'],ld);bpy.context.collection.objects.link(ob);ob.location=convert(vec(sp['pos']))
 if kind=='SUN':ob.rotation_euler=Vector(convert(vec(p['direction']))).to_track_quat('-Z','Y').to_euler()
hard=json.loads((OUT/'Rh_01_Bar_hardpoint_01.json').read_text());entry=next(e for e in hard['entities'].values() if e['entity_name']=='Camera_0');sp=entry['spatialprops']
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.location=convert(vec(sp['pos']));rot=matrix(sp['orient']);cam.rotation_euler=Matrix([convert(row) for row in rot]).transposed().to_euler();cam.data.type='PERSP';cam.data.angle=math.radians(entry['cameraprops']['fovh']);cam.data.clip_start=.05;cam.data.clip_end=500
def shot(name,pos,target,angle=58):
 cam.location=convert(pos);cam.rotation_euler=(Vector(convert(target))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.angle=math.radians(angle)
 scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
views={'overview':((-11,7,10),(0,4,0),65),'counter':((-7,3.6,5),(0,2,-.6),65)}
def render_set(prefix):
 for name,args in views.items():shot(prefix+'_'+name,*args)
render_set('before')

# Analytic architectural profiles, deliberately independent of texture brightness.
def smooth(x):
 x=np.clip(x,0,1);return x*x*(3-2*x)
def band(x,a,b,w=.008):return smooth((x-a)/w)*smooth((b-x)/w)
def height(uv,name):
 u,v=uv[:,0],uv[:,1];h=np.zeros(len(u))
 if name in ('r_bar_01','r_bar_02'):
  for x,y in ((.373,.45),(.718,.445),(.377,.752),(.716,.76)):
   r=np.sqrt((u-x)**2+(v-y)**2)
   h+=-.075*(1-smooth((r-.112)/.023))+.025*band(r,.133,.155,.009)
 if name=='detailmap_r_bar_08':
  # Four horizontal metal rails on the bar fascia, not its painted glow.
  for a,b in ((.096,.118),(.242,.269),(.382,.407),(.522,.55)):
   h+=.055*band(v,a,b,.008)*band(u,.006,.62,.014)
 if name=='detailmap_r_bar_10':
  for a,b in ((.298,.322),(.405,.428),(.505,.529),(.667,.69),(.797,.82)):
   h+=.035*band(u,a,b,.008)*band(v,.11,.73,.025)
 if name=='detailmap_r_bar_21':
  outer=band(u,.012,.685,.014)*band(v,.018,.381,.012)
  inner=band(u,.037,.651,.018)*band(v,.05,.346,.018)
  h+=.065*(outer-inner)-.028*inner
 if name=='detailmap_r_bar_03':
  for a,b,c,d in ((.005,.425,.005,.421),(.005,.465,.426,.832),(.475,.994,.213,.429),(.475,.994,.442,.653)):
   h+=.06*(band(u,a,b)*band(v,c,d)-band(u,a+.025,b-.025)*band(v,c+.025,d-.025))
  for x,y,r in ((.633,.11,.084),(.6,.342,.075),(.946,.345,.078),(.833,.565,.075)):
   rr=np.sqrt((u-x)**2+(v-y)**2);h+=.09*band(rr,r-.022,r+.018,.01)
 return h
names={'r_bar_01','r_bar_02','detailmap_r_bar_03','detailmap_r_bar_08','detailmap_r_bar_10','detailmap_r_bar_21'}
replaced=[];total=0
for index,b in enumerate(data['batches']):
 name=data['materials'][b['material']]['name'].split('.')[0].lower()
 if name not in names:continue
 vertices=[];faces=[];uvs=[];relief_normals=[]
 for tri in np.array(b['vertices']).reshape(-1,3,b['stride']):
  area=np.linalg.norm(np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]))*.5
  n=max(1,min(64,int(math.ceil(np.sqrt(area)/.055))))
  if name=='detailmap_r_bar_03' and area>.5:n=max(n,min(160,int(math.ceil(np.ptp(tri[:,6:8],axis=0).max()/.003))))
  weights=[];lookup={}
  for i in range(n+1):
   for j in range(n+1-i):lookup[i,j]=len(weights);weights.append((1-(i+j)/n,i/n,j/n))
  samples=np.array(weights)@tri;nn=samples[:,3:6];nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-8)
  shading=nn.copy()
  try:
   tangent=np.linalg.solve(tri[1:,6:8]-tri[0,6:8],tri[1:,:3]-tri[0,:3])
   eps=.0002;uvp=samples[:,6:8]
   du=(height(uvp+[eps,0],name)-height(uvp-[eps,0],name))/(2*eps)
   dv=(height(uvp+[0,eps],name)-height(uvp-[0,eps],name))/(2*eps)
   shading=np.cross(tangent[0]+nn*du[:,None],tangent[1]+nn*dv[:,None]);shading/=np.maximum(np.linalg.norm(shading,axis=1)[:,None],1e-8)
   shading[np.einsum('ij,ij->i',shading,nn)<0]*=-1
  except np.linalg.LinAlgError:pass
  relief_normals.extend([convert(p) for p in shading])
  samples[:,:3]+=nn*height(samples[:,6:8],name)[:,None];offset=len(vertices)
  vertices.extend([convert(p) for p in samples[:,:3]]);uvs.extend([(p[6],1-p[7]) for p in samples])
  for i in range(n):
   for j in range(n-i):
    ts=[(lookup[i,j],lookup[i+1,j],lookup[i,j+1])]
    if j<n-i-1:ts.append((lookup[i+1,j],lookup[i+1,j+1],lookup[i,j+1]))
    for t in ts:
     pts=samples[list(t),:3]
     if np.dot(np.cross(pts[1]-pts[0],pts[2]-pts[0]),nn[list(t)].mean(0))<0:t=t[0],t[2],t[1]
     faces.append(tuple(offset+k for k in t))
 me=bpy.data.meshes.new('Relief_'+name);me.from_pydata(vertices,[],faces);me.update();uv=me.uv_layers.new(name='Native UV0')
 for loop in me.loops:uv.data[loop.index].uv=uvs[loop.vertex_index]
 for poly in me.polygons:poly.use_smooth=True
 me.normals_split_custom_set([relief_normals[loop.vertex_index] for loop in me.loops])
 ob=bpy.data.objects.new('Relief_'+str(index)+'_'+name,me);bpy.context.collection.objects.link(ob);me.materials.append(mats[b['material']]);ob['native_batch']=index
 objects[index].hide_render=True;objects[index].hide_set(True);replaced.append(index);total+=len(faces)
render_set('geometry')
# Soft local practical lights: separate lighting study, not a claimed engine match.
for name,pos,target,color,power,size in [('counter_warm',(0,5,1),(0,1,0),(1,.55,.24),550,4),('blue_fill',(-5,4,3),(0,2,0),(.22,.58,1),350,3),('back_warm',(6,6,-3),(0,3,0),(1,.72,.43),450,3)]:
 ld=bpy.data.lights.new(name,'AREA');ld.energy=power;ld.color=color;ld.shape='DISK';ld.size=size
 ob=bpy.data.objects.new(name,ld);bpy.context.collection.objects.link(ob);ob.location=convert(pos);ob.rotation_euler=(Vector(convert(target))-ob.location).to_track_quat('-Z','Y').to_euler()
for key,mat in mats.items():
 bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.44
 if not data['materials'][key]['textures'].get('Et_name'):bs.inputs['Emission Strength'].default_value=.08
render_set('lighting')
stats={'original_triangles':sum(b['triangles'] for b in data['batches']),'prototype_triangles':total+sum(b['triangles'] for i,b in enumerate(data['batches']) if i not in replaced),'modified_batches':replaced,'geometry_materials':sorted(names),'installed':False,'renderer':'Blender Cycles; approximate source lighting; no native Dm/Bt or small scene props'}
(OUT/'prototype_stats.json').write_text(json.dumps(stats,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bismarck_bar_prototype.blend'))
