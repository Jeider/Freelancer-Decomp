"""F01 UV/01: native atlas mapping, two simple cargo leaves and roof mounts.

Offline visual prototype. The user's accepted F01 silhouette is retained;
new wing-fold motion is an explicitly separate Blender layout study.
"""
import collections
import copy
import hashlib
import json
import math
import shutil
import struct
from pathlib import Path
import numpy as np
import rh_fighter_f01_body as body
import rh_fighter_f14_uv as olduv
import uv_mesh_seams

model,s,f=body.model,body.s,body.f
B,P,R,D=body.B,body.P,body.R,body.D
uv=olduv.uv
SOURCE=body.OUT/'geometry.json'
BASE=model.TOPIC/'prototypes/f14_03/geometry.json'
OUT=model.TOPIC/'prototypes/f01_uv_01'
Z0,Z1=-3.90,-1.66
HALF=.74
HOLD=olduv.HOLD
PATCHES=dict(olduv.PATCHES)
PATCHES.update({
    'hatch':[(P,(.156,.277,.489,.553))],
    'bolt_band':[(P,(.510,.863,.994,.993))],
    'red_pair':[(R,(.012,.012,.330,.490))],
    'green_clean':[(olduv.GREEN,(.670,.012,.992,.205))],
})
HP=[dict(name='HpWeapon05',kind='Revolute',owner='Sculpted_roof_shoulders',position=[-.64,1.925,-.12]),
    dict(name='HpWeapon06',kind='Revolute',owner='Sculpted_roof_shoulders',position=[.64,1.925,-.12]),
    dict(name='HpShield01',kind='Fixed',owner='Sculpted_roof_shoulders',position=[0,1.925,.94]),
    dict(name='HpBayDoor01',kind='Fixed',owner='Root',position=[0,1.02,(Z0+Z1)/2]),
    dict(name='HpBayDoor02',kind='Fixed',owner='Root',position=[0,2.5,(Z0+Z1)/2])]


def door_y(z):return 1.004+(z-Z0)*.0075


def new_roof():
    b=B();stations=sorted(set(body.ROOF[:,0])|{Z0,Z1})
    for sign in (-1,1):
        for a,z in zip(stations,stations[1:]):
            ya=float(np.interp(a,body.TOP[:,0],body.TOP[:,1]));yz=float(np.interp(z,body.TOP[:,0],body.TOP[:,1]))
            b.face([[sign*s.side_x(a,ya),ya,a],[sign*s.side_x(z,yz),yz,z],
                    [sign*body.roof_w(z),body.roof_y(z),z],[sign*body.roof_w(a),body.roof_y(a),a]],P,model.PLAIN,[sign,1,0])
            b.face([[sign*HALF,body.roof_y(a),a],[sign*body.roof_w(a),body.roof_y(a),a],
                    [sign*body.roof_w(z),body.roof_y(z),z],[sign*HALF,body.roof_y(z),z]],P,model.PLAIN,[0,1,0])
            if a>=Z0 and z<=Z1:
                # The cargo walls join the existing hold, rather than ending
                # in an empty dark space under the shoulder.
                b.face([[sign*HALF,body.roof_y(a),a],[sign*HALF,body.roof_y(z),z],
                        [sign*.82,.61,z],[sign*.82,.61,a]],HOLD,model.PLAIN,[-sign,0,0])
        # Interior ceiling, continuous outside the opening.
    for a,z in zip(stations,stations[1:]):
        if a>=Z0 and z<=Z1:continue
        ya,yz=body.roof_y(a),body.roof_y(z)
        b.face([[-HALF,ya,a],[HALF,ya,a],[HALF,yz,z],[-HALF,yz,z]],P,model.PLAIN,[0,1,0])
        b.face([[-HALF,ya-.09,a],[HALF,ya-.09,a],[HALF,yz-.09,z],[-HALF,yz-.09,z]],HOLD,model.PLAIN,[0,-1,0])
    for z,sgn in [(Z0,1),(Z1,-1)]:
        y=body.roof_y(z)
        b.face([[-HALF,y,z],[HALF,y,z],[HALF,.61,z],[-HALF,.61,z]],HOLD,model.PLAIN,[0,0,sgn])
    # Low integrated seats; the roof below is solid. No weapon geometry baked in.
    for hp in HP[:3]:
        x,y,z=hp['position'];w=.50 if hp['name'].startswith('HpWeapon') else .46
        poly=model.clipped_rect(x-w/2,x+w/2,z-.28,z+.28,.055)
        s.prism(b,poly,1,y,1.842,olduv.WARNING)
    s.add('Sculpted_roof_shoulders',b,'hull',False)
    for sign,label in [(-1,'Port'),(1,'Starboard')]:
        b=B();lo,hi=sorted([sign*.012,sign*.721])
        poly=np.array([[lo,Z0+.016],[hi,Z0+.016],[hi,Z1-.016],[lo,Z1-.016]])
        top=np.array([[x,door_y(z),z] for x,z in poly]);bottom=top.copy();bottom[:,1]-=.065
        b.face(top,P,model.PLAIN,[0,1,0]);b.face(bottom,HOLD,model.PLAIN,[0,-1,0]);s.link(b,top,bottom,D)
        s.add(f'{label}_BayDoor',b,'cargo',True)


