"""B04/04: crowned hull volumes, swept wings and a broad wedge nose.

REAR remains the master reference, including the FIGHTER row's upper-body
construction. Static form only; no equipment pylons, rig fitting or deployment.
"""
import copy
import json
import math
import shutil
from collections import defaultdict

import numpy as np
from scipy.spatial import cKDTree

import bw_elite_b04 as base
import bw_elite_b04_02 as geom
import bw_elite_b04_03 as prev

B, f = base.B, base.f
P, D, E, G, A = prev.P, prev.D, prev.E, prev.G, prev.A
OUT = base.TOPIC / 'elite/prototypes/b04_04'
PINNED = prev.PINNED


def ease(a, b, v):
    t = np.clip((v-a)/(b-a), 0, 1)
    return t*t*(3-2*t)


def upper_volume(points):
    """Real continuous displacement of roof/cheeks, then aft convergence."""
    p = np.array(points, float, copy=True)
    x, y, z = p.T
    ax = abs(x)
    length = np.sin(np.pi*np.clip((z+1.45)/7.42, 0, 1))**2
    roof = .24*length*np.exp(-(ax/1.65)**4)*ease(.25, 1.40, y)
    side = .18*length*np.exp(-((ax-1.45)/.67)**2)*(1-ease(2.7, 3.15, ax))
    belly = -.10*length*np.exp(-(ax/1.8)**4)*(1-ease(-.7, -.10, y))
    p[:, 0] += np.sign(x)*side
    p[:, 1] += roof+belly
    # User's marked upper/lower lines converge towards the exhaust mouth.
    taper = ease(2.75, 5.98, z)*np.exp(-(ax/2.7)**8)
    p[:, 0] *= 1-.12*taper
    p[:, 1] = .43+(p[:, 1]-.43)*(1-.22*taper)
    return p


def nose_volume(points):
    p = np.array(points, float, copy=True)
    x, y, z = p.T.copy()
    width = np.interp(z, [-11.80,-10.0,-7.67,-5.461], [.27,.62,1.06,1.70])
    # Broad nose panels have a restrained crown; the original cabin is excluded.
    p[:, 1] += .055*np.clip(1-(x/width)**2, 0, 1)*ease(-11.8,-8,z)*(1-ease(-6,-5.461,z))*ease(-.12,.25,y)
    return p


WING = np.array([[1.64,-4.85],[2.48,-4.66],[5.10,-2.09],[7.10,-.20],
                 [7.10,1.38],[6.60,1.56],[5.58,1.86],[5.58,2.60],
                 [4.16,3.09],[4.16,3.65],[2.66,4.10],[1.64,2.90]])


def wing_volume(points):
    p = np.array(points, float, copy=True)
    x, y, z = p.T.copy(); ax = abs(x)
    t = np.clip((ax-1.92)/(7.10-1.92), 0, 1)
    leading = np.interp(ax, [1.92,2.48,5.10,7.10], [-4.85,-4.66,-2.09,-.20])
    trailing = np.interp(ax, [1.92,2.66,4.16,5.58,6.60,7.10], [2.8,4.10,3.65,2.60,1.56,1.38])
    chord = np.clip((z-leading)/np.maximum(.4,trailing-leading), 0, 1)
    camber = .33*np.sin(np.pi*chord)**1.35*(1-.55*t)
    thickness_weight = .25+.75*ease(-.26, .08, y)
    p[:, 1] += .13*(1-t)-.13*t+camber*thickness_weight
    return upper_volume(p)


def stand_volume(points):
    p = np.array(points, float, copy=True)
    x,y,z = p.T.copy()
    down = np.clip((-.65-y)/3.13,0,1)
    oldfront = -.65+.85*down
    oldback = 2.80-1.16*down
    t = np.clip((z-oldfront)/(oldback-oldfront), 0, 1)
    p[:, 2] -= .85*down*(1-t)
    # Bury the attachment cap above the belly's shallow recessed floors.
    # Its previous height was almost coplanar with one inset backing panel.
    p[:, 1] += .16*(1-down)
    return p


