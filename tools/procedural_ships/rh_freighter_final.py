"""Offline Q13 delivery. Never writes to DATA or overwrites the user's HP source."""
import collections
import copy
import json
from pathlib import Path
import secrets
import shutil
import struct
import numpy as np
import rh_concept_b_final as f
import rh_freighter_q13 as q
import full_ship_audit as animation_audit

ROOT=Path(__file__).resolve().parents[2]
TOPIC=ROOT/'out/ship_design/rh_freighter'
PREVIOUS=TOPIC/'prototypes/uv_15'
OUT=TOPIC/'rh_pir_freighter'
SOURCE=OUT/'source'
ASSETS=OUT/'assets'
GAME=Path('D:/Games/FL_MOD')
NATIVE=TOPIC/'references/native_source/rh_pir_freighter_original.cmp'
MAT=GAME/'DATA/ships/rheinland/rh_pir_playerships.mat'
ENV=GAME/'DATA/fx/envmapbasic.mat'
PARTS={'port_engine':'port_engine_lod1','starboard_engine':'starboard_engine_lod1',
       'port_side_panel':'rh_port_side_lod1','starboard_side_panel':'rh_star_side_lod1'}

def dump(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,default=lambda a:a.tolist() if isinstance(a,np.ndarray) else float(a)),encoding='utf8')

def tree(path):return f.mesh.read_tree(Path(path).read_bytes())
def read(name):return json.loads((OUT/name).read_text(encoding='utf8'))
def packed(groups):return [dict(g,corners=np.array(g['corners'],float)) for g in groups]
def points(groups):return np.concatenate([np.array(g['corners'])[...,:3].reshape(-1,3) for g in groups])

def world(nodes,pose=None,level=0):
    names=f.component_map(nodes);tr,_=f.audit.transforms(nodes,pose)
    return {names[file]:f.base.world(gs,*tr[file.lower()]) for file,gs in f.local_geometry(nodes,level).items()}

def hardpoints(nodes,pose=None):
    names=f.component_map(nodes);tr,_=f.audit.transforms(nodes,pose);result={}
    for file,name in names.items():
        part=f.mesh.child(nodes[0],file);r,t=tr[file.lower()]
        hp=next((n for n in part.children if n.name.lower()=='hardpoints'),None)
        if hp is None:continue
        for kind in hp.children:
            for h in kind.children:
                leaves={n.name.lower():n for n in h.children}
                p=np.frombuffer(leaves['position'].blob,'<f4');rot=np.frombuffer(leaves['orientation'].blob,'<f4').reshape(3,3)
                key=h.name.lower();assert key not in result, h.name
                result[key]=dict(name=h.name,owner=name,kind=kind.name,position=r@p+t,orientation=r@rot,
                    leaves={n.name:n.blob.hex() for n in h.children})
    return result

def set_hardpoints(nodes,hps,pose=('Sc_extend wing',0)):
    names=f.component_map(nodes);tr,_=f.audit.transforms(nodes,pose);files={v:k for k,v in names.items()}
    for file in names:
        p=f.mesh.child(nodes[0],file);p.children=[n for n in p.children if n.name.lower()!='hardpoints']
    for h in hps.values():
        file=files[h['owner']];p=f.mesh.child(nodes[0],file);r,t=tr[file.lower()]
        folder=next((n for n in p.children if n.name=='Hardpoints'),None)
        if folder is None:folder=f.folder('Hardpoints');p.children.append(folder)
        kind=next((n for n in folder.children if n.name==h['kind']),None)
        if kind is None:kind=f.folder(h['kind']);folder.children.append(kind)
        leaf=f.folder(h['name'],*[f.mesh.Node(k,bytes.fromhex(v)) for k,v in h['leaves'].items()])
        for n in leaf.children:
            if n.name.lower()=='position':n.blob=np.array(r.T@(np.array(h['position'])-t),'<f4').tobytes()
            if n.name.lower()=='orientation':n.blob=np.array(r.T@np.array(h['orientation']),'<f4').tobytes()
        kind.children.append(leaf)

