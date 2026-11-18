"""RH B revision 03: coherent shells, closed cabin/bay, forward-folding wings.

All coordinates are native Freelancer (+Y up, -Z forward). Offline authoring only.
The revision-02 generator and assets remain reproducible and untouched.
"""
import argparse
import copy
import hashlib
import json
import math
import struct as S
import zipfile

import numpy as np
from scipy.spatial import Delaunay

import rh_concept_b_detail as detail
from rh_redesign_paths import CONCEPT_B_FORM, CONCEPTS

mesh, audit, base, common = detail.mesh, detail.audit, detail.base, detail.common
previous = detail.previous
PANEL, PANEL1, METAL, DARK, GRILL = detail.PANEL, detail.PANEL1, detail.METAL, detail.DARK, detail.GRILL
STRUCT, INNER_DARK, UV, RED = detail.STRUCT, detail.INNER_DARK, detail.UV, detail.RED
OUT = CONCEPT_B_FORM
DEST = OUT / 'rh_concept_b_lod0.cmp'
ROOT_PIVOT = np.array([2.28, -1.05, 2.0])
ELBOW = np.array([3.55, -1.05, 2.0])
ARM_ANGLE, PANEL_ANGLE = np.radians([68., 27.])
WINDSCREEN_EDGE=np.array([[.809715,.436188,-5.796968],[.811056,.279848,-5.796966],
                         [.839773,.070175,-6.105736],[.876515,-.172210,-6.384759],
                         [.920872,-.464838,-6.613596],[.945413,-.626842,-6.705403],
                         [1.022878,-.809210,-6.789130]])
SIDE_WINDOW_EDGE=np.array([[.897323,.437113,-4.801570],[.923359,.279848,-5.435085],
                          [.918373,.098406,-5.732065],[.935655,-.107638,-6.011085],
                          [.974632,-.346315,-6.254062],[.975416,-.636699,-6.425356],
                          [1.003935,-.793063,-6.466875]])
AUTHORING_COUNTS={}
# Defaults keep revision 03 reproducible; later offline designs can provide their
# own compartment bounds while reusing the native CMP encoder and its checks.
CARGO_MIN=np.array([-.736,-1.201,-.398])
CARGO_MAX=np.array([.736,2.301,1.448])
MESH_PREFIX='rh_b3_'
COCKPIT_TRANSLATION=np.zeros(3)


