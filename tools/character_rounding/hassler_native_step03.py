"""An integrated Hassler tunic-vest: one sewn shell, shoulder yoke and collar.

Scrote supplies the volume reference; art supplies the hand-authored cut lines.
This is an offline editable visual iteration, not a DFM installer.
"""
import sys,json,gzip,math,hashlib,copy,warnings
from pathlib import Path
warnings.filterwarnings('ignore',category=DeprecationWarning)
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step02 as step2
from hassler_garment_mesh import pattern
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_03';PARENT=TOP/'step_02/hassler_native_upper.blend'
R=.18;H=.4;TRIM_RADIUS=.0015

def smooth(a,b,x):
    t=float(np.clip((x-a)/(b-a),0,1));return t*t*(3-2*t)
def torso_weights(surface,names,p,collar=False):
    w=surface.nearest_weights(np.array(p)).copy()
    # A sleeveless vest stays with the rib cage/clavicles; nearest-surface skin
    # transfer alone incorrectly catches upper-arm weights at the armhole.
    for side in ('L','R'):
        target=names.index(side+'CollarBone') if p[2]>.50 else names.index('Spine3')
        for name in (side+'UpArm',side+'LowArm',side+'Hand'):
            idx=names.index(name);w[target]+=w[idx];w[idx]=0
        for name in (side+'Thigh',side+'LowLeg',side+'Foot'):
            idx=names.index(name);w[names.index('LowerTorso')]+=w[idx];w[idx]=0
    if collar:
        idx=names.index('Body_Head');w[names.index('Body_Neck')]+=w[idx];w[idx]=0
    w[np.argsort(w)[:-4]]=0;return w/w.sum()
def shell_point(s,h):
    theta=s/R;v=h/H;si=math.sin(theta);co=math.cos(theta)
    rx=np.interp(v,[0,.09,.3,.55,.65,.80,.87,1],[.164,.169,.174,.182,.190,.203,.185,.105])
    fy=np.interp(v,[0,.09,.3,.55,.65,.80,1],[.188,.194,.187,.178,.170,.167,.171])
    by=np.interp(v,[0,.09,.3,.55,.65,.80,1],[.101,.115,.121,.124,.124,.113,.086])
    upper_t=max(0,(v-.65)/.35)
    lobe=math.sin(math.pi*min(1,upper_t)) if upper_t else 0
    x=rx*si+.045*si**7*lobe
    y=(fy if co>=0 else by)*math.copysign(abs(co)**.8,co)
    top=.570-.115*max(co,0)**4
    z=.215+(.43-.215)*v/.65 if v<=.65 else .43+(top-.43)*upper_t+.055*abs(si)**6*lobe
    # A small natural ease fold directly above the cinched waist; the belt
    # remains the fixed reference instead of being scaled with the new garment.
    return np.array((x,y,z))

