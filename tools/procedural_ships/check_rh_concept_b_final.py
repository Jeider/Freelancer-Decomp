"""Read back delivered CMP/3DB/SUR/INI, including animated part ownership."""
import collections
import copy
import json
from pathlib import Path
import struct as S
import numpy as np
from scipy.spatial import ConvexHull
import rh_concept_b_final as f
import full_ship_audit as full
from ship_collision_audit import sur_parts,surface

mesh,audit,b=f.mesh,f.audit,f.b
OUT=f.OUT


def leaf_hulls(data):
    result=[]
    def walk(at):
        right,ledge=S.unpack_from('<ii',data,at)
        if right:walk(at+28);walk(at+right);return
        start=at+ledge;poff,client,flags,count,_=S.unpack_from('<iIIHH',data,start)
        indices={S.unpack_from('<H',data,start+20+i*16+k*4)[0] for i in range(count) for k in range(3)}
        points=np.array([S.unpack_from('<3f',data,start+poff+i*16) for i in indices])
        hull=ConvexHull(points);result.append((client,hull))
    walk(S.unpack_from('<i',data,32)[0]);return result


def ray_hits(hulls,origin,direction):
    for _,hull in hulls:
        near,far=0.,1e9
        for eq in hull.equations:
            a=eq[:3]@direction;bb=eq[:3]@origin+eq[3]
            if abs(a)<1e-9:
                if bb>1e-5:far=-1;break
            elif a<0:near=max(near,-bb/a)
            else:far=min(far,-bb/a)
        if far>=near:return True
    return False


