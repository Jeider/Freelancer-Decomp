"""Stage matched sensor/tractor binaries; verify new and installed DLL consumers."""
from pathlib import Path
import datetime
import json
import shutil
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
BIN = ROOT / 'src/obj/health_equipment/bin'
sys.path.insert(0, str(ROOT / 'tools/flight_actions'))
from prepare_install import PE, directory, exports, string, digest


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
            if not dll_name: break
            dll = string(pe, dll_name).decode('ascii')
            installed = GAME/'bin'/dll
            replacement = replacements.get(dll.lower())
            # Existing consumers only need verification against replaced libraries.
            if (name in replacements or replacement) and (installed.exists() or replacement):
                provider = replacement or installed
                if provider not in cache: cache[provider] = exports(PE(provider))
                named, ordinal = cache[provider]
                thunk = lookup or first
                while (item := pe.u32(thunk)):
                    symbol = item & 0xffff if item & 0x80000000 else string(pe, item+2)
                    if symbol not in (ordinal if isinstance(symbol, int) else named):
                        raise ValueError(f'Missing import {name} -> {dll}: {symbol!r}')
                    thunk += 4
                    checked += 1
                if not replacement: dependencies['bin/'+dll] = digest(installed)
                if name not in replacements: dependencies['bin/'+path.name] = digest(path)
            d += 20
    stage = ROOT/'src/obj/sensor_detection_install'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    files = []
    for name in ('Common.dll','Common.pdb','Server.dll','Server.pdb','freelancer.exe','freelancer.pdb'):
        relative = 'bin/'+name
        target = stage/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(BIN/name, target)
        original = GAME/relative
        files.append(dict(relative=relative, original=digest(original) if original.exists() else None,
                          prepared=digest(target)))
    manifest = dict(game=str(GAME), files=files,
                    dependencies=[dict(relative=k,sha256=v) for k,v in dependencies.items()])
    (stage/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    script = (ROOT/'tools/flight_actions/install.ps1').read_text()
    a = script.index('$allowed = @(')
    b = script.index('\nforeach ($process', a)
    script = script[:a] + '$allowed = @(' + ', '.join("'"+f['relative']+"'" for f in files) + ')' + script[b:]
    script = script.replace('codex_flight_actions_', 'codex_sensor_detection_').replace(
        'Installed flight actions client, action config and four icons',
        'Installed scanner discovery, valuable contents detection and tractor-range Loot All')
    (stage/'install.ps1').write_text(script)
    print(f'PASS: {checked} imports verified, including existing consumers of Common/Server')
    print(stage/'install.ps1')


if __name__ == '__main__':
    main()
