"""Q13/02: authored maximum-form study. No game writes, textures or finalization.

Only the cockpit is borrowed. Geometry is built in native world coordinates;
all new pieces are named semantic volumes for further editing in Blender.
"""
import hashlib
import json
import secrets
import shutil
import numpy as np
import rh_freighter_q13 as q

f=q.f
B=q.B
OUT=q.OUT.parent/'q13_02'
SKIN,EDGE,DEEP,MECHANISM,GLASS=1,2,3,4,5
OBJECTS=[]


def add(name,b,closed=True):
    gs=b.groups() if isinstance(b,B) else b
    if closed:
        gs,report=q.coherent(gs)
    for g in gs:
        assert np.isfinite(g['corners']).all()
    OBJECTS.append(dict(name=name,groups=gs,closed=closed))


def yz(poly,x):
    return B().yz(np.array(poly,float),x)


def loops(b,contours,materials=SKIN):
    for i,(a,c) in enumerate(zip(contours,contours[1:])):
        b.bridge(a,c,materials[i] if isinstance(materials,list) else materials)


def solid_profile(name,poly,x0,x1,mat=SKIN):
    b=B();poly=np.array(poly,float)
    a=yz(poly,x0);c=yz(poly,x1)
    b.bridge(a,c,mat);b.face(a,mat,normal=[-1,0,0]);b.face(c,mat,normal=[1,0,0])
    add(name,b)


def scaled(poly,sx,sy,center=None):
    p=np.array(poly,float);center=p.mean(0) if center is None else np.array(center)
    return center+(p-center)*[sx,sy]


def octagon(z,y,rz,ry=None):
    # Broad flats; these are engineered housings rather than smooth balls.
    ry=rz if ry is None else ry;k=.41421356237
    return np.array([[z-rz,y-ry*k],[z-rz*k,y-ry],[z+rz*k,y-ry],[z+rz,y-ry*k],
                     [z+rz,y+ry*k],[z+rz*k,y+ry],[z-rz*k,y+ry],[z-rz,y+ry*k]])


def lower_side(side):
    # The diagonal joint is the boundary of two volumes at different depths.
    back=np.array([[-6.82,-1.75],[-4.55,-.27],[-3.06,-1.67],[5.84,.42],
                   [7.39,.39],[7.50,-1.55],[6.20,-4.118],[-5.25,-4.118]])
    face=np.array([[-6.45,-1.85],[-4.57,-.65],[-3.09,-2.06],[5.84,.05],
                   [7.06,.03],[7.12,-1.53],[5.99,-3.72],[-5.12,-3.72]])
    inner=np.array([[-5.88,-2.12],[-4.60,-1.15],[-3.16,-2.49],[5.71,-.40],
                   [6.61,-.42],[6.62,-1.58],[5.67,-3.26],[-4.96,-3.26]])
    # Broad inset field is unfinished skin: deliberately no cargo hatch/cover.
    b=B();a=yz(back,side*2.52);c=yz(face,side*3.34);d=yz(inner,side*3.34)
    e=yz(inner,side*3.10)
    loops(b,[a,c,d,e],[SKIN,EDGE,DEEP])
    b.face(a,SKIN,normal=[-side,0,0]);b.face(e,SKIN,normal=[side,0,0])
    add(f'Lower diagonal hull {side:+}',b)


