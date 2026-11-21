"""Static expanded collision, real native HP hulls, rebuilt shield envelope."""
import collections,struct
import numpy as np
from scipy.spatial import ConvexHull
import rh_fighter_final as d
import rh_fighter_final_mounts as mounts
import rh_concept_b_final_damage as damage
from rh_concept_b_v2_sur import read_hulls
from ship_collision_audit import sur_parts,surface
f=d.f;sur=damage.sur

def physical(name):
    for side in ('port','starboard'):
        if name.startswith(side+'_wing_'):return side+'_wing_lod1'
    return name if name.endswith('_engine_lod1') else 'Root'

def main():
    _,ns=d.tree(d.ASSETS/'rh_pir_fighter.cmp');w=d.world(ns,('Sc_extend wing',0));hp=d.hardpoints(ns,('Sc_extend wing',0))
    grouped=collections.defaultdict(list)
    for name,gs in w.items():grouped[physical(name)]+=gs
    own={};aggregate=[];report=[]
    for name,gs in grouped.items():
        triangles=np.concatenate([g['corners'][...,:3] for g in gs]);lo=triangles.min((0,1));hi=triangles.max((0,1))
        # Regional hulls preserve separate cockpit/body/drum and wide wing sweep.
        cuts=np.linspace(lo[2]-.01,hi[2]+.01,8 if name=='Root' else 5)
        hs=damage.hull_regions(triangles,f.mesh.crc(name),[[(2,a,b)] for a,b in zip(cuts,cuts[1:])]);assert hs
        p=triangles.reshape(-1,3);covered=np.zeros(len(p),bool)
        for h in hs:
            cv=ConvexHull(h.points);covered|=np.all(p@cv.equations[:,:3].T+cv.equations[:,3]<5e-4,axis=1)
        assert covered.all(),(name,sum(~covered))
        own[name]=hs.copy();aggregate+=hs;report.append(dict(part=name,hulls=len(hs),all_vertices_covered=True))
    _,native=d.tree(d.SOURCE/'original.cmp');oldhp=d.hardpoints(native,('Sc_extend wing',0));ids={f.mesh.crc(h['name']):k for k,h in oldhp.items()};embedded={}
    for pid,chunks in sur_parts((d.SOURCE/'original.sur').read_bytes()):
        if pid!=f.mesh.crc('Root'):continue
        for tag,blob in chunks:
            if tag==b'surf':
                for cid,p in read_hulls(blob):
                    if cid in ids:embedded.setdefault(ids[cid],[]).append(p)
    assert 'hpmount' in embedded,'Verify native HpMount shield, not generator HpShield01'
    equipment=[];hpids=collections.defaultdict(list)
    for key,h in hp.items():
        if key=='hpmount':continue
        if key in mounts.EQUIPMENT:
            parts,ref=mounts.equipment_reference(key);owner=physical(h['owner'])
            for gs in parts:
                local=d.points(gs);p=local@np.array(h['orientation']).T+h['position']
                hull=sur.make_hull(p,f.mesh.crc(h['name']))
                own[owner].append(hull);aggregate.append(hull);hpids[owner].append(hull.hull_id)
            equipment.append(dict(name=h['name'],visual_owner=h['owner'],collision_owner=owner,
                                  template='current actual equipment geometry',real_equipment_hulls=len(parts),reference=ref))
            continue
        source=key if key in embedded else None
        if source is None:
            family=next((p for p in ('hpweapon','hptorpedo','hpthruster','hpcm','hpmine','hpshield') if key.startswith(p)),None)
            if family:source=next((k for k in embedded if k.startswith(family)),None)
        if source is None:continue
        old=oldhp[source];owner=physical(h['owner'])
        for points in embedded[source]:
            local=(points-old['position'])@np.array(old['orientation']);p=local@np.array(h['orientation']).T+h['position'];hull=sur.make_hull(p,f.mesh.crc(h['name']))
            own[owner].append(hull);aggregate.append(hull);hpids[owner].append(hull.hull_id)
        equipment.append(dict(name=h['name'],visual_owner=h['owner'],collision_owner=owner,template=old['name'],real_native_hulls=len(embedded[source])))
    points=np.concatenate([h.points for h in aggregate]);center=(points.min(0)+points.max(0))/2;envelope=sur.make_hull(points,0)
    shield=sur.make_hull(center+(envelope.points-center)*1.06,f.mesh.crc('HpMount'));cv=ConvexHull(shield.points)
    assert np.all(points@cv.equations[:,:3].T+cv.equations[:,3]<2e-4)
    aggregate.append(shield);hpids['Root'].append(shield.hull_id);raw=bytearray(b'vers'+struct.pack('<f',2.))
    for name,hs in own.items():
        root=name=='Root';ids=sorted(set(i for vs in hpids.values() for i in vs)) if root else sorted(set(hpids[name]));blob,lo,hi=sur.encode_surface(aggregate if root else hs)
        raw+=struct.pack('<II',f.mesh.crc(name),2+int(root)+int(bool(ids)))
        if root:raw+=b'!fxd'
        raw+=b'exts'+struct.pack('<6f',*lo,*hi)+b'surf'+struct.pack('<I',len(blob))+blob
        if ids:raw+=b'hpid'+struct.pack('<I',len(ids))+np.array(ids,'<u4').tobytes()
    target=d.ASSETS/'rh_pir_fighter.sur';target.write_bytes(raw)
    for pid,chunks in sur_parts(raw):
        assert (b'!fxd' in [tag for tag,_ in chunks])==(pid==f.mesh.crc('Root'))
        for tag,blob in chunks:
            if tag==b'surf':surface(blob)
    d.dump(d.OUT/'sur_check.json',dict(sha256=f.digest(target),parts=report,equipment=equipment,original_embedded=list(embedded),
        shield=dict(hardpoint='HpMount',bounds=[shield.points.min(0),shield.points.max(0)],covers_hull_and_equipment=True),pose='static extended flight',physical_bodies=['Root']))
    print('SUR READY',len(raw),'bytes;',len(equipment),'actual equipment HP hulls',flush=True)

if __name__=='__main__':main()
