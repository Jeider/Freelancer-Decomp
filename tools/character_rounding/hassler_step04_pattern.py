"""Open uniform pattern. Native-inspired back darts, no exterior red applique."""
import math
import numpy as np
from mathutils import Vector
from mathutils.kdtree import KDTree
from hassler_garment_mesh import partition, convex_parts

def pattern(radius=.18,height=.4):
    limit=math.pi*radius
    holes=[[np.array([sign*math.pi/2*radius+.080*math.cos(a),.272+.060*math.sin(a)])
            for a in np.linspace(0,2*math.pi,65)[:-1]] for sign in (-1,1)]
    regions=[]
    for sign in (-1,1):
        regions.append((2,[(sign*s,h) for s,h in [(.125,.34),(.395,.337),(.395,.4),(.125,.4)]]))
    regions.append((1,[(-.125,0),(.110,0),(.155,.248),(.195,.34),(.125,.4),(-.135,.4),(-.17,.344),(-.175,.28)]))
    for sign in (-1,1):
        regions.extend([(1,[(sign*s,h) for s,h in [(limit,.245),(.325,.355),(.325,.395),(limit,.29)]]),
                        (1,[(sign*s,h) for s,h in [(limit-.024,0),(limit,0),(limit,.285),(limit-.024,.285)]]),
                        (6,[(sign*s,h) for s,h in [(.285,0),(.365,0),(.368,.04),(.375,.08),(.386,.12),(.398,.16),(.410,.20),(.411,.23),(.402,.26),(.384,.29),(.360,.32),(.340,.35),(.285,.37)]])])
    prepared=[(mat,tri) for mat,poly in regions for tri in convex_parts(poly)]
    s_values=sorted(set(np.linspace(-limit,limit,73).round(10).tolist()+[a*radius for a in (.14,.30,.55,.82,.85,1.08,-.24,-.45,-.75,-1.1)]))
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
    return points,faces,{'holes':[np.array(h).tolist() for h in holes],'regions':regions,
                         'radius':radius,'height':height,'manual_pattern':True,
                         'red_face_only_on_turned_uniform_flap':True}
