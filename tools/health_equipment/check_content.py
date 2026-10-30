"""Check the staged live INIs and regeneration helper, including idempotence and tier ceilings."""
from pathlib import Path
import importlib.util
import json
import re
import sys
from prepare import ROOT, GAME, blocks, value, equipment, ships

stage=Path(sys.argv[1])
manifest=json.loads((stage/'manifest.json').read_text())
report=json.loads((stage/'report.json').read_text())
staged={f['relative'].lower():stage/f['relative'] for f in manifest['files']}
def read(relative):
    return staged.get(relative.lower(),GAME/relative).read_bytes().decode('latin1')
config=read('bin/freelancer.ini')
actual_thrusters={};actual_hardware=set();hulls={}
for kind in ('equipment','ships'):
    paths=re.findall(r'(?im)^\s*'+kind+r'\s*=\s*([^;\r\n]+)',config)
    for p in dict.fromkeys(paths):
        text=read('DATA/'+p.strip().replace('\\','/'))
        # Running the upgrader again must leave every unrelated byte unchanged.
        fresh=dict(thrusters={},hardware=[],hulls={})
        assert (equipment if kind=='equipment' else ships)(text,fresh)==text
        for b in blocks(text):
            nick=value(b,'nickname');hp=value(b,'hp_type')
            if b.lower().startswith('[thruster]'):
                assert re.fullmatch(r'hp_thruster_special_(?:[1-9]|10)',hp)
                actual_thrusters[nick]=int(hp.rsplit('_',1)[1])
            if b.lower().startswith('[cloakingdevice]') and hp=='hp_hardware_special_1':
                actual_hardware.add(nick)
            if b.lower().startswith('[ship]'):
                assert re.search(r'(?im)^equipment_slot\s*=\s*HpHardware01\s*,\s*hardware\s*,\s*1\s*$',b)
                mounts={}
                for level,names in re.findall(r'(?im)^hp_type\s*=\s*hp_thruster_special_(\d+)\s*,\s*([^;\r\n]+)',b):
                    for name in names.split(','):mounts.setdefault(name.strip().lower(),set()).add(int(level))
                hulls[nick]=mounts
assert actual_thrusters==report['thrusters']
assert actual_hardware==set(report['hardware'])
for nick,hull in report['hulls'].items():
    expected=set(range(1,hull['max_class']+1))
    for hp in hull['hardpoints']: assert hulls[nick][hp.lower()]==expected
    assert all(level<=hull['max_class'] for levels in hulls[nick].values() for level in levels)
assert report['hulls']['li_elite']['max_class']==6
assert report['hulls']['rh_fighter']['max_class']==8
helper=stage/'Assets/Pythonlancer/tools/equipment_hardware.py'
spec=importlib.util.spec_from_file_location('prepared_hardware',helper);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
sample='[Ship]\nnickname=test\nhp_type=hp_fighter_engine_special_6,HpDrive01\nhp_type=hp_thruster,HpThruster01,HpThruster02\n'
updated=module.upgrade_ships(sample)
assert updated==module.upgrade_ships(updated)
assert 'hp_thruster_special_6' in updated and 'hp_thruster_special_7' not in updated
assert updated.count('equipment_slot = HpHardware01, hardware, 1')==1
source=(ROOT/'src/Server/server_pub.cpp').read_text()
assert '"interface", Player.interface_state & 0xfu)' in source
assert 'Record.Interface = Player.interface_state & 0xfu;' in source
print(f'PASS: {len(actual_thrusters)} classed thrusters, {len(hulls)} hardware-equipped hull definitions, {len(report["hulls"])} tier ceilings, {len(actual_hardware)} internal cloaks; generators idempotent; save masks')
