"""Contour-cut relief in the six user-selected materials. No uniform subdivision."""
from pathlib import Path
import json,math,ast,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/'tools/base_interiors/relief_v2.py').read_text()
VERSION=sys.argv[sys.argv.index('--output-version')+1] if '--output-version' in sys.argv else 'prototype_v3'
exec(compile(source.split('added=[]')[0].replace('prototype_v2',VERSION),__file__,'exec'))
tree=ast.parse(source)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='placements'],type_ignores=[]),__file__,'exec'))
def rect(a,b,c,d):return np.array([[a,b],[c,b],[c,d],[a,d]])
def circle(x,y,r,n=64):return np.array([[x+r*math.cos(t),y+r*math.sin(t)] for t in np.linspace(0,2*math.pi,n,endpoint=False)])
def polygon(points):return np.array(points,float)
features={}
height_profiles={}
def add(name,label,poly,depth,inset=.9):
 if np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1))<0:poly=poly[::-1]
 features.setdefault(name,[]).append((label,poly,depth,inset))
for name in ('r_bar_01','r_bar_02'):
 # These compartments already have native depth and props: never carve them twice.
 for x in (.174,.546,.918):
  for y0,y1 in ((.25,.602),(.632,.89)):add(name,'Panel divider',rect(x,y0,x+.009,y1),.035,.68)
 add(name,'Shelf dividing edge',rect(.19,.611,.9,.621),.04,.7)
add('r_bar_14','Upper trapezoid recess',polygon([[.535,.073],[.937,.073],[.937,.423],[.715,.423]]),-.09,.88)
add('r_bar_14','Lower trapezoid recess',polygon([[.745,.49],[.939,.49],[.939,.735],[.842,.735]]),-.08,.87)
add('r_bar_14','Long structural rib',polygon([[.445,.003],[.476,.003],[.918,.997],[.884,.997]]),.065,.78)
# Left ornament: separate pockets follow its stepped pattern rather than its highlights.
add('detailmap_r_bar_10','Upper curved niche',polygon([[.047,.016],[.274,.016],[.27,.065],[.254,.117],[.22,.165],[.179,.205],[.046,.212]]),-.16,.92)
add('detailmap_r_bar_10','Lower tall niche',polygon([[.145,.45],[.274,.45],[.274,.781],[.236,.818],[.145,.818]]),-.12,.9)
for a,c in ((.309,.396),(.419,.497)):
 add('detailmap_r_bar_10','Tall inset panel',rect(a,.113,c,.733),-.085,.88)
for a,b,c,d in ((.031,.22,.228,.278),(.035,.31,.09,.392),(.1,.326,.15,.411),(.159,.344,.202,.387)):
 add('detailmap_r_bar_10','Ornament channel',rect(a,b,c,d),-.065,.8)
# r_bar_04: rounded vent mouths, deep mechanical rings, sheet-metal ribs.
for x in (.074,.215,.355,.495,.635,.775,.915):
 # Rounded rectangle contour: four quarter-circles, not a sampled height grid.
 points=[]
 for cx,cy,start in ((x+.032,.069,-90),(x+.032,.091,0),(x-.032,.091,90),(x-.032,.069,180)):
  for t in np.linspace(start,start+90,9)[:-1]:points.append([cx+.012*math.cos(math.radians(t)),cy+.012*math.sin(math.radians(t))])
 add('detailmap_r_bar_04','Rounded ventilation slot',polygon(points),-.12,.82)
