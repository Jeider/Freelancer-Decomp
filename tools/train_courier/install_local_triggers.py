"""Stage/apply only checked Content.dll/PDB; preserve the game's current engine/client."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/local_triggers'
BUILD = ROOT/'src/obj/train_courier/rpg1/bin'
GAME = Path('D:/Games/FL_MOD/bin')
NAMES = ('Content.dll', 'Content.pdb')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    checks = json.loads((OUT/'check/verified.json').read_text(encoding='utf-8'))
    for path, expected in checks.items():
        assert digest(Path(path)) == expected, 'Checked input changed: '+path
    package = OUT/'package'
    manifest = OUT/'install.json'
    if not args.apply:
        package.mkdir(parents=True, exist_ok=True)
        records = {}
        for name in NAMES:
            shutil.copy2(BUILD/name, package/name)
            records[name] = {'before': digest(GAME/name), 'after': digest(package/name)}
        manifest.write_text(json.dumps(records, indent=2), encoding='utf-8')
        print('Staged '+', '.join(NAMES)+':', manifest)
        return
    processes = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, check=True).stdout.lower()
    assert not any(b'"'+name+b'"' in processes for name in
                   (b'freelancer.exe', b'freelancer_window.exe', b'flserver.exe')), 'Close game/server before installing'
    records = json.loads(manifest.read_text(encoding='utf-8'))
    assert set(records) == set(NAMES)
    for name, record in records.items():
        assert digest(GAME/name) == record['before'], 'Live file changed: '+name
        assert digest(package/name) == record['after'] == checks[str(BUILD/name)], 'Package changed: '+name
    backup = OUT/'backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    shutil.copy2(manifest, backup/'install.json')
    for name in NAMES:
        shutil.copy2(GAME/name, backup/name)
    try:
        for name in NAMES:
            shutil.copy2(package/name, GAME/name)
            assert digest(GAME/name) == records[name]['after']
    except BaseException:
        for name in NAMES:
            shutil.copy2(backup/name, GAME/name)
        raise
    print('Installed '+', '.join(NAMES)+' in', GAME)
    print('Verified backup:', backup)


if __name__ == '__main__':
    main()
