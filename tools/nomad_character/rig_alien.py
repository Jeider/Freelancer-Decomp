"""Bind the user's alien to native robot joints. Writes only a new Blender file."""
import bpy,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
import numpy as np
ROOT=Path(__file__).resolve().parents[2]/'out/nomad_character'
OUT=ROOT/'alien_rigged_v3';OUT.mkdir(exist_ok=True)
SRC=ROOT/'alien/alien.blend';source_hash=hashlib.sha256(SRC.read_bytes()).hexdigest()
bpy.ops.wm.open_mainfile(filepath=str(SRC))
body=bpy.data.objects['mesh_node']
for ob in list(bpy.data.objects):
 if ob!=body:bpy.data.objects.remove(ob,do_unlink=True)
body.hide_set(False);body.hide_render=False
bpy.ops.object.select_all(action='DESELECT');body.select_set(True);bpy.context.view_layer.objects.active=body
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# Both the source alien and native robot face Blender +Y (native -Z).
# Keep the source orientation. A 180-degree mesh-only rotation was incorrect.
original=np.array([v.co[:] for v in body.data.vertices])
data=json.loads((ROOT/'robot_skeleton.json').read_text())
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)));GROUND=.9762919
J={b['name']:np.array(C@Vector(b['position'])+Vector((0,0,GROUND))) for b in data['bones']}
names=[b['name'] for b in data['bones']];indices={name:i for i,name in enumerate(names)}
def smooth(a,b,v):
 t=max(0,min(1,(v-a)/(b-a)));return t*t*(3-2*t)
def mix(a,b,t):
 result={k:v*(1-t) for k,v in a.items()}
 for k,v in b.items():result[k]=result.get(k,0)+v*t
 return result
weights=np.zeros((len(original),len(names)))
# Identify actual connected arm surfaces below the armpits. A coordinate-only
# mask incorrectly left inner cuff and finger vertices attached to the torso.
neighbors=[set() for _ in original]
for e in body.data.edges:
 a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
eligible=original[:,2]<1.22;seen=set();arm_membership=np.zeros(len(original))
for start in np.flatnonzero(eligible):
 if start in seen:continue
 todo=[int(start)];seen.add(start);component=[]
 while todo:
  i=todo.pop();component.append(i)
  for j in neighbors[i]:
   if eligible[j] and j not in seen:seen.add(j);todo.append(j)
 points=original[component]
 if len(component)>100 and abs(points[:,0].mean())>.26 and points[:,2].min()>.70:arm_membership[component]=1
fixed=eligible|(original[:,2]>=1.435)
upper_arm=(np.abs(original[:,0])>.265)&(original[:,2]>=1.22)&(original[:,2]<1.385)
fixed|=upper_arm;arm_membership[upper_arm]=1
edges=np.array([tuple(e.vertices) for e in body.data.edges]);u=np.concatenate((edges[:,0],edges[:,1]));v=np.concatenate((edges[:,1],edges[:,0]))
conductance=1/np.maximum(np.linalg.norm(original[u]-original[v],axis=1),.001)
den=np.bincount(u,weights=conductance,minlength=len(original))
for _ in range(400):
 average=np.bincount(u,weights=conductance*arm_membership[v],minlength=len(original))/np.maximum(den,1e-9)
 arm_membership[~fixed]=average[~fixed]
