"""Stage Content/Server updates, or only the courier controller, against the installed game."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--content-only',action='store_true',help='Stage only the freshly built mission controller')
    parser.add_argument('--with-client',action='store_true',help='Include the freshly built client')
    args=parser.parse_args()
    game=Path('D:/Games/FL_MOD');out=ROOT/'out/train_courier';records={}
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    binaries=('Content.dll','Content.pdb') if args.content_only else ('Content.dll','Content.pdb','Server.dll','Server.pdb')
    if args.with_client:binaries+=('freelancer.exe','freelancer.pdb')
    for name in binaries:
        built=ROOT/'src/obj/train_courier/rpg1/bin'/name
        if digest(built)==digest(game/'bin'/name):continue
        relative='bin/'+name;target=out/'payload'/relative;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(built,target)
        records[relative]={'before':digest(game/relative),'after':digest(target)}
    dependencies={p:digest(game/p) for p in ('bin/Common.dll','bin/freelancer.exe',
        'DATA/MISSIONS/TrainCourier/catalog.ini','DATA/MISSIONS/TrainCourier/courier.ini') if p not in records}
    for name in ('Content.dll','Server.dll'):
        if 'bin/'+name not in records:dependencies['bin/'+name]=digest(game/'bin'/name)
    (out/'manifest.json').write_text(json.dumps({'game':str(game),'language':'both','files':records,'dependencies':dependencies},indent=2))
    print(f'Staged {len(records)} changed binary files: '+', '.join(records))

if __name__=='__main__':main()
