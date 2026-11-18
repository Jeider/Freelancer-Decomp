"""RH B revision 04: authored from the user's side/top contours, offline only.

The measured cabin stays at native scale; the rest of the composition is rebuilt.
Sharp corners are deliberate. Recesses are actual holes in the surrounding skin.
"""
import argparse
import hashlib
import json
import zipfile

import numpy as np
from scipy.spatial import Delaunay

import rh_concept_b_form as native
from rh_redesign_paths import CONCEPT_B_PROFILE as OUT

mesh,audit,base,detail=native.mesh,native.audit,native.base,native.detail
PANEL,STRUCT,INNER_DARK,GRILL=native.PANEL,native.STRUCT,native.INNER_DARK,native.GRILL
UV,RED,METAL=native.UV,native.RED,native.METAL
DEST=OUT/'rh_concept_b_lod0.cmp'
REFERENCE=OUT.parents[2]/'analysis/concept_b_master_views/reference_selected.png'
# The native cabin rear and nose anchor the whole SIDE drawing without shrinking glass.
SCALE=(8.34539127-4.35)/(498-421)
def yz(points):
    p=np.asarray(points,float)
    return np.stack(((181-p[...,1])*SCALE-1.741818,-4.35+(421-p[...,0])*SCALE),axis=-1)
def point(x,pixel):return np.r_[x,yz(pixel)]

ROOT_PIVOT=np.array([2.65,-.50,7.30])
ELBOW=ROOT_PIVOT+[1.25,0,0]
ARM_ANGLE,PANEL_ANGLE=np.radians([65.,25.])
WING_Y=-.50
ENGINE_X=3.65
ENGINE_Y=-1.55
ENGINE_Z0,ENGINE_Z1=6.85,10.55
CARGO_Z0,CARGO_Z1=2.70,4.55
CARGO_X,CARGO_FLOOR=.735,-.95
BODY_SECTIONS=np.array([[-.10,2.05],[2.135,3.136],[CARGO_Z0,3.2412],
                        [CARGO_Z1,3.5856],[4.627,3.60],[6.50,.85]])
def roof(z):return np.interp(z,BODY_SECTIONS[:,0],BODY_SECTIONS[:,1])
ORIGINAL_RIG=native.rig

def rotation(angle):
    c,s=np.cos(angle),np.sin(angle)
    return np.array([[c,0,s],[0,1,0],[-s,0,c]])

def refined(poly,step=.28):
    return np.concatenate([np.linspace(a,b,max(1,int(np.ceil(np.linalg.norm(b-a)/step))),endpoint=False)
                           for a,b in zip(poly,np.roll(poly,-1,axis=0))])