class Builder(detail.Builder):
    def face(self,points,material=PANEL,uvbox=UV,normal=None,uv=None):
        """Ear-clip polygons; a cabin boundary need not be strictly convex.

        The old first-three-vertices fan could reverse most of an eight-sided cap
        when its first corner was slightly concave. Winding is checked per triangle.
        """
        p=np.array(points,float)
        if len(p)<=3:return super().face(p,material,uvbox,normal,uv)
        newell=np.sum(np.cross(p,np.roll(p,-1,axis=0)),axis=0)
        axes=np.delete(np.arange(3),np.argmax(abs(newell)))
        q=p[:,axes]
        uv=np.array(uv,float) if uv is not None else (q-q.min(0))/np.maximum(np.ptp(q,axis=0),1e-5)
        area=np.sum(q[:,0]*np.roll(q[:,1],-1)-q[:,1]*np.roll(q[:,0],-1))
        orientation=1 if area>0 else -1
        def cross2(a,b):return a[0]*b[1]-a[1]*b[0]
        ids=list(range(len(p)));tris=[]
        while len(ids)>3:
            for k,c in enumerate(ids):
                a,z=ids[k-1],ids[(k+1)%len(ids)]
                if orientation*cross2(q[c]-q[a],q[z]-q[c])<1e-10:continue
                def inside(v):
                    return all(orientation*cross2(q[j]-q[i],q[v]-q[i])>=-1e-10 for i,j in ((a,c),(c,z),(z,a)))
                if any(inside(v) for v in ids if v not in (a,c,z)):continue
                tris.append((a,c,z));ids.pop(k);break
            else:raise ValueError(('Non-simple or degenerate polygon',p.tolist()))
        tris.append(ids)
        for tri in tris:super().face(p[list(tri)],material,uvbox,normal if normal is not None else newell,uv[list(tri)])

    def bolt(self, *args, **kwargs):
        raise AssertionError('Modeled rivets are forbidden in this design')

    def ring(self,center,outer,inner,low,high,sides=16,axis=0,material=PANEL,buried_inner=False):
        center=np.array(center,float);axes=[i for i in range(3) if i!=axis]
        angles=(np.arange(sides)+.5)*2*np.pi/sides;rings=[]
        for d,r in ((high,outer),(high,inner),(low,inner),(low,outer)):
            p=np.tile(center,(sides,1));p[:,axis]+=d
            p[:,axes[0]]+=np.cos(angles)*r;p[:,axes[1]]+=np.sin(angles)*r;rings.append(p)
        for k,(a,b) in enumerate(zip(rings,rings[1:]+rings[:1])):
            if buried_inner and k==1:continue
            for i in range(sides):
                j=(i+1)%sides;q=np.array([a[i],a[j],b[j],b[i]])
                n=q.mean(0)-center
                if k in (0,2):
                    n[:]=0;n[axis]=1 if k==0 else -1
                    tex=(q[:,axes]-center[axes])/(outer*2)+.5
                else:
                    n[axis]=0
                    if k==1:n=-n
                    tex=[[i/sides,0],[(i+1)/sides,0],[(i+1)/sides,1],[i/sides,1]]
                self.face(q,material,UV,n,tex)

    def bridge(self, rings, material=PANEL, caps=True):
        """Continuous closed shell through authored contour rings."""
        for a, b in zip(rings, rings[1:]):
            center = np.concatenate((a, b)).mean(0)
            for i in range(len(a)):
                j = (i+1) % len(a)
                q = np.array([a[i], a[j], b[j], b[i]])
                self.face(q, material, UV, q.mean(0)-center)
        if caps:
            self.face(rings[0], material, UV, [0, 0, -1])
            self.face(rings[-1], material, UV, [0, 0, 1])

    def slot_plate(self, center, radius, side):
        """Circular hub face with five actual rounded slots and recessed backing.

        Delaunay is accepted only if every authored boundary segment survives.
        No triangles bridging a slot and no bars pasted on a closed disk.
        """
        center = np.array(center, float)
        angle = np.arange(64)*np.pi/32
        outer = np.column_stack((radius*np.cos(angle), radius*np.sin(angle)))
        holes = []
        for y in (-.82, -.41, 0, .41, .82):
            r = .105
            length = math.sqrt((radius-.13)**2-y*y)-r
            a = np.linspace(0, np.pi, 9)
            left = np.column_stack((y+r*np.cos(a), -length-r*np.sin(a)))
            right = np.column_stack((y-r*np.cos(a), length+r*np.sin(a)))
            polygon=np.concatenate((left,right))
            # Split long straight slot edges so the constrained outline is also
            # Delaunay-compatible; vertices add actual hole-boundary topology.
            refined=[]
            for a,b in zip(polygon,np.roll(polygon,-1,axis=0)):
                refined.extend(np.linspace(a,b,max(1,int(np.ceil(np.linalg.norm(b-a)/.12))),endpoint=False))
            holes.append(np.array(refined))
        points = np.concatenate([outer]+holes)
        def inside(poly, q):
            a, b = poly, np.roll(poly, -1, axis=0)
            return bool(np.all((b[:,0]-a[:,0])*(q[1]-a[:,1])-(b[:,1]-a[:,1])*(q[0]-a[:,0]) >= -1e-9))
        # Each hole is convex but clockwise; normalize for the half-plane test.
        for i,p in enumerate(holes):
            area=np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1))
            if area<0: holes[i]=p[::-1]
        triangles = []
        for ids in Delaunay(points).simplices:
            q=points[ids].mean(0)
            if not any(inside(h,q) for h in holes): triangles.append(ids)
        edges={tuple(sorted((int(a),int(b)))) for ids in triangles for a,b in zip(ids,np.roll(ids,-1))}
        start=0
        for contour in [outer]+holes:
            for j in range(len(contour)):
                assert tuple(sorted((start+j,start+(j+1)%len(contour)))) in edges, (start,j,points[start+j],points[start+(j+1)%len(contour)])
            start+=len(contour)
        front, rear = side*.805, side*.62
        for ids in triangles:
            yz=points[ids]+center[1:]
            self.face(np.column_stack((np.full(3,front),yz)), PANEL, UV, [side,0,0],points[ids]/(radius*2)+.5)
        # Actual inner walls of every slot; the backing is deeper than the hole.
        for hole in holes:
            for a,b in zip(hole,np.roll(hole,-1,axis=0)):
                q=np.array([[front,*(a+center[1:])],[front,*(b+center[1:])],
                            [rear,*(b+center[1:])],[rear,*(a+center[1:])]])
                n=np.r_[0,hole.mean(0)-(a+b)/2]
                self.face(q,STRUCT,UV,n)
        self.face(np.column_stack((np.full(64,rear),outer+center[1:])),INNER_DARK,UV,[side,0,0])


