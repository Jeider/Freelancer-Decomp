"""B04 ELITE: offline first shape prototype, from the selected concept and native rig.

No DATA writes, installers, SUR or destruction generation. The original canopy,
its shell and UVs are copied by pinned triangle identities, never reconstructed.
"""
import copy
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import struct

import numpy as np

import bw_family_audit as reference
import rh_concept_b_final as f
from rh_freighter_q13 import B as PolygonBuilder, planar_mesh
from rh_fighter_f14_detail import fix_tjunctions

ROOT = Path(__file__).resolve().parents[2]
TOPIC = ROOT / 'out/ship_design/bw_family'
OUT = TOPIC / 'elite/prototypes/b04_01'
SOURCE = Path('D:/Games/FL_MOD/DATA/ships/border_world/bw_pir_elite/bw_pir_elite.cmp')
MAT = SOURCE.parent.parent / 'bw_pir_ships.mat'
ENV = Path('D:/Games/FL_MOD/DATA/fx/envmapbasic.mat')
P = f.mesh.crc('pir_bw_panel_256')
D = f.mesh.crc('pir_bw_panel_256D')
E = f.mesh.crc('pir_bw_engine')
G = f.mesh.crc('engine_grill01')
UV = (.12, .12, .88, .88)  # Provisional native references, not an accepted UV pass.
OBJECTS = []


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2,
        default=lambda v: v.tolist() if isinstance(v, np.ndarray) else float(v))+'\n', encoding='utf8')


class B(PolygonBuilder):
    def face(self, points, material=P, uvbox=UV, normal=None, uv=None):
        return super().face(points, material, uvbox, normal, uv)


def add(name, b, owner='Root', category='Authored hull'):
    groups = b.groups() if isinstance(b, B) else b
    if category not in ('Immutable original cabin','Native rig helpers'):
        # Preserve source cabin bits. Only our new panels receive geometric
        # seam repair after constrained triangulation introduces boundary splits.
        groups,_=fix_tjunctions(groups)
    OBJECTS.append(dict(name=name, owner=owner, category=category, groups=groups))


def ribbon(b, a, c, material=P, inward=False, face_normal=None):
    a, c = np.asarray(a), np.asarray(c)
    # Topological orientation works for concave stepped outlines too. A vector
    # from the polygon centroid reverses walls inside a concavity.
    axis=np.sum(np.cross(a,np.roll(a,-1,axis=0)),axis=0)
    travel=c.mean(0)-a.mean(0)
    reverse=(np.dot(axis,travel)<0) != inward
    arc = np.r_[0, np.cumsum(np.linalg.norm(np.roll(a, -1, axis=0)-a, axis=1))]
    for i in range(len(a)):
        j = (i+1) % len(a)
        q = np.array([a[i], a[j], c[j], c[i]])
        uv=np.array([[arc[i]/arc[-1],0],[arc[i+1]/arc[-1],0],
                     [arc[i+1]/arc[-1],1],[arc[i]/arc[-1],1]])
        if reverse:q=q[::-1];uv=uv[::-1]
        b.face(q,material,normal=face_normal,uv=uv)


def panel(b, outline, mapping, normal, holes=(), material=P):
    """Constrained planar triangles followed by an affine 3D surface map."""
    pts, tris, loops = planar_mesh(outline, holes)
    uv = (pts-pts.min(0))/np.maximum(np.ptp(pts, axis=0), 1e-8)
    world = mapping(pts)
    for ids in tris:
        b.face(world[ids], material, normal=normal, uv=uv[ids])
    return loops


def recess(b, contour, mapping, normal, depth=.10, floor=D, walls=D):
    a = mapping(np.array(contour, float));n = f.mesh.unit(np.array(normal, float))
    bottom = a-n*depth
    ribbon(b, a, bottom, walls, inward=True)
    b.face(bottom, floor, normal=normal)
    return bottom


def plate(b, outline, mapping, normal, thick=.25, holes=(), floor=P):
    loops = panel(b, outline, mapping, normal, holes)
    front = mapping(loops[0]);back = front-f.mesh.unit(np.array(normal))*thick
    ribbon(b, front, back, P)
    b.face(back, P, normal=-np.array(normal))
    for h in loops[1:]:recess(b, h, mapping, normal, min(.09, thick*.4), floor)
    return loops


def loft(b, stations, material=P, caps=True, omit=()):
    rings = [np.array(q, float) for q in stations]
    for a, c in zip(rings, rings[1:]):
        axis=np.sum(np.cross(a,np.roll(a,-1,axis=0)),axis=0)
        reverse=np.dot(axis,c.mean(0)-a.mean(0))<0
        for i in range(len(a)):
            if i in omit:continue
            j = (i+1) % len(a);q = np.array([a[i], a[j], c[j], c[i]])
            b.face(q[::-1] if reverse else q,material)
    if caps:
        b.face(rings[0], material, normal=rings[0].mean(0)-rings[1].mean(0))
        b.face(rings[-1], material, normal=rings[-1].mean(0)-rings[-2].mean(0))


