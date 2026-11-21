"""BW B04 revision 03: REAR-led upper hull and a narrow pyramidal keel.

Static shape authoring only. No animation design, collision, LOD generation or
DATA writes. Native cockpit triangles are copied without any modification.
"""
import copy
import json
import shutil
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree
import bw_elite_b04 as base
import bw_elite_b04_02 as geom

B=base.B
f=base.f
P,D,E,G=base.P,base.D,base.E,base.G
A=geom.A
OUT=base.TOPIC/'elite/prototypes/b04_03'
PINNED=geom.PINNED


def add(name,b,owner='Root',category='Upper body / authored B04 REAR forms'):
    base.add(name,b,owner,category)


def pair(name,b,owner=None,category='Upper body / authored B04 REAR forms'):
    for side,label in [(-1,'Port'),(1,'Starboard')]:
        semantic=owner.format(side='port' if side<0 else 'star') if owner else 'Root'
        add(label+'_'+name,base.mirror(b.groups(),side),semantic,category)


def orient(q,out):
    q=np.asarray(q,float)
    if np.dot(np.cross(q[1]-q[0],q[2]-q[0]),out)<0:q=q[::-1]
    return q


def inset(b,outline,mapping,normal,depth=.12,floor=D,walls=D):
    return base.recess(b,outline,mapping,normal,depth,floor,walls)


def face_with_pockets(b,q,holes=(),depth=.12,skin=P,floor=D,walls=D):
    return geom.face_field(b,q,holes,depth,skin,floor,walls)


def vanes(b,mapping,normal,count,lo=.16,hi=.84,axis=1,margin=.17,thick=.040,depth=.085,material=E):
    n=f.mesh.unit(np.asarray(normal))
    for a in np.linspace(lo,hi,count):
        if axis==1:poly=[[margin,a],[1-margin,a+.020],[1-margin,a+.020+thick],[margin,a+thick]]
        else:poly=[[a,margin],[a+thick,margin],[a+thick,1-margin],[a,1-margin]]
        geom.closed_plate(b,poly,lambda p:mapping(p)-n*depth,n,.035,material)


def cross_section(z,roof,roof_half):
    # Broad oblique cheek, NOT a small bevel around a rectangular box.
    return np.array([[-roof_half,roof,z],[roof_half,roof,z],
                     [roof_half+.45,roof-.22,z],[roof_half+.9012,roof-2.10,z],
                     [roof_half+.12,roof-2.40,z],[-roof_half-.12,roof-2.40,z],
                     [-roof_half-.9012,roof-2.10,z],[-roof_half-.45,roof-.22,z]])


def cockpit_and_native_owners(scene,names,mats):
    keep=base.native_parts(scene,names,mats)
    base.OBJECTS[:]=[e for e in base.OBJECTS
        if not e['owner'].startswith('baydoor') and e['category']!='Pocket inner walls']
    tiny=B();tiny.face([[0,-.4,2],[.01,-.4,2],[0,-.39,2]],D)
    add('Hidden_original_boards_owner',tiny,'bw_boards_lod1','Native rig helpers')
    return keep


def nose_and_cabin_surround():
    # Reuse the actual paired intakes and the exact original cabin seat; the
    # section beyond the cabin is replaced by a new oblique upper fuselage.
    geom.nose()
    # Angular cheeks around the outside of the original cabin base. The
    # aperture and glazing are never covered or reconstructed.
    b=B()
    plan=np.array([[1.71,-5.45],[1.92,-3.65],[2.13,-2.56],[2.76,-2.07],
                   [2.76,-1.25],[1.80,-1.60],[1.69,-2.25]])
    def top(q):return np.c_[q[:,0],.22+(q[:,1]+5.45)*.055,q[:,1]]
    geom.closed_plate(b,plan,top,[0,1,-.055],.32)
    pair('angular_cabin_lower_cheek',b)


