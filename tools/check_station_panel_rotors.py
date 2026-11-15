"""Evaluate Nansei's actual EngBase animation across a full loop seam."""
import json,os,subprocess
from pathlib import Path
import numpy as np
import station_batch_model as p
from station_panel_rotors import CLIP
m=p.m
manifest=json.loads((p.OUT/'manifest.json').read_text())
out=p.OUT/'panel_animation';out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0';env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[m.REPO/'src/include',vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[m.REPO/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
env['PATH']=str(m.GAME/'bin')+';'+env['PATH']
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc',str(m.REPO/'tools/check_potsdam_animation.cpp'),'/Fecheck.exe','/link','DALib.lib','dacom.lib'],cwd=out,env=env,check=True)
ini=out/'dacom.ini';ini.write_text('[DACOM]\nIgnoreDACOMEnv = true\nDllPath = '+str(m.GAME/'bin')+'\\\n[Libraries]\nReadFile.dll\nx86math.dll\nEngBase.dll\n[Engine]\nAnimation\nHardpoint\n')
model=p.OUT/'stage'/manifest['config']['panel_model']['model']
for clip,sign in ((CLIP,1),(CLIP+'_reverse',-1)):
    result=subprocess.run([str(out/'check.exe'),str(ini),str(model),clip,'1'],cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=45)
    (out/('reverse.log' if sign<0 else 'result.log')).write_bytes(result.stdout);result.check_returncode()
    frames=[]
    for line in result.stdout.decode().splitlines():
        if not line.startswith('POSE '):continue
        _,time,name,*values=line.split();assert name=='Rotor01'
        time=float(time);values=np.array(list(map(float,values)));pos=values[:3];rot=values[3:].reshape(3,3)
        assert np.allclose(pos,0,atol=.001)
        assert np.allclose(rot,m.old.euler_matrix(0,0,sign*360*(time%90)/90),atol=2e-5),(time,rot)
        frames.append(rot)
    assert len(frames)==723
    steps=[np.linalg.norm(b-a) for a,b in zip(frames,frames[1:])]
    assert min(steps)>.0122 and max(steps)<.0125
surface=m.old.parts(model.with_suffix('.sur').read_bytes())
assert {i for i,_ in surface}=={m.utf.crc('Root'),m.utf.crc('Rotor01')}
assert all(b'!fxd' in dict(chunks) for _,chunks in surface)
print('PASS: complete hub/panels rotate about local Z; constant speed through loop seam; independent moving SUR')
(p.OUT/'panel_animation.ok').write_text(m.old.sha256((p.OUT/'manifest.json').read_bytes()).hexdigest())
