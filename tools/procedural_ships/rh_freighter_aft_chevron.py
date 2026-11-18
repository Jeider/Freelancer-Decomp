"""Q13 uv_08: shallow V-shaped rear, panel03 return and continuous side UVs."""
import collections
import json
import math
import shutil
import numpy as np
import rh_freighter_aft_ribs as aft

base,old,package=aft.base,aft.old,aft.package
uv,rig,f,q=aft.uv,aft.rig,aft.f,aft.q
PREVIOUS=aft.OUT
OUT=PREVIOUS.parent/'uv_08'
EDGE=1.37
DEPTH=.70
START_Z=5.72
END_Z=8.30
STATS=[]
SEAMS=[]


def dump(name,data):
    (OUT/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,
        default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')


def guard():
    for folder in (PREVIOUS,OUT):
        for name,report in [('rh_pir_freighter.cmp','build.json'),('rh_pir_freighter_review_open.cmp','review_open_check.json')]:
            if folder==OUT and not (folder/name).exists():continue
            assert f.digest(folder/name)==json.loads((folder/report).read_text())['cmp_sha256'],(folder/name,'manual changes')


def split(polys,axis,value):
    result=[]
    for p in polys:
        if p[:,axis].min()<value-1e-6 and p[:,axis].max()>value+1e-6:
            result.extend([uv.clip(p,axis,value,True),uv.clip(p,axis,value,False)])
        else:result.append(p)
    return result


def shape_core(ob):
    groups=collections.defaultdict(list)
    for g in ob['groups']:
        for t in np.array(g['corners'],float):
            p=t[:,:3]
            if p[:,2].max()<=START_Z+1e-5:
                groups[g['material']].append(t);continue
            role=30 if np.allclose(p[:,2],END_Z,atol=1e-5) else g['material']
            for poly in split([t],2,START_Z):
                pieces=[poly]
                if poly[:,2].max()>START_Z+1e-5:
                    for cut in (-EDGE,0,EDGE):pieces=split(pieces,0,cut)
                for part in pieces:
                    part=part.copy()
                    weight=np.clip((part[:,2]-START_Z)/(END_Z-START_Z),0,1)
                    part[:,2]-=DEPTH*np.maximum(0,1-abs(part[:,0])/EDGE)*weight
                    for tri in package.triangles(part):
                        tri[:,3:6]=old.normal(tri)
                        groups[role].append(tri)
    ob['groups']=package.pack(groups)
    return ob


def prepare():
    guard();OUT.mkdir(parents=True,exist_ok=True)
    data=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    for i,ob in enumerate(data['objects']):
        if ob['name'].startswith('Continuous hull'):data['objects'][i]=shape_core(ob)
    (OUT/'mechanical_geometry.json').write_text(json.dumps(data,separators=(',',':'),default=lambda a:a.tolist()),encoding='utf8')
    for name in ('engine_geometry_check.json','aft_rib_geometry.json','vent_clearance.json'):
        shutil.copyfile(PREVIOUS/name,OUT/name)
    ribs=json.loads((OUT/'aft_rib_geometry.json').read_text())['ribs']
    aft.RIBS.update({int(side):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for side,r in ribs.items()})
    dump('aft_chevron_geometry.json',dict(center_rear_z=END_Z-DEPTH,outer_rear_z=END_Z,
        inner_rib_x=EDGE,center_recess=DEPTH,unchanged_engine_positions=True,unchanged_hold_back_wall_z=START_Z))


def strip_unfold(side):
    a=q.B().yz(base.UP_BACK,side*2.62);b=q.B().yz(base.UP_FACE,side*3.50)
    result={};previous=None;errors=[]
    # Put the unavoidable closing seam under the lower edge of the upper panel.
    # The marked aft upper slope and vertical return remain joined.
    for i in list(range(4,len(a)))+list(range(4)):
        j=(i+1)%len(a);quad=np.array([a[i],a[j],b[j],b[i]])
        co=aft.unfold_quad(quad)
        if previous is not None:
            origin=co[0].copy();u=co[3]-co[0];target=previous[2]-previous[1]
            u/=np.linalg.norm(u);v=target/np.linalg.norm(target)
            cs=u@v;sn=u[0]*v[1]-u[1]*v[0]
            rotation=np.array([[cs,-sn],[sn,cs]])
            co=(co-origin)@rotation.T+previous[1]
            errors.append(float(max(np.linalg.norm(co[0]-previous[1]),np.linalg.norm(co[3]-previous[2]))))
        result[i]=(quad,co);previous=co
    assert max(errors)<1e-7
    SEAMS.append(dict(side=side,joined_edges=9,max_shared_edge_uv_error=max(errors)*.18,
        closing_seam='lower edge behind aft corner',scale=.18))
    return result


def upper_map(name,groups):
    quads=strip_unfold(-1 if '-1' in name else 1)
    mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            for quad,co in quads.values():
                coords=aft.on_quad(t,quad,co)
                if coords is not None:
                    t[:,6:8]=coords*.18+[.11,.53]
                    mapped[uv.S].append(t);break
            else:rest[g['material']].append(t)
    for g in base.region_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return package.pack(mapped)


def core_map(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=old.normal(t)
            if g['material']==30:
                # One broad panel03 field, physically unfolded across the V.
                p=t[:,:3];x=p[:,0];ax=abs(x)
                s=np.sign(x)*(np.minimum(ax,EDGE)*math.hypot(1,DEPTH/EDGE)+np.maximum(ax-EDGE,0))
                base.add(charts,t,'rear03',np.column_stack((s,p[:,1])),(100,100),'continuous broad rear panel03')
            elif p[:,2].min()>=START_Z-1e-5 and n[1]>.4:
                # The deformed deck is no longer one plane. Grouping charts by
                # its new triangle normals creates visible diagonal UV resets.
                # Recover the pre-warp station and use one continuous loft chart.
                displacement=DEPTH*np.maximum(0,1-abs(p[:,0])/EDGE)
                original_z=START_Z+(p[:,2]-START_Z)/(1-displacement/(END_Z-START_Z))
                stations=np.array([[5.72,3.81],[7.72,2.48],[8.30,1.78]])
                arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(stations,axis=0),axis=1))]
                v=np.interp(original_z,stations[:,0],arc)
                base.add(charts,t,'light',np.column_stack((p[:,0],v)),(1.9,2.1),'continuous aft pale deck')
            else:rest[g['material']].append(t)
    for g in aft.core_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return base.complete(charts,mapped)