def main_fuselage():
    b=B()
    lead=base.octagon(-1.45,1.17,-.78,.54,.12)
    stations=[lead,cross_section(.20,1.54,1.08),cross_section(2.60,1.70,1.12),cross_section(5.15,1.70,1.01)]
    for k,(a,c) in enumerate(zip(stations,stations[1:])):
        for i in range(1,8):
            j=(i+1)%8
            q=orient([a[i],a[j],c[j],c[i]],(a[i]+a[j]+c[i]+c[j])/4-(a.mean(0)+c.mean(0))/2)
            if k==2 and i in (2,6):
                mapping,n,loops=face_with_pockets(b,q,[[[.10,.07],[.86,.07],[.86,.92],[.10,.92]]],.24)
                vanes(b,mapping,n,17,lo=.12,hi=.85,axis=1,margin=.15,thick=.026,depth=.07)
            elif i==4 and k>=1:
                # Continuous belly panels visible in B04_VIEWS_B/BOTTOM.
                holes=[[[.12,.10],[.88,.10],[.88,.45],[.12,.45]],
                       [[.12,.55],[.88,.55],[.88,.90],[.12,.90]]]
                face_with_pockets(b,q,holes,.055,P,P,D)
            elif k==2 and i in (1,7):
                face_with_pockets(b,q,[[[.20,.09],[.80,.09],[.80,.88],[.20,.88]]],.025,A,P,D)
            else:b.face(q,P)
    b.face(lead,P,normal=[0,0,-1]);b.face(stations[-1],P,normal=[0,0,1])
    # New aft cabin transition closes the width taper. Cabin remains bit exact.
    b.face([lead[0],lead[1],stations[1][1],stations[1][0]],P,normal=[0,1,-1])
    # Short paired service leaves fit the actual top-deck opening. Animation
    # deliberately not considered; pose is only a static visual prototype.
    def deck(q):return np.c_[q[:,0],1.54+(q[:,1]-.20)*(.16/2.4),q[:,1]]
    normal=np.array([0,1,-.16/2.4])
    outer=[[-1.08,.20],[1.08,.20],[1.12,2.60],[-1.12,2.60]]
    aperture=[[-.82,.43],[.82,.43],[.82,2.33],[-.82,2.33]]
    loops=base.panel(b,outer,deck,normal,[aperture])
    inset(b,loops[1],deck,normal,.56,D,D)
    # Aft deck: low pad up front and a real transverse recess behind it.
    q=[stations[2][0],stations[2][1],stations[3][1],stations[3][0]]
    mapping,n,ls=face_with_pockets(b,orient(q,[0,1,0]),[[[.11,.67],[.89,.67],[.89,.93],[.11,.93]]],.11)
    # Slot on the rear roof is divided across its width, as the REAR detail.
    for u in np.linspace(.16,.81,15):
        geom.closed_plate(b,[[u,.71],[u+.025,.71],[u+.025,.89],[u,.89]],
                          lambda p:mapping(p)-n*.047,n,.035,E)
    add('Octagonal_upper_fuselage_oblique_cheek_grilles',b)

    for name,x0,x1 in [('baydoor01_lod1',.012,.86),('baydoor02_lod1',-.86,-.012)]:
        b=B();contour=[[x0,.39],[x1,.39],[x1,2.37],[x0,2.37]]
        hole=[[x0+.09,.52],[x1-.09,.52],[x1-.09,2.24],[x0+.09,2.24]]
        m=lambda q:deck(q)+f.mesh.unit(normal)*.012
        ls=base.panel(b,contour,m,normal,[hole]);inset(b,ls[1],m,normal,.025,P,D)
        front=m(ls[0]);back=front-f.mesh.unit(normal)*.105
        base.ribbon(b,front,back,E);b.face(back,D,normal=-normal)
        add(name,b,name,'Static baydoor leaves / form only')

    # Low mount geometry is drawn in the art; final hardpoint placement is a
    # later authoring pass. The pads are not placeholder cubes.
    b=B()
    for x,z,w,l,y in [(0,3.45,.49,.86,1.70),(-1.12,.48,.30,.55,1.60)]:
        plan=np.array([[-w+.09,-l/2],[w-.09,-l/2],[w,-l/2+.08],[w,l/2-.08],
                       [w-.09,l/2],[-w+.09,l/2],[-w,l/2-.08],[-w,-l/2+.08]])
        lower=np.c_[plan[:,0]+x,np.full(8,y),plan[:,1]+z]
        upper=lower.copy();upper[:,0]=x+(upper[:,0]-x)*.84;upper[:,2]=z+(upper[:,2]-z)*.84;upper[:,1]+=.21
        base.loft(b,[lower,upper],A,caps=False);b.face(lower,P,normal=[0,-1,0])
        inner=upper.copy();inner[:,0]=x+(inner[:,0]-x)*.69;inner[:,2]=z+(inner[:,2]-z)*.66
        base.ribbon(b,upper,inner,P,face_normal=[0,1,0]);inset(b,inner[:,[0,2]],lambda q:np.c_[q[:,0],np.full(len(q),y+.21),q[:,1]],[0,1,0],.045,E,D)
    add('Low_integral_equipment_seats',b)


