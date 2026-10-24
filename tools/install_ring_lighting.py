"""Stage/install the per-ring lighting option and opt out Tau-37's ice ring.

Run without arguments to prepare; --apply installs the reviewed manifest;
--restore BACKUP restores it. Other game configuration is preserved byte for byte.
"""
import argparse
import datetime
import json
import re
from pathlib import Path

from install_hyperspace_tunnel import copy, digest, safe, stopped

REPO = Path(__file__).resolve().parents[1]
STAGE = REPO / 'src/obj/ring_lighting_install'
CONFIG = 'DATA/SOLAR/RINGS/tau37_ice.ini'
PAYLOAD = ('bin/freelancer.exe', 'bin/freelancer.pdb')
ALLOWED = {*PAYLOAD, CONFIG}


def configure(raw):
    headers = list(re.finditer(rb'^\[([^\]\r\n]+)\][ \t]*\r?$', raw, re.M))
    exterior = [i for i, h in enumerate(headers) if h[1].lower() == b'exterior']
    if len(exterior) != 1:
        raise ValueError('Expected exactly one active [Exterior] section')
    index = exterior[0]
    start = headers[index].end()
    end = headers[index + 1].start() if index + 1 < len(headers) else len(raw)
    body = raw[start:end]
    flag = re.compile(rb'^[ \t]*lighting[ \t]*=[^\r\n]*(?:\r?\n|$)', re.M | re.I)
    cleaned = flag.sub(b'', body)
    newline = b'\r\n' if b'\r\n' in raw else b'\n'
    # Header match consumes CR but leaves LF; insert after that LF.
    offset = 1 if cleaned.startswith(b'\n') else 0
    patched = cleaned[:offset] + b'lighting = false' + newline + cleaned[offset:]
    return raw[:start] + patched + raw[end:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', type=Path)
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if not (args.apply or args.restore):
        for rel in PAYLOAD:
            copy(safe(REPO, rel), safe(STAGE, rel))
        prepared = configure(safe(game, CONFIG).read_bytes())
        target = safe(STAGE, CONFIG)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(prepared)
        if configure(prepared) != prepared:
            raise ValueError('Config patch must be idempotent')
        items = []
        for rel in (*PAYLOAD, CONFIG):
            before, after = digest(safe(game, rel)), digest(safe(STAGE, rel))
            if before != after:
                items.append(dict(relative=rel, original=before, prepared=after))
        data = dict(game=str(game), files=items,
                    scope='per-ring lighting option; lighting=false only in tau37_ice.ini [Exterior]')
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
    if not data['files']:
        print('Already installed; no changes.')
        return
    backup = safe(game, 'BACKUP/codex_ring_lighting_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
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
