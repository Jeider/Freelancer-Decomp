"""Exercise real Common archetypes/cargo and production inventory/dock filtering."""
from pathlib import Path
import os
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/physics'))
from check_gravity import function

def main():
    out=ROOT/'src/obj/inventory_categories_check'
    out.mkdir(parents=True,exist_ok=True)
    production=function('src/freelancer/Client/nn_inventory.cpp','int NnItemFilterMode(')
    production+=function('src/Content/DockQueues.cpp','bool DockKeyUnlocks(')
    production+=function('src/freelancer/Client/nn_dealer.cpp','int NnDealer::GetMaxBuyCount(')
    (out/'production.inc').write_text(production)
    shutil.copy2(ROOT/'bin/Common.dll',out/'Common.dll')
    vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
    env=dict(os.environ)
    env['INCLUDE']=';'.join(map(str,[out,ROOT/'src/include',ROOT/'src/freelancer/Client',vc/'include']+
        [sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[Path('C:/DXSDK/Include')]))
    env['LIB']=';'.join(map(str,[ROOT/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
    env['PATH']='D:/games/FL_MOD/bin;'+env['PATH']
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W3','/EHsc','/MD',
        '/D_ITERATOR_DEBUG_LEVEL=1','/D_CRT_SECURE_NO_WARNINGS',str(ROOT/'tools/inventory_categories/check_native.cpp'),
        '/Fecheck.exe','/link','Common.lib','dacom.lib'],cwd=out,env=env,check=True)
    subprocess.run([str(out/'check.exe')],cwd=out,env=env,check=True)

if __name__=='__main__':main()
