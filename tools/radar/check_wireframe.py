"""Run native geometry/loader checks against the staged Lair models and new Common."""
from pathlib import Path
import os
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/obj/radar_wireframe'
VC=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
SDK=Path('C:/Program Files (x86)/Windows Kits/10');VERSION='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[ROOT/'src/include',VC/'include']+[SDK/'Include'/VERSION/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[ROOT/'bin',VC/'lib/x86']+[SDK/'Lib'/VERSION/x/'x86' for x in ('ucrt','um')]))
env['PATH']='D:/games/FL_MOD/bin;'+env['PATH']
shutil.copy2(ROOT/'bin/Common.dll',OUT/'Common.dll')
for source in ('test_wireframe.cpp','test_wireframe_layer.cpp','test_solars.cpp'):
    exe=Path(source).stem+'.exe'
    subprocess.run([str(VC/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/EHsc','/MD',
                    '/D_ITERATOR_DEBUG_LEVEL=1',str(ROOT/'tools/radar'/source),'/Fe'+exe,
                    '/link','Common.lib'],cwd=OUT,env=env,check=True)
    subprocess.run([str(OUT/exe)],cwd=OUT,env=env,check=True)
