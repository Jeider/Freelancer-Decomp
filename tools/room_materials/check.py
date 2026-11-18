"""Build and run real RP9/GPU material integration checks."""
import os
import argparse
import subprocess
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--startup-build',action='store_true',help='Use the current DLSS-enabled startup build objects')
parser.add_argument('--objects',help='Override RP9 object directory for an isolated build')
args=parser.parse_args()
objects='out/base_neural/on/obj/RP9' if args.startup_build else 'src/obj/RP9/Release'
if args.objects: objects=args.objects
defines='/DFREELANCER_DLSS5 ' if args.startup_build else ''
OUT=ROOT/'src/obj/room_materials'
OUT.mkdir(parents=True,exist_ok=True)
build=OUT/'check.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
 'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
 'cl /nologo /EHsc /MD /O2 /std:c++17 /DRP_DIRECT3D9 /D_ITERATOR_DEBUG_LEVEL=1 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX '
 +defines+'/Isrc/RP9 /Isrc/include tools/room_materials/check_route.cpp /Fosrc/obj/room_materials/check.obj /Febin/room_material_check.exe '
 +f'{objects}/RP9.obj {objects}/RP9Ex.obj {objects}/Mgsdb.obj '
 '/link /LTCG /LIBPATH:bin dacom.lib d3d9.lib ddraw.lib version.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" '
 '"C:/DXSDK_Jun10/Lib/x86/DxErr.lib" legacy_stdio_definitions.lib user32.lib\n')
env=dict(os.environ,TEMP=str(OUT),TMP=str(OUT))
with (OUT/'gpu_build.log').open('wb') as log:
    built=subprocess.run(['cmd','/c',str(build)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
if built.returncode:
    print('GPU build needs investigation; details saved to',OUT/'gpu_build.log');sys.exit(1)
env.update(FREELANCER_SHADER_CACHE_DIR=str(OUT/'shader_cache'))
with (OUT/'gpu_result.log').open('wb') as log:
    result=subprocess.run([str(ROOT/'bin/room_material_check.exe')],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT,creationflags=subprocess.CREATE_NO_WINDOW)
print('PASS GPU material checks' if not result.returncode else 'GPU check needs investigation; details saved',OUT/'gpu_result.log')
sys.exit(0 if not result.returncode else 1)
