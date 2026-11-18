"""Revision 06: native RH cabin transition, closer engines, deliberate RH UVs.

Offline shape prototype. Animation tracks are retained; no game installation.
"""
import copy
import hashlib
import json

import numpy as np
from scipy.spatial import ConvexHull
import rh_concept_b_volume as previous
from rh_redesign_paths import CONCEPT_B_ATTACHMENTS as OUT

old,native,mesh,audit,base=previous.old,previous.native,previous.mesh,previous.audit,previous.base
DEST=OUT/'rh_concept_b_lod0.cmp'
SOURCE=audit.DATA/'ships/rheinland/rh_elite/rh_elite.cmp'
LIBRARY=audit.DATA/'ships/rheinland/rh_pir_playerships.mat'
SHIFT=np.array([0.,.591818,2.70])
ENGINE_X=3.15
PANEL=mesh.crc('pir_r_panel01_256')
PANEL2=mesh.crc('pir_r_panel02_256')
DARK=mesh.crc('pir_r_panel01_256D')
VOID=mesh.crc('pir_r-dark gray')
WEAPON=mesh.crc('weaponplate')
PLAIN=(.505,.258,.997,.854)
STRIP=(.52,.103,.99,.164)
EDGE=(.001,.258,.091,.854)
GRID=(.001,.001,.336,.501)
RED_PANEL=(.337,.321,.663,.498)
HATCH=(.15,.28,.49,.55)
ROUND_HATCH=(.15,.57,.49,.85)
REMAP={mesh.crc('r_panel01_256'):PANEL,mesh.crc('r_panel02_256'):PANEL2,
       mesh.crc('r_panel01_256D'):DARK,mesh.crc('r-dark gray'):VOID}
SOURCE_SCENE=[]
PIRATE_SCENE=[]
COUNTS={}


