"""Stage the player-only archetype, both PythonLancer sources, and a new space save.

No game files are written here. install.py --player installs the reviewed manifest.
"""
import hashlib
import json
from pathlib import Path
import re
import time

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/games/FL_MOD')
OUT=ROOT/'out/train_consist/player20'
GEN='Assets/Pythonlancer/'
PLAYER='ge_train_player'
SAVE_NAME='biz_le2_train20'
SAVE_FILE='SAVE/Accts/SinglePlayer/biz_le2_train20.fl'
WAGONS=20
CAMERA_OFFSET='30, 52'
PLAYER_COCKPIT=r'cockpits\utility\ge_train_player.ini'
LOD_RANGES='0, 1000000'
PLAYER_TEMPLATE='hardcoded_inis/shiparch/playerships/ge_train_player.ini'
TEMPLATES=['hardcoded_inis/static_content/shiparch.ini','hardcoded_inis/shiparch/shiparch2.ini']
NPC_MODEL=r'ships\utility\freight_train\freight_trainx2.3db'
TRAIN_MODEL=r'ships\utility\freight_train\train_consist.cmp'


def sha(raw):return hashlib.sha256(raw).hexdigest()


def section(text,kind,nickname=None):
    matches=[]
    for m in re.finditer(r'(?im)^\[([^]\r\n]+)\][^\r\n]*',text):
        end=re.search(r'(?m)^\[',text[m.end():])
        stop=m.end()+end.start() if end else len(text)
        body=text[m.start():stop]
        if m[1].lower()==kind.lower() and (nickname is None or value(body,'nickname')==nickname):
            matches.append((m.start(),stop,body))
    assert len(matches)==1,(kind,nickname,len(matches))
    return matches[0]


def value(text,key):
    m=re.search(r'(?im)^'+re.escape(key)+r'[ \t]*=[ \t]*([^\r\n]*)',text)
    return m[1].strip() if m else None


def set_value(text,key,new):
    text,n=re.subn(r'(?im)^('+re.escape(key)+r'[ \t]*=[ \t]*)[^\r\n]*',lambda m:m[1]+new,text)
    assert n==1,(key,n)
    return text


def player_definition():
    text=(GAME/GEN/'templates'/PLAYER_TEMPLATE).read_text(encoding='utf-8')
    assert value(text,'nickname')==PLAYER and value(text,'DA_archetype')==TRAIN_MODEL
    text=set_value(text,'camera_offset',CAMERA_OFFSET)
    text=set_value(text,'cockpit',PLAYER_COCKPIT)
    text=set_value(text,'LODranges',LOD_RANGES)
    text,n=re.subn(r'(?im)^hp_type\s*=\s*hp_cargo_pod[^\r\n]*',
        'hp_type = hp_cargo_pod, '+', '.join(f'HpCargo{i:02}' for i in range(1,WAGONS*2+1)),text)
    assert n==1
    return text


def config(text,definition):
    start,end,npc=section(text,'Ship','ge_train')
    assert value(npc,'DA_archetype') in (NPC_MODEL,TRAIN_MODEL)
    restored=set_value(npc,'DA_archetype',NPC_MODEL)
    text=text[:start]+restored+text[end:]
    newline='\r\n' if '\r\n' in text else '\n'
    start,end,old=section(text,'Ship',PLAYER)
    return text[:start]+definition.rstrip().replace('\n',newline)+newline*2+text[end:]


def transform(raw):
    return bytes(v^(((b'Gene'[i&3]+i)&255)|128) for i,v in enumerate(raw))


def decode(raw):
    assert not raw.startswith(b'FLSG'),'Unsupported save container'
    return transform(raw[4:]) if raw.startswith(b'FLS1') else raw


def equipment():
    items=[('ge_t_engine_01',''),('infinite_power',''),('scanner01',''),('tractor01',''),
           ('sfx_rumble_ut_large','')]
    items += [('co_train_turret01_mark01',f'HpTurret{i:02}') for i in range(1,7)]
    items += [('SlowMediumWhite',f'HpRunningLight{i:02}') for i in range(1,8+4*WAGONS)]
    items += [('DockingLightRed',f'HpDockLight{i:02}') for i in (2,3)]
    items += [('LargeWhiteSpecialPlayer',f'HpHeadLight{i:02}') for i in (1,2)]
    items += [('cargopod_grey',f'HpCargo{i:02}') for i in range(1,2*WAGONS+1)]
    return items


