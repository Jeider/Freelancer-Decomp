"""Restore Tau29's five client fields from a verified pre-rollout backup, plus generator scope."""
import argparse
import datetime
import json
import os
import tempfile
from pathlib import Path

from install_world_asteroids import (ROOT, GENERATOR, scope, records, text, digest, safe,
                                    copy, patch_generator)

STAGE = ROOT / 'src/obj/tau29_client_asteroids'
FIELDS = tuple('DATA/SOLAR/ASTEROIDS_MOD/GENERATED/tau29_' + name + '_asteroids.ini'
               for name in ('ast1', 'ast3', 'ast4', 'ast5', 'astring1'))
ALLOWED = {*FIELDS, GENERATOR}


def prepare(game, baseline):
    previous = json.loads((baseline / 'manifest.json').read_text(encoding='utf8'))
    if Path(previous['game']).resolve() != game:
        raise ValueError('Backup belongs to another game')
    saved = {f['relative']: f for f in previous['files']}
    fields, inputs = scope(game)
    eligible = [f for f in fields if not f['reason']]
    systems = {o['system'] for f in eligible for o in f['owners']}
    models = {m for f in eligible for m in f['models']}
    payload = {}
    for rel in FIELDS:
        original = safe(baseline, rel)
        if digest(original) != saved[rel]['original']:
            raise ValueError('Backup hash mismatch: ' + rel)
        if records(text(original), 'serverdynamicasteroids'):
            raise ValueError('Expected original client field: ' + rel)
        if digest(safe(game, rel)) not in (saved[rel]['prepared'], saved[rel]['original']):
            raise ValueError('Field changed since rollout; review first: ' + rel)
        payload[rel] = original.read_bytes()
    payload[GENERATOR] = patch_generator(safe(game, GENERATOR).read_bytes(), systems, models)
    inputs[GENERATOR] = digest(safe(game, GENERATOR))
    data = dict(game=str(game), baseline=str(baseline), dependencies=inputs, files=[])
    for rel, raw in payload.items():
        if safe(game, rel).read_bytes() == raw:
            continue
        dest = safe(STAGE, rel)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        data['files'].append(dict(relative=rel, original=digest(safe(game, rel)), prepared=digest(dest)))
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf8')
    print(f'Prepared {len(data["files"])} changed files; all five Tau29 fields restored byte-for-byte. Game untouched.')


def apply(game):
    # Data-only payload: atomically replace complete files even if the game is open.
    # Already loaded fields keep their old state until the next game launch.
    def replace_data(source, destination):
        descriptor, temporary = tempfile.mkstemp(prefix=destination.name + '.', suffix='.tmp', dir=destination.parent)
        try:
            with os.fdopen(descriptor, 'wb') as stream:
                stream.write(source.read_bytes())
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, destination)
        finally:
            Path(temporary).unlink(missing_ok=True)
    data = json.loads((STAGE / 'manifest.json').read_text(encoding='utf8'))
    if Path(data['game']).resolve() != game:
        raise ValueError('Wrong game root')
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel not in ALLOWED or rel in seen:
            raise ValueError('Unexpected payload: ' + rel)
        seen.add(rel)
        if digest(safe(game, rel)) != item['original'] or digest(safe(STAGE, rel)) != item['prepared']:
            raise ValueError('File changed: ' + rel)
    for rel, expected in data['dependencies'].items():
        if digest(safe(game, rel)) != expected:
            raise ValueError('Dependency changed: ' + rel)
    if not data['files']:
        print('Already restored.')
        return
    backup = safe(game, 'BACKUP/codex_tau29_client_asteroids_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for item in data['files']:
        copy(safe(game, item['relative']), safe(backup, item['relative']))
        assert digest(safe(backup, item['relative'])) == item['original']
    copy(STAGE / 'manifest.json', backup / 'manifest.json')
    touched = []
    try:
        for item in data['files']:
            rel = item['relative']
            if digest(safe(game, rel)) != item['original']:
                raise ValueError('File changed during install: ' + rel)
            touched.append(item)
            replace_data(safe(STAGE, rel), safe(game, rel))
            assert digest(safe(game, rel)) == item['prepared']
        for rel, expected in data['dependencies'].items():
            if rel not in seen:
                assert digest(safe(game, rel)) == expected, rel
    except Exception:
        for item in touched:
            replace_data(safe(backup, item['relative']), safe(game, item['relative']))
            assert digest(safe(game, item['relative'])) == item['original']
        raise
    print(f'Restored and SHA256 verified {len(data["files"])} files. Other fields unchanged. Backup: {backup}')
    print('Restart the game to reload the restored fields.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    parser.add_argument('--baseline', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if args.apply:
        apply(game)
    else:
        if args.baseline is None:
            parser.error('--baseline is required to prepare the restoration')
        prepare(game, args.baseline.resolve(strict=True))
