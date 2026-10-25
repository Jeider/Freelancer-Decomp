"""Build/run the production jumpgate shader fixture; --frames also exports a launch sequence."""
from pathlib import Path
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'src/obj/jumpgate_check'
OUT.mkdir(parents=True, exist_ok=True)
sdk = Path(os.environ.get('DXSDK_DIR', 'C:/DXSDK_Jun10'))
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat')
script = OUT / 'build.cmd'
script.write_text(
    f'@echo off\ncall "{vc}" > nul\nif errorlevel 1 exit /b 1\n'
    f'set "INCLUDE=%INCLUDE%;{sdk / "Include"}"\n'
    'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS '
    'tools\\check_jumpgate_render.cpp /Fosrc\\obj\\jumpgate_check\\check.obj '
    '/Fesrc\\obj\\jumpgate_check\\check.exe /link d3d9.lib '
    f'"{sdk / "Lib/x86/d3dx9.lib"}" user32.lib\n', encoding='utf8')
subprocess.run(['cmd', '/c', str(script)], cwd=ROOT, check=True)
env = dict(os.environ)
env['PATH'] = str(ROOT / 'bin') + os.pathsep + env.get('PATH', '')
subprocess.run([str(OUT / 'check.exe'), *sys.argv[1:]], cwd=ROOT, env=env, check=True)
