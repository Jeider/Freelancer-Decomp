"""Stage route rotation and RDL briefs, preserving unrelated game resources."""
import ast
import argparse
import hashlib
import json
from pathlib import Path
from order_texts import rows
from text_resources import stage_localized
from data_output import data_folder

ROOT=Path(__file__).resolve().parents[2]

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--with-client',action='store_true',help='Include the freshly built client')
    parser.add_argument('--build-root',type=Path,default=ROOT/'src/obj/train_courier/rpg1')
    parser.add_argument('--description-only',action='store_true',help='Update descriptions without changing route settings')
    args=parser.parse_args()
    game=Path('D:/Games/FL_MOD');out=ROOT/'out/train_courier';payload=out/'payload';records={}
    digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
    def put(relative,data):
        if isinstance(data,str):data=data.encode('utf-8')
        before=(game/relative).read_bytes()
        if data==before:return
        target=payload/relative
        if relative.startswith('DATA/'):
            data_folder(game,payload).sync_data_file(relative.removeprefix('DATA/'),data)
        else:
            target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        records[relative]={'before':hashlib.sha256(before).hexdigest(),'after':digest(target)}

    relative='Assets/Pythonlancer/text/static.py'
    original=(game/relative).read_bytes();tree=ast.parse(original.decode('utf-8'))
    lines=original.splitlines(keepends=True);offsets=[0]
    for line in lines:offsets.append(offsets[-1]+len(line))
    replacements={number:(ru,en) for key,number,ru,en in rows() if key in ('description','description_capacity')}
    edits=[]
    for node in ast.walk(tree):
        if not (isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id=='Static' and node.args):continue
        number=ast.literal_eval(node.args[0])
        if number in replacements:
            ru,en=replacements.pop(number)
            edits.append((offsets[node.lineno-1]+node.col_offset,offsets[node.end_lineno-1]+node.end_col_offset,
                          f'Static({number}, MS({ru!r}, {en!r}))'.encode('utf-8')))
    assert not replacements,'Missing registered description IDs'
    updated=original
    for begin,end,value in sorted(edits,reverse=True):updated=updated[:begin]+value+updated[end:]
    ast.parse(updated.decode('utf-8'));put(relative,updated)
    static_path=payload/relative if relative in records else game/relative
    stage_localized(game,out,put,static_path)
    relative='DATA/MISSIONS/TrainCourier/courier.ini'
    config=(game/relative).read_text(encoding='utf-8-sig')
    if 'short_load_percent' not in config:
        config=config.replace('[CourierRules]','[CourierRules]\nshort_load_percent = 50',1)
    for key,number in [('mission_title_ids',238289),('cargo_name_ids',238290)]:
        if key not in config:config+=f'\n{key} = {number}\n'
    if not args.description_only:put(relative,config)
    binaries=['Content.dll','Content.pdb']
    if args.with_client:binaries+=['freelancer.exe','freelancer.pdb']
    for name in binaries:
        put('bin/'+name,(args.build_root/'bin'/name).read_bytes())
    dependencies={p:digest(game/p) for p in ('bin/Common.dll','bin/Server.dll','bin/freelancer.exe',
        'DATA/MISSIONS/TrainCourier/catalog.ini','DATA/MISSIONS/TrainCourier/descriptions.ini') if p not in records}
    (out/'manifest.json').write_text(json.dumps({'game':str(game),'language':'both','files':records,'dependencies':dependencies},indent=2))
    print(f'Staged {len(records)} files: {", ".join(binaries)}, RDL descriptions in RU/EN resource DLLs and Pythonlancer static cache, rotation setting')

if __name__=='__main__':main()
