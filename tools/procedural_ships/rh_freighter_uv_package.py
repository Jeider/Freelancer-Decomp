"""Q13 review package: pale local panels, native hump UV, red vents, separate nozzles.

Offline authoring only. The animated prototype preserves native zero pose;
review_open is a separate static viewing copy with extended side units.
"""
import collections
import copy
import json
import math
import secrets
import struct
import numpy as np
import rh_freighter_uv_refine as uv

rig,f,q=uv.rig,uv.f,uv.q
BASE=rig.OUT
PREVIOUS=BASE.parent/'engines_03'
OUT=BASE.parent/'uv_04'
BROWN=f.mesh.crc('pir_r_panel01_256D')
PALE=(.510,.256,.996,.855)
HATCH=(.128,.254,.502,.562)
ENGINE_REPORT=[]
REPORT=[]
NATIVE=[]
ORIGINAL_CHART=uv.atlas_chart


def configure():
    # Keep separate whole painted panels, not texture resets on every triangle.
    uv.PATCHES.update(skin=[(uv.P,PALE)],skinwide=[(uv.P,PALE)],
        light=[(uv.P,PALE)],red=[(uv.P,PALE)],
        dark=[(BROWN,PALE)],hatch=[(uv.P,HATCH)],
        vent=[(uv.R,(.344,.323,.658,.464))],
        belly=[(uv.P,PALE)])
    def chart(values,family,cell,**kw):
        if family in ('skin','light','red'):cell=(2.8,2.8)
        if family=='skinwide':cell=(2.6,1.9)
        if family=='dark':cell=(2.5,2.5)
        return ORIGINAL_CHART(values,family,cell,**kw)
    uv.atlas_chart=chart
    source=json.loads((q.ROOT/'out/ship_design/rh_freighter/references/uv_native/native_geometry.json').read_text())
    for e in source:
        if e['part']!='Root' or e['material'] not in ('pir_r_panel01_2562side','pir_r_panel02_2562side'):continue
        for t in np.array(e['corners']):
            p=t[:,:3];n=np.cross(p[1]-p[0],p[2]-p[0]);n/=max(np.linalg.norm(n),1e-12)
            if p[:,0].min()>2.35 and p[:,1].min()>4.10 and n[0]>.6:
                xy=p[:,[2,1]]
                matrix=np.column_stack((xy,np.ones(3)))
                if abs(np.linalg.det(matrix))>1e-8:
                    NATIVE.append((f.mesh.crc(e['material']),xy,np.linalg.solve(matrix,t[:,6:8])))
    assert len(NATIVE)==49,len(NATIVE)


def triangles(poly):
    for i in range(1,len(poly)-1):
        t=poly[[0,i,i+1],:8].copy()
        if np.linalg.norm(np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]))<1e-8:continue
        t[:,3:6]/=np.linalg.norm(t[:,3:6],axis=1)[:,None]
        yield t


def project_native_arch(groups):
    """Clip target surface at native UV seams in side projection, no bitmap bake."""
    mapped=collections.defaultdict(list);fallback=collections.defaultdict(list)
    transferred=0
    for g in groups:
        for t in np.array(g['corners'],float):
            n=np.cross(t[1,:3]-t[0,:3],t[2,:3]-t[0,:3]);n/=np.linalg.norm(n)
            if n[0]*t[:,0].mean()<=0 or abs(n[0])<.35:
                fallback[g['material']].append(t);continue
            remain=[t]
            for mid,xy,transform in NATIVE:
                sign=np.sign(np.linalg.det(np.column_stack((xy,np.ones(3)))))
                newremain=[]
                for poly in remain:
                    inside=poly
                    for a,b in zip(xy,np.roll(xy,-1,axis=0)):
                        if len(inside)<3:break
                        v=b-a;co=inside[:,[2,1]]-a
                        distance=(v[0]*co[:,1]-v[1]*co[:,0])*sign
                        augmented=np.column_stack((inside,distance))
                        outside=uv.clip(augmented,8,0,False)
                        if len(outside)>=3:newremain.append(outside[:,:8])
                        inside=uv.clip(augmented,8,0,True)
                        if len(inside):inside=inside[:,:8]
                    if len(inside)>=3:
                        inside[:,6:8]=np.column_stack((inside[:,[2,1]],np.ones(len(inside))))@transform
                        ts=list(triangles(inside));mapped[mid].extend(ts);transferred+=len(ts)
                remain=newremain
                if not remain:break
            for poly in remain:fallback[g['material']].extend(triangles(poly))
    if fallback:
        for g in uv.material_map('Stepped circular shoulder',pack(fallback)):mapped[g['material']].extend(g['corners'])
    REPORT.append(dict(region='hump native side projection',triangles=transferred,source_faces=len(NATIVE)))
    return pack(mapped)


