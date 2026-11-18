"""Offline all-zone RH pirate elite damage, based on the accepted revision 03."""
import collections
import copy
import json
import itertools
import secrets
import struct
import sys
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull

sys.dont_write_bytecode = True
import rh_elite_tail_refine as prev
import rh_concept_b_final_damage as dmg
from rh_concept_b_damage_reference import groups as cap_groups
from rh_concept_b_v2_sur import read_hulls
from ship_collision_audit import sur_parts, surface
r, f, b = prev.r, prev.f, prev.r.b
OUT = r.OUT/'damage_04'
ASSETS = OUT/'assets'
SOURCE = prev.OUT/(prev.NAME+'.cmp')
EXPECTED = '6ff4fe31fb882903f3a8f4135f42ff5842cb28dfaf50f11dca8525568c1e4cc6'
PALE, RED, BROWN = r.PALE, r.RED, r.BROWN
DM = f.mesh.crc('pir_r_dmg3'); EQ = f.mesh.crc('Equip_genD')
ZONES = {
    'port_wing': ('Rh_port_wing_lod1', 'Rh_port_wing_mesh', 'DpPort_Wing', 'rh_pir_elite_dmg_port_wing_cap'),
    'starboard_wing': ('Rh_starboard_wing_lod1', 'Rh_starboard_wing_mesh', 'DpStarboard_Wing', 'rh_pir_elite_dmg_starboard_wing_cap'),
    'port_engine': ('Rh_port_engine_lod1', 'Rh_port_engine_lod1', 'DpPort_Engine', 'rh_pir_elite_dmg_portengine_cap'),
    'starboard_engine': ('Rh_starboard_engine_lod1', 'Rh_starboard_engine_lod1', 'DpStarboard_Engine', 'rh_pir_elite_dmg_starengine_cap'),
    'tail': ('Rh_tail_lod1', 'Rh_tail_lod1', 'DpTail', 'rh_pir_elite_dmg_tail_cap'),
}


def save(name, value):r.save(OUT/name, value)


def prepare():
    assert f.digest(SOURCE) == EXPECTED
    report = json.loads((prev.OUT/'validation.json').read_text())
    op = prev.OUT/(prev.NAME+'_open.cmp')
    assert f.digest(op) == report['open_cmp_sha256'], 'Preserve user-edited HPs before rebuilding'
    OUT.mkdir(parents=True, exist_ok=True); ASSETS.mkdir(exist_ok=True)
    ns = r.load(SOURCE)[1]; parts = r.world(ns)
    atlas = f.audit.material_table([r.MAT, r.ENV]); images = OUT/'textures'; images.mkdir(exist_ok=True)
    mids = {g['material'] for gs in parts.values() for g in gs}|{DM, EQ}
    materials = {}
    for mid in mids:
        m = atlas[mid]; file = images/(m['name']+'.png')
        if m['image'] is not None:m['image'].save(file)
        materials[str(mid)] = dict(name=m['name'], colour=np.asarray(m['colour'])[:3],
            image=str(file) if m['image'] is not None else None, texture=m['texture'])
    shell = json.loads((prev.OUT/'geometry.json').read_text())['tail_shell']
    wing_sources = {}
    for side in ('port', 'starboard'):
        gs = parts[f'Rh_{side}_wing_mesh']
        comp = next(c for c in r.components(gs) if c['triangles'] == 44)
        wing_sources[side] = prev.m.take(gs, comp)
    save('input.json', dict(parts=parts, wings=wing_sources, tail_shell=shell, materials=materials,
                           damage_material=DM, equipment_material=EQ, source_sha256=EXPECTED))
    refs = [SOURCE, op, r.MAT, r.LIVE, r.OUT/'user_source.cmp',
            f.audit.DATA/'ships/rheinland/rh_pir_elite/rh_pir_elite1.cmp',
            f.audit.DATA/'ships/rheinland/rh_pir_elite/rh_pir_elite1.sur',
            f.audit.DATA/'ships/rheinland/rh_elite/rh_elite_dmg_port_wing.3db']
    # The current freighter is a construction/UV reference, not geometry to copy.
    freighter = f.audit.DATA/'ships/rheinland/rh_pir_freighter'
    refs += [p for p in freighter.glob('*dmg*.3db')]
    save('source_manifest.json', dict(files={str(p):f.digest(p) for p in refs if p.exists()},
        references=['rh_pir_freighter/panel_damage: peeled sheets and machinery backing',
                    'rh_freighter: original torn geometry, no imported damaged mesh'],
        original_cmp=str(refs[5]), original_sur=str(refs[6]), installed=False))
    print('PREPARED all five zones', flush=True)