def roof_distance(z):
    a=body.ROOF
    lengths=np.r_[0,np.cumsum(np.linalg.norm(np.diff(a,axis=0),axis=1))]
    return np.interp(z,a[:,0],lengths)


def rim_map(p,poly,depth):return olduv.contour_uv(p,poly,depth)


def edge_distance(point,poly):
    a=np.array(poly);d=np.roll(a,-1,axis=0)-a
    t=np.clip(np.sum((point-a)*d,axis=1)/np.sum(d*d,axis=1),0,1)
    return np.linalg.norm(point-a-t[:,None]*d,axis=1).min()


def poly_area(p):
    p=p-p[0]
    return .5*abs(np.sum(p[:,0]*np.roll(p[:,1],-1)-p[:,1]*np.roll(p[:,0],-1)))


def intersection(subject,triangle):
    if np.any(np.max(subject,axis=0)<np.min(triangle,axis=0)) or np.any(np.max(triangle,axis=0)<np.min(subject,axis=0)):
        return np.empty((0,2))
    result=np.array(subject)
    cross=lambda a,b:a[0]*b[1]-a[1]*b[0]
    orientation=cross(triangle[1]-triangle[0],triangle[2]-triangle[0])
    sign=1 if orientation>0 else -1
    for a,b in zip(triangle,np.roll(triangle,-1,axis=0)):
        if len(result)<3:return np.empty((0,2))
        out=[];edge=b-a
        for p,q in zip(result,np.roll(result,-1,axis=0)):
            dp=sign*cross(edge,p-a);dq=sign*cross(edge,q-a)
            epsilon=0.
            ip,iq=dp>=-epsilon,dq>=-epsilon
            if ip:out.append(p)
            if ip!=iq:out.append(p+(q-p)*(dp/(dp-dq)))
        result=np.array(out)
    return result