def lower_volume(points):
    p = np.array(points, float, copy=True)
    x,y,z = p.T.copy()
    p[:,1] += .10*np.exp(-(x/1.5)**4)*np.sin(np.pi*np.clip((z+1.57)/3.8,0,1))*ease(-4.6,-3.8,y)
    taper = ease(.95,2.16,z)
    p[:,0] *= 1-.08*taper
    p[:,1] = -4.45+(p[:,1]+4.45)*(1-.12*taper)
    return p


def roots():
    # Keep the closed attachment skins; replace the flat heavy shoulder cap.
    prev.roots()
    base.OBJECTS[:] = [o for o in base.OBJECTS if 'stepped_shoulders' not in o['name']]
    b=B()
    profile=np.array([[-2.58,.28],[-2.26,.43],[-1.88,.68],[-1.60,.86],
                      [-1.25,1.02],[-.3,1.16],[1.2,1.16],[2.10,1.04],
                      [2.40,.92],[2.65,.70],[2.87,.42],[3.12,.19],
                      [3.64,.08],[3.64,-.20],[-2.16,-.20]])
    cavity=[[-1.36,.10],[2.58,.10],[2.18,.71],[-1.23,.71]]
    outer=lambda q:np.c_[np.full(len(q),2.76),q[:,1],q[:,0]]
    loops=base.panel(b,profile,outer,[1,0,0],[cavity])
    prev.inset(b,loops[1],outer,[1,0,0],.33,D,D)
    for yy in [.19,.43]:
        geom.closed_plate(b,[[-1.20,yy],[2.12,yy],[2.04,yy+.055],[-1.20,yy+.055]],
                          lambda q:outer(q)-[.18,0,0],[1,0,0],.055,E)
    right=outer(loops[0]);left=right.copy()
    left[:,0]=1.70-.42*ease(-1.6,.1,left[:,2])
    left[:,1]+=.20*ease(.2,.85,left[:,1])
    for i in range(len(right)):
        j=(i+1)%len(right)
        q=prev.orient([right[i],right[j],left[j],left[i]],
            (right[i]+right[j]+left[j]+left[i])/4-(right.mean(0)+left.mean(0))/2)
        b.face(q,P)
    b.face(left,P,normal=[-1,0,0])
    prev.pair('crowned_shoulders_continuous_root_casing',b)


def nose():
    # Retain the original cabin seat and its surrounding lower cheeks.
    prev.nose_and_cabin_surround()
    base.OBJECTS[:]=[o for o in base.OBJECTS if o['name']!='Spear_nose_paired_intakes']
    b=B()
    specs=[(-11.80,.27,-.20,-.025),(-10.0,.62,-.38,.13),
           (-7.67,1.06,-.74,.34),(-5.461,1.70,-.74,.535)]
    rings=[base.octagon(z,w,lo,hi,min(.13,w*.25)) for z,w,lo,hi in specs]
    for k,(a,c) in enumerate(zip(rings,rings[1:])):
        for i in range(8):
            j=(i+1)%8
            q=prev.orient([a[i],a[j],c[j],c[i]],(a[i]+a[j]+c[j]+c[i])/4-(a.mean(0)+c.mean(0))/2)
            if i==0 and k==2:
                holes=[[[.10,.09],[.40,.09],[.44,.89],[.08,.89]],[[.60,.09],[.90,.09],[.92,.89],[.56,.89]]]
                mapping,n,loops=prev.face_with_pockets(b,q,holes,.17)
                for loop in loops[1:]:
                    lo=loop.min(0);hi=loop.max(0)
                    for v in np.linspace(lo[1]+.05,hi[1]-.07,8):
                        u0=np.interp(v,[.09,.89],[loop[0,0],loop[-1,0]])
                        u1=np.interp(v,[.09,.89],[loop[1,0],loop[2,0]])
                        pp=np.array([[u0+.012,v],[u1-.012,v],[u1-.012,v+.032],[u0+.012,v+.032]])
                        geom.closed_plate(b,pp,lambda p:mapping(p)-n*.065,n,.032,E)
            elif i in (2,6) and k==2:
                prev.face_with_pockets(b,q,[[[.15,.12],[.86,.12],[.86,.78],[.20,.78]]],.11)
            elif i==0 and k==1:
                prev.face_with_pockets(b,q,[[[.24,.22],[.76,.22],[.76,.78],[.24,.78]]],.04,P,P,D)
            else:b.face(q,P)
    b.face(rings[0],P,normal=[0,0,-1]);b.face(rings[-1],P,normal=[0,0,1])
    prev.add('Spear_nose_paired_intakes',b)


