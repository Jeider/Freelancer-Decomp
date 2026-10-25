"""Stage the first Health install without modifying the game or existing artwork."""
import hashlib
import json
import sys
from pathlib import Path

repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(repo / 'tools'))
from generate_station_lods import read_tree
from make_targeting_icons import generate, mesh_library

game = Path('D:/games/FL_MOD')
stage = repo / 'src/obj/health_hud/install'
interface = game / 'DATA/INTERFACE'
icon = interface / 'HUD/HUD_health.3db'
if icon.exists():
    raise SystemExit('Health icon already exists; preserve the current artwork instead of regenerating it.')
ini = (interface / 'hud.ini').read_bytes()
if b'[health]' in ini.lower():
    raise SystemExit('Health section already exists; review its configuration before staging.')
shared = mesh_library(read_tree((interface / 'interface.generic.vms').read_bytes())[1][0])
data, _, report = generate(interface / 'HUD/HUD_playershipinfo.3db', shared, 'HUD_health')
block = (repo / 'tools/targeting_hud/health_block.ini').read_text().replace('\n', '\r\n').encode('ascii')
payloads = {
    'bin/freelancer.exe': (repo / 'bin/freelancer.exe').read_bytes(),
    'bin/freelancer.pdb': (repo / 'bin/freelancer.pdb').read_bytes(),
    'DATA/INTERFACE/HUD/HUD_health.3db': data,
    'DATA/INTERFACE/hud.ini': ini.rstrip(b'\r\n') + b'\r\n\r\n' + block,
}
digest = lambda blob: hashlib.sha256(blob).hexdigest().upper()
files = []
for name, blob in payloads.items():
    destination = stage / name
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(blob)
    original = game / name
    files.append(dict(relative=name, original=digest(original.read_bytes()) if original.exists() else None,
                      prepared=digest(blob)))
dependencies = ['DATA/INTERFACE/HUD/hud_target2.cmp', 'DATA/INTERFACE/interface.generic.vms']
dependencies += [f'DATA/INTERFACE/HUD/HUD_weaponsgroup{i}.3db' for i in range(1, 4)]
manifest = dict(game=str(game), files=files, dependencies=[dict(relative=name, sha256=digest((game / name).read_bytes()))
                                                        for name in dependencies], icon=report)
(stage / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print('Staged client, standalone Health icon and HUD configuration:', stage)
