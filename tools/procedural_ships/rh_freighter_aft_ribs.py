"""Q13 uv_07: structural aft ribs, closer engines and physically unfolded UVs.

Offline prototype only. Retains uv_06 except the user's marked rear assembly
and side-perimeter/front-engine texture corrections.
"""
import collections
import json
import math
import shutil
import numpy as np
import rh_freighter_uv_b3 as base

uv,rig,f,q=base.uv,base.rig,base.f,base.q
old,package=base.old,base.package
PREVIOUS=base.OUT
OUT=PREVIOUS.parent/'uv_07'
SHIFT=.28
PATH=np.array([[5.72,3.81],[7.72,2.48],[8.30,1.78],
    [8.30,-2.62],[7.72,-3.24],[5.72,-3.88]])  # native z,y
HALF_WIDTH=.43
REPORT=[]
ENGINES=[]
RIBS={}
HP_OFFSETS={name:[delta,0,0] for names,delta in [
    (('HpEngine01','HpMine01','HpMass01'),SHIFT),
    (('HpEngine02','HpCM01','HpMass02'),-SHIFT)] for name in names}


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,
        default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def guard():
    for folder in (PREVIOUS,OUT):
        for name,report in [('rh_pir_freighter.cmp','build.json'),
                ('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/name).exists():continue
            assert f.digest(folder/name)==json.loads((folder/report).read_text())['cmp_sha256'],(
                folder/name,'manual edits: preserve before rebuilding')


def engine(side):
    ob=base.engine(side)
    report=base.ENGINES.pop()
    stations={7.70:(8.38,1.70,.64,.38),8.32:(8.63,1.78,.53,.40),
        8.88:(8.98,1.99,.45,.43),9.35:(9.35,2.08,.48,.48)}
    for g in ob['groups']:
        ts=np.array(g['corners'],float);p=ts[:,:,:3]
        if g['material']==8:
            for z,(newz,cx,w,neww) in stations.items():
                mask=np.isclose(p[:,:,2],z,atol=1e-6)
                p[:,:,0][mask]=side*2.08+(p[:,:,0][mask]-side*cx)*neww/w
                p[:,:,2][mask]=newz
        p[:,:,0]-=side*SHIFT
        n=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);n/=np.linalg.norm(n,axis=1)[:,None]
        ts[:,:,3:6]=n[:,None,:];g['corners']=ts
    ob['groups'],closure=q.coherent(ob['groups'])
    ob['name']=f'Engine casing - B3 aft rib mount {side:+}'
    report.update(center_xy=[side*(2.08-SHIFT),-.28],closure=closure,
        shift_x=-side*SHIFT,mount_visible_z=[8.51,9.35],
        mount_root_x=side*1.80,mount_root_z=8.38,mount_half_width=.38)
    report['previous_profile']=report.pop('profile')
    ENGINES.append(report)
    return ob


def rib(side):
    directions=np.diff(PATH,axis=0)
    normals=np.column_stack((-directions[:,1],directions[:,0]))
    normals/=np.linalg.norm(normals,axis=1)[:,None]
    offset=[]
    for i in range(len(PATH)):
        if i==0:m=normals[0]
        elif i==len(PATH)-1:m=normals[-1]
        else:
            m=normals[i-1]+normals[i];m/=np.linalg.norm(m);m/=m@normals[i]
        offset.append(m)
    offset=np.array(offset)
    outer=PATH+.21*offset;inner=PATH-.10*offset
    centers=1.80+.20*(8.30-PATH[:,0])/(8.30-5.72)
    def edge(poly,dx):
        return np.column_stack((side*(centers+dx),poly[:,1],poly[:,0]))
    oi,oo=edge(outer,-HALF_WIDTH),edge(outer,HALF_WIDTH)
    bi,bo=edge(inner,-HALF_WIDTH),edge(inner,HALF_WIDTH)
    arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff((oi+oo)/2,axis=0),axis=1))]
    b=q.B()
    for i in range(len(PATH)-1):
        j=i+1
        normal=np.array([0,*normals[i][::-1]])
        b.face([oi[i],oi[j],oo[j],oo[i]],20,normal=normal)
        b.face([bi[i],bo[i],bo[j],bi[j]],22,normal=-normal)
        b.face([oo[i],oo[j],bo[j],bo[i]],21,normal=[side,0,0])
        b.face([oi[i],bi[i],bi[j],oi[j]],21,normal=[-side,0,0])
    for i,sign in [(0,-1),(-1,1)]:
        direction=directions[0 if i==0 else -1]
        b.face([oi[i],oo[i],bo[i],bi[i]],21,normal=[0,sign*direction[1],sign*direction[0]])
    gs,closure=q.coherent(b.groups())
    RIBS[side]=dict(oi=oi,oo=oo,bi=bi,bo=bo,arc=arc,closure=closure)
    return dict(name=f'Aft structural rib {side:+}',groups=gs,closed=True)