def roots():
    b=B()
    # A continuous stepped saddle drops onto the wing at the aft corner.
    # Its large faces are authored to the REAR silhouette, not native travel.
    profile=np.array([[-2.58,.28],[-1.88,.68],[-1.42,.93],[2.35,.93],
                      [3.18,.19],[3.64,.08],[3.64,-.20],[-2.16,-.20]])
    recess=[[-1.37,.13],[2.58,.13],[2.16,.66],[-1.23,.66]]
    outer=lambda q:np.c_[np.full(len(q),2.76),q[:,1],q[:,0]]
    ls=base.panel(b,profile,outer,[1,0,0],[recess]);inset(b,ls[1],outer,[1,0,0],.33,D,D)
    for yy in [.19,.40]:
        # Stepped sill runs the length of the pocket; its ends meet the walls.
        pp=[[-1.20,yy],[2.14,yy],[2.07,yy+.055],[-1.20,yy+.055]]
        geom.closed_plate(b,pp,lambda q:outer(q)-[.18,0,0],[1,0,0],.055,E)
    rr=outer(ls[0]);ll=rr.copy();ll[:,0]=1.70
    ll[:,1]+=np.array([.0,.0,.21,.21,.27,.05,.0,.0])
    # A small built-in panel on the upper cap, with a real rebate. The aft
    # buttress remains broad and oblique instead of turning into a thin fin.
    for i in range(len(rr)):
        j=(i+1)%len(rr)
        q=orient([rr[i],rr[j],ll[j],ll[i]],(rr[i]+rr[j]+ll[j]+ll[i])/4-(rr.mean(0)+ll.mean(0))/2)
        if i==2:face_with_pockets(b,q,[[[.13,.15],[.87,.15],[.87,.83],[.13,.83]]],.028,P,P,D)
        else:b.face(q,A if i==3 else P)
    b.face(ll,P,normal=[-1,0,0])
    pair('stepped_shoulders_and_open_long_sill',b)
    b=B()
    # Low ledge goes into the wing thickness. No extra floating shelves.
    outline=[[1.70,-2.65],[2.33,-2.55],[3.12,-2.22],[3.12,3.71],[2.20,4.04],[1.70,3.52]]
    geom.closed_plate(b,outline,lambda q:np.c_[q[:,0],np.full(len(q),-.18),q[:,1]],[0,1,0],.22)
    pair('root_landing_lower_transition',b)
    b=B()
    # Fill the narrowing roof strip beside the preserved cabin, matching its
    # native outer rear border rather than bridging through any glass pane.
    q=[[1.32,.534,-1.70],[1.70,1.06,-1.42],[1.70,1.14,.20],[1.08,1.54,.20],[1.05,.54,-1.45]]
    b.face(q,P,normal=[0,1,0]);pair('closed_cabin_shoulder_transition',b)


