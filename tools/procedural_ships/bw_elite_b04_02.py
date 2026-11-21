"""B04/02: form-first reconstruction of the selected ELITE, offline only.

The rejected first version is kept as a comparison. Its native rig helpers are
reused, not its shoulder / wing / keel / lower-pod geometry. This revision is a
static flight shape study; fitting the four sliders comes after shape review.
"""
import copy
import json
import shutil
from pathlib import Path

import numpy as np
import bw_elite_b04 as base

f=base.f
B=base.B
P,D,E,G=base.P,base.D,base.E,base.G
A=f.mesh.crc('pir_bw_panel_128')
OUT=base.TOPIC/'elite/prototypes/b04_02'
PINNED=base.TOPIC/'elite/source/bw_pir_elite_original.cmp'


def add(name,b,owner='Root',category='B04 shaped hull'):
    base.add(name,b,owner,category)


def mirrored(name,b,owner=None,category='B04 shaped hull'):
    for side,label in [(-1,'Port'),(1,'Starboard')]:
        semantic=owner.format(side='port' if side<0 else 'star') if owner else 'Root'
        add(label+'_'+name,base.mirror(b.groups(),side),semantic,category)


def face_field(b,q,holes=(),depth=.12,material=P,floor=D,walls=D):
    """A real inset in a planar quad, using its physical local basis."""
    q=np.array(q,float)
    normal=f.mesh.unit(np.cross(q[1]-q[0],q[3]-q[0]))
    def mapping(p):
        u,v=p[:,0,None],p[:,1,None]
        return (1-u)*(1-v)*q[0]+u*(1-v)*q[1]+u*v*q[2]+(1-u)*v*q[3]
    loops=base.panel(b,[[0,0],[1,0],[1,1],[0,1]],mapping,normal,holes,material)
    for loop in loops[1:]:base.recess(b,loop,mapping,normal,depth,floor,walls)
    return mapping,normal,loops


def closed_plate(b,outline,mapping,normal,thickness=.18,material=P):
    front=mapping(np.array(outline,float));n=f.mesh.unit(np.array(normal))
    back=front-n*thickness
    b.face(front,material,normal=normal)
    base.ribbon(b,front,back,material)
    b.face(back,material,normal=-n)


def clip_line(poly,normal,offset):
    """Clip our simple wing sections to a half plane without extra packages."""
    out=[];normal=np.array(normal)
    for a,c in zip(poly,np.roll(poly,-1,axis=0)):
        da=float(np.dot(a,normal)-offset);dc=float(np.dot(c,normal)-offset)
        if da>=-1e-8:out.append(a)
        if (da<0<dc) or (dc<0<da):out.append(a+(c-a)*(da/(da-dc)))
    cleaned=[]
    for p in out:
        if not cleaned or np.linalg.norm(p-cleaned[-1])>1e-7:cleaned.append(p)
    if len(cleaned)>1 and np.linalg.norm(cleaned[0]-cleaned[-1])<1e-7:cleaned.pop()
    return np.array(cleaned)


def inside(point,poly):
    x,y=point;odd=False
    for a,c in zip(poly,np.roll(poly,-1,axis=0)):
        if (a[1]>y)!=(c[1]>y) and x<(c[0]-a[0])*(y-a[1])/(c[1]-a[1])+a[0]:odd=not odd
    return odd


def simple_outline(poly):
    pts=list(np.asarray(poly))
    changed=True
    while changed and len(pts)>3:
        changed=False
        for i,p in enumerate(pts):
            a=p-pts[i-1];c=pts[(i+1)%len(pts)]-p
            if abs(a[0]*c[1]-a[1]*c[0])<1e-8:
                pts.pop(i);changed=True;break
    return np.array(pts)


def boundary_parameter(point,poly):
    result=(1e9,0);along=0
    for a,c in zip(poly,np.roll(poly,-1,axis=0)):
        edge=c-a;length=np.linalg.norm(edge)
        t=np.clip(np.dot(point-a,edge)/length**2,0,1)
        dist=np.linalg.norm(point-(a+t*edge))
        if dist<result[0]:result=(dist,along+t*length)
        along+=length
    return result


