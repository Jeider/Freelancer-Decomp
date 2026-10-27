"""Build/run the actual RP9 player/world shadow routing and GPU pixel fixture."""
import os
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/player_shadow_quality'
out.mkdir(parents=True, exist_ok=True)
build = out / 'route_build.cmd'
build.write_text('@echo off\n'
    'call "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
    'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
    'cl /nologo /EHsc /MD /O2 /std:c++17 /DRP_DIRECT3D9 /D_ITERATOR_DEBUG_LEVEL=1 '
    '/D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 /Isrc/include '
    'tools/player_shadow_quality/check_route.cpp /Fosrc/obj/player_shadow_quality/route.obj '
    '/Febin/player_shadow_route_check.exe src/obj/RP9/Release/RP9.obj '
    'src/obj/RP9/Release/RP9Ex.obj src/obj/RP9/Release/Mgsdb.obj '
    '/link /LTCG /LIBPATH:bin dacom.lib d3d9.lib ddraw.lib version.lib '
    '"C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" "C:/DXSDK_Jun10/Lib/x86/DxErr.lib" '
    'legacy_stdio_definitions.lib user32.lib\n')
subprocess.run(['cmd', '/c', str(build)], cwd=root, check=True)
env = dict(os.environ)
env['FREELANCER_SHADER_CACHE_DIR'] = str(root / 'src/obj/asteroid_normals/shader_cache')
subprocess.run([str(root / 'bin/player_shadow_route_check.exe')], cwd=root, env=env, check=True)