def make_save():
    found=[]
    for path in (GAME/'SAVE/Accts/SinglePlayer').glob('*.fl'):
        raw=path.read_bytes();text=decode(raw).decode('latin1')
        desc=value(text,'description')
        if not desc:continue
        try: label=bytes.fromhex(desc).decode('utf-16-be').rstrip('\0')
        except (ValueError,UnicodeError):continue
        if label=='biz_le2':found.append((path,raw,text))
    assert len(found)==1,'Need a unique biz_le2 source save'
    path,raw,text=found[0]
    begin,end,player=section(text,'Player')
    assert value(player,'base') is None and value(player,'system')=='rh_biz' and value(player,'pos'), 'Source must be in space'
    original_player=player
    player=set_value(player,'description',SAVE_NAME.encode('utf-16-be').hex())
    stamp=time.time_ns()//100+116444736000000000
    player=set_value(player,'tstamp',f'{stamp>>32},{stamp&0xffffffff}')
    player=set_value(player,'ship_archetype',PLAYER)
    # Only the active ship changes. World state, missions, money and cargo remain.
    discard={'equip','wg','collision_group','hull_status','descrip_strid','cloak_cooldown'}
    player=''.join(line for line in player.splitlines(keepends=True) if line.split('=',1)[0].strip().lower() not in discard)
    newline='\r\n' if '\r\n' in player else '\n'
    loadout=[f'equip = {name}, {hp}, 1' for name,hp in equipment()]
    loadout += [f'wg = 0, HpTurret{i:02}' for i in range(1,7)]
    loadout += ['hull_status = 1','descrip_strid = 0']
    # Put equipment after the ship, before all existing cargo and exploration data.
    match=re.search(r'(?im)^ship_archetype[^\n]*\n',player)
    player=player[:match.end()]+newline+newline.join(loadout)+newline+player[match.end():]
    for key in ['system','pos','rotate','money','rank','name']:
        assert value(player,key)==value(original_player,key),key
    result=(text[:begin]+player+text[end:]).encode('latin1')
    assert result.endswith(text[end:].encode('latin1'))
    encoded=b'FLS1'+transform(result)
    assert decode(encoded)==result
    return encoded,{'source':str(path),'source_sha256':sha(raw),'description':SAVE_NAME,'ship':PLAYER,
                    'system':value(player,'system'),'pos':value(player,'pos'),'rotate':value(player,'rotate'),
                    'equipment':equipment(),'money':value(player,'money')}


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    definition=player_definition()
    payload={GEN+'templates/'+PLAYER_TEMPLATE:definition.encode('utf-8')}
    include='{% include "'+PLAYER_TEMPLATE+'" %}'
    for name in TEMPLATES:
        rel=GEN+'templates/'+name
        raw=(GAME/rel).read_bytes()
        text=raw.decode('utf-8')
        assert text.count(include)==1,'Expected persistent player include'
        assert value(section(text,'Ship','ge_train')[2],'DA_archetype')==NPC_MODEL
        payload[rel]=raw
    for name in ['shiparch.ini','shiparch2.ini']:
        rel='DATA/SHIPS/'+name
        payload[rel]=config((GAME/rel).read_bytes().decode('utf-8'),definition).encode('utf-8')
    saved,report=make_save()
    assert not (GAME/SAVE_FILE).exists(),'Refusing to overwrite an existing player test save'
    payload[SAVE_FILE]=saved
    # The equipped train needs the checked wagon attachment fix in Common.
    runtime=ROOT/'src/obj/train_consist'
    checked=json.loads((runtime/'check.json').read_text())
    for name,digest in checked.items():
        assert sha(Path(name).read_bytes())==digest,'Native checked input changed: '+name
    for name in ['Common.dll','Common.pdb']:
        payload['bin/'+name]=(runtime/name).read_bytes()
    for name in ['train_consist.cmp','train_consist.sur']:
        payload['DATA/SHIPS/UTILITY/FREIGHT_TRAIN/'+name]=(ROOT/'out/train_consist'/name).read_bytes()
    records={}
    for name,raw in payload.items():
        target=OUT/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        records[name]={'original':sha((GAME/name).read_bytes()) if (GAME/name).exists() else None,'installed':sha(raw)}
    # Require the known previous installation before applying this migration.
    previous=json.loads((ROOT/'out/train_consist/installed.json').read_text())
    dependencies={name:r['installed'] for name,r in previous['files'].items() if name!='DATA/SHIPS/shiparch.ini'}
    player_install=json.loads((ROOT/'out/train_consist/player/installed.json').read_text())
    for name in ['bin/Common.dll','bin/Common.pdb']:
        dependencies[name]=player_install['files'][name]['installed']
    dependencies[Path(report['source']).relative_to(GAME).as_posix()]=report['source_sha256']
    for name,digest in dependencies.items():assert sha((GAME/name).read_bytes())==digest,'Installed dependency changed: '+name
    manifest={'files':records,'dependencies':dependencies,'save':report,'wagons':WAGONS}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Staged player-only train and PythonLancer V1/V2 sources.')
    print('New save:',SAVE_NAME,'in',report['system'],report['pos'],'from',report['source'])
    return manifest


if __name__=='__main__':prepare()