class Builder(previous.Builder):
    in_recess=False
    part='body'
    panel_context=None

    def explicit(self,p,material,box,normal=None,uv=None):
        if uv is None and box==STRIP:
            p=np.asarray(p,float);edges=np.roll(p,-1,axis=0)-p
            u=mesh.unit(edges[np.argmax(np.linalg.norm(edges,axis=1))])
            n=mesh.unit(np.sum(np.cross(p,np.roll(p,-1,axis=0)),axis=0));v=np.cross(n,u)
            q=np.column_stack((p@u,p@v));span=np.maximum(np.ptp(q,axis=0),1e-6)
            uv=(q-q.min(0))/span
            # Fit a source strip at its actual texel aspect. Crop its quiet
            # middle when needed rather than stretching it along the support.
            ratio=span[0]/span[1];w,h=min(.47,.061*ratio),min(.061,.47/ratio)
            box=(.52,.1335-h/2,.52+w,.1335+h/2)
        return super().face(p,material,box,normal,uv)

    def face(self,points,material=previous.PANEL,uvbox=previous.UV,normal=None,uv=None):
        p=np.asarray(points,float)
        supplied_uv=uv is not None
        if material==old.METAL and self.allow_bay_metal:
            return super().face(p,material,uvbox,normal,uv)
        if uvbox not in (previous.UV,previous.RED):return self.explicit(p,material,uvbox,normal,uv)
        mapped=DARK if material==previous.STRUCT else VOID if material==previous.DARK else PANEL
        box=PLAIN
        if uvbox==previous.RED:mapped,box=PANEL2,RED_PANEL
        span=np.ptp(p,axis=0);axes=np.argsort(span)[-2:];q=p[:,axes]
        if uv is None:uv=(q-q.min(0))/np.maximum(np.ptp(q,axis=0),1e-6)
        if self.in_recess:mapped,box=DARK,PLAIN
        elif not supplied_uv and span[axes[1]]>.6 and span[axes[1]]/max(span[axes[0]],1e-6)>2.7:
            # Unwrap long existing ledges lengthwise. The old planar projection
            # fitted a whole square onto each strip and stretched the grain.
            uv=None;box=STRIP
        if self.panel_context is not None and not self.in_recess:
            outer,axis=self.panel_context
            if self.part=='tail' and axis==0 and np.ptp(outer,axis=0).max()>5:
                # The C-frame's five straight runs get long border strips,
                # independently of its irregular triangulation around pockets.
                yz=p[:,1:3];center=yz.mean(0);candidates=[]
                for i in range(5):
                    a,c=outer[i],outer[i+1];ia,ic=outer[11-i],outer[10-i]
                    mid0,mid1=(a+ia)/2,(c+ic)/2;d=mid1-mid0
                    t=np.clip(np.dot(center-mid0,d)/np.dot(d,d),0,1)
                    candidates.append((np.linalg.norm(center-(mid0+t*d)),a,c,ia))
                _,a,c,ia=min(candidates,key=lambda v:v[0]);d=c-a;length=np.linalg.norm(d);u=d/length
                w=ia-a;w-=np.dot(w,u)*u;width=np.linalg.norm(w);v=w/max(width,1e-6)
                uv=np.column_stack(((yz-a)@v/max(width,1e-6),(yz-a)@u/length))
                box=EDGE
            elif self.part=='wing':
                # Rim and inset read as separate pieces of the same wing.
                box=PLAIN
            elif self.part=='tail' and axis==0 and 3.2<np.ptp(outer,axis=0).max()<3.4:
                # The source's rear circular service cover, not another blank
                # square projected onto the slotted face of the drum.
                box=(.127,.565,.503,.876)
        return self.explicit(p,mapped,box,normal,uv)

    def planar(self,outer,holes,axis,level,sign=1,material=previous.PANEL):
        saved=self.panel_context;self.panel_context=(np.asarray(outer),axis)
        super().planar(outer,holes,axis,level,sign,material)
        self.panel_context=saved

    def pocket(self,contour,axis,level,depth,sign=1,floor_material=previous.DARK):
        # Both reveals and backing are dark exterior armor. Never bay metal.
        p=np.array(contour,float);axes=[i for i in range(3) if i!=axis]
        a=np.zeros((len(p),3));a[:,axis]=level;a[:,axes]=p
        c=a.copy();c[:,axis]-=sign*depth;n=np.zeros(3);n[axis]=sign
        size=np.ptp(p,axis=0);center=p.mean(0)
        # The closed dark backing of slots/grilles stays quiet. Service fields
        # use the pirate red strapped panels the user selected from the source.
        service=(self.part=='wing' or (axis==0 and self.part=='body' and center[0]<.2)
                 or (self.part=='tail' and (size.max()>2 or axis==1)))
        if service:
            order=np.argsort(size);q=p[:,order]
            uv=(q-q.min(0))/np.maximum(np.ptp(q,axis=0),1e-6)
            self.explicit(c,PANEL2,(.003,.005,.166,.499),n,uv)
        else:self.explicit(c,DARK,PLAIN,n)
        for i in range(len(p)):
            j=(i+1)%len(p);inward=np.zeros(3);inward[axes]=p.mean(0)-(p[i]+p[j])/2
            self.explicit([a[i],a[j],c[j],c[i]],DARK,STRIP,inward,[[0,0],[1,0],[1,1],[0,1]])

    def ring(self,center,outer,inner,low,high,sides=12,axis=0,**kw):
        if self.part!='tail' or outer<1.9:return super().ring(center,outer,inner,low,high,sides,axis,**kw)
        center=np.asarray(center,float);sides=20
        # Circumference is divided into four continuous islands (five sides
        # each). Their physical aspect closely matches the source panel grid.
        angles=(np.arange(sides)+.5)*2*np.pi/sides;rings=[]
        for x,r in ((high,outer),(high,inner),(low,inner),(low,outer)):
            rings.append(center+np.column_stack((np.full(sides,x),np.cos(angles)*r,np.sin(angles)*r)))
        for k,(a,c) in enumerate(zip(rings,rings[1:]+rings[:1])):
            for i in range(sides):
                j=(i+1)%sides;p=np.array([a[i],a[j],c[j],c[i]])
                t0,t1=(i%5)/5,(i%5+1)/5
                n=p.mean(0)-center
                if k in (0,2):
                    n[:]=0;n[0]=1 if k==0 else -1
                    self.explicit(p,PANEL,EDGE,n,[[0,t0],[0,t1],[1,t1],[1,t0]])
                else:
                    n[0]=0
                    if k==1:n=-n
                    self.explicit(p,PANEL2,GRID,n,[[0,t0],[0,t1],[1,t1],[1,t0]])