def octagon(z, w, bottom, top, cut=.20):
    cut = min(cut, w*.6, (top-bottom)*.35)
    return np.array([[-w+cut, top, z], [w-cut, top, z], [w, top-cut, z],
                     [w, bottom+cut, z], [w-cut, bottom, z], [-w+cut, bottom, z],
                     [-w, bottom+cut, z], [-w, top-cut, z]])


def mirror(groups, side):
    result = copy.deepcopy(groups)
    if side < 0:
        for g in result:
            g['corners'][..., 0] *= -1;g['corners'][..., 3] *= -1
            g['corners'] = g['corners'][:, [0, 2, 1]]
    return result


def nose_and_cabin_seat():
    b = B()
    specs = [(-13.186, .055, -.19, -.03), (-10.8, .37, -.34, .04),
             (-8.35, .76, -.49, .22), (-6.65, 1.13, -.68, .42),
             (-5.461, 1.70, -.81, .535)]
    rings = [octagon(z, w, bot, top, min(.16, w*.25)) for z, w, bot, top in specs]
    # Nose top gets real recessed ducts; it is not an intact face underneath them.
    loft(b, rings, omit=(0,))
    for i, (a, c) in enumerate(zip(rings, rings[1:])):
        z0, z1 = a[0, 2], c[0, 2]
        w0, w1 = a[1, 0], c[1, 0]
        t0, t1 = a[0, 1], c[0, 1]
        outline = np.array([[-w0, z0], [w0, z0], [w1, z1], [-w1, z1]])
        def mapping(q):
            return np.c_[q[:, 0], t0+(q[:, 1]-z0)/(z1-z0)*(t1-t0), q[:, 1]]
        normal = np.array([0, 1, -(t1-t0)/(z1-z0)])
        holes = []
        if i in (1, 2):
            hole = np.array([[-w0*.53, z0+.20], [w0*.53, z0+.20],
                             [w1*.70, z1-.18], [-w1*.70, z1-.18]])
            holes.append(hole)
        loops = panel(b, outline, mapping, normal, holes)
        for h in loops[1:]:
            recess(b, h, mapping, normal, .16)
            # Broad, sloped louvers within the duct, not tiny surface bolts.
            for z in np.linspace(h[0, 1]+.15, h[2, 1]-.22, 6 if i==1 else 5):
                w = np.interp(z, [h[0, 1], h[2, 1]], [h[1, 0], h[2, 0]])*.90
                q = mapping(np.array([[-w,z],[w,z],[w,z+.075],[-w,z+.075]]))
                q[:, 1] -= .075
                plate(b, [[-w,z],[w,z],[w,z+.075],[-w,z+.075]],
                    lambda ps, zz=z: mapping(ps)-[0,.075,0], normal, .035)
    add('Long_nose_with_inset_ducts', b)

    b = B()
    plan = np.array([[-1.70,-5.461],[1.70,-5.461],[1.91,-2.263],
                     [1.70,-1.45],[-1.70,-1.45],[-1.915,-2.263]])
    aperture = [[-1.19,-4.35],[1.19,-4.35],[1.20,-1.52],[-1.20,-1.52]]
    mapping = lambda q: np.c_[q[:,0],np.full(len(q),.226),q[:,1]]
    loops=panel(b,plan,mapping,[0,1,0],[aperture])
    top=mapping(loops[0]);bottom=top.copy();bottom[:,1]=-.82
    ribbon(b,top,bottom)
    b.face(bottom,P,normal=[0,-1,0])
    # Original cockpit's inner floor and rear wall close the aperture above this.
    add('Canopy_seat_and_forward_belly',b)