for x,y,r in ((.538,.39,.079),(.814,.39,.077)):add('detailmap_r_bar_04','Circular machinery recess',circle(x,y,r),-.13,.88)
for x in (.435,.568,.704,.841,.951):add('detailmap_r_bar_04','Upright fascia rib',rect(x-.004,.188,x+.005,.268),.055,.65)
add('detailmap_r_bar_04','Diagonal brace',polygon([[.205,.44],[.208,.412],[.428,.284],[.456,.284]]),.085,.83)
for v in (.144,.499,.751):add('detailmap_r_bar_04','Horizontal reinforcing edge',rect(.014,v,.981,v+.013),.06,.8)
for x in (.15,.27,.39,.51,.63,.75,.87):add('detailmap_r_bar_04','Red panel folded edge',rect(x,.515,x+.011,.729),.035,.7)
# Window grille: each drawn bar follows its own convex window bay. Avoid the black atlas gaps.
for pts in ([[.13,.245],[.251,.199],[.327,.332],[.219,.394]],[[.261,.404],[.347,.348],[.428,.438],[.357,.523]],[[.416,.506],[.482,.46],[.56,.57],[.487,.62]],[[.595,.505],[.747,.502],[.751,.627],[.585,.627]],[[.805,.485],[.887,.456],[.97,.583],[.864,.626]]):
 add('r_bar_15','Window bay inset',polygon(pts),-.085,.94)