def pack(groups):
    return [dict(material=int(mid),corners=np.array(ts),unused=204) for mid,ts in groups.items() if len(ts)]


def special_map(name,groups):
    if name.startswith('Stepped circular'):return project_native_arch(groups)
    if not name.startswith(('Continuous hull','Ventral','Intake vane','Foredeck')):
        return uv.material_map(name,groups)
    charts=collections.defaultdict(list);fallback=collections.defaultdict(list);mapped=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];c=p.mean(0);n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)
            family=None;cell=(2.8,2.8);exact=False;rotate=False;co=uv.plane_coords(p,n)
            if name.startswith('Intake vane'):
                family='vent';cell=(2.5,.40);rotate=True
            elif name.startswith('Ventral'):
                if n[1]<-.9:
                    family='hatch';cell=(5,5);co=p[:,[0,2]];exact=True
                else:family='dark' if n[1]>.5 else 'rim';cell=(2.5,.44);rotate=family=='rim'
            elif name.startswith('Foredeck'):
                if abs(n[0])>.7 and n[0]*c[0]>0:family='hatch';cell=(1.9,2.0)
            else:
                if c[2]<-3.8 and n[1]>.5:
                    # Main hood and short raised service panel have independent charts.
                    height=1.38+(c[2]+7.62)*(3.81-1.38)/3.52
                    raised=abs(c[1]-height-.18)<1e-4 and -5.9<c[2]<-4.84
                    family='hatch' if raised else 'light'
                    co=np.column_stack((p[:,0],p[:,2]*math.hypot(1,(3.81-1.38)/3.52)))
                    cell=(1.8,1.8) if raised else (2.5,2.6)
                elif n[1]<-.5 and c[1]<-3.15:
                    # Native belly rhythm: pale broad fields, dark channel floors.
                    family='dark' if abs(c[1]+3.40)<.04 else 'belly'
                    co=p[:,[0,2]];cell=(2.8,2.8)
                elif -3.7<c[1]<-3.12 and abs(n[2])>.5 and abs(c[0])<2.8:
                    family='dark';cell=(2.5,2.5)
            if family:
                key=(family,cell,exact,rotate,tuple(n.round(5)),round(float(n@c),5))
                charts[key].append((t,co))
            else:fallback[g['material']].append(t)
    if fallback:
        for g in uv.material_map(name,pack(fallback)):mapped[g['material']].extend(g['corners'])
    for (family,cell,exact,rotate,_,_),values in charts.items():
        result,stat=uv.atlas_chart(values,family,cell,exact=exact,rotate=rotate)
        for mid,ts in result.items():mapped[mid].extend(ts)
        REPORT.append(dict(object=name,**stat))
    return pack(mapped)


def engine(side):
    cx=side*2.08;cy=-.28;angles=(np.arange(12)+.5)*2*np.pi/12
    def ring(z,w,h):
        return np.column_stack((cx+w*np.cos(angles),cy+h*np.sin(angles),np.full(12,z)))
    # Distinct forward shoulder, main pod, narrow neck and projecting nozzle collar.
    profile=[(6.82,.98,1.00),(7.95,1.58,1.47),(8.30,1.72,1.60),
        (9.83,1.72,1.60),(10.40,1.30,1.22),(10.40,1.04,.98),
        (10.98,1.04,.98),(11.10,1.21,1.12),(12.158,1.21,1.12)]
    loops=[ring(*p) for p in profile];b=q.B()
    for i,(a,c) in enumerate(zip(loops,loops[1:])):
        b.bridge(a,c,3 if i in (4,5) else 2 if i in (1,6) else 1)
    b.face(loops[0],3,normal=[0,0,-1])
    mouth=ring(12.158,.98,.89);floor=ring(11.15,.84,.76)
    b.bridge(loops[-1],mouth,2);b.bridge(mouth,floor,3,inner=True);b.face(floor,7,normal=[0,0,1])
    gs,closure=q.coherent(b.groups())
    ENGINE_REPORT.append(dict(side=side,center_xy=[cx,cy],profile=profile,mouth_z=12.158,exhaust_z=11.15,
        recess_depth=1.008,closure=closure,geometry_triangles=sum(len(g['corners']) for g in gs)))
    return dict(name=f'Engine casing - separate recessed nozzle {side:+}',groups=gs,closed=True)