def nose():
    b=B()
    specs=[(-13.186,.055,-.19,-.03),(-10.75,.38,-.30,.08),
           (-8.15,.79,-.47,.30),(-5.461,1.70,-.74,.535)]
    rings=[base.octagon(z,w,lo,hi,min(.13,w*.25)) for z,w,lo,hi in specs]
    # Broad local planes: paired ducts beside a narrow centre spine near cabin.
    for k,(a,c) in enumerate(zip(rings,rings[1:])):
        for i in range(8):
            j=(i+1)%8
            q=np.array([a[i],a[j],c[j],c[i]])
            # Loft topological orientation; these rings run clockwise in XY.
            if np.dot(np.cross(q[1]-q[0],q[2]-q[0]),q.mean(0)-(a.mean(0)+c.mean(0))/2)<0:q=q[::-1]
            if i==0 and k==2:
                # Top ring order is reversed for the upward normal.
                holes=[[[.10,.09],[.39,.09],[.44,.89],[.08,.89]],
                       [[.61,.09],[.90,.09],[.92,.89],[.56,.89]]]
                mapping,n,loops=face_field(b,q,holes,.17)
                for loop in loops[1:]:
                    lo=loop.min(0);hi=loop.max(0)
                    for v in np.linspace(lo[1]+.05,hi[1]-.07,9):
                        # A thick, tilted vane; no bolts or rivet geometry.
                        u0=np.interp(v,[.09,.89],[loop[0,0],loop[-1,0]])
                        u1=np.interp(v,[.09,.89],[loop[1,0],loop[2,0]])
                        pp=np.array([[u0+.012,v],[u1-.012,v],[u1-.012,v+.025],[u0+.012,v+.025]])
                        closed_plate(b,pp,lambda p: mapping(p)-n*.065,n,.032,E)
            elif i in (2,6) and k==2:
                face_field(b,q,[[[.15,.12],[.86,.12],[.86,.78],[.20,.78]]],.11)
            elif i==0 and k==1:
                face_field(b,q,[[[.40,.25],[.60,.25],[.60,.78],[.40,.78]]],.07)
            else:b.face(q,P)
    b.face(rings[0],E,normal=[0,0,-1]);b.face(rings[-1],P,normal=[0,0,1])
    add('Spear_nose_paired_intakes',b)
    # Keep exactly the native seat construction; original cabin is unchanged.
    old_count=len(base.OBJECTS)
    base.nose_and_cabin_seat()
    base.OBJECTS[old_count:]=[e for e in base.OBJECTS[old_count:] if e['name']=='Canopy_seat_and_forward_belly']


def body():
    b=B()
    rings=[base.octagon(-1.45,1.17,-.74,.54,.12),
           base.octagon(.20,1.70,-.82,1.46,.16),
           base.octagon(2.60,1.70,-.82,1.46,.16),
           base.octagon(5.40,1.42,-.65,1.30,.16)]
    for k,(a,c) in enumerate(zip(rings,rings[1:])):
        for i in range(1,8):
            j=(i+1)%8;q=np.array([a[i],a[j],c[j],c[i]])
            normal=np.cross(q[1]-q[0],q[2]-q[0])
            if normal.dot(q.mean(0)-(a.mean(0)+c.mean(0))/2)<0:q=q[::-1]
            if k==2 and i in (2,6):
                mapping,n,loops=face_field(b,q,[[[.12,.10],[.88,.10],[.88,.86],[.12,.86]]],.20)
                # Deep rear cheek intake with long sloping blades, like B04 rear.
                for v in np.linspace(.15,.79,11):
                    pp=[[.17,v],[.83,v+.045],[.83,v+.075],[.17,v+.030]]
                    closed_plate(b,pp,lambda p:mapping(p)-n*.055,n,.075,E)
            else:b.face(q,P)
    b.face(rings[0],P,normal=[0,0,-1]);b.face(rings[-1],P,normal=[0,0,1])
    # Rear shell under the source cabin and shoulders; no side slabs beside glass.
    b.face([[-1.05,.54,-1.45],[1.05,.54,-1.45],[1.54,1.46,.2],[-1.54,1.46,.2]],P,normal=[0,1,-1])
    outer=[[-1.54,.2],[1.54,.2],[1.54,2.6],[1.26,5.4],[-1.26,5.4],[-1.54,2.6]]
    opening=[[-.82,.83],[.79,.83],[.79,4.43],[-.82,4.43]]
    def roof(q):return np.c_[q[:,0],1.46-np.maximum(q[:,1]-2.6,0)*(.16/2.8),q[:,1]]
    # Separate horizontal hold deck from the shallow falling stern deck.
    # The native doors are still the original size; the hold is kept below them.
    # A flat deck is intentional, with a short tapered rear return at the nozzle.
    roof=lambda q:np.c_[q[:,0],np.full(len(q),1.46),q[:,1]]
    ls=base.panel(b,outer,roof,[0,1,0],[opening])
    base.recess(b,ls[1],roof,[0,1,0],.70,D,D)
    # Seal the little 0.16-high rise between deck and rear cheek roof.
    for s in [-1,1]:
        b.face([[s*1.54,1.46,2.6],[s*1.26,1.46,5.4],
                [s*1.26,1.30,5.4]],P,normal=[s,.3,0])
    b.face([[-1.26,1.46,5.4],[1.26,1.46,5.4],[1.26,1.30,5.4],[-1.26,1.30,5.4]],P,normal=[0,0,1])
    add('Narrow_upper_spine_and_shallow_hold',b)
    # Two low service / weapon pads read as part of the spine, like the art.
    b=B()
    for x,z,w,l in [(-1.16,1.1,.32,.70),(.60,4.92,.55,.65)]:
        bottom=np.array([[x-w,1.465,z-l/2],[x+w,1.465,z-l/2],[x+w,1.465,z+l/2],[x-w,1.465,z+l/2]])
        top=bottom.copy();top[:,0]=x+(top[:,0]-x)*.82;top[:,2]=z+(top[:,2]-z)*.85;top[:,1]=1.65
        base.loft(b,[bottom,top],A)
    add('Integrated_spine_equipment_pads',b)