add('r_bar_15','Round metal boss',circle(.688,.38,.083),.07,.88)
add('r_bar_15','Upper frame moulding',rect(.443,.213,.978,.234),.065,.82)
# Continuous mouldings traced along the painted arch, rather than generic rings.
def wall_path(points,width,height,tag,material='r_bar_15'):
 pts=np.array(points,float);dense=[]
 # Catmull-Rom interpolation follows the traced line with a continuous tangent.
 ext=np.vstack((pts[0],pts,pts[-1]))
 for i in range(1,len(ext)-2):
  p0,p1,p2,p3=ext[i-1:i+3]
  for t in np.linspace(0,1,5,endpoint=False):dense.append(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
 dense=np.array(dense+[pts[-1]]);tangent=np.gradient(dense,axis=0);tangent/=np.linalg.norm(tangent,axis=1)[:,None];side=np.column_stack((-tangent[:,1],tangent[:,0]))
 offsets=(-1,-.65,.65,1);heights=(0,height,height,0)
 for i in range(len(dense)-1):
  for j in range(3):
   poly=np.array([dense[i]+side[i]*width*offsets[j],dense[i+1]+side[i+1]*width*offsets[j],dense[i+1]+side[i+1]*width*offsets[j+1],dense[i]+side[i]*width*offsets[j+1]])
   label=f'Wall moulding {tag}_{i}_{j}';height_profiles[label]=(poly,np.array([heights[j],heights[j],heights[j+1],heights[j+1]]));add(material,label,poly,height,1)
if VERSION=='prototype_v6':
 wall_path([[.035,.23],[.078,.39],[.19,.56],[.37,.68],[.58,.729],[.78,.73],[.98,.668]],.008,.085,'inner')
 wall_path([[.014,.48],[.13,.64],[.30,.78],[.50,.87],[.72,.904],[.97,.856]],.009,.095,'outer')
 for p in ([[.31,.696],[.42,.75],[.385,.826],[.26,.757]],[[.455,.765],[.628,.80],[.615,.889],[.438,.849]],[[.677,.80],[.831,.779],[.861,.862],[.693,.895]],[[.862,.763],[.975,.716],[.99,.807],[.893,.85]]):
  add('r_bar_15','Arch panel recess',polygon(p),-.075,.88)
 for x,y in ((.355,.752),(.542,.823),(.766,.833),(.928,.787)):
  add('r_bar_15','Handle inset',polygon([[x-.022,y-.011],[x+.024,y-.011],[x+.025,y+.008],[x-.018,y+.015]]),-.045,.75)
# The continuous seating fascia alternates r_bar_03 and r_bar_04.
# Process every native triangle using either atlas, including mirrored UV instances.
for x,y,r in ((.633,.11,.084),(.6,.342,.075),(.946,.345,.064),(.833,.565,.075)):
 add('detailmap_r_bar_03','Circular machinery recess',circle(x,y,r),-.13,.88)
for a,b,c,d in ((.007,.008,.027,.415),(.39,.008,.414,.415),(.008,.428,.46,.444),(.439,.452,.46,.817),(.476,.208,.985,.221),(.48,.429,.985,.443),(.48,.648,.985,.665)):
 add('detailmap_r_bar_03','Mechanical frame edge',rect(a,b,c,d),.055,.8)
for y in (.068,.119,.169):add('detailmap_r_bar_03','Internal grille rib',rect(.566,y,.70,y+.008),.055,.72)
# Additional flat architectural materials identified by the user.
add('r_bar_28','Central circular recess',circle(.478,.537,.102),-.18,.86)
for a,b,c,d in ((.16,.064,.39,.077),(.54,.064,.754,.077),(.16,.192,.39,.205),(.54,.192,.754,.205),(.012,.737,.435,.748),(.536,.737,.98,.748),(.012,.84,.98,.851)):
 add('r_bar_28','Panel joint channel',rect(a,b,c,d),-.05,.78)
for x in (.028,.141,.82,.931):
 add('r_bar_28','Side vent slot',rect(x,.50,x+.055,.548),-.095,.8)
for x in (.012,.093,.185,.267,.35,.433,.515,.596,.677,.759,.84,.92):
 add('r_bar_28','Lower vent slot',rect(x,.859,min(x+.052,.986),.891),-.085,.8)
for x,y in ((.238,.105),(.238,.246),(.687,.105),(.687,.246)):
 add('r_bar_28','Handle pocket',polygon([[x-.056,y-.025],[x+.045,y-.025],[x+.05,y+.008],[x+.015,y+.035],[x-.026,y+.026]]),-.08,.8)
add('r_bar_22','Upper arched recess',circle(.495,-.045,.345),-.14,.92)
for y in (.442,.463,.484):add('r_bar_22','Horizontal moulding',rect(.02,y,.975,y+.009),.045,.75)
for x in (.007,.027,.047,.939,.959,.979):add('r_bar_22','Vertical border flute',rect(x,.008,x+.007,.407),.035,.75)
add('r_bar_22','Lower inset left',rect(.197,.522,.432,.94),-.06,.93)
add('r_bar_22','Lower inset right',rect(.714,.522,.972,.94),-.06,.93)
add('r_bar_22','Central raised plate',rect(.453,.405,.552,.502),.065,.85)
# Thin pipe-shaped relief on the atlas, with narrow contour bands forming a curved profile.
# Only the painted pipe bands are split; surrounding wall triangles stay coarse.
for cx,y0,y1 in ((.301,.25,.734),(.424,.245,.984),(.541,.255,.973)):
 for j in range(12):
  a=-1+2*j/12;b=-1+2*(j+1)/12;h=.075*math.sqrt(max(0,1-((a+b)/2)**2))
  for ya,yb in ((y0,y0+.012),(y0+.012,y1-.012),(y1-.012,y1)):
   add('r_bar_05','Long pipe relief',rect(cx+a*.029,ya,cx+b*.029,yb),h,1)
for cx in (.301,.424,.541):add('r_bar_05','Pipe socket recess',circle(cx,.193,.031,48),-.055,.82)
for a,b,c,d in ((.013,.084,.213,.097),(.013,.846,.232,.86),(.02,.922,.233,.934)):
 add('r_bar_05','Panel edge',rect(a,b,c,d),.04,.8)

if VERSION=='prototype_v7':
 # Replace the estimated arch features, not layer another version on top.
 features['r_bar_15']=[]
 for points in (
  [[9,450],[197,594],[127,670],[3,541]],
  [[233,657],[416,738],[378,826],[163,719]],
  [[496,760],[676,784],[670,887],[438,849]],
  [[735,785],[937,743],[973,842],[735,886]]):
  add('r_bar_15','Traced painted panel field',polygon(points)/1024,-.055,.96)
 wall_path((np.array([[63,380],[131,509],[245,641],[428,719],[700,767],[853,752],[1010,700]])/1024).tolist(),.004,.05,'traced_inner')
 wall_path((np.array([[17,628],[200,780],[433,910],[667,963],[850,955],[1010,906]])/1024).tolist(),.005,.06,'traced_outer')
 for points in (
  [[790,758],[886,692],[940,758],[790,852]],
  [[910,671],[1005,592],[1005,691],[955,730]]):
  add('r_bar_09','Traced painted panel field',polygon(points)/1024,-.055,.96)
 wall_path((np.array([[787,742],[847,696],[910,632],[961,562],[995,487],[1006,412]])/1024).tolist(),.004,.05,'right_inner','r_bar_09')
 wall_path((np.array([[790,891],[860,858],[926,817],[986,771],[1008,748]])/1024).tolist(),.005,.06,'right_outer','r_bar_09')

if VERSION=='prototype_v8':
 registered=json.loads((OUT/'registered_features.json').read_text())
 for material,entries in registered.items():
  features[material]=[]
  for f in entries:
   poly=np.array(f['uv']);add(material,f['label'],poly,f['depth'],f['inset'])
   if 'heights' in f:height_profiles[f['label']]=(poly,np.array(f['heights']))

EPS=1e-9
def signed(p,a,b):return (b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0])
def clip(poly,a,b,inside=True):
 if len(poly)==0:return []
 out=[];prev=poly[-1];dp=signed(prev,a,b)*(1 if inside else -1)
 for cur in poly:
  dc=signed(cur,a,b)*(1 if inside else -1)
  if (dc>=-EPS)!=(dp>=-EPS):out.append(prev+(cur-prev)*(dp/(dp-dc)))
  if dc>=-EPS:out.append(cur)
  prev,dp=cur,dc
 return out
