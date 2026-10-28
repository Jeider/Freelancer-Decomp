"""Exercise the production volume-beam shader on D3D9 in an invisible test window."""
import os
from pathlib import Path
import subprocess
root = Path(__file__).resolve().parents[2]
out = root/'src/obj/beam_volume'
out.mkdir(parents=True, exist_ok=True)
build = out/'check.cmd'
build.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
    'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
    'cl /nologo /EHsc /O2 /std:c++17 /D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 /Isrc/include '
    'tools/beam_volume/check.cpp /Fosrc/obj/beam_volume/check.obj /Febin/beam_volume_check.exe '
    '/link d3d9.lib "C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" user32.lib\n')
subprocess.run(['cmd','/c',str(build)],cwd=root,check=True)
env=dict(os.environ,FREELANCER_SHADER_CACHE_DIR=str(out/'shader_cache'))
subprocess.run([str(root/'bin/beam_volume_check.exe')],cwd=root,env=env,check=True)

# Exercise the real RP9 pass/transform/state-cache route, not just the shader.
build_route=out/'route.cmd'
build_route.write_text('@echo off\ncall "C:/Program Files/Microsoft Visual Studio/18/Community/VC/Auxiliary/Build/vcvars32.bat" > nul\n'
    'if errorlevel 1 exit /b 1\nset "INCLUDE=%INCLUDE%;C:/DXSDK_Jun10/Include"\n'
    'cl /nologo /EHsc /MD /O2 /std:c++17 /DRP_DIRECT3D9 /D_ITERATOR_DEBUG_LEVEL=1 /DBEAM_ROUTE '
    '/D_CRT_SECURE_NO_WARNINGS /DNOMINMAX /Isrc/RP9 /Isrc/include '
    'tools/beam_volume/check.cpp /Fosrc/obj/beam_volume/route.obj /Febin/beam_volume_route_check.exe '
    'src/obj/RP9/Release/RP9.obj src/obj/RP9/Release/RP9Ex.obj src/obj/RP9/Release/Mgsdb.obj '
    '/link /LTCG /LIBPATH:bin dacom.lib d3d9.lib ddraw.lib version.lib '
    '"C:/DXSDK_Jun10/Lib/x86/d3dx9.lib" "C:/DXSDK_Jun10/Lib/x86/DxErr.lib" legacy_stdio_definitions.lib user32.lib\n')
subprocess.run(['cmd','/c',str(build_route)],cwd=root,check=True)
subprocess.run([str(root/'bin/beam_volume_route_check.exe')],cwd=root,env=env,check=True)
