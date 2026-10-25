"""Build/run the production nebula upsampling regression on a hidden D3D9 device."""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[1]
out = root / 'src/obj/nebula_composite_check'
out.mkdir(parents=True, exist_ok=True)
sdk = Path(os.environ.get('DXSDK_DIR', 'C:/DXSDK_Jun10'))
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat')
script = out / 'build.cmd'
script.write_text(
    f'@echo off\ncall "{vc}" > nul\nif errorlevel 1 exit /b 1\n'
    f'set "INCLUDE=%INCLUDE%;{sdk / "Include"}"\n'
    'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX '
    'tools\\check_nebula_composite.cpp /Fosrc\\obj\\nebula_composite_check\\check.obj '
    '/Fesrc\\obj\\nebula_composite_check\\check.exe /link d3d9.lib '
    f'"{sdk / "Lib/x86/d3dx9.lib"}" user32.lib\n', encoding='utf8')
subprocess.run(['cmd', '/c', str(script)], cwd=root, check=True)
env = dict(os.environ)
env['PATH'] = str(root / 'bin') + os.pathsep + env.get('PATH', '')
subprocess.run([str(out / 'check.exe')], cwd=root, env=env, check=True)
