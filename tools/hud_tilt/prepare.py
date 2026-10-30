"""Prepare a reviewed, hash-guarded installer in the workspace; do not modify the game."""
from datetime import datetime
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil

root = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--client-only', action='store_true', help='Preserve the installed renderer, shader and port.ini')
mode.add_argument('--settings', action='store_true', help='Update client and retire the experimental port.ini angle')
args = parser.parse_args()
game = Path('D:/games/FL_MOD')
stage = root / 'src/obj/hud_tilt_install' / datetime.now().strftime('%Y%m%d_%H%M%S')
stage.mkdir(parents=True)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.exists() else None

files = []
payload = ('bin/freelancer.exe','bin/freelancer.pdb') if args.client_only else ('bin/freelancer.exe','bin/freelancer.pdb','bin/RP9.dll','bin/RP9.pdb','DATA_EXTRA/SHADERS/hud_tilt.hlsl','bin/port.ini')
if args.settings:
    payload = ('bin/freelancer.exe','bin/freelancer.pdb','bin/port.ini')
for relative in payload:
    destination = stage / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    if relative == 'bin/port.ini':
        data = (game / relative).read_bytes()
        section = re.search(rb'(?mi)^\[Render\][ \t]*\r?\n', data)
        assert section, 'Render section missing'
        end = re.search(rb'(?m)^\[', data[section.end():])
        stop = section.end() + end.start() if end else len(data)
        body = data[section.end():stop]
        # Angle now belongs to user PerfOptions.ini; preserve all other settings.
        body = re.sub(rb'(?mi)^hud_tilt_degrees[ \t]*=[^\r\n]*(?:\r?\n|$)', b'', body)
        body = re.sub(rb'(?m)^; Static perspective of flight HUD side panels; 0 restores flat HUD\.\r?\n', b'', body)
        destination.write_bytes(data[:section.end()] + body + data[stop:])
    else:
        source = root / relative if relative.startswith('DATA_EXTRA') else root / 'src/obj/ship_trader_radar_bin' / Path(relative).name
        shutil.copy2(source, destination)
    files.append(dict(relative=relative, original=digest(game/relative), prepared=digest(destination)))
dependencies = ['bin/Common.dll','bin/DALib.dll','bin/dacom.dll','bin/zlib.dll','bin/imeui.dll','bin/alchemy.dll','DATA_EXTRA/SHADERS/common.hlsli']
assert digest(game / dependencies[-1]) == digest(root / dependencies[-1]), 'Installed shader helper differs from the compiled helper'
if args.client_only or args.settings:
    dependencies += ['bin/RP9.dll','DATA_EXTRA/SHADERS/hud_tilt.hlsl']
manifest = dict(game=str(game), files=files, dependencies=[dict(relative=p,sha256=digest(game/p)) for p in dependencies])
assert all(x['sha256'] for x in manifest['dependencies'])
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
shutil.copy2(root/'tools/hud_tilt/install.ps1',stage/'install.ps1')
print(stage/'install.ps1')
