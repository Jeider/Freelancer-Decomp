"""Build/run the real RP9 additive energy route on D3D9 hardware."""
import os
from pathlib import Path
import subprocess
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/nomad_energy'
OUT.mkdir(parents=True,exist_ok=True)
vc=sorted(Path('C:/Program Files/Microsoft Visual Studio').glob('*/Community/VC/Tools/MSVC/*'))[-1]
sdk=Path('C:/Program Files (x86)/Windows Kits/10')
version=sorted(p.name for p in (sdk/'Include').iterdir() if (p/'um/Windows.h').exists())[-1]
dx=Path('C:/DXSDK_Jun10');env=os.environ.copy()
env['INCLUDE']=';'.join(map(str,[vc/'include',sdk/f'Include/{version}/ucrt',sdk/f'Include/{version}/shared',sdk/f'Include/{version}/um',dx/'Include',ROOT/'src/RP9']))
env['LIB']=';'.join(map(str,[vc/'lib/x86',sdk/f'Lib/{version}/ucrt/x86',sdk/f'Lib/{version}/um/x86']))
exe=ROOT/'bin/nomad_energy_check.exe'
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/O2','/std:c++17','/EHsc','/MD','/DRP_DIRECT3D9','/D_ITERATOR_DEBUG_LEVEL=1','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS',f'/I{ROOT/"src/include"}',str(ROOT/'tools/nomad_surfaces/energy_route.cpp'),f'/Fe{exe}',*[str(ROOT/f'src/obj/RP9/Release/{n}.obj') for n in ['RP9','RP9Ex','Mgsdb']],'/link','/LTCG',f'/LIBPATH:{ROOT/"bin"}','dacom.lib','user32.lib','d3d9.lib','ddraw.lib','version.lib','legacy_stdio_definitions.lib',str(dx/'Lib/x86/d3dx9.lib'),str(dx/'Lib/x86/DxErr.lib')],cwd=OUT,env=env,check=True)
with (OUT/'validation.txt').open('wb') as log:
    result=subprocess.run([str(exe)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
print((OUT/'validation.txt').read_text(errors='replace'),flush=True)
result.check_returncode()
