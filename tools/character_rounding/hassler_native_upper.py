"""Step 01: native elite uniform, actual Reichman epaulettes, authored art panels."""
import sys,json,gzip,math,copy,hashlib,warnings
from pathlib import Path
warnings.filterwarnings('ignore',category=DeprecationWarning)
import bpy,bmesh,numpy as np
from mathutils import Vector,Matrix
from mathutils.geometry import tessellate_polygon,barycentric_transform
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(Path(__file__).parent))
from blender_workspace import configure
import hassler_build as native
from hassler_inspect import studio
configure('character_rounding')
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'step_01'
ART=Path('D:/Work/Meshy/Hassler1')

def dump(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
def material(name,color,rough=.65,metal=0.,texture=None):
    mat=bpy.data.materials.new(name);mat.use_nodes=True;mat.use_backface_culling=True
    bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1)
    bs.inputs['Roughness'].default_value=rough;bs.inputs['Metallic'].default_value=metal
    if texture:
        tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(texture,check_existing=True)
        mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    return mat
def weights(data):
    w=np.zeros((len(data['points']),len(data['bones'])))
    for i,row in enumerate(data['skin']):
        for k,v in row.items():w[i,int(k)]=v
    return w

def compact(data):
    """Keep only used native logical vertices, preserving their source mapping."""
    out=copy.deepcopy(data);used=sorted({i for g in data['groups'] for t in g['faces'] for i in t});mapping={j:i for i,j in enumerate(used)}
    for key in ('points','normals','uv','skin'):out[key]=[data[key][i] for i in used]
    for g in out['groups']:g['faces']=[[mapping[i] for i in t] for t in g['faces']]
    out['source_vertex_ids']=used;return out

def geometry(name,p,faces,uv,skin,mat,col,rig,names):
    me=bpy.data.meshes.new(name);me.from_pydata(p,[],faces);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);me.materials.append(mat)
    layer=me.uv_layers.new(name='Garment UV')
    for f in me.polygons:
        f.use_smooth=True
        for li in f.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
    native.add_skin(ob,np.array(skin),names,rig);return ob

class Surface:
    def __init__(self,data):
        self.p=np.array([native.C@Vector(p) for p in data['points']]);self.n=np.array([native.C@Vector(n) for n in data['normals']])
        self.w=weights(data);self.faces=[t for g in data['groups'] if g['name']!='rh_male_elite_4' for t in g['faces']]
        self.tree=BVHTree.FromPolygons(self.p.tolist(),self.faces,all_triangles=True)
    def sample(self,x,z,front=True):
        loc,no,ti,dist=self.tree.ray_cast(Vector((x,.5 if front else -.5,z)),Vector((0,-1 if front else 1,0)))
        if loc is None:raise ValueError(('Outside native torso',x,z,front))
        t=self.faces[ti];b=np.array(barycentric_transform(loc,*[Vector(self.p[i]) for i in t],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))))
        b=np.maximum(b,0);b/=b.sum();w=b@self.w[t];n=b@self.n[t];n/=np.linalg.norm(n)
        return np.array(loc),n,w
    def nearest_weights(self,p):
        loc,no,ti,dist=self.tree.find_nearest(Vector(p));t=self.faces[ti]
        b=np.array(barycentric_transform(loc,*[Vector(self.p[i]) for i in t],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))))
        b=np.maximum(b,0);b/=b.sum();w=b@self.w[t]
        w[w<.001]=0;idx=np.argsort(w)[:-4];w[idx]=0;return w/w.sum()

