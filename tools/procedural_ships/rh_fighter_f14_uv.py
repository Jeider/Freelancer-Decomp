"""F14 LOD0 material/UV prototype on the accepted F14/03 geometry.

Native small atlas patches, semantic recesses and physically unfolded profiles.
Offline only: no game writes, LODs, HP changes, SUR, or final animation export.
"""
import collections
import copy
import hashlib
import json
import math
import shutil
from pathlib import Path
import numpy as np
import rh_fighter_f14_form as model
import rh_fighter_f14_detail as shape
import rh_freighter_uv_refine as uv
import uv_mesh_seams

f=model.f
SOURCE=model.TOPIC/'prototypes/f14_03/geometry.json'
OUT=model.TOPIC/'prototypes/f14_uv_01'
P,R,BROWN,P3,DARK=shape.P,shape.R,shape.D,shape.P3,shape.DARK
GREEN=f.mesh.crc('pir_r_panel02_2562side')
HOLD=f.mesh.crc('metal03D')
GRILL=f.mesh.crc('engine_grill01')
WARNING=f.mesh.crc('weaponplate')
REPORT=[]

# Native V runs downwards in these boxes. Artwork boundaries were inspected
# directly on the source atlases, not inferred from material names.
PATCHES={
    'pale':[(P,(.510,.272,.995,.852))],
    'pale_strip':[(P,(.510,.865,.995,.992))],
    'pale_edge':[(P,(.020,.167,.495,.250))],
    'red':[(R,(.345,.325,.655,.463))],
    'red_plain':[(R,(.368,.347,.625,.437))],
    'red_tall':[(R,(.024,.046,.146,.447))],
    'green':[(GREEN,(.670,.010,.994,.474))],
    'brown':[(BROWN,(.510,.272,.995,.852))],
    'brown_strip':[(BROWN,(.510,.865,.995,.992))],
    'skin':[(P3,(.006,.005,.332,.495)),(P3,(.675,.008,.990,.493))],
    'skin_strip':[(P3,(.006,.503,.430,.705)),(P3,(.670,.505,.992,.621))],
    'cargo':[(HOLD,(.02,.02,.98,.98))],
    'hazard':[(WARNING,(.027,.027,.973,.105))],
}


def normal(t):
    p=t[:,:3];n=np.cross(p[1]-p[0],p[2]-p[0]);return n/max(np.linalg.norm(n),1e-12)


def key_plane(t):
    n=normal(t);return tuple(n.round(3)),round(float(n@t[0,:3]),3)


def arc_angle(p,cx,cy):
    a=np.arctan2(p[:,1]-cy,p[:,0]-cx)+np.pi/2
    a=np.unwrap(a)
    a-=math.floor(float(a.mean())/(2*np.pi))*2*np.pi
    return a


def profile_uv(p,cx,cy,profile):
    """Match the entire triangle to a physical ring band, then unfold it.

    Includes radial shoulders: width is profile arclength, never axial Z alone.
    """
    radius=np.hypot(p[:,0]-cx,p[:,1]-cy);zr=np.column_stack((p[:,2],radius))
    prof=np.asarray(profile,float);lengths=np.linalg.norm(np.diff(prof,axis=0),axis=1)
    starts=np.r_[0,np.cumsum(lengths)]
    candidates=[]
    for i,(a,b) in enumerate(zip(prof,prof[1:])):
        d=b-a;l=lengths[i];t=(zr-a)@d/(l*l)
        error=np.linalg.norm(zr-(a+np.clip(t,0,1)[:,None]*d),axis=1).max()
        candidates.append((error,i,t))
    error,i,parameter=min(candidates,key=lambda v:v[0])
    a,b=prof[i:i+2];angle=arc_angle(p,cx,cy)
    return error,i,np.column_stack((angle*(a[1]+b[1])/2,starts[i]+parameter*lengths[i]))