def prepare():
    guard();OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    for i,ob in enumerate(data['objects']):
        if ob['name'].startswith('Engine casing'):
            data['objects'][i]=engine(-1 if '-1' in ob['name'] else 1)
    data['objects'].extend([rib(-1),rib(1)])
    data['hardpoint_world_offsets']=HP_OFFSETS
    (OUT/'mechanical_geometry.json').write_text(json.dumps(data,separators=(',',':'),
        default=lambda a:a.tolist()),encoding='utf8')
    dump('engine_geometry_check.json',ENGINES)
    dump('aft_rib_geometry.json',dict(path_zy=PATH,ribs=RIBS,width=2*HALF_WIDTH,
        outward_height=.21,buried_depth=.10,engines_each_inward=SHIFT,
        common_engine_glow_preserved=True,hardpoint_world_offsets=HP_OFFSETS))
    shutil.copyfile(PREVIOUS/'vent_clearance.json',OUT/'vent_clearance.json')


def unfold_quad(quad):
    """Isometric development of the actual D-A-B / B-C-D triangulation.

    Previous perimeter UVs interpolated a different diagonal and assigned an
    average width; that sheared panel03 at tapered corners.
    """
    a,b,c,d=quad;ab=np.linalg.norm(b-a);bd=np.linalg.norm(d-b)
    xd=(d-a)@(b-a)/ab;yd=math.sqrt(max(np.dot(d-a,d-a)-xd*xd,0))
    out=np.array([[0.,0.],[ab,0.],[0.,0.],[xd,yd]])
    e=(out[3]-out[1])/bd;perp=np.array([-e[1],e[0]])
    s=(np.dot(c-b,c-b)+bd*bd-np.dot(c-d,c-d))/(2*bd)
    h=math.sqrt(max(np.dot(c-b,c-b)-s*s,0))
    v,w=out[3]-out[1],out[0]-out[1]
    side=np.sign(v[0]*w[1]-v[1]*w[0])
    out[2]=out[1]+s*e-side*h*perp
    return out


def on_quad(t,quad,coords):
    answer=[]
    for p in t[:,:3]:
        found=None
        for ids in ([3,0,1],[1,2,3]):
            tri=quad[ids];basis=(tri[1:]-tri[0]).T
            st=np.linalg.lstsq(basis,p-tri[0],rcond=None)[0]
            w=np.r_[1-st.sum(),st]
            if w.min()>-1e-4 and np.linalg.norm(w@tri-p)<2e-4:
                found=w@coords[ids];break
        if found is None:return None
        answer.append(found)
    return np.array(answer)


def upper_map(name,groups):
    side=-1 if '-1' in name else 1
    a=q.B().yz(base.UP_BACK,side*2.62);b=q.B().yz(base.UP_FACE,side*3.50)
    quads=[]
    for i in range(len(a)):
        j=(i+1)%len(a);quad=np.array([a[i],a[j],b[j],b[i]])
        quads.append((quad,unfold_quad(quad)))
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            for i,(quad,co) in enumerate(quads):
                coords=on_quad(t,quad,co)
                if coords is not None:
                    # Same physical scale in U/V; deliberate seams only at the
                    # real contour corners, never at a triangle inside a panel.
                    base.add(charts,t,'frame03',coords,(2.3,100),(name,'unfolded perimeter',i))
                    break
            else:rest[g['material']].append(t)
    for g in base.region_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return base.complete(charts,mapped)


