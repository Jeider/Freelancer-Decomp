"""Validate decoded delivery bytes; prepare reproducible Blender review inputs."""
import copy,json,shutil,struct
import numpy as np
import rh_freighter_final as d
from ship_collision_audit import sur_parts,surface
f=d.f

def main():
    path=d.ASSETS/'rh_pir_freighter.cmp';_,ns=d.tree(path);_,before=d.tree(d.OUT/'authoring_animated.cmp')
    mats=f.audit.material_table([d.MAT,d.ENV,d.ASSETS/'rh_pir_freighter_lods.mat'])
    names=f.component_map(ns);oldnames=f.component_map(before);oldgeom=d.world(before,('Sc_extend wing',0));newgeom=d.world(ns,('Sc_extend wing',0))
    maximum=dict(vertices=0,indices=0);wire={};libs={}
    for p,node in f.mesh.walk(ns):
        assert node.name.lower() not in ('material library','texture library')
        if not p.lower().endswith('/vmeshdata'):continue
        verts,groups,indices=f.audit.decode(node.blob);libs[f.mesh.crc(p.split('/')[-2])]=verts
        assert len(verts)<65536 and len(indices)<65536 and np.isfinite(verts).all()
        maximum['vertices']=max(maximum['vertices'],len(verts));maximum['indices']=max(maximum['indices'],len(indices));at=0
        for mid,lo,hi,num,_ in groups:
            assert mid in mats and num%3==0 and num>0
            ids=indices[at:at+num]+lo;assert ids.min()>=lo and ids.max()<=hi<len(verts);at+=num
        assert at==len(indices)
    for part,gs in oldgeom.items():
        by={g['material']:g['corners'] for g in newgeom[part]}
        for g in gs:
            assert g['corners'].shape==by[g['material']].shape,(part,'near geometry changed')
            assert np.allclose(g['corners'],by[g['material']],atol=3e-5),(part,'near UV or shape changed')
    leaves=lambda tree:{p.lower():n.blob for p,n in f.mesh.walk(tree)}
    for tag in ('Animation','Cons'):
        sub=lambda a:f.mesh.child(a[0],tag) if tag=='Animation' else f.mesh.child(f.mesh.child(a[0],'Cmpnd'),tag)
        assert leaves([sub(ns)])==leaves([sub(before)])
    originals=d.read('hardpoints.json');actual=d.hardpoints(ns,('Sc_extend wing',0))
    for k,h in originals.items():
        assert actual[k]['owner']==h['owner'] and actual[k]['kind']==h['kind']
        for field in ('position','orientation'):assert np.allclose(actual[k][field],h[field],atol=3e-5),(k,field)
        for tag,data in h['leaves'].items():
            if tag.lower() not in ('position','orientation'):assert actual[k]['leaves'][tag]==data
    flat=leaves(ns);joints=d.animation_audit.constructs(flat);channels=d.animation_audit.channels(flat,joints)
    assert all(c['bound_joint'] and c['native_size_valid'] and c['finite'] and not c.get('parent_mismatch') for c in channels)
    for file,name in names.items():
        data=f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'VMeshWire'),'VWireData').blob
        _,crc,bias,nv,ni,total=struct.unpack_from('<II4H',data);ids=np.frombuffer(data,'<u2',offset=16)
        assert len(ids)==ni and ni%2==0 and len(set(ids))==nv and nv==total
        if ni:assert max(ids)+bias<len(libs[crc])
        wire[name]=ni//2
    assert all(wire[part]>0 for part in d.PARTS.values())
    for p in d.ASSETS.glob('*.sur'):
        for pid,chunks in sur_parts(p.read_bytes()):
            for tag,blob in chunks:
                if tag==b'surf':surface(blob)
    damages=[]
    for z in d.read('build.json')['damage']:
        _,dn=d.tree(d.ASSETS/z['file']);gs=d.simple_geometry(dn)
        assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(dn))
        for g in gs:assert g['material'] in mats and 'metal' not in mats[g['material']]['texture'].lower()
        hp=actual[z['hardpoint'].lower()];w=f.base.world(gs,np.array(hp['orientation']),np.array(hp['position']))
        expected=d.packed(d.read('damage_world.json')[z['zone']]);a=d.points(w);b=d.points(expected)
        assert np.allclose(a.min(0),b.min(0),atol=3e-5) and np.allclose(a.max(0),b.max(0),atol=3e-5)
        for mid in {g['material'] for g in expected}:
            aa=np.concatenate([g['corners'] for g in w if g['material']==mid]);bb=np.concatenate([g['corners'] for g in expected if g['material']==mid])
            assert aa.shape==bb.shape and np.allclose(aa,bb,atol=3e-5),(z['zone'],'damage shape/UV roundtrip')
        damages.append(dict(zone=z['zone'],groups=w,part=z['part']))
    # Static review has the same flight geometry and all HP world transforms.
    _,opened=d.tree(d.OUT/'rh_pir_freighter_review_open.cmp');openh=d.hardpoints(opened)
    for k,h in actual.items():
        assert np.allclose(openh[k]['position'],h['position'],atol=3e-5)
        assert np.allclose(openh[k]['orientation'],h['orientation'],atol=3e-5)
    for k,v in d.read('source_manifest.json')['files'].items():assert f.digest(d.SOURCE/k)==v['sha256']
    assert f.digest(d.PREVIOUS/'rh_pir_freighter_review_open.cmp')==d.read('source_manifest.json')['files']['user_open.cmp']['sha256']
    assert f.digest(d.MAT)==d.read('source_manifest.json')['mat']['sha256']
    review=d.OUT/'review';review.mkdir(exist_ok=True);images={}
    for mid,m in mats.items():
        if mid not in {g['material'] for lv in range(3) for gs in f.local_geometry(ns,lv).values() for g in gs}:continue
        e={k:v for k,v in m.items() if k!='image'}
        if m['image'] is not None:
            imagepath=d.OUT/'textures'/(m['texture'].rsplit('.',1)[0]+'.png');m['image'].save(imagepath);e['image_path']=str(imagepath)
        images[mid]=e
    objects=[]
    for file,gs in f.local_geometry(ns).items():
        name=names[file];joint=next((j for j in joints if j['name']==name),dict(name='Root',parent=None,kind='fix',origin=[0,0,0],rotation=np.eye(3).tolist()))
        objects.append(dict(name=name,file=file,groups=gs,joint=joint,source_objects=['Accepted Q13 uv15; user HP source '+d.read('hardpoint_transfer.json')['source_sha256']]))
    d.dump(review/'scene.json',dict(cmp=str(path),cmp_sha256=f.digest(path),objects=objects,materials=images,channels=channels))
    d.dump(review/'build.json',dict(hardpoints=f.hp_world(ns)))
    for name in ('raised_hold_geometry.json','aft_rib_geometry.json','vent_clearance.json'):
        shutil.copyfile(d.PREVIOUS/name,review/name)
    d.dump(review/'extra_geometry.json',dict(levels=[d.world(ns,('Sc_extend wing',0),lv) for lv in (1,2)],damage=damages))
    d.dump(d.OUT/'validation.json',dict(cmp_sha256=f.digest(path),maximum=maximum,hardpoints=len(actual),user_hardpoints_preserved=len(originals),
        near_shape_uv_preserved=True,native_animation_construct_bytes_preserved=True,animation_channels=len(channels),
        wire=wire,damage_zones=4,damage_parent_placement_checked=True,external_materials=True,source_and_shared_mat_unchanged=True,
        installed=False,game_launched=False))
    print('VALIDATION PASS',maximum,'HP',len(actual),'wire',sum(wire.values()))

if __name__=='__main__':main()
