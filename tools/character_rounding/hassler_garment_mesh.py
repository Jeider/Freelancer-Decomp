"""Small planar pattern partitioner: conforming garment panels, no image guesses."""
import math
import numpy as np
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from mathutils.kdtree import KDTree

EPS=1e-9
def area(poly):return sum(np.cross(a,b) for a,b in zip(poly,poly[1:]+poly[:1]))*.5
def clean(poly):
    out=[]
    for p in poly:
        if not out or np.linalg.norm(p-out[-1])>EPS:out.append(np.array(p,dtype=float))
    if len(out)>1 and np.linalg.norm(out[0]-out[-1])<EPS:out.pop()
    return out if len(out)>=3 and abs(area(out))>1e-12 else []
def side(poly,a,b):
    inside=[];outside=[]
    if not poly:return [],[]
    for p,q in zip(poly,poly[1:]+poly[:1]):
        dp=np.cross(b-a,p-a);dq=np.cross(b-a,q-a)
        (inside if dp>=-EPS else outside).append(p)
        if (dp>EPS and dq<-EPS) or (dp<-EPS and dq>EPS):
            r=p+(q-p)*dp/(dp-dq);inside.append(r);outside.append(r)
        elif abs(dp)<=EPS and dq<-EPS:outside.append(p)
        elif dp<-EPS and abs(dq)<=EPS:outside.append(q)
    return clean(inside),clean(outside)
def partition(poly,convex):
    if not poly:return [],[]
    pp=np.array(poly);cc=np.array(convex)
    if np.any(pp.max(0)<cc.min(0)-EPS) or np.any(cc.max(0)<pp.min(0)-EPS):return [],[poly]
    current=poly;outside=[]
    for a,b in zip(convex,convex[1:]+convex[:1]):
        current,part=side(current,a,b)
        if part:outside.append(part)
        if not current:break
    return current,outside
def convex_parts(poly):
    poly=[np.array(p,float) for p in poly]
    if area(poly)<0:poly.reverse()
    if all(np.cross(poly[(i+1)%len(poly)]-p,poly[(i+2)%len(poly)]-poly[(i+1)%len(poly)])>=-EPS for i,p in enumerate(poly)):return [poly]
    ts=tessellate_polygon([[Vector((*p,0)) for p in poly]])
    return [[poly[i] if isinstance(i,int) else np.array(i[:2]) for i in t] for t in ts]

def pattern(radius=.18,height=.4):
    limit=math.pi*radius
    holes=[]
    for sign in (-1,1):
        holes.append([np.array([sign*math.pi/2*radius+.080*math.cos(a),.272+.060*math.sin(a)]) for a in np.linspace(0,2*math.pi,65)[:-1]])
    # Explicit garment cut lines interpreted from the front/back user artwork.
    regions=[(3,[(.005,.293),(.143,.286),(.211,.332),(.139,.374),(.044,.363)])]
    for sign in (-1,1):
        regions.append((2,[(sign*s,h) for s,h in [(.125,.34),(.395,.337),(.395,.4),(.125,.4)]]))
    regions.append((1,[(-.125,0),(.110,0),(.142,.248),(.045,.295),(.10,.36),(-.135,.4),(-.17,.344),(-.175,.28)]))
    for sign in (-1,1):
        regions.extend([(1,[(sign*s,h) for s,h in [(limit,.245),(.325,.355),(.325,.395),(limit,.29)]]),
                        (1,[(sign*s,h) for s,h in [(limit-.036,0),(limit,0),(limit,.285),(limit-.036,.285)]])])
    prepared=[(mat,tri) for mat,poly in regions for tri in convex_parts(poly)]
    s_values=sorted(set(np.linspace(-limit,limit,73).round(10).tolist()+[.50*radius,-.22*radius]))
    h_values=sorted(set(np.linspace(0,height,19).round(10).tolist()+[.012,.035,.08,.30,.32,.34,.37,.39]))
    polygons=[]
    for sa,sb in zip(s_values,s_values[1:]):
        for ha,hb in zip(h_values,h_values[1:]):
            remaining=[[np.array(p) for p in ((sa,ha),(sb,ha),(sb,hb),(sa,hb))]]
            for hole in holes:
                remaining=[piece for poly in remaining for piece in partition(poly,hole)[1]]
            for material,region in prepared:
                next_remaining=[]
                for poly in remaining:
                    inside,outside=partition(poly,region)
                    if inside:polygons.append((material,inside))
                    next_remaining.extend(outside)
                remaining=next_remaining
            polygons.extend((0,p) for p in remaining)
    # Insert every shared-edge junction before triangulation, so the material
    # partition cannot leave T junctions or unstitched colour islands.
    points=[];lookup={};faces=[]
    def vertex(p):
        key=tuple(np.round(p,9))
        if key not in lookup:lookup[key]=len(points);points.append(np.array(key))
        return lookup[key]
    raw=[(mat,[vertex(p) for p in poly]) for mat,poly in polygons]
    kd=KDTree(len(points))
    for i,p in enumerate(points):kd.insert(Vector((*p,0)),i)
    kd.balance()
    for mat,poly in raw:
        ring=[]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            pa,pb=points[a],points[b];delta=pb-pa;length=np.linalg.norm(delta)
            if length<1e-9:continue
            candidates=[]
            for co,i,dist in kd.find_range(Vector((*(.5*(pa+pb)),0)),length*.501+1e-8):
                t=np.dot(points[i]-pa,delta)/length**2
                if -1e-7<=t<1-1e-7 and abs(np.cross(delta,points[i]-pa))<length*2e-8:candidates.append((t,i))
            ring.extend(i for _,i in sorted(candidates))
        ring=list(dict.fromkeys(ring))
        if len(ring)<3:continue
        if len(ring)==3:faces.append((mat,ring[::-1]))
        elif len(ring)==4 and all(abs(np.cross(points[ring[(i+1)%4]]-points[j],points[ring[(i+2)%4]]-points[ring[(i+1)%4]]))>1e-11 for i,j in enumerate(ring)):
            faces.append((mat,ring[::-1]))
        else:
            center=vertex(np.mean([points[i] for i in ring],axis=0))
            faces.extend((mat,[center,b,a]) for a,b in zip(ring,ring[1:]+ring[:1]))
    return points,faces,{'holes':[np.array(h).tolist() for h in holes], 'regions':[(m,p) for m,p in regions],
                         'radius':radius,'height':height,'manual_pattern':True}