def simple_geometry(nodes):
    libs={f.mesh.crc(p.split('/')[-2]):f.audit.decode(n.blob) for p,n in f.mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    ref=next(n for p,n in f.mesh.walk(nodes) if p.lower().endswith('/level0/vmeshpart/vmeshref'))
    return f.audit.extract(ref.blob,libs)

def prepare_blender():
    _,ns=tree(OUT/'authoring_animated.cmp');mats=f.audit.material_table([MAT,ENV]);w=world(ns,('Sc_extend wing',0))
    used={g['material'] for gs in w.values() for g in gs}|{f.mesh.crc(n) for n in ('pir_r_dmg3','Equip_genD','debris')}
    images={};td=OUT/'textures';td.mkdir(exist_ok=True)
    for mid in used:
        m=mats[mid];entry={k:v for k,v in m.items() if k!='image'}
        if m['image'] is not None:
            path=td/(m['texture'].rsplit('.',1)[0]+'.png');m['image'].save(path);entry['image_path']=str(path)
        images[mid]=entry
    mechanical=json.loads((PREVIOUS/'mechanical_geometry.json').read_text())
    cockpit=next(o for o in mechanical['objects'] if o['name']=='Original cockpit - immutable')
    key=lambda t:tuple(sorted(tuple(p.round(4)) for p in np.array(t)[:,:3]))
    keys={key(t) for g in cockpit['groups'] for t in g['corners']};preserve=[];working=[]
    for g in w['Root']:
        kept=[t for t in g['corners'] if key(t) in keys];rest=[t for t in g['corners'] if key(t) not in keys]
        if kept:preserve.append(dict(g,corners=np.array(kept)))
        if rest:working.append(dict(g,corners=np.array(rest)))
    assert sum(len(g['corners']) for g in preserve)==426
    dump(OUT/'blender_input.json',dict(cmp_sha256=f.digest(OUT/'authoring_animated.cmp'),
        objects=[dict(name=n,groups=gs) for n,gs in w.items()],materials=images,
        preserved_cockpit=preserve,lod_root_working=working,
        damage_material=f.mesh.crc('pir_r_dmg3'),equipment_material=f.mesh.crc('Equip_genD')))

def pin():
    assert shutil.disk_usage(ROOT).free>4*1024**3
    SOURCE.mkdir(parents=True,exist_ok=True);ASSETS.mkdir(exist_ok=True)
    paths={'user_open.cmp':PREVIOUS/'rh_pir_freighter_review_open.cmp',
           'animated_uv15.cmp':PREVIOUS/'rh_pir_freighter.cmp','original.cmp':NATIVE,
           'original.sur':GAME/'DATA/ships/rheinland/rh_pir_freighter/rh_pir_freighter.sur'}
    for zone in PARTS:
        for ext in ('.3db','.sur'):
            name='rh_pir_freighter_dmg_'+zone+ext
            paths[name]=GAME/'DATA/ships/rheinland/rh_pir_freighter'/name
    pinned={}
    for name,path in paths.items():
        target=SOURCE/name;sha=f.digest(path)
        if target.exists():assert f.digest(target)==sha,('Source changed; preserve both deliberately',path)
        else:shutil.copy2(path,target)
        pinned[name]=dict(path=str(path),sha256=sha,bytes=path.stat().st_size)
    dump(OUT/'source_manifest.json',dict(files=pinned,mat=dict(path=str(MAT),sha256=f.digest(MAT)),installed=False))
    header,animated=tree(SOURCE/'animated_uv15.cmp');_,opened=tree(SOURCE/'user_open.cmp')
    aw=world(animated,('Sc_extend wing',0));ow=world(opened)
    assert aw.keys()==ow.keys()
    errors={}
    for part in aw:
        assert len(aw[part])==len(ow[part])
        err=0
        for a,b in zip(aw[part],ow[part]):
            assert a['material']==b['material'] and a['corners'].shape==b['corners'].shape
            err=max(err,float(abs(a['corners']-b['corners']).max()))
        assert err<2e-4,(part,err);errors[part]=err
    before=hardpoints(animated,('Sc_extend wing',0));authoritative=hardpoints(opened)
    changes={}
    for key,h in authoritative.items():
        old=before.get(key)
        if old is None or old['owner']!=h['owner'] or old['kind']!=h['kind'] or not np.allclose(h['position'],old['position'],atol=2e-5) or not np.allclose(h['orientation'],old['orientation'],atol=2e-5) or h['leaves'].keys()!=old['leaves'].keys():
            changes[key]=dict(before=old,after=h)
    set_hardpoints(animated,authoritative)
    final=hardpoints(animated,('Sc_extend wing',0));assert final.keys()==authoritative.keys()
    for k,h in authoritative.items():
        assert final[k]['owner']==h['owner']
        assert np.allclose(final[k]['position'],h['position'],atol=3e-5),k
        assert np.allclose(final[k]['orientation'],h['orientation'],atol=3e-5),k
        for tag,value in h['leaves'].items():
            if tag.lower() not in ('position','orientation'):assert final[k]['leaves'][tag]==value
    (OUT/'authoring_animated.cmp').write_bytes(f.mesh.write_tree(header,animated))
    dump(OUT/'hardpoints.json',authoritative)
    dump(OUT/'hardpoint_transfer.json',dict(source_sha256=f.digest(SOURCE/'user_open.cmp'),geometry_error=errors,
        before_count=len(before),after_count=len(final),changes=changes,removed=sorted(before.keys()-final.keys()),
        flight_world_transforms_preserved=True,all_other_hp_fields_preserved=True))
    mats=f.audit.material_table([MAT,ENV]);_,native=tree(SOURCE/'original.cmp')
    native_world=world(native,('Sc_extend wing',0));native_hps=hardpoints(native,('Sc_extend wing',0));damages=[]
    for zone,part in PARTS.items():
        path=SOURCE/('rh_pir_freighter_dmg_'+zone+'.3db');_,ns=tree(path);gs=simple_geometry(ns)
        damages.append(dict(zone=zone,groups=gs,bounds=[points(gs).min(0),points(gs).max(0)],
            materials=[mats[g['material']]['name'] for g in gs],hardpoints=[p for p,n in f.mesh.walk(ns) if p.endswith('/Position')]))
    dump(OUT/'native_damage_reference.json',damages)
    dump(OUT/'native_audit.json',dict(parts={n:dict(triangles=sum(len(g['corners']) for g in gs),bounds=[points(gs).min(0),points(gs).max(0)]) for n,gs in native_world.items()},
        hardpoints=native_hps,joints=animation_audit.constructs({p.lower():n.blob for p,n in f.mesh.walk(native)})))
    print(json.dumps(dict(pinned_user_sha256=f.digest(SOURCE/'user_open.cmp'),hardpoints=len(final),changed=list(changes),removed=sorted(before.keys()-final.keys()),geometry_max_error=max(errors.values())),indent=2))

if __name__=='__main__':
    import sys
    prepare_blender() if '--prepare-blender' in sys.argv else pin()
