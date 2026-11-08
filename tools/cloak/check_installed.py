"""Verify the actual installed Common.dll and staged player cloak definitions."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
sys.dont_write_bytecode=True
from restore_config import ROOT,GAME,OUT,FILES,restore
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def blocks(data):return re.split(r'(?m)(?=^\[)',data)
def player_blocks(data):
    return [b for b in blocks(data) if b.startswith('[CloakingDevice]') and re.search(r'(?m)^nickname\s*=\s*pl_cloak_(fast|slow)\s*$',b)]

def main():
    staged=OUT/'staged'
    sys.path.insert(0,str(GAME/'Assets/Pythonlancer'))
    from jinja2 import Environment,FileSystemLoader,StrictUndefined
    import difficulty
    template=staged/FILES[1]
    env=Environment(loader=FileSystemLoader(str(template.parent)),undefined=StrictUndefined)
    live=(staged/FILES[0]).read_text()
    for diff in (difficulty.EasyDifficulty,difficulty.NormalDifficulty,difficulty.HardDifficulty):
        result=env.get_template(template.name).render(diff=diff)
        assert player_blocks(result)==player_blocks(live)
        assert restore(result.encode())==result.encode()
    print('PASS: actual Pythonlancer template preserves cloak settings in Easy/Normal/Hard')
    config='\n'.join(player_blocks(live))
    cpp=r'''
#define main NativeBehaviorMain
#include "test_native.cpp"
#undef main
int main(int argc,char** argv){
 int result=NativeBehaviorMain(argc,argv);if(result)return result;
 char path[MAX_PATH];GetModuleFileNameA(GetModuleHandleA("Common.dll"),path,MAX_PATH);
 printf("LOADED %s\n",path);
 printf("IDS {\"li_freighter\":%u,\"pl_cloak_slow\":%u,\"pl_cloak_fast\":%u}\n",CreateID("li_freighter"),CreateID("pl_cloak_slow"),CreateID("pl_cloak_fast"));
'''
    for b in player_blocks(config):
        # The equipment loader handles visual/resource metadata outside Root::read.
        # Feed the actual gameplay fields to the same native archetype parser.
        keys={'nickname','hp_type','hit_pts','default_state','cloak_duration','cooldown_time','toggle_cooldown','cloakin_time','cloakout_time'}
        b='[CloakingDevice]\n'+'\n'.join(line for line in b.splitlines() if '=' in line and line.split('=',1)[0].strip() in keys)+'\n'
        cpp+='\n{Archetype::CloakingDevice arch;Parse(arch,R"INI('+b+')INI");\n'
        cpp+='''
 auto cfg=arch.GetSettings();assert(cfg.enabled&&!cfg.defaultState&&cfg.duration==30&&cfg.cooldown==20&&Near(cfg.toggleCooldown,.3f));
 CECloakingDevice device(nullptr,10,&arch,false);assert(!device.IsActive()&&device.cloak_percent()==0);
 device.Activate(true);device.Update(arch.CloakOutTime,0);assert(device.cloak_percent()==1&&Near(device.GetDurationRemaining(),30));
 device.Update(30,0);assert(!device.IsActive());device.Update(arch.CloakInTime,0);
 assert(device.cloak_percent()==0&&Near(device.GetCooldownRemaining(),20));assert(!device.CanToggle());
 device.Update(20,0);assert(device.CanToggle());}
'''
    cpp+='puts("PASS: installed Common.dll executes restored player defaults, expiry and recharge");return 0;}\n'
    source=OUT/'check.cpp';source.write_text(cpp)
    compiler,envvars=compiler_env();envvars['PATH']=str(GAME/'bin')+';'+envvars['PATH']
    envvars['INCLUDE']+=';'+str(ROOT/'src/include')+';'+str(ROOT/'tools/cloak')
    envvars['LIB']+=';'+str(ROOT/'bin')
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2','/MD','/D_ITERATOR_DEBUG_LEVEL=1',
        '/D_CRT_SECURE_NO_WARNINGS',str(source),'/Fo'+str(OUT/'check.obj'),'/Fe'+str(OUT/'check.exe'),
        '/link','Common.lib','dacom.lib'],env=envvars,cwd=OUT,check=True)
    (OUT/'port.ini').write_text('[Equipment]\ninternal_classes=1\n')
    result=subprocess.run([str(OUT/'check.exe'),str(ROOT/'tools/cloak/equipment.ini')],env=envvars,cwd=OUT,capture_output=True,text=True)
    print(result.stdout);print(result.stderr[-1500:] if result.returncode else '',end='');result.check_returncode()
    loaded=re.search(r'(?m)^LOADED (.+)$',result.stdout)[1].strip()
    assert Path(loaded).resolve()==(GAME/'bin/Common.dll').resolve()
    ids=json.loads(re.search(r'(?m)^IDS (.+)$',result.stdout)[1]);saves=[]
    for p in (GAME/'SAVE/Accts/SinglePlayer').glob('*.fl'):
        raw=p.read_bytes()
        if raw.startswith(b'FLS1'):raw=bytes(v^(((b'Gene'[i&3]+i)&255)|128) for i,v in enumerate(raw[4:]))
        text=raw.decode('latin1')
        if not re.search(r'(?im)^ship_archetype\s*=\s*(?:li_freighter|'+str(ids['li_freighter'])+r')\s*$',text):continue
        cloaks=[nick for nick,id in ids.items() if nick.startswith('pl_cloak') and re.search(r'(?im)^equip\s*=\s*(?:'+nick+'|'+str(id)+r')\s*,',text)]
        saves.append({'file':p.name,'cloaks':cloaks})
    (OUT/'save_audit.json').write_text(json.dumps(saves,indent=2))
    print('READ-ONLY li_freighter save audit:',saves)

if __name__=='__main__':main()
