"""Stage standalone locomotive/wagon models, persistent archetypes and a fresh space save."""
import copy, hashlib, json, re, struct, sys
from pathlib import Path
import prepare as base
import contrails
import player
ROOT=base.ROOT;GAME=base.GAME;OUT=ROOT/'out/train_yard'
sur=base.sur;u=base.u
S=struct
OUT.mkdir(parents=True,exist_ok=True)
hdr,trees=u.read_tree((ROOT/'out/train_consist/train_consist.cmp').read_bytes())
original=trees[0]

def model(name,wagons):
    root=copy.deepcopy(original);cmp=sur.child(root,'Cmpnd')
    fix=sur.child(sur.child(cmp,'Cons'),'Fix')
    rows=[fix.blob[i:i+176] for i in range(0,len(fix.blob),176)]
    entries=[n for n in cmp.children if sur.child(n,'Object name')]
    keep=[]
    for entry in entries:
        obj=sur.string(sur.child(entry,'Object name'))
        if obj.startswith('TrainWagon')==wagons:keep.append(entry)
        else:
            root.children.remove(base.partnode(root,entry));cmp.children.remove(entry)
    if wagons:
        first=keep[0];first.name='Root';sur.child(first,'Object name').blob=b'Root\0'
    for i,entry in enumerate(keep):sur.child(entry,'Index').blob=S.pack('<I',i)
    good=[]
    for row in rows:
        a,b,*rest=S.unpack('<64s64s3f9f',row)
        child=b.rstrip(b'\0').decode()
        if child.startswith('TrainWagon')!=wagons or (wagons and child=='TrainWagon01'):continue
        if wagons and a.rstrip(b'\0')==b'TrainWagon01':a=b'Root'
        good.append(S.pack('<64s64s3f9f',a,b,*rest))
    fix.blob=b''.join(good)
    contrails.annotate(root,wagons)
    path=OUT/(name+'.cmp');path.write_bytes(u.write_tree(hdr,[root]))
    parts=sur.read_cmp(path)
    regions=json.loads((ROOT/'tools/train_sur/regions.json').read_text())['train_cargo.cmp']['regions']['Root']
    own={n:sur.hulls_for(p,12,regions if wagons else None) for n,p in parts.items()}
    data=bytearray(b'vers'+S.pack('<f',2))
    for n,p in parts.items():
        hulls=own[n] if wagons else sur.transformed_hulls(n,parts,own)
        surface,lo,hi=sur.encode_surface(hulls)
        dynamic=wagons or n=='Root'
        data+=S.pack('<II',u.crc(n),3 if dynamic else 2)
        if dynamic:data+=b'!fxd'
        data+=b'exts'+S.pack('<6f',*lo,*hi)+b'surf'+S.pack('<I',len(surface))+surface
    (OUT/(name+'.sur')).write_bytes(data)
    assert len(parts)==(20 if wagons else 3)
    assert 'HpCoupleFront' in parts['Root'].hardpoints if wagons else 'HpCoupleRear' in parts['Root'].hardpoints
    print(name,':',len(parts),'parts; CMP/SUR staged')

model('train_locomotive',False)
model('train_wagons',True)

source=(GAME/player.GEN/'templates'/player.PLAYER_TEMPLATE).read_text(encoding='utf-8')
def definition(nick,model,tail):
    text=player.set_value(source,'nickname',nick)
    text=player.set_value(text,'DA_archetype','ships\\utility\\freight_train\\'+model+'.cmp')
    if tail:
        for key,value in [('mass','250'),('linear_drag','0'),('steering_torque','0, 0, 0'),
            ('angular_drag','100, 100, 100'),('rotation_inertia','100000, 100000, 100000'),('nudge_force','0'),('num_exhaust_nozzles','0')]:
            text=player.set_value(text,key,value)
    lines=[]
    for line in text.splitlines():
        if line.startswith('fuse ='):continue # Existing hull fuses reference the old monolithic train.
        if tail and line.startswith('strafe_force'):continue # Unpowered wagons must not inherit locomotive thrust.
        if tail and line.startswith('HP_tractor_source'):continue
        if tail and line.startswith('hp_type = hp_turret'):line='hp_type = hp_turret, HpTurret06'
        if not tail and (line.startswith('hp_type = hp_cargo_pod') or line.startswith('HP_bay_')):continue
        if not tail and line.startswith('hp_type = hp_turret'):line=line.replace(', HpTurret06','')
        lines.append(line)
    return '\n'.join(lines)+'\n'

payload={}
definitions=[definition('ge_train_loco_player','train_locomotive',False),definition('ge_train_wagons','train_wagons',True)]
template='hardcoded_inis/shiparch/playerships/ge_train_yard.ini'
combined='\n'.join(definitions)
payload[player.GEN+'templates/'+template]=combined.encode('utf-8')
for name in player.TEMPLATES:
    rel=player.GEN+'templates/'+name
    raw=(GAME/rel).read_bytes();text=raw.decode('utf-8')
    include='{% include "'+template+'" %}'
    assert include not in text
    anchor='{% include "'+player.PLAYER_TEMPLATE+'" %}'
    assert text.count(anchor)==1
    text=text.replace(anchor,anchor+'\n'+include)
    payload[rel]=text.encode('utf-8')
for name in ['shiparch.ini','shiparch2.ini']:
    rel='DATA/SHIPS/'+name;raw=(GAME/rel).read_bytes()
    assert b'nickname = ge_train_loco_player' not in raw
    payload[rel]=raw.rstrip()+b'\r\n\r\n'+combined.replace('\n','\r\n').encode('utf-8')
for name in ['train_locomotive','train_wagons']:
    for ext in ['cmp','sur']:payload['DATA/SHIPS/UTILITY/FREIGHT_TRAIN/'+name+'.'+ext]=(OUT/(name+'.'+ext)).read_bytes()
player.PLAYER='ge_train_loco_player';player.SAVE_NAME='biz_le2_train_yard'
player.WAGONS=0
def equipment():
    return [('ge_t_engine_01',''),('infinite_power',''),('scanner01',''),('tractor01',''),('sfx_rumble_ut_large','')]+[
        ('co_train_turret01_mark01',f'HpTurret{i:02}') for i in range(1,6)]
player.equipment=equipment
raw,report=player.make_save()
decoded=player.decode(raw).decode('latin1')
decoded=re.sub(r'(?m)^wg = 0, HpTurret06\r?\n','',decoded)
payload['SAVE/Accts/SinglePlayer/biz_le2_train_yard.fl']=b'FLS1'+player.transform(decoded.encode('latin1'))
from yard_update import move_save
payload['SAVE/Accts/SinglePlayer/biz_le2_train_yard.fl'],movement=move_save(payload['SAVE/Accts/SinglePlayer/biz_le2_train_yard.fl'])
report['movement']=movement
assert not (GAME/'SAVE/Accts/SinglePlayer/biz_le2_train_yard.fl').exists()
records={}
for name,raw in payload.items():
    path=OUT/'payload'/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
    records[name]={'original':player.sha((GAME/name).read_bytes()) if (GAME/name).exists() else None,'installed':player.sha(raw)}
(OUT/'assets.json').write_text(json.dumps({'files':records,'save':report},indent=2))
print('Staged persistent PythonLancer definitions and biz_le2_train_yard; game unchanged.')