def stepped_roots():
    # The side elevation is the key: low approach, upper cap, inclined aft
    # buttress and the long inset intake underneath. Not a wide solid shoulder.
    b=B()
    profile=np.array([[-3.75,.14],[-2.18,.72],[-1.70,.94],[2.66,.94],
                      [3.55,-.06],[3.90,-.25],[3.12,-.43],[-2.12,-.43]])
    cavity=[[-1.65,.04],[2.61,.04],[2.22,.61],[-1.42,.61]]
    def outer(q):return np.c_[np.full(len(q),2.63),q[:,1],q[:,0]]
    n=[1,0,0]
    ls=base.panel(b,profile,outer,n,[cavity])
    base.recess(b,ls[1],outer,n,.26,D,D)
    # Continuous, tilted intake floor and a single internal rail, tucked inside.
    pp=[[-1.40,.12],[2.35,.12],[2.21,.19],[-1.4,.19]]
    closed_plate(b,pp,lambda q:outer(q)-[.16,0,0],n,.035,E)
    right=outer(ls[0]);inner=right.copy();inner[:,0]=1.55
    # Inner roof rises gently to the central spine, while the forward slope
    # stays below the unchanged cockpit's side windows.
    inner[:,1]+=np.array([-.05,.0,.17,.17,.12,.0,.0,.0])
    base.ribbon(b,right,inner,P)
    b.face(inner,P,normal=[-1,0,0])
    mirrored('stepped_root_upper_cap_and_intake',b)
    # Lower terrace joins directly to the broad flight wing; one body, no gap.
    b=B()
    q=np.array([[1.53,-3.78],[2.04,-3.30],[3.10,-2.75],[3.10,3.65],[2.25,4.05],[1.52,3.4]])
    def deck(p):return np.c_[p[:,0],-.24-.055*(p[:,0]-2.63),p[:,1]]
    closed_plate(b,q,deck,[.055,1,0],.24)
    mirrored('root_lower_terrace',b)
    b=B()
    # Continuous skin over the short taper between the unchanged cabin's rear
    # shell and the new inner root. Close the unintended triangular roof wells.
    b.face([[1.32,.534,-1.70],[1.55,1.11,-1.70],
            [1.55,1.11,-1.45],[1.05,.54,-1.45]],P,normal=[0,1,0])
    b.face([[1.05,.54,-1.45],[1.55,1.11,-1.45],
            [1.55,1.11,-.30],[1.38,1.181,-.30]],P,normal=[0,1,0])
    mirrored('joined_cabin_to_root_skin',b)


WING=np.array([[2.63,-2.78],[3.30,-3.17],[6.74,-1.77],[7.05,-1.98],
               [7.05,.63],[5.46,1.18],[5.46,2.31],[3.96,2.72],
               [3.96,3.55],[2.63,3.92]])