def inside(poly,p):
    x,y=p;result=False
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        if (a[1]>y)!=(b[1]>y) and x<(b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:result=not result
    return result

class Builder(native.Builder):
    def planar(self,outer,holes,axis,level,sign=1,material=PANEL):
        """Triangulated planar skin with explicit, checked hole boundaries."""
        contours=[refined(np.array(p,float)) for p in [outer,*holes]]
        pts=np.concatenate(contours)
        triangles=[]
        for ids in Delaunay(pts).simplices:
            q=pts[ids].mean(0)
            if inside(contours[0],q) and not any(inside(h,q) for h in contours[1:]):triangles.append(ids)
        edges={tuple(sorted((int(a),int(b)))) for ids in triangles for a,b in zip(ids,np.roll(ids,-1))}
        start=0
        for c in contours:
            for i in range(len(c)):
                assert tuple(sorted((start+i,start+(i+1)%len(c)))) in edges,('lost authored boundary',axis,level,c[i])
            start+=len(c)
        axes=[i for i in range(3) if i!=axis];n=np.zeros(3);n[axis]=sign
        span=np.maximum(np.ptp(contours[0],axis=0),.001)
        for ids in triangles:
            p=np.zeros((3,3));p[:,axis]=level;p[:,axes]=pts[ids]
            self.face(p,material,UV,n,(pts[ids]-contours[0].min(0))/span)

    def pocket(self,contour,axis,level,depth,sign=1,floor_material=INNER_DARK):
        p=np.array(contour,float);axes=[i for i in range(3) if i!=axis]
        a=np.zeros((len(p),3));a[:,axis]=level;a[:,axes]=p
        c=a.copy();c[:,axis]-=sign*depth
        n=np.zeros(3);n[axis]=sign
        self.face(c,floor_material,UV,n)
        for i in range(len(p)):
            j=(i+1)%len(p)
            inward=np.zeros(3);inward[axes]=p.mean(0)-(p[i]+p[j])/2
            self.face([a[i],a[j],c[j],c[i]],PANEL,UV,inward)

    def sharp_solid(self,poly,low,high,axis=0,skip_edges=()):
        p=np.array(poly,float);axes=[i for i in range(3) if i!=axis]
        a=np.zeros((len(p),3));a[:,axis]=low;a[:,axes]=p
        c=a.copy();c[:,axis]=high
        n=np.zeros(3);n[axis]=1
        self.face(a,PANEL,UV,-n);self.face(c,PANEL,UV,n)
        area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
        for i in range(len(p)):
            if i in skip_edges:continue
            j=(i+1)%len(p);d=p[j]-p[i]
            normal=np.zeros(3);normal[axes]=np.array([d[1],-d[0]])*np.sign(area)
            self.face([a[i],a[j],c[j],c[i]],PANEL,UV,normal)

def body_geometry(b,original):
    # Common envelope: the vent is cut directly into its side, not an added box.
    z=BODY_SECTIONS[:,0];top=BODY_SECTIONS[:,1]
    side_poly=np.array([[t-.22,zz] for zz,t in zip(z,top)]+[[-.90,z[-1]],[-.90,z[0]]])
    vent=np.array([[.34,.28],[1.75,.28],[1.75,3.30],[.34,3.30]])
    lower=np.array([[-.71,.45],[-.23,.45],[-.23,3.40],[-.71,3.40]])
    for side in (-1,1):
        b.planar(side_poly,[vent,lower],0,side*1.85,side)
        b.pocket(vent,0,side*1.85,.23,side)
        b.pocket(lower,0,side*1.85,.055,side,PANEL)
        for y in (.51,.77,1.03,1.29,1.55):b.louver(side*1.66,y,1.79,1.43,side,.13)
        for zz,tt,zz2,tt2 in zip(z,top,z[1:],top[1:]):
            b.face([[side*1.85,tt-.22,zz],[side*1.40,tt,zz],
                    [side*1.40,tt2,zz2],[side*1.85,tt2-.22,zz2]],PANEL,UV,[side,1,0])
        b.face([[side*1.85,-.90,z[0]],[side*1.85,-.90,z[-1]],
                [side*1.45,-1.15,z[-1]],[side*1.45,-1.15,z[0]]],PANEL,UV,[side,-1,0])
    b.face([[-1.45,-1.15,z[0]],[1.45,-1.15,z[0]],[1.45,-1.15,z[-1]],[-1.45,-1.15,z[-1]]],PANEL,UV,[0,-1,0])
    # Roof surrounds the actual bay opening. Its front and aft wedges meet the side shell.
    for zz,tt,zz2,tt2 in zip(z,top,z[1:],top[1:]):
        in_bay=zz>=CARGO_Z0-1e-5 and zz2<=CARGO_Z1+1e-5
        ranges=[(-1.40,-.74),(.74,1.40)] if in_bay else [(-1.40,1.40)]
        for x0,x1 in ranges:
            if zz==z[0]:
                outer=[[x0,zz],[x1,zz],[x1,zz2],[x0,zz2]]
                holes=[[[s*.22,zz+.30],[s*1.04,zz+.30],[s*1.04,zz2-.24],[s*.22,zz2-.24]] for s in (-1,1)]
                temp=Builder();temp.planar(outer,holes,1,0)
                for hole in holes:temp.pocket(hole,1,0,.08,1,PANEL)
                slope=(tt2-tt)/(zz2-zz)
                for g in temp.groups():
                    v=g['corners'];v[...,1]+=tt+slope*(v[...,2]-zz)
                    v[...,5]-=slope*v[...,4]
                    v[...,3:6]/=np.linalg.norm(v[...,3:6],axis=-1,keepdims=True)
                    b.tris[g['material']].extend(v)
            else:b.face([[x0,tt,zz],[x1,tt,zz],[x1,tt2,zz2],[x0,tt2,zz2]],PANEL,UV,[0,1,0])
    for zz,tt,sgn in ((z[0],top[0],-1),(z[-1],top[-1],1)):
        p=[[-1.45,-1.15,zz],[1.45,-1.15,zz],[1.85,-.90,zz],[1.85,tt-.22,zz],
           [1.4,tt,zz],[-1.4,tt,zz],[-1.85,tt-.22,zz],[-1.85,-.90,zz]]
        b.face(p,PANEL,UV,[0,0,sgn])
    # Forward-leaning shoulder from the actual side art. Flat inset details do
    # not add a pile of plates; the sharp load-bearing wedge stays readable.
    brace=yz([[197,147],[224,147],[250,73],[247,63],[238,56],[229,59],[222,70]])
    for side in (-1,1):
        b.sharp_solid(brace,*sorted((side*1.85,side*2.13)))
        for pixel,r in (([238,69],.40),([214,156],.48)):
            c=point(0,pixel)
            b.ring(c,r,r*.55,*sorted((side*2.13,side*2.19)),48)
            a=np.arange(48)*2*np.pi/48
            b.face(np.column_stack((np.full(48,side*2.125),c[1]+r*.55*np.cos(a),c[2]+r*.55*np.sin(a))),STRUCT,UV,[side,0,0])
        # Twin neck trusses follow the long, low silhouette; no aft cabin flap.
        for pixels in ([[336,127],[353,136],[422,137]],[[336,161],[353,164],[422,164]]):
            points=[point(side*1.05,p) for p in pixels]
            for a,c in zip(points,points[1:]):b.beam(a,c,.28,.24)
        b.beam(point(side*1.05,[352,160]),point(side*1.05,[392,138]),.17,.17,STRUCT)
        b.beam(point(side*1.05,[392,138]),point(side*1.05,[420,161]),.17,.17,STRUCT)
        b.beam(point(side*1.05,[336,127]),point(side*1.05,[353,161]),.31,.25)
        for pixel in ([339,127],[353,161]):
            c=point(0,pixel)
            b.ring(c,.32,.16,*sorted((side*1.20,side*1.27)),32)
        # Root bearing has a structural bridge back into the body.
        b.beam([side*1.65,WING_Y,7.00],detail.mirrored_x(ROOT_PIVOT,side),.60,.48)
        b.beam([side*1.72,-.65,6.15],[side*1.95,-.65,7.30],.46,.44)
    # Narrow integral crown between the side trusses, visible in the TOP art.
    # It leaves the lateral triangular openings unobstructed.
    spine=[[-.48,-4.34],[.48,-4.34],[.58,-.06],[-.58,-.06]]
    b.sharp_solid(spine,.31,.47,axis=1)
    cargo_geometry(b)
    return native.cabin_geometry(original)+b.groups()

def cargo_geometry(b):
    x,z0,z1,floor=CARGO_X,CARGO_Z0,CARGO_Z1,CARGO_FLOOR
    b.allow_bay_metal=True
    b.face([[-x,floor,z0],[x,floor,z0],[x,floor,z1],[-x,floor,z1]],METAL,UV,[0,1,0])
    for side in (-1,1):
        b.face([[side*x,floor,z0],[side*x,floor,z1],[side*x,roof(z1),z1],[side*x,roof(z0),z0]],METAL,UV,[-side,0,0])
    for z,sgn in ((z0,1),(z1,-1)):
        b.face([[-x,floor,z],[x,floor,z],[x,roof(z),z],[-x,roof(z),z]],METAL,UV,[0,0,sgn])
    b.allow_bay_metal=False

def frame_geometry(b):
    # Authored C-shaped perimeter: heavy aft/bottom, thinner top-front strut.
    # No generic regular octagon and no rounded-off primary corners.
    pixels=[[214,16],[148,16],[95,48],[95,124],[123,153],[207,153],
            [207,133],[140,133],[116,112],[116,59],[154,36],[214,36]]
    p=yz(pixels)
    b.sharp_solid(p,-1.32,1.32,skip_edges=(0,))
    # Real top radiator pocket replaces the earlier raised transverse rails.
    z0,z1=sorted([p[0,1],p[1,1]]);level=p[0,0]
    outer=[[-1.32,z0],[1.32,z0],[1.32,z1],[-1.32,z1]]
    recess=[[-.94,z0+.26],[.94,z0+.26],[.94,z1-.26],[-.94,z1-.26]]
    b.planar(outer,[recess],1,level)
    b.pocket(recess,1,level,.24)
    for zz in np.linspace(z0+.50,z1-.50,5):
        b.beam([-.94,level-.12,zz],[.94,level-.12,zz],.10,.12,STRUCT)
    for side in (-1,1):
        # These actually meet the two side shoulder pivots across the width.
        b.beam(point(side*1.15,[204,35]),point(side*1.98,[238,69]),.36,.30)
    c=point(0,[175,86])
    # Functional spokes follow the reference's large openings.
    for pix0,pix1 in (([175,49],[175,35]),([175,122],[175,135]),([139,86],[110,86]),([209,86],[227,86])):
        b.beam(point(0,pix0),point(0,pix1),.40,.48)
    b.ring(c,2.01,1.66,-.98,.98,64)
    for side in (-1,1):
        b.ring(c,1.92,1.66,*sorted((side*.98,side*1.04)),64)
        temp=Builder();temp.slot_plate(c,1.66,side)
        for g in temp.groups():
            g['corners'][...,0]*=1.29
            g['corners'][...,3]/=1.29
            g['corners'][...,3:6]/=np.linalg.norm(g['corners'][...,3:6],axis=-1,keepdims=True)
            b.tris[g['material']].extend(g['corners'])
    # Broad horizontal spindle seat, structurally seated in the aft rim.
    for side in (-1,1):
        c=point(0,[109,87])
        b.ring(c,.48,.24,*sorted((side*1.32,side*1.38)),40)
        b.face([[side*1.322,*yz(p)] for p in [[103,82],[115,82],[115,92],[103,92]]],STRUCT,UV,[side,0,0])

def engine_geometry(b,side):
    c=[side*ENGINE_X,ENGINE_Y,0]
    stations=[(ENGINE_Z0,.55),(ENGINE_Z0+.18,.73),(ENGINE_Z0+.42,.84),
              (ENGINE_Z0+.55,.84),(ENGINE_Z0+.58,.79),(ENGINE_Z1-.40,.79),
              (ENGINE_Z1-.37,.84),(ENGINE_Z1-.20,.84),(ENGINE_Z1,.67)]
    b.radial(c,stations,40,axis=2,cap=STRUCT)
    b.ring(c,.67,.51,ENGINE_Z1,ENGINE_Z1+.12,40,axis=2)
    a=np.arange(40)*np.pi/20
    b.face(np.column_stack((c[0]+.51*np.cos(a),c[1]+.51*np.sin(a),np.full(40,ENGINE_Z1-.08))),GRILL,(0,0,1,1),[0,0,1])
    # Mount is part of the engine envelope, not floating top decoration.
    b.beam([side*1.28,-.30,8.10],[side*ENGINE_X,-1.08,8.10],.45,.28)
    b.beam([side*1.28,-.30,9.30],[side*ENGINE_X,-1.08,9.30],.45,.28)

def arm_geometry(b,side):
    for c,r in ((detail.mirrored_x(ROOT_PIVOT,side),.40),(detail.mirrored_x(ELBOW,side),.34)):
        b.radial(c,[(-.26,r*.88),(-.20,r),(.20,r),(.26,r*.88)],40,axis=1,cap=STRUCT)
    b.beam(detail.mirrored_x(ROOT_PIVOT,side),detail.mirrored_x(ELBOW,side),.48,.42)

def folded_to_open(p):
    folded_elbow=ROOT_PIVOT+rotation(ARM_ANGLE)@(ELBOW-ROOT_PIVOT)
    return (np.asarray(p)-folded_elbow)@rotation(ARM_ANGLE+PANEL_ANGLE)+ELBOW

def wing_geometry(b,side):
    # TOP contour in the folded pose, then inverse kinematics into bind geometry.
    # The sharp forward point is an actual corner, not a rounded paddle end.
    xz=np.array([[3.18,6.26],[3.35,-.03],[4.83,1.84],
                 [5.18,5.84],[4.54,6.88],[3.56,6.93]])
    skin=np.column_stack((xz[:,0],np.full(len(xz),WING_Y+.14),xz[:,1]))
    open_poly=folded_to_open(skin)
    poly=open_poly[:,[0,2]];poly[:,0]*=side
    lower=poly.copy()
    b.face(np.column_stack((lower[:,0],np.full(len(poly),WING_Y-.16),lower[:,1])),PANEL,UV,[0,-1,0])
    center=poly.mean(0)
    # Inset long field has the same wedge direction, buried below the top skin.
    inset=center+(poly-center)*np.array([.79,.64])
    b.planar(poly,[inset],1,WING_Y+.14)
    b.pocket(inset,1,WING_Y+.14,.075,1,PANEL)
    area=np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1))
    for a,c in zip(poly,np.roll(poly,-1,axis=0)):
        d=c-a;n=np.r_[d[1],0,-d[0]]*np.sign(area)
        b.face([[a[0],WING_Y-.16,a[1]],[c[0],WING_Y-.16,c[1]],
                [c[0],WING_Y+.14,c[1]],[a[0],WING_Y+.14,a[1]]],PANEL,UV,n)