def cabin_geometry(original):
    kept=[]
    removed=0
    for g in common.cockpit(original):
        # The original aft taper and red flap are replaced by one closed shell.
        triangles=[]
        for tri in g['corners']:
            # Replace the old inner/outer pillar skins instead of layering new
            # geometry over almost coincident, oppositely facing source faces.
            center=tri[:,:3].mean(0)
            zfront=np.interp(center[1],WINDSCREEN_EDGE[::-1,1],WINDSCREEN_EDGE[::-1,2])
            zback=np.interp(center[1],SIDE_WINDOW_EDGE[::-1,1],SIDE_WINDOW_EDGE[::-1,2])
            if (abs(center[0])>.72 and -.82<center[1]<.442 and
                tri[:,1].max()<.445 and zfront-.025<center[2]<zback+.025):
                removed+=1
                continue
            clipped=[]
            for a,b in zip(tri,np.roll(tri,-1,axis=0)):
                ain,bin=a[2]<=-4.8014,b[2]<=-4.8014
                if ain:clipped.append(a.copy())
                if ain!=bin:
                    point=a+(b-a)*((-4.80157-a[2])/(b[2]-a[2]))
                    point[3:6]=mesh.unit(point[3:6]);clipped.append(point)
            for i in range(1,len(clipped)-1):
                t=np.array([clipped[0],clipped[i],clipped[i+1]])
                if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))>1e-7:triangles.append(t)
        if triangles:
            out=copy.deepcopy(g);out['corners']=np.array(triangles)
            if out['material'] in (METAL,DARK):
                out['material']=PANEL1
                # Exterior cabin frames use the same armor atlas as its rear shell.
                p=out['corners'][...,:3];tex=np.stack(((p[...,2]+8.4)/3.7,(p[...,1]+2.2)/2.9),axis=-1)
                box=previous.PLAIN_UV
                out['corners'][...,6:8]=tex*(np.array(box[2:])-box[:2])+box[:2]
            kept.append(out)
    b=Builder()
    # Exact exterior boundary positions measured from the native cabin.
    front=np.array([[-1.420413,-1.741818],[-1.250375,-.793803],[-1.047923,.436188],
                    [-.818666,.580133],[.823100,.584477],[1.047965,.436188],
                    [1.250418,-.793803],[1.420474,-1.741818]])
    middle=front.copy();middle[:,0]*=.98
    rear=front.copy();rear[:,0]*=.88;rear[:,1]=-.56+(rear[:,1]+.56)*.94
    rings=[np.column_stack((p,np.full(len(p),z))) for p,z in
           ((front,-4.80157),(middle,-4.49),(rear,-4.35))]
    b.bridge(rings,caps=False)
    b.face(rings[-1],PANEL,UV,[0,0,1])
    # Exterior A-pillars join the two unchanged glass surfaces. The old cabin
    # relied on inward-facing trim here: culling exposed an open black strip.
    # These are the measured OUTER boundary loops, not the intermediate vertices
    # of the curved front glass. Joining intermediate rows would cover the pane.
    windscreen=WINDSCREEN_EDGE
    sideglass=SIDE_WINDOW_EDGE
    levels=sorted(set(windscreen[:,1].tolist()+sideglass[:,1].tolist()),reverse=True)
    curves=[]
    for curve in (windscreen,sideglass):
        points=[]
        for y in levels:
            points.append([np.interp(y,curve[::-1,1],curve[::-1,0]),y,
                           np.interp(y,curve[::-1,1],curve[::-1,2])])
        curves.append(np.array(points))
    pillar_faces=[]
    for side in (-1,1):
        a,c=[p.copy() for p in curves]
        a[:,0]=(a[:,0]+.025)*side;c[:,0]=(c[:,0]+.025)*side
        for i in range(len(levels)-1):
            start=len(b.tris[PANEL1])
            b.face([a[i],a[i+1],c[i+1],c[i]],PANEL,UV,[side,0,0],
                   [[0,i/(len(levels)-1)],[0,(i+1)/(len(levels)-1)],
                    [1,(i+1)/(len(levels)-1)],[1,i/(len(levels)-1)]])
            pillar_faces.extend(b.tris[PANEL1][start:])
            # Physical thickness along both pane borders; no floating coplanar decal.
            for edge,nz in ((a,-1),(c,1)):
                b.face([edge[i],edge[i+1],edge[i+1]-[side*.025,0,0],edge[i]-[side*.025,0,0]],
                       PANEL,UV,[0,0,nz])
        seal=np.array([[.922323,.437113,-4.80157],[.834715,.436188,-5.796968],
                       [.6434,.57933,-5.796968],[.823100,.584477,-4.80157]])
        seal[:,0]*=side
        b.face(seal,PANEL,UV,[side,1,0])
        # Close the underside of the original roof overhang too. A single
        # upward-facing bridging face remains invisible from below with culling.
        lip=np.array([[.809715,-5.796968],[.924344,-5.438322],
                      [1.047965,-4.801568],[.897323,-4.801570]])
        lip[:,0]*=side
        b.prism(lip,.400,.442,axis=1,bevel=.015,material=PANEL,rim=PANEL)
    # Smooth only the broad curved pillar skin, preserving hard edges at its
    # thickness, roof, hull armor and all native glass normals.
    normals={}
    for tri in pillar_faces:
        n=np.cross(tri[1,:3]-tri[0,:3],tri[2,:3]-tri[0,:3])
        for v in tri:normals.setdefault(tuple(v[:3].round(5)),[]).append(n)
    for tri in pillar_faces:
        for v in tri:v[3:6]=mesh.unit(np.sum(normals[tuple(v[:3].round(5))],axis=0))
    assert removed>0
    AUTHORING_COUNTS['replaced_legacy_pillar_triangles']=removed
    return kept+b.groups()


