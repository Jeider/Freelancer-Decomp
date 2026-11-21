"""Q13 native-scale small UV patches. Preserve form, mechanics and external MAT."""
import collections
import json
import math
import numpy as np
import rh_freighter_rig_build as rig

f,q=rig.f,rig.q
OUT=rig.OUT.parent/'uv_02'
SOURCE_GEOMETRY=rig.OUT/'mechanical_geometry.json'
P,R,D,G,H=rig.P,rig.R,rig.RD,rig.G,rig.HOLD
S=f.mesh.crc('pir_r_panel03_256')
REPORT=[]

# Pixel-authored atlas regions (native V runs top to bottom). No new textures.
# panel03 is the small interlocking skin; panel01 supplies light rolled edges;
# panel02 supplies red inserts, mechanisms and shadowed pockets.
PATCHES={
    'rim':[(P,(.017,.165,.497,.251))],
    'roof':[(P,(129/255,220/255,1.,1.))], # exact original baydoor region
    'light':[(P,(.508,.863,.998,.998)),(P,(.126,.863,.498,.998))],
    'skin':[(S,(.002,.002,.334,.499)),(S,(.337,.002,.665,.499)),
            (S,(.669,.002,.998,.499)),(S,(.002,.502,.434,.712)),
            (S,(.002,.717,.219,.998)),(S,(.668,.633,.869,.998))],
    'skinwide':[(S,(.002,.502,.434,.712)),(S,(.669,.504,.997,.627))],
    'red':[(R,(.344,.323,.658,.464))],
    'dark':[(D,(.667,.006,.997,.207)),(D,(.668,.218,.857,.488))],
    'inside':[(H,(.02,.02,.98,.98))],
    'button':[(R,(.670,.008,.992,.488))],
}


def clip(poly,axis,bound,greater):
    out=[]
    for a,b in zip(poly,np.roll(poly,-1,axis=0)):
        da=a[axis]-bound;db=b[axis]-bound
        ia=da>=-1e-10 if greater else da<=1e-10
        ib=db>=-1e-10 if greater else db<=1e-10
        if ia:out.append(a)
        if ia!=ib:out.append(a+(b-a)*(-da/(db-da)))
    return np.array(out)


def atlas_chart(values,family,cell,seed=0,rotate=False,exact=False,min_area=1e-9):
    """Clip source triangles in chart space; interpolate XYZ, never move surface."""
    coords=np.concatenate([co for _,co in values]);origin=coords.min(0)
    if rotate:
        _,e=np.linalg.eigh((coords-coords.mean(0)).T@(coords-coords.mean(0)))
        u=e[:,-1]
        if u[np.argmax(abs(u))]<0:u=-u
        basis=np.column_stack((u,[-u[1],u[0]]))
        values=[(tri,co@basis) for tri,co in values];coords=np.concatenate([co for _,co in values]);origin=coords.min(0)
    span=coords.max(0)-origin
    count=np.maximum(1,np.ceil((span-1e-6)/cell).astype(int));step=np.maximum(span/count,1e-5)
    patches=PATCHES[family];result=collections.defaultdict(list);used={};area=0.
    for tri,co in values:
        c0=np.maximum(0,np.floor((co.min(0)-origin)/step-1e-8).astype(int))
        c1=np.minimum(count-1,np.floor((co.max(0)-origin)/step+1e-8).astype(int))
        for j in range(c0[1],c1[1]+1):
            for i in range(c0[0],c1[0]+1):
                lo=origin+np.array([i,j])*step;hi=lo+step
                poly=np.concatenate((tri,co),axis=1)
                for axis,bound,ge in [(8,lo[0],True),(8,hi[0],False),(9,lo[1],True),(9,hi[1],False)]:
                    if len(poly)<3:break
                    poly=clip(poly,axis,bound,ge)
                if len(poly)<3:continue
                # Alternate actual neighboring native panels, not random colours.
                mid,box=patches[(i+2*j+seed)%len(patches)];box=np.array(box)
                avail=box[2:]-box[:2]
                scale=min(avail/step)
                # Fit square/vertical cells to appropriate panel03 fields.
                if family=='skin':
                    scores=[abs(math.log(max((b[2]-b[0])/(b[3]-b[1]),1e-8)/(step[0]/step[1]))) for _,b in patches]
                    best=min(scores);candidates=[k for k,s in enumerate(scores) if s<best+.45]
                    mid,box=patches[candidates[(i+j+seed)%len(candidates)]];box=np.array(box);avail=box[2:]-box[:2];scale=min(avail/step)
                uv=(poly[:,8:10]-(lo+hi)/2)*scale+(box[:2]+box[2:])/2
                if exact:uv=(poly[:,8:10]-lo)/step*avail+box[:2]
                poly[:,6:8]=uv
                for k in range(1,len(poly)-1):
                    t=poly[[0,k,k+1],:8].copy()
                    ar=np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))/2
                    if ar<min_area:continue
                    t[:,3:6]/=np.linalg.norm(t[:,3:6],axis=1)[:,None]
                    result[mid].append(t);area+=ar
                    used[(i,j)]=dict(material=int(mid),scale=float(scale),physical_size=step.tolist(),box=box.tolist())
    return result,dict(family=family,area=area,patches=list(used.values()))


