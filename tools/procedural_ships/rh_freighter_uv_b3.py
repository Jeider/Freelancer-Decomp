"""Q13 uv_06: B3 engine supports/barrels and the user's second UV detail pass.

Offline only. Native cockpit, HPs and animation are preserved by rig_build.
"""
import collections
import json
import math
import shutil
import numpy as np
import rh_freighter_uv_detail as old

uv, rig, f, q = old.uv, old.rig, old.f, old.q
package = old.previous
PREVIOUS = old.OUT
OUT = PREVIOUS.parent / 'uv_06'
ART = q.ROOT / 'out/ship_design/rh_freighter/concepts/round_03/rh_freighter_B3_sheet.png'
REPORT = []
ENGINES = []
SLOPE = (3.81-1.38)/3.52
SCALE = math.hypot(1, SLOPE)
UP_BACK = np.array([[-7.55,1.26],[-4.12,3.88],[5.66,3.88],[7.42,2.5],
    [7.42,.60],[5.82,.60],[-3.04,-1.49],[-4.56,.02],[-6.80,-1.52],[-7.55,-1.02]])
UP_FACE = np.array([[-7.14,1.13],[-4.01,3.60],[5.48,3.60],[7.05,2.35],
    [7.05,.91],[5.77,.91],[-2.96,-1.13],[-4.51,.42],[-6.60,-1.08],[-7.14,-.72]])
PANEL03 = list(uv.PATCHES['skin'])