def contour_uv(p,poly,depth):
    """Continuous distance along a modeled flank rim, then across its section."""
    zy=p[:,[2,1]];poly=np.array(poly);edges=np.roll(poly,-1,axis=0)-poly
    lengths=np.linalg.norm(edges,axis=1);starts=np.r_[0,np.cumsum(lengths)]
    candidates=[]
    for i,(a,d) in enumerate(zip(poly,edges)):
        t=np.clip((zy-a)@d/(lengths[i]**2),0,1)
        candidates.append((float(np.mean(np.linalg.norm(zy-(a+t[:,None]*d),axis=1))),i))
    _,i=min(candidates);a=poly[i];d=edges[i]/lengths[i]
    along=starts[i]+(zy-a)@d
    across=np.sqrt(np.linalg.norm((zy-a)-((zy-a)@d)[:,None]*d,axis=1)**2+depth**2)
    return np.column_stack((along,across))


class Mapper:
    def __init__(self,name):
        self.name=name;self.charts=collections.defaultdict(list);self.mapped=collections.defaultdict(list)

    def chart(self,t,family,co,cell=(1.7,1.7),key=None,exact=False):
        p=t[:,:3];a=p[1]-p[0];b=p[2]-p[0];length=np.linalg.norm(a)
        bx=float(b@a)/max(length,1e-15);by=np.linalg.norm(np.cross(a,b))/max(length,1e-15)
        if length>1e-8 and by>1e-8:
            x=co[1]-co[0];y=co[2]-co[0]
            sigma=np.linalg.svd(np.column_stack((x/length,(y-x*bx/length)/by)),compute_uv=False)
            if sigma[1]<1e-7 or sigma[0]/sigma[1]>6:
                # A rim's end wall needs its own section chart, never a collapsed
                # longitudinal/cylindrical projection. Same physical plane key.
                co=uv.plane_coords(p,normal(t));key=('section wall',key_plane(t));exact=False
        self.charts[(family,tuple(cell),key,exact)].append((t,co))

    def plane(self,t,family,cell=(1.7,1.7),key=None,exact=False):
        self.chart(t,family,uv.plane_coords(t[:,:3],normal(t)),cell,key or key_plane(t),exact)

    def fixed(self,t,mat,co,lo,hi,box):
        t=t.copy();lo=np.array(lo);hi=np.array(hi);box=np.array(box)
        t[:,6:8]=box[:2]+(co-lo)/(hi-lo)*(box[2:]-box[:2]);self.mapped[mat].append(t)

    def keep(self,t,mat):self.mapped[mat].append(t.copy())

    def finish(self):
        for (family,cell,key,exact),values in self.charts.items():
            groups,report=uv.atlas_chart(values,family,cell,exact=exact,min_area=1e-15)
            for mat,ts in groups.items():self.mapped[mat].extend(ts)
            REPORT.append(dict(object=self.name,chart=str(key),**report))
        return [dict(material=mat,corners=np.array(ts)) for mat,ts in self.mapped.items() if ts]


def flank(m,t,role):
    p=t[:,:3];n=normal(t);depth=np.array([shape.side_x(z,y)-abs(x) for x,y,z in p])
    if role==DARK:m.keep(t,DARK)
    elif role==R:m.chart(t,'red_plain',np.column_stack((-p[:,2],-p[:,1])),(100,100),'front donor cheek',True)
    elif np.max(abs(depth))<3e-5:
        m.chart(t,'pale',np.column_stack((-p[:,2],-p[:,1])),(1.7,1.45),'outer pale field')
    elif role==BROWN and np.max(abs(depth-.32))<3e-5:
        m.chart(t,'green',np.column_stack((-p[:,2],-p[:,1])),(1.30,1.85),'main recessed backing')
    elif role==BROWN:
        m.plane(t,'brown_strip',(1.6,.36))
    else:
        # Thin stepped rim and wide structural returns have different charts.
        if depth.max()<.105 and p[:,2].min()>-3.4 and p[:,2].max()<1.8:
            co=contour_uv(p,shape.WELL,depth)
            m.chart(t,'pale_edge',co,(2.0,.30),'well border')
        elif depth.max()>.8:
            m.chart(t,'skin_strip',contour_uv(p,shape.SIDE,depth),(1.8,.85),'outer perimeter section')
        else:m.plane(t,'pale_edge',(1.8,.30))


