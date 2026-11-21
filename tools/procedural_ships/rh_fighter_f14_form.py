"""F14/R02 first offline form prototype; native cabin, lowered fixed drum.

Only writes out/ship_design/rh_fighter/prototypes/f14_01. No installation,
animation replacement, distant LODs, damage or SUR generation.
"""
import copy
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import struct

import numpy as np
from scipy.spatial import ConvexHull

import rh_freighter_q13 as q

f = q.f
B = q.B
ROOT = Path(__file__).resolve().parents[2]
TOPIC = ROOT / 'out/ship_design/rh_fighter'
OUT = TOPIC / 'prototypes/f14_01'
SOURCE = Path('D:/Games/FL_MOD/DATA/ships/rheinland/rh_pir_fighter/rh_pir_fighter.cmp')
MAT = SOURCE.parent.parent / 'rh_pir_playerships.mat'
ENV = SOURCE.parents[3] / 'fx/envmapbasic.mat'
P, R, D = q.P, q.R, q.D
P3 = f.mesh.crc('pir_r_panel03_256')
DARK = f.mesh.crc('pir_r-dark gray')
PLAIN, RED, FRAME = q.PLAIN, q.RED, q.FRAME
RADIUS = 2.355825
DECK_Y = 1.55
DRUM_Y = DECK_Y + .20 * RADIUS
DRUM_FRONT, DRUM_REAR = 2.25, 3.65
ENGINE_X = RADIUS * .77
ENGINE_Y = DRUM_Y - RADIUS * .88
OBJECTS = []


def dump(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2,
                    default=lambda a: a.tolist() if isinstance(a, np.ndarray) else float(a)), encoding='utf8')


def add(name, groups, category='hull', closed=True):
    gs = groups.groups() if isinstance(groups, B) else groups
    assert gs and all(np.isfinite(g['corners']).all() for g in gs)
    OBJECTS.append(dict(name=name, groups=gs, category=category, authored_closed=closed))


def plane_points(poly, axis, value):
    p = np.zeros((len(poly), 3))
    p[:, axis] = value
    axes = [2, 1] if axis == 0 else [i for i in range(3) if i != axis]
    p[:, axes] = np.asarray(poly)
    return p


def panel(b, poly, axis, at, sign, material=P, holes=(), box=PLAIN):
    return b.panel(np.array(poly), axis, at, np.eye(3)[axis]*sign, material, box, holes=holes)


def connect(b, a, c, material=P, inner=False, box=FRAME):
    a, c = np.asarray(a), np.asarray(c)
    assert len(a) == len(c)
    center = np.concatenate([a, c]).mean(0)
    for i in range(len(a)):
        j = (i + 1) % len(a)
        ps = np.array([a[i], a[j], c[j], c[i]])
        n = ps.mean(0)-center
        if inner:
            n = -n
        b.face(ps, material, box, n)


def pocket(b, poly, axis, front, back, sign, floor_mat=D, wall_mat=D):
    a, c = plane_points(poly, axis, front), plane_points(poly, axis, back)
    connect(b, a, c, wall_mat, inner=True, box=PLAIN)
    panel(b, poly, axis, back, sign, floor_mat)


def solid(name, poly, axis, a, c, mat=P, category='hull'):
    b = B()
    aa, cc = plane_points(poly, axis, a), plane_points(poly, axis, c)
    connect(b, aa, cc, mat)
    panel(b, poly, axis, a, -1 if c>a else 1, mat)
    panel(b, poly, axis, c, 1 if c>a else -1, mat)
    add(name, b, category)


def top_y(z):
    return float(np.interp(z, [-4.15, -.40, 2.25, 3.05], [.72, 1.15, 1.55, 1.55]))


SIDE = np.array([[-4.15,.72],[-.40,1.15],[2.25,1.55],[2.60,.95],
                 [2.60,-1.55],[.50,-1.85],[-2.70,-1.95],[-4.15,-2.25]])
WELL = np.array([[-3.78,.24],[-.55,.63],[1.54,1.03],[1.99,.62],
                 [1.57,-.66],[-2.62,-1.25],[-3.50,-.94]])


