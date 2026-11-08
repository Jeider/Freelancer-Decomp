"""Stage/install smooth coupling, the Beta dock icon and capital maneuver flags."""
import ast,json,re,shutil,sys
from datetime import datetime
from pathlib import Path
from player import ROOT,GAME,GEN,section,value,set_value
from install import sha,replace,idle
from yard_update import RUNTIME,checks

OUT=ROOT/'out/train_consist/smooth_hud'
ICON='DATA/INTERFACE/HUD/EXTRA/hud_train_couple.3db'
ICON_SOURCE=ROOT/'src/obj/train_coupling_hud'/ICON
CAPITAL=GEN+'world/capital.py'
TEMPLATES=[GEN+'templates/hardcoded_inis/shiparch/playerships/'+n+'.ini' for n in ['ge_train_player','ge_train_yard']]
TEMPLATES += [GEN+'templates/hardcoded_inis/shiparch/capships/'+n+'.ini' for n in ['li_dreadnought','br_battleship','ku_battleship','rh_battleship','or_osiris']]
TEMPLATES += [GEN+'templates/'+n for n in ['hardcoded_inis/static_content/shiparch.ini','hardcoded_inis/shiparch/shiparch2.ini']]
SHIPARCH=['DATA/SHIPS/shiparch.ini','DATA/SHIPS/shiparch2.ini']
TRAINS={'ge_train_player','ge_train_loco_player','ge_train_wagons'}
FILES=set(RUNTIME)|{ICON,CAPITAL}|set(TEMPLATES)|set(SHIPARCH)

def verified():
    checks()
    record=ROOT/'src/obj/train_coupling_hud/check/checked.json'
    for n,h in json.loads(record.read_text()).items():assert sha(Path(n))==h,'HUD check input changed: '+n

def ships(text):
    result={}
    for match in re.finditer(r'(?im)^\[Ship\][^\[]*',text):
        name=value(match[0],'nickname')
        if name:result[name]=match[0]
    return result

def flags(text,names):
    def replace_ship(match):
        ship=match[0]
        if value(ship,'nickname') not in names:return ship
        if value(ship,'extra_maneuvers') is None:
            newline='\r\n' if '\r\n' in ship else '\n'
            ship=re.sub(r'(?im)^(\[Ship\]\r?\n)',lambda m:m[0]+'extra_maneuvers = false'+newline,ship,count=1)
        else:ship=set_value(ship,'extra_maneuvers','false')
        return ship
    return re.sub(r'(?im)^\[Ship\][^\[]*',replace_ship,text)

def data():
    OUT.mkdir(parents=True,exist_ok=True)
    raw=(GAME/CAPITAL).read_bytes();source=raw.decode('utf-8')
    needle="            f'nickname = {self.ARCHETYPE}',"
    assert source.count(needle)==1 and 'extra_maneuvers' not in source
    newline='\r\n' if '\r\n' in source else '\n'
    patched=source.replace(needle,needle+newline+"            'extra_maneuvers = false',")
    ast.parse(patched)
    payload={CAPITAL:patched.encode('utf-8')}
    for path in TEMPLATES:
        text=(GAME/path).read_bytes().decode('utf-8')
        names=set(ships(text)) if '/capships/' in path else TRAINS|{
            n for n,b in ships(text).items() if (value(b,'type') or '').upper() in ['CAPITAL','CRUISER','GUNBOAT']}
        payload[path]=flags(text,names).encode('utf-8')
    for path,content in payload.items():
        target=OUT/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
    import check_player as check
    import world.capital as capital
    original=capital.Capital.root
    check.OUT=OUT
    before={manager:check.generate(manager,False) for manager in [check.ShiparchManager,check.ShiparchManagerV2]}
    tree=ast.parse(patched);cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Capital')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='root')
    scope=dict(vars(capital));exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),CAPITAL,'exec'),scope)
    changed=set()
    try:
        capital.Capital.root=scope['root']
        for manager,old in before.items():
            new=check.generate(manager,True);a,b=ships(old),ships(new)
            assert a.keys()==b.keys()
            names={name for name in a if a[name]!=b[name]}
            assert names and all(value(b[n],'extra_maneuvers')=='false' for n in names)
            # The only generator changes must be the requested per-ship flags.
            stripped=re.sub(r'(?im)^extra_maneuvers\s*=\s*false\r?\n','',new)
            assert stripped==old,'Unrelated generator change'
            changed.update(names)
            print('PASS:',manager.__name__,len(names),'capital/train definitions; only extra_maneuvers changed')
    finally:capital.Capital.root=original
    for path in SHIPARCH:
        original=(GAME/path).read_bytes().decode('utf-8');prepared=flags(original,changed)
        assert re.sub(r'(?im)^extra_maneuvers\s*=\s*false\r?\n','',prepared)==original
        payload[path]=prepared.encode('utf-8')
    payload[ICON]=ICON_SOURCE.read_bytes()
    (OUT/'data_check.json').write_text(json.dumps({'capital_ships':sorted(changed-TRAINS),'trains':sorted(changed&TRAINS)},indent=2))
    return payload

