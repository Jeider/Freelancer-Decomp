"""Stage graph/catalog expansion and Content only, preserving the live client."""
import hashlib
import json
from pathlib import Path
from export import sections,one

ROOT=Path(__file__).resolve().parents[2]


def main():
    game=Path('D:/Games/FL_MOD');out=ROOT/'out/train_courier';payload=out/'payload'
    catalog=json.loads((out/'catalog.json').read_text(encoding='utf-8'));records={}
    def put(relative,data):
        if isinstance(data,str):data=data.encode('utf-8')
        target=payload/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        original=game/relative
        records[relative]={'before':hashlib.sha256(original.read_bytes()).hexdigest() if original.exists() else None,
                           'after':hashlib.sha256(data).hexdigest()}
    put('DATA/MISSIONS/TrainCourier/catalog.ini',(out/'catalog.ini').read_bytes())
    relative='DATA/SHIPS/train_courier_loadouts.ini'
    loadouts={one(s,'nickname') for k,s in sections(game/relative) if k=='loadout'}
    extra_loadouts=[]
    for count in range(2,21):
        arch=f'tc_wagons_{count:02}'
        for cargo in catalog['commodities'].values():
            name=arch+'_'+cargo['nickname']
            if name in loadouts:continue
            extra_loadouts.append(f'[Loadout]\nnickname = {name}\narchetype = {arch}\n'+
                ''.join(f'equip = {cargo["pod"]}, HpCargo{i:02}\ncargo = {cargo["nickname"]}, 50, HpCargo{i:02}\n' for i in range(1,count*2+1)))
    if extra_loadouts:put(relative,(game/relative).read_bytes()+b'\n\n'+'\n'.join(extra_loadouts).encode())
    universe='DATA/UNIVERSE/universe.ini';mbases='DATA/MISSIONS/mbases.ini'
    known={one(s,'nickname') for k,s in sections(game/universe) if k=='base'}
    mission={one(s,'nickname') for k,s in sections(game/mbases) if k=='mbase'}
    extra=[];extra_m=[];systems=sorted({b['system'] for b in catalog['bases'].values()})
    for system in systems:
        base='tc_'+system+'_base'
        if base not in known:
            extra.append(f'[Base]\nnickname = {base}\nsystem = {system}\nstrid_name = 1\nfile = Universe\\TrainCourier\\{base}.ini\nautosave_forbidden = true\n')
            put(f'DATA/UNIVERSE/TrainCourier/{base}.ini',f'[BaseInfo]\nnickname = {base}\nstart_room = Deck\n\n[Room]\nnickname = Deck\nfile = Universe\\ROOM\\KU\\battleship_deck.ini\n')
        if base not in mission:
            faction=next(p['faction'] for b in catalog['bases'].values() for p in b['points'] if p['system']==system)
            extra_m.append(f'[MBase]\nnickname = {base}\nlocal_faction = {faction}\ndiff = 1\n\n[MRoom]\nnickname = Deck\ncharacter_density = 0\n')
        launch=f'DATA/MISSIONS/TrainCourier/launch_{system}.ini'
        if not (game/launch).exists():
            put(launch,f'[CharacterEncounter]\nLocation = {base}, Deck\nautoplay = true\nrelocate_player = spaceflight\n\n[Char]\nnpc = test_npc_01\nactor = tc_transfer\nspot = Zs/NPC/Shipdealer/01/A/Stand\nfidget = scripts\\extras\\fidget_stand_male_NULL.thn\n')
    for relative,add in ((universe,extra),(mbases,extra_m)):
        if add:put(relative,(game/relative).read_bytes()+b'\n\n'+'\n'.join(add).encode())
    for name in ('Content.dll','Content.pdb'):
        put('bin/'+name,(ROOT/'src/obj/train_courier/rpg1/bin'/name).read_bytes())
    dependencies={p:hashlib.sha256((game/p).read_bytes()).hexdigest() for p in
                  ('bin/freelancer.exe','bin/Server.dll','bin/Common.dll','bin/port.ini','DATA/MISSIONS/TrainCourier/courier.ini')}
    (out/'manifest.json').write_text(json.dumps({'game':str(game),'language':'both','files':records,'dependencies':dependencies},indent=2))
    print(f'Staged {len(records)} files, {len(extra)} additional transfer bases; client and Server preserved')


if __name__=='__main__':main()