def intersect(poly,boundary):
 result=list(poly)
 for a,b in zip(boundary,np.roll(boundary,-1,axis=0)):
  result=clip(result,a,b)
  if len(result)<3:return []
 return result
def area(poly):
 if len(poly)<3:return 0
 p=np.array(poly);return abs(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))*.5
replacements={};counts={};hits={};preview_targets={};native_exports={}
for index,batch in enumerate(data['batches']):
 name=data['materials'][batch['material']]['name'].split('.')[0].lower()
 if name not in features:continue
 verts=[];uvs=[];uvs1=[];faces=[];normals=[];hit={}
 def emit(poly,t):
  if area(poly)<1e-10:return
  poly=np.array(poly);uv=t[:,6:8];mat=np.vstack((uv.T,np.ones(3)))
  if label in height_profiles and poly.shape[1]>2:
   q,z=height_profiles[label]
   for row in poly:
    for ids in ((0,1,2),(0,2,3)):
     w=np.linalg.solve(np.vstack((q[list(ids)].T,np.ones(3))),np.r_[row[:2],1])
     if min(w)>-1e-5:row[2]=w@z[list(ids)];break
  if name=='r_bar_05' and label=='Long pipe relief' and poly.shape[1]>2:
   # Shared analytic profile at strip boundaries: no stepped heights or cracks.
   centers=np.array([.301,.424,.541]);cx=centers[np.argmin(abs(centers-poly[:,0].mean()))]
   poly[:,2]=.075*np.sqrt(np.maximum(0,1-((poly[:,0]-cx)/.029)**2))
   y0,y1={.301:(.25,.734),.424:(.245,.984),.541:(.255,.973)}[float(cx)]
   poly[:,2]*=np.clip(np.minimum((poly[:,1]-y0)/.012,(y1-poly[:,1])/.012),0,1)
  weights=np.linalg.solve(mat,np.vstack((poly[:,:2].T,np.ones(len(poly))))).T
  pos=weights@t[:,:3];nn=weights@t[:,3:6];nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9)
  if poly.shape[1]>2:pos+=nn*poly[:,2,None]
  start=len(verts);verts.extend([convert(p) for p in pos]);uvs.extend(poly[:,:2])
  if batch['stride']==10:uvs1.extend(weights@t[:,8:10])
  for k in range(1,len(pos)-1):
   f=(start,start+k,start+k+1)
   if np.dot(np.cross(pos[k]-pos[0],pos[k+1]-pos[0]),nn.mean(0))<0:f=f[::-1]
   faces.append(f)
   if poly.shape[1]<3 or np.ptp(poly[:,2])<1e-8:
    ids=[i-start for i in f];normals.extend([convert(nn[i]) for i in ids])
   else:
    p=np.array([verts[i] for i in f]);fn=np.cross(p[1]-p[0],p[2]-p[0]);fn/=max(np.linalg.norm(fn),1e-9);normals.extend([fn]*3)
 for t in np.array(batch['vertices']).reshape(-1,3,batch['stride']):
  uv=t[:,6:8].copy()
  if area(uv)<1e-10:
   # Degenerate UV triangles remain native, with no relief.
   start=len(verts);verts.extend([convert(p) for p in t[:,:3]]);uvs.extend(uv);f=(start,start+1,start+2)
   if batch['stride']==10:uvs1.extend(t[:,8:10])
   if np.dot(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]),t[:,3:6].mean(0))<0:f=f[::-1]
   faces.append(f);normals.extend([convert(t[i-start,3:6]) for i in f]);continue
  if signed(uv[2],uv[0],uv[1])<0:uv=uv[::-1]
  remaining=[list(np.column_stack((uv,np.zeros(3))))]
  for label,outer,depth,scale in features[name]:
   if name=='r_bar_05' and label in ('Long pipe relief','Pipe socket recess'):
    nn=t[:,3:6];nn=nn/np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-9)
    if np.min(nn@nn.T)<.98:continue # native curved geometry: do not add relief twice
   if area(intersect(outer,uv))<1e-9:continue
   new_remaining=[]
   for piece in remaining:
    if area(intersect(piece,outer))<1e-10:new_remaining.append(piece);continue
    rest=piece
    for a,b in zip(outer,np.roll(outer,-1,axis=0)):
     outside=clip(rest,a,b,False)
     if area(outside)>1e-10:new_remaining.append(outside)
     rest=clip(rest,a,b)
     if len(rest)<3:break
   remaining=new_remaining
   inner=outer.mean(0)+(outer-outer.mean(0))*scale
   emit(intersect(np.column_stack((inner,np.full(len(inner),depth))),uv),t)
   for j in range(len(outer)):
    k=(j+1)%len(outer)
    sector=np.array([[*outer[j],0],[*outer[k],0],[*inner[k],depth],[*inner[j],depth]])
    emit(intersect(sector,uv),t)
   hit[label]=hit.get(label,0)+1
  for piece in remaining:emit(piece,t)
 me=bpy.data.meshes.new(name+'_contour_relief');me.from_pydata(verts,[],faces);me.update();layer=me.uv_layers.new(name='Native UV0')
 for loop in me.loops:layer.data[loop.index].uv=(uvs[loop.vertex_index][0],1-uvs[loop.vertex_index][1])
 for poly in me.polygons:poly.use_smooth=True
 me.normals_split_custom_set(normals)
 # Export both original UV sets from the same source-triangle barycentrics.
 # Never infer detail-map UVs from the already displaced Blender positions.
 ids=np.asarray(faces).ravel();p=np.asarray(verts)[ids];n=np.asarray(normals)
 native_exports[index]=np.column_stack((p[:,0],p[:,2],-p[:,1],n[:,0],n[:,2],-n[:,1],np.asarray(uvs)[ids],
                                       np.asarray(uvs1)[ids] if uvs1 else np.empty((len(ids),0)))).reshape(-1,3,batch['stride'])
 if uvs1:
  layer1=me.uv_layers.new(name='Native UV1')
  for loop in me.loops:layer1.data[loop.index].uv=(uvs1[loop.vertex_index][0],1-uvs1[loop.vertex_index][1])
  me.uv_layers.active_index=0
 ob=bpy.data.objects.new(name+'_contour_relief',me);bpy.context.collection.objects.link(ob);me.materials.append(mats[batch['material']]);replacements[index]=ob;counts[name]=len(faces);hits[name]=hit
 features_for_camera=features[name]
 preferred={'r_bar_14':0,'detailmap_r_bar_10':0,'detailmap_r_bar_04':7,'detailmap_r_bar_03':0,'r_bar_15':0,'r_bar_09':0,'r_bar_01':0,'r_bar_02':0,'r_bar_05':0,'r_bar_22':0,'r_bar_28':0}[name]
 camera_outline=rect(.27,.25,.57,.98) if name=='r_bar_05' else features_for_camera[preferred][1]
 target=camera_outline.mean(0);options=list(placements(batch,target))
 if not options:
  ts=np.array(batch['vertices']).reshape(-1,3,batch['stride']);t=max(ts,key=lambda t:np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3])));target=t[:,6:8].mean(0);options=list(placements(batch,target))
 if options:preview_targets[name]=(index,max(options,key=lambda q:np.linalg.norm(q[1])),camera_outline)