def flank(m,t,role):
    p=t[:,:3];n=olduv.normal(t)
    depth=np.array([s.side_x(z,y)-abs(x) for x,y,z in p])
    zy=np.column_stack((-p[:,2],-p[:,1]))
    vane=next((y for y in (-.60,-.16,.28,.72) if np.max(abs(depth-(.12+.15*(p[:,1]-y+.085)/.17)))<4e-5),None)
    if role==R:
        # Whole painted donor panels within each actual recessed field.
        front=float(p[:,2].mean())<-.85
        poly=body.FRONT_PANEL if front else body.REAR_PANEL
        m.chart(t,'red' if front else 'red_tall',zy,(1.70,.95) if front else (10,10),('donor panel',front),True)
    elif depth.max()<3e-5:
        m.chart(t,'pale',zy,(1.50,1.35),'continuous outer flank')
    elif np.max(abs(depth-.47))<3e-5:
        m.chart(t,'green_clean',zy,(1.30,1.15),'vent back')
    elif role==D:
        m.plane(t,'brown_strip',(1.5,.38),('well walls',olduv.key_plane(t)))
    elif vane is not None:
        # Each vane gets one uninterrupted native strip along its width.
        m.plane(t,'red',(10,10),('vane',vane),True)
    elif depth.max()>.8:
        m.chart(t,'skin_strip',rim_map(p,body.OUTLINE,depth),(1.8,.90),'outer return')
    else:
        center=p[:,[2,1]].mean(0)
        poly=min([body.FRONT_PANEL,body.VENT,body.REAR_PANEL],key=lambda q:edge_distance(center,q))
        m.chart(t,'pale_edge',rim_map(p,poly,depth),(1.9,.30),('pocket border',tuple(poly[0])))


def map_roof(m,t,role):
    p=t[:,:3];n=olduv.normal(t)
    if role==HOLD:m.plane(t,'cargo',(1.8,1.8));return
    if role==olduv.WARNING:
        if n[1]>.9:
            hp=min(HP[:3],key=lambda h:np.linalg.norm(p.mean(0)-np.array(h['position'])))
            x,y,z=hp['position'];w=.50 if hp['name'].startswith('HpWeapon') else .46
            box=(.015,.015,.985,.985) if hp['name'].startswith('HpWeapon') else (.51,.272,.995,.852)
            m.fixed(t,olduv.WARNING if hp['name'].startswith('HpWeapon') else P,p[:,[0,2]],(x-w/2,z-.28),(x+w/2,z+.28),box)
        else:m.plane(t,'brown_strip',(1.4,.28))
        return
    distance=roof_distance(p[:,2])
    if abs(n[0])>.1:
        # Unfold the slope across the shoulder, continuously along the deck.
        w=np.array([body.roof_w(z) for z in p[:,2]])
        y=np.array([body.roof_y(z) for z in p[:,2]])
        across=np.hypot(abs(p[:,0])-w,p[:,1]-y)
        m.chart(t,'bolt_band',np.column_stack((distance,across)),(1.85,.60),('shoulder',int(np.sign(p[:,0].mean()))),True)
    else:m.chart(t,'pale',np.column_stack((p[:,0],distance)),(1.25,1.75),'roof deck')


def belly_center(m,t):
    stations=[-4.3,-3.65,-2.55,-2.45,-1.28,-1.18,-.10,.0,2.2]
    for i,(a,z) in enumerate(zip(stations,stations[1:])):
        poly=uv.clip(uv.clip(t,2,a,True),2,z,False)
        if len(poly)<3:continue
        service=i in (1,5)
        xs=[-1,-.55,.55,1] if service else [-1,1]
        for x0,x1 in zip(xs,xs[1:]):
            q=uv.clip(uv.clip(poly,0,x0,True),0,x1,False)
            for j in range(1,len(q)-1):
                tri=q[[0,j,j+1]].copy();p=tri[:,:3]
                if service and x0==-.55:
                    m.fixed(tri,P,p[:,[0,2]],(-.55,a),(.55,z),PATCHES['hatch'][0][1])
                elif i in (2,4,6):
                    m.fixed(tri,D,p[:,[0,2]],(-.98,a),(.98,z),PATCHES['brown_strip'][0][1])
                else:
                    family='pale_strip' if i==0 else 'pale'
                    box=PATCHES[family][0][1]
                    m.fixed(tri,P,p[:,[0,2]],(max(x0,-.98),a),(min(x1,.98),z),box)