def wing_field_coordinates(p,field):
    outline=np.array([[1.77,-.80],[5.08,-3.40],[5.36,-3.28],[5.36,-2.19],
                      [2.46,.86],[1.77,1.02]])
    lo,hi=[(1.94,3.12),(3.16,4.46),(4.50,5.22)][field]
    poly=shape.clip_poly(shape.clip_poly(outline,0,lo,True),0,hi,False)
    poly=shape.offset(shape.offset(poly,.065),.025)
    xmin,xmax=poly[:,0].min(),poly[:,0].max();result=[]
    for x,z in p[:,[0,2]]:
        x=abs(x);zs=[]
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            if abs(a[0]-b[0])<1e-8:
                if abs(x-a[0])<2e-5:zs.extend((a[1],b[1]))
            elif min(a[0],b[0])-2e-5<=x<=max(a[0],b[0])+2e-5:
                zs.append(a[1]+(b[1]-a[1])*(x-a[0])/(b[0]-a[0]))
        assert zs,(field,x,z)
        low,high=min(zs),max(zs)
        result.append([(x-xmin)/(xmax-xmin),(z-low)/max(high-low,1e-5)])
    return np.array(result)


def wing(m,t,role):
    # Split only UV space at the hazard band. Position/normals remain interpolated
    # on the accepted triangle, with no change of silhouette or cutout depth.
    s=1 if t[:,0].mean()>0 else -1
    local=t.copy();local[:,0]*=s
    for lo,hi,mark in [(0,4.68,False),(4.68,4.93,True),(4.93,10,False)]:
        poly=uv.clip(local,0,lo,True)
        if len(poly)>2:poly=uv.clip(poly,0,hi,False)
        if len(poly)<3:continue
        for i in range(1,len(poly)-1):
            a=poly[[0,i,i+1]].copy();a[:,0]*=s;p=a[:,:3];x=abs(p[:,0]);n=normal(a)
            surface=p[:,1]+1.02+.285*(x-1.77)
            u=np.array([1,-.285,-.80]);u/=np.linalg.norm(u)
            wn=np.array([.285,1,0]);wn/=np.linalg.norm(wn);v=np.cross(wn,u)
            lp=p.copy();lp[:,0]=x;co=np.column_stack((lp@u,lp@v))
            if mark and abs(n[1])<.8:
                m.plane(a,'hazard',(1.8,.23));continue
            if mark:
                # Follow the local chord along the stripe; use a whole native
                # yellow/black edge crop, not the weapon mounting hole.
                co=np.column_stack((-p[:,2]-.80*(x-4.68),x))
                m.fixed(a,WARNING,co,(1.40,4.68),(3.18,4.93),PATCHES['hazard'][0][1])
            elif abs(n[1])>.8:
                field=int(np.searchsorted([3.14,4.48],float(x.mean())))
                family='pale' if n[1]>0 else 'skin'
                if n[1]>0 and np.max(abs(surface+.038))<3e-5:
                    m.fixed(a,P,wing_field_coordinates(p,field),(0,0),(1,1),PATCHES['pale'][0][1])
                else:
                    m.chart(a,family,co,(1.8,1.65),('wing field',field,round(float(surface.mean()),3)))
            else:m.plane(a,'brown_strip',(1.8,.36))


ENGINE_PROFILE=[(1.76,.34),(1.84,.40),(2.04,.48),(2.18,.62),(2.24,.68),
    (2.36,.68),(2.39,.655),(3.12,.655),(3.15,.68),(3.27,.68),(3.42,.59),
    (3.53,.54),(3.75,.54),(3.79,.50),(4.02,.49),(4.11,.46),(4.11,.375),
    (4.03,.375),(3.99,.405),(3.89,.405),(3.83,.37),(3.58,.32)]


