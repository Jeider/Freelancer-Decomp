"""F14/02: authored planes and recesses from F14 / R02, no artistic triangle cap.

Static offline visual prototype. Native cockpit and baydoor trajectory retained.
The rejected F14/01 remains reproducible; no game or Pythonlancer writes.
"""
import copy
import argparse
import json
import math
import shutil
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree, ConvexHull
import rh_fighter_f14_form as old

f,q,B=old.f,old.q,old.B
P,R,D,P3,DARK=old.P,old.R,old.D,old.P3,old.DARK
PLAIN,FRAME=old.PLAIN,old.FRAME
OUT=old.TOPIC/'prototypes/f14_02'
RAD,CY=old.RADIUS,old.DRUM_Y
FRONT,REAR=old.DRUM_FRONT,old.DRUM_REAR
FEATURES=[]
OBJECTS=old.OBJECTS
LOWERED=False
REAR_DROP=0.0
ENGINE_Y=old.ENGINE_Y
PLACEMENT={}


def feature(key,source,description,names):
    FEATURES.append(dict(id=key,reference=source,geometry=description,objects=names))


def clean(poly):
    p=np.array(poly,float)
    return p[[i for i in range(len(p)) if np.linalg.norm(p[i]-p[i-1])>1e-8]]


def offset(poly,distance):
    p=clean(poly);area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
    sign=1 if area>0 else -1
    result=[]
    for a,b,c in zip(np.roll(p,1,axis=0),p,np.roll(p,-1,axis=0)):
        e=b-a;g=c-b;e/=np.linalg.norm(e);g/=np.linalg.norm(g)
        n1=sign*np.array([-e[1],e[0]]);n2=sign*np.array([-g[1],g[0]])
        delta=(n1+n2)*distance/max(1+np.dot(n1,n2),.1)
        result.append(b+delta)
    return np.array(result)


def points(poly,axis,value):return old.plane_points(poly,axis,value)


def panel(b,poly,axis,value,normal,mat=P,holes=()):
    return b.panel(clean(poly),axis,value,normal,mat,PLAIN,holes=holes)


def link(b,a,c,mat=P,inner=False):old.connect(b,a,c,mat,inner)


def merge_into(b,groups):
    for g in groups:
        for t in g['corners']:b.face(t[:,:3],g['material'],PLAIN,t[:,3:6].mean(0),t[:,6:8])


def fix_tjunctions(groups):
    """Split real geometric T junctions introduced by constrained hole triangulation."""
    xyz=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])
    vertices=np.unique(xyz.round(6),axis=0);tree=cKDTree(vertices);result=[];changed=0
    for g in groups:
        triangles=[]
        for tri in g['corners']:
            loop=[]
            for a,c in zip(tri,np.roll(tri,-1,axis=0)):
                loop.append(a);v=c[:3]-a[:3];length=np.linalg.norm(v)
                if length<1e-7:continue
                candidates=vertices[tree.query_ball_point((a[:3]+c[:3])/2,length*.50001+1e-5)]
                t=(candidates-a[:3])@v/(length*length)
                error=np.linalg.norm(candidates-(a[:3]+t[:,None]*v),axis=1)
                valid=(t>2e-5)&(t<1-2e-5)&(error<2e-6)
                ts=np.unique(t[valid].round(7))
                for k in sorted(ts):loop.append(a+(c-a)*k)
            if len(loop)==3:triangles.append(tri)
            else:
                changed+=1;center=tri.mean(0)
                for a,c in zip(loop,loop[1:]+loop[:1]):
                    if np.linalg.norm(np.cross(a[:3]-center[:3],c[:3]-center[:3]))>1e-8:
                        triangles.append(np.array([center,a,c]))
        result.append(dict(g,corners=np.array(triangles)))
    return result,changed


def add(name,b,category='hull',closed=True,map_point=None):
    gs=b.groups() if isinstance(b,B) else b
    if map_point:
        gs=copy.deepcopy(gs)
        for g in gs:
            for t in g['corners']:
                t[:,:3]=np.array([map_point(v[:3]) for v in t])
                n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=max(np.linalg.norm(n),1e-12)
                t[:,3:6]=n
    # Snap authored seams to the precision used by the editor before repairing
    # constrained-triangulation junctions; avoid microscopic export-only slivers.
    prepared=[]
    for g in gs:
        a=g['corners'].copy();a[...,:3]=a[...,:3].round(5).astype('<f4').astype(float)
        p=a[...,:3];keep=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)>1e-8
        if keep.any():prepared.append(dict(g,corners=a[keep]))
    gs,splits=fix_tjunctions(prepared)
    prepared=[]
    for g in gs:
        a=g['corners'];p=a[...,:3].astype('<f4').astype(float)
        keep=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)>1e-8
        if keep.any():prepared.append(dict(g,corners=a[keep]))
    gs=prepared
    old.add(name,gs,category,closed)
    OBJECTS[-1]['tjunction_triangles_split']=splits