def side_shell(s):
    b = B()
    loops = panel(b, SIDE, 0, s*1.35, s, P, holes=[WELL])
    # Complete inner wall: outside pocket and actual cargo wall are different faces.
    panel(b, loops[0], 0, s*.80, -s, D)
    connect(b, plane_points(loops[0],0,s*.80), plane_points(loops[0],0,s*1.35), P)
    well = loops[1]
    connect(b, plane_points(well,0,s*1.35), plane_points(well,0,s*1.105), D, inner=True)
    vents = []
    for i in range(3):
        z=.50+i*.29
        vents.append(np.array([[z,.19],[z+.15,.23],[z+.29,.70],[z+.14,.67]]))
    floors = panel(b, well, 0, s*1.105, s, D, holes=vents)
    for loop in floors[1:]:
        pocket(b, loop, 0, s*1.105, s*.96, s, DARK)
    add('Port_hull' if s<0 else 'Starboard_hull', b)


def neck():
    # Join the original cabin's rear envelope to the narrow ship body; solid sides,
    # not exposed spars. The native cabin vertices themselves are untouched.
    cabin=next(o for o in OBJECTS if o['name']=='Native_cabin')
    points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in cabin['groups']])
    section=np.unique(points[abs(points[:,2]+4.70)<1e-5].round(5),axis=0)
    front=section[ConvexHull(section[:,:2]).vertices]
    assert len(front)==4 and front[0,0]<0 and front[0,1]<-2
    rings=[front,np.array([[-1.35,-2.25,-4.15],[1.35,-2.25,-4.15],
                           [1.35,.72,-4.15],[-1.35,.72,-4.15]])]
    b=B(); connect(b,*rings,P)
    b.face(rings[0],D,PLAIN,[0,0,-1]);b.face(rings[1],D,PLAIN,[0,0,1])
    add('Cockpit_transition',b)


def body_decks():
    b=B()
    # Underside follows the large authored profile changes instead of decorative grids.
    for z0,z1,y0,y1 in [(-4.15,-2.70,-2.25,-1.95),(-2.70,.50,-1.95,-1.85),(.50,2.60,-1.85,-1.55)]:
        b.face([[-.80,y0,z0],[.80,y0,z0],[.80,y1,z1],[-.80,y1,z1]],P3,PLAIN,[0,-1,0])
    # Cargo floor and end walls; the aft volume is also the sliding-lid receiver.
    b.face([[-.80,-1.05,-4.15],[.80,-1.05,-4.15],[.80,-1.05,3.05],[-.80,-1.05,3.05]],D,PLAIN,[0,1,0])
    for z in (-4.15,3.05):
        y=top_y(z)
        b.face([[-.80,-1.05,z],[.80,-1.05,z],[.80,y,z],[-.80,y,z]],D,PLAIN,[0,0,1 if z<0 else -1])
    # Close the receiver's aft belly into the existing engine shoulders, tapering
    # upwards. This is continuous hull skin rather than a loose underside cap.
    a=np.array([[-1.35,-1.55,2.60],[1.35,-1.55,2.60],[1.35,.10,2.60],[-1.35,.10,2.60]])
    c=np.array([[-1.12,-.95,3.38],[1.12,-.95,3.38],[1.12,-.42,3.38],[-1.12,-.42,3.38]])
    connect(b,a,c,P)
    b.face(c,P3,PLAIN,[0,0,1])
    # Inner walls behind the side-shell terminus complete the cargo receiver.
    for s in (-1,1):
        b.face([[s*.80,-1.05,2.60],[s*.80,-1.05,3.05],
                [s*.80,1.46,3.05],[s*.80,1.46,2.60]],D,PLAIN,[-s,0,0])
    # Roof strips frame the original lid; no fixed surface across its opening.
    for s in (-1,1):
        for z0,z1 in [(-4.15,-3.94),(-3.94,-.40),(-.40,2.25)]:
            b.face([[s*.73,top_y(z0),z0],[s*1.35,top_y(z0),z0],
                    [s*1.35,top_y(z1),z1],[s*.73,top_y(z1),z1]],P,PLAIN,[0,1,0])
    for z0,z1 in [(-4.15,-3.94),(-.40,2.25)]:
        top=np.array([[-.73,top_y(z0),z0],[.73,top_y(z0),z0],
                      [.73,top_y(z1),z1],[-.73,top_y(z1),z1]])
        low=top.copy();low[:,1]-=.06
        b.face(top,P,PLAIN,[0,1,0]);b.face(low,D,PLAIN,[0,-1,0]);connect(b,low,top,P)
    # Roof-opening thickness stays outside the native sliding door envelope.
    for s in (-1,1):
        b.face([[s*.73,top_y(-3.94),-3.94],[s*.73,top_y(-.40),-.40],
                [s*.73,top_y(-.40)-.12,-.40],[s*.73,top_y(-3.94)-.12,-3.94]],D,PLAIN,[-s,0,0])
    add('Root',b,closed=False)


