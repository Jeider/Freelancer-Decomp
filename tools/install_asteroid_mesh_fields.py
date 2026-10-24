"""Prepare/apply the mesh profile to existing generated ordinary FarRocks fields.

Preparation writes only src/obj. Installation checks hashes and backs up every changed file.
Fields without DynamicAsteroids retain their existing look. Retail assets are not copied into Git.
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
STAGE = REPO / 'src/obj/asteroid_mesh_install'
HEADER = re.compile(r'^\[([^\]\r\n]+)\][ \t]*\r?$', re.M)
BINARY_PATHS = ['bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/RP9.dll', 'bin/RP9.pdb',
                'DATA_EXTRA/SHADERS/far_rocks.hlsl', 'DATA_EXTRA/SHADERS/field_dust.hlsl']

def sections(text):
    headers = list(HEADER.finditer(text))
    return [(m[1].lower(), m.start(), m.end(), headers[i+1].start() if i+1 < len(headers) else len(text))
            for i, m in enumerate(headers)]

def values(text):
    return {m[1].lower(): m[2].strip() for m in re.finditer(r'^([\w]+)\s*=\s*([^;\r\n]*)', text, re.M)}

def field_candidates(game):
    for path in sorted((game / 'DATA/SOLAR/ASTEROIDS_MOD/GENERATED').glob('*_asteroids.ini')):
        text = path.read_bytes().decode('latin1')
        parts = sections(text)
        far = [p for p in parts if p[0] == 'farrocks']
        if not far:
            continue
        if len(far) != 1:
            raise ValueError(f'Duplicate FarRocks: {path}')
        models = [values(text[end:stop]).get('asteroid') for name, _, end, stop in parts if name == 'dynamicasteroids']
        yield path, text, far[0], [m for m in models if m]

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def safe(root, relative):
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path outside root: {path}')
    return path

def copy(source, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, dest)

def stopped():
    result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq freelancer.exe', '/FO', 'CSV', '/NH'],
                            capture_output=True, check=True)
    if b'freelancer.exe' in result.stdout.lower():
        raise RuntimeError('Close Freelancer before installation/restoration.')

def manifest(path, game):
    data = json.loads(path.read_text(encoding='utf8'))
    if Path(data['game']).resolve() != game:
        raise ValueError('Manifest game root mismatch')
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel in seen or (rel not in BINARY_PATHS and not re.fullmatch(
                r'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/[\w]+_asteroids\.ini', rel)):
            raise ValueError(f'Unexpected/duplicate target: {rel}')
        safe(game, rel)
        seen.add(rel)
    return data

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', type=Path)
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if args.restore or args.apply:
        stopped()
        source = args.restore.resolve(strict=True) if args.restore else STAGE
        data = manifest(source / 'manifest.json', game)
        for item in data['files']:
            rel = item['relative']
            expected_game = item['prepared'] if args.restore else item['original']
            expected_source = item['original'] if args.restore else item['prepared']
            if digest(safe(game, rel)) != expected_game or digest(safe(source, rel)) != expected_source:
                raise ValueError(f'File changed since preparation/install: {rel}')
        if args.restore:
            for item in data['files']:
                copy(safe(source, item['relative']), safe(game, item['relative']))
            print(f'Restored {len(data["files"])} files from {source}')
            return
        backup = safe(game, 'BACKUP/codex_asteroid_mesh_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
        for item in data['files']:
            target = safe(backup, item['relative'])
            copy(safe(game, item['relative']), target)
            if digest(target) != item['original']:
                raise ValueError(f'Backup hash mismatch: {target}')
        copy(STAGE / 'manifest.json', backup / 'manifest.json')
        try:
            for item in data['files']:
                target = safe(game, item['relative'])
                copy(safe(STAGE, item['relative']), target)
                if digest(target) != item['prepared']:
                    raise ValueError(f'Installed hash mismatch: {target}')
        except Exception:
            for item in data['files']:
                copy(safe(backup, item['relative']), safe(game, item['relative']))
            raise
        print(f'Installed and verified {len(data["files"])} changed files. Backup: {backup}')
        return

    profile = values((REPO / 'DATA_EXTRA/ASTEROIDS/dynamic_mesh_fields.ini').read_text())
    data = {'game': str(game), 'fields': [], 'skipped': [], 'files': []}
    STAGE.mkdir(parents=True, exist_ok=True)
    def record(rel):
        old, new = digest(safe(game, rel)), digest(safe(STAGE, rel))
        if old != new:
            data['files'].append(dict(relative=rel, original=old, prepared=new))
    for path, text, (_, start, end, stop), models in field_candidates(game):
        if not models:
            data['skipped'].append(path.name)
            continue
        if len(models) > 4:
            raise ValueError(f'More than four dynamic models: {path}')
        body = text[end:stop]
        for key in profile:
            body = re.sub(r'^' + re.escape(key) + r'[ \t]*=[^\r\n]*(?:\r?\n|$)', '', body, flags=re.M | re.I)
        body = '\r\n' + '\r\n'.join(f'{k} = {v}' for k, v in profile.items()) + '\r\n' + body.lstrip('\r\n')
        rel = path.relative_to(game).as_posix()
        target = safe(STAGE, rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((text[:end].rstrip('\r\n') + body + text[stop:]).encode('latin1'))
        record(rel)
        data['fields'].append(dict(relative=rel, models=models))
    for rel in BINARY_PATHS:
        copy(safe(REPO, rel), safe(STAGE, rel))
        record(rel)
    (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2), encoding='utf8')
    print(f'Prepared {len(data["fields"])} fields, {len(data["files"])} changed files; game untouched.')
    print('Skipped (no dynamic model): ' + ', '.join(data['skipped']))

if __name__ == '__main__':
    main()