def prism(b,poly,axis,front,back,mat=P):
    sign=1 if front>back else -1;n=np.eye(3)[axis]*sign
    ls=panel(b,poly,axis,front,n,mat)
    panel(b,ls[0],axis,back,-n,mat)
    link(b,points(ls[0],axis,front),points(ls[0],axis,back),mat)


def pocket(b,mouth,axis,front,back,normal,mat=D,wall_mat=D,lip=.045,lip_depth=.045):
    """True inset with a sloping mouth, long walls and a closed floor."""
    mouth=clean(mouth);sgn=1 if front>back else -1
    inner=offset(mouth,lip) if lip else mouth
    floor=panel(b,inner,axis,back,normal,mat)[0]
    # Resampling is repaired on the actual physical seams by fix_tjunctions().
    link(b,points(mouth,axis,front),points(inner,axis,front-sgn*lip_depth),wall_mat,True)
    link(b,points(inner,axis,front-sgn*lip_depth),points(inner,axis,back),wall_mat,True)


def slot(x0,x1,y0,y1,r=.04,segments=4):
    """Round-ended authored cut, with explicit corner contour rather than a decal."""
    r=min(r,(x1-x0)/2,(y1-y0)/2);out=[]
    for cx,cy,start in [(x1-r,y1-r,0),(x0+r,y1-r,90),(x0+r,y0+r,180),(x1-r,y0+r,270)]:
        for deg in np.linspace(start,start+90,segments+1):
            a=math.radians(deg);out.append([cx+r*math.cos(a),cy+r*math.sin(a)])
    return clean(out)


# Width is authored at the side of the hull, not a global scale of the cabin.
def side_x(z,y):return 1.59+.022*(z+.5)+.045*(y+.40)


SIDE=np.array([[-4.25,.40],[-3.05,.79],[-.55,1.14],[1.60,1.20],[2.24,.82],
               [2.15,-.56],[.93,-1.32],[-.95,-1.48],[-2.05,-1.78],[-3.78,-1.82],[-4.25,-1.44]])
WELL=np.array([[-3.24,-.21],[-1.35,.53],[1.36,.87],[1.75,.58],
               [1.36,-.56],[.48,-.70],[-.58,-.76],[-1.14,-1.05],[-2.76,-1.14],[-3.36,-.65]])
CHEEK=np.array([[-4.03,.25],[-2.99,.59],[-1.44,.80],[-2.48,.29],[-3.39,-.04]])


def side(s):
    b=B();n=np.array([s,0,0]);outer=s*1.0
    loops=panel(b,SIDE,0,outer,n,P,holes=[WELL,CHEEK])
    # The recessed mouth has its own border and angled walls, as in F14's flank.
    rim=loops[1];inner=offset(rim,.105)
    link(b,points(rim,0,outer),points(inner,0,s*.90),P,True)
    link(b,points(inner,0,s*.90),points(inner,0,s*.68),D,True)
    vents=[]
    for i in range(3):
        z=.29+i*.31
        vents.append(np.array([[z,-.03],[z+.15,.00],[z+.35,.49],[z+.20,.47]]))
    floors=panel(b,inner,0,s*.68,n,D,holes=vents)
    for v in floors[1:]:pocket(b,v,0,s*.68,s*.46,n,DARK,D,.025,.035)
    pocket(b,loops[2],0,outer,s*.91,n,R,P,.045,.035)
    # Return of the one coherent side shell. Its inside is the actual hold wall.
    panel(b,loops[0],0,s*.14,-n,D)
    link(b,points(loops[0],0,s*.14),points(loops[0],0,outer),P)
    def mapped(v):
        x,y,z=v;return [s*(side_x(z,y)-(1-abs(x))),y,z]
    name=('Port' if s<0 else 'Starboard')+'_carved_flank'
    add(name,b,map_point=mapped)
    feature('flank'+str(s),'F14 PERSPECTIVE + SIDE / FLIGHT',
        'Tapered oblique skin, stepped angular well, three deep diagonal vents, separate inset forward donor cheek',[name])


def roof_y(z):
    return float(np.interp(z,[-4.25,-3.05,-.55,1.60,2.24],[.72,.96,1.20,1.55,1.55]))


def roof_w(z):return float(np.interp(z,[-4.25,-3.05,-.55,1.60,2.24],[.91,1.02,1.12,1.19,1.22]))


