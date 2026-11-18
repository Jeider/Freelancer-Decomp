"""Revision 05: short shape iteration; accepted proportions, authored volume.

No animation authoring/video. The revision-04 rig is retained byte-for-byte.
No generic bevels; no uniform sampling of straight polygon edges.
"""
import argparse
import hashlib
import json
import shutil

import numpy as np
from scipy.spatial import Delaunay
import rh_concept_b_profile as old
from rh_redesign_paths import CONCEPT_B_VOLUME as OUT

native,mesh,audit,base=old.native,old.mesh,old.audit,old.base
PANEL,STRUCT,DARK,GRILL,UV,RED=old.PANEL,old.STRUCT,old.INNER_DARK,old.GRILL,old.UV,old.RED
DEST=OUT/'rh_concept_b_lod0.cmp'
COUNTS={}
def count(b):return sum(len(v) for v in b.tris.values())
def checkpoint(b,label,start):COUNTS[label]=COUNTS.get(label,0)+count(b)-start
def circle(center,r,n=12,phase=0):
    a=(np.arange(n)+phase)*2*np.pi/n
    return np.array(center)+r*np.column_stack((np.cos(a),np.sin(a)))

class Builder(old.Builder):
    def face(self,points,material=PANEL,uvbox=UV,normal=None,uv=None):
        p=np.asarray(points,float)
        keep=[i for i in range(len(p)) if np.linalg.norm(p[i]-p[i-1])>1e-8]
        if len(keep)<3:return
        p=p[keep]
        if np.linalg.norm(np.sum(np.cross(p,np.roll(p,-1,axis=0)),axis=0))<1e-9:return
        return super().face(p,material,uvbox,normal,None if uv is None else np.asarray(uv)[keep])
    def prism(self,*args,**kwargs):raise AssertionError('No new bevel/prism shortcut in this shape pass')
    def bar(self,*args,**kwargs):raise AssertionError('Use an authored structural contour, not a beveled bar')
    def radial(self,center,stations,sides,**kw):
        return super().radial(center,stations,min(sides,12),**kw)
    def ring(self,center,outer,inner,low,high,sides=12,**kw):
        return super().ring(center,outer,inner,low,high,min(sides,20),**kw)
    def planar(self,outer,holes,axis,level,sign=1,material=PANEL):
        # Add a midpoint only if necessary to recover a constrained boundary.
        # The previous uniform .28-unit resampling needlessly filled flat walls.
        contours=[]
        for poly in [outer,*holes]:
            p=np.asarray(poly,float)
            p=np.array([a for a,c in zip(p,np.roll(p,1,axis=0)) if np.linalg.norm(a-c)>1e-8])
            contours.append(p)
        for iteration in range(14):
            pts=np.concatenate(contours);triangles=[]
            for ids in Delaunay(pts).simplices:
                q=pts[ids].mean(0)
                if old.inside(contours[0],q) and not any(old.inside(h,q) for h in contours[1:]):triangles.append(ids)
            edges={tuple(sorted((int(a),int(c)))) for ids in triangles for a,c in zip(ids,np.roll(ids,-1))}
            missing=[];start=0
            for ci,p in enumerate(contours):
                for i in range(len(p)):
                    if tuple(sorted((start+i,start+(i+1)%len(p)))) not in edges:missing.append((ci,i))
                start+=len(p)
            if not missing:break
            for ci,p in enumerate(contours):
                contours[ci]=np.array([q for i,(a,c) in enumerate(zip(p,np.roll(p,-1,axis=0)))
                                      for q in ([a,(a+c)/2] if (ci,i) in missing else [a])])
        else:raise AssertionError(('Unrecovered contour',axis,level,missing))
        axes=[i for i in range(3) if i!=axis];n=np.zeros(3);n[axis]=sign
        span=np.maximum(np.ptp(contours[0],axis=0),.001)
        for ids in triangles:
            q=np.zeros((3,3));q[:,axis]=level;q[:,axes]=pts[ids]
            self.face(q,material,UV,n,(pts[ids]-contours[0].min(0))/span)

    def hollow_plate(self,outer,holes,low,high,axis=0):
        axes=[i for i in range(3) if i!=axis]
        for level,sign in ((low,-1),(high,1)):self.planar(outer,holes,axis,level,sign)
        for index,p in enumerate([outer,*holes]):
            p=np.asarray(p,float)
            area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
            for a,c in zip(p,np.roll(p,-1,axis=0)):
                q=np.zeros((4,3));q[:,axis]=[low,low,high,high];q[:,axes]=[a,c,c,a]
                d=c-a;n=np.zeros(3);n[axes]=np.array([d[1],-d[0]])*np.sign(area)*(-1 if index else 1)
                self.face(q,PANEL,UV,n)