def clipped(groups,minimum=-np.inf,maximum=np.inf):
    """Clip actual source triangles, interpolating their normals and UVs."""
    out=[]
    for g in groups:
        triangles=[]
        for t in g['corners']:
            poly=list(t.copy())
            for z,sign in ((minimum,1),(maximum,-1)):
                if not np.isfinite(z):continue
                q=[]
                for a,b in zip(poly,poly[1:]+poly[:1]):
                    ain,bin=sign*(a[2]-z)>=-1e-7,sign*(b[2]-z)>=-1e-7
                    if ain:q.append(a)
                    if ain!=bin:
                        c=a+(b-a)*((z-a[2])/(b[2]-a[2]));c[3:6]=mesh.unit(c[3:6]);q.append(c)
                poly=q
                if not poly:break
            for i in range(1,len(poly)-1):
                tri=np.array([poly[0],poly[i],poly[i+1]])
                if np.linalg.norm(np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3]))>1e-8:triangles.append(tri)
        if triangles:out.append(dict(g,corners=np.array(triangles)))
    return out


def cabin(original):
    # Keep the repaired native glazing borders. Replace the previous custom aft
    # shell with the real RH transition at exactly the same source cross section.
    groups=clipped(native.cabin_geometry(original),maximum=-4.80157)
    removed=0
    for g in groups:
        keep=~np.any(g['corners'][...,1]<-1.742,axis=1)
        removed+=int((~keep).sum());g['corners']=g['corners'][keep]
    # Close the floor at the measured outer contour after removing the chin.
    groups=closed_floor(groups,-1.741818,PANEL,PLAIN)
    COUNTS['removed_chin_triangles']=removed
    for g in groups:
        g['corners'][...,:3]+=SHIFT
        g['material']=REMAP.get(g['material'],g['material'])
    return [g for g in groups if len(g['corners'])]


def closed_floor(groups,y,material,box):
    boundary=[]
    for g in groups:
        p=g['corners'][...,:3]
        boundary.extend(p[np.isclose(p[...,1],y,atol=1e-4)][:,(0,2)])
        coplanar=np.all(np.isclose(p[...,1],y,atol=1e-4),axis=1)
        g['corners']=g['corners'][~coplanar]
    q=np.unique(np.asarray(boundary).round(6),axis=0)
    assert len(q)>=3
    q=q[ConvexHull(q).vertices]
    b=Builder();b.explicit(np.column_stack((q[:,0],np.full(len(q),y),q[:,1])),material,box,[0,-1,0])
    return [g for g in groups+b.groups() if len(g['corners'])]


def neck(b):
    groups=[g for g in SOURCE_SCENE if g['part'].lower().startswith('rh_elite_')
            and g['material'] in (*REMAP,WEAPON)]
    # The back .20 units enter the body shell; no floating bracket or red flap.
    groups=clipped(groups,-4.80157,-2.60)
    for g in groups:
        p=g['corners'][...,:3]
        p[...,1]=np.where(p[...,1]<-1.60,-1.741818,p[...,1])
        g['corners'][...,:3]+=SHIFT
        p[...,1]=np.minimum(p[...,1],1.1763+(p[...,2]+2.10157)/2.20157*(2.04-1.1763))
        n=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);length=np.linalg.norm(n,axis=1)
        keep=length>1e-8;g['corners']=g['corners'][keep];n=n[keep]/length[keep,None]
        g['corners'][...,3:6]=n[:,None,:]
        g['material']=REMAP.get(g['material'],g['material'])
    groups=closed_floor(groups,-1.15,PANEL2,GRID)
    for g in groups:b.tris[g['material']].extend(g['corners'])
    COUNTS['native_transition']=sum(len(g['corners']) for g in groups)


