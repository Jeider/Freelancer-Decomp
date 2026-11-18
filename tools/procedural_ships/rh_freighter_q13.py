"""Q13 first form prototype. Native cabin/HPs/controllers, offline CMP and previews."""
import collections
import copy
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import struct
import numpy as np
from scipy.spatial import Delaunay
from PIL import Image, ImageDraw, ImageFont
import rh_concept_b_final as f
from rh_concept_b_form import Builder as PolygonBuilder
from rh_pir_engine_damage_closed import coherent
from preview import render

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/ship_design/rh_freighter/prototypes/q13_01'
SOURCE=Path('D:/Games/FL_MOD/DATA/ships/rheinland/rh_pir_freighter/rh_pir_freighter.cmp')
MAT=SOURCE.parent.parent/'rh_pir_playerships.mat'
DEST=OUT/'rh_freighter_q13_lod0.cmp'
ART=ROOT/'out/ship_design/rh_freighter/concepts/round_10/rh_freighter_Q13_sheet.png'
P=f.mesh.crc('pir_r_panel01_256');R=f.mesh.crc('pir_r_panel02_256')
D=f.mesh.crc('pir_r_panel01_256D');G=f.mesh.crc('engine_grill01')
PLAIN=(.54,.30,.97,.80);RED=(.020,.043,.146,.457);GREEN=(.672,.008,.982,.202)
FRAME=(.006,.865,.994,.992);HATCH=(.10,.274,.46,.559)
SHELL_Y=2.4349513053894043;SHELL_Z=.9392921924591064
SHAPE=np.array([[-6.80,1.65],[-4.45,3.85],[5.65,3.85],[7.95,2.4],
                [8.0,-2.50],[6.65,-4.118],[-5.25,-4.118],[-6.80,-2.90]]) # z,y
DONOR=np.array([[-5.83,-2.75],[-4.72,-1.52],[6.87,1.04],[7.35,.60],
                [7.37,-2.25],[6.25,-3.70],[-4.90,-3.70]])
VENT=np.array([[-6.48,-.88],[-6.48,.80],[-4.85,1.98],[-3.13,1.98],[-3.13,.02],[-4.55,-.88]])
BELT=np.array([[-4.60,2.30],[-4.30,3.32],[4.64,3.32],[5.19,2.75],[5.19,.94],[-2.69,.94],[-2.69,2.30]])


def cull_render(scene,mats,center,radius,camera,size=1150,mode='texture'):
    direction=np.array(camera,float);direction/=np.linalg.norm(direction);visible=[]
    for g in scene:
        ts=g['corners'];normal=np.cross(ts[:,1,:3]-ts[:,0,:3],ts[:,2,:3]-ts[:,0,:3])
        mask=normal@direction>1e-9
        if 'two' in mats[g['material']]['kind'].lower():mask[:]=True
        if mask.any():visible.append(dict(g,corners=ts[mask]))
    return render(visible,mats,center,radius,camera,size=size,mode=mode)


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,
        default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def inside(poly,p):
    x,y=p;result=False
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result


def planar_mesh(outer,holes=()):
    """Refine only missing boundary constraints; no uniform decorative tessellation."""
    loops=[np.array(outer,float)]+[np.array(h,float) for h in holes]
    for attempt in range(10):
        points=np.concatenate(loops);d=Delaunay(points)
        edges={tuple(sorted((int(a),int(b)))) for ids in d.simplices for a,b in zip(ids,np.roll(ids,-1))}
        offset=0;new=[];missing=0
        for loop in loops:
            q=[]
            for i,a in enumerate(loop):
                j=(i+1)%len(loop);q.append(a)
                if tuple(sorted((offset+i,offset+j))) not in edges:q.append((a+loop[j])*.5);missing+=1
            new.append(np.array(q));offset+=len(loop)
        if not missing:break
        loops=new
    else:raise AssertionError('Could not preserve panel boundary')
    triangles=[ids for ids in d.simplices if inside(loops[0],points[ids].mean(0)) and
               not any(inside(h,points[ids].mean(0)) for h in loops[1:])]
    assert triangles
    # The retained triangles must meet every boundary exactly once.
    count=collections.Counter(tuple(sorted((int(a),int(b)))) for ids in triangles for a,b in zip(ids,np.roll(ids,-1)))
    offset=0
    for loop in loops:
        for i in range(len(loop)):assert count[tuple(sorted((offset+i,offset+(i+1)%len(loop))))]==1
        offset+=len(loop)
    return points,triangles,loops