def roof():
    b=B();zstations=[-4.25,-3.94,-3.05,-.55,-.40,1.60,2.24]
    # Large shoulder planes slope across the ship, unlike the discarded box.
    for s in (-1,1):
        for z0,z1 in zip(zstations,zstations[1:]):
            y0=np.interp(z0,SIDE[:5,0],SIDE[:5,1]);y1=np.interp(z1,SIDE[:5,0],SIDE[:5,1])
            a=np.array([[s*side_x(z0,y0),y0,z0],[s*side_x(z1,y1),y1,z1],
                        [s*roof_w(z1),roof_y(z1),z1],[s*roof_w(z0),roof_y(z0),z0]])
            b.face(a,P,PLAIN,[s,1,0])
            # Broad roof face between ridge edge and the native lid's channel.
            b.face([[s*.74,roof_y(z0),z0],[s*roof_w(z0),roof_y(z0),z0],
                    [s*roof_w(z1),roof_y(z1),z1],[s*.74,roof_y(z1),z1]],P,PLAIN,[0,1,0])
        # Full-length lower edge of the cargo slot, a real inner reveal.
        b.face([[s*.74,roof_y(-3.94),-3.94],[s*.74,roof_y(-.40),-.40],
                [s*.74,.94,-.40],[s*.74,.65,-3.94]],D,PLAIN,[-s,0,0])
    for z0,z1 in [(-4.25,-3.94),(-.40,1.60),(1.60,2.24)]:
        ya=1.16 if z0==-.40 else roof_y(z0);yb=roof_y(z1)
        a=np.array([[-.74,ya,z0],[.74,ya,z0],[.74,yb,z1],[-.74,yb,z1]])
        c=a.copy();c[:,1]-=.030
        b.face(a,P,PLAIN,[0,1,0]);b.face(c,D,PLAIN,[0,-1,0]);link(b,a,c,P)
        if z0==-.40:
            for s in (-1,1):
                b.face([[s*.74,ya,z0],[s*.74,roof_y(z0),z0],
                        [s*.74,roof_y(z1),z1]],P,PLAIN,[-s,0,0])
    # Solid raised low-profile roof rail strips. Section faces give the shadow.
    for s in (-1,1):
        for z0,z1 in [(-3.72,-1.75),(-1.69,.22),(.28,1.92)]:
            poly=np.array([[.81,z0],[roof_w(z0)-.035,z0+.08],
                           [roof_w(z1)-.035,z1-.08],[.81,z1]])
            top=np.array([[s*x,roof_y(z)+.045,z] for x,z in poly]);bot=top.copy();bot[:,1]-=.075
            link(b,bot,top,P);b.face(top,P,PLAIN,[0,1,0]);b.face(bot,P,PLAIN,[0,-1,0])
    add('Sculpted_roof_shoulders',b,'hull',False)
    feature('roof','F14 PERSPECTIVE / TOP',
        'Pitched roof, broad sloped shoulders, segmented upper rails, framed cargo opening', ['Sculpted_roof_shoulders'])


def keel_and_hold():
    b=B()
    # Rising lower chine: broad diagonal transition to a narrower stepped keel.
    chain=SIDE[5:]
    for s in (-1,1):
        for (z0,y0),(z1,y1) in zip(chain,chain[1:]):
            b.face([[s*side_x(z0,y0),y0,z0],[s*side_x(z1,y1),y1,z1],
                    [s*.98,y1-.20,z1],[s*.98,y0-.20,z0]],P3,PLAIN,[s,-1,0])
            b.face([[-.98,y0-.20,z0],[.98,y0-.20,z0],[.98,y1-.20,z1],[-.98,y1-.20,z1]],P,PLAIN,[0,-1,0]) if s==1 else None
    # The hold is a dedicated cavity, not the underside of a solid primitive.
    b.face([[-.82,-.70,-4.25],[.82,-.70,-4.25],[.82,-.70,2.94],[-.82,-.70,2.94]],D,PLAIN,[0,1,0])
    for s in (-1,1):
        b.face([[s*.82,-.70,-4.25],[s*.82,-.70,2.94],[s*.82,1.48,2.94],[s*.82,.63,-4.25]],D,PLAIN,[-s,0,0])
    for z,y,sgn in [(-4.25,.70,1),(2.94,1.48,-1)]:
        b.face([[-.82,-.70,z],[.82,-.70,z],[.82,y,z],[-.82,y,z]],D,PLAIN,[0,0,sgn])
    add('Root',b,'hull',False)
    # Wedge following the actual cabin's rear cross-section, not a new cabin.
    cabin=next(o for o in OBJECTS if o['name']=='Native_cabin')
    ps=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in cabin['groups']])
    p=np.unique(ps[abs(ps[:,2]+4.70)<1e-5].round(5),axis=0);p=p[ConvexHull(p[:,:2]).vertices]
    b=B();w0=side_x(-4.25,-1.44);w1=side_x(-4.25,.40)
    rear=np.array([[-w0,-1.64,-4.25],[w0,-1.64,-4.25],[w1,.40,-4.25],
                   [roof_w(-4.25),.72,-4.25],[-roof_w(-4.25),.72,-4.25],[-w1,.40,-4.25]])
    cloud=np.concatenate([p,rear]);hull=ConvexHull(cloud)
    for ids,eq in zip(hull.simplices,hull.equations):b.face(cloud[ids],P,PLAIN,eq[:3])
    add('Native_cabin_transition',b)


