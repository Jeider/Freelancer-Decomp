"""Install validated Potsdam compounds and template; never generate the universe."""
import argparse
import json
import potsdam_mega as p
from check_valensia_mega import templates

m=p.m


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    manifest_path=p.OUT/'manifest.json';manifest=json.loads(manifest_path.read_text())
    digest=m.old.sha256(manifest_path.read_bytes()).hexdigest()
    assert (p.OUT/'native_check.ok').read_text()==digest
    for name,sha in manifest['sources'].items():
        assert m.old.sha256((m.GAME/name).read_bytes()).hexdigest()==sha,'Changed source: '+name
    payload={name:(p.OUT/'stage'/name).read_bytes() for name in manifest['payload']}
    for name,raw in payload.items():assert m.old.sha256(raw).hexdigest()==manifest['payload'][name]
    before={name:(m.GAME/name).read_bytes() if (m.GAME/name).exists() else None for name in payload}
    assert all(before[n] is None or n in manifest['sources'] for n in payload)
    aliases={p.LIVE:p.LIVE.replace('.ini','PotsdamOriginal.ini'),p.TEMPLATE:p.TEMPLATE.replace('.py','Original.py')}
    for name,alias in aliases.items():assert payload[alias]==before[name]
    old=templates(before[p.TEMPLATE].decode('utf-8-sig'))['Potsdam']
    updated=templates(payload[p.TEMPLATE].decode('utf-8-sig'))
    assert updated['PotsdamOriginal']==old
    for name in ('DATA/SOLAR/solararch.ini','DATA/SOLAR/loadouts.ini'):
        assert payload[name].startswith(before[name]),name+' changed existing definitions'
    # Check global nested-file CRC uniqueness against prior optimized stations.
    seen={}
    paths=list((m.GAME/'DATA/SOLAR/OPTIMIZED/valensia_mega').glob('*.cmp'))+list((m.GAME/'DATA/SOLAR/OPTIMIZED/terraform_mega').glob('*.cmp'))
    models={str(path):path.read_bytes() for path in paths}
    models.update({name:raw for name,raw in payload.items() if name.endswith('.cmp')})
    for name,raw in models.items():
        tree=m.utf.read_tree(raw)[1][0]
        for entry in m.b.one(tree,'Cmpnd').children:
            file=m.b.one(entry,'File name')
            if not file:continue
            crc=m.utf.crc(m.b.text(file.blob));assert crc not in seen,(name,seen.get(crc));seen[crc]=name
        ids=[m.utf.crc(n.name) for n in m.b.one(tree,'VMeshLibrary').children]
        assert len(ids)==len(set(ids))
    (p.OUT/'checks.json').write_text(json.dumps(dict(manifest_sha256=digest,native_sur=True,unique_nested_names=True,
        exact_geometry=True,original_template=True,original_definitions=True),indent=2))
    size=sum(len(raw) for name,raw in before.items() if raw is not None and name not in aliases)
    print('PASS: install validation;',len(payload),'files; one rollback set',round(size/1048576,2),'MiB',flush=True)
    if not args.apply:return
    rollback=p.OUT/'rollback';rollback.mkdir(parents=True,exist_ok=True)
    assert not (rollback/'transaction.json').exists(),'Already installed or interrupted; inspect rollback'
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
    print('Installed, verified and removed temporary payload. Pythonlancer generation not run.')


if __name__=='__main__':main()
