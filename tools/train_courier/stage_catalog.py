"""Stage only the exported courier catalog, preserving installed binaries."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def main():
    game=Path('D:/Games/FL_MOD');out=ROOT/'out/train_courier';relative='DATA/MISSIONS/TrainCourier/catalog.ini'
    data=(out/'catalog.ini').read_bytes();target=out/'payload'/relative
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    records={relative:{'before':digest(game/relative),'after':digest(target)}}
    dependencies={p:digest(game/p) for p in ('bin/Content.dll','bin/Server.dll','bin/Common.dll','bin/freelancer.exe',
                  'DATA/MISSIONS/TrainCourier/courier.ini')}
    (out/'manifest.json').write_text(json.dumps({'game':str(game),'language':'both','files':records,'dependencies':dependencies},indent=2))
    print('Staged courier catalog only; installed binaries preserved')

if __name__=='__main__':main()