WING=np.array([[2.66,-2.48],[3.34,-2.98],[6.69,-1.59],[7.10,-1.42],
               [7.10,.67],[6.80,.88],[5.58,1.32],[5.58,2.24],
               [4.16,2.73],[4.16,3.43],[2.66,3.93]])
# The short continuation uses precisely the same authored leading plane.
# An almost-collinear 0.00012 sliver would introduce a spurious edge split.
WING[3,1]=-2.98+(7.10-3.34)*(1.39/3.35)


def wing_top(q):
    q=np.asarray(q);x,z=q[:,0],q[:,1]
    leading=-2.98+(x-3.34)*(1.39/3.35)
    return np.c_[x,.13-.085*(x-2.66)+.10*np.clip((z-leading)/.43,0,1),z]


def wing_bottom(q):
    q=np.asarray(q);x,z=q[:,0],q[:,1]
    return np.c_[x,-.31-.025*(x-2.66),z]


def split_sections(outline,planes):
    sections=[np.asarray(outline)]
    for n,c in planes:
        next_sections=[]
        for poly in sections:
            for sign in [-1,1]:
                cut=geom.clip_line(poly,np.asarray(n)*sign,c*sign)
                if len(cut)<3:continue
                area=abs(np.sum(cut[:,0]*np.roll(cut[:,1],-1)-cut[:,1]*np.roll(cut[:,0],-1)))
                if area>1e-7:next_sections.append(cut)
        sections=next_sections
    return sections


def wings():
    b=B();slope=1.39/3.35;origin=-2.98-3.34*slope
    sections=split_sections(WING,[([-slope,1],origin),([-slope,1],origin+.43),([1,0],6.69)])
    duct=[[3.17,-1.77],[3.90,-1.48],[3.90,1.89],[3.17,2.17]]
    # One long stepped channel follows the aft spar, as in the accepted rear.
    spar=[[4.27,1.87],[5.31,1.52],[5.31,.84],[6.54,.40],
          [6.58,.54],[5.49,.96],[5.49,1.67],[4.30,2.06]]
    # Broad outer skin field has its own shallow rebate; no uniform tiny grid.
    field=[[4.20,-1.68],[6.46,-.73],[6.46,.15],[5.08,.65],[5.08,1.23],[4.20,1.52]]
    holes=[duct,spar,field]
    boundary={tuple(p) for p in WING}
    for section in sections:
        for p in section:
            if geom.boundary_parameter(p,WING)[0]<1e-6:boundary.add(tuple(np.round(p,8)))
        local=[h for h in holes if geom.inside(np.mean(h,axis=0),section)]
        material=A if section.mean(0)[0]>6.69 else P
        base.panel(b,geom.simple_outline(section),wing_top,[.085,1,0],local,material)
    for poly,depth,floor in [(duct,.22,D),(spar,.115,D),(field,.040,P)]:
        inset(b,poly,wing_top,[.085,1,0],depth,floor,D)
    # Actual stepped longitudinal ribs inside the large wing duct.
    for x in [3.31,3.54,3.77]:
        poly=[[x,-1.50],[x+.065,-1.47],[x+.065,1.78],[x,1.81]]
        geom.closed_plate(b,poly,lambda p:wing_top(p)-[0,.11,0],[.085,1,0],.055,E)
    # Underside has the broad panel fields and root channel visible in BOTTOM.
    bottom_holes=[[[3.20,-1.60],[3.70,-1.40],[3.70,2.48],[3.20,2.65]],
                  [[4.05,-1.81],[6.35,-.85],[6.35,.24],[5.0,.74],[5.0,1.67],[4.05,1.98]]]
    base.panel(b,WING,wing_bottom,[0,-1,0],bottom_holes)
    for i,h in enumerate(bottom_holes):inset(b,h,wing_bottom,[0,-1,0],.085 if i==0 else .035,D if i==0 else P,D)
    contour=np.array(sorted(boundary,key=lambda p:geom.boundary_parameter(np.asarray(p),WING)[1]))
    base.ribbon(b,wing_top(contour),wing_bottom(contour),P)
    pair('wide_wing_sculpted_planes_spar_and_dual_sided_recesses',b,'bw_{side}_wingX01_lod1','Upper wings / static shape')


