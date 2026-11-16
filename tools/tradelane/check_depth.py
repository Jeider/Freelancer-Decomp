"""Build and exercise the actual corridor shader on D3D9 HAL (hidden window)."""
from pathlib import Path
import os
import subprocess
import sys

root = Path(__file__).resolve().parents[2]
out = root/'src/obj/tradelane_check'
out.mkdir(parents=True, exist_ok=True)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')] + [Path('C:/DXSDK_Jun10/Include')]))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')] + [Path('C:/DXSDK_Jun10/Lib/x86')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/O2', '/EHsc', '/MT', '/D_CRT_SECURE_NO_WARNINGS',
    str(root/'tools/check_tradelane_render.cpp'), '/Fecheck_depth.exe', '/link', 'd3d9.lib', 'd3dx9.lib', 'user32.lib'], cwd=out, env=env, check=True)
subprocess.run([str(out/'check_depth.exe'), *sys.argv[1:]], cwd=root, check=True)
