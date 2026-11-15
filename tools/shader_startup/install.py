"""Stage/apply RP9, client and the matching room shader with verified rollback."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
game = Path('D:/Games/FL_MOD')
stage = root/'out/shader_startup/package'
manifest_path = root/'out/shader_startup/install.json'
names = ('RP9.dll', 'freelancer.exe', 'room_material.hlsl')

def target(name):
    return game/('DATA_EXTRA/SHADERS' if name.endswith('.hlsl') else 'bin')/name

def source_file(name):
    return root/('DATA_EXTRA/SHADERS' if name.endswith('.hlsl') else 'out/base_neural/on/bin')/name

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if not args.apply:
        stage.mkdir(parents=True, exist_ok=True)
        manifest = {}
        for name in names:
            source = source_file(name)
            shutil.copy2(source, stage/name)
            manifest[name] = {'before': digest(target(name)), 'after': digest(stage/name)}
        manifest_path.write_text(json.dumps(manifest, indent=2))
        print(json.dumps(manifest, indent=2))
        return
    processes = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, check=True).stdout.lower()
    if any(b'"'+name+b'"' in processes for name in (b'freelancer.exe', b'flserver.exe', b'freelancer_window.exe')):
        raise RuntimeError('Close Freelancer/FLServer before installation')
    manifest = json.loads(manifest_path.read_text())
    for name in names:
        if digest(target(name)) != manifest[name]['before'] or digest(stage/name) != manifest[name]['after']:
            raise RuntimeError('File changed after staging: '+name)
    backup = root/'out/shader_startup/backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    for name in names:
        shutil.copy2(target(name), backup/name)
    try:
        for name in names:
            shutil.copy2(stage/name, target(name))
            if digest(target(name)) != manifest[name]['after']:
                raise RuntimeError('Installed hash mismatch: '+name)
    except Exception:
        for name in names:
            shutil.copy2(backup/name, target(name))
        raise
    print('Installed RP9.dll and freelancer.exe into', game/'bin', 'and matching room shader into DATA_EXTRA/SHADERS')
    print('Verified backup:', backup)

if __name__ == '__main__':
    main()
