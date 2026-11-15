"""Install checked mega models and Common.dll, with one minimal rollback set."""
import argparse
import json
from pathlib import Path
import subprocess
import valensia_mega as m


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    manifest=json.loads((m.OUT/'manifest.json').read_text())
    digest=m.old.sha256((m.OUT/'manifest.json').read_bytes()).hexdigest()
    assert json.loads((m.OUT/'checks.json').read_text())['manifest_sha256']==digest
    assert (m.OUT/'native_check.ok').read_text()==digest
    log=(m.OUT/'avoidance_check/result.log').read_text()
    assert 'PASS: hollow ring' in log and 'nomad_lair_beta_towerless.sur: interior clear=' in log
    for name,sha in manifest['sources'].items():
        assert m.old.sha256((m.GAME/name).read_bytes()).hexdigest()==sha,'Changed source: '+name
    contents={}
    for name,sha in manifest['payload'].items():
        raw=(m.OUT/'stage'/name).read_bytes()
        assert m.old.sha256(raw).hexdigest()==sha,name
        contents[name]=raw
    binary=m.REPO/'src/obj/train_courier/rpg1/bin'
    for name in ('Common.dll','Common.pdb'):
        source=binary/name
        assert source.stat().st_mtime>=max((m.REPO/f'src/Common/{p}').stat().st_mtime for p in
            ('common_obstacleavoidance.cpp','solar_avoidance.inl','solar_avoidance_geometry.h'))
        contents['bin/'+name]=source.read_bytes()
    before={name:(m.GAME/name).read_bytes() if (m.GAME/name).exists() else None for name in contents}
    changed={name:raw for name,raw in contents.items() if before[name]!=raw}
    for name in changed:
        assert name.startswith('DATA/') or name in ('bin/Common.dll','bin/Common.pdb',m.old.TEMPLATE,
            m.old.TEMPLATE.replace('.py','PairsOriginal.py'))
        assert name in manifest['sources'] or name.startswith('bin/') or before[name] is None,'Unexpected existing output: '+name
    aliases={m.old.TEMPLATE:m.old.TEMPLATE.replace('.py','PairsOriginal.py'),
             'DATA/'+m.old.LIVE:'DATA/'+m.old.LIVE.replace('.ini','PairsOriginal.ini')}
    backup_bytes=sum(len(before[n]) for n in changed if before[n] is not None and n not in aliases)
    print('Changed files:',len(changed),'single rollback MiB:',round(backup_bytes/1048576,2))
    if not args.apply:return
    for process in ('freelancer.exe','flserver.exe'):
        result=subprocess.run(['tasklist','/FI','IMAGENAME eq '+process,'/FO','CSV','/NH'],capture_output=True)
        assert process.encode() not in result.stdout.lower(),'Close '+process+' before replacing Common.dll'
    backup=m.OUT/'rollback'
    backup.mkdir(parents=True,exist_ok=True)
    # One rollback set for this revision, not a timestamped full tree per run.
    assert not (backup/'transaction.json').exists(),'Rollback already exists: review before replacing it'
    save,live=m.old.data_folder(m.GAME,backup),m.old.data_folder(m.GAME,m.GAME)
    records={}
    for name in changed:
        raw=before[name]
        if raw is None:records[name]=None;continue
        if name in aliases:
            assert contents[aliases[name]]==raw
            records[name]={'source':str(m.GAME/aliases[name]),'sha256':m.old.sha256(raw).hexdigest()}
            continue
        if name.startswith('DATA/'):save.sync_data_file(name[5:],raw)
        else:
            path=backup/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        records[name]={'source':str(backup/name),'sha256':m.old.sha256(raw).hexdigest()}
    (backup/'transaction.json').write_text(json.dumps(records,indent=2))
    touched=[]
    def write(name,raw):
        if name.startswith('DATA/'):
            if raw is None:live.remove_data_file(name[5:])
            else:live.sync_data_file(name[5:],raw)
        elif raw is None:(m.GAME/name).unlink(missing_ok=True)
        else:(m.GAME/name).write_bytes(raw)
    try:
        # Replace the DLL first so a sharing violation cannot leave new data with old AI.
        for name in sorted(changed,key=lambda n:(not n.startswith('bin/'),n)):
            touched.append(name);write(name,changed[name])
        for name,raw in contents.items():assert (m.GAME/name).read_bytes()==raw,name
    except Exception:
        for name in reversed(touched):
            existing=(m.GAME/name).read_bytes() if (m.GAME/name).exists() else None
            if existing!=before[name]:write(name,before[name])
        raise
    (m.OUT/'installed.json').write_text(json.dumps(dict(files=len(changed),rollback=str(backup),
        hashes={n:m.old.sha256(raw).hexdigest() for n,raw in contents.items()}),indent=2))
    print('Installed and verified. One rollback set:',backup)


if __name__=='__main__':main()
