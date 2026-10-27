"""Build the D3D9 fixtures; --build-only does not need a GPU desktop."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/nomad_surfaces'
def main():
    p=argparse.ArgumentParser();p.add_argument('--build-only',action='store_true');p.add_argument('--no-build',action='store_true');args=p.parse_args()
    OUT.mkdir(parents=True,exist_ok=True)
    env=os.environ.copy();env['PATH']=str(ROOT/'bin')+os.pathsep+env.get('PATH','');env['FREELANCER_SHADER_CACHE_DIR']=str(OUT/'cache')
    if not args.no_build:
        vc=sorted(Path('C:/Program Files/Microsoft Visual Studio').glob('*/Community/VC/Tools/MSVC/*'))[-1]
        sdk=Path('C:/Program Files (x86)/Windows Kits/10');version=sorted(p.name for p in (sdk/'Include').iterdir() if (p/'um/Windows.h').exists())[-1]
        dx=Path('C:/DXSDK_Jun10')
        env['INCLUDE']=';'.join(map(str,[vc/'include',sdk/f'Include/{version}/ucrt',sdk/f'Include/{version}/shared',sdk/f'Include/{version}/um',dx/'Include',ROOT/'src/RP9']))
        env['LIB']=';'.join(map(str,[vc/'lib/x86',sdk/f'Lib/{version}/ucrt/x86',sdk/f'Lib/{version}/um/x86']))
        subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/O2','/std:c++17','/EHsc','/MT','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS',str(ROOT/'tools/nomad_surfaces/check.cpp'),f'/Fe{OUT/"check.exe"}','/link','user32.lib','d3d9.lib',str(dx/'Lib/x86/d3dx9.lib')],cwd=OUT,env=env,check=True)
        shutil.copy2(ROOT/'bin/d3dx9_43.dll',OUT/'d3dx9_43.dll')
        subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/O2','/std:c++17','/EHsc','/MD','/DRP_DIRECT3D9','/D_ITERATOR_DEBUG_LEVEL=1','/DNOMINMAX','/D_CRT_SECURE_NO_WARNINGS',f'/I{ROOT/"src/include"}',str(ROOT/'tools/nomad_surfaces/route.cpp'),f'/Fe{ROOT/"bin/nomad_route_check.exe"}',*[str(ROOT/f'src/obj/RP9/Release/{n}.obj') for n in ['RP9','RP9Ex','Mgsdb']],'/link','/LTCG',f'/LIBPATH:{ROOT/"bin"}','dacom.lib','user32.lib','d3d9.lib','ddraw.lib','version.lib','legacy_stdio_definitions.lib',str(dx/'Lib/x86/d3dx9.lib'),str(dx/'Lib/x86/DxErr.lib')],cwd=OUT,env=env,check=True)
    if not args.build_only:
        for executable,filename in [(OUT/'check.exe','validation.txt'),(ROOT/'bin/nomad_route_check.exe','route.txt')]:
            with (OUT/filename).open('wb') as log:r=subprocess.run([str(executable)],cwd=ROOT,env=env,stdout=log,stderr=subprocess.STDOUT)
            print((OUT/filename).read_text(errors='replace'),flush=True);r.check_returncode()
if __name__=='__main__':main()
