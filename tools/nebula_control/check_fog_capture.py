"""Standalone GPU test of the bounded three-stage capture. Never launches the game."""
from pathlib import Path
import json
import hashlib
import subprocess
from PIL import Image
from build_asf_hq import compiler_env

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/physical_order/trace'
PROBE=OUT/'capture_probe'

def main():
    PROBE.mkdir(parents=True,exist_ok=True)
    compiler,env=compiler_env()
    env['INCLUDE']=';'.join(p for p in env['INCLUDE'].split(';') if 'DXSDK' not in p.upper())+';C:/DXSDK_Jun10/Include'
    env['PATH']=str(ROOT/'bin')+';D:/Games/FL_MOD/bin;'+env['PATH']
    command=[str(compiler/'cl.exe'),'/nologo','/EHsc','/MD','/O2','/std:c++17','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS',
             '/I'+str(ROOT/'src/RP9'),str(ROOT/'tools/nebula_control/check_fog_capture.cpp'),
             '/Fo'+str(PROBE/'capture.obj'),'/Fe'+str(PROBE/'capture.exe'),
             '/link','d3d9.lib','user32.lib','C:/DXSDK_Jun10/Lib/x86/d3dx9.lib']
    for name,cmd in [('capture_build',command),('capture_check',[str(PROBE/'capture.exe'),str(PROBE)])]:
        result=subprocess.run(cmd,cwd=PROBE,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
        (OUT/(name+'.log')).write_bytes(result.stdout)
        print(result.stdout.decode(errors='replace'),flush=True)
        result.check_returncode()
    folder=PROBE/'Freelancer-Decomp/Diagnostics/asteroid_fog_capture'
    files=list(folder.glob('*.png'));assert len(files)==6
    for frame in range(2):
        for stage,rgb in [('opaque',(255,0,0)),('volume',(0,255,0)),('present',(0,0,255))]:
            with Image.open(folder/f'{frame}_{stage}.png') as im:
                assert im.convert('RGB').getextrema()==tuple((v,v) for v in rgb),(frame,stage,im.getextrema())
    assert len((folder/'capture.txt').read_text().splitlines())==6
    (OUT/'capture_checks.json').write_text(json.dumps({'passed':True,'captures':6,'frames':2,'correct_stage_colors':True,'default_off':True,'state_preserved':True,
        'header':hashlib.sha256((ROOT/'src/RP9/RP9FogCapture.h').read_bytes()).hexdigest()},indent=2))
    print('PASS six images with correct independent stage colors')

if __name__=='__main__':main()
