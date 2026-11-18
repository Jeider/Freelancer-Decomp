"""Art-guided Nomad blockout, with the native robot's joints and bind bases.
Blender only. No game or DATA writes; no promise of finished game export.
"""
import bpy, math, json, random
from pathlib import Path
from mathutils import Vector, Matrix
from math import sin, cos, pi
random.seed(13)
OUT=Path(__file__).resolve().parents[2]/'out/nomad_character'
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
data=json.loads((OUT/'robot_skeleton.json').read_text())
C=Matrix(((1,0,0),(0,0,-1),(0,1,0)));GROUND=.9762919
J={b['name']:C@Vector(b['position'])+Vector((0,0,GROUND)) for b in data['bones']}
def material(name,color,metal,rough,noise=0):
 m=bpy.data.materials.new(name);m.diffuse_color=(*color,1);m.use_nodes=True
 n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if noise:
  tex=n.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=130;tex.inputs['Detail'].default_value=3
  bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.23;bump.inputs['Distance'].default_value=noise
  m.node_tree.links.new(tex.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
 return m
shell=material('01 - blue black chitin',(.035,.075,.092),.55,.3,.001)
edge=material('02 - polished chitin ridges',(.13,.23,.26),.6,.29)
flesh=material('03 - wine coloured membranes',(.26,.036,.095),.05,.45,.0007)
gold=material('04 - ochre tendons',(.27,.19,.085),.25,.43,.001)
dark=material('05 - deep joint recesses',(.012,.019,.024),.1,.38)
eye=material('06 - amber eyes',(.65,.53,.15),.35,.18)
objects=[]
def mesh(name,v,f,mat,bone):
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],f);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);me.materials.append(mat)
 for p in me.polygons:p.use_smooth=True
 if bone:
  ob.vertex_groups.new(name=bone).add(list(range(len(v))),1,'REPLACE')
 objects.append(ob);return ob