def refit_engine_seat(entry):
    # Recess only the forward support into the hull, clearing the wing root's
    # complete sweep. The engine itself and the rear attachment remain fixed.
    e=copy.deepcopy(entry)
    for g in e['groups']:
        t=np.asarray(g['corners'],float).copy();x=t[...,0];z=t[...,2]
        outer=1.64+.32*np.clip((z-1.60)/.40,0,1)
        t[...,0]=np.sign(x)*(1.20+(abs(x)-1.20)*(outer-1.20)/.76)
        n=np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]);n/=np.linalg.norm(n,axis=1)[:,None]
        t[...,3:6]=n[:,None,:];g['corners']=t
    return e


def base_mapping(entry):
    name=entry['name'];m=olduv.Mapper(name)
    for g in entry['groups']:
        for t in np.asarray(g['corners'],float):
            p=t[:,:3];n=olduv.normal(t);role=g['material']
            if name.endswith('_carved_flank'):flank(m,t,role)
            elif name=='Sculpted_roof_shoulders':map_roof(m,t,role)
            elif name.endswith('_BayDoor'):
                if role==HOLD:m.plane(t,'cargo',(1.4,1.8))
                elif n[1]>.8:
                    # A single calm, deliberately framed field on each leaf.
                    m.fixed(t,P,np.column_stack((abs(p[:,0]),p[:,2])),(.012,Z0+.016),(.721,Z1-.016),(.680,.272,.885,.852))
                else:m.plane(t,'brown_strip',(1.6,.20))
            elif name=='Root':
                if role==D or role==HOLD:m.plane(t,'cargo',(1.8,2.0));continue
                # The bottom uses real keel stations rather than a huge planar
                # atlas crop or a separate UV reset on each sloped triangle.
                chain=s.SIDE[5:][::-1];distance=np.r_[0,np.cumsum(np.linalg.norm(np.diff(chain,axis=0),axis=1))]
                along=np.interp(p[:,2],chain[:,0],distance)
                if abs(p[:,0]).max()<=.981:
                    belly_center(m,t)
                else:
                    y=np.interp(p[:,2],chain[:,0],chain[:,1])-.2
                    across=np.hypot(abs(p[:,0])-.98,p[:,1]-y)
                    m.chart(t,'skin_strip',np.column_stack((along,across)),(1.75,.70),('belly shoulders',int(np.sign(p[:,0].mean()))))
            elif name=='Tapered_lower_receiver':
                if n[1]<-.45:m.chart(t,'bolt_band',np.column_stack((p[:,0],-p[:,2])),(1.80,.65),'aft belly transverse strips',True)
                else:m.plane(t,'skin_strip',(1.6,.7))
            else:m.plane(t,'pale',(1.4,1.6))
    return m.finish()


def bary(x,p):
    a=np.column_stack((p[1]-p[0],p[2]-p[0]));q=np.linalg.solve(a,np.asarray(x).T-p[0][:,None]).T
    return np.column_stack((1-q.sum(1),q))


def wing_identical(entry):
    """Transfer the actual upper atlas layout down to the underside in XZ.

    Intersect charts, not UV point samples: every lower triangle stays within
    exactly one upper chart, including the three fields and warning stripe.
    """
    m=olduv.Mapper(entry['name']);bottom=[]
    for g in entry['groups']:
        for t in np.asarray(g['corners'],float):
            if olduv.normal(t)[1]<-.8:bottom.append(t)
            else:olduv.wing(m,t,g['material'])
    mapped=m.finish();out=collections.defaultdict(list)
    tops=[]
    for g in mapped:
        for t in g['corners']:
            out[g['material']].append(t)
            if olduv.normal(t)[1]>.05:
                poly=t[:,[0,2]]
                if poly_area(poly)>1e-15:tops.append((poly,t,g['material']))
    coverage=0.;expected=0.
    for t in bottom:
        bp=t[:,[0,2]];expected+=poly_area(bp)
        for poly,top,mat in tops:
            co=intersection(bp,poly)
            if len(co)<3 or poly_area(co)<1e-15:continue
            v=bary(co,t[:,[0,2]])@t
            v[:,6:8]=bary(co,top[:,[0,2]])@top[:,6:8];coverage+=poly_area(co)
            for i in range(1,len(v)-1):
                tri=v[[0,i,i+1]].copy()
                if olduv.normal(tri)[1]>0:tri=tri[[0,2,1]]
                out[mat].append(tri)
    assert abs(coverage-expected)<1e-6,(entry['name'],coverage,expected)
    return [dict(material=mat,corners=np.array(ts)) for mat,ts in out.items()]