def upper_core_and_bay():
    b=B()
    # Thin central core below the wing slots; four broad upper side shoulders
    # provide the visible width without filling the wing retraction volume.
    loft(b,[octagon(-1.45,1.17,-.96,.54,.12),octagon(.20,1.17,-1.03,1.46,.12),
            octagon(4.60,1.17,-1.03,1.46,.12),octagon(5.405,1.34,-.91,1.08,.16)],omit=(0,))
    # Deck with a true rectangular opening for the original two leaves.
    mapping=lambda q:np.c_[q[:,0],np.full(len(q),1.46),q[:,1]]
    outer=[[-1.05,.20],[1.05,.20],[1.05,4.60],[-1.05,4.60]]
    aperture=[[-.82,.83],[.79,.83],[.79,4.43],[-.82,4.43]]
    loops=panel(b,outer,mapping,[0,1,0],[aperture])
    # Hold is shallow and complete. Native BW has no metal library; use its
    # own dark interior panel until the material pass, never exterior metal.
    recess(b,loops[1],mapping,[0,1,0],.72,D,D)
    # Close the structural skin below the original cabin's rising rear shell;
    # it starts behind the cabin's actual interior rear bulkhead.
    b.face([[-1.05,.54,-1.45],[1.05,.54,-1.45],[1.05,1.46,.178],[-1.05,1.46,.178]],P,normal=[0,1,-1])
    b.face([[-1.05,1.46,.178],[1.05,1.46,.178],[1.05,1.46,.20],[-1.05,1.46,.20]],P,normal=[0,1,0])
    b.face([[-1.05,1.46,4.6],[1.05,1.46,4.6],[1.18,1.08,5.405],[-1.18,1.08,5.405]],P,normal=[0,1,1])
    add('Upper_core_and_complete_hold',b)


def shoulder(side):
    b=B()
    # Continuous forward saddle: no cylindrical hinges, no floating plates.
    sections=[]
    for z,inner,outer,roof,base in [(-5.25,1.53,1.90,.56,.12),(-3.25,1.58,2.72,1.03,.02),
                                  (-1.30,1.19,3.40,1.35,.30),(.20,1.19,3.50,1.35,.33),
                                  (2.92,1.19,3.50,1.35,.33)]:
        sections.append([[inner,base,z],[outer,base,z],[outer,roof-.32,z],
                         [outer-.28,roof,z],[inner,roof,z]])
    loft(b,sections,omit=(3,))
    for i,(a,c) in enumerate(zip(np.array(sections),np.array(sections[1:]))):
        z0,z1=a[0,2],c[0,2]
        outline=np.array([[a[4,0],z0],[a[3,0],z0],[c[3,0],z1],[c[4,0],z1]])
        def roof(q):return np.c_[q[:,0],a[3,1]+(q[:,1]-z0)/(z1-z0)*(c[3,1]-a[3,1]),q[:,1]]
        n=[0,1,-(c[3,1]-a[3,1])/(z1-z0)]
        holes=[]
        if i==3:
            holes=[[[1.48,.46],[2.91,.46],[2.91,2.64],[1.48,2.64]]]
        if i==1:
            holes=[[[1.88,-2.87],[2.46,-2.87],[2.85,-1.62],[1.88,-1.62]]]
        ls=panel(b,outline,roof,n,holes)
        for h in ls[1:]:recess(b,h,roof,n,.11,P,D)
    # A second stepped shoulder carries the aft grille and engine seat. Its
    # shape is continuous with the saddle, leaving a long open slot below.
    profile=np.array([[2.92,.33],[4.18,.33],[5.42,-.55],[5.42,.80],[4.28,1.43],[2.92,1.43]])
    vent=np.array([[3.18,.63],[4.00,.63],[5.10,-.12],[5.10,.65],[4.10,1.16],[3.18,1.16]])
    # The side face angles inwards toward the rectangular upper exhaust.
    def mapping(q):
        x=np.interp(q[:,0],[2.92,5.42],[3.50,1.52])
        return np.c_[x,q[:,1],q[:,0]]
    normal=np.array([1,0,(3.50-1.52)/(5.42-2.92)])
    plate(b,profile,mapping,normal,.28,[vent],D)
    # Join the intake to the central deck with a complete sloping roof. The
    # grille is a hull wall, not a separate upright fence beside an empty roof.
    prev=None
    for z in [2.92,4.28,4.60,5.42]:
        x=np.interp(z,[2.92,5.42],[3.50,1.52])
        y=np.interp(z,[2.92,4.28,5.42],[1.43,1.43,.80])
        xi=np.interp(z,[2.92,4.60,5.42],[1.05,1.05,1.18])
        yi=np.interp(z,[2.92,4.60,5.42],[1.46,1.46,1.08])
        current=np.array([[xi,yi,z],[x,y,z]])
        if prev is not None:b.face([prev[0],prev[1],current[1],current[0]],P,normal=[0,1,0])
        prev=current
    b.face([[1.19,1.35,2.92],[3.22,1.35,2.92],[3.50,1.43,2.92],[1.05,1.46,2.92]],P,normal=[0,0,-1])
    # Distinct longitudinal fins, clipped to the intake's sloped silhouette.
    for z in np.linspace(3.36,4.98,10):
        top=np.interp(z,[3.18,4.1,5.1],[1.16,1.16,.65])-.04
        bot=np.interp(z,[3.18,4.,5.1],[.63,.63,-.12])+.04
        p=np.array([[z-.035,bot],[z+.035,bot],[z+.035,top],[z-.035,top]])
        plate(b,p,lambda q:mapping(q)-f.mesh.unit(normal)*.035,normal,.055)
    # Fixed floor under the upper sliding wing. Concave floor follows the
    # support silhouette, but never covers the top of the wing slot.
    plan=[[1.18,-1.62],[2.98,-1.62],[3.72,-.62],[3.72,3.60],[2.40,4.30],[1.18,4.30]]
    plate(b,plan,lambda q:np.c_[q[:,0],np.full(len(q),-.77),q[:,1]],[0,1,0],.22)
    add(('Port' if side<0 else 'Starboard')+'_stepped_saddle',mirror(b.groups(),side))


