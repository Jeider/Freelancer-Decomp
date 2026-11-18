"""Install validated ForbesMegafactory compounds and template; never generate the universe."""
import argparse
import json
import station_batch_model as p
from check_valensia_mega import templates

m=p.m


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    manifest_path=p.OUT/'manifest.json';manifest=json.loads(manifest_path.read_text())
    digest=m.old.sha256(manifest_path.read_bytes()).hexdigest()
    assert (p.OUT/'native_check.ok').read_text()==digest
    assert (p.OUT/'physics_check.ok').read_text()==digest
    if p.CONFIG.get('docks'):assert (p.OUT/'dock_animation.ok').read_text()==digest
    if p.CONFIG.get('panel_rotors'):assert (p.OUT/'panel_animation.ok').read_text()==digest
    for name,sha in manifest['sources'].items():
        assert m.old.sha256((m.GAME/name).read_bytes()).hexdigest()==sha,'Changed source: '+name
    payload={name:(p.OUT/'stage'/name).read_bytes() for name in manifest['payload']}
    for name,raw in payload.items():assert m.old.sha256(raw).hexdigest()==manifest['payload'][name]
    before={name:(m.GAME/name).read_bytes() if (m.GAME/name).exists() else None for name in payload}
    assert all(before[n] is None or n in manifest['sources'] for n in payload)
    aliases={inst['path']:inst['path'].replace('.ini',p.CLASS+'Original.ini') for inst in p.CONFIG['instances'] if inst['path'].replace('.ini',p.CLASS+'Original.ini') in payload}
    template_alias=p.TEMPLATE.replace('.ini',p.CLASS+'Original.ini') if p.CONFIG.get('static') else p.TEMPLATE.replace('.py','Original.py')
    if template_alias in payload:aliases[p.TEMPLATE]=template_alias
    for name,alias in aliases.items():assert payload[alias]==before[name]
    if p.CONFIG.get('static'):
        from sync_story_dev import split_dev,generator_static,semantic
        assert split_dev(before[p.TEMPLATE])[1]==split_dev(payload[p.TEMPLATE])[1]
        assert semantic(generator_static(payload[p.TEMPLATE]))==semantic(payload[p.LIVE].decode('utf-8-sig'))
        updated={p.CLASS:p.source_text(payload[p.TEMPLATE].decode('utf-8-sig'))}
    else:
        old=templates(before[p.TEMPLATE].decode('utf-8-sig'))[p.CLASS+'Original' if p.CONFIG.get('rebuild') else p.CLASS]
        updated=templates(payload[p.TEMPLATE].decode('utf-8-sig'))
        assert updated[p.CLASS+'Original']==old
    template_rows=m.b.placements_from_template(updated[p.CLASS])
    for inst in p.CONFIG['instances']:
        live_rows={r.name:r for r in m.b.placements_from_template(payload[inst['path']].decode('utf-8-sig'))}
        assert len(template_rows)==manifest['after']
        for row in template_rows:
            live=live_rows[row.name.replace(p.SOURCE_PREFIX,inst['prefix'])]
            assert (row.archetype,row.rotate,row.loadout)==(live.archetype,live.rotate,live.loadout)
            assert all(abs(a+b-c)<.0001 for a,b,c in zip(row.pos,inst['offset'],live.pos)),row.name
    for name,text in ({} if p.CONFIG.get('static') else templates(before[p.TEMPLATE].decode('utf-8-sig'))).items():
        if name!=p.CLASS:assert updated[name]==text,name+' unexpectedly changed'
    for name in ('DATA/SOLAR/solararch.ini','DATA/SOLAR/loadouts.ini'):
        if p.CONFIG.get('rebuild'):
            import re
            pattern=r'(?ms)^'+re.escape(p.MARK)+r'\r?\n.*?^; END '+re.escape(p.TASK.upper())+r'\r?\n'
            assert re.sub(pattern,'',payload[name].decode('utf-8-sig')).rstrip()==re.sub(pattern,'',before[name].decode('utf-8-sig')).rstrip(),name+' unrelated definitions changed'
        else:assert payload[name].startswith(before[name]),name+' changed existing definitions'
    # Check global nested-file CRC uniqueness against prior optimized stations.
    seen={}
    folders=['valensia_mega','terraform_mega','potsdam_mega','ulster_megabase','ulster_shortbase','ulster_shortsplit','stuttgart_mega','forbes_mega']
    folders += [path.name for path in (m.GAME/'DATA/SOLAR/OPTIMIZED').glob('batch_*') if path.is_dir() and not (p.CONFIG.get('rebuild') and path.name==p.TASK)]
    paths=[path for folder in folders for path in (m.GAME/'DATA/SOLAR/OPTIMIZED'/folder).glob('*.cmp')]
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
    rollback=m.REPO/'out/stations/station_batch/rollback';rollback.mkdir(parents=True,exist_ok=True)
    transaction=rollback/'transaction.json'
    records=json.loads(transaction.read_text()) if transaction.exists() else {}
    previous_records=dict(records)
    backup=m.old.data_folder(m.GAME,rollback)
    for name,raw in before.items():
        if name in records:continue
        if raw is None:records[name]=None;continue
        if name in aliases:source=m.GAME/aliases[name]
        else:
            source=rollback/name
            if name.startswith('DATA/'):backup.sync_data_file(name[5:],raw)
            else:source.parent.mkdir(parents=True,exist_ok=True);source.write_bytes(raw)
        records[name]={'source':str(source),'sha256':m.old.sha256(raw).hexdigest()}
    transaction.write_text(json.dumps(records,indent=2))
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
        transaction.write_text(json.dumps(previous_records,indent=2))
        raise
    (p.OUT/'installed.json').write_text(json.dumps(dict(hashes=manifest['payload'],rollback=str(rollback)),indent=2))
    stage=m.old.data_folder(m.GAME,p.OUT/'stage')
    for name in payload:
        if name.startswith('DATA/'):stage.remove_data_file(name[5:])
        else:(p.OUT/'stage'/name).unlink()
    for path in (p.OUT/'stage/DATA').rglob('*'):
        if path.is_file():stage.remove_data_file(path.relative_to(p.OUT/'stage/DATA').as_posix())
    print('Installed, verified and removed temporary payload. Pythonlancer generation not run.')


if __name__=='__main__':main()