def body_geometry(b,original,neck_factory=None,cabin_factory=None,include_brace=True,sill_factory=None,mount_factory=None,front_factory=None):
    start=count(b)
    sections=np.array([[-.10,2.05],[2.135,2.94],[2.135,3.136],[2.70,3.2412],
                       [4.55,3.5856],[4.627,3.60],[6.50,.85]])
    # One compound section: crown -> overhanging shoulder -> recessed cheek ->
    # deep lower sill. These are joined surfaces, not boxes pasted on a wedge.
    def section(z,top):
        lip=min(2.06,top-.30)
        half=[[1.12,top],[1.78,lip],[2.02,lip],[2.02,lip-.18],
              [1.65,lip-.18],[1.65,.16],[2.05,.16],[2.05,-.80],[1.55,-1.15]]
        p=np.array(half+[[-x,y] for x,y in half[::-1]])
        return np.column_stack((p,np.full(len(p),z)))
    rings=[section(z,t) for z,t in sections]
    # Long cheek and sill faces are authored separately so their cavities cut
    # the actual skin and are not trapped behind an uncut parent surface.
    omit=(4,6,10,12,17)
    for a,c in zip(rings,rings[1:]):
        poly=a[:,:2]
        orientation=np.sign(np.sum(poly[:,0]*np.roll(poly[:,1],-1)-poly[:,1]*np.roll(poly[:,0],-1)))
        for i in range(len(a)):
            if i in omit:continue
            j=(i+1)%len(a);q=np.array([a[i],a[j],c[j],c[i]])
            if np.linalg.norm(np.cross(q[1]-q[0],q[2]-q[0]))<1e-9:continue
            # Concave shoulder/sill steps need contour normals, not a vector
            # from the section center (which reverses their ledge undersides).
            edge=a[j,:2]-a[i,:2]
            n=np.r_[np.array([edge[1],-edge[0]])*orientation,0.]
            if abs(c[0,2]-a[0,2])<1e-9:n[2]=-1
            b.face(q,PANEL,UV,n)
    for ring,sgn in ((rings[0],-1),(rings[-1],1)):
        if sgn==-1 and front_factory is not None:front_factory(b,ring)
        else:b.face(ring,PANEL,UV,[0,0,sgn])
    cheek=np.array([[min(2.06,t-.30)-.18,z] for z,t in sections]+[[.16,6.5],[.16,-.1]])
    grille=np.array([[.34,.40],[1.60,.40],[1.60,3.28],[.34,3.28]])
    aft_well=np.array([[.38,3.60],[1.55,3.60],[1.55,4.22],[.38,4.22]])
    sill=np.array([[-.80,-.1],[.16,-.1],[.16,6.5],[-.80,6.5]])
    fields=[np.array([[-.60,z0],[-.06,z0],[-.06,z1],[-.60,z1]]) for z0,z1 in ((.30,2.0),(2.18,3.9),(4.1,5.5))]
    for side in (-1,1):
        b.planar(cheek,[grille,aft_well],0,side*1.65,side)
        b.pocket(grille,0,side*1.65,.25,side)
        b.pocket(aft_well,0,side*1.65,.16,side,STRUCT)
        for y in (.48,.71,.94,1.17,1.40):b.louver(side*1.44,y,1.84,1.36,side,.13)
        if sill_factory is None:
            b.planar(sill,fields,0,side*2.05,side)
            for p in fields:b.pocket(p,0,side*2.05,.08,side,PANEL)
        else:sill_factory(b,side,sill,fields)
    # Roof: a visible intermediate step, large recessed panel fields and paired
    # access/weapon seats from the perspective. Low-sided functional openings.
    for i,((z,t),(zz,tt)) in enumerate(zip(sections,sections[1:])):
        if zz==z:
            b.face([[-1.12,t,z],[1.12,t,z],[1.12,tt,zz],[-1.12,tt,zz]],PANEL,UV,[0,0,-1]);continue
        in_bay=z>=old.CARGO_Z0-1e-5 and zz<=old.CARGO_Z1+1e-5
        if in_bay:
            for side in (-1,1):b.face([[side*.74,t,z],[side*1.12,t,z],[side*1.12,tt,zz],[side*.74,tt,zz]],PANEL,UV,[0,1,0])
        elif i==0:
            temp=Builder();outer=[[-1.12,z],[1.12,z],[1.12,zz],[-1.12,zz]]
            holes=[circle([side*x,az],r,8) for side in (-1,1) for x,az,r in ((.85,.45,.16),(.60,1.52,.19))]
            slit=[[-.08,z+.28],[.08,z+.28],[.08,zz-.20],[-.08,zz-.20]]
            temp.planar(outer,[*holes,slit],1,0)
            for p in holes:temp.pocket(p,1,0,.12,1,STRUCT)
            temp.pocket(slit,1,0,.10)
            slope=(tt-t)/(zz-z)
            for g in temp.groups():
                v=g['corners'];v[...,1]+=t+slope*(v[...,2]-z);v[...,5]-=slope*v[...,4]
                v[...,3:6]/=np.linalg.norm(v[...,3:6],axis=-1,keepdims=True)
                b.tris[g['material']].extend(v)
        else:b.face([[-1.12,t,z],[1.12,t,z],[1.12,tt,zz],[-1.12,tt,zz]],PANEL,UV,[0,1,0])
    checkpoint(b,'compound_hull_and_real_recesses',start)
    if include_brace:brace_geometry(b)
    for side in (-1,1):
        if mount_factory is None:
            b.beam([side*1.65,old.WING_Y,7.0],old.detail.mirrored_x(old.ROOT_PIVOT,side),.60,.48)
            b.beam([side*1.72,-.65,6.15],[side*1.95,-.65,7.30],.46,.44)
        else:mount_factory(b,side)
    if neck_factory is None:neck_geometry(b)
    else:neck_factory(b)
    old.cargo_geometry(b)
    return (native.cabin_geometry(original) if cabin_factory is None else cabin_factory(original))+b.groups()

