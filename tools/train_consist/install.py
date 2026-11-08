"""Install the player-only train and new save, with guarded backups and rollback."""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
from player import GEN, PLAYER_TEMPLATE, TEMPLATES, SAVE_FILE,OUT as STAGE

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/games/FL_MOD')
OUT=ROOT/'out/train_consist'
BIN=ROOT/'src/obj/train_consist'
MODEL='DATA/SHIPS/UTILITY/FREIGHT_TRAIN/'
PLAYER_FILES={'bin/Common.dll','bin/Common.pdb','DATA/SHIPS/shiparch.ini','DATA/SHIPS/shiparch2.ini',
              GEN+'templates/'+PLAYER_TEMPLATE,SAVE_FILE}
PLAYER_FILES.update(GEN+'templates/'+name for name in TEMPLATES)
PLAYER_FILES.update(MODEL+name for name in ['train_consist.cmp','train_consist.sur'])
PREVIOUS_PLAYER_FILES=(PLAYER_FILES-{MODEL+'train_consist.cmp',MODEL+'train_consist.sur',SAVE_FILE})|{'SAVE/Accts/SinglePlayer/biz_le2_train.fl'}
LEGACY_FILES={'bin/Common.dll','bin/Common.pdb',MODEL+'train_consist.cmp',MODEL+'train_consist.sur',
              'DATA/SHIPS/shiparch.ini'}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def replace(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(prefix='train_',suffix='.tmp',dir=target.parent)
    os.close(fd)
    try:
        shutil.copy2(source,name)
        os.replace(name,target)
    finally:
        if Path(name).exists():Path(name).unlink()


def idle():
    listing=subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True,errors='replace').lower()
    if '"freelancer.exe"' in listing or '"flserver.exe"' in listing:
        raise RuntimeError('Close Freelancer/flserver before installing or restoring Common.dll')


def restore(backup):
    backup=backup.resolve()
    assert backup.is_relative_to((GAME/'BACKUP').resolve()),'Backup must be inside game/BACKUP'
    records=json.loads((backup/'manifest.json').read_text())
    from tune import FILES as TUNE_FILES
    from camera import FILES as CAMERA_FILES
    from yard_update import RUNTIME,CONFIGS,SAVE
    from smooth_hud import FILES as SMOOTH_FILES
    yard_update_files=set(RUNTIME)|set(CONFIGS)|{SAVE}
    assert set(records) in (PLAYER_FILES,PREVIOUS_PLAYER_FILES,LEGACY_FILES,TUNE_FILES,CAMERA_FILES,yard_update_files,SMOOTH_FILES,{'bin/Common.dll','bin/Common.pdb'}),'Unexpected backup file list'
    for name,r in records.items():
        assert sha(GAME/name)==r['installed'],'File edited after installation: '+name
        if r['original'] is not None:assert sha(backup/name)==r['original'],'Backup changed: '+name
    idle()
    for name,r in records.items():
        if r['original'] is None:(GAME/name).unlink()
        else:replace(backup/name,GAME/name)
    print('Restored',backup)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--player',action='store_true',help='Player-only installation (also the default)')
    parser.add_argument('--tune',action='store_true',help='Install verified upright physics and camera/LOD update')
    parser.add_argument('--camera',action='store_true',help='Install only player camera INIs and its private cockpit')
    parser.add_argument('--strafe',action='store_true',help='Install only player train strafe INIs and generator sources')
    parser.add_argument('--parking',action='store_true',help='Install only Common runtime for fixed uncoupled wagons')
    parser.add_argument('--coupling',action='store_true',help='Install only Common runtime for automatic coupling alignment')
    parser.add_argument('--finalization',action='store_true',help='Install only Common runtime for smooth coupling completion')
    parser.add_argument('--lane',action='store_true',help='Install only Common runtime for gradual tradelane straightening')
    parser.add_argument('--smooth-hud',action='store_true',help='Install smooth coupling, Beta icon and capital maneuver flags')
    parser.add_argument('--yard-update',action='store_true',help='Install wider coupling, tail turret and adjusted yard save')
    parser.add_argument('--restore',type=Path)
    args=parser.parse_args()
    if args.restore:
        if not args.apply:parser.error('--restore requires --apply')
        restore(args.restore);return
    if args.strafe:
        from strafe import install
        install(args.apply);return
    if args.parking:
        from parking import install
        install(args.apply);return
    if args.coupling:
        from parking import install
        install(args.apply,'coupling');return
    if args.finalization:
        from parking import install
        install(args.apply,'finalization');return
    if args.lane:
        from parking import install
        install(args.apply,'lane');return
    if args.smooth_hud:
        from smooth_hud import install
        install(args.apply);return
    if args.yard_update:
        from yard_update import install
        install(args.apply);return
    if args.camera:
        from camera import install
        install(args.apply);return
    if args.tune:
        from tune import install
        install(args.apply);return
    manifest=json.loads((STAGE/'manifest.json').read_text())
    checked=json.loads((STAGE/'checked.json').read_text())
    assert sha(STAGE/'manifest.json')==checked['manifest'],'Player manifest changed since checks'
    records=manifest['files']
    assert set(records)==PLAYER_FILES and set(checked['files'])==PLAYER_FILES,'Unexpected install list'
    files={name:STAGE/name for name in records}
    for name,r in records.items():
        assert sha(files[name])==r['installed']==checked['files'][name],'Staged file changed: '+name
        assert sha(GAME/name)==r['original'],'Target changed since staging: '+name
    for name,digest in manifest['dependencies'].items():
        path=(GAME/name).resolve()
        assert path.is_relative_to(GAME.resolve()),'Dependency outside game'
        assert sha(path)==digest,'Installed dependency changed: '+name
    build=json.loads((BIN/'build.json').read_text());data=json.loads((OUT/'data.json').read_text())
    native=json.loads((BIN/'check.json').read_text())
    for name,digest in native.items():assert sha(Path(name))==digest,'Native checked artifact changed: '+name
    for name in ['train_consist.cmp','train_consist.sur']:
        assert sha(OUT/name)==data['files'][name],name+' differs from prepared data'
        assert sha(files[MODEL+name])==data['files'][name],'Staged model differs from checked model'
    assert sha(BIN/'Common.dll')==sha(files['bin/Common.dll'])==build['dll'],'DLL differs from checked build'
    assert sha(BIN/'Common.pdb')==sha(files['bin/Common.pdb']),'PDB differs from build'
    for name,digest in data['source_models'].items():assert sha(Path(name))==digest,'Source model changed'
    print(json.dumps(records,indent=2))
    if not args.apply:
        print('Validated; use --apply to install.');return
    idle()
    backup=GAME/'BACKUP'/('codex_train_player_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True)
    for name,r in records.items():
        if r['original'] is not None:
            (backup/name).parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(GAME/name,backup/name)
            assert sha(backup/name)==r['original']
    (backup/'manifest.json').write_text(json.dumps(records,indent=2))
    changed=[]
    try:
        for name,source in files.items():
            assert sha(GAME/name)==records[name]['original'],'Concurrent target change: '+name
            replace(source,GAME/name);changed.append(name)
            assert sha(GAME/name)==records[name]['installed']
    except BaseException:
        for name in reversed(changed):
            if records[name]['original'] is None:(GAME/name).unlink()
            else:replace(backup/name,GAME/name)
        raise
    (STAGE/'installed.json').write_text(json.dumps({'backup':str(backup),'files':records,'save':manifest['save']},indent=2))
    print('Installed. Backup:',backup)


if __name__=='__main__':main()
