"""Stage/install ordinary and alternate jumpgate visuals with verified backup/restore.
Run without arguments to prepare; --apply installs; --restore BACKUP rolls back.
No game INIs, ALE, Common DLL or other gate types are changed.
"""
import argparse
import datetime
import json
from pathlib import Path

from install_hyperspace_tunnel import copy, digest, safe, stopped

REPO = Path(__file__).resolve().parents[1]
STAGE = REPO / 'src/obj/jumpgate_install'
PAYLOAD = ('bin/freelancer.exe', 'bin/freelancer.pdb',
           'DATA_EXTRA/SHADERS/jumpgate_aperture.hlsl',
           'DATA_EXTRA/SHADERS/hyperspace_tunnel.hlsl')


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
        for rel in PAYLOAD:
            copy(safe(REPO, rel), safe(STAGE, rel))
            before, after = digest(safe(game, rel)), digest(safe(STAGE, rel))
            if before != after:
                items.append(dict(relative=rel, original=before, prepared=after))
        data = dict(game=str(game), files=items,
                    scope='jumpgate archetype with ordinary mod_jumpgate_tunnel or alternate big_jumpgate_tunnel + jg_donutshooter group; sig8_jg_to_rh_ber and rh_mnh_jg_to_rh_kgb references; docking and jump timing unchanged')
        (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2), encoding='utf8')
        print(f'Prepared {len(items)} changed files; game untouched.')
        return

    stopped()
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
        return
    backup = safe(game, 'BACKUP/codex_jumpgate_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
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
