"""Prepare/install native subtitles and volume beams, with verified backup/rollback."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT/'src/obj/native_visuals/install'
PAYLOAD = ('bin/freelancer.exe','bin/freelancer.pdb','bin/alchemy.dll','bin/alchemy.pdb',
           'bin/RP9.dll','bin/RP9.pdb','DATA_EXTRA/SHADERS/beam_volume.hlsl')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root',type=Path,default=Path('D:/games/FL_MOD'))
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    game=args.game_root.resolve(strict=True)
    if not args.apply:
        items=[]
        for rel in PAYLOAD:
            copy(ROOT/rel,STAGE/rel)
            items.append(dict(path=rel,before=digest(game/rel),after=digest(STAGE/rel)))
        manifest=dict(game=str(game),files=items)
        (STAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        copy(ROOT/'tools/native_visuals/README.txt',STAGE/'README.txt')
        print('Prepared',len(items),'files:',STAGE)
        print('Game files unchanged. port.ini and XML are not overwritten.')
        return

    manifest=json.loads((STAGE/'manifest.json').read_text(encoding='utf-8'))
    if Path(manifest['game']).resolve()!=game or tuple(i['path'] for i in manifest['files'])!=PAYLOAD:
        raise ValueError('Unexpected manifest game/path list')
    # Never terminate a player's running session or replace its loaded modules.
    result=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True)
    processes=result.stdout.lower()
    for name in (b'freelancer.exe',b'freelancer_window.exe',b'freelancer_en.exe',b'freelancer_window_en.exe',b'flserver.exe'):
        if b'"'+name+b'"' in processes:
            raise RuntimeError('Close Freelancer/FLServer before installing; no files changed.')
    for item in manifest['files']:
        if digest(game/item['path'])!=item['before'] or digest(STAGE/item['path'])!=item['after']:
            raise RuntimeError('File changed since preparation: '+item['path'])
    backup=ROOT/'src/obj/native_visuals/backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    for item in manifest['files']:
        if item['before'] is not None:
            copy(game/item['path'],backup/item['path'])
            if digest(backup/item['path'])!=item['before']:raise RuntimeError('Backup verification failed')
    copy(STAGE/'manifest.json',backup/'manifest.json')
    touched=[]
    try:
        for item in manifest['files']:
            touched.append(item)
            copy(STAGE/item['path'],game/item['path'])
            if digest(game/item['path'])!=item['after']:raise RuntimeError('Install hash mismatch')
    except Exception:
        for item in reversed(touched):
            target=game/item['path']
            if item['before'] is None:target.unlink(missing_ok=True)
            else:copy(backup/item['path'],target)
        raise
    print('Installed and verified',len(PAYLOAD),'files into',game)
    print('Backup:',backup)


if __name__=='__main__':main()