def lid_skin():
    # Add the modeled top lip visible on the art, retaining the real native lid
    # vertices underneath. Both travel together along the unchanged native axis.
    lid=next(o for o in OBJECTS if o['name']=='BayDoor_lod1')
    b=B();poly=old.clipped_rect(-.675,.675,-3.81,-.53,.065)
    inner=offset(poly,.065)
    def yy(z):return .740334+.087487*(z+3.889885)
    ls=panel(b,poly,1,.065,[0,1,0],P,holes=[inner])
    pocket(b,ls[1],1,.065,.025,[0,1,0],P,D,.018,.018)
    panel(b,ls[0],1,-.008,[0,-1,0],D)
    link(b,points(ls[0],1,.065),points(ls[0],1,-.008),P)
    gs=b.groups()
    for g in gs:
        for tri in g['corners']:
            for v in tri:v[1]+=yy(v[2])
            n=np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]);n/=np.linalg.norm(n);tri[:,3:6]=n
    lid['groups']+=gs
    feature('lid','F14 TOP / PERSPECTIVE','Thin modeled border and inset top skin on the native sliding lid',['BayDoor_lod1'])


def clip_poly(poly,axis,bound,greater):
    p=np.array(poly,float);out=[]
    for a,c in zip(p,np.roll(p,-1,axis=0)):
        va=a[axis]-bound;vc=c[axis]-bound
        ia=va>=-1e-9 if greater else va<=1e-9
        ic=vc>=-1e-9 if greater else vc<=1e-9
        if ia:out.append(a)
        if ia!=ic:out.append(a+(c-a)*(va/(va-vc)))
    return clean(out)


def wings(s):
    name='Port' if s<0 else 'Starboard'
    outline=np.array([[1.77,-.80],[5.08,-3.40],[5.36,-3.28],[5.36,-2.19],
                      [2.46,.86],[1.77,1.02]])
    fields=[]
    for lo,hi in [(1.94,3.12),(3.16,4.46),(4.50,5.22)]:
        poly=clip_poly(clip_poly(outline,0,lo,True),0,hi,False)
        fields.append(offset(poly,.065))
    b=B();ls=panel(b,outline,1,0,[0,1,0],P,holes=fields)
    for h in ls[1:]:pocket(b,h,1,0,-.038,[0,1,0],P,P,.025,.025)
    # The swept leading and trailing faces have actual thickness and a sloping lip.
    lower=offset(ls[0],.035)
    link(b,points(ls[0],1,0),points(lower,1,-.22),P)
    panel(b,lower,1,-.22,[0,-1,0],P3)
    def wingmap(v):
        x,y,z=v
        return [s*x,y-1.02-.285*(x-1.77),z]
    # Mirroring reverses winding; mirror after construction with proper normals.
    gs=b.groups()
    if s<0:
        for g in gs:g['corners']=g['corners'][:,[0,2,1],:]
    add(name+'_swept_wing',gs,'wing',True,wingmap)
    frame=np.array([[-1.02,-1.41],[-1.02,-.79],[-.72,-.46],[.80,-.46],
                    [1.25,-.70],[1.39,-1.35],[1.05,-1.57],[-.69,-1.57]])
    mouth=old.clipped_rect(-.88,1.10,-1.29,-.92,.055)
    b=B();normal=np.array([s,0,0])
    ls=panel(b,frame,0,s*1.91,normal,P,holes=[mouth])
    inner=offset(frame,.055)
    link(b,points(frame,0,s*1.91),points(inner,0,s*1.48),P)
    panel(b,inner,0,s*1.48,-normal,D)
    pocket(b,ls[1],0,s*1.91,s*1.56,normal,D,D,.045,.055)
    # Small inset bearing at the aft corner of the short covered carrier.
    angles=np.arange(32)*2*np.pi/32
    disc=np.column_stack([1.02+.18*np.cos(angles),-.76+.18*np.sin(angles)])
    # A ring seated in the socket, never a long exposed circular axle.
    prism(b,disc,0,s*1.928,s*1.88,P)
    add(name+'_covered_root',b,'mount')
    feature('wing'+str(s),'F14 TOP / FLIGHT and large PERSPECTIVE',
        'Thick forward-swept blade, clipped tip, modeled panel joints, tapered edges and buried short carrier with small bearing',
        [name+'_swept_wing',name+'_covered_root'])


