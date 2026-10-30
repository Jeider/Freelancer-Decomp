"""Prepare only the radar client executable/PDB, checking installed DLL imports."""
from pathlib import Path
import datetime
import json
import shutil
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/games/FL_MOD')
BIN=ROOT/'src/obj/health_equipment/bin'
sys.path.insert(0,str(ROOT/'tools/flight_actions'))
from prepare_install import PE, directory, exports, string, digest

pe=PE(BIN/'freelancer.exe')
dependencies=[]
d=directory(pe,1)
while d:
    lookup,_,_,name,first=struct.unpack('<5I',pe.read(d,20))
    if not name: break
    dll=string(pe,name).decode('ascii'); installed=GAME/'bin'/dll
    if installed.exists():
        named,ordinal=exports(PE(installed)); thunk=lookup or first
        while (item:=pe.u32(thunk)):
            symbol=item&0xffff if item&0x80000000 else string(pe,item+2)
            if symbol not in (ordinal if isinstance(symbol,int) else named):
                raise ValueError(f'Missing installed import: {dll}: {symbol!r}')
            thunk+=4
        dependencies.append(dict(relative='bin/'+dll,sha256=digest(installed)))
    elif (ROOT/'bin'/dll).exists():
        raise ValueError('Missing game DLL: '+dll)
    d+=20
stage=ROOT/'src/obj/radar_client_install'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
files=[]
for name in ('freelancer.exe','freelancer.pdb'):
    relative='bin/'+name; target=stage/relative
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(BIN/name,target)
    original=GAME/relative
    files.append(dict(relative=relative,original=digest(original) if original.exists() else None,prepared=digest(target)))
(stage/'manifest.json').write_text(json.dumps(dict(game=str(GAME),files=files,dependencies=dependencies),indent=2)+'\n')
script=(ROOT/'tools/flight_actions/install.ps1').read_text()
a=script.index('$allowed = @(');b=script.index('\nforeach ($process',a)
script=script[:a]+"$allowed = @('bin/freelancer.exe', 'bin/freelancer.pdb')"+script[b:]
script=script.replace('codex_flight_actions_','codex_radar_client_').replace(
    'Installed flight actions client, action config and four icons','Installed radar client filter')
(stage/'install.ps1').write_text(script)
print(f'Prepared client/PDB; imports verified against {len(dependencies)} game DLLs: {stage}')