def world_hp(ns, pose=('Sc_extend wing', 0)):
    tr, _ = f.audit.transforms(ns, pose); result = {}
    for path, node in f.mesh.walk(ns):
        if '/hardpoints/' not in path.lower() or not path.lower().endswith('/position'):continue
        file = path.split('/')[2]; name = path.split('/')[-2]; rot, t = tr[file.lower()]
        orient = next(n.blob for p, n in f.mesh.walk(ns) if p == path.rsplit('/', 1)[0]+'/Orientation')
        result[name.lower()] = dict(name=name, file=file, position=rot@np.frombuffer(node.blob, '<f4')+t,
            orientation=rot@np.frombuffer(orient, '<f4').reshape(3, 3))
    return result


def export():
    header, source = r.load(SOURCE); ns = copy.deepcopy(source)
    data = json.loads((OUT/'damage_world.json').read_text()); input_data = json.loads((OUT/'input.json').read_text())
    assert input_data['source_sha256'] == f.digest(SOURCE)
    parts = r.world(source); names = f.component_map(ns); rootfile = next(k for k, v in names.items() if v == 'Root')
    overrides=input_data.get('parts_override',{})
    if overrides:
        transforms,_=f.audit.transforms(ns,('Sc_extend wing',0));library=f.mesh.child(ns[0],'VMeshLibrary')
        for file,owner in names.items():
            if owner not in overrides:continue
            parts[owner]=f.merge(r.flatten_groups(overrides[owner]));rot,t=transforms[file.lower()]
            local=f.base.world(parts[owner],rot.T,-rot.T@t);blob,verts=f.mesh.pack(f.merge(local));vn='tail_split_'+owner+'.vms'
            library.children.append(f.folder(vn,f.mesh.Node('VMeshData',blob)))
            ref=f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'MultiLevel'),'Level0'),'VMeshPart'),'VMeshRef')
            ref.blob=f.fresh_ref(vn,blob,verts)
        for owner,world_lines in input_data.get('wire_override',{}).items():
            file=next(k for k,v in names.items() if v==owner);rot,t=transforms[file.lower()]
            lines=b.clean(world_lines);local=(np.array(lines)-t)@rot
            points={b.key(q):q for q in local.reshape(-1,3)};keys=sorted(points);lookup={key:i for i,key in enumerate(keys)}
            tri=np.zeros((1,3,8));tri[0,:,:3]=[[0,0,0],[.001,0,0],[0,.001,0]];tri[:,:,5]=1
            blob,verts=f.mesh.pack([dict(material=PALE,corners=tri,unused=204)]);raw=bytearray(blob);base=len(verts)
            extra=np.zeros((len(keys),8),'<f4');extra[:,:3]=[points[key] for key in keys];extra[:,5]=1
            struct.pack_into('<H',raw,14,base+len(keys));raw+=extra.tobytes();vn='tail_split_wire_'+owner+'.vms'
            library.children.append(f.folder(vn,f.mesh.Node('VMeshData',bytes(raw))))
            ids=[lookup[b.key(q)] for q in local.reshape(-1,3)]
            payload=struct.pack('<II4H',16,f.mesh.crc(vn),base,len(keys),len(ids),len(keys))+np.array(ids,'<u2').tobytes()
            f.mesh.child(f.mesh.child(f.mesh.child(ns[0],file),'VMeshWire'),'VWireData').blob=payload
        used={struct.unpack_from('<I',node.blob,4)[0] for p,node in f.mesh.walk(ns) if p.lower().endswith(('/vmeshref','/vwiredata'))}
        library.children=[node for node in library.children if f.mesh.crc(node.name) in used]
    hps = world_hp(ns); anchors = {}; moves = {}
    for zone, (_, owner, hpname, _) in ZONES.items():
        hp = hps[hpname.lower()]; before = np.array(hp['position']); position = before.copy()
        if 'engine' in zone:
            p = r.points(parts[owner]); center = (p.min(0)+p.max(0))/2
            position = np.array([center[0], p[:, 1].max(), center[2]])
        elif zone == 'tail':position = np.array([0, 1.26, 8.112])
        anchors[zone] = dict(name=hpname, position=position, orientation=np.array(hp['orientation']))
        for path, node in f.mesh.walk([f.mesh.child(ns[0], rootfile)]):
            if path.lower().endswith('/'+hpname.lower()+'/position'):node.blob = position.astype('<f4').tobytes()
        moves[zone] = dict(name=hpname, before=before, after=position)
    salt = secrets.token_hex(6); mapping = b.salt_tree(ns, salt)
    target = ASSETS/'rh_pir_elite.cmp'; target.write_bytes(f.mesh.write_tree(header, ns))
    after = r.load(target)[1]
    oldhp, newhp = r.hp_bytes(source), r.hp_bytes(after)
    changed = [key for key in oldhp if oldhp[key] != newhp[key]]
    assert len(changed) == 3 and all(key.endswith('/Position') and '/Dp' in key for key in changed), changed
    for tag in ('Cons', 'Animation'):
        get = lambda x:f.mesh.child(f.mesh.child(x[0], 'Cmpnd'), tag) if tag == 'Cons' else f.mesh.child(x[0], tag)
        assert {p:n.blob for p, n in f.mesh.walk([get(source)])} == {p:n.blob for p, n in f.mesh.walk([get(after)])}
    # Preserve equipment, visible geometry, wire and animations; only Dp anchors differ.
    compare = r.world(after)
    for part in parts:
        for a, c in zip(parts[part], compare[part]):assert a['material'] == c['material'] and np.allclose(a['corners'], c['corners'], atol=3e-6)
    cap_records = {}; actual_world = {}
    dmg.OUT = OUT
    for zone, geometry in data.items():
        gs = r.flatten_groups(geometry); hp = anchors[zone]; rot, t = hp['orientation'], hp['position']
        local = f.base.world(gs, rot.T, -rot.T@t)
        name = 'rh_pir_elite_dmg_'+zone
        # Native standalone UTF layout; material libraries stay external.
        dh, dn = r.load(r.OUT/'native_tail_damage.3db')
        blob, verts = f.mesh.pack(f.merge(local)); vn = name+'.vms'
        dn[0].children = [f.folder('VMeshLibrary', f.folder(vn, f.mesh.Node('VMeshData', blob))),
            f.folder('MultiLevel', f.mesh.Node('Switch2', np.array([0, 10000], '<f4').tobytes()),
                f.folder('Level0', f.folder('VMeshPart', f.mesh.Node('VMeshRef', f.fresh_ref(vn, blob, verts))))),
            f.folder('Hardpoints', f.folder('Fixed', f.folder('DpConnect',
                f.mesh.Node('Position', np.zeros(3, dtype='<f4').tobytes()),
                f.mesh.Node('Orientation', np.eye(3, dtype='<f4').tobytes()))))]
        cap_salt = secrets.token_hex(6); resources = b.salt_tree(dn, cap_salt)
        dest = ASSETS/(name+'.3db'); dest.write_bytes(f.mesh.write_tree(dh, dn))
        actual = cap_groups(dest); restored = f.base.world(actual, rot, t)
        for a, c in zip(f.merge(gs), f.merge(restored)):assert a['material'] == c['material'] and np.allclose(a['corners'], c['corners'], atol=5e-6)
        actual_world[zone] = restored
        cap_records[zone] = dict(file=dest.name, sha256=f.digest(dest), salt=cap_salt, resources=resources,
                                 anchor=hp, triangles=sum(len(g['corners']) for g in actual))
    # An offline static assembled CMP makes all five damaged zones inspectable in UTF viewers.
    review = copy.deepcopy(after); lib = f.mesh.child(review[0], 'VMeshLibrary')
    removed = {owner for _, owner, _, _ in ZONES.values()}|{part for part, _, _, _ in ZONES.values()}
    assembled = {k:v for k, v in parts.items() if k not in removed}
    broken_root = f.merge(parts['Root']+[g for gs in actual_world.values() for g in gs])
    assembled['Root'] = broken_root
    cmpnd = f.mesh.child(review[0], 'Cmpnd'); names = f.component_map(review)
    for file, owner in names.items():
        part = f.mesh.child(review[0], file)
        if owner in removed:
            review[0].children.remove(part)
            cmpnd.children = [n for n in cmpnd.children if n.name == 'Cons' or f.mesh.string(f.mesh.child(n, 'Object name').blob) != owner]
    rootfile = next(k for k, v in names.items() if v == 'Root')
    blob, verts = f.mesh.pack(broken_root); vn = 'damage_review_root.vms'; lib.children.append(f.folder(vn, f.mesh.Node('VMeshData', blob)))
    ref = f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(review[0], rootfile), 'MultiLevel'), 'Level0'), 'VMeshPart'), 'VMeshRef')
    ref.blob = f.fresh_ref(vn, blob, verts)
    tr, _ = f.audit.transforms(after, ('Sc_extend wing', 0)); fix = b''
    for file, owner in f.component_map(review).items():
        if owner == 'Root':continue
        rot, t = tr[file.lower()]; fix += owner_bytes('Root')+owner_bytes(owner)+np.r_[t, rot.ravel()].astype('<f4').tobytes()
    f.mesh.child(cmpnd, 'Cons').children = [f.mesh.Node('Fix', fix)]
    review[0].children = [n for n in review[0].children if n.name != 'Animation']
    review_salt = secrets.token_hex(6); review_mapping = b.salt_tree(review, review_salt)
    review_path = OUT/'rh_pir_elite_all_damage_open.cmp'; review_path.write_bytes(f.mesh.write_tree(header, review))
    save('export.json', dict(source_sha256=EXPECTED, cmp_sha256=f.digest(target), salt=salt, resources=mapping,
         damage=cap_records, dp_moves=moves, all_equipment_hp_unchanged=True, intact_geometry_and_rig_unchanged=not bool(overrides),
         ownership_split=input_data.get('ownership_split'),rig_unchanged=True,
         review_sha256=f.digest(review_path), review_salt=review_salt, review_resources=review_mapping, installed=False))
    save('review_data.json', dict(intact=parts, damage=actual_world, assembly=assembled,
         cmp_sha256=f.digest(target), review_sha256=f.digest(review_path), hardpoints=world_hp(after)))
    print('EXPORTED CMP and five damage 3DB; draft attachment anchors', flush=True)