def tube(name,points,radii,mat,bone,sides=10):
 pts=[Vector(p) for p in points];vs=[];fs=[]
 for i,p in enumerate(pts):
  axis=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();ref=Vector((0,1,0))
  if abs(axis.dot(ref))>.95:ref=Vector((1,0,0))
  u=axis.cross(ref).normalized();v=axis.cross(u).normalized();r=radii[i] if isinstance(radii,list) else radii
  for j in range(sides):vs.append(p+r*(u*cos(j*2*pi/sides)+v*sin(j*2*pi/sides)))
  if i:
   for j in range(sides):a=(i-1)*sides+j;b=(i-1)*sides+(j+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.append(tuple(reversed(range(sides))));fs.append(tuple((len(pts)-1)*sides+j for j in range(sides)))
 return mesh(name,vs,fs,mat,bone)
def curve(name,controls,r,mat,bone,steps=18,sides=8):
 # Catmull-Rom interpolation through the supplied anatomical landmarks.
 p=[Vector(controls[0])]+[Vector(v) for v in controls]+[Vector(controls[-1])];pts=[]
 for i in range(1,len(p)-2):
  for j in range(steps//(len(p)-3)+1):
   t=j/(steps//(len(p)-3)+1);a,b,c,d=p[i-1:i+3]
   pts.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
 pts.append(Vector(controls[-1]));return tube(name,pts,r,mat,bone,sides)
def loft(name,rows,mat,bone,sides=20,ridge=.0):
 # rows: x centre, y centre, z, x radius, y radius
 vs=[];fs=[]
 for i,(x,y,z,rx,ry) in enumerate(rows):
  for k in range(sides):
   a=2*pi*k/sides;fac=1+ridge*cos(6*a);vs.append((x+rx*cos(a)*fac,y+ry*sin(a)*fac,z))
  if i:
   for k in range(sides):a=(i-1)*sides+k;b=(i-1)*sides+(k+1)%sides;fs.append((a,b,b+sides,a+sides))
 fs.append(tuple(reversed(range(sides))));fs.append(tuple((len(rows)-1)*sides+k for k in range(sides)))
 return mesh(name,vs,fs,mat,bone)
def ell(name,pos,scale,mat,bone):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=pos);ob=bpy.context.object;ob.name=name;ob.scale=scale
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);ob.data.materials.append(mat)
 for p in ob.data.polygons:p.use_smooth=True
 if bone:ob.vertex_groups.new(name=bone).add(list(range(len(ob.data.vertices))),1,'REPLACE')
 objects.append(ob);return ob
def blade(name,pts,widths,mat,bone,front=True):
 # Ridged shell strip with a raised centre and folded perimeter.
 vs=[];fs=[];sign=-1 if front else 1
 for (x,y,z),w in zip(pts,widths):vs.extend([(x-w,y,z),(x,y+sign*w*.37,z+.006),(x+w,y,z),(x,y-sign*.007,z)])
 for i in range(1,len(pts)):
  for k in range(4):a=(i-1)*4+k;b=(i-1)*4+(k+1)%4;fs.append((a,b,b+4,a+4))
 fs.extend([(3,2,1,0),tuple((len(pts)-1)*4+i for i in range(4))]);return mesh(name,vs,fs,mat,bone)
def mantle(s):
 vs=[];fs=[];steps=16
 # Lenticular shoulder shield: broad front/back, tapered lateral tip.
 for layer in [0,1]:
  for i in range(9):
   t=i/8;x=s*(.045+.29*t);w=.012+.095*sin(pi*t)**.75
   for j in range(steps+1):
    u=j/steps*2-1;z=1.521+.022*sin(pi*t)-.04*t+.022*(1-u*u)
    if layer:z-=.012+.008*(1-u*u)
    vs.append((x,w*u,z))
 n=9*(steps+1)
 for layer in [0,1]:
  for i in range(8):
   for j in range(steps):
    a=layer*n+i*(steps+1)+j;f=(a,a+1,a+steps+2,a+steps+1);fs.append(f if layer==0 else f[::-1])
 for i in range(8):
  for j in [0,steps]:
   a=i*(steps+1)+j;b=a+steps+1;fs.append((a,b,b+n,a+n))
 return mesh('broad mantle shell '+str(s),vs,fs,shell,'UpperTorso')
def leg_shell(side,a,b):
 vs=[];fs=[];N=18
 for i,(t,r) in enumerate([(0,.04),(.12,.067),(.4,.064),(.72,.043),(.94,.033)]):
  p=a.lerp(b,t)
  for j in range(N+1):
   ang=-.25+ (pi+.50)*j/N
   vs.append((p.x+r*cos(ang),p.y+r*.8*sin(ang),p.z+.018*sin(ang*3)))
  if i:
   for j in range(N):q=(i-1)*(N+1)+j;fs.append((q,q+1,q+N+2,q+N+1))
 ob=mesh(side+' thigh wrap shell',vs,fs,shell,side+'Thigh')
 mod=ob.modifiers.new('Chitin thickness','SOLIDIFY');mod.thickness=.004

# Slender articulated trunk: visible gaps beneath the shoulder mantle.
loft('abdominal membrane',[(0,0,.96,.075,.065),(0,0,1.06,.055,.055),(0,0,1.19,.036,.047),(0,0,1.35,.062,.065),(0,0,1.46,.11,.075)],flesh,'LowerTorso')
loft('thoracic carapace',[(0,-.015,1.28,.038,.05),(0,-.025,1.38,.08,.065),(0,-.025,1.49,.15,.073),(0,-.015,1.52,.13,.055)],shell,'UpperTorso')
loft('pelvic girdle',[(0,0,.91,.045,.043),(0,0,.96,.105,.075),(0,0,1.04,.16,.08),(0,0,1.08,.12,.06)],shell,'MAXRoot')
for i in range(9):
 z=1.105+i*.042;w=.021+i*.008
 for s in [-1,1]:
  curve('ventral rib %s %s'%(s,i),[(s*w,-.075,z+.016),(s*w*.62,-.094,z+.019),(0,-.101,z-.009)],.007 if i<5 else .009,edge,'UpperTorso' if i>4 else 'LowerTorso',12)
  curve('dorsal chevron %s %s'%(s,i),[(s*.042,.069,z+.018),(s*.02,.086,z),(0,.092,z+.025)],.006,edge,'UpperTorso' if i>4 else 'LowerTorso',10)
for s in [-1,1]:
 mantle(s)
 # Shell mantle bridges the upper ribcage; tips overlap the upper arms.
 blade('shoulder mantle '+str(s),[(s*.015,0,1.535),(s*.13,0,1.54),(s*.25,0,1.51),(s*.32,0,1.49)],[.025,.092,.084,.003],shell,'UpperTorso')
 curve('mantle lip '+str(s),[(s*.018,-.055,1.53),(s*.13,-.09,1.535),(s*.25,-.08,1.50),(s*.32,0,1.49)],.009,edge,'UpperTorso')
 curve('flank tendon '+str(s),[(s*.12,.01,1.46),(s*.09,.025,1.34),(s*.07,.025,1.19),(s*.12,.015,1.07)],.014,gold,'LowerTorso')
 for k in range(5):
  curve('thoracic hanging fibre',[(s*(.13+.018*k),.015,1.49),(s*(.13+.012*k),.035,1.38-k*.013),(s*.085,.035,1.35)],.0017,gold,'UpperTorso',16,5)

# Long organic neck and central armoured throat. Head is carried by Body_Head.
loft('long neck membrane',[(0,.015,1.49,.085,.055),(0,.025,1.57,.058,.047),(0,.025,1.67,.047,.047),(0,.005,1.76,.07,.06)],flesh,'Body_Neck')
for i in range(8):
 z=1.515+i*.029
 ell('throat segment',(0,-.039,z),(.034,.021,.021),shell,'Body_Neck')
 ell('rear neck segment',(0,.065,z),(.033,.016,.022),shell,'Body_Neck')
for s in [-1,1]:
 for k in range(7):
  x=.034+k*.005
  curve('neck sinew',[(s*x,.0,1.51),(s*x*.7,-.024,1.61),(s*x*.8,-.014,1.70),(s*(x+.015),-.01,1.76)],.0016,edge if k==0 else flesh,'Body_Neck',18,5)
 curve('neck front horseshoe',[(s*.068,-.02,1.74),(s*.068,-.063,1.64),(s*.062,-.065,1.54),(0,-.075,1.51)],.009,gold,'Body_Neck')

# Crown and beaked skull, amber slit eyes and the toothed jaw rim.
loft('skull crown',[(0,.01,1.745,.065,.055),(0,-.005,1.775,.115,.083),(0,.012,1.82,.105,.075),(0,.022,1.85,.070,.055),(0,.018,1.866,.026,.025)],shell,'Body_Head',24,.035)
mesh('angular beak',[(0,-.17,1.742),(-.092,-.064,1.79),(.092,-.064,1.79),(0,-.102,1.817),(-.076,-.035,1.75),(.076,-.035,1.75)],[(0,1,3),(0,3,2),(0,4,1),(0,2,5),(4,5,2,1)],flesh,'Body_Head')
curve('beak centre keel',[(0,-.105,1.822),(0,-.14,1.79),(0,-.175,1.744)],.005,edge,'Body_Head')
for s in [-1,1]:
 ob=ell('amber slit eye',(s*.054,-.075,1.805),(.035,.012,.010),eye,'Body_Head');ob.rotation_euler[1]=-s*.18
 mesh('upper beak chitin '+str(s),[(0,-.173,1.744),(s*.018,-.108,1.814),(s*.096,-.057,1.803),(s*.118,-.016,1.778),(s*.064,-.105,1.768)],[(0,1,4),(1,2,4),(2,3,4)],shell,'Body_Head')
 curve('heavy brow',[(s*.015,-.095,1.811),(s*.045,-.084,1.826),(s*.087,-.052,1.817)],.008,shell,'Body_Head')
 curve('jaw ridge',[(0,-.168,1.738),(s*.047,-.11,1.733),(s*.092,-.052,1.75)],.007,edge,'Body_Head')
 for i in range(6):
  t=i/6;x=s*(.015+t*.068);y=-.15+t*.09;z=1.738+t*.008
  tube('jaw tooth',[(x,y,z),(x,y-.005,z-.014)],[.004,.0003],edge,'Body_Head',6)
 # Segmented curved auricular hoses, kept separate for future secondary motion.
 controls=[(s*.09,.025,1.79),(s*.145,.028,1.75),(s*.195,.025,1.65),(s*.23,.025,1.54)]
 curve('auricular tendon '+str(s),controls,.021,gold,'Body_Head',28,12)
 for i in range(13):
  t=i/12;x=s*(.1+.13*t);z=1.79-.25*t
  ell('hose armour bead',(x,.025,z),(.022,.023,.012),dark if i%4==0 else gold,'Body_Head')
for i in range(19):
 a=2*pi*i/19;x=.095*cos(a);y=.015+.065*sin(a);z=1.826+.016*sin(a)
 h=.032+.032*(.5+.5*cos(a*3))
 tube('crown thorn %02d'%i,[(x,y,z),(x*1.13,y*1.2,z+h*.55),(x*1.28,y*1.4,z+h)],[.011,.006,.0002],shell,'Body_Head',7)
for i in range(70):
 a=random.random()*2*pi;r=random.uniform(.3,1);x=.095*r*cos(a);y=.015+.061*r*sin(a)
 ell('crown pore',(x,y,1.852-.015*r),(.0027,.0027,.002),edge,'Body_Head')

# Robot joint centres are used directly, including its asymmetric rest pose.
for side,sgn in [('L',-1),('R',1)]:
 hip=J[side+'Thigh'];knee=J[side+'LowLeg'];ankle=J[side+'Foot'];shoulder=J[side+'UpArm'];elbow=J[side+'LowArm'];wrist=J[side+'Hand']
 leg_shell(side,hip,knee)
 for label,a,b,r,bone in [('upper arm',shoulder,elbow,.027,side+'UpArm'),('forearm',elbow,wrist,.026,side+'LowArm'),('thigh',hip,knee,.045,side+'Thigh'),('shin',knee,ankle,.032,side+'LowLeg')]:
  tube(side+' '+label+' inner tendon',[a,a.lerp(b,.18),a.lerp(b,.8),b],[r*.7,r,r*.8,r*.7],gold,bone,12)
  # Thin pink tissue visible through the dark outer cage.
  d=Vector((0,-r*.6,0));tube(side+' '+label+' membrane',[a+d,a.lerp(b,.5)+d,b+d],[r*.5,r*.7,r*.4],flesh,bone,10)
 for p,bone in [(elbow,side+'LowArm'),(knee,side+'LowLeg'),(ankle,side+'Foot'),(wrist,side+'Hand')]:ell(side+' exposed hinge',p,(.025,.024,.025),dark,bone)
 # Hip flanges and tapered thigh plates retain an open front tendon channel.
 x=hip.x
 blade(side+' hip blade',[(x+sgn*.02,0,1.08),(x+sgn*.055,-.01,1.02),(x+sgn*.05,-.02,.92),(x+sgn*.025,-.035,.85)],[.025,.055,.034,.001],shell,side+'Thigh')
 for sign in [-1,1]:
  a=hip+Vector((sign*.045,-.015,-.04));b=knee+Vector((sign*.024,-.007,.03))
  curve(side+' thigh rail',[a,a.lerp(b,.25)+Vector((sign*.009,-.025,0)),a.lerp(b,.7)+Vector((sign*.006,-.018,0)),b],.013,edge,side+'Thigh',22,10)
 blade(side+' knee cap',[(knee.x,knee.y-.026,knee.z+.045),(knee.x,knee.y-.045,knee.z),(knee.x,knee.y-.03,knee.z-.035)],[.018,.035,.007],shell,side+'LowLeg')
 # Shin carapaces: tapered greaves with a high raised central ridge.
 rows=[]
 for t,r in [(0,.032),(.16,.048),(.45,.039),(.76,.052),(1,.030)]:
  p=ankle.lerp(knee,t);rows.append((p.x,p.y,p.z,r,r*.72))
 loft(side+' greave',rows,shell,side+'LowLeg',16,.11)
 blade(side+' greave front shield',[(ankle.x,ankle.y-.041,ankle.z+.025),(ankle.x+sgn*.012,ankle.y-.05,ankle.z+.12),(knee.x+sgn*.014,knee.y-.04,knee.z-.14),(knee.x,knee.y-.038,knee.z-.045)],[.025,.042,.027,.005],shell,side+'LowLeg')
 curve(side+' greave keel',[ankle+Vector((0,-.035,0)),ankle.lerp(knee,.45)+Vector((sgn*.018,-.043,0)),knee+Vector((sgn*.02,-.04,-.04))],.009,edge,side+'LowLeg',22)
 for i in range(4):
  t=.25+i*.17;p=ankle.lerp(knee,t)
  curve(side+' greave swept ridge',[p+Vector((sgn*.041,.015,-.023)),p+Vector((sgn*.035,-.015,0)),p+Vector((0,-.045,.035))],.007,edge,side+'LowLeg',12)
 # Narrow feet and three forward claws.
 ell(side+' instep',(ankle.x,ankle.y-.038,.065),(.044,.08,.035),shell,side+'Foot')
 for k in range(3):
  x=ankle.x+(k-1)*.027
  tube(side+' toe claw',[(x,ankle.y-.08,.055),(x,ankle.y-.117,.031),(x+sgn*.006,ankle.y-.145,.025)],[.014,.012,.0005],gold,side+'Foot',8)
 # Open forearm lattice, not a solid glove.
 for phase in [0,pi]:
  pts=[]
  for i in range(25):
   t=i/24;p=elbow.lerp(wrist,t);a=phase+t*pi*2
   pts.append(p+Vector((.047*cos(a),.039*sin(a),0)))
  tube(side+' bracer helical rail',pts,.009,shell,side+'LowArm',8)
 for offset in [-1,1]:curve(side+' bracer edge',[elbow+Vector((offset*.035,0,-.015)),elbow.lerp(wrist,.5)+Vector((offset*.048,0,0)),wrist+Vector((offset*.027,0,.015))],.010,edge,side+'LowArm',18)
 curve(side+' upper arm armour',[shoulder+Vector((sgn*.022,-.015,-.02)),shoulder.lerp(elbow,.6)+Vector((sgn*.026,-.02,0)),elbow+Vector((sgn*.025,-.015,.02))],.013,shell,side+'UpArm',18)
 ell(side+' palm',wrist+Vector((0,0,-.035)),(.026,.019,.045),flesh,side+'Hand')
 for k in range(3):
  p=wrist+Vector(((k-1)*.018,-.004,-.05))
  curve(side+' long talon',[p,p+Vector((sgn*.005,-.008,-.035)),p+Vector((sgn*.003,-.022,-.075))],.006,edge,side+'Hand',12,7)

# Preserve actual DFM bind bases as well as names and hierarchy in the .blend.
arm=bpy.data.armatures.new('robot_body_a native skeleton');rig=bpy.data.objects.new('RIG - robot_body_a',arm);bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.object.mode_set(mode='EDIT')
for b in data['bones']:
 eb=arm.edit_bones.new(b['name']);m=(C@Matrix(b['basis'])).to_4x4();m.translation=J[b['name']];eb.matrix=m;eb.length=.065
for b in data['bones']:
 if b['parent'] and b['parent'] in arm.edit_bones:arm.edit_bones[b['name']].parent=arm.edit_bones[b['parent']]
bpy.ops.object.mode_set(mode='OBJECT');rig.show_in_front=True
for b in data['bones']:arm.bones[b['name']]['native_bind_3x4']=b['native_bind']
for ob in objects:
 mod=ob.modifiers.new('Robot skeleton binding','ARMATURE');mod.object=rig;ob.parent=rig
rig['source_dfm']=data['source'];rig['status']='Prototype rigid part weights; joint blending and FL animation validation pending'
# Readable collection layout.
for name,words in [('HEAD',('crown','beak','eye','brow','jaw','skull','auricular','hose')),('TORSO',('thoracic','abdominal','pelvic','mantle','flank','ventral','dorsal','neck','throat')),('LIMBS',())]:
 col=bpy.data.collections.new(name);bpy.context.scene.collection.children.link(col)
 for ob in objects:
  if any(w in ob.name for w in words) or (not words and ob.users_collection[0].name=='Collection'):
   for old in list(ob.users_collection):old.objects.unlink(ob)
   col.objects.link(ob)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100
scene.world.color=(.055,.055,.055);scene.view_settings.view_transform='AgX'
for loc,power,size in [((-3,-4,4),420,3),((3,-1,2.5),300,2.5),((1,3,3),550,2)]:
 bpy.ops.object.light_add(type='AREA',location=loc);ob=bpy.context.object;ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size;ob.rotation_euler=(Vector((0,0,1))-ob.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add();cam=bpy.context.object;scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.12
views=[('front',(0,-5,1.0),(0,0,.97),2.12),('side',(5,0,1.0),(0,0,.97),2.12),('back',(0,5,1.0),(0,0,.97),2.12),('three_quarter',(3,-5,2.2),(0,0,.98),2.12),('head',(1,-4,2.0),(0,0,1.69),.59)]
for name,loc,target,scale in views:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
# Save the working file in its front view, with rig selected for inspection.
cam.location=views[0][1];cam.rotation_euler=(Vector(views[0][2])-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2.12
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
stats={'mesh_objects':len(objects),'triangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),'robot_bones':len(arm.bones),'game_installed':False,'prototype':True,'weighting':'rigid pieces; organic joint blending still pending'}
(OUT/'report.json').write_text(json.dumps(stats,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'nomad_robot_prototype.blend'))
print(json.dumps(stats))