def flight_wings():
    b=B()
    def leading(x):return -3.17+(x-3.30)*(1.40/3.44)
    def upper(q):
        rise=np.clip((q[:,1]-leading(q[:,0]))/.42,0,1)*.11
        return np.c_[q[:,0],-.24-.055*(q[:,0]-2.63)+rise,q[:,1]]
    normal=[.055,1,0]
    duct=[[3.13,-1.95],[3.63,-1.74],[3.63,2.76],[3.13,2.96]]
    groove=[[4.03,1.85],[5.13,1.47],[5.13,1.59],[4.03,1.98]]
    regions=[WING]
    # Partition at the authored change-of-section lines. Thus the raised
    # leading plane replaces the base skin instead of overlapping another face.
    for n,c in [(np.array([-1.4/3.44,1]),leading(0)),
                (np.array([-1.4/3.44,1]),leading(0)+.42),(np.array([1,0]),6.72)]:
        next_regions=[]
        for poly in regions:
            for sign in [-1,1]:
                cut=clip_line(poly,n*sign,c*sign)
                if len(cut)>=3 and abs(np.sum(cut[:,0]*np.roll(cut[:,1],-1)-cut[:,1]*np.roll(cut[:,0],-1)))>1e-7:
                    next_regions.append(cut)
        regions=next_regions
    outer_points={tuple(p) for p in WING}
    for region in regions:
        for p in region:
            if boundary_parameter(p,WING)[0]<1e-7:outer_points.add(tuple(np.round(p,8)))
        holes=[h for h in [duct,groove] if inside(np.mean(h,axis=0),region)]
        mat=A if region.mean(0)[0]>6.72 else P
        base.panel(b,simple_outline(region),upper,normal,holes,mat)
    ordered=np.array(sorted(outer_points,key=lambda p:boundary_parameter(np.array(p),WING)[1]))
    front=upper(ordered);back=front.copy()
    back[:,1]=-.24-.055*(back[:,0]-2.63)-.24
    base.ribbon(b,front,back,P);b.face(back,P,normal=[0,-1,0])
    base.recess(b,duct,upper,normal,.19,D,D)
    base.recess(b,groove,upper,normal,.07,D,D)
    # Two wide longitudinal lips inside the long wing duct: continuous strip.
    for x0 in [3.23,3.43]:
        q=[[x0,-1.76],[x0+.055,-1.74],[x0+.055,2.65],[x0,2.68]]
        closed_plate(b,q,lambda p:upper(p)-[0,.10,0],normal,.045,E)
    mirrored('broad_stepped_upper_wing',b,'bw_{side}_wingX01_lod1','Flight wings / motion pending')


def keel():
    b=B()
    outline=np.array([[-3.47,-.71],[3.12,-.71],[2.92,-1.18],
                      [1.12,-4.58],[1.12,-4.98],[-1.65,-4.98],[-1.65,-4.58],[-3.23,-1.18]])
    hole=[[-2.23,-1.53],[2.07,-1.53],[.74,-4.21],[-.95,-4.21]]
    def side(q):return np.c_[.85+(q[:,1]+4.98)*.178,q[:,1],q[:,0]]
    n=[1,-.178,0]
    ls=base.panel(b,outline,side,n,[hole]);base.recess(b,ls[1],side,n,.18,D,D)
    # The art has an angular inset within the web; two connected sloping
    # facets, rather than the rejected pair of rectangular decorative slabs.
    inset=np.array([[-1.98,-1.75],[1.70,-1.75],[.59,-3.97],[-.74,-3.97]])
    nn=f.mesh.unit(np.array(n));p=side(inset)-nn*.12
    mid=(p[0]+p[1])/2;mid[1]-=.7;mid-=nn*.07
    b.face([p[0],p[1],mid],E,normal=n)
    b.face([p[1],p[2],p[3],mid],P,normal=n)
    b.face([p[3],p[0],mid],P,normal=n)
    base.ribbon(b,p,p-nn*.065,D)
    # Closed front/back/underside from one side to the other.
    rr=side(ls[0]);ll=rr.copy();ll[:,0]*=-1
    for i in range(len(rr)):
        j=(i+1)%len(rr)
        q=np.array([rr[i],rr[j],ll[j],ll[i]])
        expected=(rr[i]+rr[j]+ll[i]+ll[j])/4-(rr.mean(0)+ll.mean(0))/2
        if np.dot(np.cross(q[1]-q[0],q[2]-q[0]),expected)<0:q=q[::-1]
        if i in (2,6):
            # Broad front/rear skin is authored too: two stepped fields visible
            # in the accepted rear sheet, not an entirely blank trapezoid.
            holes=[[[.14,.18],[.47,.18],[.47,.82],[.14,.82]],
                   [[.53,.18],[.86,.18],[.86,.82],[.53,.82]]]
            face_field(b,q,holes,.11,P,P,D)
        else:b.face(q,P)
    add('Central_keel_starboard',b)
    # Mirror only the broad skin and inset, not the cross-hull closure faces.
    other=B();ls2=base.panel(other,outline,side,n,[hole]);base.recess(other,ls2[1],side,n,.18,D,D)
    for q,mat in [([p[0],p[1],mid],E),([p[1],p[2],p[3],mid],P),([p[3],p[0],mid],P)]:other.face(q,mat,normal=n)
    base.ribbon(other,p,p-nn*.065,D)
    add('Central_keel_port',base.mirror(other.groups(),-1))
    # Low, broad foot merges into the gondola instead of stacking wing saddles.
    b=B()
    def foot(y,w,z0,z1):return np.array([[-w,y,z0],[w,y,z0],[w,y,z1],[-w,y,z1]])
    base.loft(b,[foot(-4.63,.89,-1.70,1.15),foot(-5.12,1.12,-1.93,1.33)],P)
    add('Keel_foot_into_lower_pod',b)