def clip_triangle(records,clip):
    # Each record carries the native position/normal/skin through a 2D cut.
    area=sum(clip[i][0]*clip[(i+1)%3][1]-clip[(i+1)%3][0]*clip[i][1] for i in range(3))
    if area<0:clip=clip[::-1]
    for a,b in zip(clip,clip[1:]+clip[:1]):
        def distance(r):return (b[0]-a[0])*(r[0][2]-a[1])-(b[1]-a[1])*(r[0][0]-a[0])
        new=[]
        for start,end in zip(records,records[1:]+records[:1]):
            da,db=distance(start),distance(end);inside_a=da>=-1e-9;inside_b=db>=-1e-9
            if inside_a:new.append(start)
            if inside_a!=inside_b:
                t=da/(da-db);new.append(tuple(x+(y-x)*t for x,y in zip(start,end)))
        records=new
        if len(records)<3:return []
    return records

def panel(name,contour,front,surface,mat,col,rig,names,offset=.0025,texture_kind='gold'):
    art_tris=tessellate_polygon([[Vector((x,z,0)) for x,z in contour]])
    points=[];uv=[];skin=[];faces=[];lookup={}
    xmin,xmax=min(p[0] for p in contour),max(p[0] for p in contour);zmin,zmax=min(p[1] for p in contour),max(p[1] for p in contour)
    def vertex(r):
        p,n,w=r
        # Constant depth across a connected panel avoids cracks at native
        # duplicated vertices with different authored shading normals.
        p=p+np.array([0,offset if front else -offset,0]);p=p.round(6)
        key=tuple(p)
        if key in lookup:return lookup[key]
        idx=len(points);lookup[key]=idx;points.append(p.tolist());w=w.copy();w[w<.001]=0;w[np.argsort(w)[:-4]]=0;w/=w.sum();skin.append(w)
        if texture_kind=='gold':uv.append((.50+(p[0]-xmin)/max(xmax-xmin,.001)*.42,.08+(p[2]-zmin)/max(zmax-zmin,.001)*.23))
        else:uv.append(((p[0]-xmin)/max(xmax-xmin,.001),(p[2]-zmin)/max(zmax-zmin,.001)))
        return idx
    for tri in surface.faces:
        pp=surface.p[tri];normal=np.cross(pp[1]-pp[0],pp[2]-pp[0])
        if normal[1]*(1 if front else -1)<1e-7 or pp[:,2].max()<zmin or pp[:,2].min()>zmax:continue
        if pp[:,0].max()<xmin or pp[:,0].min()>xmax:continue
        for art_tri in art_tris:
            clipped=clip_triangle([(surface.p[i],surface.n[i],surface.w[i]) for i in tri],[contour[t] if isinstance(t,int) else (t.x,t.y) for t in art_tri])
            if len(clipped)<3:continue
            polygon=[vertex(r) for r in clipped]
            for j in range(1,len(polygon)-1):
                f=(polygon[0],polygon[j],polygon[j+1])
                if len(set(f))==3 and np.linalg.norm(np.cross(np.array(points[f[1]])-points[f[0]],np.array(points[f[2]])-points[f[0]]))>1e-11:faces.append(f)
    assert faces,name
    ob=geometry(name,points,faces,uv,skin,mat,col,rig,names)
    # A shallow edge, not a separate heavy armour shell.
    solid=ob.modifiers.new('Thin garment edge','SOLIDIFY');solid.thickness=.0014;solid.offset=0
    ob['construction']='2D authored art contour clipped onto actual native torso triangles; native weights interpolated'
    ob['art_contour_xz']=json.dumps(contour);return ob

