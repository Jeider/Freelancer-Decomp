"""Render both real PythonLancer generators and verify the staged space save."""
import hashlib
import json
import re
import sys
import io
from contextlib import redirect_stdout
from types import SimpleNamespace
from pathlib import Path
sys.dont_write_bytecode=True
from player import ROOT,GAME,OUT,GEN,PLAYER,PLAYER_TEMPLATE,TEMPLATES,SAVE_FILE,SAVE_NAME,WAGONS,NPC_MODEL,TRAIN_MODEL,section,value,decode,sha
sys.path.insert(0,str(GAME/GEN))
from jinja2 import Environment,FileSystemLoader,StrictUndefined
from managers.shiparch import ShiparchManager,ShiparchManagerV2


class IDs:
    def __init__(self):self.next_id=1000
    def new_name(self,*args,**kwargs):
        self.next_id+=1
        return SimpleNamespace(id=self.next_id)
    new_info=new_name


def generate(kind,staged):
    dirs=[str(GAME/GEN/'templates')]
    if staged:dirs.insert(0,str(OUT/GEN/'templates'))
    env=Environment(loader=FileSystemLoader(dirs),undefined=StrictUndefined)
    core=SimpleNamespace(misc_equip=None,ids=SimpleNamespace(ship=IDs(),ship_dbg=IDs()),write=False,
        tpl_manager=SimpleNamespace(get_result=lambda t,c:env.get_template(t).render(c)))
    with redirect_stdout(io.StringIO()):manager=kind(core)
    return manager.get_shiparch_content()


def sections(text):
    return [b.strip() for b in re.split(r'(?m)(?=^\[)',text) if b.strip() and b.lstrip().startswith('[')]


def main():
    manifest=json.loads((OUT/'manifest.json').read_text())
    staged_player=section((OUT/'DATA/SHIPS/shiparch.ini').read_text(encoding='utf-8'),'Ship',PLAYER)[2].strip()
    for kind in [ShiparchManager,ShiparchManagerV2]:
        before=generate(kind,False);after=generate(kind,True)
        a,b,new=section(after,'Ship',PLAYER)
        c,d,old=section(before,'Ship',PLAYER)
        assert new.strip()==staged_player,'Generated player definition must match installation'
        # Includes only add the player section and its preceding comment/whitespace.
        assert sections(after[:a]+after[b:])==sections(before[:c]+before[d:]),'Other generated ships changed'
        assert value(section(after,'Ship','ge_train')[2],'DA_archetype')==NPC_MODEL
        print('PASS:',kind.__name__,'regeneration preserves NPCs and creates one',PLAYER)
    for rel in ['DATA/SHIPS/shiparch.ini','DATA/SHIPS/shiparch2.ini']:
        source=(GAME/rel).read_text(encoding='utf-8');target=(OUT/rel).read_text(encoding='utf-8')
        a,b,new=section(target,'Ship',PLAYER)
        repaired=target[:a]+target[b:]
        s,e,npc=section(source,'Ship','ge_train')
        expected=source[:s]+npc.replace(TRAIN_MODEL,NPC_MODEL)+source[e:]
        c,d,_=section(expected,'Ship',PLAYER)
        expected=expected[:c]+expected[d:]
        assert sections(repaired)==sections(expected),'Unrelated live section changed'
        print('PASS:',rel,'NPC model restored; independent player archetype')
    # Resolve gear only through the actual client's equipment list, not unused files.
    config=(GAME/'bin/freelancer.ini').read_text(encoding='latin1')
    equipment=set()
    for rel in re.findall(r'(?im)^\s*equipment\s*=\s*([^;\r\n]+)',config):
        path=GAME/'DATA'/rel.strip()
        raw=path.read_bytes().decode('utf-8',errors='replace')
        equipment.update(n.lower() for n in re.findall(r'(?im)^nickname\s*=\s*([^\r\n;]+)',raw))
    model=json.loads((ROOT/'out/train_consist/data.json').read_text())
    assert model['wagons']==WAGONS==manifest['wagons']
    hardpoints={hp.lower() for p in model['parts'].values() for hp in p['hardpoints']}
    for name,hp in manifest['save']['equipment']:
        assert name.lower() in equipment,'Missing loaded equipment: '+name
        assert not hp or hp.lower() in hardpoints,'Missing hardpoint: '+hp
    source=decode(Path(manifest['save']['source']).read_bytes()).decode('latin1')
    target=decode((OUT/SAVE_FILE).read_bytes()).decode('latin1')
    a,b,old=section(source,'Player');c,d,new=section(target,'Player')
    assert source[:a]==target[:c] and source[b:]==target[d:],'World state changed'
    ignored={'description','tstamp','ship_archetype','equip','wg','collision_group','hull_status','descrip_strid','cloak_cooldown'}
    def untouched(s):return [x for x in s.splitlines() if x.strip() and x.split('=',1)[0].strip().lower() not in ignored]
    assert untouched(old)==untouched(new),'Progress/cargo/position changed'
    assert value(new,'base') is None and value(new,'ship_archetype')==PLAYER
    assert bytes.fromhex(value(new,'description')).decode('utf-16-be')==SAVE_NAME
    assert len(re.findall(r'(?im)^equip = cargopod_grey,',new))==WAGONS*2
    assert len(re.findall(r'(?im)^equip\s*=',new))==len(manifest['save']['equipment'])
    assert not (GAME/SAVE_FILE).exists(),'Would overwrite save'
    print('PASS: new FLS1 space save; equipment/hardpoints resolve; source and progression preserved')
    (OUT/'checked.json').write_text(json.dumps({'manifest':sha((OUT/'manifest.json').read_bytes()),
        'files':{name:sha((OUT/name).read_bytes()) for name in manifest['files']}},indent=2))


if __name__=='__main__':main()
