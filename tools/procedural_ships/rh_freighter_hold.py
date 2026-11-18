"""Narrow-hold revision from the user's installed Q13; offline output only."""
import copy,json,secrets,struct,sys,shutil
import numpy as np
import rh_freighter_final as d
from rh_pir_elite_build import salt_tree
from rh_freighter_far_lod import wire_lines,named,signature
f=d.f
OUT=d.OUT/'hold_damage'
SOURCE=d.OUT/'lod_refinement/rh_pir_freighter.cmp'
EXPECTED='7db66f300effa6dec8e996f7f031397d3ceed646e95f95129b61b8adab8ede22'
ATLAS='rh_pir_freighter_projection_lod'

def prepare():
    assert f.digest(SOURCE)==EXPECTED
    assert shutil.disk_usage(d.ROOT).free>4*1024**3
    OUT.mkdir(exist_ok=True);(OUT/'panel_damage').mkdir(exist_ok=True)
    _,ns=d.tree(SOURCE)
    levels=[d.world(ns,('Sc_extend wing',0),lv) for lv in range(3)]
    scene=d.read('review/scene.json')
    original=d.read('blender_input.json')
    # Recover ownership through the exact accepted UV recipe, not proximity to
    # coarse source planes (native UV clipping contains small geometric offsets).
    import rh_freighter_uv15 as u
    u.base.configure();cfg=json.loads((d.PREVIOUS/'cornice_symmetry.json').read_text());u.MIRROR_Z=cfg['plane_z']
    ref=json.loads((u.REFERENCE/'native_fore.json').read_text())[1];shape=cfg['front']
    ts=np.array([t['corners'] for t in ref['triangles'] if t['material']=='pir_r_panel01_256' and t['source_triangle'] in (93,94)])
    z0=ts[:,:,2].min();ts[:,:,0]-=shape['source_center_x'];ts[:,:,1]=u.TOP;ts[:,:,2]+=shape['top_z'][0]-z0;ts[:,:,3:6]=[0,1,0]
    u.TOP_GROUP=dict(material=u.uv.P,corners=ts)
    ribs=json.loads((d.PREVIOUS/'aft_rib_geometry.json').read_text())['ribs']
    u.aft.RIBS.update({int(s):{k:np.array(v) if k in ('oi','oo','bi','bo','arc') else v for k,v in r.items()} for s,r in ribs.items()})
    raw=json.loads((d.PREVIOUS/'mechanical_geometry.json').read_text())['objects'];mapped=[]
    for o in raw:
        if o['name'].startswith('Continuous hull'):mapped+=u.core_map(o['name'],o['groups'])
        elif o['name'].startswith('Raised cargo'):mapped+=u.hull.addition_map(o['name'],o['groups'])
    d.dump(OUT/'owned_core.json',mapped)
    d.dump(OUT/'input.json',dict(source=str(SOURCE),sha256=EXPECTED,levels=levels,
        materials=original['materials'],hardpoints=d.hardpoints(ns,('Sc_extend wing',0)),scene=scene,
        game_cmp_sha256=f.digest(d.GAME/'DATA/ships/rheinland/rh_pir_freighter/rh_pir_freighter.cmp'),
        shared_mat_sha256=f.digest(d.MAT)))
    print('Prepared latest installed source; no live writes',flush=True)