def brace_geometry(b):
    start=count(b)
    brace=old.yz([[197,150],[197,158],[203,164],[218,164],[229,156],[226,144],
                  [250,73],[247,63],[238,56],[229,59],[222,70],[205,135]])
    holes=[circle(old.yz(pixel),r,12) for pixel,r in (([238,69],.28),([214,156],.38))]
    slot=old.yz([[213,138],[220,138],[240,82],[234,82]])
    for side in (-1,1):
        # Full boot encircles the lower pin and connects the sill to the shoulder.
        b.sharp_solid(brace,*sorted((side*1.87,side*2.02)))
        b.planar(brace,[*holes,slot],0,side*2.18,side)
        for p in holes:b.pocket(p,0,side*2.18,.14,side,STRUCT)
        b.pocket(slot,0,side*2.18,.07,side,PANEL)
        for a,c in zip(brace,np.roll(brace,-1,axis=0)):
            b.face([[side*2.02,*a],[side*2.02,*c],[side*2.18,*c],[side*2.18,*a]],PANEL,UV,np.r_[0,(a+c)/2-brace.mean(0)])
    checkpoint(b,'shoulder_boots_and_attachments',start)

def neck_geometry(b):
    start=count(b)
    neck=old.yz([[336,123],[353,132],[421,133],[421,168],[351,167],[339,157]])
    openings=[old.yz(p) for p in ([[354,139],[388,139],[354,159]],
                                [[396,139],[419,140],[419,160]],
                                [[359,162],[415,162],[392,144]])]
    fork=old.yz([[337,120],[345,123],[363,154],[365,164],[355,170],[345,165],[330,132]])
    forkholes=[circle(old.yz(p),r,12) for p,r in (([339,127],.19),([353,161],.22))]
    for side in (-1,1):
        b.hollow_plate(neck,openings,*sorted((side*.94,side*1.17)))
        b.sharp_solid(fork,*sorted((side*1.17,side*1.29)))
        b.planar(fork,forkholes,0,side*1.38,side)
        for hole in forkholes:b.pocket(hole,0,side*1.38,.08,side,STRUCT)
        for a,c in zip(fork,np.roll(fork,-1,axis=0)):
            b.face([[side*1.29,*a],[side*1.29,*c],[side*1.38,*c],[side*1.38,*a]],PANEL,UV,np.r_[0,(a+c)/2-fork.mean(0)])
    b.sharp_solid([[-.48,-4.34],[.48,-4.34],[.58,-.06],[-.58,-.06]],.31,.47,axis=1)
    checkpoint(b,'neck_trusses_and_forks',start)

