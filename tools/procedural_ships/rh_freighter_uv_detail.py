"""Q13 uv_05: mounted engine pods and explicitly directed material regions.

Offline prototype only. Prepare raw geometry, carve vent clearance in Blender,
then export. Existing review copies and native animation/HP identities stay intact.
"""
import collections
import json
import math
import sys
import numpy as np
import rh_freighter_uv_package as previous

uv,rig,f,q=previous.uv,previous.rig,previous.f,previous.q
PREVIOUS=previous.OUT
OUT=PREVIOUS.parent/'uv_05'
BROWN=previous.BROWN
VENT=np.array([[-6.85,-.67],[-6.85,.80],[-5.35,1.91],[-4.12,1.91],[-4.12,.85],[-5.18,-.02]])
BACK=np.array([[-6.82,-1.75],[-4.55,-.27],[-3.06,-1.67],[5.84,.42],[7.39,.39],[7.50,-1.55],[6.20,-4.118],[-5.25,-4.118]])
FACE=np.array([[-6.45,-1.85],[-4.57,-.65],[-3.09,-2.06],[5.84,.05],[7.06,.03],[7.12,-1.53],[5.99,-3.72],[-5.12,-3.72]])
INNER=np.array([[-5.88,-2.12],[-4.60,-1.15],[-3.16,-2.49],[5.71,-.40],[6.61,-.42],[6.62,-1.58],[5.67,-3.26],[-4.96,-3.26]])
REPORT=[]
ENGINE_REPORT=[]


def in_vent(point,tolerance=1e-5):
    if q.inside(VENT,point):return True
    for a,b in zip(VENT,np.roll(VENT,-1,axis=0)):
        t=np.clip((point-a)@(b-a)/((b-a)@(b-a)),0,1)
        if np.linalg.norm(point-a-t*(b-a))<tolerance:return True
    return False


def configure():
    previous.configure()
    # Same dark material as the native hump. Vent wells are an explicit brown
    # exception; brown is otherwise used on the sides of raised volumes.
    uv.PATCHES.update(dark=[(uv.D,(.670,.012,.994,.206))],
        brown=[(BROWN,previous.PALE)],
        frame03=[(uv.S,(.003,.503,.433,.711)),(uv.S,(.669,.503,.995,.626))],
        red_edge=[(uv.R,(.016,.036,.148,.453))],
        red_rail=[(uv.R,(.340,.321,.658,.463))],
        pale_edge=[(uv.P,(.017,.165,.497,.251))])


def chart_result(charts,mapped):
    for (family,cell,rotate,exact,key),values in charts.items():
        result,stat=previous.ORIGINAL_CHART(values,family,cell,rotate=rotate,exact=exact)
        for mid,ts in result.items():mapped[mid].extend(ts)
        REPORT.append(dict(region=str(key),**stat))
    return previous.pack(mapped)


def add_chart(charts,t,family,co,cell=(2.5,2.5),key=None,rotate=False,exact=False):
    charts[(family,cell,rotate,exact,key)].append((t,co))


def normal(t):
    p=t[:,:3];n=np.cross(p[1]-p[0],p[2]-p[0]);return n/np.linalg.norm(n)


def contour_coordinates(t,outer,inner,outer_x,inner_x):
    """One continuous ribbon coordinate around the complete stepped outline."""
    side=np.sign(t[:,0].mean());a=q.B().yz(outer,side*outer_x);b=q.B().yz(inner,side*inner_x)
    middle=(a+b)/2;length=np.linalg.norm(np.roll(middle,-1,axis=0)-middle,axis=1)
    arc=np.r_[0,np.cumsum(length)]
    best=None
    for i in range(len(a)):
        j=(i+1)%len(a);quad=np.array([a[i],a[j],b[j],b[i]])
        distances=np.linalg.norm(t[:,:3,None]-quad.T[None,:,:],axis=1)
        ids=distances.argmin(1);err=float(distances[np.arange(3),ids].max())
        if best is None or err<best[0]:best=(err,i,ids)
    err,i,ids=best
    assert err<1e-4,('contour point not on authored ring',err,t[:,:3])
    width=np.linalg.norm(b-a,axis=1).mean()
    coords=np.array([[arc[i],0],[arc[i+1],0],[arc[i+1],width],[arc[i],width]])
    return coords[ids]