def rib_map(name,groups):
    side=-1 if '-1' in name else 1;r=RIBS[side]
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t)
            if g['material']==20:
                for i in range(len(PATH)-1):
                    j=i+1;quad=np.array([r['oi'][i],r['oi'][j],r['oo'][j],r['oo'][i]])
                    cs=np.array([[0,r['arc'][i]],[0,r['arc'][j]],[2*HALF_WIDTH,r['arc'][j]],[2*HALF_WIDTH,r['arc'][i]]])
                    co=on_quad(t,quad,cs)
                    if co is not None:break
                else:raise AssertionError(('unmapped rib cap',p))
                base.add(charts,t,'red_edge',co,(100,2.65),(name,'continuous outer red band'),exact=True)
            else:
                # Each broad side wall is an actual plane. No axial projection
                # across its bevel/corner and no full-hull atlas stretch.
                co=uv.plane_coords(p,n)
                base.add(charts,t,'frame03',co,(2.25,1.3),
                    (name,'panel03 side',tuple(n.round(5)),round(float(n@p.mean(0)),4)))
    return base.complete(charts,mapped)


def core_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];c=p.mean(0);n=old.normal(t)
            if c[2]>5.72 and n[1]>.4:
                # The old red colour-only rails incorrectly included the sloping
                # hull chamfers. Their new replacements are real structural ribs.
                base.add(charts,t,'light',uv.plane_coords(p,n),(1.9,2.1),
                    ('aft pale deck',tuple(n.round(5)),round(float(n@c),5)))
            else:rest[g['material']].append(t)
    for g in base.core_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return base.complete(charts,mapped)


def engine_map(name,groups):
    side=-1 if '-1' in name else 1
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t);c=p.mean(0)
            if g['material']==3 and p[:,2].max()<=9.48001:
                # Front conical shoulder: its radial width is much larger than
                # its axial length. Plane unfolding avoids the stretched spokes.
                base.add(charts,t,'dark',uv.plane_coords(p,n),(2.5,2.5),
                    (name,'front dark shoulder',tuple(n.round(5)),round(float(n@c),5)))
            else:
                t[:,0]+=side*SHIFT;rest[g['material']].append(t)
    for g in base.engine_map(name,package.pack(rest)):
        ts=np.array(g['corners']);ts[:,:,0]-=side*SHIFT;mapped[g['material']].extend(ts)
    return base.complete(charts,mapped)


def main():
    prepare();base.configure();rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp'
    base.REPORT.clear();diagnostics=[]
    def mapping(name,gs):
        mapper=(engine_map if name.startswith('Engine casing') else rib_map if name.startswith('Aft structural')
            else upper_map if name.startswith('Faceted shoulder') else core_map if name.startswith('Continuous hull') else base.region_map)
        result=mapper(name,gs);bad=0.;count=0
        for g in result:
            ts=np.array(g['corners']);p=ts[:,:,:3];u=ts[:,:,6:8]
            area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)/2
            a=u[:,1]-u[:,0];b=u[:,2]-u[:,0];ua=abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/2
            mask=(area>1e-6)&(ua<1e-12);bad+=float(area[mask].sum());count+=int(mask.sum())
        if not name.startswith(('Original','Stepped circular')):assert bad<1e-7,(name,bad)
        diagnostics.append(dict(object=name,collapsed_uv_triangles=count,collapsed_uv_area=bad))
        return result
    rig.material_map=mapping;rig.main(OUT/'mechanical_geometry.json')
    h=f.digest(rig.DEST)
    dump('engine_check.json',dict(engines=ENGINES,cmp_sha256=h,installed=False))
    dump('uv_degenerate.json',dict(cmp_sha256=h,objects=diagnostics))
    dump('uv_layout.json',dict(cmp_sha256=h,regions=base.REPORT,
        source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),installed=False))
    package.OUT=OUT;package.open_review()
    print('AFT_RIBS_READY',OUT)


if __name__=='__main__':main()
