import json
import os
from pathlib import Path
import subprocess
import numpy as np
import potsdam_panels as p
m=p.m
out=p.OUT/'animation_check';out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[m.REPO/'src/include',vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[m.REPO/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
env['PATH']=str(m.GAME/'bin')+';'+env['PATH']
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc',str(m.REPO/'tools/check_potsdam_animation.cpp'),'/Fecheck.exe','/link','DALib.lib','dacom.lib'],cwd=out,env=env,check=True)
ini=out/'dacom.ini';ini.write_text('[DACOM]\nIgnoreDACOMEnv = true\nDllPath = '+str(m.GAME/'bin')+'\\\n[Libraries]\nReadFile.dll\nx86math.dll\nEngBase.dll\n[Engine]\nAnimation\nHardpoint\n')
model=p.OUT/f'stage/DATA/SOLAR/OPTIMIZED/potsdam_mega/{p.NAME}.cmp'
result=subprocess.run([str(out/'check.exe'),str(ini),str(model)],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
(out/'result.log').write_bytes(result.stdout)
if result.returncode:
    print(result.stdout.decode(errors='replace')[-2500:]);raise SystemExit(result.returncode)
poses={}
for line in result.stdout.decode().splitlines():
    if not line.startswith('POSE '):continue
    _,time,name,*values=line.split();values=np.array(list(map(float,values)))
    poses.setdefault(name,[]).append((float(time),values[:3],values[3:].reshape(3,3)))
assert set(poses)=={'Rotor01','Rotor02','Rotor03'},poses.keys()
r=m.old.euler_matrix(0,-40,0)
for i,(name,frames) in enumerate(sorted(poses.items())):
    assert len(frames)==723
    for time,pos,rot in frames:
        assert np.allclose(pos,[0,600-i*600,0],atol=.001), (name,time,pos)
        theta=360*(time%p.PERIOD)/p.PERIOD
        expected=r@m.old.euler_matrix(theta,0,0)
        assert np.allclose(rot,expected,atol=2e-5),(name,time,rot,expected)
    steps=[np.linalg.norm(b[2]-a[2]) for a,b in zip(frames,frames[1:])]
    assert max(steps)<.0125 and min(steps)>.0122,(name,min(steps),max(steps))
print('PASS: native EngBase evaluated all three rotors through loop seam; fixed pivots, constant speed, expected local-X rotation')
digest=m.old.sha256((p.OUT/'manifest.json').read_bytes()).hexdigest()
(p.OUT/'animation_check.ok').write_text(digest)