def engine(m,t,role,cy):
    p=t[:,:3];cx=math.copysign(model.ENGINE_X,float(p[:,0].mean()));n=normal(t)
    radius=np.hypot(p[:,0]-cx,p[:,1]-cy)
    if np.max(abs(p[:,2]-3.58))<2e-5:
        m.fixed(t,GRILL,p[:,[0,1]],(cx-.32,cy-.32),(cx+.32,cy+.32),(0,1,1,0));return
    if np.max(abs(p[:,2]-1.76))<2e-5:
        m.fixed(t,P,p[:,[0,1]],(cx-.34,cy-.34),(cx+.34,cy+.34),(.13,.85,.495,.57));return
    error,band,co=profile_uv(p,cx,cy,ENGINE_PROFILE)
    if error<.001:
        if band>=16:family='green';cell=(.65,.92)
        elif band in (5,7,12,14):family='brown_strip';cell=(1.5,.35)
        else:family='pale_strip';cell=(1.5,.42)
        m.chart(t,family,co,cell,('engine machined band',band));return
    # Actual raised curved armor fields: one chart per sector, including end cuts.
    angle=arc_angle(p,cx,cy);sector=int(math.floor(float(angle.mean())/(np.pi/2)))%4
    if np.max(abs(n[2]))>.90:
        m.plane(t,'brown_strip',(.9,.2));return
    co=np.column_stack((angle*.685,-p[:,2]))
    family='red' if role==R else 'pale'
    m.chart(t,family,co,(1.25,.55) if role==R else (1.3,1.3),('engine armor',sector,role),role==R)


def drum(m,t,role,cy):
    p=t[:,:3];n=normal(t);rad=np.hypot(p[:,0],p[:,1]-cy);z=p[:,2]
    R0=model.RADIUS;front=model.DRUM_FRONT;rear=model.DRUM_REAR
    profile=[(front,R0-.115),(front+.025,R0-.035),(front+.07,R0),(front+.13,R0),
        (front+.15,R0-.065),(rear-.15,R0-.065),(rear-.13,R0),(rear-.07,R0),
        (rear-.025,R0-.035),(rear,R0-.115)]
    error,band,co=profile_uv(p,0,cy,profile)
    if error<.001 and band!=4:
        m.chart(t,'pale_edge',co,(1.65,.29),('drum profiled rail',band));return
    if rad.min()>R0-.225:
        angle=arc_angle(p,0,cy)
        if abs(n[2])>.55:
            co=np.column_stack((angle*(R0-.12),rad));family='pale_edge'
            m.chart(t,family,co,(1.65,.29),('annular rim',round(float(z.mean()),3)));return
        sector=int(math.floor(float(angle.mean())/(np.pi/6)))%12
        co=np.column_stack((angle*(R0-.015),z))
        family='red' if role==R else 'brown' if role==BROWN else 'pale'
        m.chart(t,family,co,(1.4,.58) if role==R else (1.4,1.25),('outer drum section',sector,role),role==R);return
    if role==DARK:m.keep(t,DARK);return
    if abs(n[2])>.98:
        face=float(z.mean());sgn=1 if p[:,0].mean()>=0 else -1
        co=np.column_stack((p[:,0],-p[:,1]))
        if abs(face-3.095)<2e-5:
            m.chart(t,'green',co,(1.3,1.85),('rear deep backing',sgn));return
        if abs(face-(rear-.045))<2e-5:
            section=int(np.searchsorted([cy-.5,cy+.73],float(p[:,1].mean())))
            m.chart(t,'pale',co,(1.5,1.5),('rear web panel',section));return
        if role==R:
            m.chart(t,'red',co,(1.35,.60),('front donor red field',round(face,3)),True);return
        if role==BROWN:
            m.chart(t,'green',co,(1.3,1.85),('inset floor',round(face,3),sgn));return
        m.chart(t,'pale',co,(1.35,1.45),('drum face',round(face,3)));return
    if role==BROWN:
        m.plane(t,'brown_strip',(1.35,.35));return
    m.plane(t,'pale_edge',(1.65,.29))


