"""Build the Leipzig external-mooring room from the installed Rheinland THN set.

Only writes DATA_EXTRA and out/capital_interiors in this checkout.
"""
from pathlib import Path
import json
import re

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
DATA = ROOT / 'DATA_EXTRA'
OUT = ROOT / 'out/capital_interiors'


def blocks(text, table='entities'):
    start = re.search(r'\b' + table + r'\s*=\s*\{', text).end()
    depth = 0
    quoted = False
    escaped = False
    begin = None
    for i in range(start, len(text)):
        c = text[i]
        if quoted:
            if escaped:
                escaped = False
            elif c == '\\':
                escaped = True
            elif c == '"':
                quoted = False
            continue
        if c == '"':
            quoted = True
        elif c == '{':
            if depth == 0:
                begin = i
            depth += 1
        elif c == '}':
            if depth == 0:
                return
            depth -= 1
            if depth == 0:
                yield text[begin:i + 1]
    raise ValueError('Unterminated THN table')


def field(block, name):
    match = re.search(r'\b' + name + r'\s*=\s*"([^"]*)"', block)
    return match.group(1) if match else ''


def camera(name):
    # Window-facing view; room architecture stays at the source's unit scale.
    return '''{
    entity_name="%s", type=3, template_name="", usr_flg=0, lt_grp=0, srt_grp=0,
    spatialprops={pos={-8, 2.7, 0}, orient={{0,0,1},{0,1,0},{-1,0,0}}},
    cameraprops={fovh=28, hvaspect=1.333333, nearplane=0.3, farplane=20000}
}''' % name


def write(relative, text):
    path = DATA / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='ascii')


def main():
    source = GAME / 'DATA/SCRIPTS/BASES/rh_08_bar_hardpoint_r6.thn'
    entities = list(blocks(source.read_text()))
    retained = []
    removed = []
    for entity in entities:
        name = field(entity, 'entity_name')
        if name in ('Set_rh_08_depot', 'LtShadowSource', 'LtGlareSource'):
            if name == 'Set_rh_08_depot':
                entity = re.sub(r'\bflags\s*=\s*\d+', 'flags=6', entity)
            retained.append(entity)
        else:
            removed.append(name)
    assert len(retained) == 3
    retained.extend(camera(name) for name in (
        'Camera_0', 'Camera_Trader_Desk', 'Camera_Trader_Wide',
        'Camera_Equip_Desk', 'Camera_Wide'))
    retained.append('''{
    entity_name="X/ShipExterior/01", type=7, template_name="", usr_flg=0,
    lt_grp=0, srt_grp=0,
    spatialprops={pos={1200,0,0}, orient={{1,0,0},{0,1,0},{0,0,1}}}
}''')
    write('SCRIPTS/BASES/capital/rh_depot_mooring.thn',
          'duration=10000\nentities={\n' + ',\n'.join(retained) + '\n}\nevents={}\n')
    # Keep the existing lighting. This script contains lights and markers only.
    ambient = GAME / 'DATA/SCRIPTS/BASES/rh_08_bar_ambi_all.thn'
    for entity in blocks(ambient.read_text()):
        assert not field(entity, 'template_name'), field(entity, 'entity_name')
    room = r'''[Room_Info]
set_script = Scripts\Bases\capital\rh_depot_mooring.thn
scene = all, ambient, Scripts\Bases\rh_08_bar_ambi_all.thn
scene = ambient, scripts\bases\ambi_terrain_bg.thn
scene = ambient, scripts\bases\ambi_banner_depot.thn

[Room_Sound]
ambient = ambience_deck_space_smaller

[PlayerShipPlacement]
name = X/ShipExterior/01

[Camera]
name = Camera_0

[Hotspot]
name = IDS_HOTSPOT_DECK
behavior = ExitDoor
room_switch = Deck

[Hotspot]
name = IDS_HOTSPOT_BAR
behavior = ExitDoor
room_switch = Bar

[Hotspot]
name = IDS_HOTSPOT_COMMODITYTRADER_ROOM
behavior = VirtualRoom
room_switch = Trader

[Hotspot]
name = IDS_HOTSPOT_EQUIPMENTDEALER_ROOM
behavior = VirtualRoom
room_switch = Equipment

[Hotspot]
name = IDS_NN_REPAIR_YOUR_SHIP
behavior = Repair
virtual_room = Deck

[Hotspot]
name = IDS_DEALER_FRONT_DESK
behavior = FrontDesk
state_read = 1
state_send = 2
virtual_room = Trader

[Hotspot]
name = IDS_HOTSPOT_COMMODITYTRADER
behavior = StartDealer
state_read = 2
state_send = 1
virtual_room = Trader

[Hotspot]
name = IDS_DEALER_FRONT_DESK
behavior = FrontDesk
state_read = 1
state_send = 2
virtual_room = Equipment

[Hotspot]
name = IDS_HOTSPOT_EQUIPMENTDEALER
behavior = StartEquipDealer
state_read = 2
state_send = 1
virtual_room = Equipment

[Hotspot]
name = IDS_NN_REPAIR_YOUR_SHIP
behavior = Repair
virtual_room = Equipment
'''
    write('UNIVERSE/ROOM/RH/capital_deck.ini', room)
    write('INTERFACE/capital_interiors.ini', r'''; Optional room variants; logical location IDs remain unchanged.
[Base]
nickname = om15_01_base
room = Deck, UNIVERSE\ROOM\RH\capital_deck.ini
''')
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'scene.json').write_text(json.dumps({
        'source': str(source), 'entities_removed': removed,
        'entities_retained': [field(e, 'entity_name') for e in retained],
    }, indent=2))
    print('Prepared capital Deck: original depot shell, no bar furniture/characters, exterior player mount.')


if __name__ == '__main__':
    main()