def clipped_rect(x0,x1,y0,y1,c=.08):
    return np.array([[x0+c,y0],[x1-c,y0],[x1,y0+c],[x1,y1-c],
                     [x1-c,y1],[x0+c,y1],[x0,y1-c],[x0,y0+c]])


def drum():
    b=B(); count=48; theta=np.arange(count)*2*np.pi/count
    def circle(radius):
        return np.column_stack([radius*np.cos(theta),DRUM_Y+radius*np.sin(theta)])
    def ring(r,z):
        return plane_points(circle(r),2,z)
    # Thin continuous lip, a structural depth, and one rear inset. No ornamental hubs.
    rings=[ring(RADIUS-.08,DRUM_FRONT),ring(RADIUS,DRUM_FRONT+.08),
           ring(RADIUS,DRUM_REAR-.08),ring(RADIUS-.08,DRUM_REAR)]
    for i in range(len(rings)-1):connect(b,rings[i],rings[i+1],R if i==1 else P)
    face_radius=RADIUS-.25
    for z,sgn,edge in [(DRUM_FRONT+.04,-1,rings[0]),(DRUM_REAR-.04,1,rings[-1])]:
        inner=ring(face_radius,z)
        for i in range(count):
            j=(i+1)%count
            b.face([edge[i],edge[j],inner[j],inner[i]],P,FRAME,[0,0,sgn])
    outer=circle(face_radius)
    # Front recess begins above the receiving corridor; lowered placement is
    # authored into the real shell rather than masking a full-height model.
    trap=np.array([[-1.12,DRUM_Y+1.34],[1.12,DRUM_Y+1.34],
                   [.57,1.59],[-.57,1.59]])
    cargo=clipped_rect(-.83,.83,.62,1.46,.035)
    front=DRUM_FRONT+.04
    loops=panel(b,outer,2,front,-1,P,holes=[trap,cargo])
    connect(b,plane_points(loops[1],2,front),plane_points(loops[1],2,front+.22),D,inner=True)
    slots=[]
    for i in range(5):
        yy=DRUM_Y+1.15-i*.285
        half=.91-i*.075
        slots.append(clipped_rect(-half,half,yy-.11,yy+.055,.045))
    tf=panel(b,loops[1],2,front+.22,-1,D,holes=slots)
    for slot in tf[1:]:pocket(b,slot,2,front+.22,front+.34,-1,DARK)
    # Real receiver walls and aft stop clear the complete measured native motion.
    pocket(b,loops[2],2,front,3.055,-1,D)
    # Two closed rear wells, tapering central web and low broad internal steps.
    left=np.array([[-.65,DRUM_Y+1.48],[-1.20,DRUM_Y+1.48],[-1.68,DRUM_Y+.92],
                   [-1.89,DRUM_Y+.12],[-1.63,DRUM_Y-.78],[-1.10,DRUM_Y-1.46],
                   [-.61,DRUM_Y-1.46],[-.36,DRUM_Y-.05]])
    right=left.copy();right[:,0]*=-1
    rear=DRUM_REAR-.04
    ls=panel(b,outer,2,rear,1,P,holes=[left,right])
    for side,loop in zip((-1,1),ls[1:]):
        pocket(b,loop,2,rear,3.18,1,D)
        # Broad stepped shelves integrated into the well's backing, below its lip.
        for y in (DRUM_Y-.55,DRUM_Y+.40):
            xs=[]
            for a,c in zip(loop,np.roll(loop,-1,axis=0)):
                if min(a[1],c[1])<=y<=max(a[1],c[1]) and abs(a[1]-c[1])>1e-6:
                    xs.append(a[0]+(c[0]-a[0])*(y-a[1])/(c[1]-a[1]))
            lo,hi=min(xs)+.035,max(xs)-.035
            prof=[[3.18,y-.14],[3.39,y-.14],[3.39,y-.035],[3.18,y+.09]]
            # zy polygon extrusion along x; joins backing instead of floating bars.
            bb=B();a=plane_points(prof,0,lo);c=plane_points(prof,0,hi)
            connect(bb,a,c,D);bb.face(a,D,PLAIN,[-1,0,0]);bb.face(c,D,PLAIN,[1,0,0])
            for g in bb.groups():
                for t in g['corners']:b.face(t[:,:3],g['material'],(0,0,1,1),t[:,3:6].mean(0),t[:,6:8])
    add('Transverse_drum',b,'drum')