def side_shell(side):
    back=np.array([[-7.55,1.26],[-4.12,3.88],[5.66,3.88],[7.42,2.5],
                   [7.42,.60],[5.82,.60],[-3.04,-1.49],[-4.56,.02],[-6.80,-1.52],[-7.55,-1.02]])
    front=np.array([[-7.14,1.13],[-4.01,3.60],[5.48,3.60],[7.05,2.35],
                    [7.05,.91],[5.77,.91],[-2.96,-1.13],[-4.51,.42],[-6.60,-1.08],[-7.14,-.72]])
    well=np.array([[-3.45,.92],[4.68,.92],[5.10,1.32],[5.10,2.87],
                   [4.66,3.30],[-3.45,3.30],[-3.83,2.92],[-3.83,1.32]])
    vent=np.array([[-6.85,-.67],[-6.85,.80],[-5.35,1.91],[-4.12,1.91],[-4.12,.85],[-5.18,-.02]])
    b=B();ls=b.panel(front,0,side*3.50,[side,0,0],SKIN,holes=[well,vent])
    # Matching refined perimeter makes the shell watertight, including pockets.
    # Boundary refinement can insert collinear points; interpolate on the back outline.
    def match_back(refined):
        result=[]
        for p in refined:
            for i,(a,c) in enumerate(zip(front,np.roll(front,-1,axis=0))):
                t=np.dot(p-a,c-a)/np.dot(c-a,c-a)
                if -.00001<=t<=1.00001 and np.linalg.norm(a+t*(c-a)-p)<1e-5:
                    result.append(back[i]+t*(back[(i+1)%len(back)]-back[i]));break
            else:raise AssertionError(p)
        return np.array(result)
    bb=match_back(ls[0]);b.bridge(yz(bb,side*2.62),yz(ls[0],side*3.50),SKIN)
    b.face(yz(bb,side*2.62),DEEP,normal=[-side,0,0])
    for i,depth in [(1,2.99),(2,2.60)]:
        b.bridge(yz(ls[i],side*3.5),yz(ls[i],side*depth),EDGE,inner=True)
        b.face(yz(ls[i],side*depth),DEEP,normal=[side,0,0])
    add(f'Faceted shoulder and intake well {side:+}',b)
    # Full-section angled louvres, clipped to the sloping perimeter.
    def span(y):
        zs=[]
        for a,c in zip(vent,np.roll(vent,-1,axis=0)):
            if min(a[1],c[1])<=y<=max(a[1],c[1]) and abs(a[1]-c[1])>1e-6:
                zs.append(a[0]+(c[0]-a[0])*(y-a[1])/(c[1]-a[1]))
        return min(zs)+.07,max(zs)-.07
    for i,y in enumerate(np.linspace(-.35,1.58,5)):
        z0,z1=span(y);z2,z3=span(y+.12)
        # Six-sided aerofoil section: lip, sloping vane, thick trailing edge.
        section=np.array([[2.68,y+.26],[3.29,y+.035],[3.39,y-.015],
                          [3.38,y-.075],[3.25,y-.075],[2.68,y+.13]])
        p0=np.array([[side*x,yy,z0] for x,yy in section]);p1=np.array([[side*x,yy,z1] for x,yy in section])
        vb=B();vb.bridge(p0,p1,EDGE);vb.face(p0,EDGE,normal=[0,0,-1]);vb.face(p1,EDGE,normal=[0,0,1])
        add(f'Intake vane {side:+} {i+1}',vb)


def side_units(side):
    # Completely new stepped octagonal units and flush recessed sockets.
    for i,z,r in [(0,-2.76,.72),(1,.66,1.11),(2,3.94,.72)]:
        y=2.08
        b=B()
        profile=[(3.00,r*1.12),(3.12,r*1.12),(3.26,r*1.01),(3.26,r*.91),
                 (3.00,r*.91)]
        rings=[yz(octagon(z,y,rr),side*x) for x,rr in profile]
        loops(b,rings,[MECHANISM,EDGE,EDGE,DEEP]);b.bridge(rings[-1],rings[0],DEEP)
        add(f'Cylinder socket {side:+} {i+1}',b)
        b=B();reach=4.70 if i==1 else 4.19
        profile=[(2.91,r*.83),(3.48,r*.83),(3.48,r*.98),(reach-.28,r*.98),
                 (reach,r*.74),(reach,r*.61),(reach-.10,r*.61)]
        rings=[yz(octagon(z,y,rr),side*x) for x,rr in profile]
        loops(b,rings,[MECHANISM,EDGE,SKIN,SKIN,EDGE,DEEP])
        b.face(rings[0],MECHANISM,normal=[-side,0,0]);b.face(rings[-1],SKIN,normal=[side,0,0])
        add(f'New transverse unit {side:+} {i+1}',b)


def section(z,w,bottom,top,corner):
    return np.array([[-w+corner,bottom,z],[w-corner,bottom,z],[w,bottom+corner,z],
        [w,top-corner,z],[w-corner,top,z],[-w+corner,top,z],[-w,top-corner,z],[-w,bottom+corner,z]])


