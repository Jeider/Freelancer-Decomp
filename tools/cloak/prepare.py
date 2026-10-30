"""Stage matching cloak binaries and the two opt-in player devices."""
from pathlib import Path
import datetime
import json
import re
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
BIN = ROOT / 'src/obj/health_equipment/bin'
sys.path.insert(0, str(ROOT / 'tools/flight_actions'))
from prepare_install import PE, directory, exports, string, digest


def configure(data):
    sections = re.split(br'(?m)(?=^\[)', data)
    found = set()
    for index, section in enumerate(sections):
        if not section.startswith(b'[CloakingDevice]'):
            continue
        name = re.search(br'(?m)^nickname\s*=\s*(\S+)', section)
        if not name or name[1] not in (b'pl_cloak_slow', b'pl_cloak_fast'):
            continue
        if name[1] in found:
            raise ValueError('Duplicate player cloak definition')
        found.add(name[1])
        newline = b'\r\n' if b'\r\n' in section else b'\n'
        extra = b''
        for key, value in ((b'default_state', b'false'), (b'cloak_duration', b'30'),
                           (b'cooldown_time', b'20'), (b'toggle_cooldown', b'0.3')):
            if not re.search(br'(?m)^' + key + br'\s*=', section):
                extra += key + b' = ' + value + newline
        end = section.index(b'\n', name.end()) + 1
        sections[index] = section[:end] + extra + section[end:]
    assert found == {b'pl_cloak_slow', b'pl_cloak_fast'}, found
    return b''.join(sections)


def main():
    replacements = {name.lower(): BIN/name for name in ('Common.dll', 'Server.dll', 'freelancer.exe')}
    consumers = dict(replacements)
    for path in (GAME/'bin').glob('*.dll'):
        if path.name.lower() not in consumers:
            consumers[path.name.lower()] = path
    dependencies, cache = {}, {}
    checked = 0
    for name, path in consumers.items():
        pe = PE(path)
        d = directory(pe, 1)
        while d:
            lookup, _, _, dll_name, first = struct.unpack('<5I', pe.read(d, 20))
            if not dll_name:
                break
            dll = string(pe, dll_name).decode('ascii')
            installed = GAME/'bin'/dll
            replacement = replacements.get(dll.lower())
            if (name in replacements or replacement) and (installed.exists() or replacement):
                provider = replacement or installed
                if provider not in cache:
                    cache[provider] = exports(PE(provider))
                named, ordinal = cache[provider]
                thunk = lookup or first
                while (item := pe.u32(thunk)):
                    symbol = item & 0xffff if item & 0x80000000 else string(pe, item+2)
                    if symbol not in (ordinal if isinstance(symbol, int) else named):
                        raise ValueError(f'Missing import {name} -> {dll}: {symbol!r}')
                    thunk += 4
                    checked += 1
                if not replacement:
                    dependencies['bin/'+dll] = digest(installed)
                if name not in replacements:
                    dependencies['bin/'+path.name] = digest(path)
            d += 20
    stage = ROOT/'src/obj/cloak_install'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    files = []
    for name in ('Common.dll', 'Common.pdb', 'Server.dll', 'Server.pdb', 'freelancer.exe', 'freelancer.pdb'):
        relative = 'bin/'+name
        target = stage/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BIN/name, target)
        original = GAME/relative
        files.append(dict(relative=relative, original=digest(original) if original.exists() else None,
                          prepared=digest(target)))
    relative = 'DATA/EQUIPMENT/weapon_equip.ini'
    original, target = GAME/relative, stage/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(configure(original.read_bytes()))
    assert configure(target.read_bytes()) == target.read_bytes()
    files.append(dict(relative=relative, original=digest(original), prepared=digest(target)))
    manifest = dict(game=str(GAME), files=files,
                    dependencies=[dict(relative=k, sha256=v) for k, v in dependencies.items()])
    (stage/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    script = (ROOT/'tools/flight_actions/install.ps1').read_text()
    a = script.index('$allowed = @(')
    b = script.index('\nforeach ($process', a)
    script = script[:a] + '$allowed = @(' + ', '.join("'"+f['relative']+"'" for f in files) + ')' + script[b:]
    script = script.replace('codex_flight_actions_', 'codex_cloak_').replace(
        'Installed flight actions client, action config and four icons',
        'Installed configurable cloak timers and player cloak definitions')
    (stage/'install.ps1').write_text(script)
    print(f'PASS: {checked} imports verified, including installed consumers of Common/Server')
    print(stage/'install.ps1')


if __name__ == '__main__':
    main()