def dump(name, data):
    (OUT/name).write_text(json.dumps(data, ensure_ascii=False, indent=2,
        default=lambda a: a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def assert_unedited():
    for folder in (PREVIOUS, OUT):
        for filename, report in [('rh_pir_freighter.cmp','build.json'),
                ('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/filename).exists():continue
            expected=json.loads((folder/report).read_text())['cmp_sha256']
            assert f.digest(folder/filename)==expected, (str(folder/filename),'manual changes: preserve before generating')


def engine(side):
    # B3: a rising, exposed structural neck, a substantial barrel, tapered rear
    # shoulder and one short nozzle collar. No disconnected bulb/dumbbell.
    angles=np.deg2rad(15+np.arange(12)*30)
    def ring(z,cx,cy,w,h):
        return np.column_stack((side*cx+w*np.cos(angles),cy+h*np.sin(angles),np.full(12,z)))
    def mount(z,cx,cy,w,h):
        xy=np.array([[w*.72,h],[0,h],[-w*.72,h],[-w,h*.72],[-w,0],[-w,-h*.72],
            [-w*.72,-h],[0,-h],[w*.72,-h],[w,-h*.72],[w,0],[w,h*.72]])
        # Same ring ordering as the barrel, positive winding around +Z.
        xy=xy[::-1]
        # Match angle order to avoid twisting the support-to-barrel transition.
        theta=np.arctan2(xy[:,1],xy[:,0]);order=np.argsort((theta-np.deg2rad(15))%(2*np.pi))
        xy=xy[order]
        return np.column_stack((side*cx+xy[:,0],cy+xy[:,1],np.full(12,z)))
    profile=[(7.70,1.70,-1.12,.64,.68),(8.32,1.78,-.91,.53,.57),
        (8.88,1.99,-.40,.45,.42),(9.35,2.08,-.28,.48,.44),
        (9.48,2.08,-.28,.91,.88),(9.90,2.08,-.28,1.29,1.24),
        (11.18,2.08,-.28,1.29,1.24),(11.62,2.08,-.28,1.04,1.00),
        (11.65,2.08,-.28,.98,.94),(12.158,2.08,-.28,.98,.94)]
    loops=[mount(*s) if i<4 else ring(*s) for i,s in enumerate(profile)]
    b=q.B()
    for i,(a,c) in enumerate(zip(loops,loops[1:])):
        b.bridge(a,c,8 if i<3 else 3 if i==3 else 9 if i==5 else 2 if i==7 else 1)
    b.face(loops[0],8,normal=[0,0,-1])
    mouth=ring(12.158,2.08,-.28,.83,.79)
    floor=ring(11.15,2.08,-.28,.76,.72)
    b.bridge(loops[-1],mouth,2)
    b.bridge(mouth,floor,3,inner=True)
    b.face(floor,7,normal=[0,0,1])
    groups,closure=q.coherent(b.groups())
    ENGINES.append(dict(side=side,center_xy=[side*2.08,-.28],profile=profile,
        mouth_z=12.158,exhaust_z=11.15,recess_depth=1.008,closure=closure,
        mount_visible_z=[8.30,9.35],engine_style='B3 rising neck and long barrel',
        geometry_triangles=sum(len(g['corners']) for g in groups)))
    return dict(name=f'Engine casing - B3 swept support {side:+}',groups=groups,closed=True)


def chamfer_rect(hw,hl,cut,cz):
    return np.array([[-hw+cut,cz-hl],[hw-cut,cz-hl],[hw,cz-hl+cut],[hw,cz+hl-cut],
        [hw-cut,cz+hl],[-hw+cut,cz+hl],[-hw,cz+hl-cut],[-hw,cz-hl+cut]])


def front_patch(ob):
    # Replace only the foredeck ramp and its little service plateau. The core
    # already has verified hold/vent cuts; these must not be rebuilt away.
    kept=collections.defaultdict(list);removed=0
    for g in ob['groups']:
        for t in np.array(g['corners'],float):
            p=t[:,:3];height=1.38+(p[:,2]+7.62)*SLOPE;d=p[:,1]-height
            if (p[:,2].min()>=-7.62001 and p[:,2].max()<=-4.09999
                    and d.min()>-1e-5 and d.max()<.18001):
                removed+=1
            else:kept[g['material']].append(t)
    assert removed>8
    outer=np.array([[-2.14,-7.62],[2.14,-7.62],[2.35,-4.10],[-2.35,-4.10]])
    hole=chamfer_rect(1.64,.69,.12,-5.37)
    top=chamfer_rect(1.50,.51,.035,-5.37)
    points,triangles,contours=q.planar_mesh(outer,[hole])
    assert len(contours[0])==4 and len(contours[1])==8
    def plane(p,lift=0):return np.column_stack((p[:,0],1.38+(p[:,1]+7.62)*SLOPE+lift,p[:,1]))
    b=q.B();n=[0,1,-SLOPE]
    for ids in triangles:b.face(plane(points[ids]),1,normal=n)
    b.bridge(plane(hole),plane(top,.18),10)
    b.face(plane(top,.18),11,normal=n)
    for g in b.groups():kept[g['material']].extend(g['corners'])
    ob['groups']=package.pack(kept)
    REPORT.append(dict(region='front hatch platform',removed_triangles=removed,
        top_width=3.,top_length=1.02,complete_hatches=2,corner_cut=.035))
    return ob


def belly_pad(index):
    z=[-1.155,2.59][index-1]
    a=chamfer_rect(.92,1.075,.12,z);c=chamfer_rect(.75,.92,.035,z)
    def plane(p,y):return np.column_stack((p[:,0],np.full(len(p),y),p[:,1]))
    b=q.B();b.bridge(plane(a,-3.80),plane(c,-4.04),10)
    b.face(plane(a,-3.80),3,normal=[0,1,0]);b.face(plane(c,-4.04),11,normal=[0,-1,0])
    groups,closure=q.coherent(b.groups())
    return dict(name=f'Ventral integrated chine {index}',groups=groups,closed=True)


def prepare():
    assert_unedited();OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    objects=[]
    for ob in data['objects']:
        name=ob['name'];side=-1 if '-1' in name else 1
        if name.startswith('Rear engine transition'):continue  # rejected protruding block
        if name.startswith('Engine casing'):ob=engine(side)
        elif name.startswith('Continuous hull'):ob=front_patch(ob)
        elif name.startswith('Ventral'):ob=belly_pad(int(name.split()[-1]))
        objects.append(ob)
    data['objects']=objects
    (OUT/'mechanical_geometry.json').write_text(json.dumps(data,separators=(',',':'),
        default=lambda a:a.tolist()),encoding='utf8')
    dump('engine_geometry_check.json',ENGINES)
    # Retain the unchanged mechanical pocket depth report for the Blender rays.
    shutil.copyfile(PREVIOUS/'vent_clearance.json',OUT/'vent_clearance.json')


def configure():
    old.configure()
    uv.PATCHES.update(panel03=PANEL03,roof_edge=[(uv.P,(.017,.165,.497,.251))],
        barrel_red=[(uv.R,(.340,.321,.658,.463))],engine_red=[(uv.R,(.016,.036,.148,.453))])


def complete(charts,mapped):
    for (family,cell,rotate,exact,key),values in charts.items():
        result,stat=package.ORIGINAL_CHART(values,family,cell,rotate=rotate,exact=exact)
        for mid,ts in result.items():mapped[mid].extend(ts)
        REPORT.append(dict(region=str(key),**stat))
    return package.pack(mapped)


def add(charts,t,family,co,cell=(2.5,2.5),key=None,rotate=False,exact=False):
    old.add_chart(charts,t,family,co,cell,key,rotate,exact)


def fixed_box(t,co,lo,hi,box,mid,mapped):
    t=t.copy();box=np.array(box);lo=np.array(lo);hi=np.array(hi)
    t[:,6:8]=box[:2]+(co-lo)/(hi-lo)*(box[2:]-box[:2]);mapped[mid].append(t)


def moving_map(name,groups):
    index=int(name.split()[-1])-1;z=[-2.76,.66,3.94][index];r=[.72,1.11,.72][index]
    reach=4.70 if index==1 else 4.19
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t);c=p.mean(0)
            if abs(n[0])>.95 or abs(p[:,0]).min()>=reach-.281:
                rest[g['material']].append(t);continue
            # A full red panel on each broad octagonal wall; each is a single
            # surface chart including both triangles, with aligned axial edges.
            angle=np.unwrap(np.arctan2(p[:,2]-z,p[:,1]-2.08))
            if angle.mean()>math.pi:angle-=2*math.pi
            co=np.column_stack((abs(p[:,0]),angle*r))
            key=('red barrel flank',tuple(n.round(4)),round(float(n@c),4))
            add(charts,t,'barrel_red',co,(100,100),key,exact=True)
    for g in old.moving_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return complete(charts,mapped)


def roof_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    profile=np.array([[1.82,4.51],[1.96,4.65],[2.15,4.65],[2.32,4.51],[2.32,4.34]])
    lengths=np.linalg.norm(np.diff(profile,axis=0),axis=1);arc=np.r_[0,np.cumsum(lengths)]
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];rho=np.hypot(p[:,1]-q.SHELL_Y,p[:,2]-q.SHELL_Z)
            theta=np.arctan2(p[:,2]-q.SHELL_Z,p[:,1]-q.SHELL_Y)
            if np.ptp(theta)<1e-5 and np.ptp(rho)>.04:
                add(charts,t,'pale_edge',np.column_stack((p[:,0],rho)),(3,100),
                    ('roof end lip',round(float(theta.mean()),4)),exact=True)
                continue
            if abs(p[:,0].mean())<1.81999 or abs(p[:,0]).min()<1.81999 or rho.max()<4.34001:
                rest[g['material']].append(t);continue
            points=np.column_stack((abs(p[:,0]),rho));best=None
            for i,(a,b) in enumerate(zip(profile,profile[1:])):
                s=(points-a)@(b-a)/lengths[i]**2
                err=np.linalg.norm(points-(a+s[:,None]*(b-a)),axis=1).max()
                if s.min()>=-1e-4 and s.max()<=1.0001 and (best is None or err<best[0]):best=(err,i,s)
            if best is None or best[0]>.001:
                rest[g['material']].append(t);continue
            _,i,s=best;theta=np.arctan2(p[:,2]-q.SHELL_Z,p[:,1]-q.SHELL_Y)
            co=np.column_stack((theta*4.6,arc[i]+s*lengths[i]))
            add(charts,t,'roof_edge',co,(4.1,100),('one roof rail',int(np.sign(p[:,0].mean()))),exact=True)
    for g in old.region_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return complete(charts,mapped)


def upper_rim(t):
    # Barycentric interpolation on each authored ruled wall handles later
    # Boolean subdivision vertices without resetting the chart at those cuts.
    side=np.sign(t[:,0].mean());a=q.B().yz(UP_BACK,side*2.62);b=q.B().yz(UP_FACE,side*3.50)
    mid=(a+b)/2;arc=np.r_[0,np.cumsum(np.linalg.norm(np.roll(mid,-1,axis=0)-mid,axis=1))]
    width=np.linalg.norm(b-a,axis=1).mean()
    for i in range(len(a)):
        j=(i+1)%len(a);quad=np.array([a[i],a[j],b[j],b[i]])
        cs=np.array([[arc[i],0],[arc[i+1],0],[arc[i+1],width],[arc[i],width]])
        answer=[]
        for p in t[:,:3]:
            found=None
            for ids in ([0,1,2],[0,2,3]):
                tri=quad[ids];basis=(tri[1:]-tri[0]).T
                st=np.linalg.lstsq(basis,p-tri[0],rcond=None)[0]
                w=np.r_[1-st.sum(),st]
                if w.min()>-1e-4 and np.linalg.norm(w@tri-p)<1e-4:found=w@cs[ids];break
            if found is None:break
            answer.append(found)
        if len(answer)==3:return np.array(answer)
    return None


def core_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];c=p.mean(0);n=old.normal(t);role=g['material'];family=None
            co=uv.plane_coords(p,n);key=(name,tuple(n.round(5)),round(float(n@c),4));exact=False;cell=(2.4,2.4)
            if role==11:  # explicit authored chart, never a cropped generic patch
                for side in (-1,1):
                    cut=np.column_stack((t,p[:,0]))
                    cut=uv.clip(cut,8,0,side>0)
                    for tt in package.triangles(cut[:,:8]) if len(cut)>=3 else []:
                        fixed_box(tt,tt[:,[0,2]],[-1.5 if side<0 else 0,-5.88],
                            [0 if side<0 else 1.5,-4.86],package.HATCH,uv.P,mapped)
                continue
            if role==10:family='brown'
            elif n[1]<-.5 and c[1]<-1.8:
                family='dark' if abs(c[1]+3.40)<.04 else 'panel03'
                # Common chart axes and origin for every belly field/chamfer.
                co=p[:,[2,0]];key=('belly panel03',family);cell=(2.2,1.9)
            elif c[2]>5.72 and n[1]>.4:
                # Rear deck echoes the forehead: pale center, red border rails.
                # Clip at X boundaries so the stripe never wanders with triangles.
                for low,high,israil in [(-20,-1.46,True),(-1.46,1.46,False),(1.46,20,True)]:
                    poly=np.column_stack((t,p[:,0]))
                    poly=uv.clip(poly,8,low,True)
                    if len(poly)>=3:poly=uv.clip(poly,8,high,False)
                    if len(poly)<3:continue
                    for tt in package.triangles(poly[:,:8]):
                        co2=np.column_stack((tt[:,2],abs(tt[:,0]) if israil else tt[:,0]))
                        add(charts,tt,'red_rail' if israil else 'light',co2,
                            (.87,100) if israil else (2,2),('rear deck edge' if israil else 'rear deck',int(np.sign(tt[:,0].mean())) if israil else 0),exact=israil)
                continue
            elif c[2]>8.299 and n[2]>.95:family='dark';co=p[:,[0,1]];key='rear central machinery'
            if family:add(charts,t,family,co,cell,key,exact=exact)
            else:rest[role].append(t)
    for g in old.region_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return complete(charts,mapped)


def region_map(name,groups):
    if name.startswith('New transverse'):return moving_map(name,groups)
    if name.startswith('Curved roof'):return roof_map(name,groups)
    if name.startswith('Continuous hull'):return core_map(name,groups)
    if not name.startswith(('Ventral','Foredeck','Faceted shoulder')):return old.region_map(name,groups)
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];c=p.mean(0);n=old.normal(t);family=None;cell=(2.5,2.5);exact=False
            co=uv.plane_coords(p,n);key=(name,tuple(n.round(5)),round(float(n@c),4))
            if name.startswith('Ventral'):
                z=[-1.155,2.59][int(name.split()[-1])-1]
                if g['material']==11:
                    fixed_box(t,np.column_stack((p[:,2]-z,p[:,0])),[-.92,-.75],[.92,.75],package.HATCH,uv.P,mapped)
                    continue
                family='brown'
            elif name.startswith('Foredeck'):
                if n[1]>.25:
                    co=np.column_stack((p[:,2],abs(p[:,0])))
                    family='red_rail';cell=(1.38,100);exact=True;key=(name,'three aligned foredeck panels')
                else:family='brown'
            elif name.startswith('Faceted shoulder'):
                co2=upper_rim(t)
                if co2 is not None:
                    family='frame03';co=co2;cell=(2.5,100);exact=True;key=(name,'entire panel03 perimeter')
            if family:add(charts,t,family,co,cell,key,exact=exact)
            else:rest[g['material']].append(t)
    for g in old.region_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return complete(charts,mapped)