def lower_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            n=normal(t);p=t[:,:3];c=p.mean(0);role=g['material']
            if role==2:
                co=contour_coordinates(t,FACE,INNER,3.34,3.34)
                # The long axis of this atlas panel is V. Every repeat follows
                # arc length, including the kink; never reset at a mesh triangle.
                add_chart(charts,t,'red_edge',co[:,::-1],(100,1.65),'lower red contour',exact=True)
            elif role==1 and not (abs(n[0])>.95 and n[0]*c[0]<0):
                co=contour_coordinates(t,BACK,FACE,2.52,3.34)
                add_chart(charts,t,'frame03',co,(2.5,100),'outer panel03 belt',exact=True)
            else:
                family='dark';co=uv.plane_coords(p,n)
                add_chart(charts,t,family,co,key=(name,role,tuple(n.round(5)),round(float(n@c),4)))
    return chart_result(charts,mapped)


def vane_map(name,groups):
    allpoints=np.concatenate([np.array(g['corners'])[...,:3].reshape(-1,3) for g in groups])
    lo,hi=allpoints[:,2].min(),allpoints[:,2].max()
    # Project across the visible continuous blade section, not per facet.
    across=lambda p:abs(p[:,0])*.94-p[:,1]*.347
    cross=across(allpoints);bottom,top=cross.min(),cross.max()
    mapped=collections.defaultdict(list);charts=collections.defaultdict(list)
    # An intact long painted panel: rotate the vertical native red panel so its
    # long side follows the vane. No tiling and no painted pale bands on the blade.
    box=np.array([.030,.048,.132,.445])
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=normal(t)
            if abs(n[2])>.9:
                add_chart(charts,t,'brown',uv.plane_coords(p,n),key=(name,'end',round(p[:,2].mean(),4)))
            else:
                t[:,6]=box[0]+(across(p)-bottom)/(top-bottom)*(box[2]-box[0])
                t[:,7]=box[1]+(p[:,2]-lo)/(hi-lo)*(box[3]-box[1])
                mapped[uv.R].append(t)
    REPORT.append(dict(region=name,red_panels=1,uv_box=box.tolist(),repeat=False))
    return chart_result(charts,mapped)


def moving_map(name,groups):
    index=int(name.split()[-1])-1;z=[-2.76,.66,3.94][index];r=[.72,1.11,.72][index]
    reach=4.70 if index==1 else 4.19
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);cap=[]
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=normal(t);c=p.mean(0)
            if abs(n[0])>.95 and n[0]*c[0]>0 and abs(c[0])>reach-.15:
                cap.append(dict(material=g['material'],corners=[t]));continue
            if abs(n[0])>.95:
                family='brown' if abs(c[0])<reach-.2 else 'pale_edge'
                co=p[:,[2,1]];key=('barrel flat',round(abs(c[0]),4))
            else:
                angle=np.unwrap(np.arctan2(p[:,2]-z,p[:,1]-2.08))
                if angle.mean()>math.pi:angle-=2*math.pi
                co=np.column_stack((angle*r,abs(p[:,0])))
                family='pale_edge' if abs(p[:,0]).min()>=reach-.281 else 'brown'
                key=('continuous barrel',family)
            add_chart(charts,t,family,co,(2.5,2.5) if family=='brown' else (2.4,100),key)
    if cap:
        for g in uv.material_map(name,cap):mapped[g['material']].extend(g['corners'])
    return chart_result(charts,mapped)


