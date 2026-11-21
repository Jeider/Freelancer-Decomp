"""Finish upper fit: visible shoulder boards, layered cords, native open neck."""
import sys,json,math
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools'),str(Path(__file__).parent)]
from blender_workspace import configure
import hassler_build as native
import hassler_native_upper as upper
import hassler_native_step02 as s2
import hassler_native_step03 as s3
import hassler_native_step07 as s7
configure('character_rounding')
TOP=upper.TOP;OUT=TOP/'step_08';PARENT=TOP/'step_07/hassler_native_upper.blend'
GARMENT='10 Sewn uniform — finished shoulder fit'
LINING='15 Red lining — tucked below shoulder board'
SHIRT='12 Inner shirt — native open neckline'
EPAULETTES='14 Epaulettes — enlarged seated gold boards'

def weights(ob,names):
    w=np.zeros((len(ob.data.vertices),len(names)))
    for v in ob.data.vertices:
        for a in v.groups:
            name=ob.vertex_groups[a.group].name
            if name in names:w[v.index,names.index(name)]=a.weight
    return w

def clone(old,name,edit,archive):
    native.move(old,archive);ob=old.copy();ob.data=old.data.copy();edit.objects.link(ob)
    ob.name=name;ob.hide_render=False;ob.hide_viewport=False;return ob

def set_weights(ob,w):
    for v in ob.data.vertices:
        for a in list(v.groups):ob.vertex_groups[a.group].remove([v.index])
        for j in np.flatnonzero(w[v.index]>0):ob.vertex_groups[j].add([v.index],float(w[v.index,j]),'REPLACE')

def torso_warp(p):
    p=np.array(p,dtype=float);q=p.copy()
    f=s3.smooth(.135,.195,p[0])*s3.smooth(.515,.568,p[2])*s3.smooth(.01,.055,p[1])
    q+=np.array([-.020,-.008,-.026])*f
    return q

def finish_cloth(old,lining,edit,archive,rig,names,source,report):
    ob=clone(old,GARMENT,edit,archive);normals=[n.vector[:] for n in ob.data.corner_normals];changed=[]
    collar_vertices={i for fi in report['cut']['collar_faces'] for i in ob.data.polygons[fi].vertices};collar_changes=[]
    for v in ob.data.vertices:
        p=np.array(v.co);q=torso_warp(p)
        if v.index in collar_vertices:
            f=s3.smooth(.015,.065,-p[1])*s3.smooth(.570,.602,p[2])
            if f>0:q+=np.array([0,-.014,-.004])*f;collar_changes.append(v.index)
        if np.linalg.norm(q-p)>1e-8:v.co=q;changed.append(v.index)
    ob.data.update();changed=set(changed)
    ob.data.normals_split_custom_set([ob.data.vertices[l.vertex_index].normal[:] if l.vertex_index in changed else normals[i] for i,l in enumerate(ob.data.loops)])
    inner=clone(lining,LINING,edit,archive);innorm=[n.vector[:] for n in inner.data.corner_normals]
    for v in inner.data.vertices:
        v.co=torso_warp(np.array(v.co)+np.array([0,.006,0]))-np.array([0,.006,0])
    inner.data.update()
    # Use smooth area-weighted shading for the red cloth after the shoulder tuck.
    inner.data.calc_loop_triangles();nn=np.zeros((len(inner.data.vertices),3));adj=[set() for _ in inner.data.vertices]
    for tri in inner.data.loop_triangles:
        ids=list(tri.vertices);a,b,c=[np.array(inner.data.vertices[i].co) for i in ids];n=np.cross(b-a,c-a)
        for i in ids:nn[i]+=n;adj[i].update(j for j in ids if j!=i)
    nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-12)
    for _ in range(3):
        nn=np.array([.6*n+.4*np.mean(nn[list(adj[i])],axis=0) if adj[i] else n for i,n in enumerate(nn)])
        nn/=np.maximum(np.linalg.norm(nn,axis=1)[:,None],1e-12)
    inner.data.normals_split_custom_set([nn[l.vertex_index] for l in inner.data.loops])
    # Rebuild only the trim to follow the moved shared shoulder boundary.
    g=s3.Garment(upper.Surface(source),names,rig,edit,list(ob.data.materials[:report['reverse_material_offset']]))
    g.p=[np.array(v.co) for v in ob.data.vertices];g.w=list(weights(ob,names));uv=ob.data.uv_layers.active
    for f in ob.data.polygons:g.face(list(f.vertices),f.material_index,[uv.data[li].uv[:] for li in f.loop_indices])
    for mat,ids in g.faces:
        for a,b in zip(ids,ids[1:]+ids[:1]):
            if min(abs(g.p[i][0]) for i in (a,b))>.19 and max(g.p[i][2] for i in (a,b))<.32:g.no_trim.add(tuple(sorted((a,b))))
    rows=report['flap']['section_vertices']
    for a,b in zip(rows,rows[1:]):g.no_trim.add(tuple(sorted((a[0],b[0]))))
    for row in (rows[0],rows[-1]):
        for j in (0,1):g.no_trim.add(tuple(sorted((row[j],row[j+1]))))
    trim=s3.piping(ob,g,g.mats[3],edit,rig,names)
    return ob,inner,{'changed_coat_vertices':sorted(changed),'max_upper_red_tuck_m':[.020,.008,.026],
                     'back_collar_clearance_vertices':collar_changes,'back_collar_offset_max_m':[0,-.014,-.004],'trim':trim}