def owner_bytes(s):return s.encode().ljust(64, b'\0')


def previews():
    from PIL import Image, ImageDraw
    from preview import render
    data = json.loads((OUT/'review_data.json').read_text())
    parts = {k:r.flatten_groups(v) for k,v in data['intact'].items()}
    wounds = {k:r.flatten_groups(v) for k,v in data['damage'].items()}
    assembly = [g for gs in data['assembly'].values() for g in r.flatten_groups(gs)]
    mats = f.audit.material_table([r.MAT,r.ENV])
    def shot(gs,cam,center,radius,size=850):
        front=[]
        for g in gs:
            a=g['corners'];n=np.cross(a[:,1,:3]-a[:,0,:3],a[:,2,:3]-a[:,0,:3]);keep=n@np.array(cam)>1e-9
            if keep.any():front.append(dict(g,corners=a[keep]))
        return render(front,mats,np.array(center),radius,cam,size,'texture')
    shots=[('all_damage',assembly,(-1,.7,1),(0,0,0),10.5),
        ('wing_top',assembly,(-.03,1,.03),(-4,-1.6,3.1),3.25),
        ('wing_below',assembly,(-.8,-1,.6),(-4,-1.7,3.5),3.0),
        ('engine_below',assembly,(-1,-.7,1),(-1.82,-3.28,4.8),3.25),
        ('engine_inside',assembly,(1,-1,.6),(-1.82,-3.28,4.8),3.0),
        ('tail_rear',assembly,(-1,.4,1),(0,1.3,8.1),3.5),
        ('tail_side',assembly,(-1,0,0),(0,1.3,7.0),3.5)]
    for name,gs,cam,center,radius in shots:shot(gs,cam,center,radius).save(OUT/(name+'.png'))
    sheet=Image.new('RGB',(1800,1200));draw=ImageDraw.Draw(sheet)
    for i,name in enumerate(['wing_top','wing_below','engine_below','engine_inside','tail_rear','tail_side']):
        x,y=i%3*600,i//3*600;sheet.paste(Image.open(OUT/(name+'.png')).resize((600,600)),(x,y));draw.text((x+15,y+15),name,fill='white')
    sheet.save(OUT/'review.png')
    isolated=Image.new('RGB',(1800,1200));draw=ImageDraw.Draw(isolated)
    for col,(zone,cam) in enumerate([('port_wing',(-.1,1,.2)),('port_engine',(-1,-.55,1)),('tail',(-1,.3,1))]):
        intact=parts[ZONES[zone][1]];p=r.points(intact);center=(p.min(0)+p.max(0))/2;radius=max(np.linalg.norm(p-center,axis=1))*1.15
        for row,gs in enumerate([intact,wounds[zone]]):
            isolated.paste(shot(gs,cam,center,radius,600),(col*600,row*600))
            draw.text((col*600+15,row*600+15),zone+(' intact' if row==0 else ' torn'),fill='white')
    isolated.save(OUT/'parts_comparison.png')
    print('CULLED PREVIEWS READY',flush=True)


