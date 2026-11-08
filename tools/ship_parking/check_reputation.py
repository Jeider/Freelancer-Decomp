"""Verify staged/installed reputation data, seller factions and refusal assets."""
import argparse
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from reputation import PROJECT, GAME, OUT, contacts, digest
from managers.parking_commandants import parse, one
from files.rpg_reputation import parking_rules, parking_scenario, parking_denial_ini

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--installed', action='store_true')
args = parser.parse_args()
root = GAME if args.installed else OUT / 'payload'
manifest = json.loads((OUT / 'manifest.json').read_text())
for name, hashes in manifest['files'].items():
    assert digest(root / name) == hashes['after'], name
for name, expected in manifest['dependencies'].items():
    assert digest(GAME / name) == expected, name

rows = contacts()
factions = {row['base']: row['faction'] for row in rows}
rules = (root / 'DATA/RPG/ship_parking.ini').read_text(encoding='utf-8')
assert parking_rules(rules, factions) == rules
bases = {one(row, 'base'): row for kind, row in parse(rules) if kind == 'parkingbase'}
groups = set()
for row in rows:
    assert one(bases[row['base']], 'reputation_faction') == row['faction'], row['base']
    content = (root / 'DATA' / (row['dialog'] or row['rtc'])).read_text(encoding='utf-8-sig')
    denial = [v for k, v in parse(content) if k == 'dialognode' and one(v, 'nickname') == 'parking_bad_reputation']
    assert len(denial) == 1, row['base']
    assert parking_denial_ini(content) == content
    if not row['group']:
        continue
    group = row['group']; groups.add(group)
    assert one(denial[0], 'fragment') == group + '_frag0023'
    scenario = json.loads((PROJECT / 'story/rpg' / (group + '.json')).read_text(encoding='utf-8'))
    assert parking_scenario(scenario) == scenario
    scenes = json.loads((GAME / f'DATA/SCRIPTS/RPG/{group}/en/manifest.json').read_text(encoding='utf-8'))
    fragment = next(f for f in scenes['fragments'] if f['id'] == group + '_frag0023')
    assert digest(GAME / 'DATA' / fragment['path']) == fragment['sha256']
    assert digest(GAME / 'DATA' / fragment['audio']) == fragment['audio_sha256']

owner_files = list((root / 'DATA/RPG/courier').glob('*_dialog.ini'))
for path in owner_files:
    content = path.read_text(encoding='utf-8')
    header = next(v for k, v in parse(content) if k == 'dialog')
    assert one(header, 'minimum_reputation') == '0', path
    assert one(header, 'reputation_strict') == '1', path
    assert one(header, 'reputation_faction') == factions[one(header, 'courier_base')], path
    assert any(k == 'dialognode' and one(v, 'nickname') == 'bad_reputation' for k, v in parse(content)), path
assert len(rows) == 233 and len(groups) == 55 and len(owner_files) == 19
print('PASS: 233 seller factions/refusals, 55 recorded refusal scenes, 19 strict owner gates, package hashes and idempotency')
