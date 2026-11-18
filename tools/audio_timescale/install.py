"""Prepare, install or restore the client and both audio DLLs with matching symbols."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BUILT = ROOT / 'out/audio_timescale/build'
STAGE = ROOT / 'out/audio_timescale/install'
GAME = Path('D:/Games/FL_MOD/bin')
FILES = ('freelancer.exe', 'freelancer.pdb', 'SoundManager.dll', 'SoundManager.pdb',
         'SoundStreamer.dll', 'SoundStreamer.pdb')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', type=Path)
    args = parser.parse_args()
    if not args.apply and not args.restore:
        from check_imports import main as check_imports
        check_imports()
        STAGE.mkdir(parents=True, exist_ok=True)
        items = []
        for name in FILES:
            shutil.copy2(BUILT / name, STAGE / name)
            items.append(dict(name=name, original=digest(GAME / name), prepared=digest(STAGE / name)))
        (STAGE / 'manifest.json').write_text(json.dumps(dict(game=str(GAME), files=items), indent=2))
        print('Prepared client, SoundManager, SoundStreamer and matching symbols. Game unchanged.')
        return
    for process in ('freelancer.exe', 'flserver.exe'):
        listing = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq ' + process, '/FO', 'CSV', '/NH'])
        if process.encode() in listing.lower():
            raise RuntimeError('Close ' + process + ' before installation or restore.')
    source = args.restore.resolve(strict=True) if args.restore else STAGE
    data = json.loads((source / 'manifest.json').read_text())
    assert Path(data['game']).resolve() == GAME.resolve()
    assert [item['name'] for item in data['files']] in (list(FILES), list(FILES[:4]))
    for item in data['files']:
        assert digest(GAME / item['name']) == item['prepared' if args.restore else 'original'], item['name']
        assert digest(source / item['name']) == item['original' if args.restore else 'prepared'], item['name']
    if args.restore:
        for item in data['files']:
            shutil.copy2(source / item['name'], GAME / item['name'])
            assert digest(GAME / item['name']) == item['original']
        print('Restored and verified', len(data['files']), 'files.')
        return
    backup = ROOT / 'out/audio_timescale/backups' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    for item in data['files']:
        shutil.copy2(GAME / item['name'], backup / item['name'])
        assert digest(backup / item['name']) == item['original']
    shutil.copy2(source / 'manifest.json', backup / 'manifest.json')
    touched = []
    try:
        for item in data['files']:
            touched.append(item)
            shutil.copy2(source / item['name'], GAME / item['name'])
            assert digest(GAME / item['name']) == item['prepared']
    except Exception:
        for item in touched:
            shutil.copy2(backup / item['name'], GAME / item['name'])
            assert digest(GAME / item['name']) == item['original']
        raise
    print('Installed and verified client, audio DLLs and symbols. Backup:', backup)

if __name__ == '__main__':
    main()
