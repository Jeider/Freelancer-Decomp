"""Export Pythonlancer's trade depths and the INSTALLED trading point poses.

Output is staged in this repo. Pythonlancer's graph generator uses its TRACKS
temporary directory when constructing the universe; no game INIs are installed.
The export(core, game, output) entry point can also be called after world generation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import sys
import contextlib
import math

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')


def sections(path):
    result = []
    data = path.read_bytes()
    try:
        source = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        source = data.decode('cp1251')
    for raw in source.splitlines():
        line = raw.split(';', 1)[0].strip()
        if line.startswith('[') and line.endswith(']'):
            result.append((line[1:-1].lower(), {}))
        elif '=' in line and result:
            key, value = line.split('=', 1)
            result[-1][1].setdefault(key.strip().lower(), []).append(value.strip())
    return result


def one(section, key, default=''):
    return section.get(key, [default])[-1]


def triple(value):
    values = [float(v.strip()) for v in value.split(',')]
    assert len(values) == 3
    return values


def planet_cargo_pose(point, planet, clearance=1000.0):
    """Horizontal tangent track, with local +X pointing away from the planet.

    Runtime adds 350 m along +X for the next order. Using the horizontal
    atmosphere radius also makes the whole straight coupling approach safe,
    regardless of train length or the runtime's additional vertical clearance.
    """
    center=triple(one(planet,'pos'))
    atmosphere=float(one(planet,'atmosphere_range'))
    position=list(point['position'])
    dx,dz=position[0]-center[0],position[2]-center[2]
    radius=math.hypot(dx,dz)
    if radius<1:raise ValueError('Planet depot has no horizontal radial direction: '+point['nickname'])
    ux,uz=dx/radius,dz/radius
    safe_radius=max(radius,atmosphere+clearance)
    position[0]=center[0]+ux*safe_radius;position[2]=center[2]+uz*safe_radius
    point['position']=position
    # pointOrientation(yaw): +X=(cos(yaw),0,-sin(yaw)); +/-Z is tangent.
    point['rotation']=[0.0,math.degrees(math.atan2(-uz,ux)),0.0]
    point['planet_clearance']=dict(nickname=one(planet,'nickname'),position=center,
                                   atmosphere_radius=atmosphere,minimum=clearance)


def fixture_pose(game, fixture):
    """Park above the upper berth, with the locomotive's nose toward the fixture."""
    import struct
    from scipy.spatial.transform import Rotation
    sys.path.insert(0, str(ROOT/'tools/train_consist'))
    import prepare as model
    definition = next(s for k, s in sections(game/'DATA/SOLAR/solararch.ini')
                      if k == 'solar' and one(s, 'nickname') == 'docking_fixture')
    tree = model.u.read_tree((game/'DATA'/one(definition, 'da_archetype').replace('\\', '/')).read_bytes())[1][0]
    def find(node):
        if node.name.lower() == 'hpdockmounta':
            return node
        for child in node.children:
            result = find(child)
            if result is not None:
                return result
    mount = struct.unpack('<3f', model.sur.child(find(tree), 'Position').blob)
    angles = triple(one(fixture, 'rotate', '0,0,0'))
    assert angles[0] == angles[2] == 0, 'Courier parking requires a horizontal fixture'
    rotation = Rotation.from_euler('xyz', angles, degrees=True)
    position = rotation.apply([mount[0], mount[1]+35, mount[2]+75])+triple(one(fixture, 'pos'))
    x, y, z, w = rotation.as_quat()
    return position.tolist(), angles, [w, x, y, z]


