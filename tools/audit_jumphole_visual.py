"""Read the configured game INIs and report jumphole visual coverage. No game writes."""
from collections import Counter
from pathlib import Path
import json
import re

GAME = Path('D:/games/FL_MOD')
DATA = GAME / 'DATA'

def sections(path):
    result = []
    for raw in path.read_text(encoding='latin1').splitlines():
        line = raw.split(';', 1)[0].strip()
        if line.startswith('[') and line.endswith(']'):
            result.append((line[1:-1].lower(), {}))
        elif result and '=' in line:
            key, value = map(str.strip, line.split('=', 1))
            result[-1][1].setdefault(key.lower(), []).append(value.lower())
    return result

def first(s, key, default=''):
    return s.get(key, [default])[0]

def table(entries, kind=None):
    out = {}
    for k, s in entries:
        if kind is None or k == kind:
            # Common's registry retains the first definition of a nickname.
            out.setdefault(first(s, 'nickname'), s)
    return out

config = dict(sections(GAME / 'bin/freelancer.ini'))['data']
arches = table(sections(DATA / config['solar'][0]), 'solar')
loads = table([s for name in config['loadouts'] for s in sections(DATA / name)], 'loadout')
equip = table([s for name in config['equipment'] for s in sections(DATA / name)], 'attachedfx')
effects = table([s for name in config['effects'] for s in sections(DATA / name)], 'effect')
universe = DATA / config['universe'][0]
covered = {'gf_wormhole_01', 'gf_wormhole_light', 'gf_wormhole_green',
           'gf_wormhole_orange', 'gf_wormhole_red', 'gf_wormsparks',
           'gf_hole_01', 'gf_hole_active_01', 'hole_center'}
rows = []
for kind, system in sections(universe):
    if kind != 'system':
        continue
    for objkind, obj in sections(universe.parent / first(system, 'file')):
        arch = arches.get(first(obj, 'archetype'), {})
        if objkind != 'object' or first(arch, 'type') != 'jump_hole':
            continue
        load = loads.get(first(obj, 'loadout', first(arch, 'loadout')), {})
        fx = [first(equip.get(item.split(',')[0].strip(), {}), 'particles') for item in load.get('equip', [])]
        fx = sorted({item for item in fx if item})
        rows.append(dict(system=first(system, 'nickname'), object=first(obj, 'nickname'),
                         archetype=first(obj, 'archetype'), jump_effect=first(obj, 'jump_effect'),
                         effects=fx, types=[first(effects.get(f, {}), 'effect_type') for f in fx],
                         covered=bool(set(fx) & covered), lod=first(arch, 'lodranges')))
out = Path('src/obj/jumphole_inventory.json')
out.write_text(json.dumps(rows, indent=2), encoding='utf8')
print(f'{len(rows)} JUMP_HOLE objects in {len(set(r["system"] for r in rows))} configured systems')
print('Covered idle effects:', sum(r['covered'] for r in rows))
print('Effects:', dict(Counter(f for r in rows for f in r['effects'])))
print('Jump styles:', dict(Counter(r['jump_effect'] for r in rows)))
print('Uncovered:', [(r['system'], r['object'], r['effects']) for r in rows if not r['covered']])
print('Inventory:', out)