def wing(side,lower=False):
    b=B()
    if not lower:
        outer=np.array([[3.28,-1.30],[3.96,-2.05],[3.98,-2.75],[4.65,-2.10],[6.80,.90],[6.95,3.05],
                        [6.18,4.05],[5.60,4.05],[5.60,3.55],[4.74,3.55],
                        [4.74,3.10],[3.28,3.10]])
        field=[[3.55,-.90],[4.20,-1.85],[4.21,-2.20],[4.48,-1.92],[6.50,1.02],[6.60,2.88],[6.06,3.80],
               [5.85,3.80],[5.85,3.30],[4.99,3.30],[4.99,2.85],[3.55,2.85]]
        # Long inlet aligned with the stepped root, modeled in the wing itself.
        slot=[[3.60,-.52],[3.84,-.40],[3.84,2.52],[3.60,2.52]]
        mapping=lambda q:np.c_[q[:,0],-.04-.06*(q[:,0]-3.28),q[:,1]]
        normal=np.array([.06,1,0])
        ls=panel(b,outer,mapping,normal,[field]);front=mapping(ls[0])
        back=front-np.array([0,.29,0]);ribbon(b,front,back)
        b.face(back,P,normal=[-.06,-1,0])
        inner=mapping(ls[1])-np.array([0,.075,0]);ribbon(b,mapping(ls[1]),inner,D,True)
        recessed=lambda q:mapping(q)-[0,.075,0]
        ls2=panel(b,ls[1],recessed,normal,[slot])
        recess(b,ls2[1],recessed,normal,.08)
        for z in np.linspace(-.26,2.33,8):
            plate(b,[[3.62,z],[3.82,z],[3.82,z+.045],[3.62,z+.045]],
                  lambda q:recessed(q)-[0,.035,0],normal,.025)
        # Integral sliding shoe reaches the fixed saddle floor. Without it the
        # blade is suspended in an empty slot in the rear and underside views.
        shoe=np.array([[3.29,-.12],[3.55,-.12],[3.55,2.44],[3.29,2.44]])
        shoe_top=np.c_[shoe[:,0],-.33-.06*(shoe[:,0]-3.28),shoe[:,1]]
        shoe_low=np.array([[3.31,-.748,-.06],[3.53,-.748,-.06],
                           [3.53,-.748,2.38],[3.31,-.748,2.38]])
        loft(b,[shoe_top,shoe_low],D)
        owner=f'bw_{"port" if side<0 else "star"}_wingX01_lod1'
    else:
        outer=np.array([[2.64,-2.50],[3.10,-2.27],[4.13,-1.14],[4.03,-.64],[3.57,-.36],[2.64,-.36]])
        field=[[2.79,-2.10],[3.04,-1.96],[3.89,-1.07],[3.79,-.75],[3.49,-.56],[2.79,-.56]]
        mapping=lambda q:np.c_[q[:,0],-5.43-.08*(q[:,0]-2.64),q[:,1]]
        plate(b,outer,mapping,[.08,1,0],.25,[field],P)
        shoe=np.array([[2.69,-1.55],[2.92,-1.55],[2.92,-.78],[2.69,-.78]])
        n=f.mesh.unit(np.array([.08,1,0]))
        shoe_top=np.c_[shoe[:,0],-5.43-.08*(shoe[:,0]+n[0]*.25-2.64)-n[1]*.25,shoe[:,1]]
        shoe_low=np.array([[2.71,-5.86,-1.51],[2.90,-5.86,-1.51],
                           [2.90,-5.86,-.82],[2.71,-5.86,-.82]])
        loft(b,[shoe_top,shoe_low],D)
        owner=f'bw_{"port" if side<0 else "star"}_wingX02_lod1'
    add(('Port' if side<0 else 'Starboard')+('_lower_wing' if lower else '_upper_wing'),
        mirror(b.groups(),side),owner,'Four native sliding wings')