def shoulder(s):
    # Local wing/engine root fairing meets the hull and lower drum. Its upper lip
    # stays below the roof; the 40/60 embedding is not faked by raising a pedestal.
    profile=np.array([[.70,-.76],[1.62,.10],[2.24,.26],[3.22,-.48],[3.22,-1.25],
                      [2.40,-1.52],[.70,-1.72]])
    b=B()
    inner=plane_points(profile,0,s*1.12)
    outer=plane_points(profile,0,s*1.94)
    outer[:,1]+=.12
    connect(b,inner,outer,P)
    b.face(inner,D,PLAIN,[-s,0,0]);b.face(outer,P,PLAIN,[s,0,0])
    add('Port_shoulder' if s<0 else 'Starboard_shoulder',b,'mount')


def wing(s):
    poly=np.array([[1.49,-.68],[4.65,-3.38],[4.94,-3.23],[4.94,-2.13],
                   [2.05,1.03],[1.49,1.03]]) # x,z; sweep forward
    b=B()
    aa=np.array([[s*x,-1.38-.31*(x-1.49),z] for x,z in poly])
    bb=aa.copy();bb[:,1]-=.18
    connect(b,bb,aa,P);b.face(aa,P,PLAIN,[0,1,0]);b.face(bb,P3,PLAIN,[0,-1,0])
    add('Port_wing' if s<0 else 'Starboard_wing',b,'wing')
    # Closed sleeve with a real wing-sized mouth; joint design remains provisional.
    frame=np.array([[-.87,-1.04],[-.62,-.80],[.99,-.80],[1.25,-1.02],
                    [1.25,-1.77],[.99,-1.95],[-.65,-1.95],[-.87,-1.71]])
    slot=clipped_rect(-.73,1.12,-1.66,-1.25,.07)
    b=B();ls=panel(b,frame,0,s*1.68,s,P,holes=[slot])
    connect(b,plane_points(ls[0],0,s*1.24),plane_points(ls[0],0,s*1.68),P)
    panel(b,ls[0],0,s*1.24,-s,D)
    pocket(b,ls[1],0,s*1.68,s*1.29,s,D)
    add('Port_socket' if s<0 else 'Starboard_socket',b,'mount')


def engine(s):
    b=B();n=16;angles=(np.arange(n)+.5)*2*np.pi/n
    def ring(z,r):
        return np.column_stack([s*ENGINE_X+r*np.cos(angles),ENGINE_Y+r*np.sin(angles),np.full(n,z)])
    profile=[(1.76,.36),(2.03,.47),(2.31,.67),(3.30,.67),(3.56,.53),
             (3.96,.53),(4.10,.49),(4.10,.39),(3.48,.34)]
    rings=[ring(z,r) for z,r in profile]
    for i,(a,c) in enumerate(zip(rings,rings[1:])):
        # A hollow aft throat with real depth, terminated by a flat dark nozzle.
        connect(b,a,c,DARK if i==7 else R if i==2 else P,inner=i==7)
    b.face(rings[0],D,PLAIN,[0,0,-1]);b.face(rings[-1],DARK,PLAIN,[0,0,1])
    add('Port_engine' if s<0 else 'Starboard_engine',b,'engine')


