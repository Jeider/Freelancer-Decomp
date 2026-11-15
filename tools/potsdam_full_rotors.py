"""Move each solar plant's central hub into its animated CMP/SUR rotor."""
import argparse
from collections import Counter
import json
import struct as S
import numpy as np
import potsdam_panels as p
m=p.m
OUT=p.OUT/'full_rotors'


def build():
    m.OUT=OUT
    builder=m.Builder()
    relative=f'DATA/SOLAR/OPTIMIZED/potsdam_mega/{p.NAME}'
    previous=builder.read(m.GAME/(relative+'.cmp'))
    builder.read(m.GAME/(relative+'.sur'))
    header,roots=m.utf.read_tree(previous);root=roots[0]
    items,hulls,_=builder.asset(m.GAME/'DATA/solar/misc/space_solar_plant.cmp')
    assert len(items)==len(hulls)==7
    visuals=[m.Visual(levels[:1],(0.,100000.),r,t) for levels,r,t in items]
    library=m.b.one(root,'VMeshLibrary');library.children=[]
    comp=m.b.one(root,'Cmpnd');surfaces=[];draws=0
    for entry in comp.children:
        obj,file=m.b.one(entry,'Object name'),m.b.one(entry,'File name')
        if not obj:continue
        name=m.b.text(obj.blob);node=m.b.one(root,m.b.text(file.blob))
        if name=='Root':
            # A physical root is required by BuildIVP_Real. Its invisible 2 cm
            # anchor lies inside the middle hub at every rotation angle.
            multi=m.utf.Node('MultiLevel')
            multi.children=[m.utf.Node('Switch2',S.pack('<2f',0,100000)),m.utf.Node('Level0')]
            node.children=[multi]
            corners=np.array([[x,y,z] for x in (-.01,.01) for y in (-.01,.01) for z in (-.01,.01)])
            anchor=m.sur.make_hull(corners,m.utf.crc('Root'),False)
            surfaces.append(('Root',[anchor]))
        else:
            assert name in ('Rotor01','Rotor02','Rotor03')
            _,new_part,meshes,stats=p.single_part(p.NAME+'_'+name+'_full',visuals)
            hps=m.b.one(node,'Hardpoints')
            node.children=new_part.children+([hps] if hps else [])
            library.children.extend(meshes);draws+=stats['draw_groups_after']
            surfaces.append((name,[m.old.ExactHull(h.points,h.faces,m.utf.crc(name),False,h.raw) for h in hulls]))
    raw=m.utf.write_tree(header,roots)
    # Animation, joint transforms and all object/part names remain byte-identical.
    old_root=m.utf.read_tree(previous)[1][0]
    def nodes(n):return (n.name,n.blob,tuple(nodes(c) for c in n.children))
    assert nodes(m.b.one(root,'Animation'))==nodes(m.b.one(old_root,'Animation'))
    assert nodes(comp)==nodes(m.b.one(old_root,'Cmpnd'))
    assert len(surfaces)==4
    surf=bytearray(b'vers'+S.pack('<f',2))
    for name,hs in surfaces:surf.extend(m.old.surface_file([(name,hs)])[8:])
    for name,hs in surfaces:
        chunks=dict(dict(m.old.parts(bytes(surf)))[m.utf.crc(name)])
        assert b'!fxd' in chunks
        restored=m.old.leaves(chunks[b'surf'])
        if name!='Root':
            key=lambda h:(np.asarray(h.points,dtype='<f4').tobytes(),h.raw[16:])
            assert Counter(map(key,hs))==Counter(map(key,restored))
            assert len(restored)==7
    builder.emit(relative+'.cmp',raw);builder.emit(relative+'.sur',bytes(surf))
    report=dict(moving_hulls=21,stationary_anchor_metres=.02,stationary_visible_geometry=0,draw_groups=draws,period_seconds=p.PERIOD)
    (OUT/'manifest.json').write_text(json.dumps(dict(sources=builder.sources,payload=builder.payload,report=report),indent=2))
    print('PASS: all seven source pieces and collision leaves belong to each rotor;',report)


def install():
    manifest_path=OUT/'manifest.json';manifest=json.loads(manifest_path.read_text())
    digest=m.old.sha256(manifest_path.read_bytes()).hexdigest()
    for stamp in ('native_check.ok','animation_check.ok'):assert (OUT/stamp).read_text()==digest
    for name,h in manifest['sources'].items():assert m.old.sha256((m.GAME/name).read_bytes()).hexdigest()==h
    payload={n:(OUT/'stage'/n).read_bytes() for n in manifest['payload']}
    for name,raw in payload.items():assert m.old.sha256(raw).hexdigest()==manifest['payload'][name]
    before={name:(m.GAME/name).read_bytes() for name in payload}
    live=m.old.data_folder(m.GAME,m.GAME);backup=m.old.data_folder(m.GAME,OUT/'rollback')
    for name,raw in before.items():
        target=backup.data_path(name[5:])
        assert not target.exists(),'Revision already backed up; inspect before retry'
        backup.sync_data_file(name[5:],raw)
    touched=[]
    try:
        for name,raw in payload.items():
            assert (m.GAME/name).read_bytes()==before[name]
            touched.append(name);live.sync_data_file(name[5:],raw)
        for name,raw in payload.items():assert (m.GAME/name).read_bytes()==raw
    except Exception:
        for name in reversed(touched):live.sync_data_file(name[5:],before[name])
        raise
    installed_path=p.OUT/'installed.json';installed=json.loads(installed_path.read_text())
    installed['hashes'].update(manifest['payload']);installed['full_rotors']=str(OUT/'manifest.json')
    installed_path.write_text(json.dumps(installed,indent=2))
    stage=m.old.data_folder(m.GAME,OUT/'stage')
    for name in payload:stage.remove_data_file(name[5:])
    print('Installed and verified CMP/SUR; staging removed; only two old model files retained')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    install() if args.apply else build()
