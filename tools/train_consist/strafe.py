"""Add maneuvering thrust to the two player trains, preserving PythonLancer sources."""
import json,re,shutil
from datetime import datetime
from player import ROOT,GAME,GEN,PLAYER_TEMPLATE,section,value,set_value,sha

OUT=ROOT/'out/train_consist/strafe'
FORCE='60000'
SHIPS=('ge_train_player','ge_train_loco_player')
CONFIGS={GEN+'templates/'+PLAYER_TEMPLATE:SHIPS[:1],
         GEN+'templates/hardcoded_inis/shiparch/playerships/ge_train_yard.ini':SHIPS[1:],
         'DATA/SHIPS/shiparch.ini':SHIPS,'DATA/SHIPS/shiparch2.ini':SHIPS}

def adjust(text,names=SHIPS):
    for name in names:
        a,b,ship=section(text,'Ship',name)
        if value(ship,'strafe_force') is not None:ship=set_value(ship,'strafe_force',FORCE)
        else:
            ship,count=re.subn(r'(?im)^(nudge_force[^\r\n]*)(\r?\n)',lambda m:m[1]+m[2]+'strafe_force = '+FORCE+m[2],ship)
            assert count==1,name
        text=text[:a]+ship+text[b:]
    return text

def digest(path):return sha(path.read_bytes())

def prepare():
    records={}
    for name,ships in CONFIGS.items():
        raw=(GAME/name).read_bytes();updated=adjust(raw.decode('utf-8'),ships).encode('utf-8')
        target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(updated)
        records[name]={'original':sha(raw),'installed':sha(updated)}
    import check_player as check
    check.OUT=OUT
    for manager in [check.ShiparchManager,check.ShiparchManagerV2]:
        before=check.generate(manager,False);after=check.generate(manager,True)
        assert after==adjust(before),'Unrelated generated ships changed'
        assert value(section(after,'Ship','ge_train_wagons')[2],'strafe_force') in (None,'0')
        print('PASS:',manager.__name__,'player train strafe only; NPCs and wagons unchanged')
    (OUT/'manifest.json').write_text(json.dumps({'files':records,'strafe_force':FORCE},indent=2))
    print('Staged strafe_force =',FORCE,'for',', '.join(SHIPS))

def install(apply):
    from install import replace
    m=json.loads((OUT/'manifest.json').read_text());records=m['files']
    assert set(records)==set(CONFIGS) and m['strafe_force']==FORCE
    for name,r in records.items():
        assert digest(GAME/name)==r['original'] and digest(OUT/name)==r['installed'],name
    if not apply:return
    backup=GAME/'BACKUP'/('codex_train_strafe_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for name,r in records.items():
        path=backup/name;path.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/name,path)
        assert digest(path)==r['original']
    shutil.copy2(OUT/'manifest.json',backup/'manifest.json')
    changed=[]
    try:
        for name,r in records.items():
            assert digest(GAME/name)==r['original'],'Concurrent target change: '+name
            replace(OUT/name,GAME/name);changed.append(name)
            assert digest(GAME/name)==r['installed']
    except BaseException:
        for name in reversed(changed):replace(backup/name,GAME/name)
        raise
    m['backup']=str(backup);(OUT/'installed.json').write_text(json.dumps(m,indent=2))
    print('Installed 4 INIs; restart game to apply. Backup:',backup)

if __name__=='__main__':prepare()