def native_parts(ns):
    names=f.component_map(ns);loc=f.local_geometry(ns);tr,_=f.audit.transforms(ns)
    world={names[file]:f.base.world(gs,*tr[file.lower()]) for file,gs in loc.items()}
    cabin=f.clip_groups(world['Root'],2,-4.70,False)
    add('Native_cabin',cabin,'native',False)
    add('glass_lod1',world['glass_lod1'],'glass',False)
    add('BayDoor_lod1',world['BayDoor_lod1'],'baydoor',False)
    # Measure the native drum's circular outer face, independent of its support flange.
    xyz=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in world['Root']])
    mask=(abs(abs(xyz[:,0])-.73305)<.00010)&(xyz[:,2]>-1.5)
    pts=np.unique(xyz[mask,1:3].round(5),axis=0)
    fit=np.linalg.lstsq(np.column_stack([2*pts,np.ones(len(pts))]),(pts*pts).sum(1),rcond=None)[0]
    radius=float(np.sqrt(fit[2]+np.dot(fit[:2],fit[:2])))
    assert abs(radius-RADIUS)<.0001
    return dict(cabin_cut_z=-4.70,cabin_triangles=sum(len(g['corners']) for g in cabin),
                original_circle_center_yz=fit[:2],native_outer_face_radius=radius,
                circle_fit_max_error=float(abs(np.linalg.norm(pts-fit[:2],axis=1)-radius).max()),
                native_glass_preserved=True,source_pose='Native construct zero pose; cabin/lid/glass fixed relative to Root')


def export_cmp(header, objects, destination, bay_open=False,min_cross_area=1e-8):
    salt=secrets.token_hex(6);mapping={};cons=f.folder('Cons');cmpnd=f.folder('Cmpnd',cons)
    nodes=[f.folder('\\',cmpnd,f.folder('VMeshLibrary'))];levels={};fix=[]
    # Root component first; semantic names remain stable across fresh salted exports.
    ordered=sorted(objects,key=lambda e:e['name']!='Root')
    for i,ob in enumerate(ordered):
        name=ob['name'];file=f'rhf14_{name}_{salt}.3db';assert len(file)<64
        mapping[name]=file
        cmpnd.children.append(f.folder('Root' if i==0 else f'Part_{name}',
            f.textnode('File name',file),f.mesh.Node('Index',struct.pack('<I',i)),f.textnode('Object name',name)))
        nodes[0].children.append(f.folder(file,f.folder('MultiLevel')))
        groups=ob['groups']
        if bay_open and name=='BayDoor_lod1':
            groups=f.base.world(groups,np.eye(3),np.array([0,.29331333136,3.35259188712]))
        levels[file]=groups
        if i:
            fix.append(b'Root\0'.ljust(64,b'\0')+name.encode().ljust(64,b'\0')+
                       np.r_[np.zeros(3),np.eye(3).reshape(-1)].astype('<f4').tobytes())
    cons.children=[f.mesh.Node('Fix',b''.join(fix))]
    f.write_geometry(nodes,[levels],min_cross_area=min_cross_area)
    resource_map={}
    for i,node in enumerate(f.mesh.child(nodes[0],'VMeshLibrary').children):
        old=node.name;node.name=f'rhf14_{i:02}_{salt}.vms';resource_map[old]=node.name
    ids={f.mesh.crc(old):f.mesh.crc(new) for old,new in resource_map.items()}
    for path,node in f.mesh.walk(nodes):
        if path.lower().endswith('/vmeshref'):
            raw=bytearray(node.blob);struct.pack_into('<I',raw,4,ids[struct.unpack_from('<I',raw,4)[0]]);node.blob=bytes(raw)
        if path.endswith('/Switch2'):node.blob=np.array([0,10000],'<f4').tobytes()
    destination.write_bytes(f.mesh.write_tree(header,nodes))
    _,reopened=f.mesh.read_tree(destination.read_bytes())
    decoded=f.local_geometry(reopened);dn=f.component_map(reopened)
    counts={dn[k]:sum(len(g['corners']) for g in gs) for k,gs in decoded.items()}
    max_error=0.
    for file,gs in decoded.items():
        # Match exported vertices without depending on material-group ordering.
        expected={g['material']:g['corners'] for g in f.merge(levels[file])}
        for g in gs:
            a=g['corners'];c=expected[g['material']]
            assert a.shape==c.shape,(file,a.shape,c.shape)
            max_error=max(max_error,float(abs(a-c).max()))
    assert max_error<1e-5
    assert all(0<n<21000 for n in counts.values())
    assert not any(n.name.lower() in ('material library','texture library') for n in reopened[0].children)
    return dict(file=destination.as_posix(),sha256=f.digest(destination),salt=salt,
                private_submodels=mapping,private_meshes=resource_map,triangles=counts,lods=1,
                readback_max_float_error=max_error,
                static_extended=True,bay_open=bay_open,embedded_materials=False)