def cargo_geometry(b):
    # Interior surfaces face into the compartment, independent of door visibility.
    x,z0,z1,floor=.735,-.397,1.447,-1.20
    b.allow_bay_metal=True
    b.face([[-x,floor,z0],[x,floor,z0],[x,floor,z1],[-x,floor,z1]],METAL,UV,[0,1,0])
    for side in (-1,1):
        b.face([[side*x,floor,z0],[side*x,floor,z1],[side*x,2.30,z1],[side*x,1.45,z0]],
               METAL,UV,[-side,0,0])
    b.face([[-x,floor,z0],[x,floor,z0],[x,1.45,z0],[-x,1.45,z0]],METAL,UV,[0,0,1])
    b.face([[-x,floor,z1],[x,floor,z1],[x,2.30,z1],[-x,2.30,z1]],METAL,UV,[0,0,-1])
    b.allow_bay_metal=False
    # Two integral longitudinal floor ridges, broad rather than tiny fasteners.
    for side in (-1,1):
        b.prism([[side*.44,z0+.10],[side*.57,z0+.10],[side*.57,z1-.10],[side*.44,z1-.10]],
                floor,floor+.065,axis=1,material=STRUCT,rim=STRUCT)
    for side in (-1,1):
        b.face([[side*x,1.45,z0],[side*.74,1.50,-.40],[side*.74,2.35,1.45],[side*x,2.30,z1]],
               PANEL,UV,[-side,0,0])


def body_geometry(b,original):
    # One torso shell: the cheeks, lower sill and front slope share its envelope.
    b.loft([(-1.95,1.04,-1.55,.70),(-.40,1.43,-1.65,1.50),
            (1.45,1.55,-1.65,2.35),(3.5,1.15,-1.55,2.35)],omit_top=True)
    b.face([[-.728,.70,-1.95],[.728,.70,-1.95],[1.001,1.50,-.40],[-1.001,1.50,-.40]],PANEL,UV,[0,1,0])
    b.face([[-1.085,2.35,1.45],[1.085,2.35,1.45],[.805,2.35,3.50],[-.805,2.35,3.50]],PANEL,RED,[0,1,0])
    for side in (-1,1):
        b.face([[side*.74,1.50,-.40],[side*1.001,1.50,-.40],[side*1.085,2.35,1.45],
                [side*.74,2.35,1.45]],PANEL,UV,[0,1,0])
        # Integrated side casing with a real inset vent, connected to lower armor.
        outer=np.array([[-1.43,-1.33],[-1.43,1.50],[1.05,1.85],[1.38,.12],[.57,-1.12]])
        inner=np.array([[-.12,-.04],[-.12,1.44],[.94,1.44],[.94,-.04]])
        # A convex casing is covered by five broad contour panels around the inset.
        # Triangulated planar annulus avoids an overlapping solid face behind the vent.
        pts=np.concatenate((outer,inner))
        tris=Delaunay(pts).simplices
        for ids in tris:
            q=pts[ids].mean(0)
            if -.12<q[0]<.94 and -.04<q[1]<1.44:continue
            b.face(np.column_stack((np.full(3,side*1.59),pts[ids])),PANEL,UV,[side,0,0])
        center=outer.mean(0)
        for a,c in zip(outer,np.roll(outer,-1,axis=0)):
            q=np.array([[side*1.59,*a],[side*1.59,*c],[side*1.34,*c],[side*1.34,*a]])
            b.face(q,PANEL,UV,np.r_[0,(a+c)/2-center])
        for a,c in zip(inner,np.roll(inner,-1,axis=0)):
            q=np.array([[side*1.59,*a],[side*1.59,*c],[side*1.48,*c],[side*1.48,*a]])
            b.face(q,STRUCT,UV,np.r_[0,inner.mean(0)-(a+c)/2])
        b.face(np.column_stack((np.full(4,side*1.47),inner)),INNER_DARK,UV,[side,0,0])
        for y in (.08,.31,.54,.77):b.louver(side*1.49,y,.70,.66,side,.12)
        b.face([[side*1.592,-1.28,-.70],[side*1.592,-.36,-.70],
                [side*1.592,-.36,.08],[side*1.592,-1.28,.08]],PANEL,RED,[side,0,0])
        # A full tapered load-bearing shoulder joins the crown and horizontal hinge.
        b.prism([[-1.20,1.25],[-1.19,2.16],[2.66,3.17],[2.91,2.65]],
                *sorted((side*1.58,side*1.91)),material=PANEL,rim=PANEL)
        b.radial([0,2.62,2.78],sorted([(side*1.91,.29),(side*2.02,.25)]),32,cap=STRUCT)
        # Neck rails meet the newly closed cabin rear, and continue into the torso.
        for y in (-1.28,.18):
            b.bar([side*.79,y,-4.37],[side*.87,y+.14,-1.82],.25,.24)
        b.bar([side*.80,-1.16,-4.25],[side*.86,.21,-1.95],.16,.16,STRUCT)
        b.bar([side*.80,.10,-4.25],[side*.86,-1.12,-1.95],.16,.16,STRUCT)
        for z,y in ((-4.23,-.56),(-1.94,-.46)):
            b.radial([0,y,z],sorted([(side*.89,.22),(side*1.0,.20)]),24,cap=STRUCT)
        # Integral pad supports the vertical folding bearing, above the engine.
        b.prism([[side*1.62,1.62],[side*2.48,1.62],[side*2.59,2.25],[side*1.62,2.43]],
                -1.38,-1.22,axis=1,material=PANEL,rim=PANEL)
    cargo_geometry(b)
    return cabin_geometry(original)+b.groups()


