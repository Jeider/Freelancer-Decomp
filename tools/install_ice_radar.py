"""Stage/install the crystal ice material and optional radar with verified backups."""
import argparse
import datetime
import json
import re
import subprocess
from pathlib import Path

from install_hyperspace_tunnel import copy, digest, safe

ROOT = Path(__file__).resolve().parents[1]
STAGE = ROOT / 'src/obj/ice_radar_install'
PORT = 'bin/port.ini'
HUD = 'DATA/INTERFACE/hud.ini'
PAYLOAD = ('bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/Shading.dll',
           'bin/Shading.pdb', 'bin/RP9.dll', 'bin/RP9.pdb',
           'DATA_EXTRA/SHADERS/surface_material.hlsl', 'DATA_EXTRA/TEXTURES/ice_layers.dds')
ALLOWED = {*PAYLOAD, PORT, HUD}


def stopped(game):
    # Beta is a separate installation and does not lock these files.
    result = subprocess.run(['powershell', '-NoProfile', '-Command',
        "Get-CimInstance Win32_Process -Filter \"name='Freelancer.exe'\" | "
        'Select-Object -ExpandProperty ExecutablePath | ConvertTo-Json -Compress'],
        capture_output=True, text=True, check=True)
    paths = json.loads(result.stdout) if result.stdout.strip() else []
    if isinstance(paths, str):
        paths = [paths]
    target = safe(game, 'bin/freelancer.exe')
    if any(not p or Path(p).resolve() == target for p in paths):
        raise RuntimeError('Close FL_MOD before installation. No process was stopped.')


def merge(raw, block, begin, end, section=None):
    if raw.count(begin) or raw.count(end):
        if raw.count(begin) != 1 or raw.count(end) != 1 or raw.index(end) < raw.index(begin):
            raise ValueError('Ambiguous configuration markers')
        return raw[:raw.index(begin)] + block + raw[raw.index(end) + len(end):]
    if section is None:
        if re.search(rb'(?mi)^\[Radar\]', raw):
            raise ValueError('Existing unmarked radar configuration needs reconciliation')
        return raw.rstrip() + b'\r\n\r\n' + block + b'\r\n'
    headers = list(re.finditer(rb'(?mi)^\[' + re.escape(section) + rb'\][ \t]*\r?\n', raw))
    if len(headers) != 1:
        raise ValueError('Expected exactly one Render section')
    if re.search(rb'(?mi)^ice_(shader|depth|frost|transmission)[ \t]*=', raw):
        raise ValueError('Existing unmarked ice configuration needs reconciliation')
    offset = headers[0].end()
    return raw[:offset] + block + b'\r\n' + raw[offset:]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    parser.add_argument('--radar-template', type=Path)
    parser.add_argument('--radar-enabled', choices=('keep', 'true', 'false'), default='keep')
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if not args.apply:
        if args.radar_template is None:
            parser.error('--radar-template is required for staging')
        reference = (ROOT / PORT).read_bytes()
        begin, end = b'; BEGIN CRYSTAL ICE', b'; END CRYSTAL ICE'
        block = reference[reference.index(begin):reference.index(end) + len(end)]
        prepared = {PORT: merge(safe(game, PORT).read_bytes(), block, begin, end, b'Render')}
        radar = args.radar_template.read_bytes()
        begin, end = b'; BEGIN HUD RADAR', b'; END HUD RADAR'
        block = radar[radar.index(begin):radar.index(end) + len(end)]
        if not re.search(rb'(?mi)^enabled[ \t]*=[ \t]*false\b', block):
            raise ValueError('Radar foundation must initially be disabled')
        original_hud = safe(game, HUD).read_bytes()
        enabled = args.radar_enabled
        if enabled == 'keep':
            existing = re.search(rb'(?mis)^\[Radar\][^\[]*?^enabled[ \t]*=[ \t]*(true|false)\b', original_hud)
            enabled = existing[1].decode('ascii').lower() if existing else 'false'
        block = re.sub(rb'(?mi)^(enabled[ \t]*=[ \t]*)false\b', lambda m: m[1] + enabled.encode('ascii'), block)
        prepared[HUD] = merge(original_hud, block, begin, end)
        for rel, content in prepared.items():
            target = safe(STAGE, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        for rel in PAYLOAD:
            copy(safe(ROOT, rel), safe(STAGE, rel))
        items = [dict(relative=rel, original=digest(safe(game, rel)), prepared=digest(safe(STAGE, rel)))
                 for rel in sorted(ALLOWED) if digest(safe(game, rel)) != digest(safe(STAGE, rel))]
        (STAGE / 'manifest.json').write_text(json.dumps(dict(game=str(game), files=items), indent=2))
        print(f'Prepared {len(items)} changed files; game untouched.')
        return
    stopped(game)
    data = json.loads((STAGE / 'manifest.json').read_text())
    if Path(data['game']).resolve() != game:
        raise ValueError('Game differs from staging root')
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel not in ALLOWED or rel in seen:
            raise ValueError(f'Unexpected path: {rel}')
        seen.add(rel)
        if digest(safe(game, rel)) != item['original'] or digest(safe(STAGE, rel)) != item['prepared']:
            raise ValueError(f'File changed since staging: {rel}')
    if not data['files']:
        print('Already installed.')
        return
    backup = safe(game, 'BACKUP/codex_ice_radar_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
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