def native_neck_loop(head):
    p=np.array([v.co[:] for v in head.data.vertices]);edges={}
    for f in head.data.polygons:
        ids=list(f.vertices)
        for a,b in zip(ids,ids[1:]+ids[:1]):
            key=tuple(sorted((tuple(np.round(p[a],6)),tuple(np.round(p[b],6)))))
            edges[key]=edges.get(key,0)+1
    border={}
    for (a,b),n in edges.items():
        if n==1 and max(a[2],b[2])<.62:border.setdefault(a,[]).append(b);border.setdefault(b,[]).append(a)
    start=max(border,key=lambda p:p[1]);ring=[start]
    while True:
        options=[p for p in border[ring[-1]] if p not in ring]
        if not options:break
        ring.append(options[0])
    assert len(ring)==10 and all(len(v)==2 for v in border.values())
    return np.array(ring)

def open_neck(old,edit,archive,rig,names):
    head=bpy.data.objects['Hassler head — native unchanged'];ring=native_neck_loop(head)
    # Match the actual native lower-neck polygon. Sampling its straight edges
    # preserves the seam while retaining the existing 48-column shirt chart.
    angles=np.arctan2(ring[:,0]-.000707,ring[:,1]+.006);order=np.argsort(angles);ring=ring[order];angles=angles[order]
    angles=np.r_[angles[-1]-2*math.pi,angles,angles[0]+2*math.pi];ring=np.vstack((ring[-1],ring,ring[0]))
    ob=clone(old,SHIRT,edit,archive);me=ob.data;w=weights(ob,names);tops=[]
    for i in range(48):
        theta=(2*math.pi*i/48+math.pi)%(2*math.pi)-math.pi
        k=max(0,min(len(angles)-2,np.searchsorted(angles,theta)-1));a,b=ring[k],ring[k+1]
        # Intersection of the requested azimuth with the exact boundary edge.
        direction=np.array([math.sin(theta),math.cos(theta)]);center=np.array([.000707,-.006])
        d=b[:2]-a[:2];cross=lambda u,v:u[0]*v[1]-u[1]*v[0]
        t=-cross(a[:2]-center,direction)/cross(d,direction);t=np.clip(t,0,1)
        q=a+(b-a)*t;me.vertices[6*48+i].co=q;tops.append((6*48+i,q.tolist()))
        w[6*48+i]=0;w[6*48+i,names.index('Body_Head')]=1
    # Remove the entire high standing band. Only the chest-to-native-neck hem
    # remains; the original head and its neck are not reshaped or reweighted.
    bm=bmesh.new();bm.from_mesh(me);bm.faces.ensure_lookup_table()
    drop=[f for f in bm.faces if f.index>=6*48];bmesh.ops.delete(bm,geom=drop,context='FACES_ONLY');bm.to_mesh(me);bm.free()
    set_weights(ob,w);me.update()
    if me.has_custom_normals:native.activate(ob);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    ob['construction']='High black neck band removed. Chest hem matches the original native head lower boundary and follows Body_Head; head/neck geometry unchanged.'
    return ob,{'native_boundary':ring[1:-1].tolist(),'hem_vertices':tops,'high_band_faces_removed':48,'neck_mesh_added':False,'native_head_unchanged':True}

