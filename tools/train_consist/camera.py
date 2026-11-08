"""Stage/install only the player train camera INIs; executable files are untouched."""
import json
import shutil
from datetime import datetime
from pathlib import Path
from player import ROOT,GAME,GEN,PLAYER,PLAYER_TEMPLATE,PLAYER_COCKPIT,CAMERA_OFFSET,NPC_MODEL,section,value,set_value,sha

OUT=ROOT/'out/train_consist/camera'
CONFIGS=[GEN+'templates/'+PLAYER_TEMPLATE,'DATA/SHIPS/shiparch.ini','DATA/SHIPS/shiparch2.ini']
COCKPIT='DATA/COCKPITS/UTILITY/ge_train_player.ini'
SOURCE=ROOT/'DATA_EXTRA/COCKPITS/UTILITY/ge_train_player.ini'
BASE_COCKPIT='DATA/COCKPITS/LIBERTY/l_freighter.ini'
TETHER='0, 30, 48'
FILES=set(CONFIGS+[COCKPIT])


def adjust(text):
    a,b,ship=section(text,'Ship',PLAYER)
    ship=set_value(ship,'camera_offset',CAMERA_OFFSET)
    ship=set_value(ship,'cockpit',PLAYER_COCKPIT)
    return text[:a]+ship+text[b:]


def file_sha(path):
    return sha(path.read_bytes()) if path.exists() else None


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    payload={n:adjust((GAME/n).read_bytes().decode('utf-8')).encode('utf-8') for n in CONFIGS}
    payload[COCKPIT]=SOURCE.read_bytes()
    model=ROOT/'out/train_consist/data.json'
    data=json.loads(model.read_text())
    assert all('hpcockpit' not in [n.lower() for n in p['hardpoints']] for p in data['parts'].values())
    # Third person uses HpCockpit's fallback (0,0,-4); turret tether is root-relative.
    y,z=map(float,CAMERA_OFFSET.split(','));x,ty,tz=map(float,TETHER.split(','))
    assert (x,ty,tz)==(0,y,z-4)
    source=payload[COCKPIT].decode('utf-8')
    base=(GAME/BASE_COCKPIT).read_text(encoding='utf-8')
    a,b,turret=section(base,'TurretCamera')
    expected=base[:a]+set_value(turret,'tether',TETHER)+base[b:]
    assert source.strip()==expected.strip(),'Shared cockpit properties must be preserved'
    assert (GAME/'DATA'/value(section(source,'Cockpit')[2],'mesh').replace('\\','/')).is_file()
    records={}
    for n,raw in payload.items():
        p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        records[n]={'original':file_sha(GAME/n),'installed':sha(raw)}
    model_file='DATA/SHIPS/UTILITY/FREIGHT_TRAIN/train_consist.cmp'
    assert file_sha(GAME/model_file)==data['files']['train_consist.cmp']
    deps=[BASE_COCKPIT,model_file]+[GEN+'templates/'+n for n in
        ['hardcoded_inis/static_content/shiparch.ini','hardcoded_inis/shiparch/shiparch2.ini']]
    manifest={'files':records,'dependencies':{n:file_sha(GAME/n) for n in deps},
              'source':str(SOURCE),'source_hash':file_sha(SOURCE),'camera_offset':CAMERA_OFFSET,'tether':TETHER}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    import check_player as check
    check.OUT=OUT
    for manager in [check.ShiparchManager,check.ShiparchManagerV2]:
        before=check.generate(manager,False);after=check.generate(manager,True)
        assert after==adjust(before),'Generator changed unrelated ships'
        assert value(section(after,'Ship','ge_train')[2],'DA_archetype')==NPC_MODEL
        ship=section(after,'Ship',PLAYER)[2]
        assert value(ship,'camera_offset')==CAMERA_OFFSET and value(ship,'cockpit')==PLAYER_COCKPIT
    (OUT/'checked.json').write_text(json.dumps({'manifest':file_sha(OUT/'manifest.json'),
        'files':{n:r['installed'] for n,r in records.items()}},indent=2))
    print('PASS: both PythonLancer generators; private cockpit; matching initial camera positions; shared cockpit preserved.')
    print('camera_offset =',CAMERA_OFFSET,'; turret tether =',TETHER)


def install(apply):
    from install import replace
    m=json.loads((OUT/'manifest.json').read_text());check=json.loads((OUT/'checked.json').read_text())
    assert file_sha(OUT/'manifest.json')==check['manifest']
    records=m['files'];assert set(records)==set(check['files'])==FILES
    assert file_sha(Path(m['source']))==m['source_hash']
    for n,r in records.items():
        assert file_sha(GAME/n)==r['original'],'Concurrent target change: '+n
        assert file_sha(OUT/n)==r['installed']==check['files'][n],'Staged file changed: '+n
    for n,digest in m['dependencies'].items():assert file_sha(GAME/n)==digest,'Dependency changed: '+n
    print('Validated camera INIs:',', '.join(records))
    if not apply:return
    # Only INIs are replaced, atomically. A running game can keep its loaded
    # configuration; the new settings take effect after the next game restart.
    backup=GAME/'BACKUP'/('codex_train_camera_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.mkdir(parents=True)
    for n,r in records.items():
        if r['original'] is not None:
            p=backup/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/n,p)
            assert file_sha(p)==r['original']
    (backup/'manifest.json').write_text(json.dumps(records,indent=2))
    changed=[]
    try:
        for n,r in records.items():
            assert file_sha(GAME/n)==r['original'],'Concurrent target change: '+n
            replace(OUT/n,GAME/n);changed.append(n)
            assert file_sha(GAME/n)==r['installed']
    except BaseException:
        for n in reversed(changed):
            if records[n]['original'] is None:(GAME/n).unlink()
            else:replace(backup/n,GAME/n)
        raise
    (OUT/'installed.json').write_text(json.dumps({'backup':str(backup),'files':records},indent=2))
    print('Installed camera INIs. Restart the game to load them. Backup:',backup)


if __name__=='__main__':prepare()
