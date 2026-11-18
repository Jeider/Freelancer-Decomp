"""Recreate a Common import library from the installed DLL, without rebuilding Common."""
from pathlib import Path
import hashlib
import json
import os
import re
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD/bin')
OUT = ROOT/'out/room_materials/runtime/imports'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    versions = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC')
    compiler = sorted(versions.iterdir())[-1]/'bin/Hostx64/x86'
    source = GAME/'Common.dll'
    data = source.read_bytes()
    pe = struct.unpack_from('<I', data, 0x3c)[0]
    sections, optional = struct.unpack_from('<H', data, pe+6)[0], struct.unpack_from('<H', data, pe+20)[0]
    ranges = []
    for index in range(sections):
        offset = pe+24+optional+40*index
        size, rva, raw = struct.unpack_from('<III', data, offset+8)
        flags = struct.unpack_from('<I', data, offset+36)[0]
        ranges.append((rva, rva+max(size, raw), bool(flags & 0x20000000)))
    listing = subprocess.check_output([str(compiler/'dumpbin.exe'), '/exports', str(source)], text=True)
    exports = re.findall(r'^\s+(\d+)\s+[0-9A-F]+\s+([0-9A-F]+)\s+(\S+)', listing, re.M)
    assert len(exports) > 1000
    lines = ['LIBRARY Common.dll', 'EXPORTS']
    for ordinal, rva, name in exports:
        code = next(code for lo, hi, code in ranges if lo <= int(rva, 16) < hi)
        lines.append(f'    {name} @{ordinal}' + ('' if code else ' DATA'))
    definition = OUT/'Common.def'
    definition.write_text('\n'.join(lines)+'\n', encoding='ascii')
    env = dict(os.environ, TEMP=str(OUT), TMP=str(OUT))
    subprocess.run([str(compiler/'lib.exe'), '/nologo', '/machine:x86', '/def:'+str(definition),
                    '/out:'+str(OUT/'Common.lib')], env=env, check=True)
    (OUT/'source.json').write_text(json.dumps(dict(source=str(source),
        sha256=hashlib.sha256(data).hexdigest(), named_exports=len(exports)), indent=2))
    print('Installed Common import library:', len(exports), 'exports')


if __name__ == '__main__':
    main()
