"""Q13 top-view angular engine prototype, recessed exhaust. Offline only."""
import collections
import copy
import json
import numpy as np
import rh_freighter_uv_refine as uv

rig,f,q=uv.rig,uv.f,uv.q
PREVIOUS=uv.OUT
OUT=PREVIOUS.parent/'engines_03'
MOUTH_Z=12.158
EXHAUST_Z=11.15
ENGINE_REPORT=[]


def engine(side):
    """Closed cut-corner rectangular pod; no circular-cylinder approximation."""
    cx=side*2.08;cy=-.28
    def ring(z,w,h,cut):
        # Four broad walls and four purposeful corner planes, NOT a regular octagon.
        dx=w*cut;dy=h*cut
        xy=np.array([[-w+dx,h],[w-dx,h],[w,h-dy],[w,-h+dy],
            [w-dx,-h],[-w+dx,-h],[-w,-h+dy],[-w,h-dy]])
        return np.column_stack((xy[:,0]+cx,xy[:,1]+cy,np.full(8,z)))
    profile=[(6.82,.98,1.00,.34),(7.80,1.78,1.62,.34),
        (10.45,1.78,1.62,.34),(11.70,1.42,1.26,.30),(MOUTH_Z,1.42,1.26,.30)]
    loops=[ring(*p) for p in profile];b=q.B()
    for station,(a,c) in enumerate(zip(loops,loops[1:])):
        center=np.concatenate((a,c)).mean(0)
        for i in range(8):
            j=(i+1)%8;poly=np.array([a[i],a[j],c[j],c[i]])
            # Large flat armored fields and a light, continuous corner frame.
            role=6 if station==1 and i in (0,2,6) else 1 if i in (0,2,4,6) else 2
            b.face(poly,role,normal=poly.mean(0)-center)
    b.face(loops[0],3,normal=[0,0,-1])
    mouth=ring(MOUTH_Z,1.12,.97,.30)
    throat=ring(EXHAUST_Z,.93,.79,.30)
    # Coplanar rear lip, full depth walls, and a real front-facing floor.
    b.bridge(loops[-1],mouth,2)
    b.bridge(mouth,throat,3,inner=True)
    b.face(throat,7,normal=[0,0,1])
    gs,closure=q.coherent(b.groups())
    ENGINE_REPORT.append(dict(side=side,center_xy=[cx,cy],cross_section='cut-corner rectangular, 4 broad flats + 4 corner planes',
        profile=profile,mouth_z=MOUTH_Z,exhaust_z=EXHAUST_Z,recess_depth=MOUTH_Z-EXHAUST_Z,
        closure=closure,geometry_triangles=sum(len(g['corners']) for g in gs)))
    return dict(name=f'Engine casing - angular recessed exhaust {side:+}',groups=gs,closed=True)


def map_engine(name,groups):
    charts=collections.defaultdict(list);mapped=collections.defaultdict(list)
    for g in groups:
        role=g['material']
        for t in np.array(g['corners'],float):
            p=t[:,:3];n=np.cross(p[1]-p[0],p[2]-p[0]);n/=np.linalg.norm(n)
            if role==7:
                cx=np.sign(p[:,0].mean())*2.08
                t[:,6:8]=(p[:,[0,1]]-[cx,-.28])/1.94+.5
                mapped[uv.G].append(t);continue
            family,cell={1:('skin',(1.8,1.65)),2:('rim',(2.55,.44)),
                3:('dark',(1.45,.95)),6:('red',(1.65,.74))}[role]
            co=uv.plane_coords(p,n)
            key=(family,cell,tuple(n.round(5)),round(float(n@p.mean(0)),5))
            charts[key].append((t,co))
    stats=[]
    for (family,cell,_,_),values in charts.items():
        result,stat=uv.atlas_chart(values,family,cell,rotate=family=='rim')
        for mid,ts in result.items():mapped[mid].extend(ts)
        stats.append(stat)
    return [dict(material=mid,corners=np.array(ts),unused=204) for mid,ts in mapped.items()]


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    prior=json.loads((PREVIOUS/'build.json').read_text(encoding='utf8'))
    assert f.digest(PREVIOUS/'rh_pir_freighter.cmp')==prior['cmp_sha256'],'Prior CMP edited: carry manual HP edits before rebuilding.'
    source=rig.OUT/'mechanical_geometry.json';data=json.loads(source.read_text(encoding='utf8'))
    new=[]
    for e in data['objects']:
        if e['name'].startswith('Engine casing'):
            new.append(engine(-1 if '-1' in e['name'] else 1))
        else:new.append(e)
    data['objects']=new
    path=OUT/'mechanical_geometry.json'
    path.write_text(json.dumps(data,separators=(',',':'),default=lambda a:a.tolist() if isinstance(a,np.ndarray) else a),encoding='utf8')
    rig.OUT=OUT;rig.DEST=OUT/'rh_pir_freighter.cmp'
    rig.material_map=lambda name,gs:map_engine(name,gs) if name.startswith('Engine casing') else uv.material_map(name,gs)
    rig.main(path)
    # Everything except the two engine meshes stays numerically identical,
    # including every UV corner. Private export names are intentionally salted.
    _,oldnodes=f.mesh.read_tree((PREVIOUS/'rh_pir_freighter.cmp').read_bytes())
    _,newnodes=f.mesh.read_tree(rig.DEST.read_bytes())
    def parts(nodes):
        names=f.component_map(nodes)
        return {names[file]:gs for file,gs in f.local_geometry(nodes).items()}
    a,b=parts(oldnodes),parts(newnodes);unchanged=[]
    for name,gs in a.items():
        if name in ('port_engine_lod1','starboard_engine_lod1'):continue
        assert len(gs)==len(b[name]),name
        for x,y in zip(gs,b[name]):
            assert x['material']==y['material'] and np.array_equal(x['corners'],y['corners']),name
        unchanged.append(name)
    report=dict(source_cmp=prior['cmp'],source_cmp_sha256=prior['cmp_sha256'],
        cmp_sha256=f.digest(rig.DEST),art=str(q.ART),art_sha256=f.digest(q.ART),
        art_reference='Q13 TOP / FLIGHT: straight rectangular side walls, angular shoulders and stepped rear throat.',
        engines=ENGINE_REPORT,unchanged_meshes_and_uv=unchanged,original_hardpoints_preserved=True,
        installed=False,game_launched=False)
    rig.dump('engine_check.json',report)
    print('ENGINES_READY',MOUTH_Z-EXHAUST_Z,'recess; unchanged parts:',unchanged)

if __name__=='__main__':main()
