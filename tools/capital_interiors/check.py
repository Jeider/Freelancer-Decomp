"""Validate the room using the installed Common/Thorn DLLs in a staged data tree."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
from prepare import ROOT, DATA, GAME, OUT, main as prepare
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    if Path(__file__).with_name('ARCHIVED').exists():
        raise SystemExit('Capital interiors are archived; this prototype check is obsolete. See README.txt.')
    prepare()
    stage=OUT/'test_data'
    for name in ('INTERFACE/capital_interiors.ini','UNIVERSE/ROOM/RH/capital_deck.ini',
                 'SCRIPTS/BASES/capital/rh_depot_mooring.thn'):
        target=stage/name
        target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(DATA/name,target)
    (stage/'test_ships.ini').write_text(''.join(
        f'[Ship]\nnickname = test_{name}\ntype = {kind}\nship_class = {label}\n'
        for name,kind,label in [('train','TRANSPORT',2),('cruiser','CRUISER',0),
                                 ('freighter','FREIGHTER',2),('fighter','FIGHTER',0)]))
    compiler,env=compiler_env()
    env['PATH']=str(GAME/'bin')+';'+env['PATH']
    exe=OUT/'check_native.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/std:c++17',
        '/D_ITERATOR_DEBUG_LEVEL=1','/D_CRT_SECURE_NO_WARNINGS',
        '/I'+str(ROOT/'src/include'),str(ROOT/'tools/capital_interiors/check_native.cpp'),
        '/Fo'+str(OUT/'check_native.obj'),'/Fe'+str(exe),'/link',
        str(ROOT/'src/obj/train_consist/Common.lib'),str(ROOT/'bin/DALib.lib'),
        str(ROOT/'bin/dacom.lib')],env=env,cwd=OUT,check=True)
    subprocess.run([str(exe),str(stage),str(ROOT/'src/obj/train_yard/Server/bin/Server.dll')],
                   env=env,cwd=OUT,check=True)

if __name__=='__main__':
    main()