def engine_ring(z):
    return np.array([[-1.00,1.44,z],[1.00,1.44,z],[1.42,1.09,z],[1.58,-.27,z],
                     [1.04,-.57,z],[-1.04,-.57,z],[-1.58,-.27,z],[-1.42,1.09,z]])


def nozzle_geometry():
    b=B();front=cross_section(5.15,1.70,1.01);rear=engine_ring(5.82)
    for i in range(8):
        j=(i+1)%8
        q=orient([front[i],front[j],rear[j],rear[i]],(front[i]+front[j]+rear[i]+rear[j])/4-(front.mean(0)+rear.mean(0))/2)
        if i in (2,6):
            mapping,n,ls=face_with_pockets(b,q,[[[.10,.12],[.90,.12],[.90,.88],[.10,.88]]],.085)
            vanes(b,mapping,n,16,lo=.15,hi=.82,axis=0,margin=.18,thick=.024,depth=.025)
        elif i==0:
            mapping,n,ls=face_with_pockets(b,q,[[[.12,.15],[.88,.15],[.88,.82],[.12,.82]]],.075)
            vanes(b,mapping,n,18,lo=.16,hi=.80,axis=0,margin=.21,thick=.023,depth=.025)
        else:b.face(q,P if i in (1,7) else E)
    b.face(front,P,normal=[0,0,-1])
    outer=base.octagon(5.88,1.26,-.49,1.33,.18)
    bevel=base.octagon(5.96,1.21,-.44,1.28,.17)
    inner=base.octagon(5.97,1.085,-.30,1.16,.10)
    deep=inner.copy();deep[:,2]=5.48
    base.ribbon(b,rear,outer,P,face_normal=[0,0,1])
    base.ribbon(b,outer,bevel,A)
    base.ribbon(b,bevel,inner,E,face_normal=[0,0,1])
    base.ribbon(b,inner,deep,D,True);b.face(deep,G,(0,0,1,1),[0,0,1])
    # Deep vertical exhaust vanes are a large geometric motif of this concept.
    for x in np.linspace(-.94,.94,16):
        p=np.array([[x-.022,-.20,5.50],[x+.022,-.20,5.50],[x+.022,1.06,5.50],[x-.022,1.06,5.50]])
        q=p.copy();q[:,2]=5.84;base.loft(b,[p,q],E)
    return b


def engines():
    b=nozzle_geometry();add('Upper_recessed_exhaust_and_three_face_collar_grilles',b,'bw_eng01_lod1','Two engines / authored REAR casing')
    groups=copy.deepcopy(b.groups())
    for g in groups:
        p=g['corners'][...,:3];p[...,0]*=.75;p[...,1]=(p[...,1]-.45)*.64-4.45;p[...,2]=(p[...,2]-5.15)*.85+1.45
        n=g['corners'][...,3:6];n/=np.array([.75,.64,.85]);n/=np.linalg.norm(n,axis=-1,keepdims=True)
    add('Lower_recessed_exhaust',groups,'bw_eng02_lod1','Two engines / authored REAR casing')


