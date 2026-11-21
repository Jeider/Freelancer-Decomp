"""Read back actual delivery bytes, validate and prepare Blender review."""
import json,struct
from collections import Counter
import numpy as np
import rh_fighter_final as d
import rh_fighter_final_mounts as mounts
import full_ship_audit as aa
from ship_collision_audit import sur_parts,surface
f=d.f

def simple_level(nodes,level):
    libs={f.mesh.crc(p.split('/')[-2]):f.audit.decode(n.blob) for p,n in f.mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    ref=next(n for p,n in f.mesh.walk(nodes) if p.lower().endswith('/level'+str(level)+'/vmeshpart/vmeshref'))
    return f.audit.extract(ref.blob,libs)

def closed_triangles(gs):
    p=np.concatenate([g['corners'][...,:3] for g in gs])
    _,ix=np.unique(p.reshape(-1,3),axis=0,return_inverse=True)
    edges=Counter(tuple(sorted((int(a),int(b)))) for face in ix.reshape(-1,3) for a,b in zip(face,np.roll(face,-1)))
    area=np.linalg.norm(np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]),axis=1)
    result=dict(boundary_edges=sum(n==1 for n in edges.values()),nonmanifold_edges=sum(n!=2 for n in edges.values()),minimum_double_area=float(area.min()))
    assert result['boundary_edges']==0 and area.min()>0,result
    return result

