"""Assemble the accepted tail/damage revision as an OFFLINE three-LOD release.

Never installs assets, modifies Pythonlancer sources or writes to live DATA.
"""
import collections
import copy
import hashlib
import json
from pathlib import Path
import secrets
import shutil
import struct
import sys

import numpy as np
import rh_elite_tail_cut as cut
from rh_pir_elite_refine_damage import decoded_wire

d = cut.d
r, f, b = d.r, d.f, d.b
SOURCE = cut.OUT
OUT = SOURCE.parent / 'release'
ASSETS = OUT / 'assets'
OLD = r.OUT / 'user_source.cmp'
PY = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
ATLAS = f.mesh.crc('rh_b_projection_lod')


def save(name, data):
    r.save(OUT / name, data)


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf8'))


def named(ns, level=0, pose=('Sc_extend wing', 0)):
    names = f.component_map(ns)
    tr, _ = f.audit.transforms(ns, pose)
    return {names[file]: f.base.world(gs, *tr[file.lower()])
            for file, gs in f.local_geometry(ns, level).items()}


def subset(gs, components):
    ids = collections.defaultdict(set)
    for c in components:
        for gi, ti in c['indices']:
            ids[gi].add(ti)
    return [dict(g, corners=np.array(g['corners'])[sorted(ids[gi])])
            for gi, g in enumerate(gs) if ids[gi]]


def drum(c):
    lo, hi = np.array(c['bounds'])
    return lo[2] > 2.4 and hi[2] < 6.7 and lo[1] > -.9 and hi[1] < 3.2 and max(abs(lo[0]), abs(hi[0])) < 1.05


def prepare():
    assert shutil.disk_usage(OUT.parent).free > 2 * 1024**3
    OUT.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    assert f.digest(SOURCE/'assets/rh_pir_elite.cmp') == json.loads((SOURCE/'tail_transfer_check.json').read_text())['cmp_sha256']
    ns = r.load(SOURCE/'assets/rh_pir_elite.cmp')[1]
    old = r.load(OLD)[1]
    parts = named(ns)
    comps = r.components(parts['Root'])
    aft = subset(parts['Root'], [c for c in comps if np.array(c['bounds'])[0, 2] > 2.4 and not drum(c)])
    kept = []
    for level in (1, 2):
        world = named(old, level)
        cs = r.components(world['Root'])
        world['Root'] = subset(world['Root'], [c for c in cs if np.array(c['bounds'])[0, 2] < 2 or drum(c)])
        # Each replacement is simplified from the accepted current geometry.
        # Unchanged body/drum/wing photos still use the user's shared atlas.
        for name in parts:
            if name == 'Rh_tail_lod1' or '_engine_' in name or 'upperarm' in name:
                world[name] = []
        kept.append(world)
    replacements = {'Root': aft}
    replacements.update({k:v for k,v in parts.items() if k=='Rh_tail_lod1' or '_engine_' in k or 'upperarm' in k})
    damage = {zone: d.cap_groups(SOURCE/'assets'/('rh_pir_elite_dmg_'+zone+'.3db')) for zone in d.ZONES}
    mats = f.audit.material_table([r.MAT, r.ENV])
    assert ATLAS in mats and mats[ATLAS]['image'] is not None
    # Verify the actual shared DDS payload against the atlas that produced the
    # retained UV charts, not just a matching material name.
    texname = 'rh_b_projection_lod.tga'
    reference = b.v.OUT/'lod_refinement/rh_concept_b_lods.mat'
    def texture_payload(path):
        tree = r.load(path)[1]
        tex = f.mesh.child(tree[0], 'Texture library').children
        node = next(t for t in tex if t.name.lower()==texname.lower())
        return [(p.rsplit('/',1)[-1], n.blob) for p,n in f.mesh.walk([node]) if n.blob]
    assert texture_payload(reference) == texture_payload(r.MAT), 'Shared projection atlas differs from its authored UVs'
    # Original export used the same texture name, but private material salts may
    # differ between retained snapshots. Only this shared identity is allowed.
    for lv in kept:
        for gs in lv.values():
            for g in gs:
                assert g['material'] in mats, hex(g['material'])
    sources = [SOURCE/'assets/rh_pir_elite.cmp', OLD, r.MAT, r.ENV, r.LIVE,
               PY/'templates/hardcoded_inis/shiparch/playerships/rh_pir_elite.ini',
               PY/'tools/data_folder.py', PY/'managers/shiparch.py', PY/'world/ship.py',
               f.audit.DATA/'SHIPS/shiparch.ini', reference]
    sources += sorted((SOURCE/'assets').glob('*'))
    save('sources.json', dict(files={str(p):f.digest(p) for p in sources if p.is_file()},
                             shared_atlas_payload_matches=True, installed=False))
    save('lod_input.json', dict(near=parts, preserved=kept, replacements=replacements, damage=damage))
    print('PREPARED hybrid LODs; shared atlas verified, native textures for changed aft geometry', flush=True)