def export(core, game, output):
    universe = game / 'DATA/UNIVERSE/universe.ini'
    entries = sections(universe)
    installed_bases = {one(s, 'nickname').lower(): s for kind, s in entries if kind == 'base'}
    points = {}
    installed_objects = {}
    parking = []
    solar_path = game/'DATA/SOLAR/solararch.ini'
    solar_defs={one(s,'nickname').lower():s for k,s in sections(solar_path) if k=='solar'}
    rings = {one(s, 'nickname').lower() for k, s in sections(solar_path)
             if k == 'solar' and one(s, 'type').upper() == 'DOCKING_RING'}
    inputs = {str(universe): hashlib.sha256(universe.read_bytes()).hexdigest()}
    fixture_arch = next(s for k, s in sections(solar_path)
                        if k == 'solar' and one(s, 'nickname') == 'docking_fixture')
    fixture_model = game/'DATA'/one(fixture_arch, 'da_archetype').replace('\\', '/')
    for path in (solar_path, fixture_model):
        inputs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    data = next(s for k,s in sections(game/'bin/freelancer.ini') if k=='data')
    loadouts, equipment, goods = {}, {}, {}
    for key, target, category in [('loadouts',loadouts,'loadout'),('equipment',equipment,'commodity'),('goods',goods,'good')]:
        for relative in data.get(key,[]):
            path=game/'DATA'/relative.replace('\\','/')
            if not path.exists():continue
            inputs[str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
            target.update({one(s,'nickname'):s for k,s in sections(path) if k==category})
    commodities={}
    # Only Pythonlancer's goods are eligible, even if a legacy loadout names a
    # retail commodity. The user's dispatcher inherits this same vocabulary.
    authored_goods={c.get_nickname():c.get_msg_id_prefix() for c in core.store.get_commodities()}
    def register_goods(names):
        for name in names:
            pod=one(equipment.get(name,{}),'pod_appearance')
            if name in authored_goods and pod:
                commodities[name]=dict(nickname=name,pod=pod,name_ids=int(one(equipment[name],'ids_name','0')),
                                       voice_name=authored_goods[name])
        return sorted(name for name in names if name in commodities)
    for kind, system in entries:
        if kind != 'system' or not one(system, 'file'):
            continue
        path = game / 'DATA/UNIVERSE' / one(system, 'file').replace('\\', '/')
        if not path.exists():
            continue
        objects = {one(s, 'nickname').lower(): s for k, s in sections(path) if k == 'object'}
        installed_objects[one(system,'nickname')]=objects
        planet_bases = {one(s, 'dock_with').lower() for s in objects.values()
                        if one(s, 'archetype').lower() in rings}
        for name, fixture in objects.items():
            base = one(fixture, 'dock_with').lower()
            if one(fixture, 'archetype').lower() != 'docking_fixture' or base not in planet_bases:
                continue
            parking.append(dict(nickname=name, base=base, system=one(system, 'nickname'),
                                fixture=fixture, faction=one(fixture, 'reputation')))
        for name, fixture in objects.items():
            if not re.search(r'_tr_point\d+$', name):
                continue
            base = one(fixture, 'dock_with').lower()
            if base not in installed_bases:
                continue
            trains = [s for n, s in objects.items() if n.startswith(name + '_moor_obj')
                      and one(s, 'archetype').startswith(('tr_point_large_train', 'tr_point_train_cargo'))]
            if not trains:
                continue
            cargo=sorted({line.split(',')[0].strip() for train in trains
                          for line in loadouts.get(one(train,'loadout'),{}).get('cargo',[])})
            for commodity_name in cargo:
                if commodity_name not in authored_goods:
                    continue
                equip=equipment.get(commodity_name,{})
                pod=one(equip,'pod_appearance')
                if pod:
                    commodities[commodity_name]=dict(nickname=commodity_name,pod=pod,name_ids=int(one(equip,'ids_name','0')),
                                           voice_name=authored_goods[commodity_name])
            cargo=[name for name in cargo if name in commodities]
            # Keep actual fixture positions; do not reroll Pythonlancer's random
            # depot type/cargo choices. Local offsets provide clearance for N cars.
            points.setdefault(base, []).append(dict(
                nickname=name, system=one(system, 'nickname'), base=base,
                position=triple(one(fixture, 'pos')), rotation=triple(one(fixture, 'rotate', '0,0,0')),
                faction=one(fixture, 'reputation'),
                train_objects=[one(s, 'nickname') for s in trains], commodities=cargo))
        inputs[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    bases = {};routes = []
    from universe.content.main_objects import Station,Shipyard,Refinery,Jumpgate,DockableObject
    from universe.content import meta
    from trade_graph import paths_from
    skipped_edges=set();disconnected_objects=set()
    authored_bases=list(core.universe.get_bases())
    # Station/Shipyard classes normally have no diversion trading fixtures.
    # Cache a free-space depot above the installed station assembly instead.
    for base in authored_bases:
        obj=base.system_object;name=obj.get_base_nickname().lower()
        if not isinstance(obj,(Station,Shipyard,Refinery)) or name in points or name not in installed_bases:continue
        objects=installed_objects.get(obj.system.NAME,{})
        anchor_name=obj.get_space_object_name().lower();anchor=objects.get(anchor_name)
        if not anchor or one(anchor,'dock_with').lower()!=name:continue
        cargo=register_goods({c.get_nickname() for c in base.get_commodities_values() if c.in_stock()})
        if not cargo:
            # Stations that only consume can still receive and forward a train.
            cargo=register_goods({c.get_nickname() for c in base.get_commodities_values() if c.is_consume()})
        if not cargo:continue
        position=triple(one(anchor,'pos'))
        assembly=[s for n,s in objects.items() if n==anchor_name or n.startswith(anchor_name+'_')]
        top=max(triple(one(s,'pos'))[1]+float(one(solar_defs.get(one(s,'archetype').lower(),{}),'solar_radius','1000'))
                for s in assembly if one(s,'pos'))
        position[1]=max(position[1]+2000,top+1000)
        angles=triple(one(anchor,'rotate','0,0,0'))
        points[name]=[dict(nickname=anchor_name+'_courier_point',system=obj.system.NAME,base=name,
                           position=position,rotation=[0,angles[1],0],faction=one(anchor,'reputation'),
                           train_objects=[],commodities=cargo,kind='station_depot',anchor=anchor_name)]
    # Use the actual planet's base link, not a nearest-body guess. Apply only to
    # freight tracks; the locomotive boarding/return berths retain fixture poses.
    for objects in installed_objects.values():
        for planet in objects.values():
            base=one(planet,'base').lower()
            if base not in points or not one(planet,'atmosphere_range'):continue
            for point in points[base]:planet_cargo_pose(point,planet)
    for base in authored_bases:
        obj = base.system_object
        name = obj.get_base_nickname().lower()
        if name not in points:
            continue
        graph = paths_from(obj,Jumpgate,skipped_edges)
        jump_graph = paths_from(obj,Jumpgate,skipped_edges,minimize_jumps=True)
        if len(graph)==1:
            disconnected_objects.add(obj.system.NAME+':'+obj.get_full_alias());continue
        bases[name] = dict(nickname=name, system=obj.system.NAME,
                           base_type='Refinery' if isinstance(obj,Refinery) else 'Shipyard' if isinstance(obj,Shipyard) else 'Station' if isinstance(obj,Station) else 'TradingDepot',
                           freight_hub=isinstance(obj.BASE_PROPS,(meta.LargePlanet,meta.Megabase,meta.Refinery)),
                           large_planet=isinstance(obj.BASE_PROPS,meta.LargePlanet),
                           refinery=isinstance(obj.BASE_PROPS,meta.Refinery),
                           economic_type=type(obj.BASE_PROPS).__name__,
                           name_ids=int(one(installed_bases[name], 'strid_name', '0')),
                           voice_name=base.get_base_msg_relative(), points=points[name])
        for target,path in graph.items():
            if not isinstance(target,DockableObject):continue
            destination = target.get_base_nickname().lower()
            if destination != name and destination in points:
                routes.append(dict(source=name, destination=destination, distance=len(path),
                                   jumps=sum(step['kind']=='jumpgate' for step in path),
                                   minimum_jumps=sum(step['kind']=='jumpgate' for step in jump_graph[target]),path=path))
    assert 'rh_biz_01_base' in bases, 'Bismarck trading points missing'
    routes = [r for r in routes if r['destination'] in bases]
    # Decorative moored trains are not a market. Export the authored economic
    # roles, including true consumption separately from intermediary resale.
    for base in authored_bases:
        name=base.system_object.get_base_nickname().lower()
        if name not in bases:continue
        market={}
        for c in base.get_commodities_values():
            nick=c.get_nickname()
            if nick not in commodities:continue
            market[nick]=dict(supply=bool(c.in_stock()), demand=bool(c.consume),
                              price=max(1,round(c.get_commodity_price())))
        bases[name]['market']=market
        for point in bases[name]['points']:
            point['commodities']=sorted(n for n,m in market.items() if m['supply'])
    for route in routes:
        route['commodities']=sorted(n for n,m in bases[route['source']]['market'].items()
                                    if m['supply'] and bases[route['destination']]['market'].get(n,{}).get('demand'))
    # These bases have graph distances and existing per-system transfer bases.
    # An arbitrary trading point can never become a final parking destination.
    parking = [p for p in parking if p['base'] in bases]
    for p in parking:
        # Story fixtures outside the courier graph can have arbitrary poses.
        # Resolve only the eligible graph bases, matching runtime selection.
        p['position'], p['rotation'], _ = fixture_pose(game, p.pop('fixture'))
    assert any(p['base'] == 'rh_biz_01_base' for p in parking), 'No Bismarck planet parking'
    assert routes, 'No connected courier destinations'
    output.mkdir(parents=True, exist_ok=True)
    catalog = dict(version=2, depth_convention='Shortest authored TradeConnection edges + jumpgate crossings; each costs 1',
                   bases=bases, routes=routes, parking=parking, commodities=commodities, inputs=inputs, excluded_jump_edges=sorted(skipped_edges),
                   disconnected_objects=sorted(disconnected_objects))
    (output/'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    ini = ['; Pythonlancer: each TradeConnection and jumpgate crossing costs one.', '[CourierCatalog]', 'version = 2']
    for base in bases.values():
        for p in base['points']:
            ini += ['', '[CourierPoint]', 'nickname = '+p['nickname'], 'base = '+p['base'],
                    'system = '+p['system'], 'faction = '+p['faction'],
                    'freight_hub = '+str(base['freight_hub']).lower(),
                    'large_planet = '+str(base['large_planet']).lower(),
                    'refinery = '+str(base['refinery']).lower(),
                    'position = '+', '.join(map(str, p['position'])),
                    'rotation = '+', '.join(map(str, p['rotation'])),
                    'name_ids = '+str(base['name_ids']), 'voice_name = '+base['voice_name'],
                    'transfer_base = tc_'+p['system']+'_base']
            ini += ['commodity = '+name for name in p['commodities']]
            ini += ['demand = '+name for name,m in base['market'].items() if m['demand']]
            ini += [f'supply_price = {name}, {m["price"]}' for name,m in base['market'].items() if m['supply']]
    for commodity in commodities.values():
        ini += ['', '[CourierCommodity]']+[key+' = '+str(value) for key,value in commodity.items()]
    for p in parking:
        base = bases[p['base']]
        ini += ['', '[CourierParking]', 'nickname = '+p['nickname'], 'base = '+p['base'],
                'system = '+p['system'], 'faction = '+p['faction'],
                'position = '+', '.join(map(str, p['position'])),
                'rotation = '+', '.join(map(str, p['rotation'])),
                'name_ids = '+str(base['name_ids']), 'voice_name = '+base['voice_name'],
                'transfer_base = tc_'+p['system']+'_base']
    for r in routes:
        ini += ['', '[CourierRoute]', 'source = '+r['source'], 'destination = '+r['destination'],
                'distance = '+str(r['distance']), 'jumps = '+str(r['minimum_jumps'])]
    (output/'catalog.ini').write_text('\n'.join(ini)+'\n', encoding='utf-8')
    print(f'Exported {len(bases)} bases, {sum(len(b["points"]) for b in bases.values())} trading points, {len(routes)} routes')
    if skipped_edges:
        print(f'Excluded {len(skipped_edges)} jump edges without reciprocal gates; see catalog.json')
    return catalog


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=GAME)
    parser.add_argument('--output', type=Path, default=ROOT/'out/train_courier')
    args=parser.parse_args()
    source=args.game/'Assets/Pythonlancer'
    sys.dont_write_bytecode=True
    sys.path.insert(0,str(source))
    os.chdir(source)
    args.output.mkdir(parents=True,exist_ok=True)
    with (args.output/'pythonlancer.log').open('w',encoding='utf-8') as log, contextlib.redirect_stdout(log):
        from core import get_core
        core=get_core()
    export(core,args.game,args.output)


if __name__=='__main__':
    main()
