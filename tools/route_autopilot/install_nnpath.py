"""Install the checked NNPath client EXE/PDB, preserving the runtime DLLs."""
from pathlib import Path
from datetime import datetime
import argparse
import json
import shutil
import subprocess
from build_nnpath import ROOT,OUT,GAME,digest


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    manifest=json.loads((OUT/'manifest.json').read_text())
    assert set(manifest['files'])=={'freelancer.exe','freelancer.pdb'}
    assert digest(ROOT/'src/freelancer/Client/player_route.cpp')==manifest['source'],'Source changed after build'
    for name,r in manifest['files'].items():
        assert digest(GAME/'bin'/name)==r['before'],'Installed file changed: '+name
        assert digest(OUT/name)==r['after'],'Build changed: '+name
    for name,h in manifest['dependencies'].items():
        assert digest(GAME/'bin'/name)==h,'Runtime dependency changed: '+name
    if not args.apply:
        print('Ready: NNPath snapshot client EXE/PDB; Common/Server/Content and mission INIs preserved.')
        return
    processes=subprocess.check_output(['tasklist','/FO','CSV','/NH']).lower()
    names=('freelancer.exe','freelancer_window.exe','freelancer_en.exe','freelancer_window_en.exe','flserver.exe')
    assert not any(('"'+name+'"').encode() in processes for name in names),'Close game before installing'
    backup=GAME/'BACKUP'/('codex_nnpath_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True)
    for name,r in manifest['files'].items():
        shutil.copy2(GAME/'bin'/name,backup/name)
        assert digest(backup/name)==r['before']
    shutil.copy2(OUT/'manifest.json',backup/'manifest.json')
    changed=[]
    try:
        for name,r in manifest['files'].items():
            target=GAME/'bin'/name
            assert digest(target)==r['before'],'Concurrent change: '+name
            temporary=target.with_suffix(target.suffix+'.nnpath-install.tmp')
            shutil.copy2(OUT/name,temporary)
            temporary.replace(target);changed.append(name)
            assert digest(target)==r['after']
    except BaseException:
        for name in reversed(changed):shutil.copy2(backup/name,GAME/'bin'/name)
        raise
    manifest['backup']=str(backup)
    (OUT/'installed.json').write_text(json.dumps(manifest,indent=2))
    print('Installed and SHA-256 verified. Backup:',backup)


if __name__=='__main__':main()
