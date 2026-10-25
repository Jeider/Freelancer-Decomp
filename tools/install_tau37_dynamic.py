"""Install the rebuilt asteroid client with original Tau37 distance, with backups."""
import argparse
import datetime
import json
import re
from pathlib import Path

from install_hyperspace_tunnel import copy, digest, safe, stopped

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'src/obj/tau37_dynamic_install'
GENERATOR = 'Assets/Pythonlancer/universe/content/asteroid_definition.py'
FIELDS = tuple(f'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/tau37_ast{i}_asteroids.ini' for i in (1, 2, 3))
FILES = ('bin/freelancer.exe', 'bin/freelancer.pdb', *FIELDS, GENERATOR)


def configure(raw, generator=False):
    text = raw.decode('latin1')
    if generator:
        match = re.search(r"(?ms)^DYNAST_TAU37 = '''(.*?)'''", text)
        if not match:
            raise ValueError('Tau37 generator template not found')
        a, b = match.span(1)
    else:
        a, b = 0, len(text)
    body, count = re.subn(r'(?mi)^(placement_radius[ \t]*=[ \t]*)(1000|2000)(?:\.0+)?([ \t]*)(?=\r?$)',
                          r'\g<1>1000.000000\3', text[a:b])
    if count != 3:
        raise ValueError(f'Expected three Tau37 placement radii, got {count}')
    return (text[:a] + body + text[b:]).encode('latin1')



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if not args.apply:
        items = []
        for rel in FILES:
            if rel in FIELDS or rel == GENERATOR:
                target = safe(STAGE, rel)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(configure(safe(game, rel).read_bytes(), rel == GENERATOR))
            else:
                copy(safe(ROOT, rel), safe(STAGE, rel))
            before, after = digest(safe(game, rel)), digest(safe(STAGE, rel))
            if before != after:
                items.append(dict(relative=rel, original=before, prepared=after))
        data = dict(game=str(game), files=items,
                    scope='Original Tau37 placement radius 1000m and generator template; no added spawn guards; opaque dynamic asteroid meshes inside nebulae')
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
    backup = safe(game, 'BACKUP/codex_tau37_dynamic_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
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