class B(PolygonBuilder):
    def face(self,points,material=P,uvbox=PLAIN,normal=None,uv=None):
        points=np.array(points,float)
        keep=[i for i in range(len(points)) if np.linalg.norm(points[i]-points[i-1])>1e-8]
        if len(keep)<3:return
        return super().face(points[keep],material,uvbox,normal,None if uv is None else np.array(uv)[keep])

    def panel(self,poly,axis,value,normal,material=P,uvbox=PLAIN,holes=(),rotate=False):
        points,tris,loops=planar_mesh(poly,holes);axes=[i for i in range(3) if i!=axis]
        # Side panels are specified z,y; horizontal plates x,z.
        if axis==0:axes=[2,1]
        lo=points.min(0);span=np.ptp(points,axis=0)
        uv=(points-lo)/span
        if rotate:uv=uv[:,::-1]
        for ids in tris:
            p=np.zeros((3,3));p[:,axis]=value;p[:,axes]=points[ids]
            self.face(p,material,uvbox,normal,uv[ids])
        return loops

    def yz(self,poly,x):
        p=np.zeros((len(poly),3));p[:,0]=x;p[:,1]=poly[:,1];p[:,2]=poly[:,0];return p

    def bridge(self,a,b,material=P,uvbox=FRAME,inner=False):
        arc=np.r_[0,np.cumsum(np.linalg.norm(np.roll(a,-1,axis=0)-a,axis=1))]
        center=np.concatenate((a,b)).mean(0)
        for i in range(len(a)):
            j=(i+1)%len(a);q=np.array([a[i],a[j],b[j],b[i]])
            n=q.mean(0)-center
            if inner:n=-n
            u,v=arc[i]/max(arc[-1],1e-5),arc[i+1]/max(arc[-1],1e-5)
            self.face(q,material,uvbox,n,[[u,0],[v,0],[v,1],[u,1]])

    def well(self,loop,side,front,back,material=R,box=RED):
        a=self.yz(loop,side*front);b=self.yz(loop,side*back)
        self.bridge(a,b,D,FRAME,inner=True)
        self.panel(loop,0,side*back,[side,0,0],material,box,rotate=True)


def wall(side):
    b=B();norm=[side,0,0]
    loops=b.panel(SHAPE,0,side*3.15,norm,P,PLAIN,holes=[DONOR,VENT,BELT])
    b.panel(loops[0],0,side*2.28,[-side,0,0],D,PLAIN)
    b.bridge(b.yz(loops[0],side*2.28),b.yz(loops[0],side*3.15),P,FRAME)
    # One large donor section with an inner hatch: stepped construction, no raised beam.
    donor=loops[1]
    hatch=np.array([[-3.10,-3.38],[6.10,-3.38],[6.88,-2.18],[6.88,.34],[-3.10,-1.86]])
    service=np.array([[-5.12,-3.36],[-3.54,-3.36],[-3.54,-2.63],[-4.75,-2.63],[-5.12,-2.99]])
    b.bridge(b.yz(donor,side*3.15),b.yz(donor,side*2.98),D,FRAME,inner=True)
    ls=b.panel(donor,0,side*2.98,norm,R,GREEN,holes=[hatch,service])
    # Use the refined inner contour so the well matches the actual cut-out.
    inner=ls[1];b.well(inner,side,2.98,2.79,R,RED)
    b.well(ls[2],side,2.98,2.83,P,HATCH)
    # Deep front vent: closed side walls plus floor, not strips pasted onto the hull.
    vent=loops[2];b.well(vent,side,3.15,2.52,D,PLAIN)
    # Three broad integrated louvres, fully closed and contained inside the pocket.
    for y,z0,z1 in [(-.34,-6.18,-3.43),(.27,-6.16,-3.43),(.88,-5.75,-3.43)]:
        profile=np.array([[z0,y-.07],[z1,y-.07],[z1,y+.045],[z0,y+.045]])
        a=b.yz(profile,side*2.64);c3=b.yz(profile,side*2.92)
        b.bridge(a,c3,P,FRAME);b.face(a,D,PLAIN,[-side,0,0]);b.face(c3,P,FRAME,norm)
    b.well(loops[3],side,3.15,2.98,P,(.54,.34,.97,.75))
    return coherent(b.groups())[0]


