"""Stage courier models and INIs against the installed mod. Does not install."""
from pathlib import Path
import argparse
import copy
import hashlib
import json
import re
import shutil
import struct
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/train_consist'))
import prepare as model
import contrails
from export import sections,one,fixture_pose
from text_resources import IDS_KEYS,TEXT_IDS,stage_localized,vendor_dialog,build as build_text
from dispatcher_en import FAMILIES as ENGLISH_FAMILIES
from dispatcher_en import REPOSITION_FAMILIES
from launchers import startup_inis,add_dependencies
u=model.u
child=model.sur.child
string=model.sur.string

def replace(text,key,value):
    expression=r'(?mi)^'+re.escape(key)+r'\s*=.*$'
    if not re.search(expression,text):return text.rstrip()+'\n'+key+' = '+value+'\n'
    return re.sub(expression,lambda m:key+' = '+value,text)

def section(text,kind,nickname):
    for block in re.split(r'(?m)(?=^\[)',text):
        if block.lower().startswith('['+kind.lower()+']') and re.search(r'(?mi)^nickname\s*=\s*'+re.escape(nickname)+r'\s*$',block):return block
    raise ValueError('Missing '+kind+' '+nickname)

def sur_parts(raw):
    assert raw[:8]==b'vers'+struct.pack('<f',2)
    out={};offset=8
    while offset<len(raw):
        start=offset
        ident,count=struct.unpack_from('<II',raw,offset);offset+=8
        for _ in range(count):
            tag=raw[offset:offset+4];offset+=4
            if tag==b'!fxd':continue
            if tag==b'exts':offset+=24
            elif tag==b'surf':
                size=struct.unpack_from('<I',raw,offset)[0];offset+=4+size
            else:raise ValueError('Unknown SUR chunk '+repr(tag))
        assert offset<=len(raw)
        out[ident]=raw[start:offset]
    return out

def wagon_model(source,count):
    header,trees=u.read_tree((source/'train_wagons.cmp').read_bytes())
    root=trees[0];compound=child(root,'Cmpnd')
    keep={'Root'}|{f'TrainWagon{i:02}' for i in range(2,count+1)}
    entries=[n for n in compound.children if child(n,'Object name')]
    for entry in entries:
        if string(child(entry,'Object name')) not in keep:
            root.children.remove(child(root,string(child(entry,'File name'))))
            compound.children.remove(entry)
    constraints=child(child(compound,'Cons'),'Fix')
    constraints.blob=b''.join(row for i in range(0,len(constraints.blob),176)
                             if (row:=constraints.blob[i:i+176])[64:128].split(b'\0')[0].decode() in keep)
    contrails.annotate(root,True)
    chunks=sur_parts((source/'train_wagons.sur').read_bytes())
    return u.write_tree(header,trees),b'vers'+struct.pack('<f',2)+b''.join(chunks[u.crc(n)] for n in sorted(keep))

def voice_properties(raw,voices=('dispatcher01','atc_leg_m01_new')):
    text=raw.decode('utf-8-sig')
    families=['board','pickup','depart','arrival','paid','continue','next','finish_delivery','park','done']
    for voice in voices:
        wanted=list(ENGLISH_FAMILIES)+list(REPOSITION_FAMILIES) if voice=='atc_leg_m01_new' else ['tc_'+f for f in families]
        blocks=re.split(r'(?m)(?=^\[)',text)
        for i,block in enumerate(blocks):
            if block.lower().startswith('[mvoiceprop]') and re.search(r'(?mi)^voice\s*=\s*'+voice+r'\s*$',block):
                block=re.sub(r'(?mi)^permutation_count\s*=\s*tc_[^\r\n]*\r?\n?', '',block)
                for family in wanted:block+=f'permutation_count = {family}, 10\n'
                blocks[i]=block;break
        else:
            blocks.append('\n[mVoiceProp]\nvoice = '+voice+'\n'+''.join(f'permutation_count = {f}, 10\n' for f in wanted))
        text=''.join(blocks)
    return text.encode('utf-8')

def hardpoint(root,name):
    if root.name.lower()==name.lower():return root
    for node in root.children:
        found=hardpoint(node,name)
        if found is not None:return found
    return None

