"""Build/run the production offscreen shader warmup on the local GPU (hidden window)."""
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[2]
out=root/'src/obj/render_warmup_check'
out.mkdir(parents=True,exist_ok=True)
cmd=out/'build.cmd'
cmd.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" >nul\n'
 'if errorlevel 1 exit /b 1\n'
 'set "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
 'cl /nologo /EHsc /std:c++17 /W4 /O2 /D_CRT_SECURE_NO_WARNINGS /Isrc/RP9 tools/hitch_log/check_warmup_gpu.cpp '
 '/Fosrc/obj/render_warmup_check/check.obj /Fesrc/obj/render_warmup_check/check.exe '
 '/link d3d9.lib user32.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib"\n')
subprocess.run(['cmd','/c',str(cmd)],cwd=root,check=True)
env=dict(os.environ)
env['PATH']='D:/games/FL_MOD/bin;'+env.get('PATH','')
subprocess.run([str(out/'check.exe')],cwd=root,env=env,check=True)