def roof(m,t,role):
    p=t[:,:3];n=normal(t)
    if role==BROWN:m.plane(t,'brown_strip',(1.6,.3));return
    # Shared longitudinal coordinates retain phase through all slope changes.
    zgrid=np.array([-4.25,-3.05,-.55,1.60,2.24]);yg=np.array([shape.roof_y(z) for z in zgrid])
    distance=np.r_[0,np.cumsum(np.hypot(np.diff(zgrid),np.diff(yg)))]
    along=np.interp(p[:,2],zgrid,distance)
    if abs(n[1])<.30:
        m.plane(t,'pale_edge',(1.85,.30));return
    if abs(n[0])>.10:
        side=int(np.sign(float(p[:,0].mean())))
        co=np.column_stack((along,abs(p[:,0])))
        m.chart(t,'pale_strip',co,(1.85,.50),('roof shoulder',side));return
    if n[1]>.8:
        co=np.column_stack((p[:,0],along))
        m.chart(t,'pale',co,(1.4,1.65),'roof field');return
    m.plane(t,'pale_edge',(1.85,.30))


def remap(entry,cy):
    name=entry['name'];m=Mapper(name)
    if name in ('Native_cabin','glass_lod1'):return entry['groups']
    for gi,g in enumerate(entry['groups']):
        for t in np.array(g['corners'],float):
            role=g['material'];p=t[:,:3];n=normal(t)
            if name.endswith('_carved_flank'):flank(m,t,role)
            elif name.endswith('_swept_wing'):wing(m,t,role)
            elif name.endswith('_sculpted_engine'):engine(m,t,role,cy)
            elif name=='Armored_transverse_drum':drum(m,t,role,DRUM_CY)
            elif name=='Sculpted_roof_shoulders':roof(m,t,role)
            elif name=='Root':
                if role==BROWN:m.plane(t,'cargo',(2.2,2.2))
                else:m.chart(t,'skin',np.column_stack((p[:,0],p[:,2])),(1.65,2.0),'lower keel')
            elif name=='BayDoor_lod1':
                if gi==0:m.keep(t,role);continue
                yy=.740334+.087487*(p[:,2]+3.889885);h=p[:,1]-yy
                if h.max()<0:m.plane(t,'cargo',(1.5,1.5));continue
                # Native shutter UV scaled to the actual new inset; one framed
                # rectangular field, with a continuous pale border round it.
                if n[1]>.8:
                    m.fixed(t,P,p[:,[0,2]],(-.675,-3.81),(.675,-.53),(.508,.990,.990,.270))
                else:m.plane(t,'brown_strip',(1.7,.25))
            elif name.endswith('_covered_root'):
                m.plane(t,'brown' if role==BROWN else 'pale_strip',(1.5,.45))
            elif name.endswith('_integrated_engine_seat'):
                m.plane(t,'brown' if role==BROWN else 'skin',(1.25,1.6))
            elif name=='Stern_receiver_fascia':
                m.plane(t,'green' if role==BROWN else 'pale_strip',(1.4,.45))
            elif name=='Tapered_lower_receiver':m.plane(t,'skin',(1.45,1.8))
            else:m.plane(t,'pale',(1.5,1.8))
    return m.finish()


def area(groups):
    return sum(np.linalg.norm(np.cross(np.asarray(g['corners'])[:,1,:3]-np.asarray(g['corners'])[:,0,:3],
        np.asarray(g['corners'])[:,2,:3]-np.asarray(g['corners'])[:,0,:3]),axis=1).sum()/2 for g in groups)