def boarding_model(source):
    header,trees=u.read_tree((source/'train_locomotive.cmp').read_bytes());root=trees[0]
    contrails.annotate(root)
    node=model.partnode(root,child(child(root,'Cmpnd'),'Root'))
    miner=u.read_tree((source.parent/'MINING/mining_with_panels.cmp').read_bytes())[1][0]
    mount=struct.unpack('<3f',child(hardpoint(miner,'HpDockMountA'),'Position').blob)
    # Copy the dockable Roid_Miner2 berth and camera as one translated rig.
    # The ship descends belly-first, keeping the miner's horizontal frames.
    for name in ['HpDockMountA','HpDockPointA01','HpDockPointA02','HpDockCamA']:
        reference=hardpoint(miner,name)
        position=struct.unpack('<3f',child(reference,'Position').blob)
        model.hp(node,name,tuple(p-m+offset for p,m,offset in zip(position,mount,(0,35,0))))
        child(hardpoint(node,name),'Orientation').blob=child(reference,'Orientation').blob
    return u.write_tree(header,trees)

def boarding_objects(game):
    fixtures=[s for k,s in sections(game/'DATA/UNIVERSE/SYSTEMS_MOD/RH_BIZMARK/rh_biz.ini')
              if k=='object' and one(s,'archetype')=='docking_fixture' and one(s,'dock_with')=='rh_biz_01_base']
    assert len(fixtures)==1,'Expected one Bismarck docking fixture'
    fixture=fixtures[0]
    position,_,quaternion=fixture_pose(game,fixture)
    return ('[Mission]\nnpc_ship_file = missions\\npcships.ini\n\n[MsnSolar]\nnickname = tc_boarding\nsystem = rh_biz\nfaction = rh_grp\n'
            'archetype = tc_boarding_solar\nstring_id = 237055\nbase = tc_rh_biz_base\nposition = '+
            ', '.join(f'{v:.9g}' for v in position)+'\norientation = '+', '.join(f'{v:.9g}' for v in quaternion)+'\n')