def wing():
    b=B(); top=lambda q:np.c_[q[:,0],np.full(len(q),.08),q[:,1]]
    bottom=lambda q:np.c_[q[:,0],np.full(len(q),-.26),q[:,1]]
    duct=[[3.12,-2.66],[3.88,-2.26],[3.88,2.36],[3.12,2.65]]
    spar=[[4.24,2.78],[5.27,2.44],[5.27,1.65],[6.80,1.24],
          [6.80,1.38],[5.47,1.80],[5.47,2.59],[4.27,2.95]]
    # Three large integrated skin fields rather than a flat rectangular paddle.
    fore=[[2.60,-4.20],[3.88,-2.94],[3.88,-2.58],[2.60,-3.76]]
    middle=[[4.18,-2.63],[5.23,-1.64],[5.23,1.31],[5.07,1.37],
            [5.07,2.08],[4.18,2.40]]
    outer=[[5.39,-1.49],[6.72,-.22],[6.72,.98],[5.39,1.32]]
    holes=[duct,spar,fore,middle,outer]
    loops=base.panel(b,WING,top,[0,1,0],holes)
    for i,poly in enumerate(loops[1:]):
        if i<2:prev.inset(b,poly,top,[0,1,0],.19 if i==0 else .09,D,D)
        else:
            # A shaped structural panel rises from an inset perimeter, with
            # the curvature added to its actual exported vertices below.
            prev.inset(b,poly,top,[0,1,0],.028,P,D)
    for x in [3.25,3.49,3.73]:
        geom.closed_plate(b,[[x,-2.29],[x+.065,-2.25],[x+.065,2.25],[x,2.29]],
                          lambda q:top(q)-[0,.09,0],[0,1,0],.045,E)
    lower=[[3.16,-2.63],[3.73,-2.29],[3.73,2.65],[3.16,2.87]]
    field=[[4.06,-2.78],[6.74,-.22],[6.74,.99],[5.08,1.45],
           [5.08,2.18],[4.06,2.52]]
    bl=base.panel(b,WING,bottom,[0,-1,0],[lower,field])
    prev.inset(b,bl[1],bottom,[0,-1,0],.055,D,D)
    prev.inset(b,bl[2],bottom,[0,-1,0],.025,P,D)
    # Both constrained planar triangulations may have added boundary points.
    boundary={tuple(np.round(p,8)) for loop in (loops[0],bl[0]) for p in loop}
    contour=np.array(sorted(boundary,key=lambda p:geom.boundary_parameter(np.array(p),WING)[1]))
    base.ribbon(b,top(contour),bottom(contour),P)
    prev.pair('swept_cambered_wing_with_stepped_spar',b,'bw_{side}_wingX01_lod1','Swept upper wings / static shape')


def rounded_rect(z,w,lo,hi,r):
    points=[]
    for cx,cy,start in [(w-r,hi-r,90),(w-r,lo+r,0),(-w+r,lo+r,-90),(-w+r,hi-r,-180)]:
        for angle in np.linspace(start,start-90,5):
            a=math.radians(angle);points.append([cx+r*math.cos(a),cy+r*math.sin(a),z])
    return np.array(points)