def prepare():
    verified()
    known={n:{sha(ROOT/n)} for n in RUNTIME}
    for path in [ROOT/'out/train_yard/installed.json']+list((ROOT/'out/train_consist').glob('*/installed.json')):
        for n,r in json.loads(path.read_text()).get('files',{}).items():
            if n in known:known[n].add(r['installed'])
    for n,h in known.items():
        if not n.endswith('.pdb'):assert sha(GAME/n) in h,'Unrecognized installed runtime: '+n
    payload=data();payload.update({n:p.read_bytes() for n,p in RUNTIME.items()})
    assert set(payload)==FILES
    records={}
    for n,content in payload.items():
        target=OUT/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(content)
        records[n]={'original':sha(GAME/n),'installed':sha(target)}
    deps=['bin/Content.dll','SAVE/Accts/SinglePlayer/biz_le2_train_yard.fl','DATA/COCKPITS/UTILITY/ge_train_player.ini']
    deps += ['DATA/SHIPS/UTILITY/FREIGHT_TRAIN/'+n+'.'+e for n in ['train_consist','train_locomotive','train_wagons'] for e in ['cmp','sur']]
    sources=['src/Directory.Build.targets','src/Common/common_train.cpp','src/Common/common_train.h','src/Common/common_archetype_ships.cpp',
        'src/Common/common_archetypeloader.cpp','src/include/common_archetype.h','src/include/train_yard_bridge.h',
        'src/Server/server_train_yard.cpp']
    sources += ['src/freelancer/Client/'+n for n in ['player_train.cpp','player_train.h','player_flight_actions.cpp',
        'hud_maneuvers.cpp','nn_button_control.cpp','player_behavior.cpp','space_camera_game.cpp']]
    for project in ['Server','freelancer']:
        tlog=ROOT/f'src/obj/train_yard/{project}/obj/{project}.tlog/CL.command.1.tlog'
        rows=tlog.read_text(encoding='utf-16').splitlines()
        commands=[rows[i+1] for i,r in enumerate(rows[:-1]) if r.startswith('^')]
        assert commands and all('FREELANCER_RPG_WORLD' in c for c in commands)
    manifest={'files':records,'dependencies':{n:sha(GAME/n) for n in deps},
        'sources':{str(ROOT/n):sha(ROOT/n) for n in sources},'FreelancerRpgWorld':1,
        'icon_source':json.loads(ICON_SOURCE.with_suffix('.json').read_text())}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Staged',len(records),'files; save and models preserved.')

def install(apply):
    verified();m=json.loads((OUT/'manifest.json').read_text());records=m['files']
    assert set(records)==FILES
    for n,r in records.items():
        assert sha(GAME/n)==r['original'],'Concurrent target change: '+n
        assert sha(OUT/n)==r['installed'],'Payload changed: '+n
    for n,p in RUNTIME.items():assert sha(p)==records[n]['installed']
    for n,h in m['sources'].items():assert sha(Path(n))==h,'Source changed: '+n
    for n,h in m['dependencies'].items():assert sha(GAME/n)==h,'Dependency changed: '+n
    if not apply:print('Validated smooth coupling and maneuver HUD update.');return
    idle();backup=GAME/'BACKUP'/('codex_train_smooth_hud_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for n,r in records.items():
        if r['original'] is not None:
            p=backup/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/n,p);assert sha(p)==r['original']
    (backup/'manifest.json').write_text(json.dumps(records,indent=2))
    changed=[]
    try:
        for n,r in records.items():
            assert sha(GAME/n)==r['original'],'Concurrent target change: '+n
            replace(OUT/n,GAME/n);changed.append(n);assert sha(GAME/n)==r['installed']
    except BaseException:
        for n in reversed(changed):
            if records[n]['original'] is None:(GAME/n).unlink()
            else:replace(backup/n,GAME/n)
        raise
    m['backup']=str(backup);(OUT/'installed.json').write_text(json.dumps(m,indent=2))
    print('Installed and verified. Backup:',backup)

if __name__=='__main__':
    if '--data-only' in sys.argv:data()
    else:prepare()
