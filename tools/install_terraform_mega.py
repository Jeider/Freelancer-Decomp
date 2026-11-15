"""Validate and install terraformer assets/source, without running Pythonlancer."""
import argparse
import ast
from collections import Counter
import json
import re
import terraform_mega as t

m=t.m


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    manifest_path=t.OUT/'manifest.json'
    manifest=json.loads(manifest_path.read_text())
    digest=m.old.sha256(manifest_path.read_bytes()).hexdigest()
    assert (t.OUT/'native_check.ok').read_text()==digest
    for name,sha in manifest['sources'].items():
        assert m.old.sha256((m.GAME/name).read_bytes()).hexdigest()==sha,'Changed input: '+name
    payload={name:(t.OUT/'stage'/name).read_bytes() for name in manifest['payload']}
    for name,raw in payload.items():assert m.old.sha256(raw).hexdigest()==manifest['payload'][name]
    before={name:(m.GAME/name).read_bytes() if (m.GAME/name).exists() else None for name in payload}
    assert all(before[n] is None or n in manifest['sources'] for n in payload)
    live=(m.GAME/t.LIVE).read_text(encoding='utf-8-sig')
    target=payload[t.LIVE].decode('utf-8').replace('\r\n','\n')
    def unaffected(text):
        return Counter(block for block in m.old.blocks(text) if not re.fullmatch(r'or_hq_terra_[123](?:_.*)?',m.old.one(m.old.fields(block),'nickname')))
    assert unaffected(live)==unaffected(target),'Unrelated system object changed'
    original_template=(m.GAME/t.TEMPLATE).read_text(encoding='utf-8-sig')
    new_template=payload[t.TEMPLATE].decode('utf-8').replace('\r\n','\n')
    assert new_template.startswith(original_template)
    ast.parse(new_template);ast.parse(payload[t.SYSTEM].decode('utf-8'))
    # Unique nested model filenames are essential: EngBase caches them globally.
    cmp_path=f'DATA/SOLAR/OPTIMIZED/terraform_mega/{t.NAME}.cmp'
    root=m.utf.read_tree(payload[cmp_path])[1][0]
    entries=m.b.one(root,'Cmpnd').children
    new_names=[m.b.text(m.b.one(n,'File name').blob) for n in entries if m.b.one(n,'File name')]
    new_crcs=[m.utf.crc(n) for n in new_names]
    assert len(set(new_crcs))==len(new_crcs)
    for path in (m.GAME/'DATA/SOLAR/OPTIMIZED/valensia_mega').glob('*.cmp'):
        tree=m.utf.read_tree(path.read_bytes())[1][0]
        for node in m.b.one(tree,'Cmpnd').children:
            file=m.b.one(node,'File name')
            if file:assert m.utf.crc(m.b.text(file.blob)) not in new_crcs
    library=m.b.one(root,'VMeshLibrary')
    ids=[m.utf.crc(n.name) for n in library.children]
    assert len(ids)==len(set(ids)), 'Duplicate mesh library entry'
    report=dict(manifest_sha256=digest,checks=['native SUR loader','exact source triangles and LODs',
        'exact collision leaf topology','unchanged rotating carriers','unchanged unrelated objects',
        'preserved template classes','Python syntax','unique nested filenames and mesh IDs'])
    (t.OUT/'checks.json').write_text(json.dumps(report,indent=2))
    aliases={t.LIVE:t.LIVE.replace('.ini','TerraformOriginal.ini'),t.TEMPLATE:t.TEMPLATE.replace('.py','Original.py')}
    backup_bytes=sum(len(raw) for name,raw in before.items() if raw is not None and name not in aliases)
    print('PASS: installation checks; files:',len(payload),'single rollback MiB:',round(backup_bytes/1048576,2),flush=True)
    if not args.apply:return
    rollback=t.OUT/'rollback';rollback.mkdir(parents=True,exist_ok=True)
    assert not (rollback/'transaction.json').exists(),'Already installed or interrupted: inspect rollback'
    backup=m.old.data_folder(m.GAME,rollback)
    records={}
    for name,raw in before.items():
        if raw is None:records[name]=None;continue
        if name in aliases:
            assert payload[aliases[name]]==raw
            source=m.GAME/aliases[name]
        else:
            source=rollback/name
            if name.startswith('DATA/'):backup.sync_data_file(name[5:],raw)
            else:source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(raw)
        records[name]={'source':str(source),'sha256':m.old.sha256(raw).hexdigest()}
    (rollback/'transaction.json').write_text(json.dumps(records,indent=2))
    live_folder=m.old.data_folder(m.GAME,m.GAME)
    def write(name,raw):
        if name.startswith('DATA/'):
            if raw is None:live_folder.remove_data_file(name[5:])
            else:live_folder.sync_data_file(name[5:],raw)
        else:
            path=m.GAME/name
            if raw is None:path.unlink(missing_ok=True)
            else:path.write_bytes(raw)
    touched=[]
    try:
        for name,raw in payload.items():
            current=(m.GAME/name).read_bytes() if (m.GAME/name).exists() else None
            assert current==before[name],'Concurrent edit: '+name
            touched.append(name);write(name,raw)
        for name,raw in payload.items():assert (m.GAME/name).read_bytes()==raw
    except Exception:
        for name in reversed(touched):write(name,before[name])
        raise
    (t.OUT/'installed.json').write_text(json.dumps(dict(hashes=manifest['payload'],rollback=str(rollback)),indent=2))
    stage=m.old.data_folder(m.GAME,t.OUT/'stage')
    for name in payload:
        if name.startswith('DATA/'):stage.remove_data_file(name[5:])
        else:(t.OUT/'stage'/name).unlink()
    print('Installed and verified; staged payload removed. Pythonlancer generation was not run.')


if __name__=='__main__':main()
