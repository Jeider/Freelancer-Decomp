"""List materials in a Freelancer .mat (UTF) with their id (name CRC) and type (diagnostics).
usage: mat_list.py <file.mat> [crc hex ...]"""
import sys
from pathlib import Path
import generate_station_lods as gen

data = Path(sys.argv[1]).read_bytes()
want = {int(x, 16) for x in sys.argv[2:]}
_, roots = gen.read_tree(data)
lib = gen.child(roots[0], 'material library')
for m in lib.children:
    crc = gen.crc(m.name)
    if want and crc not in want:
        continue
    fields = {c.name.lower(): c.blob for c in m.children if c.blob is not None}
    kind = fields.get('type', b'').split(b'\0')[0].decode('ascii', 'replace')
    textures = {k: v.split(b'\0')[0].decode('ascii', 'replace') for k, v in fields.items() if k.endswith('_name')}
    print(hex(crc), m.name, kind, textures)
