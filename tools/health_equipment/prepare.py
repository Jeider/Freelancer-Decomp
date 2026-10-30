"""Stage Health/global preferences, classed thrusters and player hardware; no live writes."""
from pathlib import Path
import ast
import collections
import datetime
import hashlib
import json
import re
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
BIN = ROOT / 'src/obj/health_equipment/bin'
sys.path.insert(0, str(ROOT / 'tools/flight_actions'))
from prepare_install import PE, directory, exports, string

def sha(data):
    return hashlib.sha256(data).hexdigest().upper()

def blocks(text):
    return re.split(r'(?m)(?=^\[[^\r\n]+\])', text)

def value(block, key):
    m = re.search(r'(?im)^\s*' + re.escape(key) + r'\s*=\s*([^;\r\n]+)', block)
    return m[1].strip() if m else ''

def insert(block, line):
    newline = '\r\n' if '\r\n' in block else '\n'
    key = line.split('=')[0].strip()
    if key == 'hp_type' and value(block, key):
        raise ValueError('Equipment already has hp_type: ' + value(block, 'nickname'))
    at = re.search(r'(?im)^nickname\s*=[^\r\n]*\r?\n', block)
    if not at: raise ValueError('Missing nickname')
    return block[:at.end()] + line + newline + block[at.end():]

def equipment(text, report):
    result = []
    for b in blocks(text):
        nick = value(b, 'nickname')
        if b.lower().startswith('[thruster]'):
            match = re.search(r'(?:afterburn|thruster)_?0?(10|[1-9])(?:_[a-z]+)?$', nick)
            # Named Order/Nomad thrusters are the top tier; numbered models keep their level.
            tier = int(match[1]) if match else {'order_thruster':10, 'no_thruster':10, 'nomad_thruster':10}[nick]
            if value(b, 'hp_type') != f'hp_thruster_special_{tier}':
                b = insert(b, f'hp_type = hp_thruster_special_{tier}')
            report['thrusters'][nick] = tier
        elif b.lower().startswith('[cloakingdevice]') and nick in {
            'cloaking_device', 'pl_cloak_slow', 'pl_cloak_fast', 'cloak_msn6'}:
            if value(b, 'hp_type') != 'hp_hardware_special_1':
                b = insert(b, 'hp_type = hp_hardware_special_1')
            report['hardware'].append(nick)
        result.append(b)
    return ''.join(result)

def ships(text, report):
    result = []
    for b in blocks(text):
        if not b.lower().startswith('[ship]'):
            result.append(b); continue
        nick = value(b, 'nickname')
        levels = re.findall(r'(?im)^hp_type\s*=\s*hp_\w+_engine_special_(\d+)', b)
        if not levels:
            levels = re.findall(r'(?im)^hp_type\s*=\s*hp_(?:gun|\w+_shield)_special_(\d+)', b)
        tier = max(map(int, levels), default=10)
        newline = '\r\n' if '\r\n' in b else '\n'
        def thruster(m):
            hps = m[1].split(';')[0].strip()
            report['hulls'][nick] = dict(max_class=tier, hardpoints=[h.strip() for h in hps.split(',')])
            return newline.join(f'hp_type = hp_thruster_special_{i}, {hps}' for i in range(1, tier+1))
        b = re.sub(r'(?im)^hp_type\s*=\s*hp_thruster\s*,\s*([^\r\n]*)', thruster, b)
        if not re.search(r'(?im)^equipment_slot\s*=\s*HpHardware01\s*,', b):
            b = insert(b, 'equipment_slot = HpHardware01, hardware, 1')
        result.append(b)
    return ''.join(result)

def replace_once(text, old, new):
    if new in text: return text
    if text.count(old) != 1: raise ValueError('Generator changed: ' + old[:90])
    return text.replace(old, new)