def lower_pod():
    b=B()
    rings=[base.octagon(-3.12,.73,-6.22,-5.52,.20),
           base.octagon(-2.42,1.46,-6.65,-5.03,.32),
           base.octagon(.10,1.46,-6.65,-5.03,.32)]
    base.loft(b,rings,P)
    # Side facets define a compact housing. The lower wings emerge from its
    # middle thickness; there is only one wing per side and no support shelves.
    add('Compact_integrated_lower_gondola',b)
    b=B()
    outline=[[1.20,-2.20],[1.72,-2.32],[3.32,-1.52],[3.50,-.96],
             [3.50,-.23],[2.15,.45],[1.20,.33]]
    def top(q):return np.c_[q[:,0],-5.62-.06*(q[:,0]-1.20),q[:,1]]
    closed_plate(b,outline,top,[.06,1,0],.24)
    cap=[[3.12,-1.62],[3.50,-.96],[3.50,-.23],[3.12,-.08]]
    closed_plate(b,cap,lambda q:top(q)+[0,.014,0],[.06,1,0],.26,A)
    mirrored('lower_short_wing',b,'bw_{side}_wingX02_lod1','Flight wings / motion pending')


def engine(lower=False):
    b=B();y=-5.77 if lower else .23;z=.10 if lower else 5.40
    w=1.46 if lower else 1.42;h=.84 if lower else 1.07
    front=base.octagon(z,w,y-h,y+h,.23)
    aft=base.octagon(z+.76,w-.09,y-h+.12,y+h-.12,.19)
    base.loft(b,[front,aft],P,caps=False)
    b.face(front,P,normal=[0,0,-1])
    # Squared nozzle set into its housing, with a single strong outer lip.
    outer=base.octagon(z+.79,w-.16,y-h+.20,y+h-.20,.14)
    inner=base.octagon(z+.81,w-.29,y-h+.32,y+h-.32,.09)
    deep=inner.copy();deep[:,2]=z+.39
    base.ribbon(b,aft,outer,A,face_normal=[0,0,1])
    base.ribbon(b,outer,inner,E,face_normal=[0,0,1])
    base.ribbon(b,inner,deep,D,True);b.face(deep,G,(0,0,1,1),[0,0,1])
    for x in np.linspace(-w+.39,w-.39,13):
        q=[[[x-.025,y-h+.41,z+.40],[x+.025,y-h+.41,z+.40],
             [x+.025,y+h-.41,z+.40],[x-.025,y+h-.41,z+.40]],
           [[x-.025,y-h+.41,z+.69],[x+.025,y-h+.41,z+.69],
             [x+.025,y+h-.41,z+.69],[x-.025,y+h-.41,z+.69]]]
        base.loft(b,q,E)
    add('Lower_engine' if lower else 'Upper_engine',b,
        'bw_eng02_lod1' if lower else 'bw_eng01_lod1','Two rectangular engines')


