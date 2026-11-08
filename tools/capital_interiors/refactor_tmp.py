from pathlib import Path

root = Path(__file__).resolve().parents[2]
def change(name, fn):
    p = root/name
    old = p.read_text(encoding='utf-8')
    new = fn(old)
    assert old != new, name
    p.write_text(new, encoding='utf-8')

names = ['menu_universe_base', 'room_control', 'nav_bar', 'nn_inventory', 'nn_ship_trader']
for name in names:
    change(f'src/freelancer/Client/{name}.cpp', lambda s:s.replace('capital_interiors.h','base_interior_profiles.h').replace('CapitalInteriors::','BaseInteriors::'))
change('src/Server/IServerImpl.cpp', lambda s:s.replace('capital_interiors.h','base_interior_profiles.h').replace('CapitalInteriors::','BaseInteriors::'))

def menu(s):
    s = s.replace('bool CapitalProfile;', 'unsigned InteriorProfile;').replace('CapitalProfile', 'InteriorProfile').replace('ResolveCapitalLocation', 'ResolveInteriorLocation').replace('BaseInteriors::Active(', 'BaseInteriors::ProfileId(').replace('bool Profile = BaseInteriors::ProfileId', 'unsigned Profile = BaseInteriors::ProfileId').replace('RoomEntry.InteriorProfile = false;', 'RoomEntry.InteriorProfile = 0;')
    start=s.index('        if (_stricmp(Room->Nickname, "ShipDealer") == 0 &&')
    end=s.index('\n    }',start)
    s=s[:start]+'''        return BaseInteriors::ResolveRoom(Room->BaseId, Location,
                                         GetPlayerShipArchetypeIdRetail());'''+s[end:]
    return s
change('src/freelancer/Client/menu_universe_base.cpp',menu)

def ship(s):
    s=s.replace('#include "capital_interiors.h"\n','').replace('#include "hud_target.h"\n','').replace('#include <algorithm>\n','')
    start=s.index('        RoomData* Room = Owner ? GetRoomRuntimeRoomData(Owner) : nullptr;')
    end=s.index('        // 0x00447331',start)
    return s[:start]+s[end:]
change('src/freelancer/Client/gf_object_ship.cpp',ship)

def room(s):
    s=s.replace('BaseInteriors::RoomFile(Room->BaseId, Room->RoomId, GetPlayerShipArchetypeIdRetail())', '!BaseInteriors::HasCharacters(GetRoomRuntimeRoomData(Room))')
    s=s.replace('return nullptr; // External-mooring terminals have no base NPCs or seated player.', 'return nullptr; // Explicit characters=false in this room INI.')
    s=s.replace('BaseInteriors::RoomFile(Room->BaseId, Room->RoomId,\n        GetPlayerShipArchetypeIdRetail()) ? 0 : 1', 'BaseInteriors::PlacementShadow(Place) ? 1 : 0')
    s=s.replace('Pad.Place->bIsPlayerShip)', 'Pad.Place->bIsPlayerShip &&\n            BaseInteriors::PlacementMatches(Pad.Place, GetPlayerShipArchetypeIdRetail()))')
    return s
change('src/freelancer/Client/room_control.cpp',room)

for name in ['nn_inventory','nn_ship_trader']:
    change(f'src/freelancer/Client/{name}.cpp', lambda s:s.replace('BaseInteriors::Active(GetClientLocationCurrentBase(), GetPlayerShipArchetypeIdRetail())', '!BaseInteriors::ServiceAllowed(GetClientLocationCurrentBase(),\n                                       GetPlayerShipArchetypeIdRetail(), "ShipDealer")'))

def nav(s):
    start=s.index('        if (BaseInteriors::Active(')
    end=s.index('\n\n', start)
    s=s[:start]+'''        unsigned const Ship = GetPlayerShipArchetypeIdRetail();
        // A physical exit must belong to the selected room set. Virtual rooms
        // (Trader/Equipment tabs inside Deck) are not physical locations.
        if (Hotspot->RoomSwitch && Hotspot->Behavior != 11 &&
            !BaseInteriors::RoomAllowed(Data->BaseId,
                MakeLocationID(Data->BaseId, Hotspot->RoomSwitch), Ship))
            continue;
        if (!BaseInteriors::ServiceAllowed(Data->BaseId, Ship, "ShipDealer") &&
            ((Hotspot->SetVirtualRoom && _stricmp(Hotspot->SetVirtualRoom, "ShipDealer") == 0) ||
             (Hotspot->RoomSwitch && _stricmp(Hotspot->RoomSwitch, "ShipDealer") == 0) ||
             (Hotspot->VirtualRoom && _stricmp(Hotspot->VirtualRoom, "ShipDealer") == 0) ||
             Hotspot->Behavior == 7))
            continue;'''+s[end:]
    return s
change('src/freelancer/Client/nav_bar.cpp',nav)

def server(s):
    s=s.replace('BaseInteriors::Active(Players[session_id].current_base,\n                                    Players[session_id].ship_archetype)', '!BaseInteriors::ServiceAllowed(Players[session_id].current_base,\n                                    Players[session_id].ship_archetype, "ShipDealer")')
    s=s.replace('''if (!BaseInteriors::ServiceAllowed(Players[session_id].current_base,
                                    Players[session_id].ship_archetype, "ShipDealer") &&
            location_id == MakeLocationID(Players[session_id].current_base, "ShipDealer")) return;''','''if (!BaseInteriors::RoomAllowed(Players[session_id].current_base, location_id,
                                       Players[session_id].ship_archetype)) return;''')
    return s
change('src/Server/IServerImpl.cpp',server)