def vertical_web_and_gondola():
    b=B()
    outline=np.array([[-4.40,-.76],[3.10,-.76],[.62,-4.93],[-2.56,-4.93]])
    hole=np.array([[-3.47,-1.36],[2.13,-1.36],[.14,-4.24],[-2.04,-4.24]])
    def mapping(q):return np.c_[.58+(q[:,1]+4.93)*.125,q[:,1],q[:,0]]
    normal=np.array([1,-.125,0])
    ls=panel(b,outline,mapping,normal,[hole])
    recess(b,ls[1],mapping,normal,.15,D)
    # Two large stepped structural fields within the web: existing contours,
    # not ornamental fasteners. Space between them is a continuous dark recess.
    for poly in ([[-3.16,-1.51],[-.62,-1.51],[-.82,-3.99],[-1.91,-3.99]],
                 [[-.42,-1.51],[1.76,-1.51],[.03,-3.99],[-.60,-3.99]]):
        plate(b,poly,lambda q:mapping(q)-f.mesh.unit(normal)*.08,normal,.055)
    right=mapping(ls[0]);left=right.copy();left[:,0]*=-1
    # End walls close the whole structural web between mirrored broad sides.
    ribbon(b,right,left,P)
    add('Central_web_right',b)
    other=B();panel(other,outline,lambda q:mapping(q)*[-1,1,1],[-1,-.125,0],[hole])
    recess(other,hole,lambda q:mapping(q)*[-1,1,1],[-1,-.125,0],.15,D)
    for poly in ([[-3.16,-1.51],[-.62,-1.51],[-.82,-3.99],[-1.91,-3.99]],
                 [[-.42,-1.51],[1.76,-1.51],[.03,-3.99],[-.60,-3.99]]):
        plate(other,poly,lambda q:(mapping(q)-f.mesh.unit(normal)*.08)*[-1,1,1],[-1,-.125,0],.055)
    add('Central_web_left',other)

    b=B()
    def slotted(z,w,bottom,top):
        return np.array([[-w+.16,top,z],[w-.16,top,z],[w,top-.14,z],
                         [w,-5.20,z],[.55,-5.20,z],[.55,-6.07,z],[w,-6.07,z],
                         [w,bottom+.16,z],[w-.16,bottom,z],[-w+.16,bottom,z],
                         [-w,bottom+.16,z],[-w,-6.07,z],[-.55,-6.07,z],
                         [-.55,-5.20,z],[-w,-5.20,z],[-w,top-.14,z]])
    loft(b,[slotted(-2.80,1.03,-6.72,-4.95),slotted(.10,1.22,-6.65,-4.85)])
    loft(b,[octagon(-4.02,.75,-6.36,-5.35,.16),octagon(-2.82,1.03,-6.72,-4.95,.18)])
    # Lower sliding saddles use covered pockets; their open mouth remains clear
    # through the original -0.1 Y / +0.3 Z retraction.
    for side in (-1,1):
        t=B();plan=[[1.05,-2.80],[1.76,-2.72],[2.98,-1.55],[2.98,.40],[1.15,.40]]
        plate(t,plan,lambda q:np.c_[q[:,0],np.full(len(q),-5.20),q[:,1]],[0,1,0],.13)
        plate(t,plan,lambda q:np.c_[q[:,0],np.full(len(q),-5.98),q[:,1]],[0,1,0],.15)
        for g in mirror(t.groups(),side):b.tris[g['material']].extend(g['corners'])
    add('Lower_gondola_and_sliding_saddles',b)


def engine(lower=False):
    b=B();y=-5.7074509 if lower else .0282997
    front=.075 if lower else 5.405;scale=.86 if lower else 1.0
    # Rectangular section with four intentionally clipped corners; the cuts
    # shape the nozzle, no generalized bevel or circular tessellation modifier.
    rings=[]
    for z,w,h,cut in [(front,1.30,.98,.20),(front+.32,1.50,1.02,.23),
                       (front+1.20,1.37,.88,.18)]:
        rings.append(octagon(z,w*scale,y-h*scale,y+h*scale,cut*scale))
    loft(b,rings,caps=False)
    b.face(rings[0],P,normal=[0,0,-1])
    lip=octagon(front+1.20,1.13*scale,y-.65*scale,y+.65*scale,.13*scale)
    ribbon(b,rings[-1],lip,E,face_normal=[0,0,1])
    deep=lip.copy();deep[:,2]=front+.83
    ribbon(b,lip,deep,D,True);b.face(deep,G,(0,0,1,1),[0,0,1])
    # Visible thick vertical louvers are a principal feature of B04's nozzle.
    for x in np.linspace(-.99*scale,.99*scale,12 if not lower else 9):
        ring=[]
        for z in [front+.86,front+1.11]:
            ring.append(np.array([[x-.025,y-.57*scale,z],[x+.025,y-.57*scale,z],
                                   [x+.025,y+.57*scale,z],[x-.025,y+.57*scale,z]]))
        loft(b,ring,E)
    add('Lower_rectangular_engine' if lower else 'Upper_rectangular_engine',b,
        'bw_eng02_lod1' if lower else 'bw_eng01_lod1','Two engines')