def rot(axis,angle):
    axis=np.array(axis,float);axis/=np.linalg.norm(axis);x,y,z=axis
    k=np.array([[0,-z,y],[z,0,-x],[-y,x,0]])
    return np.eye(3)+math.sin(angle)*k+(1-math.cos(angle))*(k@k)


def motion_transform(motion,phase):
    p=np.array(motion['pivot']);axis=motion['axis'];angle=motion['angle_degrees']*math.pi/180
    smooth=lambda x:np.clip(x,0,1)**2*(3-2*np.clip(x,0,1))
    if motion['kind']=='wing':
        slide=smooth(phase/.30);turn=smooth((phase-.25)/.75)
    else:slide=phase;turn=smooth(phase)
    r=rot(axis,angle*turn);delta=np.array(motion.get('translation',[0,0,0]))*slide
    return r,p+delta-r@p


def motions():
    result={}
    for sign,label in [(-1,'Port'),(1,'Starboard')]:
        result[label+'_BayDoor']=dict(kind='door',pivot=[sign*.721,door_y((Z0+Z1)/2),(Z0+Z1)/2],
            axis=[0,.0075,1],angle_degrees=-sign*98)
        result[label+'_swept_wing']=dict(kind='wing',pivot=[sign*1.77,-1.02,-.80],
            axis=[0,1,0],angle_degrees=sign*55,translation=[sign*.12,0,.45])
    return result


def add_hardpoints(export):
    path=Path(export['file']);header,nodes=f.mesh.read_tree(path.read_bytes())
    for owner in sorted({h['owner'] for h in HP}):
        parent=f.mesh.child(nodes[0],export['private_submodels'][owner]);hp=f.folder('Hardpoints')
        for kind in ('Fixed','Revolute'):
            bucket=f.folder(kind)
            for h in HP:
                if h['owner']!=owner or h['kind']!=kind:continue
                node=f.folder(h['name'],f.mesh.Node('Position',np.array(h['position'],'<f4').tobytes()),
                    f.mesh.Node('Orientation',np.eye(3,dtype='<f4').tobytes()))
                if kind=='Revolute':
                    for key,value in [('Axis',[0,1,0]),('Min',[-math.pi/3]),('Max',[math.pi/3])]:
                        node.children.append(f.mesh.Node(key,np.array(value,'<f4').tobytes()))
                bucket.children.append(node)
            if bucket.children:hp.children.append(bucket)
        parent.children.append(hp)
    path.write_bytes(f.mesh.write_tree(header,nodes));export['sha256']=f.digest(path);export['hardpoints']=HP
    _,check=f.mesh.read_tree(path.read_bytes());actual=f.hp_world(check)
    for h in HP:assert np.allclose(actual[h['name'].lower()]['position'],h['position'])


