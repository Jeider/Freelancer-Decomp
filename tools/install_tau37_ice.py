"""Stage/install the Tau37 ice prototype and rebuilt client, with verified backups."""
import argparse
import datetime
import json
import re
from pathlib import Path

from install_hyperspace_tunnel import copy, digest, safe, stopped

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'src/obj/tau37_ice_install'
CONFIG = 'DATA_EXTRA/VOLUMETRIC/volumetric.ini'
FILES = ('bin/freelancer.exe', 'bin/freelancer.pdb', CONFIG,
         'DATA_EXTRA/SHADERS/nebula_ice.hlsl', 'DATA_EXTRA/SHADERS/nebula_volume.hlsl',
         'DATA_EXTRA/SHADERS/nebula_walker_ice.hlsl',
         'DATA_EXTRA/SHADERS/nebula_composite.hlsl')


def configure(raw):
    begin, end = b'; BEGIN TAU37 ICE', b'; END TAU37 ICE'
    reference = (ROOT / CONFIG).read_bytes()
    block = reference[reference.index(begin):reference.index(end) + len(end)]
    if begin in raw:
        if raw.count(begin) != 1 or raw.count(end) != 1:
            raise ValueError('Ambiguous Tau37 ice configuration')
        merged = raw[:raw.index(begin)] + block + raw[raw.index(end) + len(end):]
        # User-requested global vanilla lightning, including custom installed overrides.
        merged = re.sub(rb'(?mi)^(lightning_enabled[ \t]*=[ \t]*)[^;\r\n]+', rb'\g<1>0', merged)
        return re.sub(rb'(?mi)^(lightning_lights_ships[ \t]*=[ \t]*)[^;\r\n]+', rb'\g<1>0', merged)
    if b'name = tau37_ice' in raw or b'file = gen_tau37_' in raw:
        raise ValueError('Existing unmarked Tau37 overrides need reconciliation')
    merged = raw.rstrip() + b'\r\n\r\n' + block + b'\r\n'
    merged = re.sub(rb'(?mi)^(lightning_enabled[ \t]*=[ \t]*)[^;\r\n]+', rb'\g<1>0', merged)
    return re.sub(rb'(?mi)^(lightning_lights_ships[ \t]*=[ \t]*)[^;\r\n]+', rb'\g<1>0', merged)



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if not args.apply:
        items = []
        for rel in FILES:
            if rel == CONFIG:
                target = safe(STAGE, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(configure(safe(game, rel).read_bytes()))
            else:
                copy(safe(ROOT, rel), safe(STAGE, rel))
            before, after = digest(safe(game, rel)), digest(safe(STAGE, rel))
            if before != after:
                items.append(dict(relative=rel, original=before, prepared=after))
        data = dict(game=str(game), files=items,
                    scope='Tau37 walker-based fractured ice; preserved tau37_white; vanilla lightning globally')
        (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2), encoding='utf8')
        print(f'Prepared {len(items)} changed files; game untouched.')
        return
    stopped()
    data = json.loads((STAGE / 'manifest.json').read_text(encoding='utf8'))
    if Path(data['game']).resolve() != game:
        raise ValueError('Game root differs from staged manifest')
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel not in FILES or rel in seen:
            raise ValueError(f'Unexpected target: {rel}')
        seen.add(rel)
        if digest(safe(game, rel)) != item['original'] or digest(safe(STAGE, rel)) != item['prepared']:
            raise ValueError(f'File changed since staging: {rel}')
    if not data['files']:
        print('Already installed.')
        return
    backup = safe(game, 'BACKUP/codex_tau37_ice_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for item in data['files']:
        rel = item['relative']
        if item['original'] is not None:
            copy(safe(game, rel), safe(backup, rel))
            if digest(safe(backup, rel)) != item['original']:
                raise ValueError(f'Backup mismatch: {rel}')
    copy(STAGE / 'manifest.json', backup / 'manifest.json')
    try:
        for item in data['files']:
            rel = item['relative']
            copy(safe(STAGE, rel), safe(game, rel))
            if digest(safe(game, rel)) != item['prepared']:
                raise ValueError(f'Installed hash mismatch: {rel}')
    except Exception:
        for item in data['files']:
            rel = item['relative']
            if item['original'] is None:
                safe(game, rel).unlink(missing_ok=True)
            else:
                copy(safe(backup, rel), safe(game, rel))
        raise
    print(f'Installed and verified {len(data["files"])} files. Backup: {backup}')


if __name__ == '__main__':
    main()