def rib_map(name,groups):
    side=-1 if '-1' in name else 1;r=aft.RIBS[side]
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list);rest=collections.defaultdict(list)
    for g in groups:
        for t in np.array(g['corners'],float):
            if g['material']==20 and t[:,1].max()<-2.62:
                for i in (3,4):
                    j=i+1;quad=np.array([r['oi'][i],r['oi'][j],r['oo'][j],r['oo'][i]])
                    cs=np.array([[r['arc'][i],0],[r['arc'][j],0],[r['arc'][j],2*aft.HALF_WIDTH],[r['arc'][i],2*aft.HALF_WIDTH]])
                    co=aft.on_quad(t,quad,cs)
                    if co is not None:break
                else:raise AssertionError('lower rib projection')
                base.add(charts,t,'frame03',co,(2.25,100),(name,'panel03 lower return'))
            else:rest[g['material']].append(t)
    for g in aft.rib_map(name,package.pack(rest)):mapped[g['material']].extend(g['corners'])
    return base.complete(charts,mapped)


def main():
    prepare();base.configure();uv.PATCHES['rear03']=[(uv.S,(.002,.002,.998,.998))]
    rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp';base.REPORT.clear()
    def mapping(name,groups):
        mapper=(upper_map if name.startswith('Faceted shoulder') else core_map if name.startswith('Continuous hull')
            else rib_map if name.startswith('Aft structural') else aft.engine_map if name.startswith('Engine casing') else base.region_map)
        result=mapper(name,groups)
        bad=0.;count=0
        for g in result:
            t=np.array(g['corners']);p=t[:,:,:3];u=t[:,:,6:8]
            area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)/2
            a=u[:,1]-u[:,0];b=u[:,2]-u[:,0];ua=abs(a[:,0]*b[:,1]-a[:,1]*b[:,0])/2
            mask=(area>1e-6)&(ua<1e-12);bad+=float(area[mask].sum());count+=int(mask.sum())
        if not name.startswith(('Original','Stepped circular')):assert bad<1e-7,(name,bad)
        STATS.append(dict(object=name,owner=rig.owner(name),source_triangles=sum(len(g['corners']) for g in groups),
            export_triangles=sum(len(g['corners']) for g in result),collapsed_uv_triangles=count,collapsed_uv_area=bad))
        return result
    rig.material_map=mapping;rig.main(OUT/'mechanical_geometry.json');h=f.digest(rig.DEST)
    dump('uv_degenerate.json',dict(cmp_sha256=h,objects=STATS))
    dump('mesh_breakdown.json',dict(cmp_sha256=h,objects=STATS))
    dump('uv_layout.json',dict(cmp_sha256=h,regions=base.REPORT,continuous_side_seams=SEAMS,
        source_cmp_sha256=f.digest(PREVIOUS/'rh_pir_freighter.cmp'),installed=False))
    engines=json.loads((OUT/'engine_geometry_check.json').read_text())
    dump('engine_check.json',dict(cmp_sha256=h,engines=engines,installed=False))
    package.OUT=OUT;package.open_review()
    print('AFT_CHEVRON_READY',OUT)


if __name__=='__main__':main()