def shoulders(s):
    name='Port' if s<0 else 'Starboard'
    profile=np.array([[.57,-1.28],[.66,-.74],[1.26,-.25],[1.92,.31],
                      [2.51,.23],[3.43,-.24],[3.43,-.63],[2.92,-.92],[1.49,-1.22]])
    pocket_shape=np.array([[1.38,-.73],[1.54,-.37],[2.36,-.30],[2.56,-.54],[2.12,-.88]])
    b=B();n=np.array([s,0,0]);ls=panel(b,profile,0,s*1.96,n,P,holes=[pocket_shape])
    pocket(b,ls[1],0,s*1.96,s*1.85,n,D,P,.055,.07)
    inside=offset(ls[0],.04)
    link(b,points(ls[0],0,s*1.96),points(inside,0,s*1.20),P)
    panel(b,inside,0,s*1.20,-n,D)
    def refit(p):
        # Keep the forward attachment in the accepted flank/root, then descend
        # to the relocated nacelle. This moves the recess together with its skin.
        p=p.copy();p[1]+=REAR_DROP*np.clip((p[2]-.57)/(2.18-.57),0,1)
        return p
    add(name+'_integrated_engine_seat',b,'mount',map_point=refit if LOWERED else None)


def engine(s):
    name='Port' if s<0 else 'Starboard';cx=s*old.ENGINE_X;cy=old.ENGINE_Y
    b=B();n=48;angle=np.arange(n)*2*np.pi/n
    def ring(z,r):return np.column_stack([cx+r*np.cos(angle),cy+r*np.sin(angle),np.full(n,z)])
    profile=[(1.76,.34),(1.84,.40),(2.04,.48),(2.18,.62),
             (2.24,.68),(2.36,.68),(2.39,.655),(3.12,.655),
             (3.15,.68),(3.27,.68),(3.42,.59),(3.53,.54),
             (3.75,.54),(3.79,.50),(4.02,.49),(4.11,.46),
             (4.11,.375),(4.03,.375),(3.99,.405),(3.89,.405),
             (3.83,.37),(3.58,.32)]
    rs=[ring(z,r) for z,r in profile]
    for i,(a,c) in enumerate(zip(rs,rs[1:])):
        # Every machined ring has a real section. The exhaust has no fake fan blades.
        mat=DARK if i>=16 else D if i in (5,7,12) else P
        if i==15:
            for j in range(n):b.face([a[j],a[(j+1)%n],c[(j+1)%n],c[j]],P,PLAIN,[0,0,1])
        else:link(b,a,c,mat,inner=i>=16)
    b.face(rs[0],D,PLAIN,[0,0,-1]);b.face(rs[-1],DARK,PLAIN,[0,0,1])
    # Four broad curved armor panels with explicit end chamfers and seams.
    for sector in range(4):
        a0=sector*np.pi/2+.025;a1=(sector+1)*np.pi/2-.025
        angles=np.linspace(a0,a1,13)
        tracks=[]
        for r in (.653,.685):
            aa=[];cc=[]
            for i,a in enumerate(angles):
                z0=2.40+(.07 if i in (0,len(angles)-1) else 0)
                z1=3.11-(.07 if i in (0,len(angles)-1) else 0)
                aa.append([cx+r*np.cos(a),cy+r*np.sin(a),z0])
                cc.append([cx+r*np.cos(a),cy+r*np.sin(a),z1])
            tracks.append((np.array(aa),np.array(cc)))
        for i in range(len(angles)-1):
            for k,sgn in [(0,-1),(1,1)]:
                a,c=tracks[k];ps=[a[i],a[i+1],c[i+1],c[i]]
                radial=np.mean(ps,axis=0)-np.array([cx,cy,np.mean(ps,axis=0)[2]])
                b.face(ps,R if sector==1 else P,PLAIN,radial*sgn)
            for end,norm in [(0,[0,0,-1]),(1,[0,0,1])]:
                a,c=tracks[0][end],tracks[1][end]
                b.face([a[i],a[i+1],c[i+1],c[i]],P,FRAME,norm)
        for i,sgn in [(0,-1),(-1,1)]:
            a,c=tracks
            theta=angles[i];normal=np.array([-np.sin(theta),np.cos(theta),0])*sgn
            b.face([a[0][i],a[1][i],c[1][i],c[0][i]],P,FRAME,normal)
    add(name+'_sculpted_engine',b,'engine',
        map_point=(lambda p:p+np.array([0,REAR_DROP,0])) if LOWERED else None)
    feature('engine'+str(s),'F14_R02 large REAR 3/4',
        'Compact shoulder-mounted nacelle, segmented curved casing, two collar bands, stepped tapered nozzle and deep closed throat',
        [name+'_sculpted_engine',name+'_integrated_engine_seat'])


def arc(radius,lo,hi,count=20):
    a=np.radians(np.linspace(lo,hi,count))
    return np.column_stack([radius*np.cos(a),CY+radius*np.sin(a)])


def face_plate(b,poly,front,back,material=P,face_sign=-1):
    # Continuous shallow armor field: step at its perimeter, no floating plaque.
    poly=clean(poly);small=offset(poly,.025)
    n=np.array([0,0,face_sign]);ls=panel(b,small,2,front,n,material)
    panel(b,poly,2,back,-n,material)
    link(b,points(small,2,front),points(poly,2,back),material)


