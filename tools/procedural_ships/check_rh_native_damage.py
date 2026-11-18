"""Load actual CMP/animation through the staged EngBase DLL, without game startup."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'src/obj/ship_damage/native_check'
MODEL=ROOT/'out/ship_design/rh_elite/rh_pir_elite/damage_refinement/assets/rh_pir_elite.cmp'
DLL=ROOT/'src/obj/ship_damage/bin/EngBase.dll'
if not DLL.exists():DLL=GAME/'bin/EngBase.dll'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    compiler,env=compiler_env();env['INCLUDE']=str(ROOT/'src/include')+';'+env['INCLUDE']
    env['LIB']=str(ROOT/'bin')+';'+env['LIB'];env['PATH']=str(GAME/'bin')+';'+env['PATH']
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc',
        str(ROOT/'tools/procedural_ships/check_rh_native_damage.cpp'),'/Fecheck.exe',
        '/link','DALib.lib','dacom.lib'],cwd=OUT,env=env,check=True)
    ini=OUT/'dacom.ini'
    ini.write_text('[DACOM]\nIgnoreDACOMEnv = true\nDllPath = '+str(GAME/'bin')+'\\\n'
        '[Libraries]\nReadFile.dll\nx86math.dll\n'+str(DLL)+'\n[Engine]\nAnimation\nHardpoint\n')
    report=[]
    for name,model in [('installed',GAME/'DATA/ships/rheinland/rh_pir_elite/rh_pir_elite.cmp'),('revised',MODEL)]:
        result=subprocess.run([str(OUT/'check.exe'),str(ini),str(model)],cwd=OUT,env=env,
            capture_output=True,timeout=30)
        (OUT/(name+'.log')).write_bytes(result.stdout+result.stderr)
        text=result.stdout.decode(errors='replace');print(name,text)
        if result.returncode:print(result.stderr.decode(errors='replace'))
        result.check_returncode()
        assert str(DLL).lower() in text.lower(),'Test loaded another EngBase DLL'
        assert text.count('PASS')==5
        report.append(dict(model=str(model),sha256=hashlib.sha256(model.read_bytes()).hexdigest(),passes=5))
    (MODEL.parents[1]/'native_check.json').write_text(json.dumps(dict(dll_sha256=hashlib.sha256(DLL.read_bytes()).hexdigest(),models=report),indent=2))


if __name__=='__main__':main()