def parked_solar(text):
    # Same solid model, berth and miner camera; DockQueues rejects incoming
    # requests by this separate archetype, including after mission completion.
    blocks=[b for b in re.split(r'(?m)(?=^\[)',text)
            if not re.search(r'(?mi)^nickname\s*=\s*tc_parked_locomotive\s*$',b)]
    text=''.join(blocks).rstrip()+'\n'
    return text+'\n'+replace(section(text,'Solar','tc_boarding_solar'),'nickname','tc_parked_locomotive')

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game',type=Path,default=Path('D:/Games/FL_MOD'))
    parser.add_argument('--language',choices=['ru','en'],default='ru')
    parser.add_argument('--voice-language',choices=['ru','en'],help='Dispatcher language; defaults to text language')
    parser.add_argument('--enable-audio',action='store_true',help='Enable English comms after validating all installed recordings')
    parser.add_argument('--update-boarding',action='store_true',help='Stage docking CMP/SUR, solid solar, parking pose and rebuilt Content')
    parser.add_argument('--update-contrails',action='store_true',help='Stage trail anchors on locomotive, boarding solar and all wagon lengths; no binaries')
    parser.add_argument('--update-transfer',action='store_true',help='Stage rebuilt Content/Server/client for the immediate ship transfer')
    parser.add_argument('--update-client',action='store_true',help='Stage only the rebuilt client EXE/PDB')
    parser.add_argument('--update-mission',action='store_true',help='Stage rebuilt Content and updated mission text/config')
    parser.add_argument('--update-launchers',action='store_true',help='Repair courier dependencies in all language startup INIs; no binaries')
    args=parser.parse_args();game=args.game
    voice_language=args.voice_language or args.language
    voice='dispatcher01' if voice_language=='ru' else 'atc_leg_m01_new'
    out=ROOT/'out/train_courier';payload=out/'payload'
    catalog=json.loads((out/'catalog.json').read_text(encoding='utf-8'))
    audio=None
    if args.enable_audio:
        assert voice_language=='en', 'Only the English recordings are ready for validation'
        assert args.update_boarding or args.update_transfer or args.update_mission, 'Enable audio together with the updated controller'
        from voice_audio import prepare_english
        audio=prepare_english(game,catalog)
    if not (args.update_boarding or args.update_transfer or args.update_client or args.update_contrails or args.update_mission or args.update_launchers):
        for path,expected in catalog['inputs'].items():
            assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==expected,'Catalog input changed; export again: '+path
    records={}
    def put(relative,data):
        if isinstance(data,str):data=data.encode('utf-8')
        target=payload/relative;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
        original=game/relative
        records[relative]={'before':hashlib.sha256(original.read_bytes()).hexdigest() if original.exists() else None,
                           'after':hashlib.sha256(data).hexdigest()}
    def stage_launchers(index=None):
        if index is None:
            resources=next(s for k,s in sections(game/'bin/freelancer.ini') if k=='resources')
            index=[v.lower() for v in resources['dll']].index('train_courier_text.dll')+1
        for path in startup_inis(game):
            before=path.read_bytes();after=add_dependencies(before,index)
            if after!=before:put(str(path.relative_to(game.resolve())).replace('\\','/'),after)
    if args.update_launchers:
        assert not any((args.update_boarding,args.update_transfer,args.update_client,args.update_contrails,args.update_mission,args.enable_audio))
        stage_launchers()
        (out/'manifest.json').write_text(json.dumps({'game':str(game.resolve()),'language':args.language,'files':records},indent=2),encoding='utf-8')
        print(f'Staged {len(records)} startup INIs; no binary or audio changes');return
    modelpath='DATA/SHIPS/UTILITY/FREIGHT_TRAIN/'
    source=game/modelpath
    if args.update_boarding or args.update_transfer or args.update_client or args.update_contrails or args.update_mission:
        assert (game/'DATA/MISSIONS/TrainCourier/courier.ini').exists(),'Install the courier mission first'
        if args.update_boarding:
            put(modelpath+'train_boarding.cmp',boarding_model(source))
            put(modelpath+'train_boarding.sur',(source/'train_locomotive.sur').read_bytes())
            solar=(game/'DATA/SOLAR/train_courier.ini').read_text(encoding='utf-8-sig')
            solar=replace(solar,'phantom_physics','false')
            solar=replace(solar,'docking_sphere','berth, HpDockMountA, 5')
            put('DATA/SOLAR/train_courier.ini',solar)
            put('DATA/MISSIONS/TrainCourier/objects.ini',boarding_objects(game))
        if args.update_contrails:
            put(modelpath+'train_locomotive.cmp',contrails.annotated((source/'train_locomotive.cmp').read_bytes()))
            if not args.update_boarding:
                put(modelpath+'train_boarding.cmp',contrails.annotated((source/'train_boarding.cmp').read_bytes()))
            put(modelpath+'train_wagons.cmp',contrails.annotated((source/'train_wagons.cmp').read_bytes(),True))
            for count in range(2,21):
                cmp,_=wagon_model(source,count)
                put(modelpath+f'train_wagons_{count:02}.cmp',cmp)
        binary=ROOT/'src/obj/train_courier/rpg1/bin'
        names=['freelancer.exe','freelancer.pdb'] if args.update_client or args.update_transfer else []
        if args.update_boarding or args.update_transfer or args.update_mission:
            assert catalog.get('parking'), 'Export the catalog again for planet parking'
            names+=['Content.dll','Content.pdb']
            names+=['Server.dll','Server.pdb']
            solar=(payload/'DATA/SOLAR/train_courier.ini').read_text(encoding='utf-8-sig') if args.update_boarding else (game/'DATA/SOLAR/train_courier.ini').read_text(encoding='utf-8-sig')
            put('DATA/SOLAR/train_courier.ini',parked_solar(solar))
            put('DATA/MISSIONS/TrainCourier/catalog.ini',(out/'catalog.ini').read_bytes())
            resources=next(s for k,s in sections(game/'bin/freelancer.ini') if k=='resources')
            indexes=[i for i,d in enumerate(resources.get('dll',[]),1) if d.strip().lower()=='train_courier_text.dll']
            assert len(indexes)==1,'Installed courier resource DLL missing or ambiguous'
            index=indexes[0]
            stage_localized(game,out,put)
            path='DATA/MISSIONS/TrainCourier/courier.ini'
            config=(game/path).read_text(encoding='utf-8-sig')
            config=replace(config,'voice',voice)
            if args.enable_audio:config=replace(config,'audio_enabled','true')
            for key in IDS_KEYS:config=replace(config,key+'_ids',str(TEXT_IDS[key]))
            put(path,config)
            put('DATA/MISSIONS/voice_properties.ini',voice_properties((game/'DATA/MISSIONS/voice_properties.ini').read_bytes(),[voice]))
            if audio is not None:put('DATA/AUDIO/voices_space_male.ini',audio)
        for name in names:
            put('bin/'+name,(binary/name).read_bytes())
        stage_launchers()
        (out/'manifest.json').write_text(json.dumps({'game':str(game.resolve()),'language':args.language,'files':records},indent=2),encoding='utf-8')
        print(f'Staged {len(records)} files; binaries: '+(', '.join(names) or 'none'))
        return
    archtext=(game/'DATA/SHIPS/shiparch.ini').read_text(encoding='utf-8-sig')
    tail=section(archtext,'Ship','ge_train_wagons')
    definitions=[];loadouts=[]
    for count in range(2,21):
        name=f'train_wagons_{count:02}';nick=f'tc_wagons_{count:02}'
        cmp,sur=wagon_model(source,count)
        put(modelpath+name+'.cmp',cmp);put(modelpath+name+'.sur',sur)
        text=replace(tail,'nickname',nick)
        text=replace(text,'DA_archetype','ships\\utility\\freight_train\\'+name+'.cmp')
        text=re.sub(r'(?mi)^hp_type\s*=.*\n?', '',text)
        text+='hp_type = hp_cargo_pod, '+', '.join(f'HpCargo{i:02}' for i in range(1,count*2+1))+'\n'
        definitions.append(text)
        loadouts.append('[Loadout]\nnickname = '+nick+'\narchetype = '+nick+'\n'+
                        ''.join(f'equip = cargopod_grey, HpCargo{i:02}\n' for i in range(1,count*2+1)))
        for cargo in catalog['commodities'].values():
            loadouts.append('[Loadout]\nnickname = '+nick+'_'+cargo['nickname']+'\narchetype = '+nick+'\n'+
                            ''.join(f'equip = {cargo["pod"]}, HpCargo{i:02}\ncargo = {cargo["nickname"]}, 50, HpCargo{i:02}\n'
                                    for i in range(1,count*2+1)))
    loadouts.append('[Loadout]\nnickname = tc_locomotive\narchetype = ge_train_loco_player\n'+
                    '\n'.join('equip = '+item for item in ['ge_t_engine_01','infinite_power','scanner01','tractor01','sfx_rumble_ut_large']+
                              [f'co_train_turret01_mark01, HpTurret{i:02}' for i in range(1,6)])+'\n')
    put('DATA/SHIPS/train_courier.ini','\n'.join(definitions))
    put('DATA/SHIPS/train_courier_loadouts.ini','\n'.join(loadouts))
    # Dockable solar: preserve the visible locomotive and add an external berth.
    put(modelpath+'train_locomotive.cmp',contrails.annotated((source/'train_locomotive.cmp').read_bytes()))
    put(modelpath+'train_boarding.cmp',boarding_model(source))
    put(modelpath+'train_boarding.sur',(source/'train_locomotive.sur').read_bytes())
    mats='\n'.join(line for line in section(archtext,'Ship','ge_train_loco_player').splitlines() if line.lower().startswith('material_library'))
    put('DATA/SOLAR/train_courier.ini',parked_solar('[Solar]\nnickname = tc_boarding_solar\nids_name = 237055\nids_info = 1\ntype = STATION\n'+
        'DA_archetype = ships\\utility\\freight_train\\train_boarding.cmp\n'+mats+
        '\nLODranges = 0, 25000\nmass = 10000\nhit_pts = 1000000000\nsolar_radius = 45\n'+
        'docking_sphere = berth, HpDockMountA, 5\nphantom_physics = false\n'))
    prefix='DATA/MISSIONS/TrainCourier/'
    put(prefix+'catalog.ini',(out/'catalog.ini').read_bytes())
    systems=sorted({b['system'] for b in catalog['bases'].values()})
    bases=[];mission_bases=[]
    for system in systems:
        base='tc_'+system+'_base'
        bases.append(f'[Base]\nnickname = {base}\nsystem = {system}\nstrid_name = 1\nfile = Universe\\TrainCourier\\{base}.ini\nautosave_forbidden = true\n')
        faction=next(p['faction'] for b in catalog['bases'].values() for p in b['points'] if p['system']==system)
        mission_bases.append(f'[MBase]\nnickname = {base}\nlocal_faction = {faction}\ndiff = 1\n\n[MRoom]\nnickname = Deck\ncharacter_density = 0\n')
        put('DATA/UNIVERSE/TrainCourier/'+base+'.ini',f'[BaseInfo]\nnickname = {base}\nstart_room = Deck\n\n[Room]\nnickname = Deck\nfile = Universe\\ROOM\\KU\\battleship_deck.ini\n')
        put(prefix+'launch_'+system+'.ini',f'[CharacterEncounter]\nLocation = {base}, Deck\nautoplay = true\nrelocate_player = spaceflight\n\n[Char]\nnpc = test_npc_01\nactor = tc_transfer\nspot = Zs/NPC/Shipdealer/01/A/Stand\nfidget = scripts\\extras\\fidget_stand_male_NULL.thn\n')
    universe=(game/'DATA/UNIVERSE/universe.ini').read_bytes()
    assert b'nickname = tc_rh_biz_base' not in universe,'Already staged/installed; regenerate from clean backup or update installer'
    put('DATA/UNIVERSE/universe.ini',universe+b'\n\n'+'\n'.join(bases).encode())
    put('DATA/MISSIONS/mbases.ini',(game/'DATA/MISSIONS/mbases.ini').read_bytes()+b'\n\n'+'\n'.join(mission_bases).encode())
    # Place alongside the actual Bismarck fixture, not its ring or planet center.
    put(prefix+'objects.ini',boarding_objects(game))
    # A resource-only DLL keeps mission text localizable without reassigning IDs.
    resources=next(s for k,s in sections(game/'bin/freelancer.ini') if k=='resources')
    assert not any('train_courier' in d for d in resources.get('dll',[]))
    index=len(resources.get('dll',[]))+1
    put('bin/train_courier_text.dll',build_text(out,args.language))
    stage_localized(game,out,put)
    ids=[TEXT_IDS[key] for key in IDS_KEYS]
    config='[CourierRules]\nfirst_wagons = 2\nmax_wagons = 20\nfirst_distance = 1\ndistance_step = 1\nbase_reward = 2000\nper_wagon_reward = 500\nper_distance_reward = 1000\ndelivery_radius = 250\ndelivery_speed = 2\ncleanup_distance = 25000\n'
    config+='\n[Presentation]\naudio_enabled = false\nvoice = '+voice+'\n'
    config+=''.join(f'{key}_ids = {value}\n' for key,value in zip(IDS_KEYS,ids))
    put(prefix+'courier.ini',config)
    stage_launchers(index)
    put('DATA/MISSIONS/voice_properties.ini',voice_properties((game/'DATA/MISSIONS/voice_properties.ini').read_bytes()))
    contact=(game/'DATA/RPG/rh_biz_contact.ini').read_bytes()
    assert b'[Dialog]' not in contact,'Existing Bismarck dialogue needs a targeted merge'
    put('DATA/RPG/rh_biz_contact.ini',contact+b'\n'+vendor_dialog().encode())
    # Binaries are staged only after the current sources have built successfully.
    binary=ROOT/'src/obj/train_courier/rpg1/bin'
    client=(binary/'freelancer.exe').read_bytes()
    assert b'RpgDialogNodeText' in client and b'TrainYardBridge' in client,'Client must include RPG dialogue and train controls'
    for name in ['Common.dll','Common.pdb','Server.dll','Server.pdb','Content.dll','Content.pdb','freelancer.exe','freelancer.pdb']:put('bin/'+name,(binary/name).read_bytes())
    (out/'manifest.json').write_text(json.dumps({'game':str(game.resolve()),'language':args.language,'files':records},indent=2),encoding='utf-8')
    print(f'Staged {len(records)} files, 19 wagon sizes, {len(systems)} hidden transfer bases. Audio disabled until recordings are supplied.')

if __name__=='__main__':main()
