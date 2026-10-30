"""Check the actual Common DLL, redirected save folder and RP9's exported bridge."""
from pathlib import Path
import os
import shutil
import subprocess

root=Path(__file__).resolve().parents[2]
out=root/'src/obj/graphics_settings_native'
binary=out/'bin'; saves=out/'SAVE'
binary.mkdir(parents=True,exist_ok=True); saves.mkdir(exist_ok=True)
shutil.copy2(root/'src/obj/graphics_settings_bin/Common.dll',binary/'Common.dll')
(binary/'flplusplus.ini').write_text('[flplusplus]\nsave_in_directory = true\n')
(binary/'port.ini').write_text('[Render]\nrock_relief = 2.4\nlocal_shadows = 1\n')
(saves/'PerfOptions.ini').write_text('[Graphics]\nshadows = 0\nrelief = 0\nantialiasing = 0\nanisotropy = 2\n')
(binary/'native.cpp').write_text(r'''
#include "graphics_settings.h"
#include "common_misc.h"
#include "port_config.h"
#include "RP9UserGraphics.h"
#include <cassert>
#include <cstdio>
#include <cstring>
int main(int argc,char** argv){
 assert(argc==2);char path[MAX_PATH];assert(GetUserDataPath(path));assert(_stricmp(path,argv[1])==0);
 assert(GraphicsSettings::Get(GraphicsSettings::Shadows)==0);
 assert(PortConfigInt("Render","local_shadows",1)==0);
 assert(PortConfigFloat("Render","rock_relief",1)==0);
 assert(Rp9UserGraphics("local_shadows",1)==0);
 assert(Rp9UserGraphics("smaa",1)==0 && Rp9UserGraphics("fxaa",1)==0);
 assert(Rp9UserGraphics("anisotropy",16)==4);
 GraphicsSettings::Set(GraphicsSettings::Shadows,3);
 assert(GraphicsSettings::Get(GraphicsSettings::Shadows,true)==3);
 assert(GraphicsSettings::RestartRequired() && Rp9UserGraphics("local_shadows",1)==0);
 puts("PASS: real Common.dll reads the redirected save folder; client and RP9 share the immutable active snapshot");
}
''')
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10'); version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[root/'src/include',root/'src/RP9',Path('C:/DXSDK/Include')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]+[root/'src/obj/graphics_settings_bin']))
env['PATH']='D:/games/FL_MOD/bin'+os.pathsep+env.get('PATH','')
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/EHsc','/MD','/D_ITERATOR_DEBUG_LEVEL=1','native.cpp','/Fenative.exe','/link','Common.lib'],cwd=binary,env=env,check=True)
subprocess.run([str(binary/'native.exe'),str(saves)],cwd=binary,env=env,check=True)
