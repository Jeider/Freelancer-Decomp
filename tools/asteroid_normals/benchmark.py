"""Run an isolated normal-map GPU cost benchmark; does not change game files."""
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
if not (root / 'src/include/render/IRPNormalSurface.h').exists():
    raise SystemExit('Asteroid normal maps are disabled. Archived timings describe the former implementation.')
out = root / 'src/obj/asteroid_normals'
build = out / 'benchmark_build.cmd'
build.write_text('@echo off\n'
    'call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
    'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
    'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 '
    'tools/asteroid_normals/benchmark.cpp /Fosrc/obj/asteroid_normals/benchmark.obj '
    '/Febin/asteroid_normal_benchmark.exe /link d3d9.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" user32.lib\n')
subprocess.run(['cmd', '/c', str(build)], cwd=root, check=True)
env = dict(os.environ)
env['FREELANCER_SHADER_CACHE_DIR'] = str(out / 'shader_cache')
result = subprocess.run([str(root / 'bin/asteroid_normal_benchmark.exe')], cwd=root,
                        env=env, capture_output=True, text=True, check=True)
(out / 'benchmark.txt').write_text(result.stdout)
print(result.stdout, end='')