def body(original):
    b=Builder()
    groups=previous.body_geometry(b,original,neck_factory=neck,cabin_factory=cabin,include_brace=False)
    # Replace the compound hull's bottom, whose former per-section UV repeated
    # a whole armor field. Continuous side strips surround three service panels.
    for g in groups:
        p=g['corners'][...,:3]
        bottom=(np.all(np.isclose(p[...,1],-1.15,atol=1e-6),axis=1)
                & np.all(p[...,2]>=-.100001,axis=1) & np.all(p[...,2]<=6.500001,axis=1))
        g['corners']=g['corners'][~bottom]
    floor=Builder()
    def panel(x0,x1,z0,z1,mat,box,rail=False):
        floor.explicit([[x0,-1.15,z0],[x1,-1.15,z0],[x1,-1.15,z1],[x0,-1.15,z1]],mat,box,[0,-1,0],
                   [[0,0],[0,1],[1,1],[1,0]] if rail else [[0,0],[1,0],[1,1],[0,1]])
    for x0,x1 in ((-1.55,-.80),(.80,1.55)):panel(x0,x1,-.10,6.50,PANEL,(.001,.859,.999,.998),True)
    # Match the actual pirate underside: two columns of strapped red service
    # panels, with one continuous map down the keel. No invented hatch collage.
    panel(-.80,.80,-.10,6.50,PANEL2,(.001,.001,.336,1.36))
    return [g for g in groups+floor.groups() if len(g['corners'])]


def engine(b,side):
    name='_port_engine_' if side<0 else '_starboard_engine_'
    groups=copy.deepcopy([g for g in PIRATE_SCENE if name in g['part'].lower()])
    # Reuse the actual source barrel and its seam layout. Its UVs wrap around
    # the cylinder and collar correctly; no square atlas per cylinder facet.
    pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])
    lo,hi=pts.min(0),pts.max(0);center=(lo+hi)/2
    scale=np.array([1.50/(hi[0]-lo[0]),1.50/(hi[1]-lo[1]),(old.ENGINE_Z1-old.ENGINE_Z0)/(hi[2]-lo[2])])
    target=np.array([side*ENGINE_X,old.ENGINE_Y,(old.ENGINE_Z0+old.ENGINE_Z1)/2])
    for g in groups:
        g['corners'][...,:3]=(g['corners'][...,:3]-center)*scale+target
        n=g['corners'][...,3:6]/scale;n/=np.linalg.norm(n,axis=-1,keepdims=True);g['corners'][...,3:6]=n
        b.tris[g['material']].extend(g['corners'])
    COUNTS['engine_native_triangles']=sum(len(g['corners']) for g in groups)
    # Native RH uses swept, tapering cheek supports, not two parallel rods.
    # Adapt that continuous load path to this design's aft engine position.
    contour=np.array([[1.20,6.12],[1.75,6.12],[ENGINE_X,7.30],
                      [ENGINE_X,8.18],[2.65,8.02],[1.20,6.80]])
    upper=np.column_stack((side*contour[:,0],-.18-.36*(contour[:,0]-1.20),contour[:,1]))
    lower=upper-[0,.24,0]
    b.face(upper,PANEL,STRIP,[0,1,0]);b.face(lower,DARK,STRIP,[0,-1,0])
    center=np.concatenate((upper,lower)).mean(0)
    for i in range(len(upper)):
        j=(i+1)%len(upper);q=np.array([upper[i],upper[j],lower[j],lower[i]])
        b.face(q,PANEL,STRIP,q.mean(0)-center)


