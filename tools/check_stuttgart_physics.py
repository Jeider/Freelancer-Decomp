import json,os,subprocess,re,sys
from pathlib import Path
import stuttgart_mega as p
import numpy as np
m=p.m
out=p.OUT/'physics_check';out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[m.REPO/'src/include',vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]+[Path('C:/DXSDK/Include')]))
env['LIB']=';'.join(map(str,[m.REPO/'bin',vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
env['PATH']=str(m.GAME/'bin')+';'+env['PATH']
env['_NT_SYMBOL_PATH']=str(m.REPO/'src/obj/graphics_auto_install/bin')+';'+str(m.GAME/'bin')
cmd=[str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/MD','/EHsc','/D_ITERATOR_DEBUG_LEVEL=1',str(m.REPO/'tools/check_stuttgart_physics.cpp'),'/Fecheck.exe','/link','Common.lib','DALib.lib','dacom.lib']
subprocess.run(cmd,cwd=out,env=env,check=True)
(out/'check_dacom.ini').write_text('[DACOM]\nIgnoreDACOMEnv = true\nDllPath = '+str(m.GAME/'bin')+'\\\n[Libraries]\nReadFile.dll\nx86math.dll\nEngBase.dll\nsystem.dll\n[System]\n[Engine]\nHardpoint\nAnimation\n')
legacy=False
manifest=json.loads((p.OUT/'manifest.json').read_text());fixture=[]
folder=m.old.data_folder(m.GAME,p.OUT/'stage')
for c in manifest['components']:
    model=p.OUT/f"stage/DATA/SOLAR/OPTIMIZED/stuttgart_mega/{c['name']}.cmp"
    fixture.append(f"{model.name} "+' '.join(map(str,c['origin']))+" 1 1")
    for body in c['bodies']:
        surface=p.OUT/f"stage/DATA/SOLAR/OPTIMIZED/stuttgart_mega/{body['name']}.sur"
        h=m.old.leaves(dict(dict(m.old.parts(surface.read_bytes()))[m.utf.crc('Root')])[b'surf'])[0]
        a,b,d=h.points[h.faces[0]];normal=np.cross(b-a,d-a);normal/=np.linalg.norm(normal)
        center=(a+b+d)/3+np.array(body['origin'])
        rays=np.concatenate([center+normal*2,center-normal*2])
        fixture.append(body['name']+'.cmp '+' '.join(map(str,body['origin']))+' 1 0 '+' '.join(map(str,np.eye(3).flat))+' '+' '.join(map(str,rays)))
# Include the unchanged working dock and both retained towers at their actual
# template poses. Stage their existing assets through the same DATA API.
sources=p.templates((m.GAME/p.TEMPLATE).read_text(encoding='utf-8-sig'))
source=sources.get('StuttgartMegabaseOriginal',sources['StuttgartMegabase'])
retained=[]
builder=m.Builder();folder=m.old.data_folder(m.GAME,p.OUT/'stage')
for row in m.b.placements_from_template(source):
    if p.group(row):continue
    arch=builder.solars[row.archetype.lower()]
    path=m.b.model_path(m.GAME/'DATA',m.old.one(arch,'da_archetype'))
    for asset in (path,path.with_suffix('.sur')):
        if asset.exists():folder.sync_data_file('SOLAR/OPTIMIZED/stuttgart_mega/'+asset.name,asset.read_bytes())
    rot=m.old.euler_matrix(*row.rotate)
    root_id=m.utf.crc('Root') if path.suffix.lower()=='.cmp' else 0
    count=1+(sum(ident!=root_id and b'!fxd' in dict(chunks) for ident,chunks in m.old.parts(path.with_suffix('.sur').read_bytes())) if path.with_suffix('.sur').exists() else 0)
    retained.append(path.name+' '+' '.join(map(str,row.pos))+f' {count} 0 '+' '.join(map(str,rot.flat)))
fixture=retained+fixture
(out/'fixture.txt').write_text('\n'.join(fixture))
logpath=out/'result.log'
with logpath.open('wb') as log:
    result=subprocess.run([str(out/'check.exe'),str(p.OUT/'stage/DATA/SOLAR/OPTIMIZED/stuttgart_mega'),str(out/'fixture.txt')],cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=40)
print(logpath.read_text(errors='replace')[-5000:]);result.check_returncode()
(p.OUT/'physics_check.ok').write_text(m.old.sha256((p.OUT/'manifest.json').read_bytes()).hexdigest())
