"""Compile the production startup manifest, persist it, verify warm hits and native D3D9 acceptance."""
import os
from pathlib import Path
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/shader_startup'
out.mkdir(parents=True, exist_ok=True)
cmd = out / 'build.cmd'
cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" >nul\n'
               'if errorlevel 1 exit /b 1\n'
               'set "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
               'cl /nologo /EHsc /std:c++17 /utf-8 /W4 /O2 /D_CRT_SECURE_NO_WARNINGS /Isrc/RP9 '
               'tools/shader_startup/check.cpp /Fosrc/obj/shader_startup/check.obj /Fesrc/obj/shader_startup/check.exe '
               '/link d3d9.lib user32.lib gdi32.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib"\n')
subprocess.run(['cmd', '/c', str(cmd)], cwd=root, check=True)
env = dict(os.environ)
env['PATH'] = 'D:/Games/FL_MOD/bin;' + env.get('PATH', '')
subprocess.run([str(out/'check.exe'), str(root/'DATA_EXTRA/SHADERS')+'/', str(out/'cache')],
               cwd=root, env=env, check=True)
