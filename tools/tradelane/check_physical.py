"""Check staged TLR surfaces through native Common/IVP and moving-body ray casts."""
from physical_model import *
import os
import shutil
import subprocess
sys.path.insert(0,str(ROOT/'tools/cursors'))
from check import compiler_env, VC

CHECK=ROOT/'src/obj/tradelane_physical_check'
CHECK.mkdir(parents=True,exist_ok=True)
binary=ROOT/'src/obj/train_courier/rpg1/bin'
for name in ('Common.dll','Common.pdb'):
    shutil.copy2(binary/name,CHECK/name)
env=compiler_env();env['INCLUDE']=str(ROOT/'src/include')+';'+env['INCLUDE']+';C:/DXSDK/include'
env['LIB']=str(binary)+';'+str(ROOT/'bin')+';'+env['LIB']
env['PATH']=str(GAME/'bin')+';'+env.get('PATH','')
(CHECK/'check_dacom.ini').write_text('[DACOM]\nIgnoreDACOMEnv = true\nDllPath = '+str(GAME/'bin')+'\\\n\n[Libraries]\nReadFile.dll\nx86math.dll\nEngBase.dll\nsystem.dll\n\n[System]\n\n[Engine]\nHardpoint\nAnimation\n')
stage=DataFolder(root=OUT/'stage')
stage.sync_data_file('SOLAR/DOCKABLE/tlr_root.3db',(GAME/'DATA/SOLAR/DOCKABLE/tlr_root.3db').read_bytes())
for source,name,args in [(ROOT/'tools/train_sur/check.cpp','surface',[str(stage.data_path(MODEL.replace('.cmp','.sur'))),str(stage.data_path('SOLAR/DOCKABLE/tlr_root.sur'))]),
                         (Path(__file__).with_suffix('.cpp'),'physics',[str(OUT/'stage/DATA'),'attached'])]:
    cmd=[str(VC/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MD','/D_ITERATOR_DEBUG_LEVEL=1','/D_CRT_SECURE_NO_WARNINGS',str(source),'/Fe'+name+'.exe','/link','Common.lib','DALib.lib','dacom.lib']
    with (CHECK/(name+'_compile.log')).open('wb') as log:r=subprocess.run(cmd,cwd=CHECK,env=env,stdout=log,stderr=subprocess.STDOUT)
    if r.returncode:print((CHECK/(name+'_compile.log')).read_text(errors='replace'))
    r.check_returncode()
    for parameters in ([args] if name=='surface' else [args,args[:-1]+['direct']]):
        with (CHECK/(name+'_'+Path(parameters[-1]).name+'.log')).open('wb') as log:
            r=subprocess.run([str(CHECK/(name+'.exe'))]+parameters,cwd=CHECK,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=90)
        print(Path(log.name).read_text(errors='replace'));r.check_returncode()
paths=[stage.data_path(n) for n in json.loads((OUT/'manifest.json').read_text())['files']]
paths += [binary/'Common.dll',ROOT/'src/Common/solar_animation.cpp',ROOT/'src/include/solar_animation.h',Path(__file__),Path(__file__).with_suffix('.cpp')]
(CHECK/'verified.json').write_text(json.dumps({str(p):digest(p.read_bytes()) for p in paths},indent=2))
