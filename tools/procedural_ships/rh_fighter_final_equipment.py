"""Equipment hull clearance against the actual cargo-leaf sweep."""
import numpy as np
from scipy.spatial import ConvexHull
import rh_fighter_final as d
import rh_fighter_final_mounts as mounts
from rh_concept_b_v2_sur import read_hulls
from ship_collision_audit import sur_parts
f=d.f

def clipped(triangle,equations):
    poly=triangle.copy()
    for eq in equations:
        if not len(poly):return poly
        out=[]
        for a,b in zip(poly,np.roll(poly,-1,axis=0)):
            da=a@eq[:3]+eq[3];db=b@eq[:3]+eq[3];ia=da<=-1e-5;ib=db<=-1e-5
            if ia:out.append(a)
            if ia!=ib:out.append(a+(b-a)*(da/(da-db)))
        poly=np.array(out)
    return poly

def main():
    _,ns=d.tree(d.ASSETS/'rh_pir_fighter.cmp');hp=d.hardpoints(ns,('Sc_extend wing',0));geo=d.world(ns,('Sc_extend wing',0));hulls={};ids={f.mesh.crc(h['name']):key for key,h in hp.items()}
    for pid,chunks in sur_parts((d.ASSETS/'rh_pir_fighter.sur').read_bytes()):
        if pid!=f.mesh.crc('Root'):continue
        for tag,blob in chunks:
            if tag==b'surf':
                for cid,p in read_hulls(blob):
                    if cid in ids and (ids[cid].startswith(('hpweapon','hpshield')) or ids[cid] in mounts.EQUIPMENT):hulls.setdefault(ids[cid],[]).append(p)
    collisions=[];equipment=[];wing_clearance={}
    for key,parts in hulls.items():
        for part in parts:
            cv=ConvexHull(part);lo=part.min(0);hi=part.max(0);equipment.append((key,cv,lo,hi))
        if hp[key]['owner'].endswith('_wing_mesh'):
            gap=100
            for time in np.linspace(0,2,61):
                r,t=d.runtime(ns,time)[hp[key]['owner'].lower()]
                for p in parts:gap=min(gap,float(abs((p@r.T+t)[:,0]).min()-1.712))
            assert gap>.1,(key,gap);wing_clearance[key]=gap
    for time in np.linspace(0,2.1333333,61):
        poses=d.runtime(ns,time,'Sc_open baydoor')
        for side in ('port','starboard'):
            name=side+'_baydoor_lod1';r,t=poses[name];p=np.concatenate([g['corners'][...,:3] for g in geo[name]])@r.T+t
            for key,cv,lo,hi in equipment:
                if hp[key]['owner']!='Root':continue
                for tri in p:
                    if np.any(tri.max(0)<lo) or np.any(tri.min(0)>hi):continue
                    poly=clipped(tri,cv.equations)
                    if len(poly)>=3 and np.linalg.norm(np.cross(poly[1]-poly[0],poly[2]-poly[0]))>1e-7:
                        collisions.append(dict(time=float(time),door=name,equipment=key));break
    mounts_verified={}
    for key in mounts.EQUIPMENT:
        h=hp[key];parts,ref=mounts.equipment_reference(key)
        local=np.concatenate([d.points(gs) for gs in parts]);points=local@h['orientation'].T+h['position']
        covered=np.zeros(len(points),bool)
        for p in hulls[key]:
            cv=ConvexHull(p);covered|=np.all(points@cv.equations[:,:3].T+cv.equations[:,3]<4e-5,axis=1)
        assert covered.all(),key
        # HpConnect's Y points out of the hull / mounting plane.
        assert local[:,1].min()>-.015,(key,local[:,1].min())
        mounts_verified[key]=dict(owner=h['owner'],actual_equipment_vertices=len(points),all_vertices_covered=True,
                                  mount_normal_gap=float(local[:,1].min()),world_bounds=[points.min(0),points.max(0)])
    volumes={};source={o['name']:o['groups'] for o in d.read('blender_input.json')['objects']}
    def volume(gs):
        p=np.concatenate([g['corners'][...,:3] for g in d.packed(gs)]);return abs(np.einsum('ij,ij->i',p[:,0],np.cross(p[:,1],p[:,2])).sum()/6)
    for name,gs in d.read('damage_world.json').items():
        before=source[name+('_mesh' if name.endswith('wing') else '_lod1')];ratio=volume(gs)/volume(before);assert ratio>.20
        volumes[name]=float(ratio)
    d.dump(d.OUT/'equipment_check.json',dict(cmp_sha256=f.digest(d.ASSETS/'rh_pir_fighter.cmp'),sur_sha256=f.digest(d.ASSETS/'rh_pir_fighter.sur'),samples=61,
        wing_equipment_clearance=wing_clearance,cargo_collisions=collisions,equipment_mounts_verified=mounts_verified,
        damage_volume_retained=volumes,gun_hulls='real native collision geometry; visual equipment variants may differ'))
    assert not collisions,collisions[:8]
    print('EQUIPMENT CLEARANCE PASS',wing_clearance,'damage remaining',volumes,flush=True)

if __name__=='__main__':main()
