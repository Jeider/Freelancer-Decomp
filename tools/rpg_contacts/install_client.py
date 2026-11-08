"""Stage/install only the RPG-enabled client EXE and its matching PDB."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
BUILD=ROOT/'src/obj/rpg_contacts/build_Release_1_client'
OUT=ROOT/'src/obj/rpg_contacts/client_install'
GAME=Path('D:/games/FL_MOD')
FILES=('bin/freelancer.exe','bin/freelancer.pdb')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if not args.apply:
        commands=(BUILD/'obj/freelancer.tlog/CL.command.1.tlog').read_text(encoding='utf-16')
        rows=commands.splitlines()
        compiled=[rows[i+1] for i,r in enumerate(rows[:-1]) if r.startswith('^')]
        assert compiled and all('FREELANCER_RPG_WORLD' in r for r in compiled),'Client build lacks RPG flag'
        assert (BUILD/'bin/freelancer.exe').is_file()
        records={}
        for name in FILES:
            source=BUILD/name;target=OUT/name
            target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            records[name]={'before':sha(GAME/name),'after':sha(target),'build':str(source)}
        # Preserve installed runtime dependencies, including the separately checked train.
        dependencies={name:sha(GAME/'bin'/name) for name in ('Common.dll','Content.dll')}
        (OUT/'manifest.json').write_text(json.dumps({'files':records,'dependencies':dependencies,
            'FreelancerRpgWorld':1},indent=2))
        print('Staged RPG=1 client EXE/PDB; Common and Content preserved.')
        return
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert set(manifest['files'])==set(FILES) and manifest['FreelancerRpgWorld']==1
    processes=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+p+b'"' in processes for p in (b'freelancer.exe',b'freelancer_window.exe',b'freelancer_en.exe',b'freelancer_window_en.exe',b'flserver.exe')),'Close game before installing'
    for name,r in manifest['files'].items():
        assert sha(GAME/name)==r['before'] and sha(OUT/name)==r['after']==sha(Path(r['build'])),name
    for name,h in manifest['dependencies'].items():assert sha(GAME/'bin'/name)==h,name
    backup=GAME/'BACKUP'/('codex_rpg_client_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for name,r in manifest['files'].items():
        target=backup/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(GAME/name,target);assert sha(target)==r['before']
    shutil.copy2(OUT/'manifest.json',backup/'manifest.json')
    changed=[]
    try:
        for name,r in manifest['files'].items():
            assert sha(GAME/name)==r['before'],'Concurrent file change: '+name
            temp=(GAME/name).with_suffix('.rpg-install.tmp')
            shutil.copy2(OUT/name,temp);temp.replace(GAME/name);changed.append(name)
            assert sha(GAME/name)==r['after']
    except BaseException:
        for name in reversed(changed):shutil.copy2(backup/name,GAME/name)
        raise
    manifest['backup']=str(backup)
    (OUT/'installed.json').write_text(json.dumps(manifest,indent=2))
    print('Installed and verified RPG=1 client. Backup:',backup)
if __name__=='__main__':main()