def nozzle():
    b=B();front=prev.cross_section(5.15,1.70,1.01);rear=prev.engine_ring(5.82)
    for i in range(8):
        j=(i+1)%8;q=prev.orient([front[i],front[j],rear[j],rear[i]],
            (front[i]+front[j]+rear[i]+rear[j])/4-(front.mean(0)+rear.mean(0))/2)
        if i in (2,6):
            mapping,n,_=prev.face_with_pockets(b,q,[[[.10,.12],[.90,.12],[.90,.88],[.10,.88]]],.085)
            prev.vanes(b,mapping,n,16,lo=.15,hi=.82,axis=0,margin=.18,thick=.024,depth=.025)
        elif i==0:
            mapping,n,_=prev.face_with_pockets(b,q,[[[.12,.15],[.88,.15],[.88,.82],[.12,.82]]],.075)
            prev.vanes(b,mapping,n,18,lo=.16,hi=.80,axis=0,margin=.21,thick=.023,depth=.025)
        else:b.face(q,P)
    b.face(front,P,normal=[0,0,-1])
    rim=rounded_rect(5.88,1.24,-.47,1.31,.27)
    # Connect the octagonal casing to the softened nozzle corners as a real
    # annular face, with no face underneath the exhaust aperture.
    pts,triangles,ls=base.planar_mesh(rear[:,:2],[rim[:,:2]])
    outer_count=len(ls[0]);world=np.c_[pts,np.r_[np.full(outer_count,5.82),np.full(len(pts)-outer_count,5.88)]]
    for ids in triangles:b.face(world[ids],P,normal=[0,0,1])
    # Recover the exact boundary constraints at the inner edge before the loft.
    # The ring has no collinear straight-edge subdivisions in this recipe.
    rings=[rim,rounded_rect(5.93,1.245,-.475,1.315,.255),
           rounded_rect(5.99,1.21,-.44,1.28,.23),
           rounded_rect(6.015,1.09,-.30,1.16,.16)]
    for a,c in zip(rings,rings[1:]):base.ribbon(b,a,c,P)
    inner=rings[-1];deep=inner.copy();deep[:,2]=5.48
    base.ribbon(b,inner,deep,D,True);b.face(deep,G,normal=[0,0,1])
    for x in np.linspace(-.94,.94,16):
        a=np.array([[x-.022,-.20,5.50],[x+.022,-.20,5.50],[x+.022,1.04,5.50],[x-.022,1.04,5.50]])
        c=a.copy();c[:,2]=5.84;base.loft(b,[a,c],E)
    return b


def engines():
    b=nozzle();prev.add('Upper_tapered_exhaust_soft_corner_rim',b,'bw_eng01_lod1','Two exhausts / authored casing')
    groups=copy.deepcopy(b.groups())
    for g in groups:
        p=g['corners'][...,:3];p[...,0]*=.75;p[...,1]=(p[...,1]-.45)*.64-4.45;p[...,2]=(p[...,2]-5.15)*.85+1.45
        n=g['corners'][...,3:6];n/=np.array([.75,.64,.85]);n/=np.linalg.norm(n,axis=-1,keepdims=True)
    prev.add('Lower_tapered_exhaust_soft_corner_rim',groups,'bw_eng02_lod1','Two exhausts / authored casing')


