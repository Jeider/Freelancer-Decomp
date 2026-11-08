"""Refresh installed English dispatcher timings and enable recorded pickup directions."""
import hashlib
import json
from pathlib import Path

from data_output import data_folder
from stage import replace,voice_properties
from voice_audio import prepare_english,reposition_ready

ROOT=Path(__file__).resolve().parents[2]


def main():
    game=Path('D:/Games/FL_MOD');out=ROOT/'out/train_courier'
    payload=out/'payload';folder=data_folder(game,payload);records={}
    digest=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
    def put(relative,content):
        if isinstance(content,str):content=content.encode('utf-8')
        original=(game/relative).read_bytes()
        if original==content:return
        assert relative.startswith('DATA/')
        target=folder.sync_data_file(relative.removeprefix('DATA/'),content)
        records[relative]={'before':hashlib.sha256(original).hexdigest(),'after':digest(target)}

    ready=reposition_ready(game)
    catalog=json.loads((out/'catalog.json').read_text(encoding='utf-8'))
    put('DATA/AUDIO/voices_space_male.ini',prepare_english(game,catalog,reposition=ready))
    relative='DATA/MISSIONS/TrainCourier/courier.ini'
    config=(game/relative).read_text(encoding='utf-8-sig')
    config=replace(config,'audio_enabled','true')
    config=replace(config,'reposition_audio_enabled','true' if ready else 'false')
    put(relative,config)
    relative='DATA/MISSIONS/voice_properties.ini'
    put(relative,voice_properties((game/relative).read_bytes(),voices=('atc_leg_m01_new',)))
    dependencies={p:digest(game/p) for p in (
        'bin/Content.dll','bin/Server.dll','bin/Common.dll','bin/freelancer.exe',
        'DATA/MISSIONS/TrainCourier/catalog.ini','DATA/MISSIONS/TrainCourier/descriptions.ini')}
    (out/'manifest.json').write_text(json.dumps({'game':str(game),'language':'both',
        'files':records,'dependencies':dependencies},indent=2),encoding='utf-8')
    print(f'Staged {len(records)} audio configuration files; pickup directions enabled={ready}')


if __name__=='__main__':main()
