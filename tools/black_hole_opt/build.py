from pathlib import Path
import os,subprocess
root=Path(__file__).resolve().parents[2]
out=root/'src/obj/black_hole_opt';out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include',root/'src/freelancer/Client']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[Path('C:/DXSDK_Jun10/Include')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]+[Path('C:/DXSDK_Jun10/Lib/x86')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT',str(root/'tools/black_hole_opt/bench.cpp'),'/Febench.exe','/link','d3d9.lib','d3dx9.lib','user32.lib'],cwd=out,env=env,check=True)
