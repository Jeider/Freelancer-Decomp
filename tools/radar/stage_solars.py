"""Stage explicit radar metadata in the active solararch; never change game files.

The mining list is vetted against Pythonlancer templates/solar/{asteroid,
gas_crystal,debris_box}.py and the systems referenced by universe.ini.
Those templates generate system objects/loadouts, not this solararch file.
"""
import collections
import hashlib
import json
from pathlib import Path
import re

REPO = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
STAGE = REPO / 'src/obj/radar_mining/data'
ORE = ('om15', 'ku_tgk', 'tau37', 'li_cal', 'co_cur', 'tau29', 'green', 'lava')
MINING = {f'{name}_mineast_super{suffix}' for name in ORE for suffix in ('', '_ultra')}
MINING.update(f'{name}{suffix}' for name in (
    'om15_mineast_super_lowdamage', 'icecrystal_mineast_super',
    'ice_asteroid_insane', 'debris_box_2025') for suffix in ('', '_ultra'))
HIDDEN = {'docking_fixture', 'docking_fixture_mountpoint', 'docking_fixture_traders',
          'tr_point_large_train', 'tr_point_train_cargo', 'tr_point_train_cargo_empty',
          'tr_point_large_transport', 'tr_point_small_transport'}
HEADERS = re.compile(rb'(?m)^\[([^\]\r\n]+)\][^\r\n]*\r?\n')


def sections(data):
    matches = list(HEADERS.finditer(data))
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(data)
        yield match[1].decode().lower(), match.start(), end, data[match.start():end]


def values(section):
    return {k.decode().lower(): v.split(b';')[0].strip().decode('cp1251')
            for k, v in re.findall(rb'(?m)^\s*(\w+)\s*=\s*([^\r\n]*)', section)}


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def main():
    path = GAME / 'DATA/SOLAR/solararch.ini'
    original = path.read_bytes()
    edits, found, archetypes = [], set(), {}
    for kind, start, _, block in sections(original):
        if kind != 'solar':
            continue
        data = values(block)
        name = data.get('nickname', '').lower()
        archetypes[name] = data
        if name not in MINING | HIDDEN:
            continue
        assert name not in found, f'Duplicate solar: {name}'
        found.add(name)
        key = 'radar_mining' if name in MINING else 'radar_hidden'
        assert key not in data, f'Already configured: {name}'
        if name in MINING:
            assert data['type'] == 'NON_TARGETABLE'
            assert data['da_archetype'].lower().startswith('solar\\asteroids_mod\\')
        nickname = re.search(rb'(?mi)^nickname\s*=[^\r\n]*\r?\n', block)
        newline = b'\r\n' if nickname[0].endswith(b'\r\n') else b'\n'
        edits.append((start + nickname.end(), key.encode() + b' = true' + newline))
    assert found == MINING | HIDDEN, sorted((MINING | HIDDEN) - found)
    prepared = original
    for offset, content in reversed(edits):
        prepared = prepared[:offset] + content + prepared[offset:]
    assert re.sub(rb'(?m)^radar_(?:mining|hidden) = true\r?\n', b'', prepared) == original

    # Audit only active main systems: do not include backup or mission copies.
    uses = collections.defaultdict(collections.Counter)
    dependencies = []
    universe = GAME / 'DATA/UNIVERSE/universe.ini'
    dependencies.append(dict(relative=universe.relative_to(GAME).as_posix(), sha256=sha(universe.read_bytes())))
    systems = 0
    for kind, _, _, block in sections(universe.read_bytes()):
        system = values(block)
        if kind != 'system' or not system.get('file', '').lower().startswith('systems_mod\\'):
            continue
        systems += 1
        path = universe.parent / system['file'].replace('\\', '/')
        data = path.read_bytes()
        dependencies.append(dict(relative=path.relative_to(GAME).as_posix(), sha256=sha(data)))
        for section, _, _, obj in sections(data):
            if section == 'object':
                obj = values(obj)
                uses[obj.get('archetype', '').lower()][system['nickname']] += 1
    for name in uses:
        if 'static_large_ast' in name or name == 'sig13_mineable_gas_static':
            assert name not in MINING
    report = dict(systems=systems, mining={name: dict(uses[name]) for name in sorted(MINING)},
                  hidden={name: dict(uses[name]) for name in sorted(HIDDEN)},
                  mining_objects=sum(sum(uses[n].values()) for n in MINING),
                  hidden_objects=sum(sum(uses[n].values()) for n in HIDDEN),
                  excluded_inner_clouds=sum(uses['sig13_mineable_gas_static'].values()))
    target = STAGE / 'DATA/SOLAR/solararch.ini'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(prepared)
    (STAGE / 'report.json').write_text(json.dumps(report, indent=2))
    (STAGE / 'manifest.json').write_text(json.dumps(dict(
        files=[dict(relative='DATA/SOLAR/solararch.ini', original=sha(original), prepared=sha(prepared))],
        dependencies=dependencies), indent=2))
    print(f'Staged {len(MINING)} mining archetypes, {len(HIDDEN)} hidden archetypes; '
          f'{systems} main systems, {report["mining_objects"]} mining objects. '
          f'{report["excluded_inner_clouds"]} inner clouds remain excluded. All original bytes preserved.')


if __name__ == '__main__':
    main()
