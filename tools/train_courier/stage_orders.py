"""Stage economic orders, localized briefs, saved timer and HUD as one package."""
import hashlib
import json
from pathlib import Path
from stage import replace
from text_resources import stage_localized,TEXT_IDS
from order_texts import description_ini,rows

ROOT=Path(__file__).resolve().parents[2]

def main():
    game=Path('D:/Games/FL_MOD');out=ROOT/'out/train_courier';payload=out/'payload';records={}
    def put(relative,data):
        if isinstance(data,str):data=data.encode('utf-8')
        target=payload/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        old=game/relative
        records[relative]={'before':hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else None,
                           'after':hashlib.sha256(data).hexdigest()}
    put('DATA/MISSIONS/TrainCourier/catalog.ini',(out/'catalog.ini').read_bytes())
    put('DATA/MISSIONS/TrainCourier/descriptions.ini',description_ini())
    relative='DATA/MISSIONS/TrainCourier/courier.ini'
    config=(game/relative).read_text(encoding='utf-8-sig')
    # Append a separate section; all entries remain ordinary INI settings.
    if '[OrderEconomy]' not in config:
        config+='\n[OrderEconomy]\nper_wagon_distance_reward = 150\ncargo_value_rate = 0.01\nloss_value_rate = 0.05\norder_seconds = 300\nwagon_seconds = 180\n'
        config+='\n[OrderPresentation]\ntimer_position = 0.275, -0.12\n'
        config+=''.join(f'{key}_ids = {TEXT_IDS[key]}\n' for key in ('description','timer','overdue','loss'))
    config=replace(config,'description_ids',str(TEXT_IDS['description_capacity']))
    put(relative,config)
    stage_localized(game,out,put)
    for name in ('Content.dll','Content.pdb','freelancer.exe','freelancer.pdb'):
        put('bin/'+name,(ROOT/'src/obj/train_courier/rpg1/bin'/name).read_bytes())
    dependencies={p:hashlib.sha256((game/p).read_bytes()).hexdigest() for p in
                  ('bin/Server.dll','bin/Common.dll','DATA/SHIPS/train_courier_loadouts.ini')}
    (out/'manifest.json').write_text(json.dumps({'game':str(game),'language':'both','files':records,'dependencies':dependencies},indent=2))
    # Human-readable editable source is Pythonlancer static.py; this is a review copy.
    from text_resources import localized_rows
    localized,_=localized_rows(game,payload/'Assets/Pythonlancer/text/static.py' if 'Assets/Pythonlancer/text/static.py' in records else None)
    for lang,index in [('ru',1),('en',2)]:
        (out/f'order_briefs_{lang}.txt').write_text('\n\n'.join(f'IDS {row[0]}\n{row[index]}' for row in localized if row[0]>=238283),encoding='utf-8')
    print(f'Staged {len(records)} files: Content/client, catalog, descriptions, config, static cache and RU/EN resources')

if __name__=='__main__':main()