def subdivide_for_volume(groups,warp,tolerance=.009):
    """Conforming adaptive edge splits driven by actual surface curvature."""
    groups=copy.deepcopy(groups)
    def edge_key(a,b):return tuple(sorted((tuple(np.round(a[:3],6)),tuple(np.round(b[:3],6)))))
    for iteration in range(9):
        marked=set()
        for g in groups:
            t=g['corners'];p=t[...,:3];q=warp(p.reshape(-1,3)).reshape(-1,3,3)
            mid=(p+np.roll(p,-1,axis=1))*.5
            error=np.linalg.norm(warp(mid.reshape(-1,3)).reshape(-1,3,3)-(q+np.roll(q,-1,axis=1))*.5,axis=2)
            for row,edge in np.argwhere(error>tolerance):marked.add(edge_key(t[row,edge],t[row,(edge+1)%3]))
            center_error=np.linalg.norm(warp(p.mean(1))-q.mean(1),axis=1)
            for row in np.flatnonzero((center_error>tolerance)&(error.max(1)<=tolerance)):
                j=int(np.argmax(np.linalg.norm(p[row]-np.roll(p[row],-1,axis=0),axis=1)))
                marked.add(edge_key(t[row,j],t[row,(j+1)%3]))
        if not marked:break
        for g in groups:
            out=[]
            for t in g['corners']:
                mask=[edge_key(t[i],t[(i+1)%3]) in marked for i in range(3)]
                total=sum(mask)
                if not total:out.append(t);continue
                mids=(t+np.roll(t,-1,axis=0))*.5
                if total==3:
                    out.extend([[t[0],mids[0],mids[2]],[mids[0],t[1],mids[1]],
                                [mids[2],mids[1],t[2]],[mids[0],mids[1],mids[2]]])
                elif total==1:
                    i=mask.index(True);j=(i+1)%3;k=(i+2)%3
                    out.extend([[t[i],mids[i],t[k]],[mids[i],t[j],t[k]]])
                else:
                    k=mask.index(False);a=(k+1)%3;c=(k+2)%3
                    out.extend([[t[c],mids[c],mids[a]],[t[a],mids[a],t[k]],[mids[a],mids[c],t[k]]])
            g['corners']=np.array(out)
    for g in groups:
        t=g['corners'];t[...,:3]=warp(t[...,:3].reshape(-1,3)).reshape(-1,3,3)
        n=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-30)
        t[...,3:6]=n[:,None,:]
    return groups


def weld_and_normals(groups,angle=34):
    """Weld only numerical seam residues; smooth only shallow adjoining angles."""
    raw=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in groups])
    points,inverse=np.unique(np.round(raw,5),axis=0,return_inverse=True);parent=np.arange(len(points))
    def find(i):
        while parent[i]!=i:parent[i]=parent[parent[i]];i=parent[i]
        return i
    for a,c in cKDTree(points).query_pairs(1.6e-5):parent[find(c)]=find(a)
    snapped=points[[find(i) for i in inverse]];offset=0;clean=[]
    for g in groups:
        t=g['corners'];count=len(t)*3;t[...,:3]=snapped[offset:offset+count].reshape(-1,3,3);offset+=count
        area=np.linalg.norm(np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]),axis=1)
        if (area>2e-8).any():clean.append(dict(g,corners=t[area>2e-8]))
    # Normal fans are split across sharp geometry edges, but not merely because
    # the native material changes. The same rule is used in the Blender review.
    lookup=defaultdict(list);alltris=np.concatenate([g['corners'] for g in clean])
    raw_n=np.cross(alltris[:,1,:3]-alltris[:,0,:3],alltris[:,2,:3]-alltris[:,0,:3])
    unit=raw_n/np.maximum(np.linalg.norm(raw_n,axis=1,keepdims=True),1e-30)
    for k,t in enumerate(alltris):
        for v in t:lookup[tuple(v[:3])].append(k)
    cutoff=math.cos(math.radians(angle));offset=0
    for g in clean:
        for k,t in enumerate(g['corners']):
            for v in t:
                ids=lookup[tuple(v[:3])];ids=[i for i in ids if np.dot(unit[i],unit[offset+k])>cutoff]
                n=raw_n[ids].sum(0);v[3:6]=n/np.linalg.norm(n)
        offset+=len(g['corners'])
    return clean


