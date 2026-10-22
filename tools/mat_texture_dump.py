"""Save a texture from a Freelancer .mat (UTF texture library, TGA or DDS MIP0) as PNG via
D3DX-free decoding of uncompressed TGA; DDS is written raw (diagnostics).
usage: mat_texture_dump.py <file.mat> <texture name> <out path without extension>"""
import struct as S
import sys
from pathlib import Path
import generate_station_lods as gen

data = Path(sys.argv[1]).read_bytes()
_, roots = gen.read_tree(data)
lib = gen.child(roots[0], 'texture library')
tex = next(n for n in lib.children if n.name.lower() == sys.argv[2].lower())
leaves = {c.name.lower(): c.blob for c in tex.children if c.blob is not None}
print('leaves:', {k: len(v) for k, v in leaves.items()})
out = Path(sys.argv[3])
if 'mip0' in leaves:
    blob = leaves['mip0']
    out.with_suffix('.tga').write_bytes(blob)
    idlen, cmap, kind, _, _, _, _, _, w, h, bpp, desc = S.unpack_from('<BBBHHBHHHHBB', blob)
    print('tga type', kind, w, 'x', h, bpp, 'bpp')
elif 'mips' in leaves:
    out.with_suffix('.dds').write_bytes(leaves['mips'])
    print('dds written')