def check():
    assembly=json.loads((OUT/'assembly.json').read_text())
    shift=np.array(assembly.get('center_shift_native',[0,0,0]))
    _,ns=mesh.read_tree(f.DEST.read_bytes());flat={p.lower():n.blob for p,n in mesh.walk(ns)}
    joints=full.constructs(flat);channels=full.channels(flat,joints)
    assert channels and all(c['bound_joint'] and c['native_size_valid'] and c['finite'] and not c.get('parent_mismatch') for c in channels)
    tracks={(c['script'],c['child']):c for c in channels}
    for c in channels:
        if c['script']=='sc_launch extend':assert np.allclose(c['last'],tracks['sc_extend wing',c['child']]['first'])
    report=dict(cmp_sha256=f.digest(f.DEST),parts=f.component_map(ns),channels=len(channels),lods=[],hardpoints=[],source_unchanged=False)
    mats=audit.material_table([f.SHARED_MAT,f.LOD_MAT])
    assert f.SHARED_MAT.exists() and f.LOD_MAT.exists()
    assert not any(n.name.lower() in ('material library','texture library') for _,n in mesh.walk(ns))
    maxv=maxi=0
    for p,blob in flat.items():
        if not p.endswith('/vmeshdata'):continue
        v,groups,idx=audit.decode(blob);assert len(v)<65536 and len(idx)<65536
        maxv=max(maxv,len(v));maxi=max(maxi,len(idx));at=0
        for mat,lo,hi,count,_ in groups:
            assert mat in mats,(p,hex(mat));ids=idx[at:at+count]+lo
            assert count%3==0 and ids.min()>=lo and ids.max()<=hi<len(v);at+=count
        assert at==len(idx)
    for lv in range(3):
        parts=f.local_geometry(ns,lv);count=0
        for file,groups in parts.items():
            for g in groups:
                a=g['corners'];count+=len(a)
                assert np.isfinite(a).all();assert np.allclose(np.linalg.norm(a[...,3:6],axis=-1),1,atol=1e-4)
                area=np.linalg.norm(np.cross(a[:,1,:3]-a[:,0,:3],a[:,2,:3]-a[:,0,:3]),axis=1)
                assert (area>1e-9).all(),(lv,file,float(area.min()))
        report['lods'].append(count)
    assert report['lods'][0]>report['lods'][1]>report['lods'][2]
    # Every original named hardpoint survives; check all mounts, not just weapons.
    source_audit=json.loads((Path(__file__).resolve().parents[2]/'out/ship_design/analysis/full_models/models/rh_pir_elite_b7ff51cb.json').read_text())
    old={hp['name'].lower() for hp in source_audit['hardpoints']};current=f.hp_world(ns)
    assert set(old)<=set(current)
    for p,blob in flat.items():
        if '/hardpoints/' in p and p.endswith('/orientation'):
            r=np.frombuffer(blob,'<f4').reshape(3,3);assert np.allclose(r.T@r,np.eye(3),atol=2e-5) and np.linalg.det(r)>.999
    report['original_hardpoints']=len(old);report['named_hardpoints']=len(current)
    report['hardpoints']=list(current.values())
    for kind,values in audit.sections(OUT/'shiparch_fragment.ini'):
        if kind=='ship':
            for row in values.get('hp_type',[]):
                assert all(name.strip().lower() in current for name in row.split(',')[1:]),row
    damages=json.loads((OUT/'damage_manifest.json').read_text());assert len(damages)==5
    simple={v['da_archetype'][0].replace('\\','/').lower().rsplit('/',1)[-1]:v
            for kind,v in audit.sections(OUT/'shiparch_fragment.ini') if kind=='simple'}
    cap_materials=[]
    for d in damages:
        assert d['hardpoint'] in current
        assert d['part'] in report['parts'].values()
        for key in ('parent','debris'):
            target=OUT/d[key]['file'];assert target.exists() and target.with_suffix('.sur').exists()
            assert f.digest(target)==d[key]['sha256']
            _,cap=mesh.read_tree(target.read_bytes());cf={p.lower():n.blob for p,n in mesh.walk(cap)}
            assert not any(n.name.lower() in ('material library','texture library') for _,n in mesh.walk(cap)),target
            paths=[audit.DATA/p for p in simple[target.name.lower()]['material_library']]
            assert paths==[b.prior.LIBRARY] and all(p.exists() for p in paths)
            shared=audit.material_table([f.SHARED_MAT]);used=set()
            for p,blob in cf.items():
                if p.endswith('/vmeshdata'):
                    _,material_groups,_=audit.decode(blob);used.update(g[0] for g in material_groups)
            assert used and all(m in shared and shared[m]['image'] is not None for m in used),(target,used)
            cap_materials.append(dict(file=target.name,bytes=target.stat().st_size,shared_mat=str(paths[0]),materials=[shared[m]['name'] for m in sorted(used)]))
            assert any(p.endswith('/dpconnect/position') and len(v)==12 for p,v in cf.items())
            for _,chunks in sur_parts(target.with_suffix('.sur').read_bytes()):surface(dict(chunks)[b'surf'])
    # Independent serialized collision readback and sample coverage.
    collision={pid:leaf_hulls(dict(chunks)[b'surf']) for pid,chunks in sur_parts((OUT/'rh_concept_b.sur').read_bytes())}
    coverage=[];tr,_=audit.transforms(ns)
    for file,gs in f.local_geometry(ns).items():
        name=report['parts'][file];crc=mesh.crc(name)
        if crc not in collision:continue  # glass and cargo doors use the root body
        tris=np.concatenate([g['corners'][...,:3] for g in gs]);r,t=tr[file.lower()]
        samples=np.concatenate((tris.reshape(-1,3),tris.mean(1)))
        for owner,points in ((crc,samples),(mesh.crc('Root'),samples@r.T+t)):
            covered=np.zeros(len(points),bool)
            for client,h in collision[owner]:
                if client!=crc:continue
                covered |= np.all(points@h.equations[:,:3].T+h.equations[:,3]<=3e-4,axis=1)
            coverage.append(dict(part=name,owner=owner,samples=len(points),uncovered=int((~covered).sum())))
    report['collision_coverage']=coverage
    assert all(x['uncovered']==0 for x in coverage),[x for x in coverage if x['uncovered']]
    report['tail_gap_open']=not ray_hits(collision[mesh.crc('Root')],np.array([20.,4.5,9.7])+shift,np.array([-1.,0,0]))
    assert report['tail_gap_open'],'Collision filled the negative space above the drum'
    assembly=json.loads((OUT/'assembly.json').read_text())
    # Destruction removes only the rear upright, not the upper/lower frame or
    # drum. Check the serialized geometry and SUR, including both damage caps.
    split=assembly['split'];tail_id=mesh.crc('Rh_tail_lod1');root_id=mesh.crc('Root')
    for lv in range(3):
        gs=f.local_geometry(ns,lv)[split['tail']];r,t=tr[split['tail'].lower()]
        points=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in gs])@r.T+t
        assert points[:,1].min()>=split['cut_y']-1e-4
        assert points[:,1].max()<=split['cut_top_y']+1e-4
    tail_damage=next(d for d in damages if d['zone']=='tail')
    cap_hulls=[h for _,chunks in sur_parts((OUT/tail_damage['parent']['file']).with_suffix('.sur').read_bytes())
               for h in leaf_hulls(dict(chunks)[b'surf'])]
    rear_checks=[]
    for y in (1.4,3.3):
        origin=np.array([20.,y,12.4])+shift;direction=np.array([-1.,0.,0.])
        intact=ray_hits([h for h in collision[root_id] if h[0]==tail_id],origin,direction)
        body=ray_hits([h for h in collision[root_id] if h[0]==root_id],origin,direction)
        cap=ray_hits(cap_hulls,origin-np.array(tail_damage['anchor']),direction)
        assert intact and not body and not cap,('rear upright collision',y,intact,body,cap)
        rear_checks.append(dict(y=y,intact_hit=intact,surviving_body_hit=body,damage_cap_hit=cap))
    for name in ('hprunninglight03','hprunninglight04','hpturret02','hpturret03'):
        assert current[name]['file']==split['body'],name
    for name in ('hpcm01','hpmine01','hpthruster01','hpthruster02'):
        assert current[name]['file']==(split['tail'] if 'approved_tail_blend_sha256' in assembly else split['body'] if name in ('hpcm01','hpmine01') else split['tail']),name
    report['rear_only_destruction']=dict(collision_rays=rear_checks,all_lods_rear_only=True)
    assert f.digest(b.DEST)==assembly['accepted_sha256'] and source_audit['sha256']==assembly['original_sha256']
    installed_hash=f.digest(b.base.SOURCE);materials=json.loads((OUT/'materials_manifest.json').read_text())
    assert f.digest(Path(assembly['original']))==assembly['original_sha256']
    assert installed_hash in (assembly['original_sha256'],materials['cmp_before_sha256'],report['cmp_sha256'],assembly.get('installed_before_sha256'))
    report['source_unchanged']=installed_hash==assembly['original_sha256']
    report['original_reference']=dict(sha256=source_audit['sha256'],installed_cmp_sha256=installed_hash,hardpoint_basis='archived original model audit')
    report['shared_mat_sha256']=f.digest(f.SHARED_MAT)
    report['directx']=dict(max_vertices=maxv,max_indices=maxi,limit=65535)
    report['damage_caps']=10
    report['damage_shared_materials']=cap_materials
    wire_counts={}
    for file in report['parts']:
        part=mesh.child(ns[0],file);wire=mesh.child(mesh.child(part,'VMeshWire'),'VWireData').blob
        lv=mesh.child(mesh.child(mesh.child(mesh.child(part,'MultiLevel'),'Level1'),'VMeshPart'),'VMeshRef').blob
        assert S.unpack_from('<I',wire,4)[0]==S.unpack_from('<I',lv,4)[0],('Wire must reference second LOD',file)
        assert len(wire)==16+S.unpack_from('<H',wire,12)[0]*2
        wire_counts[file]=S.unpack_from('<H',wire,12)[0]//2
    report['wire_lod']=1;report['wire_lines']=wire_counts
    # Independent native transforms for a reopened Blender comparison.
    single=copy.deepcopy(ns)
    for file in f.component_map(single):
        ml=mesh.child(mesh.child(single[0],file),'MultiLevel')
        ml.children=[n for n in ml.children if n.name in ('Switch2','Level0')]
    samples=[]
    names=f.component_map(single)
    for frame in (1,25,37,49,61,73,84,97,109,121,133,145,169,185,201,225,241,257):
        phase=0 if frame<=25 or frame>=145 else (frame-25)/48 if frame<73 else 1 if frame<=97 else 1-(frame-97)/48
        door=max(0,min(1,(frame-169)/32)) if frame<225 else max(0,1-(frame-225)/32)
        posed=b.native.evaluate_pose(single,phase,door);entry=dict(frame=frame,objects=[])
        for file in names:
            pts=np.concatenate([g['corners'][...,:3].reshape(-1,3) for g in posed if g['part']==file])
            ids=np.arange(0,len(pts),19)
            entry['objects'].append(dict(name=names[file],indices=ids.tolist(),positions=pts[ids].tolist()))
        samples.append(entry)
    (OUT/'native_samples.json').write_text(json.dumps(dict(cmp_sha256=report['cmp_sha256'],samples=samples),separators=(',',':')))
    (OUT/'checks.json').write_text(json.dumps(report,indent=2),encoding='utf8')
    print('PASS',report['lods'],'channels',len(channels),'hardpoints',len(current),'damage',report['damage_caps'],'SUR coverage',sum(c['samples'] for c in coverage),flush=True)


if __name__=='__main__':check()