def pyramidal_stand():
    b=B()
    def ring(y,w,z0,z1,corner):
        return np.array([[-w+corner,y,z0],[w-corner,y,z0],[w,y,z0+corner],[w,y,z1-corner],
                         [w-corner,y,z1],[-w+corner,y,z1],[-w,y,z1-corner],[-w,y,z0+corner]])
    top=ring(-.65,.94,-.65,2.80,.20);low=ring(-3.78,.42,.20,1.64,.11)
    for i in range(8):
        j=(i+1)%8
        q=orient([top[i],top[j],low[j],low[i]],(top[i]+top[j]+low[i]+low[j])/4-(top.mean(0)+low.mean(0))/2)
        if i in (2,6):
            mapping,n,loops=face_with_pockets(b,q,[[[.16,.13],[.84,.13],[.78,.84],[.22,.84]]],.075,P,P,D)
            # A diagonal recessed split changes the light on the broad face,
            # leaving its pyramidal structural corners sharp and uninterrupted.
        elif i in (0,4):face_with_pockets(b,q,[[[.19,.19],[.81,.19],[.75,.75],[.25,.75]]],.045,P,P,D)
        else:b.face(q,A if i in (1,5) else P)
    b.face(top,P,normal=[0,1,0]);b.face(low,P,normal=[0,-1,0])
    add('Narrow_truncated_pyramid_keel',b,category='Narrow lower support / user redesign')


def lower_gondola():
    b=B()
    rear=cross_section(5.15,1.70,1.01)
    rear[:,0]*=.75;rear[:,1]=(rear[:,1]-.45)*.64-4.45;rear[:,2]=1.45
    mid=rear.copy();mid[:,2]=-.88
    front=base.octagon(-1.57,.71,-5.06,-4.23,.16)
    for k,(a,c) in enumerate(zip([front,mid],[mid,rear])):
        for i in range(8):
            j=(i+1)%8
            q=orient([a[i],a[j],c[j],c[i]],(a[i]+a[j]+c[i]+c[j])/4-(a.mean(0)+c.mean(0))/2)
            if k==1 and i==4:face_with_pockets(b,q,[[[.16,.12],[.84,.12],[.84,.86],[.16,.86]]],.05,P,P,D)
            else:b.face(q,P)
    b.face(front,P,normal=[0,0,-1]);b.face(rear,P,normal=[0,0,1])
    add('Compact_lower_gondola_without_oversized_base',b,category='Lower gondola')
    b=B()
    outline=np.array([[1.05,-.95],[1.65,-1.08],[3.10,-.36],[3.25,.00],
                       [3.25,.55],[2.0,1.03],[1.05,.85]])
    top=lambda q:np.c_[q[:,0],-4.38-.055*(q[:,0]-1.05),q[:,1]]
    hole=[[1.57,-.62],[2.84,-.10],[2.84,.31],[1.57,.77]]
    ls=base.panel(b,outline,top,[.055,1,0],[hole]);inset(b,ls[1],top,[.055,1,0],.035,P,D)
    front=top(ls[0]);back=front.copy();back[:,1]-=.23
    base.ribbon(b,front,back,P);b.face(back,P,normal=[0,-1,0])
    pair('short_lower_wing',b,'bw_{side}_wingX02_lod1','Lower wings / static shape')