class SampleMesh:
    def __init__(self,ob,names,face_filter=None):
        me=ob.data;me.calc_loop_triangles();self.p=np.array([v.co[:] for v in me.vertices]);self.w=weights(ob,names)
        self.faces=[list(t.vertices) for t in me.loop_triangles if face_filter is None or face_filter(me.polygons[t.polygon_index])]
        self.tree=BVHTree.FromPolygons(self.p.tolist(),self.faces,all_triangles=True)
    def skin(self,hit,idx):
        tri=self.faces[idx];b=np.array(barycentric_transform(hit,*[Vector(self.p[i]) for i in tri],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1))))
        b=np.maximum(b,0);b/=b.sum();w=b@self.w[tri];w[w<1e-7]=0;w[np.argsort(w)[:-4]]=0;w/=w.sum();return w

def fit_epaulettes(old,coat,lining,edit,archive,rig,names):
    ob=clone(old,EPAULETTES,edit,archive);me=ob.data
    for v in me.vertices:
        x,y,z=v.co;sign=1 if x>0 else -1
        v.co=(sign*(.154+(abs(x)-.150)*1.12),y*1.38+.014,z+.020)
    me.update();surface=SampleMesh(coat,names,lambda f:f.material_index!=4 and f.center.z>.45)
    w=[]
    for v in me.vertices:
        p=v.co;hit,no,idx,dist=surface.tree.ray_cast(Vector((p.x,p.y,.8)),Vector((0,0,-1)))
        if hit is None:hit,no,idx,dist=surface.tree.find_nearest(p)
        row=surface.skin(hit,idx);side='R' if p.x>0 else 'L'
        # Cloth-following attachment, with a restrained arm contribution at the
        # outer edge rather than the old unrelated source weights.
        arm=names.index(side+'UpArm');clav=names.index(side+'CollarBone')
        for bone in ('LLowArm','RLowArm','LHand','RHand','Body_Head','Body_Neck'):
            j=names.index(bone);row[clav]+=row[j];row[j]=0
        excess=max(0,row[arm]-.30);row[arm]-=excess;row[clav]+=excess
        row[np.argsort(row)[:-4]]=0;row/=row.sum();w.append(row)
    set_weights(ob,np.array(w))
    if me.has_custom_normals:native.activate(ob);bpy.ops.mesh.customdata_custom_splitnormals_clear()
    solid=next(m for m in ob.modifiers if m.type=='SOLIDIFY');solid.thickness=.0015;solid.use_quality_normals=True
    # Fill the actual space beneath the board's roof. Its upper contour comes
    # from the gold mesh, its lower seat from the shoulder; no loose ellipsoid
    # and no thin decal on the sleeve. The two layers inherit their own seats.
    me.update();roof=[f for f in me.polygons if f.normal.z>.18 and f.center.z>.550]
    ids=sorted({i for f in roof for i in f.vertices});mapping={i:k for k,i in enumerate(ids)}
    epw=weights(ob,names);ps=[];uv=[];skin=[];lower=[];lower_w=[];meuv=me.uv_layers.active;uvmap={}
    for f in roof:
        for i,li in zip(f.vertices,f.loop_indices):uvmap.setdefault(i,meuv.data[li].uv[:])
    for i in ids:
        p=np.array(me.vertices[i].co);normal=np.array(me.vertices[i].normal);top=p-normal*.007
        hit,no,fi,dist=surface.tree.ray_cast(Vector((p[0],p[1],.8)),Vector((0,0,-1)))
        if hit is None:hit,no,fi,dist=surface.tree.find_nearest(Vector(p))
        contact=np.array(hit);bottom=.70*contact+.30*top
        bottom[2]=min(top[2]-.009,max(contact[2]-.001,top[2]-.060))
        # Keep the lower surface inside the gold sheet at curved front edges.
        penetration=np.dot(bottom-p,normal)+.006
        if penetration>0:bottom-=normal*penetration
        ps.append(top);uv.append(uvmap[i]);skin.append(epw[i]);lower.append(bottom);lower_w.append(surface.skin(hit,fi))
    count=len(ids);ps+=lower;uv+=list(uv);skin+=lower_w;fs=[];adj={}
    for f in roof:
        ring=[mapping[i] for i in f.vertices];fs.append(ring);fs.append([i+count for i in ring[::-1]])
        for a,b in zip(ring,ring[1:]+ring[:1]):adj.setdefault(tuple(sorted((a,b))),[]).append((a,b))
    side_start=len(fs)
    for e,uses in adj.items():
        if len(uses)==1:
            a,b=uses[0];fs.append([b,a,a+count,b+count])
    pad=upper.geometry('16 Grey shoulder supports — seated under gold roofs',ps,fs,uv,skin,old.data.materials[1],edit,rig,names)
    for f in list(pad.data.polygons)[side_start:]:
        a,b,c,d=[np.array(pad.data.vertices[i].co) for i in f.vertices];length=np.linalg.norm(b-a);depth=(np.linalg.norm(c-b)+np.linalg.norm(d-a))*.5
        for li,q in zip(f.loop_indices,[(0,0),(length,0),(length,depth),(0,depth)]):pad.data.uv_layers.active.data[li].uv=q
    bm=bmesh.new();bm.from_mesh(pad.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(pad.data);bm.free()
    pad['construction']='Upper contour/skin from the gold shoulder roof, lower contour/skin from the actual shoulder; closed grey support fills the intervening volume.'
    ob['construction']='Original projecting silhouette enlarged along the shoulder and front, fitted to current cloth; Dietrich UV/material retained.'
    return ob,pad,{'width_scale_from_inner_anchor':1.12,'depth_scale':1.38,'front_shift_m':.014,'rise_m':.020,'grey_backing_m':.0015,'arm_weight_limit':.30,'grey_support':'Closed volume derived from the gold roof and the actual shoulder.'}

def cords(old,coat,edit,archive,rig,names):
    native.move(old,archive);gold=old.data.materials[0].copy();gold.name='Hassler 08 — gold aiguillette cord'
    bs=gold.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.56
    surface=SampleMesh(coat,names,lambda f:f.material_index!=4)
    curves=[([[-.185,.555],[-.188,.340],[-.084,.310],[-.070,.435]],.0033),
            ([[-.198,.555],[-.184,.305],[-.083,.270],[-.062,.425]],.0028),
            ([[-.211,.555],[-.180,.280],[-.082,.235],[-.054,.415]],.0028)]
    results=[]
    for number,(controls,radius) in enumerate(curves,1):
        controls=np.array(controls);centers=[];ww=[];n=56;sides=8
        for t in np.linspace(0,1,n):
            q=(1-t)**3*controls[0]+3*(1-t)**2*t*controls[1]+3*(1-t)*t*t*controls[2]+t**3*controls[3]
            hit,no,idx,dist=surface.tree.ray_cast(Vector((q[0],.6,q[1])),Vector((0,-1,0)))
            assert hit is not None,('Cord outside cloth',number,q.tolist())
            centers.append(np.array(hit)+np.array([0,.011,0]));ww.append(surface.skin(hit,idx))
        # A hanging cord bridges the shoulder/chest hollow; it must not follow
        # the abrupt depth recess there and cut diagonally through its rim.
        raw=np.array([p[1] for p in centers]);envelope=np.array([max(raw[max(0,i-3):min(n,i+4)]) for i in range(n)])
        fair=np.convolve(np.pad(envelope,(2,2),mode='edge'),[.10,.20,.40,.20,.10],mode='valid')
        for i in range(4,n-3):centers[i][1]=max(raw[i],fair[i])
        ps=[];uv=[];skin=[];fs=[];distance=0
        for i,p in enumerate(centers):
            if i:distance+=np.linalg.norm(p-centers[i-1])
            tangent=Vector(centers[min(i+1,n-1)]-centers[max(0,i-1)]).normalized();u=tangent.cross(Vector((0,1,0))).normalized();v=tangent.cross(u).normalized()
            for k in range(sides):
                a=2*math.pi*k/sides
                ps.append(p+radius*(np.array(u)*math.cos(a)+np.array(v)*math.sin(a)));uv.append((distance/.04,k/sides));skin.append(ww[i])
        for i in range(n-1):
            for k in range(sides):a=i*sides+k;b=i*sides+(k+1)%sides;fs.append([a,b,b+sides,a+sides])
        fs.append(list(range(sides-1,-1,-1)));fs.append([(n-1)*sides+k for k in range(sides)])
        ob=upper.geometry(f'13.{number} Aiguillette — graduated gold loop',ps,fs,uv,skin,gold,edit,rig,names)
        for f in list(ob.data.polygons)[-2:]:
            for k,li in enumerate(f.loop_indices):a=2*math.pi*k/sides;ob.data.uv_layers.active.data[li].uv=(.5+.45*math.cos(a),.5+.45*math.sin(a))
        ob['editable_centerline']=json.dumps([p.tolist() for p in centers]);ob['radius_m']=radius
        results.append({'name':ob.name,'controls_xz':controls.tolist(),'centers':[p.tolist() for p in centers],'radius_m':radius,'front_offset_m':.011,'shoulder_hollow_bridged':True,'buried_attachment_rings':4})
    return results

def render(scene,label,direction,target=(0,0,1.47),scale=1.02):
    s7.OUT=OUT;s7.render(scene,label,direction,target,scale)

def main():
    OUT.mkdir(parents=True,exist_ok=True);parent_hash=s2.sha(PARENT)
    bpy.ops.wm.open_mainfile(filepath=str(PARENT));configure('character_rounding');scene=bpy.context.scene;scene.frame_set(1)
    source=native.load('body');names=[b['name'] for b in source['bones']];rig=bpy.data.objects['RIG — native Rheinland']
    edit=bpy.data.collections['EDIT — native costume upper study'];archive=native.collection('ARCHIVE — step 07 before upper finish');archive.hide_viewport=archive.hide_render=True
    originals={key:next(o for o in edit.objects if o.name.startswith(key)) for key in ('10 ','11 ','12 ','13 ','14 ','15 ')}
    prior=json.loads((TOP/'step_07/report.json').read_text(encoding='utf8'))
    native.move(originals['11 '],archive)
    coat,lining,cloth=finish_cloth(originals['10 '],originals['15 '],edit,archive,rig,names,source,prior)
    shirt,neck=open_neck(originals['12 '],edit,archive,rig,names)
    ep,pad,shoulders=fit_epaulettes(originals['14 '],coat,lining,edit,archive,rig,names)
    loops=cords(originals['13 '],coat,edit,archive,rig,names)
    report={'step':'08 shoulder fit, multiple aiguillettes, native neck','parent':str(PARENT),'parent_sha256':parent_hash,
            'cloth':cloth,'neck':neck,'epaulettes':shoulders,'cords':loops,'inherited_opening':prior['flap'],'sleeves':prior['sleeves'],
            'art_references':[str(TOP/'source/art/hassler1.png'),str(TOP/'source/art/hassler2.png')],
            'game_installed':False,'game_animations_validated':False}
    upper.dump(OUT/'report.json',report);doc=bpy.data.texts.get('README — native upper prototype');doc.clear();doc.write(json.dumps(report,ensure_ascii=False,indent=2))
    native.activate(coat);scene.cycles.samples=32;scene.render.resolution_x=scene.render.resolution_y=1000
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hassler_native_upper.blend'),compress=True)
    render(scene,'front',(0,1,0));render(scene,'three_quarter',(.65,1,.12))
    if '--quick' not in sys.argv:
        render(scene,'collar_close',(.35,1,.18),(0,.02,1.53),.64)
        render(scene,'shoulder_detail',(1,.65,.35),(.16,0,1.50),.44)
        render(scene,'shoulders_above',(0,1,.8),(0,.01,1.50),.72)
        render(scene,'back',(0,-1,.03));render(scene,'side',(1,0,.02))
        scene.frame_set(60);render(scene,'shoulder_pose',(.65,1,.12));scene.frame_set(120);render(scene,'turn_pose',(.65,1,.12));scene.frame_set(1)
    assert s2.sha(PARENT)==parent_hash
    print(json.dumps({'step':8,'cord_loops':len(loops),'removed_neck_band_faces':neck['high_band_faces_removed']}),flush=True)

if __name__=='__main__':main()