def drum():
    b=B();n=96;angles=np.arange(n)*2*np.pi/n
    def circle(r):return np.column_stack([r*np.cos(angles),CY+r*np.sin(angles)])
    def ring(r,z):return points(circle(r),2,z)
    # Rail shoulders and the segmented central skin have the exact fixed envelope.
    section=[(RAD-.115,FRONT),(RAD-.035,FRONT+.025),(RAD,FRONT+.07),
             (RAD,FRONT+.13),(RAD-.065,FRONT+.15),
             (RAD-.065,REAR-.15),(RAD,REAR-.13),(RAD,REAR-.07),
             (RAD-.035,REAR-.025),(RAD-.115,REAR)]
    rings=[ring(r,z) for r,z in section]
    for i in range(len(rings)-1):link(b,rings[i],rings[i+1],D if i==4 else P)
    rface=RAD-.22
    for a,z,sgn in [(rings[0],FRONT+.09,-1),(rings[-1],REAR-.09,1)]:
        c=ring(rface,z)
        for i in range(n):
            j=(i+1)%n;b.face([a[i],a[j],c[j],c[i]],P,FRAME,[0,0,sgn])
    # A dozen broad outer sections, each with a seam and slightly recessed ends.
    for sector in range(12):
        a0=sector*np.pi/6+.006;a1=(sector+1)*np.pi/6-.006
        aa=np.linspace(a0,a1,9)
        tracks=[]
        for r in (RAD-.068,RAD-.006):
            tracks.append([np.array([[r*np.cos(a),CY+r*np.sin(a),z] for a in aa])
                           for z in (FRONT+.17,REAR-.17)])
        for i in range(8):
            for k,sgn in [(0,-1),(1,1)]:
                a,c=tracks[k];ps=np.array([a[i],a[i+1],c[i+1],c[i]])
                normal=ps.mean(0)-np.array([0,CY,ps[:,2].mean()])
                b.face(ps,R if sector in (1,2,4,7,10) else P,PLAIN,normal*sgn)
            for end,sgn in [(0,-1),(1,1)]:
                a,c=tracks[0][end],tracks[1][end]
                b.face([a[i],a[i+1],c[i+1],c[i]],P,FRAME,[0,0,sgn])
        for i,sgn in [(0,-1),(-1,1)]:
            a,c=tracks;normal=np.array([-np.sin(aa[i]),np.cos(aa[i]),0])*sgn
            b.face([a[0][i],a[1][i],c[1][i],c[0][i]],P,FRAME,normal)
    front=FRONT+.09;rear=REAR-.09
    trap=np.array([[-1.24,CY+1.48],[1.24,CY+1.48],[.64,1.57+REAR_DROP],[-.64,1.57+REAR_DROP]])
    # The native lid still travels at its original height. On the lowered drum,
    # its receiver occupies the now-hidden lower portion of the front recess.
    # Trim only that buried portion; keep the visible lip/slot in translated art
    # coordinates. Extend the receiver down around the unchanged cargo floor.
    if LOWERED:trap=clip_poly(trap,1,1.51,True)
    cargo=old.clipped_rect(-.84,.84,-.77 if LOWERED else .61,1.48,.035)
    ls=panel(b,circle(rface),2,front,[0,0,-1],P,holes=[trap,cargo])
    # Two-stage reveal around the trapezoid. Its five slots remain real tunnels
    # into a closed backing, not raised bars over a flat disc.
    inner=offset(ls[1],.075)
    link(b,points(ls[1],2,front),points(inner,2,front+.095),P,True)
    link(b,points(inner,2,front+.095),points(inner,2,front+.25),D,True)
    slots=[]
    for i in range(5):
        y=CY+1.23-i*.265;half=.98-i*.078
        if not LOWERED or y-.12>inner[:,1].min()+.025:
            slots.append(slot(-half,half,y-.12,y+.05,.055,5))
    floor=panel(b,inner,2,front+.25,[0,0,-1],D,holes=slots)
    for hole in floor[1:]:pocket(b,hole,2,front+.25,front+.40,[0,0,-1],DARK,D,.018,.035)
    if not LOWERED:
        service=np.array([[-.44,1.72],[.44,1.72],[.52,1.96],[-.52,1.96]])
        face_plate(b,service,front+.22,front+.255,D,-1)
    pocket(b,ls[2],2,front,3.055,[0,0,-1],D,D,.015,.025)
    # The three large donor fields follow the art's actual unequal division.
    crown=np.concatenate([arc(rface-.025,49,132,25),np.array([[-1.13,CY+1.54],[1.12,CY+1.54]])])
    left=np.concatenate([arc(rface-.025,134,234,27),np.array([[-.91,1.50+REAR_DROP],[-1.30,CY+1.40]])])
    right=np.concatenate([arc(rface-.025,-54,47,28),
                          np.array([[1.30,CY+1.40],[.91,1.50+REAR_DROP]])])
    for poly,mat in [(crown,P),(left,R),(right,P)]:face_plate(b,poly,FRONT+.035,front+.006,mat,-1)
    # R02 rear: broad hourglass spine, large angled openings and deep closed wells.
    left=np.array([[-.66,CY+1.45],[-1.17,CY+1.45],[-1.70,CY+.91],
                   [-1.91,CY+.10],[-1.65,CY-.78],[-1.13,CY-1.49],
                   [-.63,CY-1.49],[-.36,CY-.02]])
    right=left.copy();right[:,0]*=-1
    ls=panel(b,circle(rface),2,rear,[0,0,1],P,holes=[left,right])
    for side,mouth in zip((-1,1),ls[1:]):
        inside=offset(mouth,.075)
        link(b,points(mouth,2,rear),points(inside,2,rear-.105),P,True)
        link(b,points(inside,2,rear-.105),points(inside,2,3.095),D,True)
        panel(b,inside,2,3.095,[0,0,1],D)
        for y in (CY-.60,CY+.37):
            def cuts(height):
                xs=[]
                for a,c in zip(inside,np.roll(inside,-1,axis=0)):
                    if min(a[1],c[1])<=height<=max(a[1],c[1]) and abs(a[1]-c[1])>1e-6:
                        xs.append(a[0]+(c[0]-a[0])*(height-a[1])/(c[1]-a[1]))
                return min(xs),max(xs)
            lo=max(cuts(y-.10)[0],cuts(y+.11)[0])+.01
            hi=min(cuts(y-.10)[1],cuts(y+.11)[1])-.01
            prof=np.array([[3.09,y-.11],[3.40,y-.11],[3.40,y-.025],[3.09,y+.12]])
            a=points(prof,0,lo);c=points(prof,0,hi)
            link(b,a,c,D);b.face(a,D,PLAIN,[-1,0,0]);b.face(c,D,PLAIN,[1,0,0])
    web=np.array([[-.62,CY+1.77],[.62,CY+1.77],[.31,CY-.025],[.55,CY-1.54],
                  [-.55,CY-1.54],[-.31,CY-.025]])
    for lo,hi in [(CY+.74,CY+1.80),(CY-.49,CY+.715),(CY-1.56,CY-.515)]:
        p=clip_poly(clip_poly(web,1,lo,True),1,hi,False)
        face_plate(b,p,REAR-.045,rear-.005,P,1)
    add('Armored_transverse_drum',b,'drum')
    feature('drum_front','F14 PERSPECTIVE',
        ('Lowered drum; visible translated armor and trapezoid lip retained; buried lower front detail replaced by native-height cargo receiver'
         if LOWERED else 'Three unequal armor fields, segmented outer skin and double rail, sloped trapezoid reveal, five deep rounded slots and lower inset service field'),
        ['Armored_transverse_drum'])
    feature('drum_rear','F14_R02 REAR 3/4',
        'Angled well mouths with two-stage reveals, broad sloping internal ledges and segmented hourglass central spine',
        ['Armored_transverse_drum'])


