"""Build and run real RP9/GPU material integration checks."""
import os
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/room_materials'
OUT.mkdir(parents=True,exist_ok=True)
build=OUT/'check.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
 'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
 'cl /nologo /EHsc /MD /O2 /std:c++17 /DRP_DIRECT3D9 /D_ITERATOR_DEBUG_LEVEL=1 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX '
 '/Isrc/RP9 /Isrc/include tools/room_materials/check_route.cpp /Fosrc/obj/room_materials/check.obj /Febin/room_material_check.exe '
 'src/obj/RP9/Release/RP9.obj src/obj/RP9/Release/RP9Ex.obj src/obj/RP9/Release/Mgsdb.obj '
 '/link /LTCG /LIBPATH:bin dacom.lib d3d9.lib ddraw.lib version.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" '
 '"C:/DXSDK_Jun10/Lib/x86/DxErr.lib" legacy_stdio_definitions.lib user32.lib\n')
subprocess.run(['cmd','/c',str(build)],cwd=ROOT,check=True)
env=dict(os.environ,FREELANCER_SHADER_CACHE_DIR=str(OUT/'shader_cache'))
subprocess.run([str(ROOT/'bin/room_material_check.exe')],cwd=ROOT,env=env,check=True)