def main():
    path=d.ASSETS/'rh_pir_fighter.cmp';_,ns=d.tree(path);_,source=d.tree(d.OUT/'authoring_animated.cmp')
    mats=f.audit.material_table([d.MAT,d.ENV,d.ASSETS/'rh_pir_fighter_lods.mat']);names=f.component_map(ns);hp=d.hardpoints(ns,('Sc_extend wing',0))
    origin=np.array(d.read('build.json').get('origin_offset',[0,0,0]))
    libs={};maximum=dict(vertices=0,indices=0);resources=set();wire={};metal=[]
    for p,n in f.mesh.walk(ns):
        assert n.name.lower() not in ('material library','texture library')
        if not p.lower().endswith('/vmeshdata'):continue
        verts,groups,idx=f.audit.decode(n.blob);crc=f.mesh.crc(p.split('/')[-2]);assert crc not in resources;resources.add(crc);libs[crc]=verts
        assert len(verts)<65536 and len(idx)<65536 and np.isfinite(verts).all();at=0
        maximum['vertices']=max(maximum['vertices'],len(verts));maximum['indices']=max(maximum['indices'],len(idx))
        for mid,lo,hi,count,_ in groups:
            assert mid in mats,(mid,p)
            ii=idx[at:at+count]+lo;assert count%3==0 and len(ii)>0 and ii.min()>=lo and ii.max()<=hi<len(verts);at+=count
        assert at==len(idx)
    a=d.world(source,('Sc_extend wing',0));b=d.world(ns,('Sc_extend wing',0))
    for name,gs in a.items():
        expected=f.merge(gs);actual=f.merge(b[name]);assert len(expected)==len(actual)
        for g,h in zip(expected,actual):assert g['material']==h['material'] and np.allclose(g['corners'],h['corners'],atol=3e-5),name
    for file,gs in f.local_geometry(ns).items():
        for g in gs:
            if 'metal' not in mats[g['material']]['texture'].lower():continue
            p=g['corners'][...,:3]+origin;assert names[file]=='Root' or '_baydoor_' in names[file]
            assert abs(p[:,:,0]).max()<.76 and p[:,:,2].min()>-3.92 and p[:,:,2].max()<-1.64
            metal.append(names[file])
    flat={p.lower():n.blob for p,n in f.mesh.walk(ns)};joints=aa.constructs(flat);channels=aa.channels(flat,joints)
    assert all(c['native_size_valid'] and c['bound_joint'] and c['finite'] and not c.get('parent_mismatch') for c in channels)
    for file,name in names.items():
        blob=f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'VMeshWire'),'VWireData').blob
        size,crc,start,nv,ni,total=struct.unpack_from('<II4H',blob);ids=np.frombuffer(blob,'<u2',offset=16)
        assert size==16 and ni==len(ids) and ni%2==0 and nv==len(set(ids)) and total==nv
        if ni:assert max(ids)+start<len(libs[crc])
        wire[name]=ni//2
    assert all(wire[p]>0 for p in d.PARTS.values())
    zero,_=f.audit.transforms(ns);flight,_=f.audit.transforms(ns,('Sc_extend wing',0))
    for file,name in names.items():
        if wire[name]:assert all(np.allclose(x,y,atol=2e-6) for x,y in zip(zero[file.lower()],flight[file.lower()])),name
    damages=[];damage_report={};declared=d.read('build.json')['damage'];all_used=set()
    for zone in declared:
        _,dn=d.tree(d.ASSETS/zone['file']);gs=d.simple_geometry(dn);h=hp[zone['hardpoint'].lower()]
        assert f.digest(d.ASSETS/zone['file'])==zone['sha256']
        switches=np.frombuffer(f.mesh.child(f.mesh.child(dn[0],'MultiLevel'),'Switch2').blob,'<f4')
        assert np.array_equal(switches,[0,180,550,10000])
        for p,n in f.mesh.walk(dn):
            assert n.name.lower() not in ('material library','texture library')
            if p.lower().endswith('/vmeshdata'):
                crc=f.mesh.crc(p.split('/')[-2]);assert crc not in resources;resources.add(crc)
                v,draws,idx=f.audit.decode(n.blob);at=0
                assert len(v)<65536 and len(idx)<65536 and np.isfinite(v).all()
                for mid,lo,hi,count,_ in draws:
                    actual=idx[at:at+count]+lo;at+=count
                    assert mid in mats and actual.min()>=lo and actual.max()<=hi<len(v)
                assert at==len(idx)
        for g in gs:assert g['material'] in mats and 'metal' not in mats[g['material']]['texture'].lower()
        placed=f.base.world(gs,np.array(h['orientation']),np.array(h['position']));all_used|={g['material'] for g in gs}
        expected=d.packed(d.read('damage_world.json')[zone['zone']])
        if zone['zone'].endswith('_wing'):
            expected+=a[zone['zone']+'_lod1']+a[zone['zone']+'_slide']
        for g,v in zip(f.merge(expected),f.merge(placed)):
            assert g['material']==v['material'] and np.allclose(g['corners'],v['corners'],atol=3e-5)
        levels=[];checks=[]
        for lv in range(3):
            local=simple_level(dn,lv);assert sum(len(g['corners']) for g in local)==zone['lod_triangles'][lv]
            for g in local:assert g['material'] in mats and 'metal' not in mats[g['material']]['texture'].lower()
            checks.append(dict(level=lv,triangles=zone['lod_triangles'][lv],**closed_triangles(local)))
            levels.append(f.base.world(local,np.array(h['orientation']),np.array(h['position'])))
        damage_report[zone['zone']]=dict(file=zone['file'],sha256=zone['sha256'],levels=checks)
        damages.append(dict(name=zone['zone'],part=zone['part'],groups=placed,levels=levels))
    d.dump(d.OUT/'damage_export_check.json',dict(cmp_sha256=f.digest(path),zones=damage_report,shared_mat=True,debris_caps=False))
    for p in d.ASSETS.glob('*.sur'):
        for pid,chunks in sur_parts(p.read_bytes()):
            for tag,blob in chunks:
                if tag==b'surf':surface(blob)
    _,opened=d.tree(d.OUT/'rh_pir_fighter_review_open.cmp');oh=d.hardpoints(opened)
    for key,h in hp.items():
        assert np.allclose(h['position'],oh[key]['position'],atol=3e-5) and np.allclose(h['orientation'],oh[key]['orientation'],atol=3e-5)
    # Every user-edited HP survives the coordinate-system change, including
    # the latest forward thruster moves. No geometry follows the mount edits.
    _,user=d.tree(d.SOURCE/'user_hardpoints.cmp');userhp=d.hardpoints(user);usergeo=d.world(user)
    source_origin=np.array(d.read('user_hardpoint_source.json').get('coordinate_origin',[0,0,0]))
    shift=source_origin-origin
    assert set(hp)==set(userhp)
    for key,h in userhp.items():
        now=hp[key]
        assert h['owner']==now['owner'] and h['kind']==now['kind']
        assert np.allclose(h['position']+shift,now['position'],atol=2e-6) and np.allclose(h['orientation'],now['orientation'],atol=2e-6),key
        assert {k:v for k,v in h['leaves'].items() if k.lower() not in ('position','orientation')}=={k:v for k,v in now['leaves'].items() if k.lower() not in ('position','orientation')}
    # Export quantization and static-vs-animated identity transforms can differ
    # in the last float digits; verify the actual old geometry/UV in order.
    saved=json.loads((d.SOURCE/'ventral_shelves.json').read_text(encoding='utf8'))
    permitted=[t[:,:3] for ob in saved['objects'] for g in d.packed(ob['groups'])
               if g['material']==f.mesh.crc('pir_r_panel01_256') for t in g['corners']]
    uv_changed=0;triangles=0
    for name,gs in usergeo.items():
        for old in f.merge(gs):
            now=next(g for g in f.merge(b[name]) if g['material']==old['material'])
            expected=old['corners'].copy();expected[...,:3]+=shift
            assert expected.shape==now['corners'].shape
            assert np.allclose(expected[...,:6],now['corners'][...,:6],atol=3e-5),(name,old['material'])
            changes=np.max(abs(expected[...,6:]-now['corners'][...,6:]),axis=(1,2))>3e-5
            for t in old['corners'][changes]:
                assert name=='Root' and old['material']==f.mesh.crc('pir_r_panel01_256')
                assert any(np.allclose(t[:,:3]+source_origin,p,atol=3e-5) for p in permitted)
            uv_changed+=int(changes.sum());triangles+=len(expected)
    assert uv_changed in (0,12) and triangles==16997,(uv_changed,triangles)
    seats=[]
    for ob in d.read('blender_input.json')['original_objects']:
        if not ob['name'].endswith('_ventral_thruster_pylon'):continue
        p=np.concatenate([g['corners'][...,:3] for g in d.packed(ob['groups'])])+origin;edges=Counter()
        for t in p:
            for a,c in zip(t,np.roll(t,-1,axis=0)):edges[tuple(sorted((tuple(a.round(5)),tuple(c.round(5)))))] += 1
        volume=float(np.einsum('ij,ij->i',p[:,0],np.cross(p[:,1],p[:,2])).sum()/6)
        assert all(v==2 for v in edges.values()) and volume>0,(ob['name'],volume)
        assert abs(float(p[:,:,1].min())+2.48)<2e-5 and float(p[:,:,2].min())<=1.90001
        assert float(p[:,:,2].max())<=3.12001,'New sole overlaps the existing flat skin'
        seats.append(dict(object=ob['name'],closed=True,volume=volume))
    assert len(seats)==2
    previews=[];equipment_refs={}
    for key in mounts.EQUIPMENT:
        parts,ref=mounts.equipment_reference(key);h=hp[key];equipment_refs[key]=ref
        gs=[dict(g,material=100000001) for part in parts for g in part]
        previews.append(dict(name=h['name']+' equipment example',groups=f.base.world(gs,h['orientation'],h['position'])))
    # Surface-mounted weapons and folded gun envelope stay outside the receiving well.
    probes={}
    for key in ('hpweapon01','hpweapon02','hpweapon03','hpweapon04'):
        h=hp[key];surface_y=d.surface_at(b[h['owner']],h['position'],1);gap=float(h['position'][1]-surface_y);assert 0<=gap<.02
        probes[key]=dict(surface_gap=gap)
    source_data=json.loads((d.PREVIOUS/'geometry.json').read_text(encoding='utf8'))
    for file,sha in source_data['sources'].items():
        reference=d.SOURCE/'original.cmp' if d.Path(file)==d.Path(source_data['source']) else d.Path(file)
        assert f.digest(reference)==sha,str(reference)
    images={};all_used|={g['material'] for lv in range(3) for gs in f.local_geometry(ns,lv).values() for g in gs}
    for mid in all_used:
        m=mats[mid];e={k:v for k,v in m.items() if k!='image'}
        if m['image'] is not None:
            target=d.OUT/'textures'/(m['texture'].rsplit('.',1)[0]+'.png');m['image'].save(target);e['image_path']=str(target)
        images[mid]=e
    parents={j['name']:j['parent'] for j in joints};objects=[dict(name=names[file],groups=gs,parent=parents.get(names[file])) for file,gs in f.local_geometry(ns).items()]
    frames={}
    for frame in range(1,206):
        if frame<=49:t=2*(49-frame)/48
        elif frame<=97:t=2*(frame-49)/48
        elif frame<=145:t=2*(145-frame)/48
        else:t=0
        pose=d.runtime(ns,t)
        if frame>145:
            u=(frame-145)/30 if frame<=175 else (205-frame)/30
            bay=d.runtime(ns,u*2.1333333,'Sc_open baydoor')
            for name in pose:
                if '_baydoor_' in name:pose[name]=bay[name]
        frames[str(frame)]=pose
    images[100000001]=dict(name='equipment placement preview',texture='',colour=[.32,.42,.54])
    d.dump(d.OUT/'review.json',dict(origin_offset=origin,cmp_sha256=f.digest(path),objects=objects,materials=images,frames=frames,
        levels=[d.world(ns,('Sc_extend wing',0),lv) for lv in (1,2)],damage=damages,hardpoints=hp,equipment_examples=previews))
    d.dump(d.OUT/'validation.json',dict(origin_offset=origin,cmp_sha256=f.digest(path),maximum=maximum,hardpoints=len(hp),near_shape_preserved=True,
        wire=wire,wire_static_flight=True,animation_channels=len(channels),cargo_metal_only=True,surface_mounts=probes,
        damage_zones=4,damage_parent_roundtrip=True,source_and_shared_mat_unchanged=True,user_hardpoints_preserved=len(hp),
        existing_skin_uv_preserved=True,updated_shelf_uv_triangles=uv_changed,additive_pylon_triangles=0,pylon_topology=seats,equipment_references=equipment_refs,installed=False,game_launched=False))
    print('READBACK PASS',maximum,'HP',len(hp),'wire edges',sum(wire.values()),flush=True)

if __name__=='__main__':main()