def main():
    assert shutil.disk_usage(ROOT).free>2*1024**3
    OUT.mkdir(parents=True,exist_ok=True)
    selection=json.loads((TOPIC/'selection.json').read_text(encoding='utf8'))
    assert f.digest(SOURCE)==selection['source_sha256']
    sources=[SOURCE,MAT,ENV,TOPIC/selection['art'],TOPIC/selection['rear_view']['art']]
    pinned={p.as_posix():f.digest(p) for p in sources}
    header,ns=f.mesh.read_tree(SOURCE.read_bytes())
    OBJECTS.clear();native=native_parts(ns)
    neck();body_decks()
    for s in (-1,1):side_shell(s);shoulder(s);wing(s);engine(s)
    drum()
    materials=f.audit.material_table([MAT,ENV])
    used={g['material'] for e in OBJECTS for g in e['groups']}
    assert used<=materials.keys()
    assert all('metal' not in materials[mid]['texture'].lower() for mid in used)
    palette={}
    td=OUT/'textures';td.mkdir(exist_ok=True)
    for mid in used:
        mat=materials[mid];m={k:v for k,v in mat.items() if k!='image'}
        m['image_path']=None
        if mat['image']:
            path=td/(mat['texture'].replace('.tga','')+'.png')
            if not path.exists():mat['image'].save(path)
            m['image_path']=path.as_posix()
        palette[str(mid)]=m
    exports=[export_cmp(header,OBJECTS,OUT/'rh_pir_fighter_f14_open.cmp'),
             export_cmp(header,OBJECTS,OUT/'rh_pir_fighter_f14_bay_open.cmp',True)]
    points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for e in OBJECTS for g in e['groups']])
    report=dict(source=SOURCE.as_posix(),source_sha256=f.digest(SOURCE),sources=pinned,native=native,
                art=selection['art'],rear_art=selection['rear_view']['art'],
                drum=dict(radius=RADIUS,diameter=2*RADIUS,center_y=DRUM_Y,local_roof_y=DECK_Y,
                          bottom_y=DRUM_Y-RADIUS,top_y=DRUM_Y+RADIUS,
                          submerged_height_fraction=(DECK_Y-(DRUM_Y-RADIUS))/(2*RADIUS),
                          axial_thickness=DRUM_REAR-DRUM_FRONT,front_z=DRUM_FRONT,rear_z=DRUM_REAR),
                engines=dict(centers_x=[-ENGINE_X,ENGINE_X],center_y=ENGINE_Y,
                             lowering_vs_unsubmerged_placement=.8*RADIUS),
                objects=OBJECTS,materials=palette,exports=exports,
                native_hardpoints_reference=f.hp_world(ns),
                bounds=[points.min(0),points.max(0)],total_triangles=sum(len(g['corners']) for e in OBJECTS for g in e['groups']),
                stage='First static form prototype. Native cockpit, full cargo cavity. Articulation provisional; no animation/damage/SUR/LOD finalization.',
                installed=False,game_launched=False)
    dump(OUT/'geometry.json',report)
    for p,h in pinned.items():assert f.digest(Path(p))==h,'Changed source during prototype build'
    print(json.dumps(dict(output=str(OUT),triangles=report['total_triangles'],native=native,
                          drum=report['drum'],bounds=report['bounds']),default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a,indent=2))


if __name__=='__main__':main()