def set_level(ns, file, level, groups, label):
    part = f.mesh.child(ns[0], file) if file else ns[0]
    ml = f.mesh.child(part, 'MultiLevel')
    blob, verts = f.mesh.pack(f.merge(r.flatten_groups(groups)))
    vn = label+'.vms'
    f.mesh.child(ns[0], 'VMeshLibrary').children.append(f.folder(vn, f.mesh.Node('VMeshData', blob)))
    ml.children = [c for c in ml.children if c.name != 'Level'+str(level)]
    ml.children.append(f.folder('Level'+str(level), f.folder('VMeshPart', f.mesh.Node('VMeshRef', f.fresh_ref(vn,blob,verts)))))
    f.mesh.child(ml, 'Switch2').blob = np.array([0,180,550,10000],'<f4').tobytes()


def export():
    data = load('lod_geometry.json')
    header, ns = r.load(SOURCE/'assets/rh_pir_elite.cmp')
    names = f.component_map(ns)
    transforms, _ = f.audit.transforms(ns, ('Sc_extend wing',0))
    for level, parts in enumerate(data['levels'],1):
        for file, name in names.items():
            rot,t = transforms[file.lower()]
            local = f.base.world(r.flatten_groups(parts[name]),rot.T,-rot.T@t)
            set_level(ns,file,level,local,'release_lod'+str(level)+'_'+name)
    salt = secrets.token_hex(6)
    mapping = b.salt_tree(ns,salt)
    main = ASSETS/'rh_pir_elite.cmp'
    main.write_bytes(f.mesh.write_tree(header,ns))
    # Static collision is already rebuilt for precisely this accepted LOD0.
    shutil.copyfile(SOURCE/'assets/rh_pir_elite.sur',ASSETS/'rh_pir_elite.sur')
    caps = {}
    for zone, levels in data['damage'].items():
        filename='rh_pir_elite_dmg_'+zone+'.3db'
        h,n = r.load(SOURCE/'assets'/filename)
        for lv,groups in enumerate(levels,1):
            set_level(n,None,lv,groups,'release_damage_'+zone+'_'+str(lv))
        cs = secrets.token_hex(6)
        cm = b.salt_tree(n,cs)
        (ASSETS/filename).write_bytes(f.mesh.write_tree(h,n))
        sur=filename.removesuffix('.3db')+'.sur'
        shutil.copyfile(SOURCE/'assets'/sur,ASSETS/sur)
        caps[zone] = dict(salt=cs,resources=cm)
    files = {p.name:dict(bytes=p.stat().st_size,sha256=f.digest(p)) for p in sorted(ASSETS.iterdir()) if p.suffix in ('.cmp','.sur','.3db')}
    assert len(files)==12
    manifest=dict(files=files,salt=salt,resources=mapping,damage=caps,
                  source_cmp=str(SOURCE/'assets/rh_pir_elite.cmp'), source_sha256=f.digest(SOURCE/'assets/rh_pir_elite.cmp'),
                  shared_material='rh_b_projection_lod',shared_atlas_unchanged=True,installed=False)
    save('export.json',manifest)
    r.save(ASSETS/'manifest.json',manifest)
    print('EXPORTED 12 offline assets, 3 LODs, 5 damage zones, fresh salts',flush=True)


def standalone_groups(ns,level):
    # Reuse the normal CMP decoder without writing a temporary file.
    tmp=copy.deepcopy(ns)
    original=tmp[0]
    lib=f.mesh.child(original,'VMeshLibrary')
    body=f.folder('review.3db',copy.deepcopy(f.mesh.child(original,'MultiLevel')))
    tmp[0]=f.folder(original.name,lib,body,
                   f.folder('Cmpnd',f.folder('Root',f.textnode('Object name','Root'),
                      f.textnode('File name','review.3db'),f.mesh.Node('Index',struct.pack('<I',0)))))
    return f.local_geometry(tmp,level)['review.3db']