def native_parts(scene,names,mats):
    byname={}
    for g in scene:byname.setdefault(names[g['part'].lower()],[]).append(g)
    root=byname['Root'];keep={
        'pir_bw_panel2sideD':list(range(54)),
        'pir_bw_panel_256D':list(range(32,36))+list(range(48,80)),
        'pir_bw_panel_256':[60,61]+list(range(96,104))+list(range(235,243))}
    cabin=[]
    for g in root:
        indices=keep.get(mats[g['material']]['name'],[])
        if indices:cabin.append(dict(g,corners=g['corners'][indices].copy()))
    add('Native_cockpit_shell_and_frame',cabin,'Root','Immutable original cabin')
    add('bw_glass_lod1',copy.deepcopy(byname['bw_glass_lod1']),'bw_glass_lod1','Immutable original cabin')
    for name,x0,x1 in [('baydoor01_lod1',-.004,.873),('baydoor02_lod1',-.9025,-.025)]:
        door=B()
        plate(door,[[x0,.84],[x1,.84],[x1,4.42],[x0,4.42]],
              lambda q:np.c_[q[:,0],np.full(len(q),1.61),q[:,1]],[0,1,0],.12)
        add(name,door,name,'Flat cargo leaves / native hinges')
    # Retain source helper components, so Cmpnd/Cons and animation bindings are
    # unchanged. Replace missing-material placeholder triangles with BW dark.
    generated={'Root','bw_glass_lod1','baydoor01_lod1','baydoor02_lod1',
               'bw_eng01_lod1','bw_eng02_lod1'}
    for name,gs in byname.items():
        if name in generated or 'wingX' in name:continue
        if name=='bw_boards_lod1':
            # Old boards close the original wings at x=3.77; retaining them
            # would leave a visible wall cutting across our new sliding blades.
            # Keep the semantic owner/joint, author new innermost pocket walls.
            boards=B()
            for x,y0,y1,z0,z1 in [(1.185,-.76,.22,-1.35,4.1),(.565,-6.06,-5.21,-2.77,.06)]:
                for side in [-1,1]:
                    boards.face([[side*x,y0,z0],[side*x,y1,z0],[side*x,y1,z1],[side*x,y0,z1]],
                                D,normal=[side,0,0])
            add(name,boards,name,'Pocket inner walls')
            continue
        for g in gs:
            if mats[g['material']]['kind']=='MISSING':
                # Keep a nondegenerate helper VMesh for the original construct
                # node, entirely inside fixed opaque skin. Do not expose the
                # old missing-material marker triangle beside a redesigned wing.
                g['material']=D
                p=g['corners'][...,:3];p+=np.array([0,-.50,2.0])-p.reshape(-1,3).mean(0)
        add(name,copy.deepcopy(gs),name,'Native rig helpers')
    return keep


def private_salt(nodes):
    salt=secrets.token_hex(6);mapping={}
    for i,n in enumerate(f.mesh.child(nodes[0],'VMeshLibrary').children):
        old=n.name;n.name=f'bwp_b04_{i:02}_{salt}.vms';mapping[old]=n.name
    crcs={f.mesh.crc(a):f.mesh.crc(c) for a,c in mapping.items()}
    for path,n in f.mesh.walk(nodes):
        if path.lower().endswith('/vmeshref'):
            raw=bytearray(n.blob);old=struct.unpack_from('<I',raw,4)[0]
            struct.pack_into('<I',raw,4,crcs[old]);n.blob=bytes(raw)
    for e in f.mesh.child(nodes[0],'Cmpnd').children:
        if e.name=='Cons':continue
        ref=f.mesh.child(e,'File name');old=f.mesh.string(ref.blob)
        semantic=f.mesh.string(f.mesh.child(e,'Object name').blob)
        new=f'b04_{semantic}_{salt}.3db';assert len(new)<64
        f.mesh.child(nodes[0],old).name=new;ref.blob=new.encode()+b'\0';mapping[old]=new
    return salt,mapping


def normalized_tree(native):
    nodes=copy.deepcopy(native)
    for file in f.component_map(nodes):
        part=f.mesh.child(nodes[0],file)
        part.children=[n for n in part.children if n.name.lower() not in ('vmeshpart','multilevel','vmeshwire')]
        part.children.append(f.folder('MultiLevel'))
    nodes[0].children=[n for n in nodes[0].children if n.name.lower() not in ('material library','texture library')]
    return nodes


