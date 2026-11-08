"""Stage configurable courier starts, launch comm timing and localized IDS."""
import hashlib
import json
import re
from pathlib import Path
from text_resources import IDS_KEYS,TEXT_IDS,stage_localized,vendor_dialog
from stage import replace

ROOT=Path(__file__).resolve().parents[2]


def main():
    game=Path('D:/Games/FL_MOD');out=ROOT/'out/train_courier';payload=out/'payload'
    records={}
    def put(relative,data):
        if isinstance(data,str):data=data.encode('utf-8')
        original=game/relative;target=payload/relative
        target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        records[relative]={'before':hashlib.sha256(original.read_bytes()).hexdigest() if original.exists() else None,
                           'after':hashlib.sha256(data).hexdigest()}
    stage_localized(game,out,put)
    relative='DATA/MISSIONS/TrainCourier/courier.ini'
    config=(game/relative).read_text(encoding='utf-8-sig')
    for key in IDS_KEYS:config=replace(config,key+'_ids',str(TEXT_IDS[key]))
    if not re.search(r'(?mi)^boarding_comm_delay\s*=',config):
        config=replace(config,'boarding_comm_delay','3')
    if not re.search(r'(?mi)^boarding_comm_delay_max\s*=',config):
        config=replace(config,'boarding_comm_delay_max','5')
    put(relative,config)
    relative='DATA/RPG/rh_biz_contact.ini'
    contact=(game/relative).read_text(encoding='utf-8-sig')
    parts=re.split(r'(?mi)(?=^\[Dialog\]\s*$)',contact,maxsplit=1)
    assert len(parts)==2 and 'tc_offer' in parts[1],'Expected the courier vendor dialog'
    # Subsequent builds preserve the user's counts and text IDs.
    put(relative,contact if re.search(r'(?mi)^text_ids\s*=',parts[1]) else parts[0]+vendor_dialog())
    for name in ('Content.dll','Content.pdb','freelancer.exe','freelancer.pdb'):
        put('bin/'+name,(ROOT/'src/obj/train_courier/rpg1/bin'/name).read_bytes())
    dependencies={p:hashlib.sha256((game/p).read_bytes()).hexdigest()
                  for p in ('bin/Common.dll','bin/Server.dll','bin/port.ini','bin/freelancer.ini','bin/freelan_en_port.ini')}
    (out/'manifest.json').write_text(json.dumps({'game':str(game),'language':'both','files':records,'dependencies':dependencies},indent=2),encoding='utf-8')
    print(f'Staged {len(records)} files: configurable 2/10/20 starts, launch comm, RU/EN resources and Pythonlancer static cache')


if __name__=='__main__':main()
