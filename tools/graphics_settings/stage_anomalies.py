"""Stage the two new preference strings, current binaries and anomaly shader."""
from pathlib import Path
import importlib.util
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
STAGE=ROOT/'src/obj/anomaly_settings_install'
spec=importlib.util.spec_from_file_location('strings',ROOT/'tools/targeting_hud/stage_interface_strings.py')
strings=importlib.util.module_from_spec(spec)
spec.loader.exec_module(strings)
strings.ROWS=[row for row in strings.ROWS if row[0] in ('GraphicsWeaponLights','GraphicsAnomalies')]
strings.STAGE=STAGE
strings.main()

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest().upper() if p.exists() else None

for name in ('freelancer.exe','freelancer.pdb','Common.dll','Common.pdb'):
    target=STAGE/'bin'/name
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/'src/obj/train_courier/rpg1/bin'/name,target)
shader='DATA_EXTRA/SHADERS/jumphole_lens.hlsl'
(STAGE/shader).parent.mkdir(parents=True,exist_ok=True)
shutil.copy2(ROOT/shader,STAGE/shader)
paths=['bin/'+name for name in ('freelancer.exe','freelancer.pdb','Common.dll','Common.pdb')]
paths += [shader,'Assets/Pythonlancer/text/static.py','EXE/NameResources.dll','RESOURCES_ENG/NameResources.dll']
manifest=dict(game=str(GAME),files=[dict(relative=p,original=digest(GAME/p),prepared=digest(STAGE/p)) for p in paths],dependencies=[])
(STAGE/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
installer=(ROOT/'tools/graphics_settings/install.ps1').read_text()
start=installer.index('$allowed=@(')
end=installer.index('\n',start)
installer=installer[:start]+'$allowed=@('+','.join("'"+p+"'" for p in paths)+')'+installer[end:]
installer=installer.replace('Count -ne 7','Count -ne 8')
(STAGE/'install.ps1').write_text(installer,encoding='utf-8')
print(STAGE/'install.ps1')
