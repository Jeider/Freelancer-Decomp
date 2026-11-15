"""Install checked solar rotor assets; no engine build or universe generation."""
import argparse
import json
import potsdam_panels as p
m=p.m


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    manifest_path=p.OUT/'manifest.json';manifest=json.loads(manifest_path.read_text())
    digest=m.old.sha256(manifest_path.read_bytes()).hexdigest()
    for stamp in ('native_check.ok','animation_check.ok'):
        assert (p.OUT/stamp).read_text()==digest,stamp
    for name,sha in manifest['sources'].items():assert m.old.sha256((m.GAME/name).read_bytes()).hexdigest()==sha,name
    payload={name:(p.OUT/'stage'/name).read_bytes() for name in manifest['payload']}
    for name,raw in payload.items():assert m.old.sha256(raw).hexdigest()==manifest['payload'][name]
    before={name:(m.GAME/name).read_bytes() if (m.GAME/name).exists() else None for name in payload}
    assert all(before[n] is None or n in manifest['sources'] for n in payload)
    aliases={p.p.TEMPLATE:p.p.TEMPLATE.replace('.py','StaticOriginal.py'),p.p.LIVE:p.p.LIVE.replace('.ini','PanelsOriginal.ini')}
    for name,alias in aliases.items():
        assert payload[alias]==before[name]
        old=before[name].decode('utf-8-sig');new=payload[name].decode('utf-8-sig')
        assert new.replace('archetype = '+p.NAME,'archetype = pdm_top')==old
    for name in ('DATA/SOLAR/solararch.ini','DATA/SOLAR/loadouts.ini',p.EQUIPMENT):assert payload[name].startswith(before[name])
    model=m.utf.read_tree(payload[f'DATA/SOLAR/OPTIMIZED/potsdam_mega/{p.NAME}.cmp'])[1][0]
    new_ids=set()
    for entry in m.b.one(model,'Cmpnd').children:
        file=m.b.one(entry,'File name')
        if file:
            ident=m.utf.crc(m.b.text(file.blob));assert ident not in new_ids;new_ids.add(ident)
    for folder in ('potsdam_mega','valensia_mega','terraform_mega'):
        for path in (m.GAME/'DATA/SOLAR/OPTIMIZED'/folder).glob('*.cmp'):
            root=m.utf.read_tree(path.read_bytes())[1][0]
            for entry in m.b.one(root,'Cmpnd').children:
                file=m.b.one(entry,'File name')
                if file:assert m.utf.crc(m.b.text(file.blob)) not in new_ids,path
    print('PASS: animated CMP + four native SUR bodies; existing content and unique part names verified',flush=True)
    if not args.apply:return
    rollback=p.OUT/'rollback';rollback.mkdir(parents=True,exist_ok=True)
    assert not (rollback/'transaction.json').exists(),'Already installed or interrupted'
    backup=m.old.data_folder(m.GAME,rollback);records={}
    for name,raw in before.items():
        if raw is None:records[name]=None;continue
        if name in aliases:source=m.GAME/aliases[name]
        else:
            source=rollback/name
            if name.startswith('DATA/'):backup.sync_data_file(name[5:],raw)
            else:source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(raw)
        records[name]={'source':str(source),'sha256':m.old.sha256(raw).hexdigest()}
    (rollback/'transaction.json').write_text(json.dumps(records,indent=2))
    live=m.old.data_folder(m.GAME,m.GAME)
    def write(name,raw):
        if name.startswith('DATA/'):
            if raw is None:live.remove_data_file(name[5:])
            else:live.sync_data_file(name[5:],raw)
        else:
            path=m.GAME/name
            if raw is None:path.unlink(missing_ok=True)
            else:path.write_bytes(raw)
    touched=[]
    try:
        for name,raw in payload.items():
            assert ((m.GAME/name).read_bytes() if (m.GAME/name).exists() else None)==before[name]
            touched.append(name);write(name,raw)
        for name,raw in payload.items():assert (m.GAME/name).read_bytes()==raw
    except Exception:
        for name in reversed(touched):write(name,before[name])
        raise
    (p.OUT/'installed.json').write_text(json.dumps(dict(hashes=manifest['payload'],rollback=str(rollback)),indent=2))
    stage=m.old.data_folder(m.GAME,p.OUT/'stage')
    for name in payload:
        if name.startswith('DATA/'):stage.remove_data_file(name[5:])
        else:(p.OUT/'stage'/name).unlink()
    print('Installed and byte-verified; stage removed; no engine binary or Pythonlancer generation touched')


if __name__=='__main__':main()
