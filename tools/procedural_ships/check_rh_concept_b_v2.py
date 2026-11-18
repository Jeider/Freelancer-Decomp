"""Read-back checks and Blender data for the offline, user-HP-based RH B."""
import collections
import json
from pathlib import Path
import struct as S
import numpy as np
from scipy.spatial import ConvexHull
import rh_concept_b_v2 as v
import full_ship_audit as full
from rh_concept_b_engine_shell import topology
from rh_concept_b_v2_sur import read_hulls
from ship_collision_audit import sur_parts,surface
f,OUT=v.f,v.OUT


def flat(nodes):return {p.lower():n.blob for p,n in f.mesh.walk(nodes)}


def main():
    meta=json.loads((OUT/'input_manifest.json').read_text())
    for key,digest in (('source','source_sha256'),('snapshot','source_sha256'),
                       ('shared_mat','shared_mat_sha256'),('game_cmp','game_cmp_sha256')):
        assert f.digest(Path(meta[key]))==meta[digest],('Input changed',key)
    nodes=f.mesh.read_tree(v.DEST.read_bytes())[1];ff=flat(nodes);names=f.component_map(nodes)
    original=f.mesh.read_tree(v.SOURCE.read_bytes())[1];oldff=flat(original)
    now_hp=v.hp.hardpoint_records(nodes);old_hp=v.hp.hardpoint_records(original)
    by_hp={(h['owner'],h['name']):h for h in now_hp}
    assert len(now_hp)==len({h['name'].lower() for h in now_hp})==79
    for h in old_hp:
        if h['name'].lower().startswith('dp'):continue
        assert by_hp[h['owner'],h['name']]==h,h['name']
    old_leaves={p:b for p,b in oldff.items() if '/hardpoints/' in p and not p.split('/hardpoints/')[1].split('/')[1].startswith('dp')}
    assert all(ff[p]==b for p,b in old_leaves.items()),'Equipment HP leaf bytes changed'
    materials=f.audit.material_table([f.SHARED_MAT])
    assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(nodes))
    libraries={f.mesh.crc(p.split('/')[-2]):f.audit.decode(b) for p,b in ff.items() if p.endswith('/vmeshdata')}
    assert len(libraries)==sum(p.endswith('/vmeshdata') for p in ff),'Duplicate VMesh CRC'
    max_vertices=max_indices=0
    for verts,groups,indices in libraries.values():
        assert len(verts)<=65535 and len(indices)<=65535
        max_vertices=max(max_vertices,len(verts));max_indices=max(max_indices,len(indices));at=0
        for mat,lo,hi,count,_ in groups:
            ids=indices[at:at+count]+lo;at+=count
            assert mat in materials,hex(mat)
            assert not materials[mat]['texture'] or materials[mat]['image'] is not None,hex(mat)
            assert count%3==0 and ids.min()>=lo and ids.max()<=hi<len(verts)
        assert at==len(indices)
    levels=[f.local_geometry(nodes,i) for i in range(3)]
    for level in levels:
        for file,gs in level.items():
            for g in gs:
                t=g['corners'];assert np.isfinite(t).all()
                assert (np.linalg.norm(np.cross(t[:,1,:3]-t[:,0,:3],t[:,2,:3]-t[:,0,:3]),axis=1)>1e-9).all()
                assert np.allclose(np.linalg.norm(t[...,3:6],axis=-1),1,atol=1e-4)
                m=materials[g['material']]
                if 'metal' in m['texture'].lower():assert file.lower().startswith('baydoor') or names[file]=='Root'
    engines={}
    for file,gs in levels[0].items():
        if '_engine_' not in file.lower():continue
        t=np.concatenate([g['corners'] for g in gs]);engines[file]=topology(t)
        assert not any(engines[file].values()),engines[file]
    joints=full.constructs(ff);channels=full.channels(ff,joints)
    oj=full.constructs(oldff);oc=full.channels(oldff,oj);old_tracks={(c['script'],c['child']):c for c in oc}
    errors=[]
    for c in channels:
        assert c['native_size_valid'] and c['bound_joint'] and c['finite'] and not c.get('parent_mismatch')
        old=old_tracks[c['script'],c['child']]
        for time in np.linspace(0,c['duration'],17):
            a=np.interp(time,c['times'],np.array(c['values'])[:,0]);b=np.interp(time,old['times'],np.array(old['values'])[:,0])
            na=full.matrices(joints,{c['child'].lower():[a]})[c['child'].lower()]
            nb=full.matrices(oj,{c['child'].lower():[b]})[c['child'].lower()]
            errors.append(max(float(np.max(abs(na[0]-nb[0]))),float(np.max(abs(na[1]-nb[1])))))
    assert max(errors)<2e-6,max(errors)
    unfolded=f.mesh.read_tree((OUT/'unfolded_reference.cmp').read_bytes())[1]
    utr,_=f.audit.transforms(unfolded);rest,_=f.audit.transforms(nodes)
    pose0,_=f.audit.transforms(nodes,('Sc_extend wing',0));pose1,_=f.audit.transforms(nodes,('Sc_extend wing',1))
    launch,_=f.audit.transforms(nodes,('Sc_launch extend',1))
    for file in names:
        for expected,actual in ((utr,pose0),(rest,pose1),(pose0,launch)):
            assert all(np.allclose(a,b,atol=2e-6) for a,b in zip(expected[file.lower()],actual[file.lower()]))
    wire=[(p,b) for p,b in ff.items() if p.endswith('/vwiredata')];assert len(wire)==1
    _,crc,bias,remap,count,nv=S.unpack_from('<II4H',wire[0][1])
    ids=np.frombuffer(wire[0][1],'<u2',offset=16);verts=libraries[crc][0]
    assert len(ids)==count and count%2==0 and len(set(ids))==remap
    assert ids.max()<nv and bias+nv<=len(verts)
    wire_points=verts[bias+ids,:3].reshape(-1,2,3)
    manifest=json.loads((OUT/'wire_manifest.json').read_text())
    assert np.allclose(wire_points,np.array(manifest['lines']),atol=2e-6)
    collision={};fixed=[];hpids={}
    for pid,chunks in sur_parts((OUT/'rh_concept_b.sur').read_bytes()):
        tags=dict(chunks)
        surface(tags[b'surf']);collision[pid]=[(cid,ConvexHull(p)) for cid,p in read_hulls(tags[b'surf'])]
        if b'!fxd' in tags:fixed.append(pid)
        hpids[pid]=set(np.frombuffer(tags.get(b'hpid',b''),'<u4').tolist())
    root=f.mesh.crc('Root');assert fixed==[root]
    coverage=[]
    for file,gs in levels[0].items():
        part=names[file];cid=f.mesh.crc(part)
        if cid not in collision:continue
        points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in gs]);r,t=utr[file.lower()]
        world=points@r.T+t
        for owner,samples in ((cid,points),(root,world)):
            covered=np.zeros(len(samples),bool)
            for client,hull in collision[owner]:
                if client==cid:covered|=np.all(samples@hull.equations[:,:3].T+hull.equations[:,3]<3e-4,axis=1)
            assert covered.all(),(part,owner,int((~covered).sum()))
            coverage.append(dict(part=part,owner=owner,samples=len(samples),uncovered=0))
    hp_by_name={h['name'].lower():h for h in now_hp}
    sur_meta=json.loads((OUT/'sur_manifest.json').read_text())
    for e in sur_meta['equipment']:
        cid=f.mesh.crc(e['name']);owner=f.mesh.crc(e['owner'])
        assert cid in hpids[root] and cid in hpids[owner]
        hulls=[h for i,h in collision[root] if i==cid];assert hulls
        assert max(np.ptp(h.points,axis=0).max() for h in hulls)>.3
    shield=[h for i,h in collision[root] if i==f.mesh.crc('HpMount')];assert len(shield)==1
    pts=np.concatenate([h.points for i,h in collision[root] if i!=f.mesh.crc('HpMount')])
    assert np.all(pts@shield[0].equations[:,:3].T+shield[0].equations[:,3]<3e-4)
    damages=json.loads((OUT/'damage_manifest.json').read_text());assert len(damages)==5
    config=list(f.audit.sections(OUT/'shiparch_fragment.ini'))
    groups={data['obj'][0].lower():data for kind,data in config if kind=='collisiongroup'}
    for d in damages:
        group=groups[d['part'].lower()]
        assert group['group_dmg_hp']==[d['debris_hardpoint']]
        assert hp_by_name[d['debris_hardpoint'].lower()]['owner']==d['part']
        for k in ('parent','debris'):
            path=OUT/d[k]['file'];assert f.digest(path)==d[k]['sha256']
            cap=f.mesh.read_tree(path.read_bytes())[1]
            assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(cap))
            for p,n in f.mesh.walk(cap):
                if p.lower().endswith('/vmeshdata'):
                    _,ms,_=f.audit.decode(n.blob);assert all(m[0] in materials for m in ms)
            assert any(p.endswith('/dpconnect/position') for p in flat(cap))
            for pid,chunks in sur_parts(path.with_suffix('.sur').read_bytes()):surface(dict(chunks)[b'surf'])
    ship=next(data for kind,data in config if kind=='ship')
    assert all('rh_concept_b_lods' not in path for path in ship['material_library'])
    report=dict(cmp_sha256=f.digest(v.DEST),sur_sha256=f.digest(OUT/'rh_concept_b.sur'),
        unchanged_inputs=True,hardpoints=len(now_hp),equipment_hardpoint_leaf_bytes_preserved=True,
        engines=engines,animation_max_error=max(errors),animation_samples=len(errors),
        folded_rest=True,launch_continuity=True,static_unfolded_sur=True,collision_coverage=coverage,
        embedded_equipment=len(sur_meta['equipment']),shield_covers_hull_and_equipment=True,
        wire_edges=count//2,wire_pose='static unfolded Root',damage_caps=10,unique_damage_names=True,
        lod_triangles=[sum(len(g['corners']) for gs in lv.values() for g in gs) for lv in levels],
        max_vertices=max_vertices,max_indices=max_indices,materials_external=True,
        weapon05_06_coincident=by_hp['Root','HpWeapon05']['position']==by_hp['Root','HpWeapon06']['position'])
    v.dump('validation.json',report)
    build=json.loads((OUT/'build.json').read_text());build['cmp_sha256']=report['cmp_sha256']
    build['lod_triangles']=report['lod_triangles'];v.dump('build.json',build)
    js={j['name']:dict(j,axis=j.get('axis',[0,1,0])) for j in joints}
    js['Root']=dict(parent=None,origin=[0,0,0],rotation=np.eye(3).tolist(),axis=[0,1,0])
    scripts=collections.defaultdict(list)
    for c in channels:scripts[c['script']].append(dict(child=c['child'],keys=list(zip(c['times'],np.array(c['values'])[:,0]))))
    poses={}
    for label,tr in (('rest',rest),('unfolded',pose0)):
        poses[label]={names[file]:dict(rotation=r,position=t) for file,(r,t) in ((file,tr[file.lower()]) for file in names)}
    v.dump('blender_data.json',dict(joints=js,scripts=scripts,hardpoints=now_hp,cmp_sha256=report['cmp_sha256'],poses=poses,
        levels=[{names[file]:gs for file,gs in lv.items()} for lv in levels]))
    print('V2 CHECKS OK',json.dumps({k:report[k] for k in ('hardpoints','animation_samples','wire_edges','lod_triangles','embedded_equipment','weapon05_06_coincident')}),flush=True)


if __name__=='__main__':main()