def toggle(mode,only=None):
 for index,ob in enumerate(objects):ob.hide_render=(only is not None and index!=only) or (mode=='after' and index in replacements)
 for index,ob in replacements.items():ob.hide_render=mode=='before' or (only is not None and index!=only)
views={'overview':((-11,7,10),(0,4,0),65),'counter':((-7,3.6,5),(0,2,-.6),65),'seating_fascia':((1,6,-18),(1,1,-4.85),72)}
for mode in ('before','after'):
 toggle(mode)
 for name,args in views.items():shot(mode+'_'+name,*args)
clay=bpy.data.materials.new('Neutral relief inspection');clay.use_nodes=True;clay.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=(.24,.28,.31,1);clay.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.72
for name,(index,(center,basis,normal),outline) in preview_targets.items():
 if VERSION=='prototype_v8':continue # whole-wall and registration views are generated after reopening
 size=max(np.linalg.norm((outline-outline.mean(0))@basis,axis=1).max()*2,.6);distance=size*1.5
 position=center+normal*distance+basis[0]/np.linalg.norm(basis[0])*distance*.28
 for mode in ('before','after'):
  toggle(mode,index)
  for style in ('texture','clay'):
   scene.view_layers[0].material_override=clay if style=='clay' else None
   shot(name+'_'+style+'_'+mode,position,center,56)