def region_map(name,groups):
    if name.startswith('Lower diagonal'):return lower_map(name,groups)
    if name.startswith('Intake vane'):return vane_map(name,groups)
    if name.startswith('New transverse'):return moving_map(name,groups)
    selected=('Faceted shoulder','Recess relief','Continuous hull','Foredeck')
    if not name.startswith(selected):return previous.special_map(name,groups)
    charts=collections.defaultdict(list);fallback=collections.defaultdict(list);mapped=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];c=p.mean(0);n=normal(t);family=None
            co=uv.plane_coords(p,n);cell=(2.5,2.5);rotate=False;exact=False
            if name.startswith('Faceted shoulder'):
                if in_vent(c[[2,1]]) and abs(c[0])<=3.501:
                    family='brown'
                elif g['material'] in (2,3,4) and abs(c[0])<3.499:
                    family='dark'  # all walls as well as the backing of button well
                elif abs(n[0])<.80 and n[1]<-.10:
                    family='brown'  # lower sloping side / diagonal joint
            elif name.startswith('Recess relief'):
                if not (abs(n[0])>.95 and n[0]*c[0]>0):family='brown'
            elif name.startswith('Continuous hull'):
                height=1.38+(c[2]+7.62)*(3.81-1.38)/3.52
                # The small service plateau's sides, excluding its accepted lid UV.
                delta=c[1]-height
                if -.001<delta<.181 and -5.91<c[2]<-4.83 and abs(c[0])<1.61 and delta<.179:
                    if n[1]<.6 or abs(delta)>.005:family='brown'
                if in_vent(c[[2,1]]) and abs(c[0])>=2.57:family='brown'
            elif name.startswith('Foredeck'):
                family='red_rail' if n[1]>.25 else 'brown'
                rotate=family=='red_rail';exact=rotate
                cell=(2.5,100) if rotate else (2.5,2.5)
            if family:
                add_chart(charts,t,family,co,cell,(name,tuple(n.round(5)),round(float(n@c),4)),rotate,exact)
            else:fallback[g['material']].append(t)
    if fallback:
        for g in previous.special_map(name,previous.pack(fallback)):mapped[g['material']].extend(g['corners'])
    return chart_result(charts,mapped)


def engine(side):
    cx=side*2.08;cy=-.28;angles=np.deg2rad(120-np.arange(12)*30)
    def ring(z,w,h):return np.column_stack((cx+w*np.cos(angles),cy+h*np.sin(angles),np.full(12,z)))
    def bracket(z,w,h):
        cut=.20
        xy=np.array([[-w+cut,h],[0,h],[w-cut,h],[w,h-cut],[w,0],[w,-h+cut],
            [w-cut,-h],[0,-h],[-w+cut,-h],[-w,-h+cut],[-w,0],[-w,h-cut]])
        return np.column_stack((cx+xy[:,0],cy+xy[:,1],np.full(12,z)))
    stations=[(7.45,1.0,.84),(8.15,.62,.53),(9.12,.62,.53),(9.42,.80,.67),
        (9.73,1.64,1.52),(10.55,1.64,1.52),(10.85,1.28,1.16),
        (10.85,1.04,.98),(11.00,1.04,.98),(11.12,1.21,1.12),(12.158,1.21,1.12)]
    loops=[bracket(*s) if i<4 else ring(*s) for i,s in enumerate(stations)]
    b=q.B()
    for i,(a,c) in enumerate(zip(loops,loops[1:])):
        b.bridge(a,c,8 if i<3 else 3 if i in (6,7) else 2 if i==8 else 1)
    b.face(loops[0],8,normal=[0,0,-1])
    mouth=ring(12.158,.98,.89);floor=ring(11.15,.84,.76)
    b.bridge(loops[-1],mouth,2);b.bridge(mouth,floor,3,inner=True);b.face(floor,7,normal=[0,0,1])
    groups,closure=q.coherent(b.groups())
    ENGINE_REPORT.append(dict(side=side,center_xy=[cx,cy],profile=stations,mouth_z=12.158,
        exhaust_z=11.15,recess_depth=1.008,mount_visible_z=[8.30,9.42],
        mount_half_width=.62,main_pod_half_width=1.64,closure=closure,
        geometry_triangles=sum(len(g['corners']) for g in groups)))
    return dict(name=f'Engine casing - structural mounting neck {side:+}',groups=groups,closed=True)


