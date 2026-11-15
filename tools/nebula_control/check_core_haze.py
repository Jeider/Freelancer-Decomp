"""Compile and exercise the production interior-haze shader on a hidden D3D9 device."""
from pathlib import Path
import os
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'src/obj/core_haze_check'
OUT.mkdir(parents=True, exist_ok=True)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
dx = Path('C:/DXSDK_Jun10')
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str,[vc/'include',dx/'Include']+
    [sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB'] = ';'.join(map(str,[vc/'lib/x86',dx/'Lib/x86']+
    [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT',
    str(Path(__file__).with_suffix('.cpp')), '/Fecheck.exe','/link','d3d9.lib','d3dx9.lib','user32.lib'],
    cwd=OUT,env=env,check=True)
subprocess.run([str(OUT/'check.exe')],cwd=ROOT,env=env,check=True)