def engine_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list)
    side=-1 if '-1' in name else 1;cx=side*2.08
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t);c=p.mean(0);role=g['material']
            if role==7:
                fixed_box(t,p[:,[0,1]],[cx-.82,-1.10],[cx+.82,.54],(0,0,1,1),uv.G,mapped);continue
            if role==8:
                family='brown' if abs(n[0])>.5 or n[1]<0 else 'light'
                co=uv.plane_coords(p,n);key=('B3 support',tuple(n.round(4)),round(float(n@c),4));cell=(2,1.4);exact=False
            else:
                angle=np.unwrap(np.arctan2(p[:,1]+.28,p[:,0]-cx))
                if angle.mean()>math.pi:angle-=2*math.pi
                family={1:'light',2:'pale_edge',3:'dark',9:'engine_red'}[role]
                co=np.column_stack((angle*1.25,p[:,2]));cell=(2,100);exact=False
                key=(name,role,round(p[:,2].min(),4),round(p[:,2].max(),4))
                if role==9:
                    # B3 painted panels follow the longitudinal body, bounded by
                    # its shoulders. One per broad facet; no tiny random strips.
                    cell=(.66,100);exact=True;key=(name,'barrel red panels')
                if np.ptp(p[:,2])<1e-5:co=p[:,[0,1]];cell=(2.4,2.4)
            add(charts,t,family,co,cell,key,exact=exact)
    return complete(charts,mapped)


