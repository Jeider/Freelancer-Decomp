"""Stage/install the Leipzig mooring interior and matching client/server builds."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
from prepare import ROOT, DATA, GAME, OUT

STAGE=OUT/'install'
ASSETS=('INTERFACE/capital_interiors.ini','UNIVERSE/ROOM/RH/capital_deck.ini',
        'SCRIPTS/BASES/capital/rh_depot_mooring.thn')
FILES={
    'bin/freelancer.exe':ROOT/'src/obj/train_yard/freelancer/bin/freelancer.exe',
    'bin/freelancer.pdb':ROOT/'src/obj/train_yard/freelancer/bin/freelancer.pdb',
    'bin/Server.dll':ROOT/'src/obj/train_yard/Server/bin/Server.dll',
    'bin/Server.pdb':ROOT/'src/obj/train_yard/Server/bin/Server.pdb',
    **{'DATA/'+p:DATA/p for p in ASSETS},
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def main():
    if (Path(__file__).with_name('ARCHIVED')).exists():
        raise SystemExit('Capital interiors are archived; installation is disabled. See README.txt.')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if not args.apply:
        records={}
        for project in ('freelancer','Server'):
            tlog=ROOT/f'src/obj/train_yard/{project}/obj/{project}.tlog/CL.command.1.tlog'
            rows=tlog.read_text(encoding='utf-16').splitlines()
            commands=[rows[i+1] for i,line in enumerate(rows[:-1]) if line.startswith('^')]
            assert commands and all('FREELANCER_RPG_WORLD' in c for c in commands),project
        for name,source in FILES.items():
            target=STAGE/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,target)
            records[name]={'before':sha(GAME/name),'after':sha(target),'source':str(source)}
        deps={name:sha(GAME/'bin'/name) for name in ('Common.dll','Content.dll','Thorn.dll','DALib.dll','dacom.dll')}
        (STAGE/'manifest.json').write_text(json.dumps({'files':records,'dependencies':deps},indent=2))
        print('Staged',len(records),'files; RPG=1 client/server, Common/Content unchanged.')
        return
    manifest=json.loads((STAGE/'manifest.json').read_text())
    assert set(manifest['files'])==set(FILES)
    tasks=subprocess.check_output(['tasklist','/FO','CSV','/NH']).lower()
    assert not any(b'"'+name+b'"' in tasks for name in (
        b'freelancer.exe',b'freelancer_window.exe',b'freelancer_en.exe',
        b'freelancer_window_en.exe',b'flserver.exe')),'Close game before install'
    for name,record in manifest['files'].items():
        assert sha(GAME/name)==record['before'],'Changed game file: '+name
        assert sha(STAGE/name)==record['after']==sha(Path(record['source'])),'Changed build: '+name
    for name,digest in manifest['dependencies'].items():
        assert sha(GAME/'bin'/name)==digest,'Changed dependency: '+name
    backup=GAME/'BACKUP'/('codex_capital_interiors_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True)
    for name,record in manifest['files'].items():
        if record['before']:
            target=backup/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(GAME/name,target)
            assert sha(target)==record['before']
    shutil.copy2(STAGE/'manifest.json',backup/'manifest.json')
    changed=[]
    try:
        for name,record in manifest['files'].items():
            target=GAME/name
            assert sha(target)==record['before'],'Concurrent change: '+name
            target.parent.mkdir(parents=True,exist_ok=True)
            temporary=target.with_suffix(target.suffix+'.capital-install.tmp')
            shutil.copy2(STAGE/name,temporary)
            temporary.replace(target)
            changed.append(name)
            assert sha(target)==record['after']
    except BaseException:
        for name in reversed(changed):
            if manifest['files'][name]['before']:
                shutil.copy2(backup/name,GAME/name)
            else:
                # This is one explicitly listed file created by this install.
                (GAME/name).unlink()
        raise
    manifest['backup']=str(backup)
    (OUT/'installed.json').write_text(json.dumps(manifest,indent=2))
    print('Installed and SHA-256 verified. Backup:',backup)

if __name__=='__main__':
    main()