# Anatomy measured from the front/side rest model. Skeleton itself is immutable.
zsource=[-.0102,.075,.62,1.03,1.20,1.43,1.58,1.70,1.8902]
ztarget=[0,.10,.526,.9763,1.164,1.476,1.61,1.68,1.87]
new=[]
for index,p in enumerate(original):
 x,y,z=p;sgn=1 if x>=0 else -1;side='R' if x>=0 else 'L';ax=abs(x)
 # Anatomical zones, not blind closest-bone transfer across the open ribcage.
 leg=1-smooth(.97,1.065,z)
 arm=float(arm_membership[index])
 if z>.80:leg*=smooth(.025,.085,ax)
 torso=mix({'MAXRoot':1},{'LowerTorso':1},smooth(1.04,1.18,z))
 torso=mix(torso,{'UpperTorso':1},smooth(1.23,1.37,z))
 neck=mix({'UpperTorso':1},{'Body_Neck':1},smooth(1.49,1.62,z))
 neck=mix(neck,{'Body_Head':1},smooth(1.65,1.72,z))
 torso=mix(torso,neck,smooth(1.45,1.50,z))
 lw=mix({side+'Foot':1},{side+'LowLeg':1},smooth(.08,.16,z))
 lw=mix(lw,{side+'Thigh':1},smooth(.575,.66,z))
 aw=mix({side+'Hand':1},{side+'LowArm':1},smooth(.875,.945,z))
 aw=mix(aw,{side+'UpArm':1},smooth(1.175,1.25,z))
 w=mix(mix(torso,lw,leg),aw,arm)
 for name,value in w.items():weights[index,indices[name]]=value
 # Rest-pose fitting: preserve transverse radii while moving limb centre lines.
 q=p.copy();q[2]=np.interp(z,zsource,ztarget)
 source_leg=np.array([sgn*np.interp(z,[.075,.62,1.03],[.145,.15,.14]),np.interp(z,[.075,.62,1.03],[0,-.015,0]),q[2]])
 target_leg=np.array([np.interp(z,[.075,.62,1.03],[J[side+'Foot'][0],J[side+'LowLeg'][0],J[side+'Thigh'][0]]),np.interp(z,[.075,.62,1.03],[J[side+'Foot'][1],J[side+'LowLeg'][1],J[side+'Thigh'][1]]),q[2]])
 q[:2]+=(target_leg-source_leg)[:2]*leg*(1-arm)
 source_arm=np.array([sgn*np.interp(z,[.91,1.215,1.43],[.35,.33,.29]),np.interp(z,[.91,1.215,1.43],[.025,0,0]),0])
 target_arm=np.array([np.interp(z,[.91,1.215,1.43],[J[side+'Hand'][0],J[side+'LowArm'][0],J[side+'UpArm'][0]]),np.interp(z,[.91,1.215,1.43],[J[side+'Hand'][1],J[side+'LowArm'][1],J[side+'UpArm'][1]]),0])
 q[:2]+=(target_arm-source_arm)[:2]*arm
 q[2]=q[2]*(1-arm)+np.interp(z,[.70,.91,1.215,1.43],[J[side+'Hand'][2]-.21,J[side+'Hand'][2],J[side+'LowArm'][2],J[side+'UpArm'][2]])*arm
 new.append(q)
# Light graph smoothing only at mixed-weight seams, across real connected edges.
neighbors=[set() for _ in original]
for e in body.data.edges:
 a,b=e.vertices;neighbors[a].add(b);neighbors[b].add(a)
for _ in range(3):
 revised=weights.copy()
 for i,near in enumerate(neighbors):
  if near and weights[i].max()<.995:revised[i]=weights[i]*.7+weights[list(near)].mean(axis=0)*.3
 weights=revised
for i,w in enumerate(weights):
 keep=np.argsort(w)[-4:];mask=np.zeros(len(w));mask[keep]=w[keep];mask[mask<.002]=0;weights[i]=mask/mask.sum()
for v,p in zip(body.data.vertices,new):v.co=p
body.data.update();body.name='Alien - skinned original mesh'
armature=bpy.data.armatures.new('Native robot_body_a skeleton');rig=bpy.data.objects.new('RIG - robot_body_a',armature);bpy.context.collection.objects.link(rig)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for b in data['bones']:
 eb=armature.edit_bones.new(b['name']);m=(C@Matrix(b['basis'])).to_4x4();m.translation=Vector(J[b['name']]);eb.matrix=m;eb.length=.065
for b in data['bones']:
 if b['parent']:armature.edit_bones[b['name']].parent=armature.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for b in data['bones']:armature.bones[b['name']]['native_bind_3x4']=b['native_bind']
for n in names:body.vertex_groups.new(name=n)
for i,w in enumerate(weights):
 for j in np.flatnonzero(w):body.vertex_groups[names[j]].add([i],float(w[j]),'REPLACE')
