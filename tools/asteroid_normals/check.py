"""Build and run real D3D9 normal-map shader and production-route fixtures."""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[2]
if not (root / 'src/include/render/IRPNormalSurface.h').exists():
    print('SKIP: asteroid normal-map prototype is disabled; use player_shadow_quality/check.py.')
    raise SystemExit(0)
out = root / 'src/obj/asteroid_normals'
out.mkdir(parents=True, exist_ok=True)
(out / 'baseline.hlsl').write_bytes(subprocess.check_output(
    ['git', 'show', 'HEAD:DATA_EXTRA/SHADERS/surface_material.hlsl'], cwd=root))
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat')
sdk = Path('C:/DXSDK_Jun10')
env = dict(os.environ)
env['PATH'] = str(root / 'bin') + os.pathsep + env.get('PATH', '')
env['FREELANCER_SHADER_CACHE_DIR'] = str(out / 'shader_cache')
for test in ('gpu', 'route'):
    production = test == 'route'
    flags = '/MD /DRP_DIRECT3D9 /D_ITERATOR_DEBUG_LEVEL=1' if production else ''
    exe = f'bin/asteroid_normal_{test}_check.exe'
    objects = ('src/obj/RP9/Release/RP9.obj src/obj/RP9/Release/RP9Ex.obj '
               'src/obj/RP9/Release/Mgsdb.obj') if production else ''
    libs = (f'/LTCG /LIBPATH:bin dacom.lib ddraw.lib version.lib '
            f'"{sdk / "Lib/x86/DxErr.lib"}" legacy_stdio_definitions.lib') if production else ''
    build = out / f'{test}_build.cmd'
    build.write_text(f'@echo off\ncall "{vc}" > nul\nif errorlevel 1 exit /b 1\n'
        f'set "INCLUDE=%INCLUDE%;{sdk / "Include"}"\n'
        f'cl /nologo /EHsc /O2 /std:c++17 {flags} /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX '
        f'/Isrc/RP9 /Isrc/include tools/asteroid_normals/check_{test}.cpp '
        f'/Fosrc/obj/asteroid_normals/{test}.obj /Fe{exe} {objects} '
        f'/link d3d9.lib "{sdk / "Lib/x86/d3dx9.lib"}" user32.lib {libs}\n')
    subprocess.run(['cmd', '/c', str(build)], cwd=root, check=True)
    subprocess.run([str(root / exe)], cwd=root, env=env, check=True)
