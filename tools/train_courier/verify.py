"""Validate staged courier content without modifying the game."""
from pathlib import Path
from dispatcher_en import FAMILIES as ENGLISH_FAMILIES
from dispatcher_en import REPOSITION_FAMILIES
import hashlib
import json
import sys
import math
from export import sections,one
from text_resources import IDS_KEYS,TEXTS,TEXT_IDS,localized_rows
from launchers import startup_inis,DEPENDENCIES

ROOT=Path(__file__).resolve().parents[2]

def main():
    out=ROOT/'out/train_courier';payload=out/'payload'
    manifest=json.loads((out/'manifest.json').read_text(encoding='utf-8'))
    for rel,item in manifest['files'].items():
        assert hashlib.sha256((payload/rel).read_bytes()).hexdigest()==item['after'],rel
    # Partial packages must validate the binaries that will actually run, not
    # stale files left in payload by a previous full installation.
    def effective(relative):
        return (payload if relative in manifest['files'] else Path(manifest['game']))/relative
    client=effective('bin/freelancer.exe').read_bytes()
    assert all(marker in client for marker in (b'RpgDialogNodeText',b'TrainYardBridge',b'TrainCourierBaseTransfer')), \
        'Client lacks RPG dialogue or courier transfer; rebuild freelancer with FreelancerRpgWorld=1'
    content=effective('bin/Content.dll').read_bytes()
    assert b'start_train_courier' in content and b'TrainCourier: NNPath' in content, 'Content lacks the courier controller'
    assert all(marker in effective('bin/Server.dll').read_bytes() for marker in (b'TrainCourierBridge',b'tc_parked_locomotive')), 'Server lacks parked-locomotive launch/cleanup; rebuild Server with Content'
    presentation=next(s for k,s in sections(effective('DATA/MISSIONS/TrainCourier/courier.ini')) if k=='presentation')
    title=int(one(presentation,'title_ids'))
    game=Path(manifest['game']).resolve()
    for path in startup_inis(game):
        relative=str(path.relative_to(game)).replace('\\','/')
        entries=sections(effective(relative))
        data=next(s for k,s in entries if k=='data')
        resources=next(s for k,s in entries if k=='resources')
        for key,value in DEPENDENCIES.items():
            assert value.lower() in [v.replace('/','\\').lower() for v in data.get(key,[])], f'{relative}: missing {key} = {value}'
        dlls=[v.lower() for v in resources.get('dll',[])]
        if title==TEXT_IDS['title']:
            assert Path(dlls[2].replace('\\','/')).name=='nameresources.dll', f'{relative}: wrong name resource index'
        else:
            assert dlls.index('train_courier_text.dll')+1==title//65536, f'{relative}: wrong courier resource index'
    for offset,key in enumerate(IDS_KEYS,1):
        expected=TEXT_IDS[key] if title==TEXT_IDS['title'] else (title//65536)*65536+offset
        assert int(one(presentation,key+'_ids') or 0)==expected, \
            'Mission text/config update required: stage with --update-mission'
    if title==TEXT_IDS['title']:
        sys.path.insert(0,str(ROOT/'tools/targeting_hud'))
        import stage_interface_strings as ids
        rows,registered=localized_rows(game,effective('Assets/Pythonlancer/text/static.py'))
        assert set(TEXT_IDS.values())<=registered.keys(),'Missing Pythonlancer static IDs'
        for ini in startup_inis(game):
            relative=str(ini.relative_to(game)).replace('\\','/')
            resource=next(s for k,s in sections(effective(relative)) if k=='resources')['dll'][2]
            resource=(game/'bin'/resource.replace('\\','/')).resolve().relative_to(game).as_posix()
            english='resources_eng' in resource.lower()
            data=ids.resources(effective(resource))
            for number,ru,en in rows:
                block,slot=(number&65535)//16+1,number%16
                found=[ids.decode_block(raw)[slot] for k,raw in data.items() if k[0]==6 and k[1]==block]
                assert found and all(s==(en if english else ru) for s in found),f'{resource}: IDS {number}'
        contact=sections(effective('DATA/RPG/rh_biz_contact.ini'))
        external=next((one(s,'dialog') for k,s in contact if k=='characterencounter' and one(s,'dialog')),None)
        if external:
            contact=sections(effective('DATA/'+external.replace('\\','/')))
        choices=[s for k,s in contact if k=='dialogchoice' and one(s,'action')=='start_train_courier']
        assert choices and all(2<=int(one(s,'first_wagons'))<=20 for s in choices)
        assert all(one(s,'text_ids') or (external and one(s,'text_ru') and one(s,'text_en'))
                   for k,s in contact if k in ('dialognode','dialogchoice'))
        assert b'RpgDialogNodeTextIds' in client and b'RpgDialogChoiceTextIds' in content
        print('PASS: vendor wagon choices, localized dialogue, RU/EN IDS and Pythonlancer static cache')
    else:
        text_dll=effective('bin/train_courier_text.dll').read_bytes()
        assert all(text.encode('utf-16-le') in text_dll for text in TEXTS[manifest['language']][:len(IDS_KEYS)]), \
            'Mission strings are outdated: stage with --update-mission'
    catalog=json.loads((out/'catalog.json').read_text(encoding='utf-8'))
    assert catalog.get('parking'), 'Re-export catalog with planet docking fixtures'
    for p in catalog['parking']:
        assert p['base'] in catalog['bases'] and p['faction']
    points={p['nickname']:p for base in catalog['bases'].values() for p in base['points']}
    planet_points=[p for p in points.values() if 'planet_clearance' in p]
    assert planet_points,'Re-export catalog with tangent planet freight tracks'
    for p in planet_points:
        planet=p['planet_clearance'];x,_,z=p['position'];cx,_,cz=planet['position']
        yaw=math.radians(p['rotation'][1]);radial=(math.cos(yaw),-math.sin(yaw));axis=(math.sin(yaw),math.cos(yaw))
        assert p['rotation'][0]==p['rotation'][2]==0
        dx,dz=x-cx,z-cz
        assert abs(dx*axis[0]+dz*axis[1])<1e-5,'Train must be tangent to planet'
        assert dx*radial[0]+dz*radial[1]>0,'Next track must move away from planet'
        # Minimum horizontal distance of the entire infinite approach line,
        # including the delivery tolerance. Covers both ends and all train sizes.
        for shift in (0,350):
            d=abs((dx+shift*radial[0])*axis[1]-(dz+shift*radial[1])*axis[0])
            assert d-planet['atmosphere_radius']>=planet['minimum']-1e-5
            assert d-250>planet['atmosphere_radius']
    print(f'PASS: {len(planet_points)} planet tracks tangent, 1 km atmosphere clearance, outward next-order offset')
    assert len(points)==sum(len(b['points']) for b in catalog['bases'].values())
    assert all(r['source'] in catalog['bases'] and r['destination'] in catalog['bases'] and r['distance']>0 for r in catalog['routes'])
    assert any(r['source']=='rh_biz_01_base' and r['destination']=='rh_biz_02_base' and r['distance']==1 for r in catalog['routes'])
    if catalog['version']>=2:
        assert {'Station','Shipyard','Refinery'}<={b['base_type'] for b in catalog['bases'].values()}
        assert any(b['large_planet'] for b in catalog['bases'].values())
        assert any(b['freight_hub'] and not b['large_planet'] and not b['refinery'] for b in catalog['bases'].values())
        cached={one(s,'nickname'):s for k,s in sections(effective('DATA/MISSIONS/TrainCourier/catalog.ini')) if k=='courierpoint'}
        for base in catalog['bases'].values():
            assert not (base['large_planet'] or base['refinery']) or base['freight_hub']
            for point in base['points']:
                for flag in ('freight_hub','large_planet','refinery'):
                    assert one(cached[point['nickname']],flag)==str(base[flag]).lower()
        for route in catalog['routes']:
            assert route['distance']==len(route['path'])
            assert route['jumps']==sum(s['kind']=='jumpgate' for s in route['path'])
            assert 0<=route['minimum_jumps']<=route['jumps']
            assert all(s['kind'] in ('tradelane','jumpgate') for s in route['path'])
            assert all(a['to']==b['from'] for a,b in zip(route['path'],route['path'][1:]))
        print('PASS: Station/Shipyard/Refinery; inherited economic hub markers; graph distance and minimum jump count')
    bases={one(s,'nickname'):s for k,s in sections(effective('DATA/UNIVERSE/universe.ini')) if k=='base'}
    mission_bases={one(s,'nickname') for k,s in sections(effective('DATA/MISSIONS/mbases.ini')) if k=='mbase'}
    npc={one(s,'nickname') for k,s in sections(Path(manifest['game'])/'DATA/MISSIONS/specific_npc.ini') if k=='npc'}
    for p in points.values():
        transfer='tc_'+p['system']+'_base'
        assert transfer in mission_bases,'Missing Content base record'
        assert one(bases[transfer],'autosave_forbidden')=='true'
        assert one(bases[transfer],'system')==p['system']
        rtc=sections(effective('DATA/MISSIONS/TrainCourier/launch_'+p['system']+'.ini'))
        assert any(k=='characterencounter' and one(s,'relocate_player')=='spaceflight' for k,s in rtc)
        assert all(one(s,'npc') in npc for k,s in rtc if k=='char')
    objects=sections(effective('DATA/MISSIONS/TrainCourier/objects.ini'))
    assert not any(k=='trigger' for k,s in objects)
    assert any(k=='msnsolar' and one(s,'base')=='tc_rh_biz_base' for k,s in objects)
    boarding=next(s for k,s in objects if k=='msnsolar' and one(s,'nickname')=='tc_boarding')
    solar=next(s for k,s in sections(effective('DATA/SOLAR/train_courier.ini')) if k=='solar' and one(s,'nickname')=='tc_boarding_solar')
    assert one(solar,'phantom_physics')=='false','Boarding hull must be solid'
    assert one(solar,'docking_sphere')=='berth, HpDockMountA, 5'
    parked=next(s for k,s in sections(effective('DATA/SOLAR/train_courier.ini'))
                if k=='solar' and one(s,'nickname')=='tc_parked_locomotive')
    for key in ('da_archetype','docking_sphere','phantom_physics'):
        assert one(parked,key)==one(solar,key), 'Final solar must preserve the miner launch rig and hull'
    fixture=next(s for k,s in sections(Path(manifest['game'])/'DATA/UNIVERSE/SYSTEMS_MOD/RH_BIZMARK/rh_biz.ini')
                 if k=='object' and one(s,'archetype')=='docking_fixture' and one(s,'dock_with')=='rh_biz_01_base')
    position=[float(x) for x in one(boarding,'position').split(',')]
    center=[float(x) for x in one(fixture,'pos').split(',')]
    w,x,y,z=[float(x) for x in one(boarding,'orientation').split(',')]
    assert abs(w*w+x*x+y*y+z*z-1)<1.e-6
    forward=(-2*(x*z+w*y),-2*(y*z-w*x),-(1-2*(x*x+y*y)))
    toward=(center[0]-position[0],center[2]-position[2])
    alignment=(forward[0]*toward[0]+forward[2]*toward[1])/(toward[0]**2+toward[1]**2)**.5
    assert alignment>.9999 and abs(forward[1])<1.e-6,'Locomotive must face fixture horizontally'
    assert 150<position[1]-center[1]<200,'Park just above upper berth, not 500 m above fixture'
    arches={one(s,'nickname'):s for k,s in sections(effective('DATA/SHIPS/train_courier.ini')) if k=='ship'}
    loadouts={one(s,'nickname'):s for k,s in sections(effective('DATA/SHIPS/train_courier_loadouts.ini')) if k=='loadout'}
    for n in range(2,21):
        name=f'tc_wagons_{n:02}'
        assert name in arches and name in loadouts
        assert len(loadouts[name]['equip'])==n*2
        assert len(arches[name]['hp_type'])==1
        assert len(arches[name]['hp_type'][0].split(','))-1==n*2
        for cargo in catalog['commodities'].values():
            loaded=loadouts[name+'_'+cargo['nickname']]
            assert loaded['equip']==[f'{cargo["pod"]}, HpCargo{i:02}' for i in range(1,n*2+1)]
            assert loaded['cargo']==[f'{cargo["nickname"]}, 50, HpCargo{i:02}' for i in range(1,n*2+1)]
    # A story-only base can have no authored market. It remains a graph/parking
    # anchor but must neither invent stock nor receive a commercial delivery.
    for base in catalog['bases'].values():
        supply={n for n,m in base['market'].items() if m['supply']}
        assert all(set(p['commodities'])==supply for p in base['points'])
    usable=[r for r in catalog['routes'] if r['commodities']]
    assert usable
    for route in catalog['routes']:
        source=catalog['bases'][route['source']]['market'];target=catalog['bases'][route['destination']]['market']
        assert set(route['commodities'])=={n for n,m in source.items() if m['supply'] and target.get(n,{}).get('demand')}
    from order_texts import REASONS
    briefs={one(s,'commodity'):s.get('text_ids',[]) for k,s in sections(effective('DATA/MISSIONS/TrainCourier/descriptions.ini')) if k=='courierdescription'}
    assert set(briefs)==set(catalog['commodities'])=={'comm_'+n for n in REASONS}
    assert all(len(v)==10 and len(set(v))==10 and all(int(i) in registered for i in v) for v in briefs.values())
    assert b'TrainCourierGetHud' in content and b'TrainCourierGetHud' in client
    print(f'PASS: {len(usable)} supply/consumption routes; 500 localized briefs; native timer export and client')
    assert all(name in catalog['commodities'] for point in points.values() for name in point['commodities'])
    voices=sections(effective('DATA/MISSIONS/voice_properties.ini'))
    for name in [one(presentation,'voice')]:
        voice=next(s for k,s in voices if k=='mvoiceprop' and one(s,'voice')==name)
        families=[v for v in voice.get('permutation_count',[]) if v.startswith('tc_')]
        if name=='atc_leg_m01_new':
            counts={v.split(',')[0].strip() for v in families}
            assert set(ENGLISH_FAMILIES)<=counts<=set(ENGLISH_FAMILIES)|set(REPOSITION_FAMILIES)
            assert len(counts)==len(families)
        else:assert len(families)==10
        assert all(v.endswith(', 10') for v in families)
    if one(presentation,'audio_enabled').lower()=='true':
        assert one(presentation,'voice')=='atc_leg_m01_new'
        assert all(marker in content for marker in (b'tc_order',b'tc_destination',b'tc_collect',b'tc_recover'))
        from voice_audio import prepare_english
        path=effective('DATA/AUDIO/voices_space_male.ini')
        reposition=any(one(s,'reposition_audio_enabled').lower()=='true' for k,s in sections(effective('DATA/MISSIONS/TrainCourier/courier.ini')))
        if reposition:assert set(REPOSITION_FAMILIES)<=counts
        assert prepare_english(Path(manifest['game']),catalog,path,reposition)==path.read_bytes(), 'Courier sound durations must match WAV samples'
    print(f'PASS: staged hashes, RPG client, {len(points)} installed trading points, graph routes, hidden bases, RTC NPCs, MsnSolar, 19 wagon sizes, {len(catalog["commodities"])} commodities and selected dispatcher configuration')

if __name__=='__main__':main()