def collar(col,rig,names,surface,gray,dark):
    # Two explicit rails: collar attachment and turned-out upper edge.
    # The wearer-left end extends lower across the chest, as in the art.
    lower=np.array([[-.055,.147,.464],[-.105,.101,.506],[-.108,.027,.543],[-.086,-.075,.560],
                    [0,-.105,.568],[.086,-.075,.560],[.108,.027,.543],[.095,.111,.516],[.041,.148,.516]])
    upper=np.array([[-.018,.159,.493],[-.099,.110,.564],[-.110,.027,.626],[-.095,-.070,.650],
                    [0,-.095,.663],[.095,-.070,.650],[.110,.027,.626],[.095,.116,.575],[.020,.154,.542]])
    def catmull(points,t):
        i=min(int(t),len(points)-2);f=t-i;a=points[max(i-1,0)];b=points[i];c=points[i+1];d=points[min(i+2,len(points)-1)]
        return .5*((2*b)+(-a+c)*f+(2*a-5*b+4*c-d)*f*f+(-a+3*b-3*c+d)*f*f*f)
    ps=[];uv=[];skin=[];faces=[];sections=49;rows=5
    for i in range(sections):
        t=i/(sections-1)*(len(lower)-1);a=catmull(lower,t);b=catmull(upper,t)
        for j in range(rows):
            f=j/(rows-1);p=a*(1-f)+b*f
            outward=np.array([p[0],p[1],0.]);outward/=max(np.linalg.norm(outward),1e-6)
            p+=outward*(.004*math.sin(math.pi*f));ps.append(p);uv.append((i/(sections-1),f));skin.append(surface.nearest_weights(p))
    for i in range(sections-1):
        for j in range(rows-1):
            a=i*rows+j;faces.append((a,a+rows,a+rows+1,a+1))
    ob=geometry('01 Collar — asymmetric folded cloth',ps,faces,uv,skin,gray,col,rig,names)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    # Ensure the exterior faces outward before giving the cloth its thickness.
    normal=sum((f.normal for f in ob.data.polygons[len(ob.data.polygons)//2-2:len(ob.data.polygons)//2+2]),Vector())
    if normal.y>0:
        bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
    solid=ob.modifiers.new('Cloth thickness 2 mm','SOLIDIFY');solid.thickness=.002;solid.offset=-1
    bevel=ob.modifiers.new('Soft folded edge 1 mm','BEVEL');bevel.width=.001;bevel.segments=2;bevel.limit_method='ANGLE';bevel.angle_limit=.55
    ob['construction']='Hand-authored continuous fold; Wilham collar construction reference; no Meshy geometry'
    return ob

def epaulettes(data,col,rig,names):
    d=copy.deepcopy(data);d['groups']=[g for g in d['groups'] if g['name']=='reich 2']
    p=np.array(d['points'])
    for g in d['groups']:g['faces']=[t for t in g['faces'] if all(p[i,1]>.49 and abs(p[i,0])>.14 for i in t)]
    assert sum(len(g['faces']) for g in d['groups'])>100
    d=compact(d)
    ob=native.native_mesh(d,'02 Epaulettes — Reichman source geometry',col)
    ob['native_vertex_map']=d['source_vertex_ids']
    for v in ob.data.vertices:
        v.co.x+=.012 if v.co.x>0 else -.012
        v.co.z+=.015
    src_names=[b['name'] for b in d['bones']];source=weights(d);w=np.zeros((len(source),len(names)))
    for i,name in enumerate(src_names):w[:,names.index(name)]=source[:,i]
    native.add_skin(ob,w,names,rig)
    underside=material('Epaulette backing — grey prototype cloth',(.14,.16,.15),.72)
    ob.data.materials.append(underside)
    shell=ob.modifiers.new('Close original shoulder sheet underside','SOLIDIFY');shell.thickness=.0025;shell.offset=-1;shell.material_offset=1;shell.material_offset_rim=1
    ob['source_sha256']=data['sha256'];ob['source']='rh_reichman_body Mesh0 shoulder faces; native UVs/normals; fitted +12 mm outward and +15 mm upward'
    return ob

def cord(col,rig,names,surface,gold):
    controls=np.array([[-.181,.534],[-.181,.363],[-.095,.361],[-.041,.446]])
    ps=[];uv=[];skin=[];faces=[];steps=30;sides=6
    centers=[];ws=[]
    for i in range(steps):
        t=i/(steps-1);q=(1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3]
        p,n,w=surface.sample(q[0],q[1]);centers.append(p+n*.009);ws.append(w)
    for i,p in enumerate(centers):
        tangent=Vector(centers[min(i+1,steps-1)]-centers[max(i-1,0)]).normalized();u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u).normalized()
        for k in range(sides):
            a=k*2*math.pi/sides;ps.append(p+np.array(u)*math.cos(a)*.0023+np.array(v)*math.sin(a)*.0023);uv.append((i/(steps-1),k/sides));skin.append(ws[i])
    for i in range(steps-1):
        for k in range(sides):a=i*sides+k;b=i*sides+(k+1)%sides;faces.append((a,b,b+sides,a+sides))
    return geometry('06 Aiguillette — single structural cord',ps,faces,uv,skin,gold,col,rig,names)

def main():
    OUT.mkdir(parents=True,exist_ok=True);bpy.ops.wm.read_factory_settings(use_empty=True);configure('character_rounding')
    data=native.load('body');ep=native.load('epaulettes');wilham=json.loads(gzip.decompress((TOP/'source/wilham.json.gz').read_bytes()))
    edit=native.collection('EDIT — native costume upper study');rigcol=native.collection('RIG — native elite body')
    context=native.collection('CONTEXT — unchanged head and hands');archive=native.collection('ARCHIVE — original references disabled')
    rig=native.rig_native(data,rigcol);rig.location.z=.975662;names=[b['name'] for b in data['bones']]
    original=native.native_mesh(data,'Original rh_male_elite body',archive);original.location.z=.975662
    ref=native.native_mesh(wilham,'Wilham reference — collar construction',archive);ref.location=(.9,0,.975662)
    full=native.native_mesh(ep,'Reichman reference — native shoulder details',archive);full.location=(-.9,0,.975662)
    source=np.array(data['points']);base=copy.deepcopy(data);neck=copy.deepcopy(data);removed=[]
    # Both sides of the native hanging shoulder plates span two materials.
    # Select their actual connected components, not only one material group.
    keys=[tuple(p.round(5)) for p in source];adj={}
    for g in data['groups']:
        for t in g['faces']:
            for i in t:adj.setdefault(keys[i],set()).update(keys[j] for j in t)
    seeds={keys[i] for g in data['groups'] if g['name']=='rh_male_elite_4' for t in g['faces'] for i in t}
    armour=set();todo=list(seeds)
    while todo:
        k=todo.pop()
        if k in armour:continue
        armour.add(k);todo.extend(adj[k]-armour)
    for gi,g in enumerate(base['groups']):
        native_faces=g['faces'];keep=[];cut=[]
        for t in native_faces:
            p=source[t].mean(0)
            is_neck=p[1]>.548 and abs(p[0])<.136
            if is_neck:cut.append(t)
            elif keys[t[0]] not in armour:keep.append(t)
        g['faces']=keep;neck['groups'][gi]['faces']=cut;removed.extend(cut)
    base=compact(base);neck=compact(neck)
    ob=native.native_mesh(base,'00 Native elite — original torso and sleeves',edit);native.add_skin(ob,weights(base),names,rig);ob['native_vertex_map']=base['source_vertex_ids']
    dark=material('Hassler black neck insert',(.012,.018,.016),.9)
    insert=native.native_mesh(neck,'00 Native neck insert — recoloured black',edit);insert.data.materials.clear();insert.data.materials.append(dark)
    attachment={tuple(np.round(p,5)) for p in base['points']}
    for v,p in zip(insert.data.vertices,neck['points']):
        if tuple(np.round(p,5)) not in attachment:v.co.x*=.72;v.co.y*=.72
    insert['construction']='Original native collar inset radially inside grey fold; attachment vertices remain pinned to native torso'
    for f in insert.data.polygons:f.material_index=0
    native.add_skin(insert,weights(neck),names,rig)
    surface=Surface(base)
    gray=material('Hassler grey collar cloth',(.26,.285,.27),.72)
    red=material('Hassler red lapel cloth',(.35,.025,.014),.77)
    pattern=material('Reichman ornamental gold — temporary cloth crop',(.5,.3,.07),.58,.15,ep['groups'][1]['texture'])
    gold=material('Hassler gold braid',(.5,.31,.065),.46,.45)
    epaulettes(ep,edit,rig,names);collar(edit,rig,names,surface,gray,dark)
    panel('00 Black chest insert — covers native neck clasp',[(.075,.505),(.095,.579),(-.095,.579),(-.08,.505),(0,.468)],True,surface,dark,edit,rig,names,.004,'plain')
    panel('03 Chest gold facing',[(.108,.183),(.133,.435),(.022,.463),(-.063,.490),(-.126,.450),(-.105,.183)],True,surface,pattern,edit,rig,names)
    panel('04 Red asymmetrical lapel',[(.023,.450),(.136,.432),(.187,.535),(.091,.568),(.043,.521)],True,surface,red,edit,rig,names,.004,'plain')
    panel('05 Left shoulder gold facing',[(-.193,.544),(-.147,.562),(-.075,.493),(-.127,.442),(-.163,.493)],True,surface,pattern,edit,rig,names)
    panel('07 Back Y facing',[(-.187,.536),(-.121,.557),(0,.474),(.121,.557),(.187,.536),(.050,.403),(.041,.184),(-.041,.184),(-.050,.403)],False,surface,pattern,edit,rig,names)
    cord(edit,rig,names,surface,gold)
    for kind,hp,bone,label in [('head','hp_head','Body_Head','Hassler head'),('left_hand','hp_left b','LHand','Left glove'),('right_hand','hp_right b','RHand','Right glove')]:native.attached(native.load(kind),data,label,hp,bone,context,rig)
    archive.hide_viewport=archive.hide_render=True
    # References remain available inside the file without entering renders.
    refs=native.collection('REFERENCE ART — disabled')
    for filename,x in [('hassler1.png',1.4),('hassler2.png',1.8),('wilham.JPG',2.3)]:
        obj=bpy.data.objects.new(filename,None);refs.objects.link(obj);obj.empty_display_type='IMAGE';obj.data=bpy.data.images.load(str(ART/filename),check_existing=True);obj.empty_display_size=.8;obj.location=(x,0,1.4)
    refs.hide_viewport=refs.hide_render=True
    native.pose_action(rig);scene=bpy.context.scene;cam=studio(scene);scene.cycles.samples=32
    scene.render.resolution_x=1000;scene.render.resolution_y=1000
    for label,direction,target,scale in [('front',(0,1,0),(0,0,1.47),1.02),('three_quarter',(.65,1,.12),(0,0,1.47),1.02),
             ('back',(0,-1,.03),(0,0,1.47),1.02),('side',(1,0,.02),(0,0,1.47),1.02),('full',(0,1,.02),(0,0,.94),2.05)]:
        d=Vector(direction).normalized();cam.location=Vector(target)+d*4;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
        scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)
    d=Vector((.35,1,.08)).normalized();cam.location=Vector((0,0,1.47))+d*4;cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.02
    native.activate(rig)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    report={'approach':'native body reconstruction; no Meshy mesh import','step':'01 upper costume visual prototype',
            'source_body':data['sha256'],'source_epaulettes':ep['sha256'],'native_faces_retained':sum(len(g['faces']) for g in base['groups']),
            'neck_faces_recoloured':len(removed),'native_lower_body_unchanged':True,'native_head_hands_unchanged':True,'installed':False,
            'objects':{ob.name:{'vertices':len(ob.data.vertices),'triangles':sum(len(f.vertices)-2 for f in ob.data.polygons)} for ob in edit.objects if ob.type=='MESH'},
            'textures':'native textures retained; new collar and red lapel use prototype material colours; gold ornaments reuse Reichman source crop'}
    dump(OUT/'report.json',report);text=bpy.data.texts.new('README — native upper prototype');text.write(json.dumps(report,indent=2,ensure_ascii=False))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True);print(json.dumps(report),flush=True)

if __name__=='__main__':main()