def main():
    free=shutil.disk_usage(base.ROOT).free;assert free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    selection=json.loads((base.TOPIC/'selection.json').read_text(encoding='utf8'))
    assert f.digest(PINNED)==selection['source_sha256']
    row=json.loads((base.reference.a.OUT/'ships/bw_elite_pir/source.json').read_text(encoding='utf8'))
    row['model']=PINNED.as_posix()
    scene,mats,stats=base.reference.a.source.load(row,pose=('Sc_extend wing',0))
    header,nodes=f.mesh.read_tree(PINNED.read_bytes());names={k.lower():v for k,v in f.component_map(nodes).items()}
    paths=[PINNED,base.MAT,base.ENV,base.TOPIC/'concepts/round_04/bw_family_B04_VIEWS_A_sheet.png',
           base.TOPIC/'concepts/round_04/bw_family_B04_VIEWS_B_sheet.png']
    pinned={p.as_posix():f.digest(p) for p in paths}
    base.OBJECTS.clear();copied=cockpit_and_native_owners(scene,names,mats)
    nose_and_cabin_surround();main_fuselage();roots();wings();engines();pyramidal_stand();lower_gondola()
    # Stabilize only new geometry at the export/editor welding precision.
    # Never touch native cockpit coordinates or UVs. Remove zero-area seam
    # fragments from collinear constraints, not any authored surface detail.
    for e in base.OBJECTS:
        if e['category'] in ('Immutable original cabin','Native rig helpers'):continue
        # Welding by proximity also joins values on opposite sides of a
        # decimal rounding boundary after the lower nozzle's anisotropic scale.
        raw=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in e['groups']])
        points,inverse=np.unique(np.round(np.round(raw,8),5),axis=0,return_inverse=True)
        parent=np.arange(len(points))
        def find(i):
            while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
            return i
        for a,c in cKDTree(points).query_pairs(1.6e-5):parent[find(c)]=find(a)
        snapped=points[[find(i) for i in inverse]];offset=0
        groups=[]
        for g in e['groups']:
            t=g['corners'];count=len(t)*3;t[...,:3]=snapped[offset:offset+count].reshape(-1,3,3);offset+=count
            area=np.linalg.norm(np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]),axis=1)
            if (area>1e-9).any():groups.append(dict(g,corners=t[area>1e-9]))
        e['groups']=groups
    world={}
    for e in base.OBJECTS:world.setdefault(e['owner'],[]).extend(e['groups'])
    world={n:f.merge(gs) for n,gs in world.items()};assert set(world)==set(names.values())
    used={g['material'] for gs in world.values() for g in gs}
    assert not any('metal' in (mats[m]['texture']+' '+mats[m]['name']).lower() for m in used)
    old=json.loads((base.OUT/'geometry.json').read_text(encoding='utf8'))
    materials={m:dict({k:v for k,v in mats[m].items() if k!='image'},image_path=old['materials'].get(str(m),{}).get('image_path')) for m in used}
    old_cabin={e['name']:e for e in old['objects'] if e['category']=='Immutable original cabin'}
    for e in base.OBJECTS:
        if e['name'] not in old_cabin:continue
        for a,c in zip(e['groups'],old_cabin[e['name']]['groups']):assert a['material']==c['material'] and np.array_equal(a['corners'],np.array(c['corners']))
    export=base.export(header,nodes,world,('Sc_extend wing',0),OUT/'bw_pir_elite_b04_review_open.cmp')
    vertices=np.concatenate([g['corners'][...,:3].reshape(-1,3) for e in base.OBJECTS for g in e['groups']])
    base.dump(OUT/'geometry.json',dict(sources=pinned,objects=base.OBJECTS,materials=materials,motion={},
        cargo_ray_probes=[([0,1.43,1.3],[0,-1,0]),([0,1.3,1.3],[1,0,0]),([0,1.3,1.3],[-1,0,0]),
                          ([0,1.3,1.3],[0,0,1]),([0,1.3,1.3],[0,0,-1])]))
    manifest=dict(stage='static detailed upper-body form prototype, user review pending',revision='B04/03',
        reference_priority=['B04_VIEWS_B ELITE REAR and REAR 3/4','B04_VIEWS_A ELITE front and TOP'],sources=pinned,
        cockpit_exactly_preserved=True,cockpit_copied_indices=copied,free_disk_before_bytes=free,
        total_triangles=sum(len(g['corners']) for gs in world.values() for g in gs),dimensions=np.ptp(vertices,axis=0),export=export,
        animation_status='Deferred entirely at user request. Static flight pose only.',
        hardpoints_status='Native data retained as editing references; not fitted to changed form.',
        uv_status='Provisional native external references. Shape-review shading in Blender; full UV pass pending.',
        lower_support=dict(top_width=1.88,bottom_width=.84,top_length=3.45,bottom_length=1.44,height=3.13),
        no_game_writes=True,no_lods_sur_damage=True)
    base.dump(OUT/'manifest.json',manifest)
    print(json.dumps(dict(output=OUT.as_posix(),triangles=manifest['total_triangles']),indent=2))


if __name__=='__main__':main()