def check():
    source=r.load(SOURCE/'assets/rh_pir_elite.cmp')[1]
    ns=r.load(ASSETS/'rh_pir_elite.cmp')[1]
    manifest=load('export.json')
    assert all(f.digest(ASSETS/name)==record['sha256'] for name,record in manifest['files'].items())
    assert r.hp_bytes(source)==r.hp_bytes(ns)
    for name in ('Animation','Cons'):
        def branch(n):
            return f.mesh.child(n[0],name) if name=='Animation' else f.mesh.child(f.mesh.child(n[0],'Cmpnd'),name)
        assert [(p,n.blob) for p,n in f.mesh.walk([branch(source)])]==[(p,n.blob) for p,n in f.mesh.walk([branch(ns)])]
    for pose in (None,('Sc_extend wing',0),('Sc_extend wing',.5),('Sc_extend wing',1),('Sc_open baydoor',1)):
        a,c=named(source,0,pose),named(ns,0,pose)
        for part in a:
            for x,y in zip(a[part],c[part]):
                assert x['material']==y['material'] and np.array_equal(x['corners'],y['corners']),part
    mats=f.audit.material_table([r.MAT,r.ENV])
    resources=set();files={}
    for path in [ASSETS/'rh_pir_elite.cmp']+sorted(ASSETS.glob('*.3db')):
        tree=r.load(path)[1];libs={};draws=[]
        assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(tree))
        for p,node in f.mesh.walk(tree):
            if not p.lower().endswith('/vmeshdata'):continue
            crc=f.mesh.crc(p.split('/')[-2]);assert crc not in resources
            resources.add(crc)
            verts,groups,ids=f.audit.decode(node.blob);libs[crc]=(verts,groups,ids)
            assert len(verts)<65536 and len(ids)<65536 and np.isfinite(verts).all()
            at=0
            for mid,lo,hi,count,_ in groups:
                assert mid in mats and (not mats[mid]['texture'] or mats[mid]['image'] is not None), (path.name,hex(mid))
                assert count%3==0 and 0<=lo<=hi<len(verts)
                assert not count or ids[at:at+count].max()+lo<=hi
                at+=count
            assert at==len(ids)
            draws.append(dict(vertices=len(verts),indices=len(ids),materials=len(groups)))
        for p,node in f.mesh.walk(tree):
            if p.lower().endswith('/vmeshref'):
                size,crc,v0,nv,i0,ni,g0,ng=struct.unpack_from('<II6H',node.blob)
                assert size==60 and crc in libs
                verts,groups,ids=libs[crc]
                assert v0+nv<=len(verts) and i0+ni<=len(ids) and g0+ng<=len(groups)
            elif p.lower().endswith('/vwiredata'):
                size,crc,bias,nv,ni,total=struct.unpack_from('<II4H',node.blob)
                ids=np.frombuffer(node.blob,'<u2',offset=16)
                assert size==16 and crc in libs and ni==len(ids) and ni%2==0 and total==nv==len(set(ids))
                assert ni==0 or bias+ids.max()<len(libs[crc][0])
        if path.suffix=='.3db':
            old=d.cap_groups(SOURCE/'assets'/path.name)
            levels=[standalone_groups(tree,i) for i in range(3)]
            for a,c in zip(old,levels[0]):assert a['material']==c['material'] and np.array_equal(a['corners'],c['corners'])
            for gs in levels:
                for g in gs:
                    assert 'metal' not in mats[g['material']]['name'].lower()
                    assert 'metal' not in (mats[g['material']]['texture'] or '').lower()
            counts=[sum(len(g['corners']) for g in gs) for gs in levels]
            assert counts[0]>counts[1]>counts[2]
        else:
            levels=[f.local_geometry(tree,i) for i in range(3)]
            counts=[sum(len(g['corners']) for gs in lv.values() for g in gs) for lv in levels]
        files[path.name]=dict(sha256=f.digest(path),lod_triangles=counts,draws=draws)
    # Native near geometry and collision payloads are bit-exact to damage_05.
    surs={p.name:f.digest(p) for p in ASSETS.glob('*.sur')}
    assert all(f.digest(SOURCE/'assets'/name)==sha for name,sha in surs.items())
    ws=decoded_wire(source,f.audit.transforms(source,('Sc_extend wing',0))[0])
    wn=decoded_wire(ns,f.audit.transforms(ns,('Sc_extend wing',0))[0])
    assert set(ws)==set(wn)
    for part in ws:assert np.array_equal(ws[part],wn[part]),part
    for z,(owner,visual,_,_) in d.ZONES.items():
        assert len(wn[owner])>0
        if owner!=visual:assert not len(wn[visual])
    # The wing wires are static even while their visual child folds forward.
    folded=decoded_wire(ns,f.audit.transforms(ns,None)[0])
    for side in ('port','starboard'):
        name='Rh_'+side+'_wing_lod1';assert np.array_equal(wn[name],folded[name])
    source_guard=load('sources.json')['files']
    assert all(f.digest(Path(p))==sha for p,sha in source_guard.items()),'Input or live source changed'
    report=dict(cmp_sha256=f.digest(ASSETS/'rh_pir_elite.cmp'),files=files,sur_files=surs,
                hardpoints=79,hardpoints_bytes_unchanged=True,near_geometry_unchanged=True,
                animation_and_cons_bytes_unchanged=True,static_extended_collision_unchanged=True,
                wire_same_as_accepted=True,wing_wire_static_extended=True,
                shared_atlas_payload_verified=True,external_materials=True,
                tail_ownership='middle rear upright and sleeve on Tail; upper/lower frame and drum on Root',
                source_and_live_files_unchanged=True,installed=False,game_launched=False)
    save('validation.json',report)
    print('CHECKED exact near geometry, 79 HPs, rig, wire, collision, materials and all 3 LOD index ranges',flush=True)


