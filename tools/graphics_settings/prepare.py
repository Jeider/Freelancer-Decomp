"""Stage verified binaries and shader; leave installed INIs and saves untouched."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import shutil
import sys

root=Path(__file__).resolve().parents[2]
game=Path('D:/games/FL_MOD')
stage=root/'src/obj/graphics_settings_install'/datetime.now().strftime('%Y%m%d_%H%M%S')
stage.mkdir(parents=True)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.exists() else None

client_common_only='--client-common-only' in sys.argv
files=[]
for relative in ('bin/freelancer.exe','bin/freelancer.pdb','bin/Common.dll','bin/Common.pdb',
                 'bin/RP9.dll','bin/RP9.pdb','DATA_EXTRA/SHADERS/surface_material.hlsl'):
    if client_common_only and relative not in ('bin/freelancer.exe','bin/freelancer.pdb','bin/Common.dll','bin/Common.pdb'):
        continue
    if relative.startswith('DATA_EXTRA'):
        source=root/relative
    else:
        build='ship_trader_radar_bin' if Path(relative).name.startswith('freelancer.') else 'graphics_settings_bin'
        source=root/'src/obj'/build/Path(relative).name
    target=stage/relative; target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)
    files.append(dict(relative=relative,original=digest(game/relative),prepared=digest(target)))

dependencies=['bin/DALib.dll','bin/dacom.dll','bin/zlib.dll','bin/imeui.dll','bin/alchemy.dll',
              'DATA_EXTRA/SHADERS/scene_smaa.hlsl','DATA_EXTRA/SHADERS/SMAA/SMAA.hlsl',
              'DATA_EXTRA/SHADERS/SMAA/AreaTexDX9.dds','DATA_EXTRA/SHADERS/SMAA/SearchTex.dds']
manifest=dict(game=str(game),files=files,dependencies=[dict(relative=p,sha256=digest(game/p)) for p in dependencies])
assert all(item['sha256'] for item in manifest['dependencies']), 'Missing installed rendering dependency'
(stage/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
installer=(root/'tools/graphics_settings/install.ps1').read_text()
if client_common_only:
    begin=installer.index('$allowed=@(');end=installer.index('\n',begin)
    installer=installer[:begin]+"$allowed=@('bin/freelancer.exe','bin/freelancer.pdb','bin/Common.dll','bin/Common.pdb')"+installer[end:]
    installer=installer.replace('Count -ne 7','Count -ne 4')
(stage/'install.ps1').write_text(installer)
print(stage/'install.ps1')
