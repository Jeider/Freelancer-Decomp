"""Compile and run the production GPU detector without changing game preferences."""
from pathlib import Path
import os
import subprocess

root=Path(__file__).resolve().parents[2]
out=root/'src/obj/graphics_adapter_check'
out.mkdir(parents=True,exist_ok=True)
(out/'probe.cpp').write_text('''#include "graphics_adapter.h"
int main() {
    auto gpu=GraphicsAdapter::Detect();
    printf("GPU: %s\\nKey: %s\\nType: %s\\n",gpu.Name,gpu.Key,
        gpu.Type==GraphicsAdapter::Integrated?"integrated":gpu.Type==GraphicsAdapter::Discrete?"discrete":"unknown");
    return gpu.Type==GraphicsAdapter::Unknown?1:0;
}
''')
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10'); version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include',root/'src/include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT','probe.cpp','/Feprobe.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'probe.exe')],cwd=out,check=True)