def export(header,native,world,pose,dest,animated=False):
    nodes=normalized_tree(native);names=f.component_map(nodes)
    tr,_=f.audit.transforms(native,pose)
    local={}
    for file,semantic in names.items():
        r,t=tr[file.lower()];gs=copy.deepcopy(world[semantic])
        for g in gs:
            g['corners'][...,:3]=(g['corners'][...,:3]-t)@r
            g['corners'][...,3:6]=g['corners'][...,3:6]@r
        local[file]=gs
    f.write_geometry(nodes,[local])
    if not animated:
        records=[]
        for file,semantic in names.items():
            if semantic=='Root':continue
            r,t=tr[file.lower()]
            records.append(b'Root\0'.ljust(64,b'\0')+semantic.encode().ljust(64,b'\0')+
                           np.r_[t,r.reshape(-1)].astype('<f4').tobytes())
        f.mesh.child(f.mesh.child(nodes[0],'Cmpnd'),'Cons').children=[f.mesh.Node('Fix',b''.join(records))]
        nodes[0].children=[n for n in nodes[0].children if n.name.lower()!='animation']
    for p,n in f.mesh.walk(nodes):
        if p.lower().endswith('/switch2'):n.blob=np.array([0,10000],'<f4').tobytes()
    salt,mapping=private_salt(nodes)
    dest.write_bytes(f.mesh.write_tree(header,nodes))
    _,check=f.mesh.read_tree(dest.read_bytes());decoded=f.local_geometry(check)
    counts={f.component_map(check)[k]:sum(len(g['corners']) for g in gs) for k,gs in decoded.items()}
    # Compare all output vertices/UVs against float32 source geometry.
    bysemantic={names[k]:f.merge(gs) for k,gs in local.items()};error=0.
    for file,gs in decoded.items():
        name=f.component_map(check)[file];expected={g['material']:g['corners'] for g in bysemantic[name]}
        for g in gs:
            a=g['corners'];c=expected[g['material']]
            assert a.shape==c.shape,(name,a.shape,c.shape)
            error=max(error,float(abs(a-c).max()))
    assert error<1e-5,error
    assert all(0<n<21000 for n in counts.values()),counts
    assert not any(n.name.lower() in ('material library','texture library') for n in check[0].children)
    return dict(path=dest.as_posix(),sha256=f.digest(dest),salt=salt,resources=mapping,triangles=counts,
                readback_max_float_error=error,animated=animated,embedded_materials=False,wireframe='not authored at shape stage')