def frame_geometry(b,include_brace_ties=True,skin_factory=None,drum_factory=None):
    start=count(b)
    p=old.yz([[214,16],[148,16],[95,48],[95,124],[123,153],[207,153],
              [207,133],[140,133],[116,112],[116,59],[154,36],[214,36]])
    recesses=[old.yz(q) for q in ([[102,52],[151,22],[204,22],[204,30],[151,30],[108,59]],
                                [[100,67],[110,65],[110,114],[132,138],[128,145],[101,121]],
                                [[139,138],[196,138],[196,148],[139,148]])]
    if skin_factory is not None:skin_factory(b,p)
    else:
        for side in (-1,1):
            b.planar(p,recesses,0,side*1.32,side)
            for hole in recesses:b.pocket(hole,0,side*1.32,.12,side,PANEL)
    # Perimeter walls join both skins, including the inside contour of the frame.
    area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
    for i,(a,c) in enumerate(zip(p,np.roll(p,-1,axis=0))):
        if i in (0,6):continue
        d=c-a;n=np.r_[0,np.array([d[1],-d[0]])*np.sign(area)]
        b.face([[-1.32,*a],[-1.32,*c],[1.32,*c],[1.32,*a]],PANEL,UV,n)
    for index,depth in ((0,.24),(6,.16)):
        z0,z1=sorted([p[index,1],p[index+1,1]]);y=p[index,0]
        outer=[[-1.32,z0],[1.32,z0],[1.32,z1],[-1.32,z1]]
        hole=[[-.94,z0+.26],[.94,z0+.26],[.94,z1-.26],[-.94,z1-.26]]
        b.planar(outer,[hole],1,y);b.pocket(hole,1,y,depth,1,PANEL)
        if index==0:
            for zz in np.linspace(z0+.50,z1-.50,4):b.beam([-.94,y-.13,zz],[.94,y-.13,zz],.11,.11,STRUCT)
    if include_brace_ties:
        for side in (-1,1):b.beam(old.point(side*1.15,[204,35]),old.point(side*1.98,[238,69]),.36,.30)
    # Flared support plates behind the drum; their end widths are authored.
    supports=[[[168,35],[180,35],[179,52],[171,52]],[[170,120],[181,120],[186,134],[165,134]],
              [[111,81],[141,81],[141,90],[111,95]]]
    if include_brace_ties:supports.append([[208,81],[227,79],[228,90],[208,91]])
    for points in supports:
        b.sharp_solid(old.yz(points),-.33,.33)
    # Side tie plates attach at the same axial points seen in the supplied profile.
    for side in (-1,1):
        ties=[[[108,82],[146,82],[153,85],[151,90],[108,92]]]
        if include_brace_ties:ties.append([[194,82],[227,81],[230,86],[224,91],[194,91]])
        for q in ties:
            b.sharp_solid(old.yz(q),*sorted((side*1.17,side*1.32)))
        if include_brace_ties:b.beam(old.point(side*1.27,[222,86]),old.point(side*2.02,[232,86]),.32,.20)
    checkpoint(b,'frame_recesses_deck_and_ties',start)
    start=count(b)
    if drum_factory is not None:
        drum_factory(b);checkpoint(b,'central_drum',start);return
    c=old.point(0,[175,86]);b.ring(c,2.01,1.66,-.98,.98,20)
    outer=circle(c[1:],1.66,20,phase=.5)  # Exact boundary of ring(), no rotated seam.
    slots=[]
    for y in (-.88,-.44,0,.44,.88):
        half=np.sqrt((1.53)**2-y*y)-.10
        slots.append(np.array([[c[1]+y-.09,c[2]-half],[c[1]+y+.09,c[2]-half],
                               [c[1]+y+.09,c[2]+half],[c[1]+y-.09,c[2]+half]]))
    for side in (-1,1):
        b.planar(outer,slots,0,side*.98,side)
        for slot in slots:b.pocket(slot,0,side*.98,.15,side)
    checkpoint(b,'central_drum',start)

