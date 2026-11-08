"""Stage pending planet tracks, named pickups, raised HUD timer and new voice hook."""
import hashlib
import json
import re
from pathlib import Path
from stage import voice_properties,replace
from stage_catalog import main as stage_catalog
from text_resources import stage_localized,TEXT_IDS
from prepare_reposition import patch_dispatcher
from voice_audio import reposition_ready,prepare_english

ROOT=Path(__file__).resolve().parents[2]

def main():
    stage_catalog()
    out=ROOT/'out/train_courier';payload=out/'payload'
    manifest=json.loads((out/'manifest.json').read_text());game=Path(manifest['game'])
    def put(relative,data):
        if isinstance(data,str):data=data.encode('utf-8')
        target=payload/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        old=game/relative
        manifest['files'][relative]={'before':hashlib.sha256(old.read_bytes()).hexdigest() if old.exists() else None,
                                     'after':hashlib.sha256(data).hexdigest()}
        manifest['dependencies'].pop(relative,None)
    ready=reposition_ready(game)
    relative='DATA/MISSIONS/TrainCourier/courier.ini'
    config=(game/relative).read_text(encoding='utf-8-sig')
    config=replace(config,'timer_position','0.275, -0.12')
    config=replace(config,'wagon_seconds','180')
    for key,value in [('pickup_from_ids',str(TEXT_IDS['pickup_from'])),
                      ('description_ids',str(TEXT_IDS['description_capacity'])),('wagons_per_jump','5'),
                      ('reposition_audio_enabled','true' if ready else 'false')]:
        if re.search(r'(?m)^'+key+r'\s*=',config):config=replace(config,key,value)
        else:config+='\n'+key+' = '+value+'\n'
    put(relative,config)
    relative='DATA/MISSIONS/voice_properties.ini'
    put(relative,voice_properties((game/relative).read_bytes(),voices=('atc_leg_m01_new',)))
    if ready:
        catalog=json.loads((out/'catalog.json').read_text())
        put('DATA/AUDIO/voices_space_male.ini',prepare_english(game,catalog,reposition=True))
    relative='Assets/Pythonlancer/universe/audio/dispatcher_en.py'
    original=(game/relative).read_text(encoding='utf-8')
    changed=patch_dispatcher(original)
    if original!=changed:put(relative,changed)
    stage_localized(game,out,put)
    for name in ('Content.dll','Content.pdb'):
        put('bin/'+name,(ROOT/'src/obj/train_courier/rpg1/bin'/name).read_bytes())
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(f'Staged {len(manifest["files"])} files; timer raised by one icon; reposition audio enabled={ready}')

if __name__=='__main__':main()