def frame_geometry(b):
    center=np.array([1.80,4.65])
    outer=np.array([[5.15,3.10],[5.15,6.15],[3.80,7.65],[-.15,7.65],
                    [-1.60,6.10],[-1.60,3.10],[-.10,1.60],[3.80,1.60]])
    inner=center+(outer-center)*.715
    # Continuous closed octagonal ring. Bevels meet exactly at the sector boundaries.
    rings=[(.80,center+(outer-center)*.975),(.80,center+(inner-center)*1.035),
           (.66,inner),(-.66,inner),(-.80,center+(inner-center)*1.035),
           (-.80,center+(outer-center)*.975),(-.66,outer),(.66,outer)]
    for k,((x,a),(xx,c)) in enumerate(zip(rings,rings[1:]+rings[:1])):
        for i in range(8):
            j=(i+1)%8
            q=np.array([[x,*a[i]],[x,*a[j]],[xx,*c[j]],[xx,*c[i]]])
            if k==0:n=[1,0,0]
            elif k==4:n=[-1,0,0]
            else:
                n=np.r_[0,q.mean(0)[1:]-center]
                if k in (1,2,3):n=-n
            b.face(q,PANEL,RED if i in (1,5) and k in (0,4) else UV,n)
    c=np.r_[0,center]
    for angle in (0,np.pi/2,np.pi,3*np.pi/2):
        vec=np.array([0,np.cos(angle),np.sin(angle)])
        b.bar(c+vec*1.28,c+vec*2.73,.45,.56,PANEL)
    # Central annulus leaves actual room for the perforated covers and recessed ends.
    b.ring(c,1.55,1.25,-.72,.72,sides=64,material=PANEL)
    for side in (-1,1):
        b.ring(c,1.48,1.255,*sorted((side*.72,side*.805)),sides=64,material=PANEL)
        b.slot_plate(c,1.255,side)
    # Functional frame latches, no rows of decorative bolts.
    for z in (1.66,7.60):
        b.prism([[1.37,z-.31],[2.03,z-.31],[2.12,z+.25],[1.30,z+.25]],-.90,.90)
        for side in (-1,1):b.radial([0,1.72,z],sorted([(side*.91,.22),(side*1.01,.18)]),24,cap=STRUCT)
    for z in np.linspace(3.65,5.45,4):b.beam([-.65,5.15,z],[.65,5.15,z],.12,.12,STRUCT)


def arm_geometry(b,side):
    root,elbow=detail.mirrored_x(ROOT_PIVOT,side),detail.mirrored_x(ELBOW,side)
    # Vertical bearings make the actual horizontal folding plane legible.
    for c,r in ((root,.37),(elbow,.31)):
        b.radial(c,[(-.22,r*.90),(-.15,r),(.15,r),(.22,r*.90)],32,axis=1,cap=STRUCT)
    p=np.array([[2.28,1.70],[3.55,1.75],[3.63,2.20],[2.28,2.32]])
    p[:,0]*=side
    b.prism(p,-1.22,-.88,axis=1,material=PANEL,rim=PANEL)


def wing_geometry(b,side):
    p=np.array([[3.55,1.27],[5.93,1.34],[6.22,1.57],[6.18,2.72],[5.95,2.94],[3.55,2.82]])
    p[:,0]*=side
    b.prism(p,-1.24,-.87,axis=1,bevel=.035,material=PANEL,rim=PANEL)
    # Broad inlaid skin with a flush weapon mounting panel (gun remains separate).
    p=np.array([[3.75,1.45],[5.80,1.51],[5.86,2.69],[3.75,2.65]])
    p[:,0]*=side
    b.prism(p,-.871,-.825,axis=1,bevel=.025,material=PANEL,rim=PANEL)
    b.face([[side*4.52,-.823,1.64],[side*5.28,-.823,1.64],
            [side*5.28,-.823,2.37],[side*4.52,-.823,2.37]],PANEL,common.SERVICE_UV,[0,1,0])
    b.ring([side*4.90,-.821,2.0],.22,.13,0,.025,24,axis=1,material=STRUCT)


def design(part,original):
    name=part.lower();b=Builder()
    side=-1 if '_port_' in name or 'baydoor01' in name else 1
    if name.startswith('rh_elite_'):return body_geometry(b,original)
    if '_tail_' in name:frame_geometry(b)
    elif '_engine_' in name:detail.engine_geometry(b,side)
    elif '_upperarm_' in name:arm_geometry(b,side)
    elif '_wing_' in name:wing_geometry(b,side)
    elif name.startswith('baydoor'):detail.door_geometry(b,side)
    else:return original
    return b.groups()


