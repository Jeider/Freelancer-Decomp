"""Stage/apply the native DLSS strength control to the existing base-neural installation."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/base_neural'
PACKAGE=OUT/'slider'
PAYLOAD=PACKAGE/'payload'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def stage():
    sys.path.insert(0,str(ROOT))
    from tools.targeting_hud import stage_interface_strings as strings
    strings.STAGE=PAYLOAD
    strings.main()
    verified=json.loads((OUT/'checks/strength/verified.json').read_text())
    assert sha(OUT/'on/bin/fl_base_neural.addon32')==verified['addon_sha256'],'GPU-tested addon changed'
    rows=[]
    for row in json.loads((PACKAGE/'strings_manifest.json').read_text()):
        if row['original'].lower()!=row['prepared'].lower():
            rows.append({'relative':row['relative'],'before':row['original'].lower(),'after':row['prepared'].lower()})
    for name in ('freelancer.exe','fl_base_neural.addon32'):
        source=OUT/'on/bin'/name;relative='bin/'+name
        (PAYLOAD/relative).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(source,PAYLOAD/relative)
        rows.append({'relative':relative,'before':sha(GAME/relative),'after':sha(PAYLOAD/relative)})
    # Preserve concurrent engine installations and the current maximum profile.
    guards={name:sha(GAME/name) for name in ('bin/RP9.dll','bin/Common.dll','bin/Content.dll','bin/Server.dll',
            'bin/port.ini','bin/ReShade.ini','bin/neural/host64/ReShade.ini')}
    (PACKAGE/'manifest.json').write_text(json.dumps({'files':rows,'guards':guards},indent=2))
    print('Prepared native strength slider:',len(rows),'files; existing engine/configuration hashes recorded')

def apply():
    processes=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True,errors='replace').lower()
    assert '"freelancer.exe"' not in processes,'Close Freelancer before installing'
    manifest=json.loads((PACKAGE/'manifest.json').read_text())
    for name,digest in manifest['guards'].items():assert sha(GAME/name)==digest,'Concurrent change: '+name
    for row in manifest['files']:
        name=row['relative']
        assert sha(GAME/name)==row['before'],'Concurrent change: '+name
        assert sha(PAYLOAD/name)==row['after'],'Package changed: '+name
    backup=OUT/'backups'/(PACKAGE.name+'_'+datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True)
    for row in manifest['files']:
        name=row['relative'];(backup/name).parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(GAME/name,backup/name)
    (backup/'manifest.json').write_text(json.dumps(manifest,indent=2))
    touched=[]
    try:
        # Binaries first: mapped files fail before resource/config updates.
        for row in sorted(manifest['files'],key=lambda r:0 if r['relative'].startswith('bin/') else 1):
            name=row['relative'];touched.append(name)
            shutil.copy2(PAYLOAD/name,GAME/name)
            assert sha(GAME/name)==row['after']
    except Exception:
        for name in reversed(touched):
            if sha(GAME/name)!=sha(backup/name):shutil.copy2(backup/name,GAME/name)
        raise
    print('Installed base-neural update:',PACKAGE.name,'; verified files:',len(manifest['files']),'; backup:',backup)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stage',action='store_true');mode.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    if args.stage:stage()
    else:apply()
