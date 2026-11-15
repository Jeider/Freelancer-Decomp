"""Stage/install the matched SP transfer client, Server and Content with rollback."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD/bin')
PACKAGE = ROOT / 'out/train_space_transfer/package'
MANIFEST = PACKAGE.parent / 'install.json'
SOURCES = {
    name: ROOT / folder / name
    for folder, names in [
        ('out/base_neural/on/bin', ('freelancer.exe', 'freelancer.pdb')),
        ('src/obj/train_courier/rpg1/bin', ('Server.dll', 'Server.pdb', 'Content.dll', 'Content.pdb'))]
    for name in names
}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        for check in ('check_space_transfer.py', 'check_transfer_binding.py', 'check_transfer_docking.py', 'check_transfer_hud.py', 'check_boarding.py'):
            subprocess.run([sys.executable, str(Path(__file__).with_name(check))], cwd=ROOT, check=True)
        assert digest(ROOT / 'out/base_neural/on/bin/Common.dll') == digest(GAME / 'Common.dll'), 'Common differs from tested build'
        PACKAGE.mkdir(parents=True, exist_ok=True)
        records = {}
        for name, source in SOURCES.items():
            shutil.copy2(source, PACKAGE / name)
            records[name] = {'before': digest(GAME / name) if (GAME / name).exists() else None,
                             'after': digest(PACKAGE / name)}
        manifest = {'files': records, 'dependencies': {name: digest(GAME / name) for name in ('Common.dll', 'RP9.dll')},
                    'scope': 'SP courier transfer enabled; ordinary MP path retained; gameplay validation still required'}
        MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        print('Staged matched client/Server/Content:', MANIFEST)
        return
    processes = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, check=True).stdout.lower()
    assert not any(b'"'+name+b'"' in processes for name in
                   (b'freelancer.exe', b'flserver.exe', b'freelancer_window.exe')), 'Close game/server before installing'
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert set(manifest['files']) == set(SOURCES), 'Unexpected package files'
    for name, record in manifest['files'].items():
        current = digest(GAME / name) if (GAME / name).exists() else None
        assert current == record['before'], 'Live file changed: '+name
        assert digest(PACKAGE / name) == record['after'], 'Package changed: '+name
    for name, expected in manifest['dependencies'].items():
        assert digest(GAME / name) == expected, 'Dependency changed: '+name
    backup = PACKAGE.parent / 'backups' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    shutil.copy2(MANIFEST, backup / 'install.json')
    for name, record in manifest['files'].items():
        if record['before'] is not None:
            shutil.copy2(GAME / name, backup / name)
    try:
        for name, record in manifest['files'].items():
            shutil.copy2(PACKAGE / name, GAME / name)
            assert digest(GAME / name) == record['after'], 'Installed hash mismatch: '+name
    except BaseException:
        for name, record in manifest['files'].items():
            if record['before'] is not None:
                shutil.copy2(backup / name, GAME / name)
            else:
                (GAME / name).unlink(missing_ok=True)
        raise
    print('Installed client, Server and Content in', GAME)
    print('Verified backup:', backup)

if __name__ == '__main__':
    main()
