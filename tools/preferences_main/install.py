"""Stage/install/restore the cached preferences probe; never launch the game."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
TOPIC = ROOT / 'out/preferences_main_hitch'
BUILD = TOPIC / 'build'
STAGE = TOPIC / 'install'
GAME = Path('D:/Games/FL_MOD/bin')
FILES = ('freelancer.exe', 'freelancer.pdb')
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_client():
    compiler, env = compiler_env()
    def dump(option, path):
        return subprocess.check_output([str(compiler / 'dumpbin.exe'), option, str(path)], env=env, text=True)
    def exports(path):
        return set(re.findall(r'^\s+\d+\s+[0-9A-F]+\s+(?:[0-9A-F]+\s+)?(\S+)', dump('/exports', path), re.M))
    assert exports(GAME / 'freelancer.exe') <= exports(BUILD / 'freelancer.exe')
    dependency, cache, count = None, {}, 0
    for line in dump('/imports', BUILD / 'freelancer.exe').splitlines():
        match = re.match(r'^    (\S+\.dll)\s*$', line, re.I)
        if match:
            dependency = match.group(1)
            continue
        match = re.match(r'^\s+[0-9A-F]+\s+(\?\S+|[A-Za-z_]\S*)\s*$', line)
        if not match or not dependency or not (GAME / dependency).exists():
            continue
        if dependency not in cache:
            cache[dependency] = exports(GAME / dependency)
        assert match.group(1) in cache[dependency], (dependency, match.group(1))
        count += 1
    print(f'PASS: client exports preserved; {count} imports resolve against installed DLLs')

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', type=Path)
    args = parser.parse_args()
    if not args.apply and not args.restore:
        check_client()
        evidence = json.loads((BUILD / 'build.json').read_text())
        assert digest(BUILD / 'freelancer.exe') == evidence['client']
        STAGE.mkdir(parents=True, exist_ok=True)
        items = []
        for name in FILES:
            shutil.copy2(BUILD / name, STAGE / name)
            items.append(dict(name=name, original=digest(GAME / name), prepared=digest(STAGE / name)))
        (STAGE / 'manifest.json').write_text(json.dumps(dict(game=str(GAME), files=items), indent=2))
        print('Prepared only freelancer.exe and its PDB. Game unchanged.')
        return
    for process in ('freelancer.exe', 'flserver.exe'):
        listing = subprocess.check_output(['tasklist', '/FI', 'IMAGENAME eq ' + process, '/FO', 'CSV', '/NH'])
        if process.encode() in listing.lower():
            raise RuntimeError('Close ' + process + ' before installation or restore.')
    source = args.restore.resolve(strict=True) if args.restore else STAGE
    data = json.loads((source / 'manifest.json').read_text())
    assert Path(data['game']).resolve() == GAME.resolve()
    assert [item['name'] for item in data['files']] == list(FILES)
    for item in data['files']:
        assert digest(GAME / item['name']) == item['prepared' if args.restore else 'original'], item['name']
        assert digest(source / item['name']) == item['original' if args.restore else 'prepared'], item['name']
    if args.restore:
        for item in data['files']:
            shutil.copy2(source / item['name'], GAME / item['name'])
            assert digest(GAME / item['name']) == item['original']
        print('Restored and verified client and PDB.')
        return
    backup = TOPIC / 'backups' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
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
    print('Installed and verified client and PDB. Backup:', backup)

if __name__ == '__main__':
    main()