def covered(points,hulls,tolerance=4e-4):
    good=np.zeros(len(points),bool)
    for h in hulls:
        q=ConvexHull(h.points);good|=np.all(points@q.equations[:,:3].T+q.equations[:,3]<=tolerance,axis=1)
    return good


def partition(gs,client,steps=None,cuts=None):
    tris=np.concatenate([g['corners'][...,:3] for g in gs]);points=tris.reshape(-1,3)
    if steps is None:return [dmg.sur.make_hull(points,client)]
    limits=[np.linspace(points[:,i].min()-1e-5,points[:,i].max()+1e-5,n+1) for i,n in enumerate(steps)]
    for axis,values in (cuts or {}).items():
        lo,hi=points[:,axis].min()-1e-5,points[:,axis].max()+1e-5
        limits[axis]=[lo]+[v for v in values if lo<v<hi]+[hi]
    regions=[[(i,limits[i][j],limits[i][j+1]) for i,j in enumerate(cell)] for cell in itertools.product(*[range(len(v)-1) for v in limits])]
    return dmg.hull_regions(tris,client,regions)


def write_sur(path,own,aggregate,hpids):
    raw=bytearray(b'vers'+struct.pack('<f',2.))
    rootkey='Root' if 'Root' in own else 0
    for owner,hulls in own.items():
        root=owner==rootkey;ids=sorted(set(hpids.get(owner,[])))
        if root:ids=sorted({i for values in hpids.values() for i in values})
        blob,lo,hi=dmg.sur.encode_surface(aggregate if root else hulls)
        pid=f.mesh.crc(owner) if isinstance(owner,str) else owner
        raw+=struct.pack('<II',pid,2+int(root)+int(bool(ids)))
        if root:raw+=b'!fxd'
        raw+=b'exts'+struct.pack('<6f',*lo,*hi)+b'surf'+struct.pack('<I',len(blob))+blob
        if ids:raw+=b'hpid'+struct.pack('<I',len(ids))+np.asarray(ids,'<u4').tobytes()
    path.write_bytes(raw)
    for pid,chunks in sur_parts(raw):
        assert (b'!fxd' in [tag for tag,_ in chunks])==(pid==(f.mesh.crc(rootkey) if isinstance(rootkey,str) else rootkey))
        for tag,blob in chunks:
            if tag==b'surf':surface(blob)