scene.view_layers[0].material_override=None;toggle('after');shot('after_overview',*views['overview'])
# Originals belong to an explicitly disabled archive, not to the active viewport.
archive=bpy.data.collections.new('ARCHIVE - original replaced surfaces - disabled');scene.collection.children.link(archive)
for index in replacements:
 ob=objects[index]
 for collection in list(ob.users_collection):collection.objects.unlink(ob)
 archive.objects.link(ob);ob.hide_render=True;ob.hide_set(True)
archive.hide_render=True;archive.hide_viewport=True
for ob in replacements.values():ob.hide_render=False;ob.hide_set(False)
assert all(objects[i].hide_render and objects[i].hide_get() for i in replacements)
stats={'source_triangles':sum(b['triangles'] for b in data['batches']),'result_triangles':sum(counts.values())+sum(b['triangles'] for i,b in enumerate(data['batches']) if i not in replacements),'material_triangles':counts,'feature_hits':hits,'changed_batches':list(replacements),'installed':False}
(OUT/'prototype_stats.json').write_text(json.dumps(stats,indent=2));(OUT/'feature_contours.json').write_text(json.dumps({n:[{'label':l,'uv':p.tolist(),'depth':d,'inset':s} for l,p,d,s in fs] for n,fs in features.items()},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bismarck_material_relief.blend'))
