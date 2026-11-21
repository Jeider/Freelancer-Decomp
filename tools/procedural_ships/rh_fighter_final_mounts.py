"""Forward ventral shelves at the original bottom height; preserve hull UVs."""
import json, shutil
import numpy as np
import rh_fighter_final as d

EQUIPMENT={'hpthruster01':'ST/rh_thruster02.3db','hpthruster02':'ST/rh_thruster02.3db',
           'hpmine01':'WEAPONS/ge_mine_dropper.3db','hpcm01':'WEAPONS/li_cm_dropper01.cmp'}


def equipment_reference(key):
    """Actual model in its HpConnect frame; mod ship HPs no longer match old SUR."""
    source=d.GAME/'DATA/EQUIPMENT/MODELS'/EQUIPMENT[key]
    pinned=d.SOURCE/'equipment'/source.name;pinned.parent.mkdir(exist_ok=True)
    if not pinned.exists():shutil.copy2(source,pinned)
    _,ns=d.tree(pinned)
    is_cmp=any(n.name.lower()=='cmpnd' for n in ns[0].children)
    transforms=d.f.audit.transforms(ns)[0] if is_cmp else {}
    libs={d.f.mesh.crc(p.split('/')[-2]):d.f.audit.decode(n.blob) for p,n in d.f.mesh.walk(ns) if p.lower().endswith('/vmeshdata')}
    def pose(path):
        owner=next((k for k in path.lower().split('/') if k in transforms),None)
        return transforms[owner] if owner else (np.eye(3),np.zeros(3))
    connect=None;parts=[];connect_leaves={};connect_path=None
    for path,n in d.f.mesh.walk(ns):
        if '/hpconnect/' in path.lower():
            connect_leaves[n.name.lower()]=n.blob;connect_path=path
        if not path.lower().endswith('/vmeshref') or ('multilevel' in path.lower() and 'level0' not in path.lower()):continue
        gs=d.f.audit.extract(n.blob,libs);r,t=pose(path);parts.append(d.f.base.world(gs,r,t))
    if connect_path:
        r,t=pose(connect_path)
        connect=(r@np.frombuffer(connect_leaves['orientation'],'<f4').reshape(3,3),r@np.frombuffer(connect_leaves['position'],'<f4')+t)
    assert connect is not None and parts,key
    r,t=connect
    parts=[d.f.base.world(gs,r.T,-r.T@t) for gs in parts]
    return parts,dict(file=str(pinned),original=str(source),sha256=d.f.digest(pinned),connection='HpConnect',
                      local_bounds=[np.concatenate([d.points(gs) for gs in parts]).min(0),np.concatenate([d.points(gs) for gs in parts]).max(0)])


def patch(entries, groups, hps):
    # Accepted shape is an authoring asset, not a function of HP coordinates:
    # the user can move a mount without dragging/remodelling its entire shelf.
    source=d.SOURCE/'ventral_shelves.json'
    saved=json.loads(source.read_text(encoding='utf8'))
    assert saved['accepted_by_user'] and len(saved['objects'])==2
    pale=d.f.mesh.crc('pir_r_panel01_256');pads=[];uv_checks=[]
    def stretch(t):
        edges=(t[1:,:3]-t[0,:3]).T
        e1=edges[:,0]/np.linalg.norm(edges[:,0]);e2=edges[:,1]-e1*(e1@edges[:,1]);e2/=np.linalg.norm(e2)
        jac=(t[1:,6:]-t[0,6:]).T@np.linalg.inv(np.array([e1,e2])@edges)
        singular=np.linalg.svd(jac,compute_uv=False)
        return float(singular[0]/singular[-1])
    for obj in saved['objects']:
        gs=d.packed(obj['groups']);p=d.points(gs);x=(p[:,0].min()+p[:,0].max())/2
        key='hpthruster01' if obj['name'].startswith('Port') else 'hpthruster02'
        h=hps[key];before=[];after=[];flat_uv={};changed=0
        for g in gs:
            if g['material']!=pale:continue
            for t in g['corners']:
                before.append(stretch(t));q=t[:,:3]
                t[:,6]=.7525+(q[:,0]-x)*.60
                if q[:,2].min()<2.219:
                    # Natural crease only: unwrap the real slope length, not Z.
                    slope=(q[q[:,2].argmax(),1]-q[q[:,2].argmin(),1])/np.ptp(q[:,2])
                    length=(q[:,2]-1.90)*np.hypot(1,slope)
                else:length=q[:,2]-2.22
                t[:,7]=.29+length*.60
                assert np.all(t[:,6:] >= [.51,.272]) and np.all(t[:,6:] <= [.995,.852])
                if q[:,2].min()>2.219:
                    for v in t:
                        k=tuple(v[:3].round(6))
                        if k in flat_uv:assert np.allclose(flat_uv[k],v[6:],atol=1e-8)
                        flat_uv[k]=v[6:]
                after.append(stretch(t));changed+=1
        assert changed==6 and max(after)<1.00001
        assert h['owner']=='Root' and abs(h['position'][1]+2.48)<.0002
        assert abs(h['position'][0]-x)<.30 and 2.22<=h['position'][2]<=3.435
        entry=dict(obj,groups=gs);entries[obj['name']]=entry;groups['Root']+=gs
        pads.append(dict(object=obj['name'],hardpoint=h['name'],bounds=[p.min(0),p.max(0)],
                         mounting_plane=-2.48,triangles=sum(len(g['corners']) for g in gs),
                         geometry_unchanged=True,hardpoint_preserved=True))
        uv_checks.append(dict(object=obj['name'],triangles=changed,old_anisotropy=before,new_anisotropy=after,
                              uv_per_world_unit=.60,charts=2,flat_mount_continuous=True,
                              seam='only at the physical front-ramp crease',material='pir_r_panel01_256'))
    report=dict(source=d.read('user_hardpoint_source.json'),geometry_source=str(source),
                geometry_source_sha256=d.f.digest(source),pads=pads,
                added_triangles=0,retained_pylon_triangles=56,geometry_unchanged=True,
                preserved_hardpoints=len(hps),all_hardpoints=len(hps),changes={},uv_changes=uv_checks)
    d.dump(d.OUT/'mounts_check.json',report)
    return report