def previews():
    from PIL import Image,ImageDraw
    from preview import render
    ns=r.load(ASSETS/'rh_pir_elite.cmp')[1]
    mats=f.audit.material_table([r.MAT,r.ENV])
    def shot(gs,cam,center,radius,size):
        front=[]
        for g in gs:
            a=np.array(g['corners']);n=np.cross(a[:,1,:3]-a[:,0,:3],a[:,2,:3]-a[:,0,:3]);keep=n@np.array(cam)>1e-9
            if keep.any():front.append(dict(g,corners=a[keep]))
        return render(front,mats,np.array(center),radius,cam,size,'texture')
    sheet=Image.new('RGB',(1800,1800));draw=ImageDraw.Draw(sheet)
    export=dict(cmp_sha256=f.digest(ASSETS/'rh_pir_elite.cmp'),levels=[],damage={},hardpoints=d.world_hp(ns))
    for lv in range(3):
        parts=named(ns,lv);export['levels'].append(parts)
        gs=[g for x in parts.values() for g in x]
        for row,cam in enumerate([(-1,.6,1),(-1,0,0),(0,1,.001)]):
            im=shot(gs,cam,(0,0,0),10.7,600)
            sheet.paste(im,(lv*600,row*600));draw.text((lv*600+15,row*600+15),'LOD '+str(lv),fill='white')
    sheet.save(OUT/'lod_comparison.png')
    damage_sheet=Image.new('RGB',(1800,1200));dd=ImageDraw.Draw(damage_sheet)
    for zone,(_,_,hpname,_) in d.ZONES.items():
        tree=r.load(ASSETS/('rh_pir_elite_dmg_'+zone+'.3db'))[1]
        hp=export['hardpoints'][hpname.lower()]
        export['damage'][zone]=[f.base.world(standalone_groups(tree,lv),hp['orientation'],hp['position']) for lv in range(3)]
    removed={p for v in d.ZONES.values() for p in v[:2]}
    for lv in range(3):
        assembly=[g for p,gs in export['levels'][lv].items() if p not in removed for g in gs]
        assembly += [g for levels in export['damage'].values() for g in levels[lv]]
        for row,(cam,center,radius) in enumerate([((-1,.7,1),(0,0,0),10.7),((-1,.4,1),(0,1.3,8.1),3.5)]):
            damage_sheet.paste(shot(assembly,cam,center,radius,600),(lv*600,row*600))
            dd.text((lv*600+15,row*600+15),'DAMAGED LOD '+str(lv),fill='white')
    damage_sheet.save(OUT/'damage_lods.png')
    save('review_data.json',export)
    print('PREVIEWS READY from exported CMP/3DB, all levels and damage',flush=True)


if __name__ == '__main__':
    {'prepare':prepare,'export':export,'check':check,'previews':previews}[sys.argv[1]]()