class Garment:
    def __init__(self,surface,names,rig,col,materials):
        self.surface=surface;self.names=names;self.rig=rig;self.col=col;self.mats=materials
        self.p=[];self.w=[];self.faces=[];self.uv=[];self.ids={};self.param={};self.collar_join=[];self.no_trim=set()
    def vertex(self,p):
        key=tuple(np.round(p,7))
        if key not in self.ids:
            self.ids[key]=len(self.p);self.p.append(np.array(key));self.w.append(torso_weights(self.surface,self.names,np.array(key),True))
        return self.ids[key]
    def face(self,ids,material,uv=None):
        if len(set(ids))<3:return
        self.faces.append((material,list(ids)))
        self.uv.append(uv if uv is not None else [self.default_uv(self.p[i],material) for i in ids])
    def default_uv(self,p,mat):
        x,y,z=p
        if mat==1:return (.5+x*1.4,.10+(z-.18)*1.72)
        if mat==2:
            # Dietrich's broad epaulette field. No old padding border is mapped
            # inside the new collar-reaching yoke; its border is real red cloth.
            return (.33+np.clip((abs(x)-.085)/.19,0,1)*.52,.11+np.clip((y+.10)/.21,0,1)*.25)
        if mat in (0,4):return (.37+x*.55,.65+np.clip((z-.17)/.45,0,1)*.25)
        return (x*2,z*2)
    def build(self):
        me=bpy.data.meshes.new('Hassler sewn garment control mesh');me.from_pydata(self.p,[],[f for _,f in self.faces]);me.update()
        ob=bpy.data.objects.new('10 Tunic-vest — continuous shell and collar',me);self.col.objects.link(ob)
        for mat in self.mats:me.materials.append(mat)
        layer=me.uv_layers.new(name='Hassler garment charts')
        for poly,(mat,ids),uv in zip(me.polygons,self.faces,self.uv):
            poly.material_index=mat;poly.use_smooth=True
            for li,q in zip(poly.loop_indices,uv):layer.data[li].uv=q
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
        probe=[f for f in bm.faces if f.calc_center_median().y>.12 and .27<f.calc_center_median().z<.42]
        if sum(f.normal.y for f in probe)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
        bm.to_mesh(me);bm.free()
        native.add_skin(ob,np.array(self.w),self.names,self.rig)
        lining=ob.modifiers.new('Garment thickness and finished openings 2.4 mm','SOLIDIFY');lining.thickness=.0024;lining.offset=-1
        ob['construction']='Single connected sewn shell: torso, waist ease, collar-reaching yoke and folded collar. Colour fields are shared faces, not overlays.'
        ob['neckline_join_vertices']=self.collar_join
        return ob