def core():
    # Structural skin underneath the outer shoulders and diagonal belly.
    rings=[section(*s) for s in [(-8.416,1.98,-2.0786,.766,.12),(-7.62,2.40,-2.22,1.38,.26),
        (-4.10,2.72,-3.88,3.81,.37),(5.72,2.72,-3.88,3.81,.37),
        (7.72,2.47,-3.24,2.48,.42),(8.30,2.04,-2.62,1.78,.35)]]
    b=B();loops(b,rings,SKIN);b.face(rings[0],DEEP,normal=[0,0,-1]);b.face(rings[-1],DEEP,normal=[0,0,1])
    add('Continuous inner hull and cockpit neck',b)
    # Foredeck ridge: real change of slope with an inset transverse cooling trench.
    # The central field is left plain for the later texture pass (no modeled lid).
    for side in (-1,1):
        p=np.array([[-7.64,1.42],[-4.13,3.85],[-3.52,3.85],[-3.67,3.45],[-6.94,1.18]])
        solid_profile(f'Foredeck angular shoulder {side:+}',p,side*2.04,side*2.68)
    # Rear shoulders mount the engines; every connection is a closed housing.
    for side in (-1,1):
        p=[(5.24,3.79),(6.50,3.34),(7.68,2.45),(8.35,1.06),(7.80,-1.98),(6.85,-2.77),(6.25,-1.48)]
        solid_profile(f'Rear engine transition {side:+}',p,side*.35,side*3.02)


def arch(side):
    b=B();theta=np.linspace(-np.pi/2,np.pi/2,65)
    def arc(r,x):
        return np.column_stack((np.full(len(theta),side*x),q.SHELL_Y+r*np.cos(theta),q.SHELL_Z+r*np.sin(theta)))
    # Real axial depth in every concentric transition. No painted fake rings.
    profiles=[(4.909,2.35),(4.909,2.72),(4.80,2.93),(4.42,2.93),
              (4.25,2.74),(3.12,2.67),(3.02,2.82),(2.78,2.82),(2.61,2.63),(.0,2.63)]
    arcs=[arc(r,x) for r,x in profiles]
    for k,(a,c) in enumerate(zip(arcs,arcs[1:])):
        for j in range(len(theta)-1):
            b.face([a[j],a[j+1],c[j+1],c[j]],EDGE if k in (0,2,6) else SKIN,
                   normal=[side,np.cos((theta[j]+theta[j+1])/2)*.3,np.sin((theta[j]+theta[j+1])/2)*.3])
    center=[side*2.35,q.SHELL_Y,q.SHELL_Z]
    b.face(np.vstack((arcs[0],center)),DEEP,normal=[-side,0,0])
    for j in (0,-1):b.face([a[j] for a in arcs]+[center],SKIN,normal=[0,-1,0])
    add(f'Stepped circular shoulder {side:+}',b)


def roof():
    b=B();theta=np.linspace(-75,75,65)*np.pi/180
    def p(x,t,r):return [x,q.SHELL_Y+r*np.cos(t),q.SHELL_Z+r*np.sin(t)]
    # Continuous curved roof surface, plain: small lids and covers deliberately absent.
    for a,c in zip(theta,theta[1:]):
        n=[0,np.cos((a+c)/2),np.sin((a+c)/2)]
        for xa,xb,ra,rb in [(-2.32,-2.15,4.51,4.65),(-2.15,-1.96,4.65,4.65),
                           (-1.96,-1.82,4.65,4.51),(-1.82,1.82,4.51,4.51),
                           (1.82,1.96,4.51,4.65),(1.96,2.15,4.65,4.65),(2.15,2.32,4.65,4.51)]:
            b.face([p(xa,a,ra),p(xb,a,rb),p(xb,c,rb),p(xa,c,ra)],SKIN,normal=n)
        b.face([p(-2.32,a,4.34),p(-2.32,c,4.34),p(2.32,c,4.34),p(2.32,a,4.34)],DEEP,normal=-np.array(n))
        for s in (-1,1):b.face([p(s*2.32,a,4.34),p(s*2.32,a,4.51),p(s*2.32,c,4.51),p(s*2.32,c,4.34)],EDGE,normal=[s,0,0])
    for t in (theta[0],theta[-1]):
        contour=[p(x,t,r) for x,r in [(-2.32,4.51),(-2.15,4.65),(-1.96,4.65),(-1.82,4.51),
                (1.82,4.51),(1.96,4.65),(2.15,4.65),(2.32,4.51),(2.32,4.34),(-2.32,4.34)]]
        b.face(contour,EDGE,normal=[0,-np.sin(t),np.cos(t)] if t<0 else [0,np.sin(t),-np.cos(t)])
    add('Curved roof and recessed tracks',b)