def door_geometry(b,side):
    z0,z1=CARGO_Z0,CARGO_Z1
    p=np.array([[side*.015,roof(z0),z0],[side*.74,roof(z0),z0],
                [side*.74,roof(z1),z1],[side*.015,roof(z1),z1]])
    # One continuous sloped panel, no raised stamped sockets.
    b.face(p,PANEL,RED,[0,1,0])
    b.allow_bay_metal=True;b.face(p-[0,.065,0],METAL,UV,[0,-1,0]);b.allow_bay_metal=False
    for a,c in zip(p,np.roll(p,-1,axis=0)):
        b.face([a,c,c-[0,.065,0],a-[0,.065,0]],PANEL,UV,(a+c)/2-p.mean(0))

def design(part,original):
    name=part.lower();b=Builder();side=-1 if '_port_' in name or 'baydoor01' in name else 1
    if name.startswith('rh_elite_'):return body_geometry(b,original)
    if '_tail_' in name:frame_geometry(b)
    elif '_engine_' in name:engine_geometry(b,side)
    elif '_upperarm_' in name:arm_geometry(b,side)
    elif '_wing_' in name:wing_geometry(b,side)
    elif name.startswith('baydoor'):door_geometry(b,side)
    else:return original
    return b.groups()

def rig(nodes):
    ORIGINAL_RIG(nodes)
    for p,n in mesh.walk(nodes):
        if '/cmpnd/cons/' not in p.lower():continue
        size=208 if p.lower().endswith('/rev') else 176
        blob=bytearray(n.blob)
        for at in range(0,len(blob),size):
            name=mesh.string(blob[at+64:at+128]).lower();f=np.frombuffer(blob,'<f4',(size-128)//4,at+128)
            side=-1 if '_port_' in name or 'baydoor01' in name else 1
            if '_engine_' in name:f[:3]=[side*ENGINE_X,ENGINE_Y,(ENGINE_Z0+ENGINE_Z1)/2]
            elif '_tail_' in name:f[:3]=point(0,[175,86])
            elif 'baydoor' in name:
                f[:3]=[side*.74,roof(CARGO_Z0),CARGO_Z0]
                f[15:18]=mesh.unit(np.array([0,roof(CARGO_Z1)-roof(CARGO_Z0),CARGO_Z1-CARGO_Z0]))*(-side)
        n.blob=bytes(blob)
    transforms,_=audit.transforms(nodes)
    seat=folded_to_open([4.0,WING_Y+.075,2.40])
    tip=folded_to_open([3.35,WING_Y,-.03])
    for p,n in mesh.walk(nodes):
        if '/hardpoints/' not in p.lower() or not p.lower().endswith('/position'):continue
        part=p.split('/')[2].lower();hp=p.split('/')[-2].lower()
        side=-1 if '_port_' in part else 1;target=None
        if '_wing_' in part:
            if hp.startswith('hpweapon'):target=detail.mirrored_x(seat,side)
            elif hp.startswith(('hpcontrail','hpdocklight')):target=detail.mirrored_x(tip,side)
        elif '_engine_' in part:
            if hp.startswith('hpengine'):target=[side*ENGINE_X,ENGINE_Y,ENGINE_Z1+.12]
            elif hp.startswith('hprunninglight'):target=[side*ENGINE_X,ENGINE_Y,ENGINE_Z0]
            elif hp.startswith('hpmass'):target=[side*ENGINE_X,ENGINE_Y,(ENGINE_Z0+ENGINE_Z1)/2]
        elif part.startswith('rh_elite_'):
            target={'dpport_wing':detail.mirrored_x(ROOT_PIVOT,-1),'dpstarboard_wing':ROOT_PIVOT,
                    'dpport_engine':[-ENGINE_X,ENGINE_Y,8.7],'dpstarboard_engine':[ENGINE_X,ENGINE_Y,8.7],
                    'hpweapon03':[-.85,roof(.45)-.065,.45],'hpweapon04':[.85,roof(.45)-.065,.45]}.get(hp)
        if target is not None:
            r,t=transforms[part];n.blob=np.asarray(r.T@(np.asarray(target)-t),'<f4').tobytes()

def configure():
    native.OUT,native.DEST=OUT,DEST
    native.ROOT_PIVOT,native.ELBOW=ROOT_PIVOT,ELBOW
    native.ARM_ANGLE,native.PANEL_ANGLE=ARM_ANGLE,PANEL_ANGLE
    native.design,native.rig=design,rig
    native.MESH_PREFIX='rh_b4_'
    native.CARGO_MIN=np.array([-CARGO_X-.001,CARGO_FLOOR-.001,CARGO_Z0-.001])
    native.CARGO_MAX=np.array([CARGO_X+.001,roof(CARGO_Z1)+.001,CARGO_Z1+.001])

def build():
    configure();nodes=native.build();native.export(nodes)
    checks=json.loads((OUT/'checks.json').read_text())
    checks.update(revision=4,primary_reference=str(REFERENCE),reference_sha256=hashlib.sha256(REFERENCE.read_bytes()).hexdigest(),
                  wing_rig='65 degree root + 25 degree elbow, local +/-Y; t=0 open, t=end forward/inward',
                  shape='side-art scale anchored to unchanged cabin; C frame; forward shoulder; long sharp top-view panels',
                  recessed_details=['integrated side grilles','lower side fields','top frame radiator','wing panel fields','hub slots'],
                  wing_weapon_seat=folded_to_open([4.0,WING_Y+.075,2.40]).tolist(),
                  compartment=dict(x=CARGO_X,z0=CARGO_Z0,z1=CARGO_Z1,floor=CARGO_FLOOR,top0=float(roof(CARGO_Z0)),top1=float(roof(CARGO_Z1))))
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('REVISION 04',checks['triangles'],'triangles',flush=True)

def package():
    with zipfile.ZipFile(OUT/'rh_concept_b_revision_04.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in OUT.iterdir():
            if p.is_file() and p.suffix not in ('.zip','.blend1','.log'):z.write(p,p.name)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
    if args.package_only:package()
    else:build()