def export():
    data=json.loads((OUT/'geometry.json').read_text());header,ns=d.tree(SOURCE);before=copy.deepcopy(ns)
    assert f.digest(SOURCE)==EXPECTED
    names=f.component_map(ns);tr,_=f.audit.transforms(ns,('Sc_extend wing',0));lib=f.mesh.child(ns[0],'VMeshLibrary')
    rootfile=next(k for k,v in names.items() if v=='Root');r,t=tr[rootfile.lower()]
    for lv,groups in enumerate(data['roots']):
        gs=f.base.world(d.packed(groups),r.T,-r.T@t);blob,v=f.mesh.pack(f.merge(gs));vn='rpf_narrow_hold_lod'+str(lv)+'.vms'
        lib.children.append(f.folder(vn,f.mesh.Node('VMeshData',blob)))
        ref=f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(ns[0],rootfile),'MultiLevel'),'Level'+str(lv)),'VMeshPart')
        f.mesh.child(ref,'VMeshRef').blob=f.fresh_ref(vn,blob,v)
    # Only approved light positions change: retain raw bytes for every other HP.
    hps=d.hardpoints(ns,('Sc_extend wing',0))
    fixed=f.mesh.child(f.mesh.child(f.mesh.child(ns[0],rootfile),'Hardpoints'),'Fixed')
    for key,h in data['lights'].items():
        assert 'light' in key and hps[key]['owner']=='Root'
        hp=next(n for n in fixed.children if n.name.lower()==key)
        f.mesh.child(hp,'Position').blob=np.array(r.T@(np.array(h['after'])-t),'<f4').tobytes()
    used={struct.unpack_from('<I',n.blob,4)[0] for p,n in f.mesh.walk(ns) if p.lower().endswith(('/vmeshref','/vwiredata'))}
    lib.children=[n for n in lib.children if f.mesh.crc(n.name) in used]
    salt=secrets.token_hex(6);mapping=salt_tree(ns,salt)
    target=OUT/'rh_pir_freighter.cmp';target.write_bytes(f.mesh.write_tree(header,ns));_,ns=d.tree(target)
    for part,lines in wire_lines(before).items():assert np.allclose(lines,wire_lines(ns)[part],atol=2e-5)
    nh=d.hardpoints(ns,('Sc_extend wing',0));assert hps.keys()==nh.keys()
    for k,h in hps.items():
        assert h['owner']==nh[k]['owner']
        for tag,raw in h['leaves'].items():
            if tag.lower()=='position' and k in data['lights']:continue
            assert raw==nh[k]['leaves'][tag],(k,tag)
    for lv in range(3):
        for name,old in signature(before,lv).items():
            if name!='Root':assert old==signature(ns,lv)[name],(lv,name)
    for tag in ('Animation','Cons'):
        sub=lambda a:f.mesh.child(a[0],tag) if tag=='Animation' else f.mesh.child(f.mesh.child(a[0],'Cmpnd'),tag)
        leaves=lambda a:{p:n.blob for p,n in f.mesh.walk([sub(a)])}
        assert leaves(before)==leaves(ns)
    mats=f.audit.material_table([d.MAT,d.ENV,d.ASSETS/'rh_pir_freighter_lods.mat']);maximum=0
    for p,n in f.mesh.walk(ns):
        assert n.name.lower() not in ('texture library','material library')
        if p.lower().endswith('/vmeshdata'):
            vs,gs,ids=f.audit.decode(n.blob);assert np.isfinite(vs).all() and len(vs)<65536 and len(ids)<65536
            maximum=max(maximum,len(vs));at=0
            for mid,lo,hi,num,_ in gs:
                assert mid in mats and num%3==0;ii=ids[at:at+num]+lo
                assert ii.min()>=lo and ii.max()<=hi<len(vs);at+=num
    opened=copy.deepcopy(ns)
    for p,n in f.mesh.walk(opened):
        if p.lower().endswith('/cons/pris'):
            raw=bytearray(n.blob)
            for at in range(0,len(raw),208):
                vs=np.frombuffer(raw,'<f4',20,at+128).copy();vs[:3]+=vs[15:18];raw[at+128:at+208]=vs.tobytes()
            n.blob=bytes(raw)
    opened[0].children=[n for n in opened[0].children if n.name.lower()!='animation']
    osalt=secrets.token_hex(6);omap=salt_tree(opened,osalt)
    (OUT/'rh_pir_freighter_review_open.cmp').write_bytes(f.mesh.write_tree(header,opened))
    import rh_freighter_final_build as builder
    saved=d.ASSETS;d.ASSETS=OUT;damages={}
    damage_world=json.loads((OUT/'damage_world.json').read_text());anchors={a['zone']:a for a in d.read('build.json')['damage']}
    try:
        for zone in ('port_side_panel','starboard_side_panel'):
            gs=d.packed(damage_world[zone]);anchor=np.array(anchors[zone]['position'])
            for g in gs:g['corners'][...,:3]-=anchor
            damages[zone]=builder.simple(zone,gs,secrets.token_hex(6))
    finally:d.ASSETS=saved
    counts=[sum(len(g['corners']) for gs in named(ns,lv).values() for g in gs) for lv in range(3)]
    assert counts[2]<=500
    actual_roots=[d.world(ns,('Sc_extend wing',0),lv)['Root'] for lv in range(3)]
    for authored,actual in zip(data['roots'],actual_roots):
        aa=f.merge(d.packed(authored));bb=f.merge(actual)
        assert len(aa)==len(bb)
        for a,b in zip(aa,bb):
            assert a['material']==b['material'] and np.allclose(a['corners'],b['corners'],atol=3e-5)
    d.dump(OUT/'exported_roots.json',dict(cmp_sha256=f.digest(target),roots=actual_roots))
    d.dump(OUT/'validation.json',dict(source_sha256=EXPECTED,cmp_sha256=f.digest(target),counts=counts,
        max_vertices=maximum,private_salt=salt,resources=mapping,open_salt=osalt,open_resources=omap,
        lights=data['lights'],other_hp_bytes_exact=True,animation_cons_bytes_exact=True,wire_398_edges_preserved=True,
        non_root_geometry_exact=True,damage=damages,main_sur='Unchanged: same exterior and equipment/shield HPs',
        materials='Existing external MAT, no additional LOD MAT',installed=False))
    print('EXPORTED',counts,flush=True)

