"""Stage/apply matching RPG Content/client binaries; preserve other installed modules."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/rpg_cutscenes/engine_install'
GAME = Path('D:/Games/FL_MOD')
BUILD = ROOT / 'src/obj/rpg_contacts'
SOURCES = {name: BUILD / ('build_Release_1_client' if name.startswith('freelancer') else 'build_Release_1') / 'bin' / name
           for name in ('freelancer.exe', 'freelancer.pdb', 'Content.dll', 'Content.pdb')}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        OUT.mkdir(parents=True, exist_ok=True)
        files = {}
        for name, source in SOURCES.items():
            target = OUT / name
            shutil.copy2(source, target)
            files[name] = {'before': sha(GAME / 'bin' / name), 'after': sha(target), 'source': str(source)}
        manifest = {'files': files, 'dependencies': {name: sha(GAME / 'bin' / name) for name in ('Common.dll', 'Server.dll')}}
        (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
        print('Staged matching Content.dll/client with PDBs; game unchanged')
        return
    manifest = json.loads((OUT / 'manifest.json').read_text())
    if set(manifest['files']) != set(SOURCES):
        raise ValueError('Unexpected engine manifest')
    processes = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, check=True).stdout.lower()
    for name in (b'freelancer.exe', b'freelancer_en.exe', b'freelancer_window.exe', b'freelancer_window_en.exe', b'flserver.exe'):
        if b'"' + name + b'"' in processes:
            raise RuntimeError('Close the game/server before installing binaries')
    for name, entry in manifest['files'].items():
        if sha(GAME / 'bin' / name) != entry['before'] or sha(OUT / name) != entry['after'] or sha(SOURCES[name]) != entry['after']:
            raise ValueError('File changed since staging: ' + name)
    for name, expected in manifest['dependencies'].items():
        if sha(GAME / 'bin' / name) != expected:
            raise ValueError('Installed dependency changed: ' + name)
    backup = OUT / 'backups' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    for name in SOURCES:
        shutil.copy2(GAME / 'bin' / name, backup / name)
        assert sha(backup / name) == manifest['files'][name]['before']
    touched = []
    try:
        for name, entry in manifest['files'].items():
            touched.append(name)
            shutil.copy2(OUT / name, GAME / 'bin' / name)
            assert sha(GAME / 'bin' / name) == entry['after']
    except BaseException:
        for name in reversed(touched):
            shutil.copy2(backup / name, GAME / 'bin' / name)
        raise
    manifest['backup'] = str(backup)
    (OUT / 'installed.json').write_text(json.dumps(manifest, indent=2))
    print('Installed and verified Content/client in game bin; backup:', backup)


if __name__ == '__main__':
    main()
