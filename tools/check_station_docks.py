import json,os,subprocess
from pathlib import Path
import station_batch_model as p
from station_docks import direct
m=p.m
standalone=os.environ.get('STATION_DOCK_STANDALONE')=='1'
manifest=json.loads((p.OUT/'manifest.json').read_text())
report=json.loads((p.OUT/'docks.json').read_text()) if standalone else manifest['config']['dock_model']
out=p.OUT/'dock_animation';out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0';env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[m.REPO/'src/include',vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[m.REPO/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
env['PATH']=str(m.GAME/'bin')+';'+env['PATH']
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc',str(m.REPO/'tools/check_station_docks.cpp'),'/Fecheck.exe','/link','DALib.lib','dacom.lib'],cwd=out,env=env,check=True)
ini=out/'dacom.ini';ini.write_text('[DACOM]\nIgnoreDACOMEnv = true\nDllPath = '+str(m.GAME/'bin')+'\\\n[Libraries]\nReadFile.dll\nx86math.dll\nEngBase.dll\n[Engine]\nAnimation\nHardpoint\n')
model=p.OUT/'stage'/report['model'];tree=m.utf.read_tree(model.read_bytes())[1][0]
scripts=direct(direct(tree,'Animation'),'Script');count=len(report['ports'])
assert [n.name for n in scripts.children]==[f'Sc_open dock{i+1}' for i in range(count)]
with (out/'result.log').open('wb') as log:
    result=subprocess.run([str(out/'check.exe'),str(ini),str(model),str(count),str(report.get('active_side',1)),report.get('layout','cluster')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=40)
print((out/'result.log').read_text(errors='replace'));result.check_returncode()
if not standalone:(p.OUT/'dock_animation.ok').write_text(m.old.sha256((p.OUT/'manifest.json').read_bytes()).hexdigest())
