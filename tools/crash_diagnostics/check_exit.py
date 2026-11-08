"""Reproduce the observed CRT exit-order crash with the actual light registry."""
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
OUT=ROOT/'src/obj/crash_diagnostics'

PREFIX=r'''
#define NOMINMAX
#include <windows.h>
#include <cstdlib>
#include <cstdio>
#include <unordered_map>
#include "cockpit_effect_brightness.h"
struct ICamera {};struct FSpaceCamera:ICamera {};
FSpaceCamera* GetFirstPersonSpaceCamera(){return nullptr;}
ICamera* AsCamera(FSpaceCamera* p){return p;}
'''
MAIN=r'''
static int light;
void Teardown(){CockpitEffectBrightness::Forget(&light);puts("PASS: light cleanup after CRT registry destruction");}
int main(){
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 // main.cpp registers this before any lights/effects are created.
 atexit(Teardown);
 {CockpitEffectBrightness::CreationScope scope(CockpitEffectBrightness::Kind::Weapon);
  CockpitEffectBrightness::Register(&light);}
 // Returning destroys lazily initialized statics before the earlier atexit handler.
 return 0;
}
'''
source=(ROOT/'src/freelancer/Client/cockpit_effect_brightness.cpp').read_text()
source='\n'.join(line for line in source.splitlines() if not line.startswith('#include'))
compiler,env=compiler_env();OUT.mkdir(parents=True,exist_ok=True)
cpp=OUT/'exit_order.cpp';cpp.write_text(PREFIX+source+MAIN)
exe=OUT/'exit_order.exe'
subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/O2','/std:c++17',
    '/I'+str(ROOT/'src/freelancer/Client'),str(cpp),'/Fo'+str(OUT/'exit_order.obj'),'/Fe'+str(exe)],env=env,cwd=ROOT,check=True)
result=subprocess.run([str(exe)],cwd=ROOT,capture_output=True,text=True)
print(result.stdout,end='')
print(f'Exit code: {result.returncode & 0xffffffff:08x}')
if result.returncode in (0xc0000005,-1073741819):
    print('CONFIRMED: current registry crashes during early-registered client atexit teardown')
else:result.check_returncode()