def plane_coords(xyz,n):
    # Orthonormal plane basis: sloped surfaces keep their physical UV scale.
    normal=n.copy()
    if normal[np.argmax(abs(normal))]<0:normal=-normal
    base=np.eye(3)[int(np.argmin(abs(normal)))];u=np.cross(normal,base);u/=np.linalg.norm(u);v=np.cross(normal,u)
    # Favor longitudinal direction for hull strips (rather than world-axis projection).
    if abs(v[2])>abs(u[2]):u,v=v,-u
    if u[np.argmax(abs(u))]<0:u,v=-u,-v
    return np.column_stack((xyz@u,xyz@v))


def material_map(name,groups):
    if name.startswith('Original'):return [dict(g,corners=np.array(g['corners'],float)) for g in groups]
    charts=collections.defaultdict(list);direct=collections.defaultdict(list)
    for g in groups:
        for tri in np.array(g['corners'],float):
            xyz=tri[:,:3];p=xyz.mean(0);n=np.cross(xyz[1]-xyz[0],xyz[2]-xyz[0]);n/=np.linalg.norm(n)
            role=g['material'];family='skin';cell=(1.85,1.85);rotate=False;exact=False
            key=('plane',tuple(n.round(4)),round(float(n@p),4),role)
            co=plane_coords(xyz,n)
            if role in (3,4):family='dark';cell=(1.45,.95)
            if role==2:family='rim';cell=(2.55,.44);rotate=True
            if name.startswith(('Foredeck','Rear engine')):
                if role==1:family='light';cell=(2.50,.78)
            if name.startswith('Continuous hull'):
                interior=(abs(abs(p[0])-2.39)<.001 or abs(p[1]+3.10)<.001 or abs(p[2]+3.72)<.001 or abs(p[2]-5.72)<.001)
                if interior and abs(p[0])<=2.391 and -3.101<=p[1]<3.9 and -3.721<=p[2]<=5.721:
                    family='inside';cell=(2.8,2.8)
                elif n[1]>.5:family='light';cell=(2.5,.78)
                elif n[1]<-.5 and role==1:family='skin';cell=(2.2,1.6)
            if name.startswith('Ventral'):family='rim';cell=(2.55,.44);rotate=True
            if name.startswith('Lower diagonal'):
                if role==1:family='skin';cell=(2.3,1.9)
            if name.startswith('Recess relief'):
                if abs(n[0])>.85 and n[0]*p[0]>0:
                    co=xyz[:,[2,1]]
                    if 'Aft' in name:family='red';cell=(1.65,.74)
                    else:family='skin';cell=(1.7,1.45)
                elif role==1:family='dark';cell=(1.5,.95)
            if name.startswith('Intake vane'):family='rim';cell=(2.55,.44);rotate=True
            if name.startswith('Curved roof'):
                r=np.hypot(xyz[:,1]-q.SHELL_Y,xyz[:,2]-q.SHELL_Z)
                angle=np.arctan2(xyz[:,2]-q.SHELL_Z,xyz[:,1]-q.SHELL_Y)
                if n@np.array([0,p[1]-q.SHELL_Y,p[2]-q.SHELL_Z])<0 and r.mean()<4.4:
                    family='inside';cell=(2.5,2.5);co=np.column_stack((xyz[:,0],angle*4.34));key=('roof interior',)
                elif abs(p[0])<1.83 and abs(n[0])<.1:
                    # Original roof = repeated rolled strips, ~0.115 UV/unit.
                    # Rebuild that layout on the new continuous shutter.
                    family='roof';cell=(3.7,1.06);co=np.column_stack((xyz[:,0],angle*4.51));key=('native roof strips',);exact=True
                else:
                    family='rim';cell=(2.55,.44);co=np.column_stack((angle*4.6,xyz[:,0]));key=('roof rails',round(abs(p[0]),2),int(np.sign(p[0])))
            elif name.startswith('Stepped circular'):
                r=np.hypot(xyz[:,1]-q.SHELL_Y,xyz[:,2]-q.SHELL_Z)
                angle=np.arctan2(xyz[:,2]-q.SHELL_Z,xyz[:,1]-q.SHELL_Y)
                profile=np.array([(4.909,2.35),(4.909,2.72),(4.80,2.93),(4.42,2.93),
                    (4.25,2.74),(3.12,2.67),(3.02,2.82),(2.78,2.82),(2.61,2.63),(0,2.63)])
                rx=np.column_stack((r,abs(xyz[:,0])))
                errors=[]
                for a,b in zip(profile,profile[1:]):
                    t=np.clip((rx-a)@(b-a)/np.dot(b-a,b-a),0,1)
                    errors.append(np.linalg.norm(rx-(a+t[:,None]*(b-a)),axis=1).max())
                band=int(np.argmin(errors))
                if abs(n[0])>.8 and (r.mean()<2.61 or n[0]*p[0]<0):
                    co=xyz[:,[2,1]];family='skin';cell=(1.8,1.8);key=('cheek plane',round(p[0],2))
                elif errors[band]<.02 and band<8:
                    a,b=profile[band:band+2];delta=b-a;length=np.linalg.norm(delta)
                    along=(rx-a)@delta/length
                    co=np.column_stack((angle*(a[0]+b[0])/2,along))
                    family='skinwide' if band==4 else 'rim';cell=(1.9,1.9) if band==4 else (2.55,.44)
                    # Use the physical band, NOT the triangle's mean radius.
                    # Boolean subdivisions must share the same chart origin.
                    key=('cheek profile band',band)
                else:
                    co=plane_coords(xyz,n);family='dark' if role==3 else 'rim';cell=(1.45,.95) if role==3 else (2.55,.44);rotate=True
            elif name.startswith('Engine casing'):
                cx=math.copysign(2.08,p[0]);cy=-.28;r=np.hypot(xyz[:,0]-cx,xyz[:,1]-cy)
                if abs(n[2])>.95 and abs(p[2]-12.158)<.001 and r.max()<1.09:
                    t=tri.copy();t[:,6:8]=(xyz[:,[0,1]]-[cx,cy])/2.16+.5;direct[G].append(t);continue
                if abs(n[2])<.95:
                    angle=np.unwrap(np.arctan2(xyz[:,1]-cy,xyz[:,0]-cx))
                    if angle.mean()>math.pi:angle-=2*math.pi
                    band=int(np.searchsorted([7.15,7.85,8.17,10.35,10.87,11.63,11.84,12.158],p[2]))
                    co=np.column_stack((angle*1.86,xyz[:,2]));key=('engine barrel',band)
                    family='light';cell=(2.6,.78)
                    if 10.87<p[2]<11.64:family='skin';cell=(1.9,1.1)
                else:family='rim';cell=(2.55,.44);rotate=True
            elif name.startswith(('New transverse','Cylinder socket')):
                if abs(n[0])>.85 and n[0]*p[0]>0 and name.startswith('New'):
                    co=xyz[:,[2,1]];family='button';cell=(3,3)
                elif role in (3,4):family='dark';cell=(1.45,.95)
                else:family='rim';cell=(2.55,.44);rotate=True
                if name.startswith('New transverse') and abs(n[0])<.85:
                    index=int(name.split()[-1])-1;cz=[-2.76,.66,3.94][index];radius=[.72,1.11,.72][index]
                    a=np.unwrap(np.arctan2(xyz[:,2]-cz,xyz[:,1]-2.08))
                    if a.mean()>math.pi:a-=2*math.pi
                    co=np.column_stack((a*radius,abs(xyz[:,0])));key=('button wrap',role);rotate=False
            charts[(family,cell,rotate,exact,key)].append((tri,co))
    stats=[]
    for ix,((family,cell,rotate,exact,key),values) in enumerate(charts.items()):
        # Large generic coplanar rims: align the continuous direction once,
        # then repeat whole strip patches at a stable physical length.
        result,stat=atlas_chart(values,family,cell,seed=0,rotate=rotate,exact=exact)
        for mid,ts in result.items():direct[mid].extend(ts)
        stats.append(stat)
    old=np.concatenate([g['corners'] for g in groups]);new=np.concatenate(list(direct.values()))
    area=lambda ts:np.linalg.norm(np.cross(ts[:,1,:3]-ts[:,0,:3],ts[:,2,:3]-ts[:,0,:3]),axis=1).sum()/2
    assert np.isclose(area(old),area(new),rtol=2e-6),(name,area(old),area(new))
    assert np.allclose(old[:,:,:3].min((0,1)),new[:,:,:3].min((0,1)))
    assert np.allclose(old[:,:,:3].max((0,1)),new[:,:,:3].max((0,1)))
    REPORT.append(dict(object=name,original_triangles=len(old),triangles=len(new),surface_area=float(area(new)),charts=stats))
    return [dict(material=mid,corners=np.array(ts),unused=204) for mid,ts in direct.items()]


def main():
    prior=json.loads((rig.OUT/'build.json').read_text(encoding='utf8'))
    assert f.digest(rig.DEST)==prior['cmp_sha256'],'Prototype was manually edited; preserve its HPs before rebuilding.'
    rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp';rig.material_map=material_map
    rig.main(SOURCE_GEOMETRY)
    rig.dump('uv_layout.json',dict(source_geometry=str(SOURCE_GEOMETRY),form_unchanged=True,objects=REPORT))
    areas=collections.Counter()
    for ob in REPORT:
        for c in ob['charts']:areas[c['family']]+=c['area']
    print('UV_FAMILIES_AREA',dict(areas));print('UV_PATCHES',sum(len(c['patches']) for ob in REPORT for c in ob['charts']))

if __name__=='__main__':main()