def main():
    prepare();configure();rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp'
    diagnostics=[]
    def mapping(name,gs):
        result=engine_map(name,gs) if name.startswith('Engine casing') else region_map(name,gs)
        bad=0.;count=0
        for g in result:
            ts=np.array(g['corners']);p=ts[:,:,:3];u=ts[:,:,6:8]
            area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)/2
            a=u[:,1]-u[:,0];b=u[:,2]-u[:,0];ua=abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/2
            mask=(area>1e-6)&(ua<1e-12)
            bad+=float(area[mask].sum());count+=int(mask.sum())
        diagnostics.append(dict(object=name,collapsed_uv_triangles=count,collapsed_uv_area=bad))
        if not name.startswith(('Original','Stepped circular')):
            assert bad<1e-7, (name,'collapsed UV surface',bad)
        return result
    rig.material_map=mapping
    rig.main(OUT/'mechanical_geometry.json')
    dump('uv_degenerate.json',dict(cmp_sha256=f.digest(rig.DEST),objects=diagnostics))
    dump('engine_check.json',dict(engines=ENGINES,cmp_sha256=f.digest(rig.DEST),installed=False))
    dump('uv_layout.json',dict(cmp_sha256=f.digest(rig.DEST),regions=REPORT,
        source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),engine_art=str(ART),
        engine_art_sha256=f.digest(ART),installed=False))
    package.OUT=OUT;package.open_review()
    print('UV_B3_READY',OUT)


if __name__=='__main__':main()
