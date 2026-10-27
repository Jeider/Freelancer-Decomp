"""Render the production ship-glass shader on D3D9 and check transmission/tint."""
import os
import subprocess
from pathlib import Path
root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/ship_glass'
out.mkdir(parents=True, exist_ok=True)
build = out / 'check.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
 'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
 'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 /Isrc/include '
 'tools/ship_glass/check.cpp /Fosrc/obj/ship_glass/check.obj /Febin/ship_glass_check.exe '
 '/link d3d9.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" user32.lib\n')
subprocess.run(['cmd', '/c', str(build)], cwd=root, check=True)
env = dict(os.environ, FREELANCER_SHADER_CACHE_DIR=str(out / 'shader_cache'))
subprocess.run([str(root / 'bin/ship_glass_check.exe')], cwd=root, env=env, check=True)
