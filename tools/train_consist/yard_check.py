"""Run the standalone yard physics integration test with real CMP, SUR and IVP."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env
OUT=ROOT/'src/obj/train_consist';ASSETS=ROOT/'out/train_yard'
compiler,env=compiler_env();env['PATH']=str(ROOT/'bin')+';'+env['PATH']
sys.path.insert(0,str(Path(__file__).parent))
from player import GAME,section
weapon=(GAME/'DATA/EQUIPMENT/ORIGINAL/weapon_equip.ini').read_text()
gun_fixture=section(weapon,'Munition','co_train_turret01_mark01_ammo')[2]+section(weapon,'Gun','co_train_turret01_mark01')[2]
(ASSETS/'yard_guns.ini').write_text(gun_fixture)
(ASSETS/'yard_flags.ini').write_text('[Ship]\nnickname = test_maneuver_default\n\n[Ship]\nnickname = test_maneuver_capital\nextra_maneuvers = false\n\n[Ship]\nnickname = test_maneuver_inherited\ninherit = test_maneuver_capital\n\n[Ship]\nnickname = test_maneuver_override\ninherit = test_maneuver_capital\nextra_maneuvers = true\n')
for name in ['equipment/models/turret/utility_turret01.cmp','equipment/models/turret/utility_turret01.sur','equipment/models/ge_turret.mat']:
    target=ASSETS/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/'DATA'/name,target)
for ext in ['3db','sur']:shutil.copy2(ROOT/'out/train_consist'/('pod_grey.'+ext),ASSETS/('pod_grey.'+ext))
args=[str(compiler/'cl.exe'),'/nologo','/std:c++17','/W4','/EHsc','/O2','/MD','/D_ITERATOR_DEBUG_LEVEL=1','/D_CRT_SECURE_NO_WARNINGS',
    '/I'+str(ROOT/'src/include'),str(Path(__file__).with_name('yard_check.cpp')),'/Feyard_check.exe','/link',
    '/LIBPATH:'+str(OUT),'/LIBPATH:'+str(ROOT/'bin'),'Common.lib','DALib.lib','dacom.lib']
with (OUT/'yard_compile.log').open('wb') as log:r=subprocess.run(args,cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT)
if r.returncode:print((OUT/'yard_compile.log').read_text(errors='replace')[-9000:])
r.check_returncode()
with (OUT/'yard_check.log').open('wb') as log:r=subprocess.run([str(OUT/'yard_check.exe'),str(ASSETS)],cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT)
print((OUT/'yard_check.log').read_text(errors='replace'));r.check_returncode()
checked=[OUT/'Common.dll',Path(__file__),Path(__file__).with_name('yard_check.cpp'),ASSETS/'yard_guns.ini',ASSETS/'yard_flags.ini',GAME/'DATA/EQUIPMENT/ORIGINAL/weapon_equip.ini']+[ASSETS/(n+'.'+e) for n in ['train_locomotive','train_wagons'] for e in ['cmp','sur']]
(ASSETS/'checked.json').write_text(json.dumps({str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in checked},indent=2))
