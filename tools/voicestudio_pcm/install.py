"""Install the checked PCM voice patch into Pythonlancer, with backups; no DATA."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/voicestudio_pcm'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((OUT / 'manifest.json').read_text(encoding='utf-8'))
    destination = Path(manifest['destination']).resolve()
    payload = (OUT / 'payload').resolve()
    for relative, hashes in manifest['files'].items():
        target, source = (destination / relative).resolve(), (payload / relative).resolve()
        if not target.is_relative_to(destination) or not source.is_relative_to(payload):
            raise ValueError('Unexpected path outside installation root')
        if any(part.lower() == 'data' for part in target.parts):
            raise ValueError('This patch must not write DATA')
        if digest(target) != hashes['before'] or digest(source) != hashes['after']:
            raise ValueError('File changed since staging: ' + relative)
    if not args.apply:
        print(f'Checked {len(manifest["files"])} files; ready to install with --apply')
        return
    backup = OUT / 'backups' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    for relative, hashes in manifest['files'].items():
        if hashes['before'] is not None:
            target = backup / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(destination / relative, target)
            if digest(target) != hashes['before']:
                raise ValueError('Backup failed: ' + relative)
    shutil.copy2(OUT / 'manifest.json', backup / 'manifest.json')
    touched = []
    try:
        for relative, hashes in manifest['files'].items():
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            touched.append(relative)
            shutil.copy2(payload / relative, target)
            if digest(target) != hashes['after']:
                raise ValueError('Installed hash mismatch: ' + relative)
    except Exception:
        for relative in reversed(touched):
            target = (destination / relative).resolve()
            if not target.is_relative_to(destination):
                raise ValueError('Rollback escaped installation root')
            if manifest['files'][relative]['before'] is None:
                target.unlink(missing_ok=True)
            else:
                shutil.copy2(backup / relative, target)
        raise
    print(f'Installed PCM WAV voice generation. Backups: {backup}')


if __name__ == '__main__':
    main()