def main():
    assert shutil.disk_usage(ROOT).free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    selection=json.loads((TOPIC/'selection.json').read_text(encoding='utf8'))
    assert f.digest(SOURCE)==selection['source_sha256']
    source_row=json.loads((reference.a.OUT/'ships/bw_elite_pir/source.json').read_text(encoding='utf8'))
    scene,mats,stats=reference.a.source.load(source_row,pose=('Sc_extend wing',0))
    header,nodes=f.mesh.read_tree(SOURCE.read_bytes());names={k.lower():v for k,v in f.component_map(nodes).items()}
    pinned={p.as_posix():f.digest(p) for p in [SOURCE,MAT,ENV,TOPIC/selection['art'],TOPIC/selection['rear_view']['art']]}
    original=TOPIC/'elite/source';original.mkdir(exist_ok=True)
    pinned_cmp=original/'bw_pir_elite_original.cmp'
    if pinned_cmp.exists():assert f.digest(pinned_cmp)==selection['source_sha256']
    else:shutil.copyfile(SOURCE,pinned_cmp)
    OBJECTS.clear();copied=native_parts(scene,names,mats)
    nose_and_cabin_seat();upper_core_and_bay();vertical_web_and_gondola()
    for s in [-1,1]:shoulder(s);wing(s);wing(s,True)
    engine();engine(True)
    world={}
    for e in OBJECTS:world.setdefault(e['owner'],[]).extend(e['groups'])
    world={n:f.merge(gs) for n,gs in world.items()}
    assert set(world)==set(names.values()),(set(world)-set(names.values()),set(names.values())-set(world))
    used={g['material'] for gs in world.values() for g in gs};assert used<=mats.keys()
    assert not any('metal' in (mats[m]['texture']+' '+mats[m]['name']).lower() for m in used)
    material_info={}
    texture_dir=OUT/'native_texture_references';texture_dir.mkdir(exist_ok=True)
    for m in used:
        entry=mats[m];image_path=None
        if entry['image']:
            p=texture_dir/(entry['texture'].replace('.tga','.png'));entry['image'].save(p);image_path=p.as_posix()
        material_info[m]={k:v for k,v in entry.items() if k!='image'};material_info[m]['image_path']=image_path
    exports=[]
    for name,animated in [('bw_pir_elite_b04_review_open.cmp',False),('bw_pir_elite_b04_animated.cmp',True)]:
        exports.append(export(header,nodes,world,('Sc_extend wing',0),OUT/name,animated))
    # Derive relative matrices from the real native constructs at three poses.
    flight,_=f.audit.transforms(nodes,('Sc_extend wing',0));folded,_=f.audit.transforms(nodes,('Sc_extend wing',1))
    door,_=f.audit.transforms(nodes,('Sc_open baydoor',1))
    motion={}
    for file,name in f.component_map(nodes).items():
        r,t=flight[file.lower()]
        for target,kind in [(folded,'wing'),(door,'cargo')]:
            rr,tt=target[file.lower()];dr=rr@r.T;dt=tt-dr@t
            if kind=='cargo' and not name.startswith('baydoor'):continue
            if kind=='wing' and name.startswith('baydoor'):continue
            if np.max(abs(dr-np.eye(3)))>1e-6 or np.max(abs(dt))>1e-6:
                motion[name]=dict(kind=kind,rotation=dr,translation=dt,
                    pivot=np.linalg.lstsq(np.eye(3)-dr,dt,rcond=1e-5)[0] if kind=='cargo' else np.zeros(3))
    # Static open baydoor review keeps wings in flight, with HP local data intact.
    open_world=copy.deepcopy(world)
    for name,m in motion.items():
        if m['kind']!='cargo':continue
        for g in open_world[name]:
            g['corners'][...,:3]=g['corners'][...,:3]@m['rotation'].T+m['translation']
            g['corners'][...,3:6]=g['corners'][...,3:6]@m['rotation'].T
    # Export against flight transforms, then change only fixed door transforms
    # would apply motion twice; instead use a source clone with open door state.
    # This third static mesh is a geometry review, not a new animated rig.
    exports.append(export(header,nodes,open_world,('Sc_extend wing',0),OUT/'bw_pir_elite_b04_review_bay_open.cmp'))
    _,written=f.mesh.read_tree((OUT/'bw_pir_elite_b04_animated.cmp').read_bytes())
    def hp_leaves(ns):
        sem={k.lower():v for k,v in f.component_map(ns).items()}
        return {sem[p.split('/')[2].lower()]+'/'+p.lower().split('/hardpoints/')[-1]:hashlib.sha256(n.blob).hexdigest()
                for p,n in f.mesh.walk(ns) if '/hardpoints/' in p.lower()}
    native_hp=hp_leaves(nodes);output_hp=hp_leaves(written)
    assert native_hp==output_hp
    native_animation={p.lower().split('/animation/')[-1]:hashlib.sha256(n.blob).hexdigest()
                      for p,n in f.mesh.walk(nodes) if '/animation/' in p.lower()}
    output_animation={p.lower().split('/animation/')[-1]:hashlib.sha256(n.blob).hexdigest()
                      for p,n in f.mesh.walk(written) if '/animation/' in p.lower()}
    assert native_animation==output_animation
    cons=lambda ns:{p.lower():hashlib.sha256(n.blob).hexdigest() for p,n in f.mesh.walk(ns) if '/cmpnd/cons/' in p.lower()}
    assert cons(nodes)==cons(written)
    dump(OUT/'geometry.json',dict(sources=pinned,objects=OBJECTS,materials=material_info,motion=motion,
        cargo_ray_probes=[([0,1.38,2.5],[0,-1,0]),([0,1.1,2.5],[1,0,0]),([0,1.1,2.5],[-1,0,0]),
                          ([0,1.1,2.5],[0,0,1]),([0,1.1,2.5],[0,0,-1])]))
    manifest=dict(stage='unapproved offline shape prototype',concept='B04 / ELITE',sources=pinned,
                  original_pinned=pinned_cmp.as_posix(),native_triangles=stats['triangles'],
                  total_triangles=sum(sum(len(g['corners']) for g in gs) for gs in world.values()),
                  cockpit_copied_indices=copied,all_native_hardpoint_leaves_identical=True,
                  all_native_animation_leaves_identical=True,exports=exports,
                  native_hardpoint_count=stats['hardpoint_count'],native_animation_leaf_count=len(native_animation),
                  native_cons_identical=True,cargo_leaves='New flat leaves on unchanged native Rev joints',
                  uv_status='Provisional native atlas references. Authoritative form review uses clay.',
                  notes=['Four native translating wings, unchanged launch playback.',
                         'Exactly two engines, ignoring the false third face on original generated SIDE.',
                         'Native cockpit copied whole: panes, frame, rear shell, inner walls and floor.',
                         'No final LODs, SUR, HUD wire or damage generated; no game writes.'])
    dump(OUT/'manifest.json',manifest)
    print(json.dumps(dict(output=OUT.as_posix(),triangles=manifest['total_triangles'],exports=[e['path'] for e in exports]),indent=2))


if __name__=='__main__':main()