def animated_angles(fold):
    def smooth(t):
        t=float(np.clip(t,0,1));return t*t*(3-2*t)
    return ARM_ANGLE*smooth((fold-.04)/.96),PANEL_ANGLE*smooth(fold/.82)


def rig(nodes):
    original=copy.deepcopy(mesh.child(mesh.child(nodes[0],'Animation'),'Script'))
    # Reuse proven native component/hardpoint assembly, then author new axes/keys.
    detail.ROOT_PIVOT,detail.ELBOW=ROOT_PIVOT,ELBOW
    detail.ARM_ANGLE,detail.PANEL_ANGLE=ARM_ANGLE,PANEL_ANGLE
    detail.relocate_and_rig(nodes)
    cons=mesh.child(mesh.child(nodes[0],'Cmpnd'),'Cons')
    rev=mesh.child(cons,'Rev');blob=bytearray(rev.blob)
    for at in range(0,len(blob),208):
        name=mesh.string(blob[at+64:at+128]).lower()
        if '_wing_' in name or '_upperarm' in name:
            f=np.frombuffer(blob,'<f4',20,at+128)
            side=-1 if '_port_' in name else 1
            f[15:18]=[0,side,0]
    rev.blob=bytes(blob)
    scripts=mesh.child(mesh.child(nodes[0],'Animation'),'Script')
    scripts.children=[]
    for script in original.children:
        if script.name.lower()=='sc_rotate dish':continue  # Source orphan 'dish2', absent from this design.
        result=copy.deepcopy(script);result.children=[]
        for joint in script.children:
            child=mesh.string(mesh.child(joint,'Child name').blob)
            ch=mesh.child(joint,'Channel');count,interval,kind=S.unpack('<IfI',mesh.child(ch,'Header').blob)
            raw=np.frombuffer(mesh.child(ch,'Frames').blob,'<f4')
            assert kind==1
            if interval<0:ts,vs=raw.reshape(count,2).T
            else:ts,vs=np.arange(count)*interval,raw[:count]
            wing='_wing_' in child.lower()
            if not wing:
                item=copy.deepcopy(joint)
                # Convert the native uniform door stop keys to explicit times;
                # preserve their declared values and playback duration.
                dest=mesh.child(item,'Channel')
                mesh.child(dest,'Header').blob=S.pack('<IfI',count,-1,1)
                mesh.child(dest,'Frames').blob=np.column_stack((ts,vs)).astype('<f4').tobytes()
                result.children.append(item);continue
            side='port' if '_port_' in child.lower() else 'starboard'
            parent=f'Rh_{side}_upperarm'
            times=sorted(set(float(v) for a,b in zip(ts,ts[1:]) for v in np.linspace(a,b,33))) if len(ts)>1 and ts[-1]<=10 else ts.tolist()
            values=[animated_angles(1-float(np.interp(t,ts,vs))/1.17808997631073) for t in times]
            for name,par,index in ((child,parent,1),(parent,'Root',0)):
                item=copy.deepcopy(joint);item.name=f'Joint map {len(result.children)}'
                mesh.child(item,'Child name').blob=name.encode()+b'\0'
                mesh.child(item,'Parent name').blob=par.encode()+b'\0'
                dest=mesh.child(item,'Channel')
                mesh.child(dest,'Header').blob=S.pack('<IfI',len(times),-1,1)
                mesh.child(dest,'Frames').blob=np.array([[t,v[index]] for t,v in zip(times,values)],'<f4').tobytes()
                result.children.append(item)
        for index,joint in enumerate(result.children):joint.name=f'Joint map {index}'
        scripts.children.append(result)
    # Weapon seats are tied to the panel and move with it throughout the cycle.
    transforms,_=audit.transforms(nodes)
    for p,n in mesh.walk(nodes):
        if '/hardpoints/' not in p.lower() or not p.lower().endswith('/position'):continue
        part=p.split('/')[2].lower();hp=p.split('/')[-2].lower()
        if '_wing_' in part and hp.startswith('hpweapon'):
            side=-1 if '_port_' in part else 1;r,t=transforms[part]
            n.blob=np.array(r.T@(np.array([side*4.9,-.785,2.0])-t),'<f4').tobytes()