def main():
    free=shutil.disk_usage(base.ROOT).free
    assert free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    selection=json.loads((base.TOPIC/'selection.json').read_text(encoding='utf8'))
    assert f.digest(PINNED)==selection['source_sha256']
    row=json.loads((base.reference.a.OUT/'ships/bw_elite_pir/source.json').read_text(encoding='utf8'))
    row['model']=PINNED.as_posix()
    scene,mats,stats=base.reference.a.source.load(row,pose=('Sc_extend wing',0))
    header,nodes=f.mesh.read_tree(PINNED.read_bytes())
    names={k.lower():v for k,v in f.component_map(nodes).items()}
    pinned={p.as_posix():f.digest(p) for p in [PINNED,base.MAT,base.ENV,
              base.TOPIC/selection['art'],base.TOPIC/selection['rear_view']['art']]}
    base.OBJECTS.clear();copied=base.native_parts(scene,names,mats)
    base.OBJECTS[:]=[e for e in base.OBJECTS if e['category']!='Pocket inner walls']
    for e in base.OBJECTS:
        if e['owner'].startswith('baydoor'):
            for g in e['groups']:g['corners'][...,1]-=.035
    tiny=B();tiny.face([[0,-.5,2],[.01,-.5,2],[0,-.49,2]],D)
    add('boards_semantic_placeholder',tiny,'bw_boards_lod1','Native rig helpers')
    nose();body();stepped_roots();flight_wings();keel();lower_pod();engine();engine(True)
    world={}
    for e in base.OBJECTS:world.setdefault(e['owner'],[]).extend(e['groups'])
    world={n:f.merge(gs) for n,gs in world.items()}
    assert set(world)==set(names.values())
    used={g['material'] for gs in world.values() for g in gs}
    assert not any('metal' in (mats[m]['texture']+' '+mats[m]['name']).lower() for m in used)
    # Do not duplicate native authoring PNGs. They remain in the first revision.
    old=json.loads((base.OUT/'geometry.json').read_text(encoding='utf8'))['materials']
    materials={}
    for m in used:
        materials[m]={k:v for k,v in mats[m].items() if k!='image'}
        materials[m]['image_path']=old.get(str(m),{}).get('image_path')
    outcmp=OUT/'bw_pir_elite_b04_review_open.cmp'
    export=base.export(header,nodes,world,('Sc_extend wing',0),outcmp)
    _,written=f.mesh.read_tree(outcmp.read_bytes())
    def hp_data(tree):
        owner={k.lower():v for k,v in f.component_map(tree).items()}
        return {owner[p.split('/')[2].lower()]+'/'+p.lower().split('/hardpoints/')[-1]:n.blob
                for p,n in f.mesh.walk(tree) if '/hardpoints/' in p.lower()}
    assert hp_data(nodes)==hp_data(written)
    # Verify copied cabin data have not passed through transform/shape editing.
    oldcab={e['name']:e for e in json.loads((base.OUT/'geometry.json').read_text(encoding='utf8'))['objects']
            if e['category']=='Immutable original cabin'}
    for e in base.OBJECTS:
        if e['name'] not in oldcab:continue
        for a,c in zip(e['groups'],oldcab[e['name']]['groups']):
            assert a['material']==c['material'] and np.array_equal(a['corners'],np.array(c['corners']))
    vertices=np.concatenate([g['corners'][...,:3].reshape(-1,3) for e in base.OBJECTS for g in e['groups']])
    base.dump(OUT/'geometry.json',dict(sources=pinned,objects=base.OBJECTS,materials=materials,
        motion={},cargo_ray_probes=[([0,1.38,2.5],[0,-1,0]),([0,1.1,2.5],[1,0,0]),
        ([0,1.1,2.5],[-1,0,0]),([0,1.1,2.5],[0,0,1]),([0,1.1,2.5],[0,0,-1])]))
    base.dump(OUT/'manifest.json',dict(stage='unapproved second static shape prototype',concept='B04 / ELITE',
        sources=pinned,free_disk_before_bytes=free,cockpit_copied_indices=copied,cockpit_exactly_preserved=True,
        all_native_hardpoint_leaves_identical=True,
        total_triangles=sum(sum(len(g['corners']) for g in gs) for gs in world.values()),
        dimensions=np.ptp(vertices,axis=0),export=export,
        animation_status='Intentionally static flight shape study. Native original rig remains pinned; fit travel after review.',
        hardpoints_status='Native names/ownership retained for editing. Final fitting to new wing shape is pending.',
        uv_status='Temporary native external material references; clay review is authoritative.',
        no_game_writes=True,prior_revision='b04_01 rejected by user: form does not read as selected B04'))
    print(json.dumps(dict(output=OUT.as_posix(),triangles=sum(len(g['corners']) for gs in world.values() for g in gs)),indent=2))


if __name__=='__main__':main()
