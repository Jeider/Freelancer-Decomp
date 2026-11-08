"""Compile and run the train in the actual native engine, using staged files only."""
from pathlib import Path
import os
import subprocess
import sys
import hashlib
import json
import shutil
import argparse
import re
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
OUT=ROOT/'src/obj/train_consist'
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scenario',choices=['normal','overload','upright','remote','handling','tail','cruise','docking'])
    args_cli=parser.parse_args()
    constants=Path('D:/games/FL_MOD/DATA/Constants.ini')
    engine_config=Path('D:/games/FL_MOD/DATA/EQUIPMENT/engine_equip.ini')
    for key,expected in [('CRUISING_SPEED',600),('CRUISE_ACCEL_TIME',10),('CRUISE_DRAG',600)]:
        match=re.search(r'^'+key+r'\s*=\s*([\d.]+)',constants.read_text(),re.M)
        assert match and float(match[1])==expected,'Update native cruise fixture for '+key
    engine=re.search(r'^nickname\s*=\s*ge_t_engine_01\s*$([^\[]*)',engine_config.read_text(),re.M)[1]
    for key,expected in [('max_force',240000),('linear_drag',3000),('cruise_charge_time',7)]:
        assert float(re.search(r'^'+key+r'\s*=\s*([\d.]+)',engine,re.M)[1])==expected,key
    compiler,env=compiler_env()
    for ext in ['3db','sur']:
        shutil.copy2(Path('D:/games/FL_MOD/DATA/Equipment/models/commodities/crates')/('pod_grey.'+ext),ROOT/'out/train_consist'/('pod_grey.'+ext))
    env['PATH']=str(ROOT/'bin')+';'+env['PATH']
    (OUT/'check_dacom.ini').write_text('[DACOM]\nIgnoreDACOMEnv = true\nDllPath = '+str(ROOT/'bin')+'\\\n\n[Libraries]\nReadFile.dll\nx86math.dll\nEngBase.dll\nsystem.dll\n\n[System]\n\n[Engine]\nHardpoint\nAnimation\n')
    args=[str(compiler/'cl.exe'),'/nologo','/std:c++17','/W4','/EHsc','/O2','/MD','/D_ITERATOR_DEBUG_LEVEL=1',
          '/D_CRT_SECURE_NO_WARNINGS','/I'+str(ROOT/'src/include'),str(Path(__file__).with_name('check.cpp')),
          '/Fecheck.exe','/link','/LIBPATH:'+str(ROOT/'bin'),'Common.lib','DALib.lib','dacom.lib']
    with (OUT/'check_compile.log').open('wb') as log:
        result=subprocess.run(args,cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:print((OUT/'check_compile.log').read_text(errors='replace'))
    result.check_returncode()
    with (OUT/'check.log').open('wb') as log:
        count=json.loads((ROOT/'out/train_consist/data.json').read_text())['wagons']
        for mode in ([args_cli.scenario] if args_cli.scenario else ['normal','overload','upright','remote','handling','tail','cruise','docking']):
            r=subprocess.run([str(OUT/'check.exe'),str(ROOT/'out/train_consist'),str(count),mode],cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT)
            if r.returncode:break
    print((OUT/'check.log').read_text(errors='replace'))
    r.check_returncode()
    checked=[OUT/'Common.dll',ROOT/'out/train_consist/train_consist.cmp',ROOT/'out/train_consist/train_consist.sur',
             constants,engine_config,Path(__file__),Path(__file__).with_name('check.cpp'),Path(__file__).with_name('check_dock.h')]
    if not args_cli.scenario:
        (OUT/'check.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in checked},indent=2))
if __name__=='__main__':main()