def delivery():
    validation=json.loads((OUT/'validation.json').read_text());motion=json.loads((OUT/'motion_check.json').read_text())
    assert validation['cmp_sha256']==motion['cmp_sha256']==f.digest(OUT/'rh_pir_freighter.cmp')
    assert not motion['collisions'] and all(c['outward_clear'] for c in motion['light_clearance'])
    mats=f.audit.material_table([d.MAT,d.ENV]);damage=json.loads((OUT/'damage_world.json').read_text())
    anchors={a['zone']:a for a in d.read('build.json')['damage']};files=['rh_pir_freighter.cmp']
    for zone in ('port_side_panel','starboard_side_panel'):
        path=OUT/('rh_pir_freighter_dmg_'+zone+'.3db');_,ns=d.tree(path)
        for p,n in f.mesh.walk(ns):assert n.name.lower() not in ('texture library','material library')
        actual=d.simple_geometry(ns);expected=d.packed(damage[zone]);anchor=np.array(anchors[zone]['position'])
        for a in expected:a['corners'][...,:3]-=anchor
        for a,b in zip(f.merge(expected),f.merge(actual)):
            assert a['material']==b['material'] and a['material'] in mats
            assert np.isfinite(b['corners']).all() and np.allclose(a['corners'],b['corners'],atol=3e-5)
        files.extend([path.name,path.with_suffix('.sur').name])
    original=json.loads((OUT/'input.json').read_text())
    game=d.GAME/'DATA/ships/rheinland/rh_pir_freighter/rh_pir_freighter.cmp'
    assert f.digest(game)==original['game_cmp_sha256'] and f.digest(d.MAT)==original['shared_mat_sha256']
    d.dump(OUT/'delivery_manifest.json',dict(files={n:dict(sha256=f.digest(OUT/n),bytes=(OUT/n).stat().st_size) for n in files},
        blend_sha256=f.digest(OUT/'rh_pir_freighter_review.blend'),installed=False,game_and_shared_mat_unchanged=True))
    print('DELIVERY PASS: five offline replacement assets, live CMP/MAT unchanged',flush=True)

if __name__=='__main__':
    delivery() if '--delivery' in sys.argv else export() if '--export' in sys.argv else prepare()