def main():
    stage = ROOT / 'src/obj/health_equipment_install' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    payload = {}
    report = dict(thrusters={}, hardware=[], hulls={})
    config = (GAME / 'bin/freelancer.ini').read_text()
    for kind in ('equipment', 'ships'):
        paths = re.findall(r'(?im)^\s*' + kind + r'\s*=\s*([^;\r\n]+)', config)
        for p in dict.fromkeys(paths):
            relative = 'DATA/' + p.strip().replace('\\','/')
            original = (GAME / relative).read_bytes()
            content = original.decode('latin1')
            changed = (equipment if kind == 'equipment' else ships)(content, report).encode('latin1')
            if changed != original: payload[relative] = changed
    # A historical custom NPC loadout uses the same tradable cloak as the player.
    relative = 'DATA/SHIPS/loadout_mod.ini'
    content = (GAME / relative).read_bytes()
    changed = re.sub(rb'(?im)^(equip\s*=\s*cloaking_device\s*,\s*)HpConnect\b',
                     rb'\1HpHardware01', content)
    if changed != content: payload[relative] = changed

    generator = 'Assets/Pythonlancer/'
    relative = generator + 'world/thruster.py'
    text = (GAME / relative).read_text(encoding='utf-8')
    text = replace_once(text, 'nickname = {nickname}\nids_name', 'nickname = {nickname}\nhp_type = hp_thruster_special_{equipment_class}\nids_name')
    text = replace_once(text, "'nickname': self.get_nickname(),", "'nickname': self.get_nickname(),\n            'equipment_class': self.equipment_class,")
    ast.parse(text); payload[relative] = text.encode('utf-8')
    relative = generator + 'world/hardware.py'
    text = (GAME / relative).read_text(encoding='utf-8')
    text = replace_once(text, '[CloakingDevice]\nnickname = {self.get_nickname()}\n',
                        '[CloakingDevice]\nnickname = {self.get_nickname()}\nhp_type = hp_hardware_special_1\n')
    ast.parse(text); payload[relative] = text.encode('utf-8')
    relative = generator + 'world/ship.py'
    text = (GAME / relative).read_text(encoding='utf-8')
    text = replace_once(text, "lines.append(self.build_equip_line(self.THRUSTER_CLASS, ', '.join(self.THRUSTERS)))",
                        "for tier in range(1, self.get_equipment_level() + 1):\n                lines.append(self.build_equip_line(f'hp_thruster_special_{tier}', ', '.join(self.THRUSTERS)))")
    text = replace_once(text, '    def get_generic_equip_lines(self):\n        lines = []',
                        "    def get_generic_equip_lines(self):\n        lines = ['equipment_slot = HpHardware01, hardware, 1']")
    ast.parse(text); payload[relative] = text.encode('utf-8')
    # Capital/static ship fragments also need the new slot after a full regeneration.
    relative = generator + 'managers/shiparch.py'
    text = (GAME / relative).read_text(encoding='utf-8')
    text = replace_once(text, 'from world.ship import Ship', 'from world.ship import Ship\nfrom tools.equipment_hardware import upgrade_ships')
    if text.count('        return shiparch\n') != 2 and text.count('        return upgrade_ships(shiparch)\n') != 2:
        raise ValueError('Expected both shiparch generators')
    text = text.replace('        return shiparch\n', '        return upgrade_ships(shiparch)\n')
    ast.parse(text); payload[relative] = text.encode('utf-8')
    # A small standalone helper shares the exact live-data transformation and is idempotent.
    import inspect
    helper = 'import re\n\n' + '\n\n'.join(inspect.getsource(f) for f in (blocks, value, insert, ships))
    helper += "\n\ndef upgrade_ships(text):\n    return ships(text, {'hulls': {}})\n"
    ast.parse(helper); payload[generator + 'tools/equipment_hardware.py'] = helper.encode('utf-8')

    port = (GAME / 'bin/port.ini').read_bytes()
    if re.search(rb'(?im)^internal_classes\s*=', port):
        port = re.sub(rb'(?im)^(internal_classes\s*=\s*)\d+', rb'\g<1>1', port)
    else:
        port += b'\r\n[Equipment]\r\ninternal_classes = 1\r\n'
    payload['bin/port.ini'] = port
    for name in ('Common.dll','Common.pdb','Server.dll','Server.pdb','freelancer.exe','freelancer.pdb'):
        payload['bin/'+name] = (BIN / name).read_bytes()
    payload['DATA/INTERFACE/HUD/EXTRA/HUD_DefCloak.3db'] = (ROOT/'assets/hud/extra/HUD_DefCloak.3db').read_bytes()

    # Verify every imported game symbol against the complete resulting binary set.
    dependencies = {}
    for name in ('Common.dll','Server.dll','freelancer.exe'):
        pe = PE(BIN / name)
        d = directory(pe, 1)
        while d:
            lookup, _, _, dll_name, first = struct.unpack('<5I', pe.read(d, 20))
            if not dll_name: break
            dll = string(pe, dll_name).decode('ascii')
            installed = GAME/'bin'/dll
            replacement = next((k for k in payload if k.lower() == 'bin/'+dll.lower()), None)
            if installed.exists() or replacement:
                path = BIN / dll if replacement else installed
                named, ordinal = exports(PE(path))
                thunk = lookup or first
                while (item := pe.u32(thunk)):
                    symbol = item & 0xffff if item & 0x80000000 else string(pe, item+2)
                    if symbol not in (ordinal if isinstance(symbol,int) else named):
                        raise ValueError(f'Missing import {name} -> {dll}: {symbol!r}')
                    thunk += 4
                if not replacement: dependencies['bin/'+dll] = sha(installed.read_bytes())
            d += 20

    files = []
    for relative, data in payload.items():
        original = GAME / relative
        if original.exists() and original.read_bytes() == data: continue
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(data)
        files.append(dict(relative=relative, original=sha(original.read_bytes()) if original.exists() else None, prepared=sha(data)))
    manifest = dict(game=str(GAME), files=files, dependencies=[dict(relative=k,sha256=v) for k,v in dependencies.items()])
    (stage/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    (stage/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    script = (ROOT/'tools/flight_actions/install.ps1').read_text()
    a=script.index('$allowed = @('); b=script.index('\nforeach ($process',a)
    script=script[:a]+"$allowed = @("+', '.join("'"+f['relative']+"'" for f in files)+")"+script[b:]
    script=script.replace('codex_flight_actions_', 'codex_health_equipment_')
    script=script.replace('Installed flight actions client, action config and four icons', 'Installed Health, global HUD preferences, equipment classes and generator support')
    (stage/'install.ps1').write_text(script)
    print(f'Staged {len(files)} files; {len(report["thrusters"])} thrusters; {len(report["hulls"])} class-limited hulls; {len(report["hardware"])} player cloaks: {stage}')

if __name__ == '__main__': main()
