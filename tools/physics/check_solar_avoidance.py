"""Native hollow-solar regression on a ring fixture and actual Nomad Lair SURs."""
import os
from pathlib import Path
import re
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import valensia_optimize as v
import valensia_mega as mega


def main():
    out=mega.OUT/'avoidance_check'
    out.mkdir(parents=True,exist_ok=True)
    boxes=[((-400,-400,-100),(-200,400,100)),((200,-400,-100),(400,400,100)),
           ((-200,200,-100),(200,400,100)),((-200,-400,-100),(200,-200,100))]
    hulls=[v.sur.make_hull(np.array([[x,y,z] for x in (a[0],b[0]) for y in (a[1],b[1]) for z in (a[2],b[2])]),v.utf.crc('Root')) for a,b in boxes]
    folder=v.data_folder(v.GAME,out)
    folder.sync_data_file('fixture/ring.sur',v.surface_file([('Root',hulls)]))
    vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk=Path('C:/Program Files (x86)/Windows Kits/10')
    version='10.0.26100.0';env=dict(os.environ)
    env['INCLUDE']=';'.join(map(str,[v.REPO/'src/include',vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
    env['LIB']=';'.join(map(str,[v.REPO/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
    env['PATH']=str(v.GAME/'bin')+';'+env['PATH']
    commands=(v.REPO/'src/obj/Common/Release/Common.tlog/CL.command.1.tlog').read_text(encoding='utf-16')
    found=re.search(r'/D _ITERATOR_DEBUG_LEVEL=(\d)',commands)
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/W4','/MD','/EHsc',
        '/D_ITERATOR_DEBUG_LEVEL='+(found[1] if found else '0'),str(Path(__file__).with_suffix('.cpp')),
        '/Fecheck.exe','/link','Common.lib','DALib.lib','dacom.lib'],cwd=out,env=env,check=True)
    waist=mega.OUT/'stage/DATA/SOLAR/OPTIMIZED/valensia_mega/vlm_hq_waist.sur'
    if not waist.exists():waist=v.GAME/'DATA/SOLAR/OPTIMIZED/valensia_mega/vlm_hq_waist.sur'
    paths=[out/'DATA/fixture/ring.sur',v.GAME/'DATA/SOLAR/DOCKABLE/nomad_lair.sur',
           v.GAME/'DATA/SOLAR/DOCKABLE/nomad_lair_beta_towerless.sur',
           waist]
    result=subprocess.run([str(out/'check.exe'),*map(str,paths)],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/'result.log').write_bytes(result.stdout)
    print(result.stdout.decode(errors='replace'))
    result.check_returncode()


if __name__=='__main__':main()
