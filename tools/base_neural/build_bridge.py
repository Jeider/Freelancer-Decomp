"""Build x86 DX11 adapter and GPU probe; uses pinned Feeder 0.7.0 ReShade SDK."""
from pathlib import Path
import argparse
import subprocess

ROOT=Path(__file__).resolve().parents[2]
SDK=ROOT/'out/base_neural/reference/DLSS5-Feeder-0.7.0/external/reshade/include'
VC=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvarsall.bat')

def q(p):
    return '"'+str(p)+'"'

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--enabled',choices=['0','1'],default='1')
    a=ap.parse_args()
    if a.enabled=='0':
        print('FreelancerDlss5=0: no adapter or helper dependencies built')
        return
    if not (SDK/'reshade.hpp').is_file():
        raise SystemExit('Missing pinned SDK: run tools/base_neural/prepare.py --fetch')
    out=ROOT/'out/base_neural/on/bin'
    obj=ROOT/'out/base_neural/on/obj/bridge'
    out.mkdir(parents=True,exist_ok=True);obj.mkdir(parents=True,exist_ok=True)
    flags='/nologo /std:c++20 /EHsc /O2 /MD /W3 /DWIN32_LEAN_AND_MEAN /DFREELANCER_DLSS5 /I'+q(ROOT/'src/include')+' /I'+q(ROOT/'src/BaseNeuralBridge')+' /I'+q(SDK)+' /I'+q(SDK.parents[1]/'imgui')
    commands=['@echo off','call '+q(VC)+' amd64_x86 >nul','if errorlevel 1 exit /b 1',
              'cd /d '+q(obj),
              'cl '+flags+' /LD '+q(ROOT/'src/BaseNeuralBridge/bridge.cpp')+' '+q(ROOT/'src/BaseNeuralBridge/feed_client.cpp')+
              ' /link /OUT:'+q(out/'fl_base_neural.addon32')+' d3d11.lib dxgi.lib d3dcompiler.lib user32.lib advapi32.lib',
              'if errorlevel 1 exit /b 1',
              'cl '+flags+' '+q(ROOT/'tools/base_neural/probe_feed.cpp')+' '+q(ROOT/'src/BaseNeuralBridge/feed_client.cpp')+
              ' /link /OUT:'+q(out/'probe_feed.exe')+' d3d11.lib dxgi.lib user32.lib',
              'if errorlevel 1 exit /b 1',
              'cl '+flags+' /I'+q(ROOT/'src/RP9')+' /I"C:/DXSDK_Jun10/Include" '+q(ROOT/'tools/base_neural/probe_wrapper.cpp')+
              ' /link /OUT:'+q(out/'probe_wrapper.exe')+' user32.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib"',
              'if errorlevel 1 exit /b 1',
              'cl '+flags+' '+q(ROOT/'tools/base_neural/probe_flow.cpp')+
              ' /link /OUT:'+q(out/'probe_flow.exe')+' d3d11.lib d3dcompiler.lib',
              'if errorlevel 1 exit /b 1',
              'cl '+flags+' /LD '+q(ROOT/'tools/base_neural/probe_overlay.cpp')+
              ' /link /OUT:'+q(out/'overlay_check.addon32')+' user32.lib',
              'exit /b %errorlevel%']
    batch=obj/'build.cmd';batch.write_text('\n'.join(commands)+'\n',encoding='utf-8')
    log=obj/'build.log'
    with log.open('wb') as f:r=subprocess.run(['cmd','/d','/c',str(batch)],stdout=f,stderr=subprocess.STDOUT,cwd=ROOT)
    if r.returncode:print(log.read_text(encoding='utf-8',errors='replace')[-14000:])
    r.check_returncode();print('PASS x86 adapter and GPU probe')

if __name__=='__main__':main()