def collision():
    ns=r.load(ASSETS/'rh_pir_elite.cmp')[1];parts=r.world(ns);names=f.component_map(ns)
    files={v:k for k,v in names.items()};tr,_=f.audit.transforms(ns,('Sc_extend wing',0))
    own={};aggregate=[];hpids=collections.defaultdict(list);checks=[]
    wing_owner={f'Rh_{s}_wing_mesh':f'Rh_{s}_wing_lod1' for s in ('port','starboard')}
    for name,gs in parts.items():
        if name in wing_owner.values() or name=='Rh_glass_lod1' or name.startswith('BayDoor'):continue
        owner=wing_owner.get(name,name);client=f.mesh.crc(owner)
        if name=='Root':
            hulls=[]
            for comp in r.components(gs):
                cg=prev.m.take(gs,comp);p=r.points(cg)
                if np.linalg.matrix_rank(p-p[0],tol=1e-5)<3:
                    # Real planar cabin floor/backing: give that exact footprint
                    # finite physical thickness, not an equipment marker cube.
                    if np.linalg.matrix_rank(p-p[0],tol=1e-5)==2:
                        normal=np.linalg.svd(p-p.mean(0))[2][-1]
                        hulls.append(dmg.sur.make_hull(np.concatenate([p+normal*.012,p-normal*.012]),client))
                    continue
                # The persistent C frame must not acquire a convex slab through
                # its large negative spaces. Other small closed fittings stay whole.
                lo,hi=p.min(0),p.max(0)
                frame=comp['triangles']==395 or (abs((hi[0]-lo[0])-1.04)<.001 and lo[2]>2.49 and hi[1]-lo[1]>1)
                steps=(1,5,5) if frame else None
                hulls+=partition(cg,client,steps)
        else:
            steps=(3,1,1) if 'wing_mesh' in name else (1,1,3) if 'engine' in name else (3,3,1) if 'tail' in name else None
            hulls=partition(gs,client,steps)
        p=r.points(gs);good=covered(p,hulls)
        if name=='Root' and not good.all():
            save('collision_uncovered.json',p[~good])
        assert good.all(),(name,'missing collision vertices',int((~good).sum()))
        rot,t=tr[files[owner].lower()]
        own[owner]=[dmg.sur.Hull((h.points-t)@rot,h.faces,h.hull_id) for h in hulls]
        aggregate+=hulls;checks.append(dict(owner=owner,visual=name,hulls=len(hulls),covered_vertices=len(p)))
        if name in wing_owner:
            # Local child body for separated assemblies; the active ship aggregate
            # uses ONLY the stable CollisionGroup owner, never a duplicate wing.
            cr,ct=tr[files[name].lower()]
            own[name]=[dmg.sur.Hull((h.points-ct)@cr,h.faces,f.mesh.crc(name)) for h in hulls]
    # The retail pirate files were removed by the user. Reuse the authenticated
    # native equipment hulls retained in the earlier verified unfolded export.
    prior=f.OUT.parent/'final_v2';source_cmp=prior/'unfolded_reference.cmp';source_sur=prior/'rh_concept_b.sur'
    prior_report=json.loads((prior/'sur_manifest.json').read_text())
    assert f.digest(source_sur)==prior_report['sur_sha256']
    assert prior_report['original_sur_sha256']=='d6d2e951b4e0f8da97b020f41e18ab160dd6c407b0753ee3d3b21b98e0b706e2'
    old_hp=world_hp(r.load(source_cmp)[1],None);new_hp=world_hp(ns)
    hp_names={f.mesh.crc(h['name']):key for key,h in old_hp.items()};embedded={}
    for pid,chunks in sur_parts(source_sur.read_bytes()):
        if pid!=f.mesh.crc('Root'):continue
        for tag,blob in chunks:
            if tag!=b'surf':continue
            for client,p in read_hulls(blob):
                if client in hp_names and hp_names[client]!='hpmount':embedded[hp_names[client]]=p
    expected={h['name'].lower():h for h in prior_report['equipment']};assert set(embedded)==set(expected)
    equipment=[];templates={key:key for key in embedded}
    templates['hpweapon07']='hpweapon05'
    for key,template in templates.items():
        p=embedded[template]
        assert np.allclose([p.min(0),p.max(0)],expected[template]['bounds'],atol=2e-4)
        if key not in new_hp:continue
        source,target=old_hp[template],new_hp[key]
        local=(p-source['position'])@source['orientation'];world=local@target['orientation'].T+target['position']
        h=dmg.sur.make_hull(world,f.mesh.crc(target['name']));aggregate.append(h)
        actual=names[target['file']];owner=wing_owner.get(actual,actual)
        for recipient in {owner,actual}:
            rot,t=tr[files[recipient].lower()]
            assert recipient in own,(key,recipient)
            own[recipient].append(dmg.sur.Hull((h.points-t)@rot,h.faces,h.hull_id));hpids[recipient].append(h.hull_id)
        equipment.append(dict(name=target['name'],owner=owner,hardpoint_owner=actual,template=source['name'],volume=ConvexHull(h.points).volume,
                              bounds=[h.points.min(0),h.points.max(0)]))
    need={key for key in new_hp if key.startswith(('hpweapon','hpturret','hpthruster','hpmine','hpcm','hpshield','hpmiscgun'))}
    assert need <= {h['name'].lower() for h in equipment},need-{h['name'].lower() for h in equipment}
    all_points=np.concatenate([h.points for h in aggregate]);envelope=dmg.sur.make_hull(all_points,0)
    center=(all_points.min(0)+all_points.max(0))/2
    shield=dmg.sur.make_hull(center+(envelope.points-center)*1.06,f.mesh.crc('HpMount'))
    assert covered(all_points,[shield]).all();own['Root'].append(shield);aggregate.append(shield);hpids['Root'].append(shield.hull_id)
    write_sur(ASSETS/'rh_pir_elite.sur',own,aggregate,hpids)
    manifest=dict(cmp_sha256=f.digest(ASSETS/'rh_pir_elite.cmp'),sur_sha256=f.digest(ASSETS/'rh_pir_elite.sur'),
        pose='extended static; only Root has !fxd',parts=checks,equipment=equipment,
        equipment_reference=dict(cmp=str(source_cmp),cmp_sha256=f.digest(source_cmp),sur=str(source_sur),sur_sha256=f.digest(source_sur),
            provenance='Authenticated native hulls retained in final_v2; all reference bounds checked'),
        shield=dict(name='HpMount',volume=ConvexHull(shield.points).volume,bounds=[shield.points.min(0),shield.points.max(0)],covers_all=True),damage={})
    for zone in ZONES:
        dest=ASSETS/('rh_pir_elite_dmg_'+zone+'.3db');gs=cap_groups(dest);hulls=[]
        for comp in r.components(gs):
            cg=prev.m.take(gs,comp);p=r.points(cg)
            if np.linalg.matrix_rank(p-p[0],tol=1e-6)<3:continue
            steps=None
            if comp['triangles']>55:
                # Each closed torn skin is split; do not bridge its entire opening.
                steps=(2,2,4) if 'engine' in zone else (3,1,2) if 'wing' in zone else (1,5,3)
            cuts={0:[-.54,.54]} if zone=='tail' and steps is not None and (OUT/'frame_split_geometry.json').exists() else None
            hulls+=partition(cg,0,steps,cuts)
        assert covered(r.points(gs),hulls).all(),zone
        write_sur(dest.with_suffix('.sur'),{0:hulls},hulls,{})
        manifest['damage'][zone]=dict(sha256=f.digest(dest.with_suffix('.sur')),hulls=len(hulls),triangles=sum(len(h.faces) for h in hulls),covered=True)
    save('collision_check.json',manifest)
    save('sur_preview.json',[dict(client=h.hull_id,points=h.points,faces=h.faces,shield=h.hull_id==shield.hull_id) for h in aggregate])
    # Replace the unavailable historical paths with the actual pinned provenance.
    sources=json.loads((OUT/'source_manifest.json').read_text());sources['original_cmp']='historical rh_pir_elite1.cmp removed from game'
    sources['original_sur']='historical rh_pir_elite1.sur; authenticated hash recorded by final_v2'
    sources['equipment_reference']=manifest['equipment_reference'];save('source_manifest.json',sources)
    print('COLLISION READY',len(aggregate),'hulls including',len(equipment),'equipment and shield',flush=True)


