"""Stage/apply independent travel quality and the scrollable preferences page."""
from pathlib import Path
import importlib.util
import json
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import install_tradelane_visual as installer
from install_hyperspace_tunnel import copy, digest, safe

STAGE=ROOT/'out/travel_settings/install'
GAME=Path('D:/Games/FL_MOD')
BIN=ROOT/'out/base_neural/on/bin'
PAYLOAD=('bin/freelancer.exe','bin/freelancer.pdb','bin/Common.dll','bin/Common.pdb',
         'DATA_EXTRA/SHADERS/tradelane_corridor.hlsl','Assets/Pythonlancer/text/static.py',
         'EXE/NameResources.dll','RESOURCES_ENG/NameResources.dll')

def stage():
    for binary, dependencies in (
        ('freelancer.exe', ['src/freelancer/Client/nn_preferences_graphics.cpp','src/freelancer/Client/nn_preferences.h',
          'src/freelancer/Client/flplusplus.cpp','src/freelancer/Client/gate_tunnel.cpp','src/freelancer/Client/jump_cloud.inl',
          'src/freelancer/Client/tradelane_visual.cpp','src/include/graphics_settings.h','src/include/travel_quality.h']),
        ('Common.dll',['src/Common/graphics_settings.cpp','src/include/graphics_settings.h'])):
        if any((ROOT/p).stat().st_mtime>(BIN/binary).stat().st_mtime for p in dependencies):
            raise RuntimeError('Rebuild '+binary+' before staging')
    spec=importlib.util.spec_from_file_location('travel_strings',ROOT/'tools/targeting_hud/stage_interface_strings.py')
    strings=importlib.util.module_from_spec(spec);spec.loader.exec_module(strings)
    strings.ROWS=[row for row in strings.ROWS if row[0] in ('GraphicsTradeLane','GraphicsHyperspace')]
    strings.STAGE=STAGE;strings.main()
    items=[]
    for rel in PAYLOAD:
        if rel.startswith('bin/'):
            copy(BIN/Path(rel).name,safe(STAGE,rel))
        elif rel.startswith('DATA_EXTRA/'):
            copy(safe(ROOT,rel),safe(STAGE,rel))
        before,after=digest(safe(GAME,rel)),digest(safe(STAGE,rel))
        if before!=after:items.append(dict(relative=rel,original=before,prepared=after))
    (STAGE/'manifest.json').write_text(json.dumps(dict(game=str(GAME),files=items,
        scope='Independent travel quality, preferences scroll, RU/EN labels; no gameplay DATA or user preference writes'),indent=2))
    print(f'Prepared {len(items)} changed files; game untouched.')

if __name__=='__main__':
    if '--apply' in sys.argv or '--restore' in sys.argv:
        installer.STAGE=STAGE;installer.PAYLOAD=PAYLOAD;installer.main()
    else:
        stage()
