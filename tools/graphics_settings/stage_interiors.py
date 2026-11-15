"""Stage interior quality UI/resources and freshly built binaries, without installing."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
menu_only = '--menu-only' in sys.argv
space = '--space' in sys.argv
presets = '--presets' in sys.argv
STAGE = ROOT/('src/obj/graphics_menu_install' if menu_only else 'src/obj/interior_settings_install')
if space: STAGE=ROOT/'src/obj/space_settings_install'
if presets: STAGE=ROOT/'src/obj/graphics_presets_install'
spec = importlib.util.spec_from_file_location('strings', ROOT/'tools/targeting_hud/stage_interface_strings.py')
strings = importlib.util.module_from_spec(spec)
spec.loader.exec_module(strings)
names = ('GraphicsStandard', 'GraphicsAdditional', 'GraphicsImageTab', 'GraphicsDisplayTab') if menu_only else ('GraphicsInteriors',)
if space: names=('GraphicsSurfaceRelief','GraphicsHighlights','GraphicsReflections')
if presets: names=('GraphicsAllOff',)
strings.ROWS = [row for row in strings.ROWS if row[0] in names]
strings.STAGE = STAGE
strings.main()

paths = []
for name in ('freelancer.exe', 'freelancer.pdb', 'Common.dll', 'Common.pdb', 'RP9.dll', 'RP9.pdb'):
    if menu_only and not name.startswith('freelancer.'): continue
    if presets and name.startswith('RP9.'): continue
    relative = 'bin/'+name
    target = STAGE/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT/'src/obj/train_courier/rpg1/bin'/name, target)
    paths.append(relative)
if space:
    relative='DATA_EXTRA/SHADERS/surface_material.hlsl'
    (STAGE/relative).parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/relative,STAGE/relative)
    paths.append(relative)
paths += ['Assets/Pythonlancer/text/static.py', 'EXE/NameResources.dll', 'RESOURCES_ENG/NameResources.dll']

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.exists() else None

manifest = dict(game=str(GAME), files=[dict(relative=p, original=digest(GAME/p), prepared=digest(STAGE/p))
                                   for p in paths], dependencies=[])
(STAGE/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
installer = (ROOT/'tools/graphics_settings/install.ps1').read_text()
begin = installer.index('$allowed=@(')
end = installer.index('\n', begin)
installer = installer[:begin]+'$allowed=@('+','.join(repr(p) for p in paths)+')'+installer[end:]
installer = installer.replace('Count -ne 7', 'Count -ne '+str(len(paths)))
(STAGE/'install.ps1').write_text(installer, encoding='utf-8')
print(STAGE/'install.ps1')