def validate():
    import re
    exp=json.loads((OUT/'export.json').read_text());coll=json.loads((OUT/'collision_check.json').read_text())
    blend=json.loads((OUT/'blender_check.json').read_text());geo=json.loads((OUT/'damage_geometry_check.json').read_text())
    current=f.digest(ASSETS/'rh_pir_elite.cmp')
    assert current==exp['cmp_sha256']==coll['cmp_sha256']==blend['cmp_sha256']
    assert f.digest(OUT/'rh_pir_elite_damage.blend')==blend['blend_sha256']
    assert f.digest(ASSETS/'rh_pir_elite.sur')==coll['sur_sha256']
    assert f.digest(SOURCE)==EXPECTED
    mats=f.audit.material_table([r.MAT,r.ENV]);resources=set();reports={}
    for path in [ASSETS/'rh_pir_elite.cmp']+sorted(ASSETS.glob('*.3db')):
        ns=r.load(path)[1];libs={};counts=[]
        assert not any(n.name.lower() in ('material library','texture library') for _,n in f.mesh.walk(ns))
        for p,node in f.mesh.walk(ns):
            if not p.lower().endswith('/vmeshdata'):continue
            key=p.split('/')[-2];crc=f.mesh.crc(key);assert crc not in resources;resources.add(crc)
            verts,groups,ids=f.audit.decode(node.blob);libs[crc]=(verts,groups,ids)
            assert len(verts)<65536 and len(ids)<65536 and np.isfinite(verts).all()
            at=0
            for mid,start,end,count,unused in groups:
                assert mid in mats,(path.name,hex(mid))
                assert count%3==0 and start<=end<len(verts)
                assert count==0 or ids[at:at+count].max()+start<=end
                at+=count
            assert at==len(ids);counts.append(dict(vertices=len(verts),indices=len(ids),groups=len(groups)))
        for p,node in f.mesh.walk(ns):
            if p.lower().endswith('/vmeshref'):
                size,crc,v0,nv,i0,ni,g0,ng=struct.unpack_from('<II6H',node.blob)
                assert size==60 and crc in libs
                verts,groups,ids=libs[crc];assert v0+nv<=len(verts) and i0+ni<=len(ids) and g0+ng<=len(groups)
            elif p.lower().endswith('/vwiredata'):
                size,crc,bias,nv,ni,total=struct.unpack_from('<II4H',node.blob);ids=np.frombuffer(node.blob,'<u2',offset=16)
                assert size==16 and crc in libs and ni==len(ids) and ni%2==0 and nv==total==len(set(ids))
                assert ni==0 or bias+ids.max()<len(libs[crc][0])
        if path.suffix=='.3db':
            zone=path.stem.removeprefix('rh_pir_elite_dmg_');gs=cap_groups(path)
            assert f.digest(path)==exp['damage'][zone]['sha256']
            assert f.digest(path.with_suffix('.sur'))==coll['damage'][zone]['sha256']
            uv_stats=[]
            for g in gs:
                mat=mats[g['material']];assert not ('metal' in mat['name'].lower() or 'metal' in (mat['texture'] or '').lower())
                a=g['corners'];area=np.linalg.norm(np.cross(a[:,1,:3]-a[:,0,:3],a[:,2,:3]-a[:,0,:3]),axis=1)/2
                uvarea=abs(np.linalg.det(np.stack((a[:,1,6:]-a[:,0,6:],a[:,2,6:]-a[:,0,6:]),axis=1)))/2
                collapsed=(uvarea<1e-10)&(area>1e-6);assert not collapsed.any(),(zone,mat['name'],int(collapsed.sum()))
                uv_stats.append(dict(material=mat['name'],texture=mat['texture'],triangles=len(a),meaningful_collapsed_uv=0))
            reports[path.name]=dict(sha256=f.digest(path),draws=counts,materials=uv_stats)
        else:reports[path.name]=dict(sha256=current,draws=counts)
    actual=r.world(r.load(OUT/'rh_pir_elite_all_damage_open.cmp')[1],None)
    intended=json.loads((OUT/'review_data.json').read_text())['assembly']
    assert set(actual)==set(intended)
    for name,gs in actual.items():
        a,c=f.merge(gs),f.merge(r.flatten_groups(intended[name]));assert len(a)==len(c)
        for x,y in zip(a,c):assert x['material']==y['material'] and np.allclose(x['corners'],y['corners'],atol=4e-6)
    for zone in ('port_wing','starboard_wing'):assert geo[zone]['retained_fraction']>=.20
    ns=r.load(ASSETS/'rh_pir_elite.cmp')[1];hp=world_hp(ns);names=f.component_map(ns)
    assert len(hp)==79 and len({h['name'].lower() for h in hp.values()})==79
    # Current generator contract already uses all five stable receiving points.
    template=Path('D:/Games/FL_MOD/Assets/Pythonlancer/templates/hardcoded_inis/shiparch/playerships/rh_pir_elite.ini')
    txt=template.read_text(encoding='utf8');sections=re.split(r'(?=\[CollisionGroup\])',txt)[1:];bindings=[]
    draft=['; Reference bindings only. Preserve the existing complete CollisionGroups and balance.','; External shared MAT; no detached-debris caps.','']
    for zone,(part,visual,hpname,simple) in ZONES.items():
        block=next(s for s in sections if re.search(r'^obj\s*=\s*'+re.escape(part)+r'\s*$',s,re.I|re.M))
        assert re.search(r'^dmg_hp\s*=\s*'+hpname+r'\s*$',block,re.I|re.M)
        assert re.search(r'^dmg_obj\s*=\s*'+simple+r'\s*$',block,re.I|re.M)
        assert 'group_dmg_' not in block.lower()
        assert names[hp[hpname.lower()]['file']]=='Root'
        bindings.append(dict(zone=zone,collision_group=part,visual_child=visual,receiving_hp=hpname,simple=simple))
        draft+=['[CollisionGroup]','obj = '+part,'dmg_hp = '+hpname,'dmg_obj = '+simple,'',
            '[Simple]','nickname = '+simple,r'DA_archetype = ships\rheinland\rh_pir_elite\rh_pir_elite_dmg_'+zone+'.3db',
            r'material_library = ships\rheinland\rh_pir_playerships.mat','']
    (OUT/'damage_bindings.ini').write_text('\n'.join(draft),encoding='utf8')
    # Check all combinations of logical detachments: immutable Root survives,
    # only the selected wing proxy and visual child are removed together.
    cases=[]
    for mask in range(32):
        selected=[z for i,z in enumerate(ZONES) if mask&(1<<i)]
        removed={p for z in selected for p in ZONES[z][:2]}
        survivors=set(names.values())-removed;assert 'Root' in survivors
        cases.append(dict(destroyed=selected,surviving_parts=len(survivors),caps=len(selected)))
    guard=json.loads((OUT/'source_manifest.json').read_text())['files']
    assert all(f.digest(Path(p))==h for p,h in guard.items()),'External/source files changed during authoring'
    report=dict(cmp_sha256=current,blender_sha256=blend['blend_sha256'],files=reports,bindings=bindings,
        logical_damage_combinations=cases,external_files_unchanged=guard,pythonlancer_template_sha256=f.digest(template),
        hardpoints_total=79,equipment_hp_unchanged=True,changed_hp_positions=3,cap_hp_unique=True,external_materials=True,
        near_model_only=True,game_launched=False,installed=False)
    save('validation.json',report)
    print('VALIDATED five damage zones, external materials, 32 ownership combinations; no game writes',flush=True)


if __name__ == '__main__':
    {'prepare':prepare, 'export':export, 'previews':previews, 'collision':collision, 'validate':validate}[sys.argv[1]]()