def evaluate_pose(nodes,phase=0,door=0):
    posed=copy.deepcopy(nodes)
    flat={p.lower():n.blob for p,n in mesh.walk(nodes)};values={}
    for p,b in flat.items():
        if not p.endswith('/channel/header'):continue
        f=phase if '/sc_extend wing/' in p else door if '/sc_open baydoor/' in p else None
        if f is None:continue
        count,interval,kind=S.unpack('<IfI',b)
        assert interval==-1 and kind==1
        frames=np.frombuffer(flat[p.rsplit('/',1)[0]+'/frames'],'<f4').reshape(count,2)
        child=mesh.string(flat[p.rsplit('/channel/',1)[0]+'/child name']).lower()
        values[child]=float(np.interp(f*frames[-1,0],frames[:,0],frames[:,1]))
    for p,n in mesh.walk(posed):
        if not p.lower().endswith('/cons/rev'):continue
        blob=bytearray(n.blob)
        for at in range(0,len(blob),208):
            name=mesh.string(blob[at+64:at+128]).lower();f=np.frombuffer(blob,'<f4',20,at+128)
            angle=values.get(name,0);axis=mesh.unit(f[15:18].astype(float));x,y,z=axis
            cross=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
            rotation=np.eye(3)*np.cos(angle)+(1-np.cos(angle))*np.outer(axis,axis)+np.sin(angle)*cross
            f[6:15]=(rotation@f[6:15].reshape(3,3)).ravel()
        n.blob=bytes(blob)
    transforms,_=audit.transforms(posed)
    libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    scene=[]
    for p,n in mesh.walk(nodes):
        if not p.lower().endswith('/vmeshref'):continue
        part=p.split('/')[2];r,t=transforms[part.lower()]
        for g in base.world(audit.extract(n.blob,libs),r,t):g['part']=part;scene.append(g)
    return scene


