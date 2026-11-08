"""Verify both real PythonLancer generators and the independent yard save."""
import json,re,hashlib
from pathlib import Path
import check_player as check
from player import ROOT,GAME,GEN,section,value,decode,sha
OUT=ROOT/'out/train_yard';PAYLOAD=OUT/'payload'
check.OUT=PAYLOAD
names=['ge_train_loco_player','ge_train_wagons']
def without_yard(text):
    for nick in names:
        a,b,_=section(text,'Ship',nick);text=text[:a]+text[b:]
    return check.sections(text)
for kind in [check.ShiparchManager,check.ShiparchManagerV2]:
    before=check.generate(kind,False);after=check.generate(kind,True)
    assert without_yard(after)==check.sections(before),'Unrelated generated ships changed'
    for nick in names:
        installed=section((PAYLOAD/'DATA/SHIPS/shiparch.ini').read_text(encoding='utf-8'),'Ship',nick)[2]
        assert section(after,'Ship',nick)[2].strip()==installed.strip()
    print('PASS:',kind.__name__,'persists both yard archetypes; other ships unchanged')
for name in ['shiparch.ini','shiparch2.ini']:
    assert without_yard((PAYLOAD/'DATA/SHIPS'/name).read_text(encoding='utf-8'))==check.sections((GAME/'DATA/SHIPS'/name).read_text(encoding='utf-8'))
manifest=json.loads((OUT/'assets.json').read_text())
source=decode(Path(manifest['save']['source']).read_bytes()).decode('latin1')
target=decode((PAYLOAD/'SAVE/Accts/SinglePlayer/biz_le2_train_yard.fl').read_bytes()).decode('latin1')
a,b,old=section(source,'Player');c,d,new=section(target,'Player')
assert source[:a]==target[:c] and source[b:]==target[d:]
ignored={'description','tstamp','ship_archetype','equip','wg','collision_group','hull_status','descrip_strid','cloak_cooldown','pos'}
def untouched(text):return [line for line in text.splitlines() if line.strip() and line.split('=',1)[0].strip().lower() not in ignored]
assert untouched(old)==untouched(new)
movement=manifest['save']['movement']
assert sum((a-b)**2 for a,b in zip(movement['before'],movement['after']))**.5>29.99
assert all(abs(float(a)-b)<.001 for a,b in zip(value(new,'pos').split(','),movement['after']))
assert value(new,'ship_archetype')==names[0] and value(new,'base') is None
assert bytes.fromhex(value(new,'description')).decode('utf-16-be')=='biz_le2_train_yard'
assert 'HpTurret06' not in new and 'cargopod_grey' not in new
import prepare
parts=prepare.sur.read_cmp(OUT/'train_locomotive.cmp')
hardpoints={h.lower() for p in parts.values() for h in p.hardpoints}
for name,hp in manifest['save']['equipment']:assert not hp or hp.lower() in hardpoints,hp
print('PASS: fresh yard save, locomotive equipment hardpoints, progression/cargo preserved, moved forward 30 m')
(OUT/'config_checked.json').write_text(json.dumps({'manifest':sha((OUT/'assets.json').read_bytes()),'files':manifest['files']},indent=2))