def body(cabin):
    b=B()
    # Hollow hold: both inner wall surfaces belong to wall(), these connect them.
    # Keep the entire curved shutter sweep clear above its lowest y=-2.07.
    b.face([[-2.28,-3.65,-5.25],[2.28,-3.65,-5.25],[2.28,-3.65,6.50],[-2.28,-3.65,6.50]],R,RED,[0,1,0])
    for a,c in zip(SHAPE,np.roll(SHAPE,-1,axis=0)):
        if np.allclose(a,[-4.45,3.85]) and np.allclose(c,[5.65,3.85]):continue
        q=np.array([[-2.28,a[1],a[0]],[2.28,a[1],a[0]],[2.28,c[1],c[0]],[-2.28,c[1],c[0]]])
        n=q.mean(0)-[0,0,0];b.face(q,P,PLAIN,n)
    # Recessed rim, instead of a solid deck across the cargo aperture.
    for side in (-1,1):
        b.face([[side*2.28,3.85,-4.45],[side*2.72,3.85,-4.45],
                [side*2.72,3.85,5.65],[side*2.28,3.85,5.65]],P,FRAME,[0,1,0])
    for z in (-4.45,5.65):
        b.face([[-2.28,-3.65,z],[2.28,-3.65,z],[2.28,3.79,z],[-2.28,3.79,z]],D,PLAIN,[0,0,1 if z<0 else -1])
    # Close the front deck-to-shutter seam outside the source shutter's swept volume.
    b.face([[-2.28,3.85,-4.45],[2.28,3.85,-4.45],[2.28,3.57,-3.50],[-2.28,3.57,-3.50]],P,FRAME,[0,1,0])
    b.face([[-2.28,3.57,-3.50],[2.28,3.57,-3.50],[2.28,3.45,-3.50],[-2.28,3.45,-3.50]],D,FRAME,[0,0,1])
    # Neck meets the untouched native cabin at its measured rear plane.
    rings=[]
    for z,w,bot,top in [(-8.416,1.98,-2.0786,.766),(-7.6,2.42,-2.45,1.05),(-6.8,3.15,-2.90,1.65)]:
        rings.append(np.array([[-w,bot,z],[w,bot,z],[w,top,z],[-w,top,z]]))
    distances=np.r_[0,np.cumsum([np.linalg.norm((c-a)[0,[0,2]]) for a,c in zip(rings,rings[1:])])]
    for si,(a,c) in enumerate(zip(rings,rings[1:])):
        for j in range(4):
            k=(j+1)%4;q=np.array([a[j],a[k],c[k],c[j]])
            n=q.mean(0)-np.concatenate((a,c)).mean(0)
            if j in (0,2):uv=np.column_stack((.75+q[:,0]*.065,.46+(q[:,2]+8.416)*.065))
            else:uv=np.column_stack((.54+np.array([distances[si],distances[si],distances[si+1],distances[si+1]])*.12,.80-(q[:,1]+2.90)*.12))
            b.face(q,P,(0,0,1,1),n,uv)
    b.face(rings[0],D,PLAIN,[0,0,-1]);b.face(rings[-1],D,PLAIN,[0,0,1])
    # Fixed cheeks form one thick half-disc on each side; the roof between them moves.
    theta=np.linspace(-np.pi/2,np.pi/2,19)
    for side in (-1,1):
        def arc(radius,x):return np.column_stack((np.full(len(theta),side*x),SHELL_Y+radius*np.cos(theta),SHELL_Z+radius*np.sin(theta)))
        outer=arc(4.909,2.84);inner=arc(4.58,2.84);recess=arc(4.58,2.71);back=arc(4.909,2.27)
        for k in range(18):
            q=[outer[k],outer[k+1],inner[k+1],inner[k]];b.face(q,P,FRAME,[side,0,0],[[k/18,0],[(k+1)/18,0],[(k+1)/18,1],[k/18,1]])
            b.face([inner[k],inner[k+1],recess[k+1],recess[k]],D,FRAME,[0,np.cos(theta[k]),np.sin(theta[k])])
            b.face([outer[k],outer[k+1],back[k+1],back[k]],P,FRAME,[0,np.cos(theta[k]),np.sin(theta[k])])
        # Concentric stepped fields with a few broad donor panels, no bolts.
        for ra,rb in ((4.58,3.58),(3.58,2.83),(2.83,0)):
            a=arc(ra,2.71);c=arc(rb,2.71)
            for k in range(18):
                m,box=(R,RED) if (k//3)%3==1 and ra>3 else ((R,GREEN) if (k//3)%3==0 else (P,PLAIN))
                q=np.array([a[k],a[k+1],c[k+1],c[k]])
                # UV is continuous within each wide 30-degree donor sector.
                uv=[[k%3/3,0],[(k%3+1)/3,0],[(k%3+1)/3,1],[k%3/3,1]]
                b.face(q,m,box,[side,0,0],uv)
        center=np.array([side*2.27,SHELL_Y,SHELL_Z]);b.face(np.vstack((back,center)),D,PLAIN,[-side,0,0])
        for k in (0,18):b.face([outer[k],back[k],center,[side*2.71,SHELL_Y,SHELL_Z],recess[k],inner[k]],P,FRAME,[0,-1,0])
    return f.merge(cabin+b.groups())


def shutter():
    b=B();angles=np.linspace(-75,75,13)*np.pi/180
    def p(x,a,r):return np.array([x,SHELL_Y+r*np.cos(a),SHELL_Z+r*np.sin(a)])
    for i,(a,c) in enumerate(zip(angles,angles[1:])):
        outer=np.array([p(-2.16,a,4.50),p(2.16,a,4.50),p(2.16,c,4.50),p(-2.16,c,4.50)])
        hole=np.array([p(-1.91,a+.027,4.50),p(1.91,a+.027,4.50),p(1.91,c-.027,4.50),p(-1.91,c-.027,4.50)])
        inset=np.array([p(-1.91,a+.027,4.445),p(1.91,a+.027,4.445),p(1.91,c-.027,4.445),p(-1.91,c-.027,4.445)])
        normal=np.array([0,np.cos((a+c)/2),np.sin((a+c)/2)])
        for j in range(4):
            k=(j+1)%4;b.face([outer[j],outer[k],hole[k],hole[j]],P,FRAME,normal)
            b.face([hole[j],hole[k],inset[k],inset[j]],D,FRAME,inset.mean(0)-(hole[j]+hole[k])/2)
        b.face(inset,R if i%4!=0 else P,RED if i%4!=0 else HATCH,normal,[[0,0],[0,1],[1,1],[1,0]])
        low=np.array([p(-2.16,a,4.33),p(2.16,a,4.33),p(2.16,c,4.33),p(-2.16,c,4.33)])
        b.face(low,D,PLAIN,-normal)
        for j,k,sign in ((0,3,-1),(1,2,1)):
            b.face([outer[j],outer[k],low[k],low[j]],P,FRAME,[sign,0,0])
        if i==0:b.face([outer[0],outer[1],low[1],low[0]],P,FRAME,[0,-np.sin(a),np.cos(a)])
        if i==11:b.face([outer[2],outer[3],low[3],low[2]],P,FRAME,[0,np.sin(c),-np.cos(c)])
    return coherent(b.groups())[0]


def engine(side):
    b=B();x=side*2.022728;y=-.309611;angles=np.arange(12)*2*np.pi/12+np.pi/12
    def ring(z,r):return np.column_stack((x+r*np.cos(angles),y+r*np.sin(angles),np.full(12,z)))
    rings=[ring(z,r) for z,r in [(6.30,.96),(7.0,1.40),(8.05,1.74),(10.62,1.74),(11.70,1.40),(12.158,1.40)]]
    for i,(a,c) in enumerate(zip(rings,rings[1:])):
        for j in range(12):
            k=(j+1)%12;q=np.array([a[j],a[k],c[k],c[j]])
            normal=q.mean(0)-[x,y,q[:,2].mean()]
            if i==2 and j in (0,1,4,5,8,9):
                v0,v1=(j%4)/2,(j%4+1)/2
                b.face(q,R,(.355,.327,.652,.472),normal,[[0,v0],[0,v1],[1,v1],[1,v0]])
            else:
                uv=np.column_stack((.54+(q[:,2]-6.30)*.072,.40+np.array([j%4,j%4+1,j%4+1,j%4])*.069))
                b.face(q,P,(0,0,1,1),normal,uv)
    b.face(rings[0],P,PLAIN,[0,0,-1])
    inner=ring(12.158,1.12);back=ring(11.20,1.07)
    for j in range(12):
        k=(j+1)%12;b.face([rings[-1][j],rings[-1][k],inner[k],inner[j]],P,FRAME,[0,0,1])
        q=np.array([inner[j],inner[k],back[k],back[j]])
        b.face(q,D,FRAME,[x,y,q[:,2].mean()]-q.mean(0))
    b.face(back,G,(0,0,1,1),[0,0,1])
    return b.groups()


def salted(nodes,salt):
    mapping={};lib=f.mesh.child(nodes[0],'VMeshLibrary')
    for i,n in enumerate(lib.children):
        old=n.name;n.name=f'rhf_q13_{i:02}_{salt}.vms';mapping[old]=n.name
    ids={f.mesh.crc(a):f.mesh.crc(b) for a,b in mapping.items()}
    for p,n in f.mesh.walk(nodes):
        if p.lower().endswith(('/vmeshref','/vwiredata')):
            raw=bytearray(n.blob);struct.pack_into('<I',raw,4,ids[struct.unpack_from('<I',raw,4)[0]]);n.blob=bytes(raw)
    for entry in f.mesh.child(nodes[0],'Cmpnd').children:
        if entry.name=='Cons':continue
        leaf=f.mesh.child(entry,'File name');old=f.mesh.string(leaf.blob);obj=f.mesh.string(f.mesh.child(entry,'Object name').blob)
        new=f'rhf_{obj}_{salt}.3db';assert len(new)<64
        f.mesh.child(nodes[0],old).name=new;leaf.blob=new.encode()+b'\0';mapping[old]=new
    return mapping


def main():
    assert shutil.disk_usage(ROOT.anchor).free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    selection=json.loads((OUT.parents[1]/'selection.json').read_text())
    assert f.digest(SOURCE)==selection['source_sha256'] and f.digest(ART)==selection['art_sha256']
    header,nodes=f.mesh.read_tree(SOURCE.read_bytes());original=copy.deepcopy(nodes)
    names=f.component_map(nodes);local=f.local_geometry(nodes);tr,_=f.audit.transforms(nodes)
    world={names[k]:f.base.world(gs,*tr[k.lower()]) for k,gs in local.items()}
    cabin=f.clip_groups(f.clip_groups(world['Root'],2,-8.416,False),1,.82,False)
    authored={'Root':body(cabin),'rh_port_side_lod1':wall(-1),'rh_star_side_lod1':wall(1),
        'port_engine_lod1':engine(-1),'starboard_engine_lod1':engine(1),'Baydoor_lod1':shutter()}
    new={}
    for file,name in names.items():
        r,t=tr[file.lower()];new[file]=f.base.world(authored[name],r.T,-r.T@t) if name in authored else local[file]
    # One level only: no automatic decimation, damage geometry or SUR in this shape trial.
    f.write_geometry(nodes,[new])
    for file in names:
        ml=f.mesh.child(f.mesh.child(nodes[0],file),'MultiLevel')
        f.mesh.child(ml,'Switch2').blob=np.array([0,10000],'<f4').tobytes()
    salt=secrets.token_hex(6);resource_map=salted(nodes,salt)
    nodes[0].children=[n for n in nodes[0].children if n.name.lower() not in ('material library','texture library')]
    DEST.write_bytes(f.mesh.write_tree(header,nodes))
    _,decoded=f.mesh.read_tree(DEST.read_bytes());decoded_local=f.local_geometry(decoded);dn=f.component_map(decoded)
    mats=f.audit.material_table([MAT,SOURCE.parents[3]/'fx/envmapbasic.mat'])
    counts={};objects=[]
    for file,gs in decoded_local.items():
        a=np.concatenate([g['corners'] for g in gs]);assert np.isfinite(a).all()
        assert len(a)*3<65536
        for g in gs:
            assert g['material'] in mats
            assert 'metal' not in mats[g['material']]['texture'].lower()
        counts[dn[file]]=len(a);objects.append(dict(name=dn[file],file=file,groups=gs))
    # Original HP bytes and all native motion channels remain authoritative.
    leafs=lambda ns,pred:{p:n.blob for p,n in f.mesh.walk(ns) if pred(p.lower())}
    for tag in ('Animation','Cons'):
        root=lambda ns:f.mesh.child(ns[0],tag) if tag=='Animation' else f.mesh.child(f.mesh.child(ns[0],'Cmpnd'),tag)
        assert leafs([root(original)],lambda p:True)==leafs([root(decoded)],lambda p:True)
    for old,newfile in [(old,resource_map[old]) for old in names]:
        a=f.mesh.child(original[0],old);c=f.mesh.child(decoded[0],newfile)
        hp=lambda n:{p.split('/Hardpoints/',1)[-1]:v.blob for p,v in f.mesh.walk([n]) if '/Hardpoints/' in p}
        assert hp(a)==hp(c)
    for n in ('glass_lod1','rh_port_big_btn_lod1','rh_port_sml_btn_lod1','rh_star_big_btn_lod1','rh_star_sml_btn_lod1'):
        old=local[next(k for k,v in names.items() if v==n)];now=decoded_local[next(k for k,v in dn.items() if v==n)]
        assert all(a['material']==c['material'] and np.allclose(a['corners'],c['corners'],atol=1e-6) for a,c in zip(old,now))
    flat={p.lower():n.blob for p,n in f.mesh.walk(decoded)}
    import full_ship_audit as audit
    constructs=audit.constructs(flat);channels=audit.channels(flat,constructs)
    # Geometry for Blender in part-local native coordinates, same bytes as CMP.
    for obj in objects:
        obj['joint']=next((c for c in constructs if c['name'].lower()==obj['name'].lower()),dict(name='Root',parent=None,kind='fix',origin=[0,0,0],rotation=np.eye(3).tolist()))
    images={}
    td=OUT/'textures';td.mkdir(exist_ok=True)
    for mid in {g['material'] for gs in decoded_local.values() for g in gs}:
        m=mats[mid];data={k:v for k,v in m.items() if k!='image'}
        if m['image'] is not None:
            p=td/(m['texture'].rsplit('.',1)[0]+'.png')
            if not p.exists():m['image'].save(p)
            data['image_path']=str(p)
        images[mid]=data
    dump('scene.json',dict(cmp=str(DEST),cmp_sha256=f.digest(DEST),objects=objects,materials=images,channels=channels))
    variants={}
    for title,pose in [('flight',('Sc_extend wing',0)),('stowed',('Sc_extend wing',1)),('bay_open',('Sc_rh_freighter',1))]:
        tt,_=f.audit.transforms(decoded,pose);variants[title]=[dict(g,part=dn[file]) for file,gs in decoded_local.items() for g in f.base.world(gs,*tt[file.lower()])]
    points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in variants['flight']]);center=(points.min(0)+points.max(0))/2
    radius=np.linalg.norm(points-center,axis=1).max()*1.02
    for label,cam in [('side',(1,0,0)),('perspective',(1,.70,-1.05)),('rear',(1,.65,1.15)),('under',(1,-.85,-1))]:
        for mode in ('texture','clay'):
            cull_render(variants['flight'],mats,center,radius,cam,size=1150,mode=mode).save(OUT/(mode+'_'+label+'.png'))
    # Top slightly tilted to avoid a degenerate camera cross product.
    cull_render(variants['flight'],mats,center,radius,(0,1,.00001),size=1150).save(OUT/'texture_top.png')
    cull_render(variants['bay_open'],mats,center,radius,(1,1,-1.05),size=1150).save(OUT/'bay_open.png')
    original_flight,_=f.audit.transforms(original,('Sc_extend wing',0))
    origpoints=np.concatenate([g['corners'][...,:3].reshape(-1,3) for file,gs in local.items() for g in f.base.world(gs,*original_flight[file.lower()])])
    dump('build.json',dict(source=str(SOURCE),source_sha256=f.digest(SOURCE),art=str(ART),art_sha256=f.digest(ART),
        cmp=str(DEST),cmp_sha256=f.digest(DEST),salt=salt,resources=resource_map,triangles=counts,total_triangles=sum(counts.values()),
        bounds=[points.min(0),points.max(0)],size=np.ptp(points,axis=0),original_size=np.ptp(origpoints,axis=0),
        native_cabin_triangles=sum(len(g['corners']) for g in cabin),native_glass_and_cylinders_preserved=True,
        native_hardpoint_payloads_preserved=True,native_animation_payloads_preserved=True,
        shared_mat=str(MAT),shared_mat_sha256=f.digest(MAT),lods=1,installed=False,game_launched=False))
    assert f.digest(SOURCE)==selection['source_sha256']
    print('Q13 PROTOTYPE',sum(counts.values()),'triangles; dimensions',np.ptp(points,axis=0).round(3),'CMP',DEST)


if __name__=='__main__':main()