def make_materials():
    elite=native.load('body');cloth=elite['groups'][1]['texture']
    diet=step2.load(TOP/'source/dietrich/source/dietrich.json.gz')
    green=upper.material('Hassler 03 — native green cloth',(.04,.10,.075),.82,texture=cloth)
    n=green.node_tree.nodes;l=green.node_tree.links;tex=next(n for n in n if n.type=='TEX_IMAGE')
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[0].default_value=.20;mix.inputs[1].default_value=(.025,.065,.048,1)
    l.new(tex.outputs['Color'],mix.inputs[2]);l.new(mix.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    brocade=upper.material('Hassler 03 — Dietrich front brocade',(.5,.35,.1),.78,.025,diet['groups'][3]['texture'])
    shoulder=upper.material('Hassler 03 — Dietrich shoulder brocade',(.5,.35,.1),.78,.025,diet['groups'][0]['texture'])
    red=upper.material('Hassler 03 — continuous red cloth binding',(.32,.019,.012),.82)
    grey=upper.material('Hassler 03 — grey woven collar',(.20,.23,.22),.88,texture=cloth)
    n=grey.node_tree.nodes;l=grey.node_tree.links;tex=next(n for n in n if n.type=='TEX_IMAGE');bw=n.new('ShaderNodeRGBToBW');ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(.14,.16,.15,1);ramp.color_ramp.elements[1].color=(.28,.31,.29,1)
    l.new(tex.outputs['Color'],bw.inputs[0]);l.new(bw.outputs[0],ramp.inputs[0]);l.new(ramp.outputs[0],n.get('Principled BSDF').inputs['Base Color'])
    black=upper.material('Hassler 03 — black inner shirt',(.009,.014,.012),.94)
    return [green,brocade,shoulder,red,grey,black]

def add_collar(g):
    # Follow the actual top boundary, sharing every stitch vertex with the vest.
    # The asymmetric tips leave the centre of the black shirt open as in the art.
    top=[(s,i) for i,(s,h) in g.param.items() if abs(h-H)<1e-8 and not(-.22*R+1e-8<s<.50*R-1e-8)]
    top.sort(key=lambda a:(a[0]/R)%(2*math.pi))
    # Start at wearer-right front, continue across back, end at the longer left tip.
    top=[a for a in top if (a[0]/R)%(2*math.pi)>=.50-1e-7]
    rows=[];sections=[]
    for s,idx in top:
        theta=(s/R)%(2*math.pi);p=g.p[idx];co=math.cos(theta);si=math.sin(theta)
        arc=(theta-.50)/(2*math.pi-.22-.50)
        ends=1-smooth(0,.13,arc)*smooth(0,.13,1-arc)
        crown=.620-.025*max(co,0)**2
        # Long front end lays over the left facing instead of standing as a tube.
        end_height=p[2]+(.018 if si>0 else .028)
        crown=crown*(1-ends)+end_height*ends
        inner=np.array((.092*si,(.099 if co>=0 else .083)*co,crown))
        outward=np.array((si,co,0.));roll=inner+outward*.006;roll[2]+=.002
        edge=p+outward*(.030 if co<.4 else .012)
        edge[2]=p[2]-(.010 if si>0 else .029)*max(co,0)**3-.004
        if si<0:
            tip=smooth(.72,.98,arc);edge[0]+=.045*tip;edge[1]+=.010*tip
        face=roll*.46+edge*.54+outward*.003
        # A narrow bridge at each tip; all rows converge in height, but retain
        # actual cloth thickness and an explicitly finished end edge.
        section=[p,inner,roll,face,edge]
        ids=[idx]+[g.vertex(q) for q in section[1:]];rows.append(ids);sections.append(section)
        g.collar_join.append(idx)
    for k,(a,b) in enumerate(zip(rows,rows[1:])):
        ua=.28+k/(len(rows)-1)*.25;ub=.28+(k+1)/(len(rows)-1)*.25
        for j in range(4):
            va=.65+j/4*.25;vb=.65+(j+1)/4*.25
            g.face([a[j],a[j+1],b[j+1],b[j]],4,[(ua,va),(ua,vb),(ub,vb),(ub,va)])
    for end in (rows[0],rows[-1]):
        g.no_trim.update(tuple(sorted((end[j],end[j+1]))) for j in (0,1))
    return {'sewn_sections':len(rows),'profile_rows':5,'source_reference':'Wilham inner stand and fold; fresh art-led rails, not the rounded step-02 collar'}

def compact_path(ids,points,closed):
    ids=list(ids)
    changed=True
    while changed and len(ids)>4:
        changed=False;out=[]
        for j,i in enumerate(ids):
            if not closed and j in (0,len(ids)-1):out.append(i);continue
            a=points[ids[j-1]];p=points[i];b=points[ids[(j+1)%len(ids)]];d=b-a
            length=np.linalg.norm(d)
            dist=np.linalg.norm(np.cross(p-a,d))/max(length,1e-12)
            if dist<.00022 and length<.045 and (not out or out[-1]==ids[j-1]):changed=True
            else:out.append(i)
        ids=out
    return ids

def piping(garment,g,mat,col,rig,names):
    me=garment.data;adj={};normals=np.zeros((len(me.vertices),3))
    for f in me.polygons:
        for i in f.vertices:normals[i]+=np.array(f.normal)
        for a,b in zip(f.vertices,list(f.vertices[1:])+[f.vertices[0]]):adj.setdefault(tuple(sorted((a,b))),[]).append(f.material_index)
    # Adjacent gold textures belong to the same continuous cloth facing.
    family=lambda m:1 if m in (1,2) else m
    edges={e for e,ms in adj.items() if (len(ms)==1 or len({family(m) for m in ms})>1)
           and not(len(ms)==2 and 4 in ms) and e not in g.no_trim}
    graph={}
    for a,b in edges:graph.setdefault(a,set()).add(b);graph.setdefault(b,set()).add(a)
    pending=set(edges);paths=[]
    def walk(start,next_):
        path=[start];a,b=start,next_
        while tuple(sorted((a,b))) in pending:
            pending.remove(tuple(sorted((a,b))));path.append(b)
            if b==start:break
            if len(graph[b])!=2:break
            a,b=b,next(i for i in graph[b] if i!=a)
        return path
    for start,ns in graph.items():
        if len(ns)!=2:
            for n in ns:
                if tuple(sorted((start,n))) in pending:paths.append(walk(start,n))
    while pending:
        a,b=next(iter(pending));paths.append(walk(a,b))
    p=[];faces=[];uv=[];skin=[];lengths=[]
    normals/=np.maximum(np.linalg.norm(normals,axis=1)[:,None],1e-12)
    for raw in paths:
        closed=raw[0]==raw[-1];raw=raw[:-1] if closed else raw;ids=compact_path(raw,g.p,closed)
        if len(ids)<2:continue
        offset=len(p);length=0
        for j,i in enumerate(ids):
            a=g.p[ids[j-1 if j else (-1 if closed else 0)]];b=g.p[ids[(j+1)%len(ids)] if j+1<len(ids) or closed else ids[-1]]
            tangent=Vector(b-a).normalized();normal=Vector(normals[i]);normal=(normal-tangent*normal.dot(tangent)).normalized()
            other=tangent.cross(normal).normalized();center=g.p[i]+normals[i]*.0010
            if j:length+=np.linalg.norm(g.p[i]-g.p[ids[j-1]])
            for k in range(6):
                angle=k*2*math.pi/6;p.append(center+TRIM_RADIUS*(np.array(normal)*math.cos(angle)+np.array(other)*math.sin(angle)))
                uv.append((length/.05,k/6));skin.append(g.w[i])
        for j in range(len(ids) if closed else len(ids)-1):
            for k in range(6):
                a=offset+j*6+k;b=offset+j*6+(k+1)%6;c=offset+((j+1)%len(ids))*6+(k+1)%6;d=offset+((j+1)%len(ids))*6+k
                faces.append([a,b,c,d])
        if not closed:
            faces.append([offset+k for k in range(5,-1,-1)]);faces.append([offset+(len(ids)-1)*6+k for k in range(6)])
        lengths.append(float(length))
    ob=upper.geometry('11 Red binding — continuous 3 mm seams',p,faces,uv,skin,mat,col,rig,names)
    layer=ob.data.uv_layers.active
    for face in ob.data.polygons:
        if len(face.vertices)==6:
            for j,li in enumerate(face.loop_indices):
                angle=2*math.pi*j/6;layer.data[li].uv=(.5+.45*math.cos(angle),.5+.45*math.sin(angle))
    ob['diameter_m']=TRIM_RADIUS*2;ob['construction']='Derived from sewn garment boundaries and material interfaces; uniform circular cross-section; gold-to-gold atlas changes excluded'
    return {'paths':len(lengths),'diameter_m':TRIM_RADIUS*2,'total_length_m':sum(lengths)}

def inner_shirt(surface,rig,names,col,mat,green,garment):
    head=bpy.data.objects['Hassler head — native unchanged'];hp=[v.co[:] for v in head.data.vertices]
    tree=BVHTree.FromPolygons(hp,[list(f.vertices) for f in head.data.polygons])
    outer=BVHTree.FromPolygons([v.co[:] for v in garment.data.vertices],[list(f.vertices) for f in garment.data.polygons])
    p=[];uv=[];skin=[];faces=[];count=48
    profiles=[(.170,.145,.160,.085),(.30,.155,.163,.100),(.40,.168,.158,.110),
              (.46,.179,.151,.104),(.505,.192,.140,.105),(.530,.185,.115,.095),
              (.560,.095,.105,.075)]
    for row in range(len(profiles)+1):
        for i in range(count):
            theta=2*math.pi*i/count;co=math.cos(theta);si=math.sin(theta)
            ztop=.620-.021*max(co,0)**3
            start=Vector((.3*si,.3*co,ztop));hit,normal,ti,dist=tree.ray_cast(start,Vector((-si,-co,0)))
            if hit is None:hit=Vector((.068*si,.075*co,ztop))
            upper=np.array(hit)+np.array((si,co,0))*.0015
            if row<len(profiles):
                z,rx,fy,by=profiles[row];q=np.array((rx*si,(fy if co>0 else by)*co,z))
            else:q=upper
            # Keep the lining inside the actual cut of the jacket wherever that
            # jacket exists; leave its native-sized shoulder support in armholes.
            hit,no,ti,dist=outer.ray_cast(Vector((.45*si,.45*co,q[2])),Vector((-si,-co,0)))
            if hit is not None:
                allowed=max(.02,np.linalg.norm(np.array(hit)[:2])-.012)
                radius=np.linalg.norm(q[:2])
                if radius>allowed:q[:2]*=allowed/radius
            # The inner shirt stays under the jacket, with just its throat visible.
            p.append(q);uv.append((.37+q[0]*.55,.65+np.clip((q[2]-.17)/.45,0,1)*.25));skin.append(torso_weights(surface,names,q))
    for row in range(len(profiles)):
        for i in range(count):a=row*count+i;b=row*count+(i+1)%count;faces.append([a,a+count,b+count,b])
    ob=upper_geometry('12 Inner shirt — torso and fitted black neck',p,faces,uv,skin,mat,col,rig,names)
    ob.data.materials.append(green)
    for f in ob.data.polygons:
        front_opening=f.center.y>0 and abs(f.center.x)<.15 and f.center.z>.425
        f.material_index=0 if front_opening or f.index//count>=5 else 1
    return ob

def upper_geometry(name,p,faces,uv,skin,mat,col,rig,names):
    ob=upper.geometry(name,p,faces,uv,skin,mat,col,rig,names)
    bm=bmesh.new();bm.from_mesh(ob.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if name.startswith('12 '):
        probe=[f for f in bm.faces if f.calc_center_median().y>.08 and f.calc_center_median().z<.5]
        if sum(f.normal.y for f in probe)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    bm.to_mesh(ob.data);bm.free()
    return ob

def cord(garment,g,rig,col,names,mat):
    front=[list(f.vertices) for f in garment.data.polygons if f.normal.y>.1 and f.center.y>0]
    tree=BVHTree.FromPolygons([v.co[:] for v in garment.data.vertices],front)
    controls=np.array([[-.178,.553],[-.182,.356],[-.095,.355],[-.060,.457]])
    centers=[];skin0=[];n=32
    for i in range(n):
        t=i/(n-1);q=(1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3]
        p,no,ti,dist=tree.ray_cast(Vector((q[0],.5,q[1])),Vector((0,-1,0)))
        if p is None:p,no,ti,dist=tree.find_nearest(Vector((q[0],.16,q[1])))
        centers.append(np.array(p)+np.array(no)*.006);skin0.append(torso_weights(g.surface,names,np.array(p)))
    ps=[];uv=[];skin=[];fs=[]
    for i,p in enumerate(centers):
        t=Vector(centers[min(i+1,n-1)]-centers[max(i-1,0)]).normalized();u=t.cross(Vector((0,1,0))).normalized();v=t.cross(u).normalized()
        for k in range(6):a=2*math.pi*k/6;ps.append(p+.002*(np.array(u)*math.cos(a)+np.array(v)*math.sin(a)));uv.append((i/n,k/6));skin.append(skin0[i])
    for i in range(n-1):
        for k in range(6):a=i*6+k;b=i*6+(k+1)%6;fs.append([a,b,b+6,a+6])
    return upper_geometry('13 Aiguillette — fitted to tunic volume',ps,fs,uv,skin,mat,col,rig,names)

def stage_base(archive):
    base=bpy.data.objects['00 Native elite — original torso and sleeves'];old_points=[v.co.copy() for v in base.data.vertices]
    # Retain actual limb-weighted sleeve faces. Replace the old torso with the
    # continuous inner shirt, rather than leaving its clasp and armour shading
    # protruding through the new jacket. Low waist/belt faces remain untouched.
    limb={vg.index for vg in base.vertex_groups if vg.name in ('LUpArm','RUpArm','LLowArm','RLowArm','LHand','RHand')}
    scores={v.index:sum(g.weight for g in v.groups if g.group in limb) for v in base.data.vertices}
    uv=base.data.uv_layers[0]
    belt={f.index for f in base.data.polygons if f.material_index==1 and all(uv.data[li].uv.x<.2 for li in f.loop_indices) and all(-.02<base.data.vertices[i].co.z<.3 for i in f.vertices)}
    mesh=base.data;bm=bmesh.new();bm.from_mesh(mesh);bm.verts.ensure_lookup_table()
    cut=[f for f in bm.faces if f.index not in belt and all(v.co.z>.195 and abs(v.co.x)<.225 for v in f.verts) and max(scores[v.index] for v in f.verts)<.45]
    count=len(cut);bmesh.ops.delete(bm,geom=cut,context='FACES_ONLY');bm.to_mesh(mesh);bm.free()
    base.name='00 Native sleeves and lower body';base['covered_native_faces_removed']=count
    return count

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    cam=scene.camera;d=Vector(direction).normalized();cam.location=Vector(target)+d*4
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
    scene.render.filepath=str(OUT/(label+'.png'));bpy.ops.render.render(write_still=True)

def main():
    OUT.mkdir(parents=True,exist_ok=True);parent_hash=step2.sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    source=native.load('body');names=[b['name'] for b in source['bones']];rig=bpy.data.objects['RIG — native Rheinland']
    surface=upper.Surface(step2.actual_base());edit=bpy.data.collections['EDIT — native costume upper study']
    archive=native.collection('ARCHIVE — step 02 separate panels');archive.hide_viewport=archive.hide_render=True
    for ob in list(edit.objects):
        if ob.name!='00 Native elite — original torso and sleeves':native.move(ob,archive)
    removed=stage_base(archive);materials=make_materials();g=Garment(surface,names,rig,edit,materials)
    params,faces,layout=pattern(R,H);mapping={}
    for i,(s,h) in enumerate(params):
        idx=g.vertex(shell_point(s,h));mapping[i]=idx
        # Periodic back seam is a single geometric vertex. Save either parameter;
        # the boundary list below explicitly restores both sides for collar order.
        g.param[idx]=(float(s),float(h))
    for material,ids in faces:
        uv=None
        if material==2:
            uv=[(.39+(abs(params[i][0])-.125)/.270*.43,.11+(params[i][1]-.337)/.063*.22) for i in ids]
        g.face([mapping[i] for i in ids],material,uv)
    collar=add_collar(g);garment=g.build();trim=piping(garment,g,materials[3],edit,rig,names)
    inner_shirt(surface,rig,names,edit,materials[5],materials[0],garment)
    gold=upper.material('Hassler 03 — gold braid',(.5,.31,.065),.58,.25);cord(garment,g,rig,edit,names,gold)
    scene.cycles.samples=32;scene.render.resolution_x=1000;scene.render.resolution_y=1000
    views=[('front',(0,1,0)),('three_quarter',(.65,1,.12)),('back',(0,-1,.03)),('side',(1,0,.02))]
    if '--quick' in sys.argv:views=views[:2]
    for label,d in views:render(scene,label,d)
    if '--quick' not in sys.argv:
        render(scene,'collar_close',(.35,1,.18),(0,0,1.54),.63)
        render(scene,'waist_close',(.7,1,.12),(0,0,1.23),.55)
        scene.frame_set(120);render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1)
    upper.dump(OUT/'pattern.json',layout)
    report={'step':'03 continuous tunic-vest','parent':str(PARENT),'parent_sha256':parent_hash,
            'source_scrote':step2.load(TOP/'source/scrote/source/scrote.json.gz')['sha256'],
            'construction':'One connected tunic shell including shoulder yoke and sewn collar; materials partition that surface without floating panels',
            'collar':collar,'trim':trim,'covered_native_faces_removed':removed,
            'waist_profiles':{str(z):shell_point(0,z).tolist() for z in (0,.012,.035,.08,.16)},
            'head_fit_preserved_from_step_02':True,'game_installed':False,'game_animations_validated':False,
            'reference_interpretation':'Manually authored from Hassler front/back art. Scrote is the volume/hem construction reference, not a copied uniform.'}
    upper.dump(OUT/'report.json',report)
    text=bpy.data.texts.get('README — native upper prototype');text.clear();text.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(garment);cam=scene.camera;d=Vector((.35,1,.08)).normalized();cam.location=Vector((0,0,1.47))+d*4
    cam.rotation_euler=(-d).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1.02
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    assert step2.sha(PARENT)==parent_hash;print(json.dumps(report,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