def engines(side):
    # Broad polygonal shoulders with deep concentric exhaust, not borrowed retail barrels.
    x=side*2.08;y=-.28;angles=(np.arange(16)+.5)*2*np.pi/16
    def ring(z,r):return np.column_stack((x+r*np.cos(angles),y+r*np.sin(angles),np.full(16,z)))
    profile=[(6.82,.98),(7.15,1.36),(7.85,1.78),(8.17,1.86),(10.35,1.86),
        (10.87,1.61),(10.87,1.41),(11.63,1.41),(11.84,1.30),(12.158,1.30),
        (12.158,1.08),(11.82,1.04),(10.82,.83)]
    rings=[ring(z,r) for z,r in profile];b=B();loops(b,rings,
        [MECHANISM,SKIN,EDGE,SKIN,SKIN,EDGE,MECHANISM,EDGE,SKIN,EDGE,DEEP,DEEP])
    b.face(rings[0],DEEP,normal=[0,0,-1]);b.face(rings[-1],DEEP,normal=[0,0,1])
    add(f'Engine sculpted casing {side:+}',b)
    # Internal stator vanes stop short of the hot core; actual wedge sections.
    for j,t in enumerate(np.linspace(0,2*np.pi,12,endpoint=False)):
        v=B();a=[];c=[]
        for z,rad,dt in [(10.86,.32,-.03),(10.86,.80,-.03),(11.55,.97,.02),(11.55,.45,.02)]:
            a.append([x+rad*np.cos(t+dt),y+rad*np.sin(t+dt),z])
            c.append([x+rad*np.cos(t+dt+.045),y+rad*np.sin(t+dt+.045),z])
        v.bridge(np.array(a),np.array(c),MECHANISM);v.face(a,MECHANISM);v.face(c,MECHANISM)
        add(f'Exhaust stator {side:+} {j+1}',v)


def main():
    assert shutil.disk_usage(q.ROOT.anchor).free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    _,nodes=f.mesh.read_tree(q.SOURCE.read_bytes());tr,_=f.audit.transforms(nodes)
    names=f.component_map(nodes);local=f.local_geometry(nodes)
    world={names[k]:f.base.world(gs,*tr[k.lower()]) for k,gs in local.items()}
    cabin=f.clip_groups(f.clip_groups(world['Root'],2,-8.416,False),1,.82,False)
    cabin_hash=hashlib.sha256(b''.join(g['corners'].tobytes() for g in cabin)).hexdigest()
    add('Original cockpit - immutable',cabin,False)
    add('Original glazing - immutable',world['glass_lod1'],False)
    core();roof()
    for s in (-1,1):
        lower_side(s);side_shell(s);side_units(s);arch(s);engines(s)
    counts={o['name']:sum(len(g['corners']) for g in o['groups']) for o in OBJECTS}
    pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for o in OBJECTS for g in o['groups']])
    salt=secrets.token_hex(6)
    for o in OBJECTS:o['resource']=o['name'].replace(' ','_')+'_'+salt
    data=dict(objects=OBJECTS,source=str(q.SOURCE),source_sha256=f.digest(q.SOURCE),art=str(q.ART),
        art_sha256=f.digest(q.ART),salt=salt,cabin_hash=cabin_hash,
        colours={SKIN:[.43,.46,.48],EDGE:[.34,.37,.39],DEEP:[.11,.135,.15],MECHANISM:[.22,.245,.26],GLASS:[.09,.16,.20]},
        counts=counts,total_triangles=sum(counts.values()),bounds=[pts.min(0),pts.max(0)],
        stage='Geometry prototype only. No textures, small lids, hatches, LODs, SUR, damage or installation.')
    (OUT/'geometry.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'),
        default=lambda v:v.tolist() if isinstance(v,np.ndarray) else float(v)),encoding='utf8')
    summary={k:v for k,v in data.items() if k not in ('objects','colours')}
    (OUT/'build.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2,
        default=lambda v:v.tolist() if isinstance(v,np.ndarray) else float(v)),encoding='utf8')
    print(OUT.name.upper(),len(OBJECTS),'objects',sum(counts.values()),'triangles',OUT)


if __name__=='__main__':main()
