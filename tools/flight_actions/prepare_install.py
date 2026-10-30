"""Prepare a fixed, hash-verified FL_MOD installation; never modify the game."""
import datetime
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
sys.path.insert(0, str(ROOT / 'tools/beta_evade_patch'))
from verify import PE

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()

def flight_config(data):
    """Add missing action defaults; preserve every existing setting and byte."""
    defaults = [(b'reverse_strafe_interval', b'2.0'),
                (b'goto_weave_interval', b'2.0'), (b'goto_weave_angle', b'25.0')]
    data = add_defaults(data, b'FlightActions', defaults)
    return add_defaults(data, b'Navigation', [(b'autopilot', b'1'), (b'route_generator', b'beta'),
                                             (b'clearance', b'300'), (b'dock_distance', b'2000')])

def add_defaults(data, name, defaults):
    newline = b'\r\n' if b'\r\n' in data else b'\n'
    section = re.search(rb'(?im)^[ \t]*\['+name+rb'\][ \t]*(?:;[^\r\n]*)?\r?$', data)
    if not section:
        setting = b''.join(key+b' = '+value+newline for key, value in defaults)
        return data + (b'' if data.endswith(newline) else newline) + newline + b'['+name+b']' + newline + setting
    next_section = re.search(rb'(?m)^[ \t]*\[', data[section.end():])
    end = section.end()+next_section.start() if next_section else len(data)
    setting = b''.join(key+b' = '+value+newline for key, value in defaults
                      if not re.search(rb'(?im)^[ \t]*'+key+rb'[ \t]*=', data[section.end():end]))
    if not setting:
        return data
    prefix = data[:end]
    return prefix + (b'' if prefix.endswith(newline) else newline) + setting + data[end:]

def string(pe, rva):
    result = bytearray()
    while (b := pe.read(rva, 1)) != b'\0':
        result += b
        rva += 1
    return bytes(result)

def directory(pe, index):
    optional = struct.unpack_from('<I', pe.data, 0x3c)[0] + 24
    return struct.unpack_from('<I', pe.data, optional + 96 + index * 8)[0]

def exports(pe):
    d = directory(pe, 0)
    if not d: return set(), set()
    base, count, names, functions, strings, ordinals = struct.unpack('<6I', pe.read(d+16, 24))
    named = {string(pe, pe.u32(strings+4*i)) for i in range(names)}
    ordinal = {base+i for i in range(count) if pe.u32(functions+4*i)}
    return named, ordinal

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--client-bin', type=Path, default=ROOT / 'bin')
    args = parser.parse_args()
    exe = args.client_bin / 'freelancer.exe'
    pe = PE(exe)
    if b'FlightAction%d' not in pe.data:
        raise RuntimeError('Client was not built with flight actions enabled')
    dependencies = []
    d = directory(pe, 1)
    while d:
        lookup, _, _, name, first = struct.unpack('<5I', pe.read(d, 20))
        if not name: break
        dll = string(pe, name).decode('ascii')
        installed = GAME / 'bin' / dll
        if installed.exists():
            named, ordinal = exports(PE(installed))
            thunk = lookup or first
            while (item := pe.u32(thunk)):
                symbol = (item & 0xffff) if item & 0x80000000 else string(pe, item+2)
                if symbol not in (ordinal if isinstance(symbol, int) else named):
                    raise RuntimeError(f'Missing installed import: {dll}: {symbol!r}')
                thunk += 4
            dependencies.append(dict(relative=f'bin/{dll}', sha256=digest(installed)))
        elif (ROOT / 'bin' / dll).exists():
            raise RuntimeError(f'Missing installed DLL: {dll}')
        d += 20
    stage = ROOT / 'src/obj/flight_actions_install' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    names = ['bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/port.ini'] + [
        f'DATA/INTERFACE/HUD/EXTRA/{f}' for f in
        ['HUD_drasticevade.3db', 'HUD_turntoface.3db', 'hud_mnvrstrafe.3db', 'hud_mnvrevade.3db']]
    files = []
    for name in names:
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        original = GAME / name
        if name == 'bin/port.ini':
            target.write_bytes(flight_config(original.read_bytes()))
        else:
            source = args.client_bin / Path(name).name if name.startswith('bin/') else ROOT / 'assets/hud/extra' / Path(name).name
            shutil.copyfile(source, target)
        files.append(dict(relative=name, original=digest(original) if original.exists() else None,
                          prepared=digest(target)))
    (stage / 'manifest.json').write_text(json.dumps(dict(game=str(GAME), files=files,
                                                        dependencies=dependencies), indent=2)+'\n')
    shutil.copyfile(Path(__file__).with_name('install.ps1'), stage / 'install.ps1')
    print(f'Imports verified against {len(dependencies)} installed DLLs. Staged {len(files)} files: {stage}')

if __name__ == '__main__': main()