def weapon_seat(b,side):
    # A shallow, integral pylon at the existing wing hardpoint. No gun geometry.
    center=old.detail.mirrored_x(old.folded_to_open([4.0,old.WING_Y+.075,2.40]),side)
    # Lay out in the folded panel coordinates, then use the unchanged transform.
    points=[[3.66,1.98],[4.34,1.98],[4.42,2.76],[3.58,2.76]]
    top=np.array([old.detail.mirrored_x(old.folded_to_open([x,old.WING_Y+.075,z]),side) for x,z in points])
    bottom=top.copy();bottom[:,1]=old.WING_Y-.03
    # Recessed pylon crown stays at the hardpoint; surrounding panel is higher.
    b.face(top,WEAPON,(0,0,1,1),[0,1,0],[[0,0],[1,0],[1,1],[0,1]])
    for i in range(4):
        j=(i+1)%4;q=np.array([top[i],top[j],bottom[j],bottom[i]])
        b.face(q,DARK,STRIP,q.mean(0)-center)


def design(part,original):
    name=part.lower();b=Builder();side=-1 if '_port_' in name or 'baydoor01' in name else 1
    if name.startswith('rh_elite_'):return body(original)
    if '_tail_' in name:
        b.part='tail';previous.frame_geometry(b,include_brace_ties=False)
    elif '_engine_' in name:engine(b,side)
    elif '_upperarm_' in name:previous.arm_geometry(b,side)
    elif '_wing_' in name:
        b.part='wing'
        old.wing_geometry(b,side);weapon_seat(b,side)
    elif name.startswith('baydoor'):old.door_geometry(b,side)
    else:return original
    return b.groups()


def rig(nodes):
    old.rig(nodes)
    for path,n in mesh.walk(nodes):
        if path.lower().endswith('/cons/fix'):
            blob=bytearray(n.blob)
            for at in range(0,len(blob),176):
                name=mesh.string(blob[at+64:at+128]).lower()
                if '_glass_' in name:np.frombuffer(blob,'<f4',3,at+128)[:]+=SHIFT
            n.blob=bytes(blob)
        if path.lower().endswith('/position') and any('/'+hp+'/' in path.lower() for hp in ('hppilot','hpcockpit')):
            n.blob=(np.frombuffer(n.blob,'<f4')+SHIFT).astype('<f4').tobytes()
    # Embed the unmodified PIRATE exterior atlases/material definitions.
    # Names/CRCs stay native and source MAT is never edited.
    _,lib=mesh.read_tree(LIBRARY.read_bytes())
    keepmat={'pir_r_panel01_256','pir_r_panel01_256d','pir_r_panel02_256','pir_r-dark gray','weaponplate','engine_grill01'}
    keeptex={'pir_r_panel01_256.tga','pir_r_panel02_256.tga','weaponplate2.tga','engine_grill01.tga'}
    for source in lib[0].children:
        wanted=keepmat if source.name.lower()=='material library' else keeptex
        target=next((n for n in nodes[0].children if n.name.lower()==source.name.lower()),None)
        if target is None:target=mesh.Node(source.name);nodes[0].children.append(target)
        names={n.name.lower() for n in target.children}
        for n in source.children:
            if n.name.lower() in wanted and n.name.lower() not in names:target.children.append(copy.deepcopy(n))