mod=body.modifiers.new('Native robot skin - linear blend','ARMATURE');mod.object=rig;mod.use_deform_preserve_volume=False;body.parent=rig
rig['source_dfm']=data['source'];body['source_blend']=str(SRC)
# A short, explicit deformation test action. The saved file opens in rest pose.
def pose(frame,rotations):
 for bone in rig.pose.bones:bone.rotation_mode='QUATERNION';bone.rotation_quaternion=Quaternion((1,0,0,0))
 for name,axis,degrees in rotations:
  bone=rig.pose.bones[name];local=armature.bones[name].matrix_local.to_3x3().inverted()@Vector(axis)
  bone.rotation_quaternion=Quaternion(local,math.radians(degrees))
 for bone in rig.pose.bones:bone.keyframe_insert('rotation_quaternion',frame=frame)
scene=bpy.context.scene
pose(1,[])
pose(30,[('LLowArm',(1,0,0),65),('RLowArm',(1,0,0),45),('Body_Head',(0,0,1),25)])
pose(60,[('LUpArm',(0,1,0),35),('RUpArm',(0,1,0),-35),('LLowArm',(1,0,0),35),('RLowArm',(1,0,0),35)])
pose(90,[('LThigh',(1,0,0),25),('LLowLeg',(1,0,0),-50),('RThigh',(1,0,0),-15),('Body_Head',(0,0,1),-20)])
pose(120,[]);scene.frame_start=1;scene.frame_end=120
for frame,label in [(1,'REST'),(30,'ELBOWS + HEAD'),(60,'SHOULDERS'),(90,'KNEE'),(120,'REST')]:scene.timeline_markers.new(label,frame=frame)
if rig.animation_data and rig.animation_data.action:rig.animation_data.action.name='Robot binding - synthetic joint checks'
scene.frame_set(1)
# Validate untouched topology, all weights, exact native pivots and rest identity.
assert np.isfinite(new).all() and np.isfinite(weights).all()
assert np.max(abs(weights.sum(axis=1)-1))<1e-6
assert (np.sum(weights>0,axis=1)<=4).all()
for b in data['bones']:assert (armature.bones[b['name']].head_local-Vector(J[b['name']])).length<1e-5
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
evaluated=body.evaluated_get(deps);me=evaluated.to_mesh();rest=np.array([v.co[:] for v in me.vertices]);evaluated.to_mesh_clear()
rest_error=float(np.linalg.norm(rest-np.array(new),axis=1).max());assert rest_error<1e-5
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.render.resolution_x=900;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Rig inspection');scene.world.color=(.07,.07,.07);scene.view_settings.view_transform='AgX'
for loc,power,size in [((-3,-4,4),420,3),((3,-1,2.5),300,2.5),((1,3,3),550,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);lamp=bpy.context.object;lamp.data.energy=power;lamp.data.shape='DISK';lamp.data.size=size;lamp.rotation_euler=(Vector((0,0,1))-lamp.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.15
for label,frame,location in [('rest_front',1,(0,5,.95)),('rest_side',1,(5,0,.95)),('rest_back',1,(0,-5,.95)),('elbows_head',30,(2,5,1.8)),('shoulders',60,(0,5,.95)),('knee',90,(3,5,1.7))]:
 scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(deps);me=ev.to_mesh();assert all(math.isfinite(c) for v in me.vertices for c in v.co);ev.to_mesh_clear()
 cam.location=location;cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
scene.frame_set(1);cam.location=(0,5,.95);cam.rotation_euler=(Vector((0,0,.95))-cam.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
report=dict(source_sha256=source_hash,vertices=len(body.data.vertices),triangles=sum(len(f.vertices)-2 for f in body.data.polygons),bones=len(names),max_influences=int((weights>0).sum(axis=1).max()),rest_error=rest_error,native_joint_positions_unchanged=True,topology_unchanged=True,game_installed=False,game_animations_tested=False)
(OUT/'report.json').write_text(json.dumps(report,indent=2));np.savez(OUT/'binding.npz',source_positions=original,positions=new,weights=weights,bone_names=names)
assert hashlib.sha256(SRC.read_bytes()).hexdigest()==source_hash
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'alien_robot_rigged.blend'));print(json.dumps(report))
