"""Stage/install Player-only detailed shadows with verified backup/restore.
Run without arguments to prepare; --apply installs; --restore BACKUP rolls back.
Game configurations are unchanged; client, RP9 and the surface shader are installed.
"""
import argparse
import datetime
import json
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from install_hyperspace_tunnel import copy, digest, safe, stopped

REPO = Path(__file__).resolve().parents[2]
STAGE = REPO / 'src/obj/player_shadow_quality/install'
ASSETS = REPO / 'src/obj/player_shadow_quality/assets'
MAT = 'DATA/SOLAR/ASTEROIDS_MOD/KU_TGK/ast_ku_tgk.mat'
PAYLOAD = ('bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/RP9.dll', 'bin/RP9.pdb',
           'DATA_EXTRA/SHADERS/surface_material.hlsl', MAT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', type=Path)
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if not (args.apply or args.restore):
        items = []
        assets = json.loads((ASSETS / 'manifest.json').read_text())
        if digest(safe(game, MAT)) != assets['source_sha256']:
            raise ValueError('MAT changed since preparation; run prepare_assets.py again.')
        for rel in PAYLOAD:
            copy(safe(ASSETS if rel == MAT else REPO, rel), safe(STAGE, rel))
            before, after = digest(safe(game, rel)), digest(safe(STAGE, rel))
            if before != after:
                items.append(dict(relative=rel, original=before, prepared=after))
        data = dict(game=str(game), files=items,
                    scope='Player-only detailed shadows; 8K near for player receivers, 4K far and capped filtering for other receivers; FPS limit untouched')
        (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2), encoding='utf8')
        print(f'Prepared {len(items)} changed files; game untouched.')
        return

    stopped()
    import subprocess
    processes = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq flserver.exe', '/FO', 'CSV', '/NH'],
                               capture_output=True, check=True)
    if b'flserver.exe' in processes.stdout.lower():
        raise RuntimeError('Close FLServer before installation/restoration.')
    source = args.restore.resolve(strict=True) if args.restore else STAGE
    data = json.loads((source / 'manifest.json').read_text(encoding='utf8'))
    if Path(data['game']).resolve() != game:
        raise ValueError('Manifest game root mismatch')
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel not in PAYLOAD or rel in seen:
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
    if not data['files']:
        print('Already installed; no changes.')
        warm_game(game)
        return
    backup = safe(game, 'BACKUP/codex_player_shadow_quality_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
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

    warm_game(game)

def warm_game(game):
    sys.path.insert(0, str(REPO / 'tools/asteroid_normals'))
    from warm import warm
    warm(game)

if __name__ == '__main__':
    main()