def stern():
    b=B();outline=np.array([[-1.27,-.13],[1.27,-.13],[1.29,-.92],[1.06,-1.04],[-1.06,-1.04],[-1.29,-.92]])
    mouth=np.array([[-.96,-.37],[.96,-.37],[.76,-.87],[-.76,-.87]])
    ls=panel(b,outline,2,3.44,[0,0,1],P,holes=[mouth])
    pocket(b,ls[1],2,3.44,3.17,[0,0,1],D,D,.035,.045)
    panel(b,ls[0],2,3.12,[0,0,-1],D)
    link(b,points(ls[0],2,3.44),points(ls[0],2,3.12),P)
    for y in (-.49,-.69):
        p=old.clipped_rect(-.72,.72,y-.035,y+.035,.025)
        prism(b,p,2,3.215,3.165,D)
    add('Stern_receiver_fascia',b,'hull',map_point=(lambda p:p+np.array([0,REAR_DROP,0])) if LOWERED else None)
    # Tapered bottom continuation joins the narrow keel to the receiving fascia.
    a=np.array([[-1.02,-1.30,1.48],[1.02,-1.30,1.48],[1.25,-.30,1.48],[-1.25,-.30,1.48]])
    c=np.array([[-1.07,-1.035,3.14],[1.07,-1.035,3.14],[1.25,-.29,3.14],[-1.25,-.29,3.14]])
    c[:,1]+=REAR_DROP
    b=B();link(b,a,c,P);b.face(a,D,PLAIN,[0,0,-1]);b.face(c,D,PLAIN,[0,0,1])
    add('Tapered_lower_receiver',b,'hull')
    feature('stern_channel','F14_R02 REAR 3/4 / REAR',
        'Closed central receiving recess with tapered corners and two internal steps between the engines',
        ['Stern_receiver_fascia','Tapered_lower_receiver'])


