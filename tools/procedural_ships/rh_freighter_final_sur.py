"""Static flight SUR with actual native equipment hulls, rebuilt after HP edits."""
import collections,struct
import numpy as np
from scipy.spatial import ConvexHull
import rh_freighter_final as d
import rh_concept_b_final_damage as damage
from rh_concept_b_v2_sur import read_hulls
from ship_collision_audit import sur_parts,surface
f=d.f;sur=damage.sur

def main():
    _,nodes=d.tree(d.ASSETS/'rh_pir_freighter.cmp')
    names=f.component_map(nodes);files={v:k for k,v in names.items()};tr,_=f.audit.transforms(nodes,('Sc_extend wing',0))
    w=d.world(nodes,('Sc_extend wing',0));hps=d.hardpoints(nodes,('Sc_extend wing',0))
    own={};aggregate=[];report=[]
    for name,gs in w.items():
        if name in ('Baydoor_lod1','glass_lod1'):continue
        triangles=np.concatenate([g['corners'][...,:3] for g in gs]);bounds=[triangles.min((0,1)),triangles.max((0,1))]
        if name=='Root':cuts=[-12,-8,-4,0,4,7,11]
        elif 'engine' in name:cuts=[8,9.5,10.5,12.3]
        elif 'side' in name:cuts=[-8,-4,0,4,8]
        else:cuts=[float(bounds[0][2])-.01,float(bounds[1][2])+.01]
        hs=damage.hull_regions(triangles,f.mesh.crc(name),[[(2,a,b)] for a,b in zip(cuts,cuts[1:])])
        assert hs,name
        p=triangles.reshape(-1,3);covered=np.zeros(len(p),bool)
        for h in hs:
            cv=ConvexHull(h.points);covered|=np.all(p@cv.equations[:,:3].T+cv.equations[:,3]<5e-4,axis=1)
        assert covered.all(),(name,'uncovered',sum(~covered))
        r,t=tr[files[name].lower()];own[name]=[sur.Hull((h.points-t)@r,h.faces,h.hull_id) for h in hs]
        aggregate+=hs;report.append(dict(part=name,hulls=len(hs),all_vertices_covered=True))
    _,native=d.tree(d.SOURCE/'original.cmp');oldhp=d.hardpoints(native,('Sc_extend wing',0));ids={f.mesh.crc(h['name']):key for key,h in oldhp.items()};embedded={}
    for pid,chunks in sur_parts((d.SOURCE/'original.sur').read_bytes()):
        if pid!=f.mesh.crc('Root'):continue
        for tag,blob in chunks:
            if tag==b'surf':
                for cid,p in read_hulls(blob):
                    if cid in ids:embedded.setdefault(ids[cid],[]).append(p)
    assert 'hpmount' in embedded,'Confirm native shield link before export'
    equipment=[];hpids=collections.defaultdict(list)
    for key,h in hps.items():
        if key=='hpmount':continue
        source=key if key in embedded else None
        if source is None:
            family=next((prefix for prefix in ('hpweapon','hpturret','hpthruster','hpcm','hpmine','hpshield') if key.startswith(prefix)),None)
            if family:source=next((k for k in embedded if k.startswith(family)),None)
        if source is None:continue
        old=oldhp[source]
        for points in embedded[source]:
            local=(points-old['position'])@np.array(old['orientation']);p=local@np.array(h['orientation']).T+h['position']
            hull=sur.make_hull(p,f.mesh.crc(h['name']));owner=h['owner'];r,t=tr[files[owner].lower()]
            assert owner in own,owner
            own[owner].append(sur.Hull((hull.points-t)@r,hull.faces,hull.hull_id));aggregate.append(hull)
            hpids[owner].append(hull.hull_id)
        equipment.append(dict(name=h['name'],owner=h['owner'],template=old['name'],real_native_hulls=len(embedded[source])))
    pts=np.concatenate([h.points for h in aggregate]);envelope=sur.make_hull(pts,0);center=(pts.min(0)+pts.max(0))/2
    shield=sur.make_hull(center+(envelope.points-center)*1.06,f.mesh.crc('HpMount'))
    cv=ConvexHull(shield.points);assert np.all(pts@cv.equations[:,:3].T+cv.equations[:,3]<2e-4)
    aggregate.append(shield);hpids['Root'].append(shield.hull_id)
    raw=bytearray(b'vers'+struct.pack('<f',2.))
    for name,hs in own.items():
        root=name=='Root';ids=sorted(set(i for v in hpids.values() for i in v)) if root else sorted(set(hpids[name]))
        blob,lo,hi=sur.encode_surface(aggregate if root else hs)
        raw+=struct.pack('<II',f.mesh.crc(name),2+int(root)+int(bool(ids)))
        if root:raw+=b'!fxd'
        raw+=b'exts'+struct.pack('<6f',*lo,*hi)+b'surf'+struct.pack('<I',len(blob))+blob
        if ids:raw+=b'hpid'+struct.pack('<I',len(ids))+np.array(ids,'<u4').tobytes()
    target=d.ASSETS/'rh_pir_freighter.sur';target.write_bytes(raw)
    for pid,chunks in sur_parts(raw):
        assert (b'!fxd' in [tag for tag,_ in chunks])==(pid==f.mesh.crc('Root'))
        for tag,blob in chunks:
            if tag==b'surf':surface(blob)
    d.dump(d.OUT/'sur_check.json',dict(sha256=f.digest(target),parts=report,equipment=equipment,
        original_equipment=list(embedded),shield=dict(hardpoint='HpMount',bounds=[shield.points.min(0),shield.points.max(0)],covers_hull_and_equipment=True),pose='static extended flight',physical_bodies=['Root']))
    print('SUR READY',len(raw),'bytes;',len(equipment),'actual equipment hull bindings')

if __name__=='__main__':main()