def main():
    free=shutil.disk_usage(base.ROOT).free;assert free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    sel=json.loads((base.TOPIC/'selection.json').read_text(encoding='utf8'));assert f.digest(PINNED)==sel['source_sha256']
    row=json.loads((base.reference.a.OUT/'ships/bw_elite_pir/source.json').read_text(encoding='utf8'));row['model']=PINNED.as_posix()
    scene,mats,_=base.reference.a.source.load(row,pose=('Sc_extend wing',0))
    header,nodes=f.mesh.read_tree(PINNED.read_bytes());names={k.lower():v for k,v in f.component_map(nodes).items()}
    paths=[PINNED,base.MAT,base.ENV,base.TOPIC/'concepts/round_04/bw_family_B04_VIEWS_A_sheet.png',base.TOPIC/'concepts/round_04/bw_family_B04_VIEWS_B_sheet.png']
    pinned={p.as_posix():f.digest(p) for p in paths}
    base.OBJECTS.clear();copied=prev.cockpit_and_native_owners(scene,names,mats)
    nose();prev.main_fuselage();roots();wing();engines();prev.pyramidal_stand();prev.lower_gondola()
    base.OBJECTS[:]=[o for o in base.OBJECTS if o['name']!='Low_integral_equipment_seats']
    for obj in base.OBJECTS:
        if obj['category'] in ('Immutable original cabin','Native rig helpers'):continue
        n=obj['name'].lower()
        if 'spear_nose' in n:warp=nose_volume
        elif 'swept_cambered_wing' in n:warp=wing_volume
        elif 'pyramid' in n:warp=stand_volume
        elif 'lower' in n and ('gondola' in n or 'wing' in n or 'exhaust' in n):warp=lower_volume
        else:warp=upper_volume
        obj['groups']=weld_and_normals(subdivide_for_volume(obj['groups'],warp))
        obj['smooth_angle_degrees']=34
    world={}
    for obj in base.OBJECTS:world.setdefault(obj['owner'],[]).extend(obj['groups'])
    world={n:f.merge(gs) for n,gs in world.items()};assert set(world)==set(names.values())
    used={g['material'] for gs in world.values() for g in gs}
    assert not any('metal' in (mats[m]['texture']+' '+mats[m]['name']).lower() for m in used)
    old=json.loads((base.OUT/'geometry.json').read_text(encoding='utf8'))
    materials={m:dict({k:v for k,v in mats[m].items() if k!='image'},image_path=old['materials'].get(str(m),{}).get('image_path')) for m in used}
    original={e['name']:e for e in old['objects'] if e['category']=='Immutable original cabin'}
    for obj in base.OBJECTS:
        if obj['name'] not in original:continue
        for a,c in zip(obj['groups'],original[obj['name']]['groups']):assert a['material']==c['material'] and np.array_equal(a['corners'],np.array(c['corners']))
    export=base.export(header,nodes,world,('Sc_extend wing',0),OUT/'bw_pir_elite_b04_review_open.cmp')
    verts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for gs in world.values() for g in gs])
    probes=[([0,1.55,1.3],[0,-1,0]),([0,1.50,1.3],[1,0,0]),([0,1.50,1.3],[-1,0,0]),([0,1.50,1.3],[0,0,1]),([0,1.50,1.3],[0,0,-1])]
    base.dump(OUT/'geometry.json',dict(sources=pinned,objects=base.OBJECTS,materials=materials,motion={},cargo_ray_probes=probes))
    manifest=dict(stage='static volume and swept-wing prototype, user review pending',revision='B04/04',sources=pinned,
        reference_priority=['B04_VIEWS_B ELITE REAR','B04_VIEWS_B FIGHTER upper hull and BOTTOM wing sweep','B04_VIEWS_A cross-check'],
        cockpit_exactly_preserved=True,cockpit_copied_indices=copied,free_disk_before_bytes=free,
        total_triangles=sum(len(g['corners']) for gs in world.values() for g in gs),dimensions=np.ptp(verts,axis=0),export=export,
        equipment_pylons=False,animation_status='Deferred entirely; static shape only',
        hardpoints_status='Native references preserved, not fitted',uv_status='Provisional external native UVs; neutral form review',
        authored_changes=['Continuous convex roof and cheeks','Cambered swept wings','Broader shorter wedge nose with finite tip',
                          'Raised curved shoulders','Taper towards exhaust with softly profiled rim','Straight forward face of narrow stand'],
        no_game_writes=True,no_lods_sur_damage=True)
    base.dump(OUT/'manifest.json',manifest)
    print(json.dumps(dict(output=OUT.as_posix(),triangles=manifest['total_triangles'])))


if __name__=='__main__':main()