def build():
    OUT.mkdir(parents=True,exist_ok=True)
    src=base.SOURCE.read_bytes();header,nodes=mesh.read_tree(src)
    before={p:n.blob for p,n in mesh.walk(nodes)}
    tr0,_=audit.transforms(nodes)
    libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    rig(nodes)
    for part in nodes[0].children:
        ml=next((n for n in part.children if n.name.lower()=='multilevel'),None) if part.blob is None else None
        if ml:
            ml.children=[n for n in ml.children if not n.name.lower().startswith('level') or n.name.lower()=='level0']
            mesh.child(ml,'Switch2').blob=S.pack('<2f',0,1000000)
    tr,_=audit.transforms(nodes);library=mesh.child(nodes[0],'VMeshLibrary')
    report=[];wires={}
    for p,n in list(mesh.walk(nodes)):
        if not p.lower().endswith('/vmeshref'):continue
        part=p.split('/')[2]
        if '_upperarm_' in part.lower():old=[]
        else:
            r,t=tr0[part.lower()];old=base.world(audit.extract(n.blob,libs),r,t)
        new=previous.merge(design(part,old))
        report.append(dict(part=part,triangles=sum(len(g['corners']) for g in new),groups=len(new)))
        if '_glass_' in part.lower():continue
        r,t=tr[part.lower()];blob,vertices=mesh.pack(base.world(new,r.T,-r.T@t))
        name=MESH_PREFIX+hashlib.sha256((p+hashlib.sha256(blob).hexdigest()).encode()).hexdigest()[:16]+'.vms'
        entry=mesh.Node(name);entry.children=[mesh.Node('VMeshData',blob)];library.children.append(entry)
        n.blob=mesh.make_ref(n.blob,name,blob,vertices);wires[part]=(blob,mesh.crc(name))
    for p,n in mesh.walk(nodes):
        part=p.split('/')[2] if len(p.split('/'))>2 else ''
        if p.lower().endswith('/vwiredata') and part in wires:n.blob=previous.feature_wire(*wires[part])
    used={S.unpack_from('<I',n.blob,4)[0] for p,n in mesh.walk(nodes) if p.lower().endswith(('/vmeshref','/vwiredata'))}
    library.children=[n for n in library.children if mesh.crc(n.name) in used]
    output=mesh.write_tree(header,nodes);_,decoded=mesh.read_tree(output)
    flat={p:n.blob for p,n in mesh.walk(decoded)}
    dl={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(decoded) if p.lower().endswith('/vmeshdata')}
    mats=audit.material_table([audit.DATA/p for p in base.ROW['materials']]+[base.SOURCE])
    maxv=maxi=maxdraw=0
    for vertices,groups,indices in dl.values():
        assert len(vertices)<=65535 and len(indices)<=65535 and len(groups)<=65535
        maxv=max(maxv,len(vertices));maxi=max(maxi,len(indices));at=0
        for _,start,end,count,_ in groups:
            assert count%3==0 and 0<=start<=end<len(vertices)
            ids=indices[at:at+count]+start
            assert len(ids)==count and ids.min()>=start and ids.max()<=end
            maxdraw=max(maxdraw,count//3);at+=count
        assert at==len(indices)
    for p,b in flat.items():
        if '/hpcockpit/' in p.lower() or '/hppilot/' in p.lower():
            if p.lower().endswith('/position'):
                assert np.allclose(np.frombuffer(b,'<f4'),np.frombuffer(before[p],'<f4')+COCKPIT_TRANSLATION,atol=1e-6),p
            else:assert b==before[p],p
        if '/rh_glass_' in p.lower() and '/switch2' not in p.lower():assert b==before[p],p
        if not p.lower().endswith('/vmeshref'):continue
        for g in audit.extract(b,dl):
            assert np.isfinite(g['corners']).all()
            assert np.allclose(np.linalg.norm(g['corners'][...,3:6],axis=-1),1,atol=1e-5)
            mat=mats[g['material']]
            if 'metal' not in mat['texture'].lower() and not mat['name'].lower().startswith('metal'):continue
            if '/baydoor' in p.lower():continue
            assert '/rh_elite_' in p.lower(),p
            pts=g['corners'][...,:3]
            assert np.all(pts>=CARGO_MIN) and np.all(pts<=CARGO_MAX),p
    assert base.SOURCE.read_bytes()==src
    DEST.write_bytes(output)
    stats=dict(source=str(base.SOURCE),source_sha256=hashlib.sha256(src).hexdigest(),output_sha256=hashlib.sha256(output).hexdigest(),
               concept=str(CONCEPTS/'rh_concept_B.png'),triangles=sum(p['triangles'] for p in report),parts=report,lods=[0],
               directx_format_checks=dict(index_format='D3DFMT_INDEX16',limit=65535,max_vertices_per_vmesh=maxv,max_indices_per_vmesh=maxi,max_triangles_per_draw=maxdraw),
               wing_rig='68 degree root + 27 degree elbow, local +/-Y; t=0 open, t=end forward/inward fold',
               cockpit='original glass/pilot/camera retained; original front retained; red aft flap removed and rear shell rebuilt',
               metal_texture_policy='only door undersides and spatially checked cargo interior',modeled_rivets=0,
               authoring_counts=AUTHORING_COUNTS,
               limitations=['offline prototype, not installed','SUR, damage caps and distant LODs deferred','existing exterior texture atlas; final UV art pass deferred'])
    (OUT/'checks.json').write_text(json.dumps(stats,indent=2),encoding='utf8')
    print(json.dumps(stats,indent=2),flush=True)
    return decoded


def export(nodes):
    mats=audit.material_table([audit.DATA/p for p in base.ROW['materials']]+[base.SOURCE])
    opened,folded=evaluate_pose(nodes,0),evaluate_pose(nodes,1)
    base.export_obj(OUT/'rh_concept_b_open.obj',opened,mats)
    base.export_obj(OUT/'rh_concept_b_folded.obj',folded,mats)
    names={mesh.string(mesh.child(n,'File name').blob):mesh.string(mesh.child(n,'Object name').blob)
           for n in mesh.child(nodes[0],'Cmpnd').children if n.name!='Cons'}
    joints={'Root':dict(parent=None,origin=[0,0,0],rotation=np.eye(3).tolist(),axis=[0,1,0])}
    for p,n in mesh.walk(nodes):
        if '/cmpnd/cons/' not in p.lower():continue
        rev=p.lower().endswith('/rev');size=208 if rev else 176
        for at in range(0,len(n.blob),size):
            parent=mesh.string(n.blob[at:at+64]);name=mesh.string(n.blob[at+64:at+128])
            f=np.frombuffer(n.blob,'<f4',(size-128)//4,at+128).astype(float)
            assert not rev or np.all(f[3:6]==0),'Blender export requires zero joint offset'
            joints[name]=dict(parent=parent,origin=f[:3].tolist(),rotation=f[6:15].reshape(3,3).tolist() if rev else f[3:12].reshape(3,3).tolist(),axis=f[15:18].tolist() if rev else [0,1,0])
    libs={mesh.crc(p.split('/')[-2]):audit.decode(n.blob) for p,n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    objects=[]
    for p,n in mesh.walk(nodes):
        if not p.lower().endswith('/vmeshref'):continue
        part=p.split('/')[2]
        objects.append(dict(name=names[part],file=part,joint=joints[names[part]],groups=[dict(material=g['material'],corners=g['corners'].tolist()) for g in audit.extract(n.blob,libs)]))
    animation=[];doors=[];flat={p.lower():n.blob for p,n in mesh.walk(nodes)}
    for p,b in flat.items():
        if not p.endswith('/channel/frames'):continue
        target=animation if '/sc_extend wing/' in p else doors if '/sc_open baydoor/' in p else None
        if target is None:continue
        name=mesh.string(flat[p.rsplit('/channel/',1)[0]+'/child name'])
        target.append(dict(object=name,keys=np.frombuffer(b,'<f4').reshape(-1,2).tolist()))
    data=dict(objects=objects,animation=animation,doors=doors,open_phase=0,folded_phase=1,
              materials={str(k):dict(name=v['name'],texture=v['texture'].rsplit('.',1)[0]+'.png' if v['image'] else None,colour=v['colour'].tolist()) for k,v in mats.items() if k in {g['material'] for g in opened}},concept=str(CONCEPTS/'rh_concept_B.png'))
    (OUT/'blender_scene.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf8')
    print('Exported',OUT,flush=True)


def package():
    with zipfile.ZipFile(OUT/'rh_concept_b_revision_03.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for p in OUT.iterdir():
            if p.is_file() and p.suffix not in ('.zip','.blend1','.log'):archive.write(p,p.name)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--package-only',action='store_true');args=parser.parse_args()
    if args.package_only:package()
    else:export(build())
