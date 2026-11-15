"""Exercise the actual RP9 loader with a local proxy DLL, in isolated processes."""
from pathlib import Path
import os
import subprocess

root = Path(__file__).resolve().parents[2]
out = root / 'src/obj/base_neural_loader_check'
out.mkdir(parents=True, exist_ok=True)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc/'include', root/'src/RP9'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB'] = ';'.join(map(str, [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
cl = str(vc/'bin/Hostx64/x86/cl.exe')
(out/'proxy.cpp').write_text('''#include <windows.h>
BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID){return TRUE;}
''')
subprocess.run([cl, '/nologo', '/LD', '/MT', 'proxy.cpp', '/link', '/OUT:d3d9.dll'], cwd=out, env=env, check=True)
(out/'probe.cpp').write_text(r'''#include "RP9D3DLoader.h"
#include <cstdio>
bool enabled=false;
#ifndef NO_CLIENT_EXPORT
#pragma comment(linker,"/EXPORT:FlBaseNeuralRuntimeEnabled=_FlBaseNeuralRuntimeEnabled")
extern "C" bool __cdecl FlBaseNeuralRuntimeEnabled(){return enabled;}
#endif
int main(int argc,char** argv){
    if(argc!=3)return 10;
    enabled=argv[1][0]=='1';
    HMODULE module=Rp9D3DLoader::Load();
    if(!module)return 11;
    wchar_t path[32768]={};GetModuleFileNameW(module,path,32768);
    auto local=Rp9D3DLoader::ExecutableDirectory()+L"d3d9.dll";
    bool optional=_wcsicmp(path,local.c_str())==0;
    wprintf(L"Loaded: %s\n",path);
    if(optional!=(argv[2][0]=='1'))return 12;
    if(!optional && GetModuleHandleW(L"dxgi.dll"))return 13;
    FreeLibrary(module);
}
''')
for name, defines in [('off', []), ('on', ['/DFREELANCER_DLSS5']), ('no_export', ['/DFREELANCER_DLSS5', '/DNO_CLIENT_EXPORT'])]:
    subprocess.run([cl, '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT', *defines, 'probe.cpp', '/Fe'+name+'.exe'], cwd=out, env=env, check=True)
dependencies = ['dxgi.dll', 'fl_base_neural.addon32', 'neural/host64/fl_base_neural_host.exe',
                'neural/host64/dxgi.dll', 'neural/host64/renodx-dlss5.addon64',
                'neural/host64/nvngx_dlss.dll', 'neural/host64/nvngx_dlssnr.dll']
for name in dependencies:
    path = out/name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('Test fixture: must never be loaded as a DLL')
def run(exe, enabled, optional):
    subprocess.run([str(out/(exe+'.exe')), str(enabled), str(optional)], cwd=out, check=True)
run('off', 1, 0)
run('no_export', 1, 0)
run('on', 0, 0)
run('on', 1, 1)
for name in dependencies:
    path=out/name
    path.unlink()
    run('on', 1, 0)
    path.write_text('Test fixture: must never be loaded as a DLL')
print('PASS: compiled-out, missing client export, disabled, enabled, every incomplete runtime')
