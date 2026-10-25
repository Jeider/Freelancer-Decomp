"""Build production shader preview/cache warmer; generate noise from the client's source."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
out = root / 'src/obj/nebula_ice_check'
out.mkdir(parents=True, exist_ok=True)
source = (root / 'src/freelancer/Client/nebula_volume.cpp').read_text(encoding='utf-8-sig')
noise = source[source.index('    unsigned int Hash(unsigned int X)'):source.index('    // Coverage (the fraction')]
(out / 'nebula_noise_fixture.h').write_text(
    'const unsigned long kNoiseSize=64;\n'
    'float Clamp(float x,float a,float b){return std::max(a,std::min(b,x));}\n' + noise)
sdk = Path('C:/DXSDK_Jun10')
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat')
script = out / 'build.cmd'
script.write_text(
    f'@echo off\ncall "{vc}" > nul\nif errorlevel 1 exit /b 1\n'
    f'set "INCLUDE=%INCLUDE%;{sdk / "Include"}"\n'
    'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX '
    '/Isrc\\RP9 /Isrc\\obj\\nebula_ice_check tools\\check_nebula_ice.cpp '
    '/Fosrc\\obj\\nebula_ice_check\\check.obj /Fesrc\\obj\\nebula_ice_check\\check.exe '
    f'/link d3d9.lib "{sdk / "Lib/x86/d3dx9.lib"}" user32.lib\n')
subprocess.run(['cmd', '/c', str(script)], cwd=root, check=True)
env = dict(os.environ)
env['PATH'] = str(root / 'bin') + os.pathsep + env.get('PATH', '')
env['FREELANCER_SHADER_CACHE_DIR'] = str(out / 'cache')
subprocess.run([str(out / 'check.exe'), *sys.argv[1:]], cwd=root, env=env, check=True)