def main():
    assert shutil.disk_usage(model.ROOT).free>3*1024**3
    data=json.loads(SOURCE.read_text(encoding='utf8'));base=json.loads(BASE.read_text(encoding='utf8'))
    for path,digest in data['sources'].items():assert f.digest(Path(path))==digest,path
    uv.PATCHES.update(PATCHES);olduv.REPORT.clear();s.OBJECTS.clear();new_roof()
    replacement={e['name']:e for e in s.OBJECTS};oldbase={e['name']:e for e in base['objects']}
    objects=[];checks=[];preserved=[]
    for e in data['objects']:
        name=e['name']
        if name=='BayDoor_lod1':continue
        if name in replacement:e=copy.deepcopy(replacement.pop(name))
        elif name.endswith('_integrated_engine_seat'):e=refit_engine_seat(oldbase[name])
        elif name in ('Root','Tapered_lower_receiver') or name.endswith('_swept_wing'):e=copy.deepcopy(oldbase[name])
        else:e=copy.deepcopy(e)
        remap=name.endswith(('_carved_flank','_swept_wing','_integrated_engine_seat')) or name in ('Root','Sculpted_roof_shoulders','Tapered_lower_receiver')
        if not remap:preserved.append(name)
        objects.append((e,remap))
    objects.extend((copy.deepcopy(e),True) for e in replacement.values())
    output=[]
    for e,remap in objects:
        original=[dict(g,corners=np.asarray(g['corners'],float)) for g in e['groups']]
        if remap:
            gs=wing_identical(dict(e,groups=original)) if e['name'].endswith('_swept_wing') else base_mapping(dict(e,groups=original))
            try:gs,clean=uv_mesh_seams.clean(gs,original,e['authored_closed'])
            except AssertionError as exc:raise AssertionError((e['name'],exc)) from exc
            assert abs(olduv.area(gs)-olduv.area(original))<max(1e-5,olduv.area(original)*2e-5),e['name']
        else:gs=original;clean={}
        e['groups']=gs;output.append(e)
        checks.append(dict(name=e['name'],remapped=remap,seam_cleanup=clean,
            triangles=sum(len(g['corners']) for g in gs),area=olduv.area(gs)))
    OUT.mkdir(parents=True,exist_ok=True)
    header,_=f.mesh.read_tree(model.SOURCE.read_bytes());motion=motions()
    exports=[]
    for suffix,mode in [('open',None),('bay_open','door'),('folded_study','wing')]:
        posed=copy.deepcopy(output)
        for e in posed:
            if e['name'] in motion and motion[e['name']]['kind']==mode:
                r,t=motion_transform(motion[e['name']],1);e['groups']=f.base.world(e['groups'],r,t)
        ex=model.export_cmp(header,posed,OUT/f'rh_pir_fighter_f01_uv_{suffix}.cmp',min_cross_area=1e-12)
        add_hardpoints(ex);exports.append(ex)
    data.update(objects=output,exports=exports,revision='F01 UV/01',shape_source=SOURCE.as_posix(),
        shape_source_sha256=f.digest(SOURCE),total_triangles=sum(c['triangles'] for c in checks),
        stage='Offline LOD0 UV and two-leaf baydoor prototype; wing motion is a layout study, not the final game rig.',
        preview_name_prefix='textured',position_decimals=9,blend_basename='rh_pir_fighter_f01_uv.blend',
        motion=motion,hardpoints=HP,preserved_objects=preserved,
        form_notes=['Solid raised roof with two additional weapon seats and one shield seat',
                    'Simple paired longitudinal cargo leaves; the old sliding lid is removed',
                    'Native small-patch UVs; exact upper-wing charts transferred to the underside',
                    'Wing-fold study: short aft travel then yaw inward along the hull; no native RH fighter folding'])
    model.dump(OUT/'geometry.json',data)
    model.dump(OUT/'uv_report.json',dict(source_sha256=f.digest(SOURCE),geometry_sha256=f.digest(OUT/'geometry.json'),
        object_checks=checks,charts=olduv.REPORT,wing_underside='Exact chart intersection/transfer from upper surface in XZ'))
    print(json.dumps(dict(output=str(OUT),triangles=data['total_triangles'],preserved=preserved),indent=2))


if __name__=='__main__':main()