def rear_transition(side):
    # Remove the old full-height wedge that swallowed the entire mounting neck.
    poly=np.array([[6.1,1.5],[7.55,.85],[8.10,.45],[8.10,-.80],[7.4,-1.28],[6.1,-1.45]])
    b=q.B();a=b.yz(poly,side*.85);c=b.yz(poly,side*3.02)
    b.bridge(a,c,1);b.face(a,3,normal=[-side,0,0]);b.face(c,1,normal=[side,0,0])
    groups,closure=q.coherent(b.groups())
    return dict(name=f'Rear engine transition {side:+}',groups=groups,closed=True)


def engine_map(name,groups):
    other=[];charts=collections.defaultdict(list);mapped=collections.defaultdict(list)
    for g in groups:
        if g['material']!=8:other.append(g);continue
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=normal(t);c=p.mean(0)
            family='brown' if abs(n[0])>.3 or n[1]<0 else 'light'
            add_chart(charts,t,family,uv.plane_coords(p,n),key=(name,tuple(n.round(5)),round(float(n@c),4)))
    for g in previous.map_engine(name,other):mapped[g['material']].extend(g['corners'])
    return chart_result(charts,mapped)


def assert_unedited():
    for filename,report in [('rh_pir_freighter.cmp','build.json'),('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
        data=json.loads((PREVIOUS/report).read_text())
        assert f.digest(PREVIOUS/filename)==data['cmp_sha256'],f'{filename} manually edited; preserve changes first.'


def prepare():
    assert_unedited();OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    result=[]
    for ob in data['objects']:
        side=-1 if '-1' in ob['name'] else 1
        if ob['name'].startswith('Engine casing'):ob=engine(side)
        elif ob['name'].startswith('Rear engine transition'):ob=rear_transition(side)
        elif ob['name'].startswith('Faceted shoulder'):
            # The old vent floor (2.60) crossed the housing's back wall (2.62).
            # Leave a real .03-thick web behind the blind pocket instead.
            for g in ob['groups']:
                a=np.array(g['corners'],float)
                mask=np.isclose(abs(a[:,:,0]),2.60,atol=1e-5)
                a[:,:,0][mask]=side*2.65
                normals=np.cross(a[:,1,:3]-a[:,0,:3],a[:,2,:3]-a[:,0,:3])
                lengths=np.linalg.norm(normals,axis=1)
                assert lengths.min()>1e-10
                a[:,:,3:6]=(normals/lengths[:,None])[:,None,:]
                g['corners']=a
        result.append(ob)
    data['objects']=result
    (OUT/'raw_geometry.json').write_text(json.dumps(data,separators=(',',':'),default=lambda a:a.tolist()),encoding='utf8')
    (OUT/'engine_geometry_check.json').write_text(json.dumps(ENGINE_REPORT,indent=2),encoding='utf8')
    print('PREPARED',OUT/'raw_geometry.json')


def main():
    assert_unedited();configure()
    rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp'
    rig.material_map=lambda name,gs:engine_map(name,gs) if name.startswith('Engine casing') else region_map(name,gs)
    rig.main(OUT/'mechanical_geometry.json')
    engines=json.loads((OUT/'engine_geometry_check.json').read_text())
    rig.dump('engine_check.json',dict(engines=engines,cmp_sha256=f.digest(rig.DEST),installed=False))
    rig.dump('uv_layout.json',dict(cmp_sha256=f.digest(rig.DEST),regions=REPORT,
        dark_cavities='pir_r_panel02_2562side / native hump material',vent_well='pir_r_panel01_256D',
        brown_raised_sides='pir_r_panel01_256D',contour='continuous arc length; panel03 outer belt + red front rim',
        source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),installed=False))
    previous.OUT=OUT;previous.open_review()
    print('UV_DETAIL_READY',OUT)


if __name__=='__main__':
    prepare() if '--prepare' in sys.argv else main()