def map_engine(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];cx=np.sign(p[:,0].mean())*2.08
            if g['material']==7:
                t[:,6:8]=(p[:,[0,1]]-[cx,-.28])/1.80+.5;mapped[uv.G].append(t);continue
            angle=np.unwrap(np.arctan2((p[:,1]+.28)/1.60,(p[:,0]-cx)/1.72))
            if angle.mean()>math.pi:angle-=2*math.pi
            family={1:'light',2:'rim',3:'dark'}[g['material']]
            station=round(p[:,2].min(),4),round(p[:,2].max(),4)
            if station[0]==station[1]:
                co=p[:,[0,1]];key=(family,station,'end');cell=(2.8,2.8)
            else:
                co=np.column_stack((angle*1.6,p[:,2]));key=(family,station,'barrel');cell=(2.4,2.0)
                if family=='rim':cell=(2.55,.44)
            charts[(key,cell)].append((t,co))
    for ((family,station,kind),cell),values in charts.items():
        result,stat=uv.atlas_chart(values,family,cell)
        for mid,ts in result.items():mapped[mid].extend(ts)
        REPORT.append(dict(object=name,**stat))
    return pack(mapped)


def open_review():
    header,nodes=f.mesh.read_tree(rig.DEST.read_bytes())
    before=copy.deepcopy(nodes);tr,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    flat={p.lower():n for p,n in f.mesh.walk(nodes)}
    for path,node in flat.items():
        if not path.endswith('/cons/pris'):continue
        raw=bytearray(node.blob)
        assert len(raw)%208==0
        for at in range(0,len(raw),208):
            values=np.frombuffer(raw,dtype='<f4',count=20,offset=at+128).copy()
            values[:3]+=values[15:18]
            raw[at+128:at+208]=values.tobytes()
        node.blob=bytes(raw)
    nodes[0].children=[n for n in nodes[0].children if n.name.lower()!='animation']
    poses,_=f.audit.transforms(nodes)
    assert all(np.allclose(poses[k][0],v[0]) and np.allclose(poses[k][1],v[1]) for k,v in tr.items())
    salt=secrets.token_hex(6);resources=q.salted(nodes,salt)
    dest=OUT/'rh_pir_freighter_review_open.cmp';dest.write_bytes(f.mesh.write_tree(header,nodes))
    _,decoded=f.mesh.read_tree(dest.read_bytes())
    assert not any(n.name.lower() in ('animation','material library','texture library') for _,n in f.mesh.walk(decoded))
    # Local mesh data and HP coordinates are the same; only review constructs move.
    for old,new in resources.items():
        def hp(ns,file):return {p.split('/Hardpoints/',1)[-1]:n.blob for p,n in f.mesh.walk([f.mesh.child(ns[0],file)]) if '/Hardpoints/' in p}
        if old.lower().endswith('.3db'):assert hp(before,old)==hp(decoded,new)
    rig.dump('review_open_check.json',dict(cmp=str(dest),cmp_sha256=f.digest(dest),salt=salt,
        resources=resources,pose='flight / extended',runtime_animation_removed_for_static_review=True,
        matches_animated_flight_transforms=True,hardpoint_local_bytes_preserved=True,installed=False))


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    previous=json.loads((PREVIOUS/'build.json').read_text())
    assert f.digest(PREVIOUS/'rh_pir_freighter.cmp')==previous['cmp_sha256'],'Prior prototype edited: preserve manual HP edits first.'
    configure()
    data=json.loads((BASE/'mechanical_geometry.json').read_text())
    data['objects']=[engine(-1 if '-1' in o['name'] else 1) if o['name'].startswith('Engine casing') else o for o in data['objects']]
    path=OUT/'mechanical_geometry.json'
    path.write_text(json.dumps(data,separators=(',',':'),default=lambda a:a.tolist()),encoding='utf8')
    rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp'
    rig.material_map=lambda name,gs:map_engine(name,gs) if name.startswith('Engine casing') else special_map(name,gs)
    rig.main(path)
    rig.dump('engine_check.json',dict(engines=ENGINE_REPORT,cmp_sha256=f.digest(rig.DEST),installed=False))
    rig.dump('uv_layout.json',dict(cmp_sha256=f.digest(rig.DEST),objects=REPORT,
        pale_texture='pir_r_panel01.tga',dark_material='pir_r_panel01_256D',
        dark_colour=[.470588,.3490196,.09411765],native_hump_faces=len(NATIVE),
        red_vent_material='pir_r_panel02_256',installed=False))
    open_review()
    print('UV_PACKAGE_READY',OUT)


if __name__=='__main__':main()
