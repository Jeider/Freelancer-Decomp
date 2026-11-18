"""Prepare evacuation content and Pythonlancer changes without live writes."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
PROJECT=GAME/'Assets/Pythonlancer'
OUT=ROOT/'out/train_courier/evacuation'
PACKAGE=OUT/'package'
GEN='Assets/Pythonlancer/'
EMPLOYERS={'rh_grp':'tr_grp_rh','rc_grp':'tr_grp_rh',
           'li_grp':'tr_grp_li','lc_grp':'tr_grp_li',
           'br_grp':'tr_grp_br','bc_grp':'tr_grp_br',
           'ku_grp':'tr_grp_ku','kc_grp':'tr_grp_ku','co_grp':'co_grp'}
EVENTS={'train_delivery_late':-.01,'train_cargo_loss':-.1,'train_locomotive_loss':-.2}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def patch_once(text,old,new):
    if new in text:return text
    assert text.count(old)==1,old
    return text.replace(old,new,1)

def faction_source(text):
    text=patch_once(text,'    def get_empathy_content(self):',
        '    # Courier events are configurable per faction, just like retail mission events.\n'
        '    TRAIN_DELIVERY_LATE = -0.01\n    TRAIN_CARGO_LOSS = -0.1\n    TRAIN_LOCOMOTIVE_LOSS = -0.2\n\n'
        '    def get_empathy_content(self):')
    return patch_once(text,'event = random_mission_abortion, -0.067500\n',
        'event = random_mission_abortion, -0.067500\n'
        'event = train_delivery_late, {self.TRAIN_DELIVERY_LATE:.6f}\n'
        'event = train_cargo_loss, {self.TRAIN_CARGO_LOSS:.6f}\n'
        'event = train_locomotive_loss, {self.TRAIN_LOCOMOTIVE_LOSS:.6f}\n')

def empathy(text):
    def change(match):
        block=match[0]
        for event,value in EVENTS.items():
            line=f'event = {event}, {value:.6f}\n'
            if re.search(r'(?m)^event\s*=\s*'+event+r'\s*,',block):continue
            block=re.sub(r'(?m)^(event\s*=\s*random_mission_abortion[^\n]*\n)',lambda m:m[0]+line,block,count=1)
        if re.search(r'(?m)^group\s*=\s*tr_grp_rh\s*$',block):
            block,count=re.subn(r'(?m)^empathy_rate\s*=\s*rh_grp\s*,[^\n]*',
                               'empathy_rate = rh_grp, 1.0',block)
            assert count==1
        return block
    return re.sub(r'(?mi)^\[RepChangeEffects\][^\[]*',change,text)

def catalog(text):
    def change(match):
        block=match[0]
        if re.search(r'(?m)^employer\s*=',block):return block
        faction=re.search(r'(?m)^faction\s*=\s*(\S+)',block)[1]
        employer=EMPLOYERS.get(faction,faction)
        return re.sub(r'(?m)^(faction\s*=[^\n]*\n)',lambda m:m[0]+'employer = '+employer+'\n',block,count=1)
    return re.sub(r'(?mi)^\[Courier(?:Point|Parking)\][^\[]*',change,text)

DATA_API='''
    def sync_train_evacuation(self, files):
        """Evacuation content, including staged publication and rollback."""
        allowed = {'MISSIONS/empathy.ini', 'MISSIONS/TrainCourier/catalog.ini',
                   'MISSIONS/TrainCourier/courier.ini', 'SOLAR/train_courier.ini',
                   'INTERFACE/HUD/EXTRA/hud_train_evacuate.3db'}
        for name in files:
            if name not in allowed:
                raise ValueError('Unexpected evacuation DATA file: ' + name)
            self.data_path(name)
        for name, content in files.items():
            if content is None:
                self.remove_data_file(name)
            else:
                self.sync_data_file(name, content)
'''

def data_class(source):
    scope={'__name__':'evacuation_data_folder'}
    exec(compile(source,'Pythonlancer/tools/data_folder.py','exec'),scope)
    return scope['DataFolder']

def icon():
    # An authored vector symbol rasterized for the game's native HUD material.
    from PIL import Image,ImageDraw
    sys.path.insert(0,str(ROOT/'tools'))
    from make_targeting_icons import generate
    image=Image.new('RGBA',(512,512),(0,0,0,0));draw=ImageDraw.Draw(image)
    white=(255,255,255,255)
    draw.line([(248,68),(92,68),(92,444),(248,444)],fill=white,width=28,joint='curve')
    draw.polygon([(204,224),(350,224),(350,155),(456,256),(350,357),(350,288),(204,288)],fill=white)
    texture=OUT/'evacuate.tga';image.resize((128,128),Image.Resampling.LANCZOS).save(texture)
    raw,_,report=generate(GAME/'DATA/INTERFACE/HUD/EXTRA/hud_train_couple.3db',{},'hud_train_evacuate',texture)
    (OUT/'icon.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    image.resize((128,128),Image.Resampling.LANCZOS).save(OUT/'evacuate.png')
    return raw

def evacuated_solar(solar,game=GAME):
    from export import sections,one
    if 'nickname = tc_evacuated_locomotive' in solar:return solar
    loco=next(s for k,s in sections(game/'DATA/SHIPS/shiparch.ini') if k=='ship' and one(s,'nickname')=='ge_train_loco_player')
    block=next(b for b in re.split(r'(?m)(?=^\[Solar\])',solar) if 'nickname = tc_parked_locomotive' in b)
    block=block.replace('tc_parked_locomotive','tc_evacuated_locomotive')
    block=re.sub(r'(?m)^hit_pts\s*=.*$',lambda m:'hit_pts = '+one(loco,'hit_pts'),block)
    block+='\nexplosion_arch = '+one(loco,'explosion_arch','explosion_large')+'\n'
    return solar.rstrip()+'\n\n'+block

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=(PROJECT/'tools/data_folder.py').read_text(encoding='utf-8')
    if 'def sync_train_evacuation(' not in source:source=source.rstrip()+'\n'+DATA_API
    cls=data_class(source);data=cls(root=PACKAGE)
    records={}
    def put(name,content):
        raw=content.encode('utf-8') if isinstance(content,str) else content
        path=PACKAGE/name
        if name.startswith('DATA/'):data.sync_train_evacuation({name[5:]:raw})
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(raw)
        if name.endswith('.py'):ast.parse(raw)
        records[name]={'before':digest(GAME/name),'after':digest(path)}
    put(GEN+'tools/data_folder.py',source)
    put(GEN+'universe/faction.py',faction_source((PROJECT/'universe/faction.py').read_text(encoding='utf-8')))
    owners=(PROJECT/'managers/courier_owners.py').read_text(encoding='utf-8')
    # Explicit owner-to-employer mapping; destination changes never select a new employer.
    helper='\nCOURIER_EMPLOYERS = '+repr(EMPLOYERS)+'\n\ndef courier_employer(faction):\n    return COURIER_EMPLOYERS.get(faction, faction)\n\n'
    owners=patch_once(owners,'\ndef asset_path(',helper+'\ndef asset_path(')
    owners=patch_once(owners,'f\'base = {name}\\nsystem = {system}\\nfaction = {entry["faction"]}\\n\'',
        'f\'base = {name}\\nsystem = {system}\\nfaction = {entry["faction"]}\\nemployer = {courier_employer(entry["faction"])}\\n\'')
    put(GEN+'managers/courier_owners.py',owners)
    put('DATA/MISSIONS/empathy.ini',empathy((GAME/'DATA/MISSIONS/empathy.ini').read_text(encoding='utf-8-sig')))
    put('DATA/MISSIONS/TrainCourier/catalog.ini',catalog((GAME/'DATA/MISSIONS/TrainCourier/catalog.ini').read_text(encoding='utf-8-sig')))
    solar=(GAME/'DATA/SOLAR/train_courier.ini').read_text(encoding='utf-8-sig')
    put('DATA/SOLAR/train_courier.ini',evacuated_solar(solar))
    config=(GAME/'DATA/MISSIONS/TrainCourier/courier.ini').read_text(encoding='utf-8-sig')
    if 'evacuation_audio_enabled' not in config:
        config=re.sub(r'(?m)^(audio_enabled\s*=[^\n]*\n)',
            lambda m:m[0]+'; Enable only after the te_* recording bank is installed.\nevacuation_audio_enabled = false\n',config,count=1)
    assert 'evacuation_audio_enabled' in config
    put('DATA/MISSIONS/TrainCourier/courier.ini',config)
    put('DATA/INTERFACE/HUD/EXTRA/hud_train_evacuate.3db',icon())
    from text_resources import stage_localized
    rows=stage_localized(GAME,OUT,put)
    manifest={'files':records,'events':EVENTS,'employers':EMPLOYERS,'audio_generated':False,
              'ui_ids':[n for n,ru,en in rows if 239300<=n<239330]}
    (OUT/'content.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('Staged evacuation content:',len(records),'files;',len(manifest['ui_ids']),'bilingual UI strings')

if __name__=='__main__':main()
