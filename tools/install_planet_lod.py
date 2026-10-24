"""Stage/install adaptive planet detail, with verified backup and restore.

Updates only the two planet quality settings; preserves all other game configuration.
Run without arguments to prepare, --apply to install, --restore BACKUP to roll back.
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STAGE = REPO / 'src/obj/planet_lod_install'
CONFIG = 'bin/port.ini'
SHADER = 'DATA_EXTRA/SHADERS/planet_surface.hlsl'
PAYLOAD = ('bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/RP9.dll', 'bin/RP9.pdb',
           'bin/Shading.dll', 'bin/Shading.pdb', SHADER)
ALLOWED = {*PAYLOAD, CONFIG}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def safe(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path outside root: {path}')
    return path


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def stopped():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq freelancer.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, check=True)
    if b'freelancer.exe' in result.stdout.lower():
        raise RuntimeError('Close Freelancer before installation/restoration.')


def configure(raw):
    text = raw.decode('latin1')
    sections = list(re.finditer(r'^\[([^]\r\n]+)\][ \t]*(?=\r?$)', text, re.M))
    matches = [(i, section) for i, section in enumerate(sections) if section[1].lower() == 'render']
    if len(matches) != 1:
        raise ValueError('Expected exactly one Render section')
    index, section = matches[0]
    end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
    body = text[section.end():end]
    settings = {'planet_adaptive_detail': '1', 'planet_lod_pixel_scale': '1'}
    newline = '\r\n' if '\r\n' in body else '\n'
    for name, value in settings.items():
        pattern = re.compile(r'^' + name + r'[ \t]*=[^\r\n]*', re.M | re.I)
        if len(pattern.findall(body)) > 1:
            raise ValueError(f'Duplicate setting: {name}')
        if pattern.search(body):
            body = pattern.sub(name + ' = ' + value, body)
        else:
            offset = len(newline) if body.startswith(newline) else 0
            body = body[:offset] + name + ' = ' + value + newline + body[offset:]
    return (text[:section.end()] + body + text[end:]).encode('latin1'), sorted(settings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', type=Path)
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if not (args.apply or args.restore):
        original = safe(game, CONFIG).read_bytes()
        configured, settings = configure(original)
        staged_config = safe(STAGE, CONFIG)
        staged_config.parent.mkdir(parents=True, exist_ok=True)
        staged_config.write_bytes(configured)
        for rel in PAYLOAD:
            copy(safe(REPO, rel), safe(STAGE, rel))
        items = []
        for rel in (CONFIG, *PAYLOAD):
            before, after = digest(safe(game, rel)), digest(safe(STAGE, rel))
            if before != after:
                items.append(dict(relative=rel, original=before, prepared=after))
        data = dict(game=str(game), settings=settings, files=items)
        (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2), encoding='utf8')
        print(f'Prepared {len(settings)} settings, {len(items)} changed files; game untouched.')
        return

    stopped()
    source = args.restore.resolve(strict=True) if args.restore else STAGE
    data = json.loads((source / 'manifest.json').read_text(encoding='utf8'))
    if Path(data['game']).resolve() != game:
        raise ValueError('Manifest game root mismatch')
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel not in ALLOWED or rel in seen:
            raise ValueError(f'Unexpected/duplicate target: {rel}')
        seen.add(rel)
        expected_game = item['prepared'] if args.restore else item['original']
        expected_source = item['original'] if args.restore else item['prepared']
        if digest(safe(game, rel)) != expected_game or digest(safe(source, rel)) != expected_source:
            raise ValueError(f'File changed since preparation/install: {rel}')

    def restore_from(backup):
        for item in data['files']:
            target = safe(game, item['relative'])
            if item['original'] is None:
                target.unlink(missing_ok=True)
            else:
                copy(safe(backup, item['relative']), target)
            if digest(target) != item['original']:
                raise ValueError(f'Restore verification failed: {target}')

    if args.restore:
        restore_from(source)
        print(f'Restored and verified {len(data["files"])} files from {source}')
        return
    backup = safe(game, 'BACKUP/codex_planet_lod_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for item in data['files']:
        if item['original'] is not None:
            target = safe(backup, item['relative'])
            copy(safe(game, item['relative']), target)
            if digest(target) != item['original']:
                raise ValueError(f'Backup verification failed: {target}')
    copy(source / 'manifest.json', backup / 'manifest.json')
    try:
        for item in data['files']:
            rel = item['relative']
            copy(safe(source, rel), safe(game, rel))
            if digest(safe(game, rel)) != item['prepared']:
                raise ValueError(f'Installation verification failed: {rel}')
    except Exception:
        restore_from(backup)
        raise
    print(f'Installed and verified {len(data["files"])} files. Backup: {backup}')


if __name__ == '__main__':
    main()
