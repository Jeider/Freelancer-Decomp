"""Upgrade the installed yard: wider coupling, six turrets, and a clear spawn."""
import json,math,re,shutil
from datetime import datetime
from pathlib import Path
from player import ROOT,GAME,GEN,section,value,set_value,decode,transform

OUT=ROOT/'out/train_consist/yard_update'
BIN=ROOT/'src/obj/train_consist'
SAVE='SAVE/Accts/SinglePlayer/biz_le2_train_yard.fl'
TEMPLATE=GEN+'templates/hardcoded_inis/shiparch/playerships/ge_train_yard.ini'
CONFIGS=[TEMPLATE,'DATA/SHIPS/shiparch.ini','DATA/SHIPS/shiparch2.ini']
RUNTIME={}
for name,folder,ext in [('Common',BIN,'dll'),('Server',ROOT/'src/obj/train_yard/Server/bin','dll'),
                        ('freelancer',ROOT/'src/obj/train_yard/freelancer/bin','exe')]:
    for suffix in [ext,'pdb']:RUNTIME['bin/'+name+'.'+suffix]=folder/(name+'.'+suffix)


def adjust(text):
    a,b,ship=section(text,'Ship','ge_train_wagons')
    if 'hp_type = hp_turret, HpTurret06' not in ship:
        newline='\r\n' if '\r\n' in ship else '\n'
        ship=re.sub(r'(?m)^mass\s*=',lambda m:'hp_type = hp_turret, HpTurret06'+newline+m[0],ship,count=1)
    assert ship.count('hp_type = hp_turret, HpTurret06')==1
    return text[:a]+ship+text[b:]


def move_save(raw,distance=30):
    text=decode(raw).decode('latin1');a,b,ship=section(text,'Player')
    assert value(ship,'ship_archetype')=='ge_train_loco_player' and value(ship,'base') is None
    pos=[float(x) for x in value(ship,'pos').split(',')]
    pitch,yaw,roll=[math.radians(float(x)) for x in value(ship,'rotate').split(',')]
    # EulerMatrix's third column, negated: Freelancer's forward is local -Z.
    forward=[-(math.cos(roll)*math.cos(pitch)*math.sin(yaw)+math.sin(roll)*math.sin(pitch)),
             -(math.sin(roll)*math.cos(pitch)*math.sin(yaw)-math.cos(roll)*math.sin(pitch)),
             -math.cos(yaw)*math.cos(pitch)]
    moved=[p+distance*f for p,f in zip(pos,forward)]
    new=set_value(ship,'pos',','.join(f'{p:.6f}' for p in moved))
    assert set_value(new,'pos',value(ship,'pos'))==ship,'Save fields other than position changed'
    return b'FLS1'+transform((text[:a]+new+text[b:]).encode('latin1')),{'before':pos,'after':moved,'forward_m':distance}


def checks():
    from install import sha
    for record in [ROOT/'out/train_yard/checked.json',BIN/'check.json']:
        for path,h in json.loads(record.read_text()).items():assert sha(Path(path))==h,'Checked input changed: '+path


def prepare():
    from install import sha
    checks()
    installed_records=[ROOT/'out/train_yard/installed.json']+list((ROOT/'out/train_consist').glob('*/installed.json'))
    known={name:{sha(ROOT/name)} for name in RUNTIME}
    for record in installed_records:
        for name,r in json.loads(record.read_text()).get('files',{}).items():
            if name in known:known[name].add(r['installed'])
    # Installed symbols can be stale even when the paired runtime is a known build.
    # Guard executable code here; preserve and hash every current PDB in the backup.
    for name,hashes in known.items():
        if not name.endswith('.pdb'):
            assert sha(GAME/name) in hashes,'Unrecognized installed runtime: '+name
    import check_player as check
    check.OUT=OUT
    payload={n:adjust((GAME/n).read_bytes().decode('utf-8')).encode('utf-8') for n in CONFIGS}
    payload[SAVE],movement=move_save((GAME/SAVE).read_bytes())
    payload.update({name:path.read_bytes() for name,path in RUNTIME.items()})
    records={}
    for name,raw in payload.items():
        path=OUT/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        records[name]={'original':sha(GAME/name),'installed':sha(path)}
    for manager in [check.ShiparchManager,check.ShiparchManagerV2]:
        before=check.generate(manager,False);after=check.generate(manager,True)
        assert after==adjust(before),'Unrelated generated ship changed'
        print('PASS:',manager.__name__,'persists last-wagon turret; other ships unchanged')
    tlog=ROOT/'src/obj/train_yard/freelancer/obj/freelancer.tlog/CL.command.1.tlog'
    rows=tlog.read_text(encoding='utf-16').splitlines()
    commands=[rows[i+1] for i,r in enumerate(rows[:-1]) if r.startswith('^')]
    assert commands and all('FREELANCER_RPG_WORLD' in c for c in commands),'RPG flag lost'
    deps=['bin/Content.dll','DATA/COCKPITS/UTILITY/ge_train_player.ini',
          GEN+'templates/hardcoded_inis/shiparch/playerships/ge_train_player.ini']
    deps += ['DATA/SHIPS/UTILITY/FREIGHT_TRAIN/'+name+'.'+ext for name in
             ['train_locomotive','train_wagons','train_consist'] for ext in ['cmp','sur']]
    source_files=['src/Common/common_train.cpp','src/Server/server_train_yard.cpp',
                  'src/freelancer/Client/player_train.cpp','src/freelancer/Client/cli_projectile_fx.cpp',
                  'src/freelancer/Client/client_iclient_space.cpp',
                  'src/include/train_yard_bridge.h']
    m={'files':records,'dependencies':{n:sha(GAME/n) for n in deps},'movement':movement,
       'sources':{str(ROOT/n):sha(ROOT/n) for n in source_files},'FreelancerRpgWorld':1}
    (OUT/'manifest.json').write_text(json.dumps(m,indent=2))
    print('Staged',len(records),'files; save moved forward 30 m, capture 15 m, initial pin gap 12 m.')


def install(apply):
    from install import sha,replace,idle
    checks();m=json.loads((OUT/'manifest.json').read_text());records=m['files']
    assert set(records)==set(RUNTIME)|set(CONFIGS)|{SAVE}
    for n,r in records.items():
        assert sha(GAME/n)==r['original'],'Concurrent target change: '+n
        assert sha(OUT/n)==r['installed'],'Staged file changed: '+n
    for n,p in RUNTIME.items():assert sha(p)==records[n]['installed'],'Built runtime changed: '+n
    for n,h in m['dependencies'].items():assert sha(GAME/n)==h,'Dependency changed: '+n
    for n,h in m['sources'].items():assert sha(Path(n))==h,'Source changed: '+n
    if not apply:
        print('Validated yard update.');return
    idle();backup=GAME/'BACKUP'/('codex_train_yard_update_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for n,r in records.items():
        p=backup/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/n,p)
        assert sha(p)==r['original']
    (backup/'manifest.json').write_text(json.dumps(records,indent=2))
    changed=[]
    try:
        for n,r in records.items():
            assert sha(GAME/n)==r['original'],'Concurrent target change: '+n
            replace(OUT/n,GAME/n);changed.append(n);assert sha(GAME/n)==r['installed']
    except BaseException:
        for n in reversed(changed):replace(backup/n,GAME/n)
        raise
    m['backup']=str(backup);(OUT/'installed.json').write_text(json.dumps(m,indent=2))
    print('Installed and verified. Backup:',backup)


if __name__=='__main__':prepare()