def main():
    global OUT,LOWERED,CY,REAR_DROP,ENGINE_Y,PLACEMENT
    ap=argparse.ArgumentParser()
    ap.add_argument('--variant',choices=('f14_02','f14_03'),default='f14_02')
    args=ap.parse_args();LOWERED=args.variant=='f14_03'
    OUT=old.TOPIC/'prototypes'/args.variant
    assert shutil.disk_usage(old.ROOT).free>3*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    selected=json.loads((old.TOPIC/'selection.json').read_text(encoding='utf8'))
    assert f.digest(old.SOURCE)==selected['source_sha256']
    sources=[old.SOURCE,old.MAT,old.ENV,old.TOPIC/selected['art'],old.TOPIC/selected['rear_view']['art']]
    pins={p.as_posix():f.digest(p) for p in sources}
    header,ns=f.mesh.read_tree(old.SOURCE.read_bytes());OBJECTS.clear();FEATURES.clear()
    native=old.native_parts(ns)
    if LOWERED:
        glass=next(e for e in OBJECTS if e['name']=='glass_lod1')
        xyz=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in glass['groups']])
        ENGINE_Y=float((xyz[:,1].min()+xyz[:,1].max())/2)
        REAR_DROP=ENGINE_Y-old.ENGINE_Y;CY=old.DRUM_Y+REAR_DROP
        PLACEMENT=dict(datum='Mid-height of immutable native cockpit glazing bounds',
            cockpit_glass_y_bounds=[float(xyz[:,1].min()),float(xyz[:,1].max())],
            engine_axis_y=ENGINE_Y,previous_engine_axis_y=old.ENGINE_Y,
            rear_translation_y=REAR_DROP,drum_center_y=CY,previous_drum_center_y=old.DRUM_Y,
            baydoor_path_unchanged=True,cabin_unchanged=True,
            prior_40_60_ratio_superseded_by='User: engines at cockpit level; rear drum lowered correspondingly')
    for s in (-1,1):side(s);wings(s);shoulders(s);engine(s)
    roof();keel_and_hold();lid_skin();drum();stern()
    materials=f.audit.material_table([old.MAT,old.ENV]);used={g['material'] for e in OBJECTS for g in e['groups']}
    assert used<=materials.keys()
    assert all('metal' not in materials[mid]['texture'].lower() for mid in used)
    palette={};td=OUT/'textures';td.mkdir(exist_ok=True)
    for mid in used:
        mat=materials[mid];m={k:v for k,v in mat.items() if k!='image'};m['image_path']=None
        if mat['image']:
            path=td/(mat['texture'].replace('.tga','')+'.png')
            if not path.exists():mat['image'].save(path)
            m['image_path']=path.as_posix()
        palette[str(mid)]=m
    exports=[old.export_cmp(header,OBJECTS,OUT/'rh_pir_fighter_f14_open.cmp'),
             old.export_cmp(header,OBJECTS,OUT/'rh_pir_fighter_f14_bay_open.cmp',True)]
    points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for e in OBJECTS for g in e['groups']])
    report=dict(source=old.SOURCE.as_posix(),source_sha256=f.digest(old.SOURCE),sources=pins,native=native,
        art=selected['art'],rear_art=selected['rear_view']['art'],features=FEATURES,
        revision=('F14/03: engines at cockpit level and rear drum lowered with them' if LOWERED else
                  'F14/02: authored form and cutouts; F14/01 rejected by user'),artistic_polygon_limit=None,
        placement=PLACEMENT,
        drum=dict(radius=RAD,diameter=2*RAD,center_y=CY,local_roof_y=old.DECK_Y,
                  submerged_height_fraction=(old.DECK_Y-CY+RAD)/(2*RAD),front_z=FRONT,rear_z=REAR),
        dimensions=dict(main_side_width_at_midheight=2*side_x(0,0),previous_side_width=2.70,
                        extended_span=10.72,previous_span=9.88),
        objects=OBJECTS,materials=palette,exports=exports,native_hardpoints_reference=f.hp_world(ns),
        bounds=[points.min(0),points.max(0)],total_triangles=sum(len(g['corners']) for e in OBJECTS for g in e['groups']),
        stage='Detailed static shape prototype; art-driven surfaces and real recesses. UV and rig provisional.',
        installed=False,game_launched=False)
    old.dump(OUT/'geometry.json',report)
    for p,h in pins.items():assert f.digest(Path(p))==h
    print(json.dumps(dict(output=str(OUT),triangles=report['total_triangles'],objects=len(OBJECTS),
                         width=report['dimensions'],features=len(FEATURES)),indent=2))


if __name__=='__main__':main()