def build():
    global SOURCE_SCENE,PIRATE_SCENE
    row=next(r for r in audit.inventory()[0] if r['model'].replace('\\','/').lower()=='ships/rheinland/rh_elite/rh_elite.cmp')
    SOURCE_SCENE,_,_=audit.load(row)
    PIRATE_SCENE,_,_=audit.load(base.ROW)
    old.configure();old.ENGINE_X=ENGINE_X
    native.OUT,native.DEST=OUT,DEST
    native.design,native.rig=design,rig
    native.MESH_PREFIX='rh_b6_';native.COCKPIT_TRANSLATION=SHIFT
    # Roof temporary builder must use the same dark-recess/UV rules.
    previous.Builder=Builder
    nodes=native.build();native.export(nodes)
    _,before=mesh.read_tree((previous.OUT/'rh_concept_b_lod0.cmp').read_bytes())
    tracks=lambda ns:{p:n.blob for p,n in mesh.walk(ns) if '/animation/' in p.lower() or p.lower().endswith('/cons/rev')}
    assert tracks(nodes)==tracks(before),'Shape pass changed animation'
    oldglass=[g['corners'] for g in native.evaluate_pose(before,0) if '_glass_' in g['part'].lower()]
    newglass=[g['corners'] for g in native.evaluate_pose(nodes,0) if '_glass_' in g['part'].lower()]
    for a,b in zip(oldglass,newglass):
        assert np.allclose(b[...,:3],a[...,:3]+SHIFT,atol=1e-6)
        assert np.array_equal(a[...,3:],b[...,3:])
    scene=native.evaluate_pose(nodes,0)
    mats=audit.material_table([audit.DATA/p for p in base.ROW['materials']]+[DEST])
    used=sorted({mats[g['material']]['name'] for g in scene})
    assert all('r_panel' not in name or name.startswith('pir_') for name in used)
    for source in PIRATE_SCENE:
        if '_engine_' not in source['part'].lower():continue
        output=next(g for g in scene if g['part']==source['part'] and g['material']==source['material'])
        assert np.array_equal(source['corners'][...,6:8],output['corners'][:len(source['corners']),...,6:8])
    # Front-facing floor coverage at the cabin and the shortened connector.
    tris=np.concatenate([g['corners'] for g in scene if g['part'].lower().startswith('rh_elite_')])
    lower=tris[(tris[...,4].mean(1)<-.9)&np.all(np.isclose(tris[...,1],-1.15,atol=1e-4),axis=1)]
    floor_samples=[(x,z) for x in (-.55,0,.55) for z in (-5.,-4.5,-3.7,-2.3,-1.8,-.3)]
    def inside(q,t):
        p=t[:,(0,2)];edges=np.roll(p,-1,axis=0)-p;offset=np.array(q)-p
        cross=edges[:,0]*offset[:,1]-edges[:,1]*offset[:,0]
        return np.all(cross>=-1e-5) or np.all(cross<=1e-5)
    for point in floor_samples:assert any(inside(point,t) for t in lower),('open cabin floor',point)
    checks=json.loads((OUT/'checks.json').read_text())
    prior=json.loads((previous.OUT/'checks.json').read_text())
    checks.update(revision=6,reference_model=str(SOURCE),reference_sha256=hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
                  reference_material=str(LIBRARY),reference_material_sha256=hashlib.sha256(LIBRARY.read_bytes()).hexdigest(),
                  cockpit='cabin/glass/pilot/camera move together +2.70 Z and +0.591818 Y; chin removed; floor aligned to -1.15; solid native transition adapted to body',
                  cockpit_translation=SHIFT.tolist(),engine_spacing_before=7.30,engine_spacing_after=6.30,
                  engine_radius_before=.80,engine_radius_after=.75,
                  native_transition_triangles=COUNTS['native_transition'],
                  animation='tracks and revolving constructs byte-identical to revision 05; only static glass/engine origins relocated',
                  uv='pirate atlases throughout; source engine UVs; native red strapped underside; rear source hatch on drum; separately mapped existing rims and dark reveals',
                  removed_diagonal_brace=True,removed_chin_triangles=COUNTS['removed_chin_triangles'],
                  wing_rig=prior['wing_rig'],used_materials=used,engine_uv='byte-identical float32 UV values to source pirate engines',
                  downward_floor_coverage_samples=len(floor_samples),
                  limitations=['offline shape/UV prototype; not installed','no animation/video pass','SUR, damage caps and distant LODs deferred'])
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
    print('READY SHAPE 06',checks['triangles'],DEST,flush=True)


if __name__=='__main__':build()