def engine_geometry(b,side):
    start=count(b);c=[side*old.ENGINE_X,old.ENGINE_Y,0];z0,z1=old.ENGINE_Z0,old.ENGINE_Z1
    b.radial(c,[(z0,.66),(z0+.23,.80),(z1-.22,.80),(z1,.67)],12,axis=2,cap=STRUCT)
    b.ring(c,.67,.51,z1,z1+.12,12,axis=2)
    a=np.arange(12)*np.pi/6
    b.face(np.column_stack((c[0]+.51*np.cos(a),c[1]+.51*np.sin(a),np.full(12,z1-.08))),GRILL,(0,0,1,1),[0,0,1])
    for z in (8.10,9.30):b.beam([side*1.28,-.30,z],[side*old.ENGINE_X,-1.08,z],.45,.28)
    checkpoint(b,'engines_pair',start)

def arm_geometry(b,side):
    start=count(b)
    for c,r in ((old.detail.mirrored_x(old.ROOT_PIVOT,side),.40),(old.detail.mirrored_x(old.ELBOW,side),.34)):
        b.radial(c,[(-.22,r),(.22,r)],12,axis=1,cap=STRUCT)
    b.beam(old.detail.mirrored_x(old.ROOT_PIVOT,side),old.detail.mirrored_x(old.ELBOW,side),.48,.42)
    checkpoint(b,'wing_bearings_pair',start)

def design(part,original):
    name=part.lower();b=Builder();side=-1 if '_port_' in name or 'baydoor01' in name else 1
    if name.startswith('rh_elite_'):return body_geometry(b,original)
    if '_tail_' in name:frame_geometry(b)
    elif '_engine_' in name:engine_geometry(b,side)
    elif '_upperarm_' in name:arm_geometry(b,side)
    elif '_wing_' in name:
        start=count(b);old.wing_geometry(b,side);checkpoint(b,'sharp_wings_pair',start)
    elif name.startswith('baydoor'):old.door_geometry(b,side)
    else:return original
    return b.groups()

def build():
    old.configure();native.OUT,native.DEST=OUT,DEST;native.design=design;native.MESH_PREFIX='rh_b5_'
    nodes=native.build();native.export(nodes)
    # This pass must not silently redesign or retime the current mechanism.
    _,before=mesh.read_tree((old.OUT/'rh_concept_b_lod0.cmp').read_bytes())
    a={p:n.blob for p,n in mesh.walk(before) if '/animation/' in p.lower() or '/cmpnd/cons/' in p.lower()}
    z={p:n.blob for p,n in mesh.walk(nodes) if '/animation/' in p.lower() or '/cmpnd/cons/' in p.lower()}
    assert a==z,'Shape iteration changed the rig'
    checks=json.loads((OUT/'checks.json').read_text())
    oldchecks=json.loads((old.OUT/'checks.json').read_text())
    checks.update(revision=5,authoring_triangle_allocation=COUNTS,animation='retained byte-for-byte from revision 04; animation work paused',
                  wing_rig=oldchecks['wing_rig'],compartment=oldchecks['compartment'],new_bevels=0,
                  shape='accepted side/top proportions; large-art stepped compound hull, shoulder boots, fork/truss joints, frame pockets and ties',
                  round_segments=dict(hub=20,engine=12,bearing=12,access_opening=8),
                  limitations=['shape prototype; not installed','no animation/video pass','SUR, distant LOD, damage caps and final UV deferred'])
    refs=OUT.parents[2]/'analysis/volume_reference';refs.mkdir(parents=True,exist_ok=True)
    for name,path in [('perspective.png','C:/Users/Freel/AppData/Local/Temp/codex-clipboard-VI12yy.png'),
                      ('brace_profile.png','C:/Users/Freel/AppData/Local/Temp/codex-clipboard-9HFge0.png')]:
        target=refs/name
        if not target.exists():shutil.copy2(path,target)
        assert target.read_bytes()==__import__('pathlib').Path(path).read_bytes()
    checks['detail_references']=[dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in refs.iterdir() if p.suffix=='.png']
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('SHAPE 05',checks['triangles'],json.dumps(COUNTS),flush=True)

if __name__=='__main__':build()
