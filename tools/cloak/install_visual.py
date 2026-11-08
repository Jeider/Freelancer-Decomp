"""Stage and install the isolated cloak renderer with hash guards and rollback."""
import argparse
from datetime import datetime
import json
from pathlib import Path
import shutil
import subprocess
from build_visual import ROOT,OUT,digest

GAME=Path('D:/games/FL_MOD')
PAYLOAD=('bin/freelancer.exe','bin/freelancer.pdb','DATA_EXTRA/SHADERS/cloak_refraction.hlsl')


def current(path):
    return digest(path) if path.exists() else None


def stage():
    build=json.loads((OUT/'build.json').read_text())
    assert digest(GAME/PAYLOAD[0])==build['baseline_client'],'Installed client changed'
    assert digest(OUT/'freelancer.exe')==build['client']
    assert all(digest(ROOT/p)==h for p,h in build['sources'].items()),'Sources changed since build'
    manifest={}
    for relative in PAYLOAD:
        source=OUT/Path(relative).name if relative.startswith('bin/') else ROOT/relative
        target=OUT/'staged'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,target)
        manifest[relative]={'before':current(GAME/relative),'after':digest(target)}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Staged client, symbols and cloak shader; installed baseline and source hashes verified')


def apply():
    manifest=json.loads((OUT/'manifest.json').read_text());assert tuple(manifest)==PAYLOAD
    processes=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    for name in (b'freelancer.exe',b'freelancer_window.exe',b'freelancer_en.exe',b'freelancer_window_en.exe',b'flserver.exe'):
        assert b'"'+name+b'"' not in processes,'Close Freelancer/FLServer before installation'
    for relative,item in manifest.items():
        assert current(GAME/relative)==item['before'],relative+' changed since staging'
        assert digest(OUT/'staged'/relative)==item['after']
    backup=OUT/('backup_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True)
    for relative,item in manifest.items():
        if item['before'] is not None:
            saved=backup/relative;saved.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/relative,saved)
            assert digest(saved)==item['before']
    shutil.copy2(OUT/'manifest.json',backup/'manifest.json')
    touched=[]
    try:
        for relative,item in manifest.items():
            target=GAME/relative;target.parent.mkdir(parents=True,exist_ok=True);touched.append(relative)
            shutil.copy2(OUT/'staged'/relative,target);assert digest(target)==item['after']
    except Exception:
        for relative in reversed(touched):
            if manifest[relative]['before'] is None:(GAME/relative).unlink(missing_ok=True)
            else:shutil.copy2(backup/relative,GAME/relative)
        raise
    print('Installed and hash-verified:',', '.join(PAYLOAD),'Backup:',backup)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    apply() if parser.parse_args().apply else stage()
