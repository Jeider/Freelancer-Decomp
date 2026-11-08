"""Stage launch-objective fix and a 3..5 second initial greeting delay."""
import hashlib
import json
from pathlib import Path
from stage import replace

ROOT=Path(__file__).resolve().parents[2]


def main():
    game=Path('D:/Games/FL_MOD');out=ROOT/'out/train_courier';payload=out/'payload';records={}
    def put(relative,data):
        if isinstance(data,str):data=data.encode('utf-8')
        target=payload/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        records[relative]={'before':hashlib.sha256((game/relative).read_bytes()).hexdigest(),
                           'after':hashlib.sha256(data).hexdigest()}
    path='DATA/MISSIONS/TrainCourier/courier.ini'
    config=(game/path).read_text(encoding='utf-8-sig')
    config=replace(config,'boarding_comm_delay','3')
    config=replace(config,'boarding_comm_delay_max','5');put(path,config)
    for name in ('Content.dll','Content.pdb'):
        put('bin/'+name,(ROOT/'src/obj/train_courier/rpg1/bin'/name).read_bytes())
    dependencies={p:hashlib.sha256((game/p).read_bytes()).hexdigest() for p in
                  ('bin/freelancer.exe','bin/Server.dll','bin/Common.dll','DATA/MISSIONS/TrainCourier/catalog.ini')}
    (out/'manifest.json').write_text(json.dumps({'game':str(game),'language':'both','files':records,'dependencies':dependencies},indent=2))
    print('Staged Content DLL/PDB and courier.ini; client and other content preserved')


if __name__=='__main__':main()