def main():
    global DRUM_CY
    assert shutil.disk_usage(model.ROOT).free>3*1024**3
    data=json.loads(SOURCE.read_text(encoding='utf8'));DRUM_CY=data['drum']['center_y'];cy=data['placement']['engine_axis_y']
    for p,digest in data['sources'].items():assert f.digest(Path(p))==digest,p
    OUT.mkdir(parents=True,exist_ok=True);uv.PATCHES.update(PATCHES);REPORT.clear()
    objects=copy.deepcopy(data['objects']);audit=[]
    for e in objects:
        original=e['groups']
        if e['name'] not in ('Native_cabin','glass_lod1'):
            canonical=[dict(g,corners=np.array(g['corners'],float)) for g in original]
            for g in canonical:g['corners'][...,:3]=g['corners'][...,:3].round(5)
            gs=remap(dict(e,groups=canonical),cy)
            try:gs,cleaned=uv_mesh_seams.clean(gs,canonical,e['authored_closed'])
            except AssertionError as err:raise AssertionError((e['name'],err)) from err
            splits=cleaned['tjunction_splits']
            # UV clipping changes tessellation, not the actual surfaces.
            before=area(original);after=area(gs)
            assert abs(after-before)<max(1e-5,before*2e-5),(e['name'],before,after)
        else:gs=original;splits=0;before=after=area(original);cleaned={}
        e['groups']=gs
        audit.append(dict(name=e['name'],before_triangles=sum(len(g['corners']) for g in original),
            after_triangles=sum(len(g['corners']) for g in gs),area_before=before,area_after=after,
            edge_repairs=splits,seam_cleanup=cleaned,native_unchanged=e['name'] in ('Native_cabin','glass_lod1')))
    mats=f.audit.material_table([model.MAT,model.ENV]);palette={}
    used={g['material'] for e in objects for g in e['groups']};assert used<=mats.keys()
    td=OUT/'textures';td.mkdir(exist_ok=True)
    for mid in used:
        mat=mats[mid];row={k:v for k,v in mat.items() if k!='image'};row['image_path']=None
        if mat['image'] is not None:
            p=td/(Path(mat['texture']).stem+'.png')
            if not p.exists():mat['image'].save(p)
            row['image_path']=p.as_posix()
        palette[str(mid)]=row
    for e in objects:
        for g in e['groups']:
            if 'metal' in mats[g['material']]['texture'].lower():
                assert e['name'] in ('Root','BayDoor_lod1'),e['name']
    header,_=f.mesh.read_tree(model.SOURCE.read_bytes())
    # UV seams can require very small but valid positive-area triangles. Keep
    # them rather than using the older broad sliver filter, which opens holes.
    # Export/readback still requires identical face counts and finite float32s.
    exports=[model.export_cmp(header,objects,OUT/'rh_pir_fighter_lod0_open.cmp',min_cross_area=1e-12),
             model.export_cmp(header,objects,OUT/'rh_pir_fighter_lod0_bay_open.cmp',True,min_cross_area=1e-12)]
    data.update(objects=objects,materials=palette,exports=exports,shape_source=str(SOURCE),
        shape_source_sha256=f.digest(SOURCE),revision='F14 UV/01: accepted F14/03 shape, native pirate atlas mapping',
        stage='LOD0 UV/material prototype only; no distant LODs, damage, SUR or final rig',
        total_triangles=sum(len(g['corners']) for e in objects for g in e['groups']),
        preview_name_prefix='textured',blend_basename='rh_pir_fighter_lod0.blend')
    model.dump(OUT/'geometry.json',data)
    model.dump(OUT/'uv_report.json',dict(shape_source=str(SOURCE),shape_sha256=f.digest(SOURCE),
        object_checks=audit,charts=REPORT,geometry_sha256=f.digest(OUT/'geometry.json')))
    for p,digest in data['sources'].items():assert f.digest(Path(p))==digest,p
    print(json.dumps(dict(output=str(OUT),triangles=data['total_triangles'],charts=len(REPORT),objects=audit),indent=2))


if __name__=='__main__':main()
