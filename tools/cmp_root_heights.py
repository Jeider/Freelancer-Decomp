"""Heights of the .cmp Root part's triangles near a box (diagnostics).
usage: cmp_root_heights.py <file> xmin xmax zmin zmax"""
import struct as S
import sys
from pathlib import Path
import generate_station_lods as gen

data = Path(sys.argv[1]).read_bytes()
xmin, xmax, zmin, zmax = map(float, sys.argv[2:6])
_, roots = gen.read_tree(data)
root = roots[0]
lib = {gen.crc(n.name): n for n in gen.child(root, 'VMeshLibrary').children}
part = next(n for n in root.children if n.name.lower().startswith('li_elite_lod1'))
level0 = gen.child(gen.child(part, 'MultiLevel'), 'Level' + (sys.argv[6] if len(sys.argv) > 6 else '0'))
ref = gen.child(gen.child(level0, 'VMeshPart'), 'VMeshRef').blob
crc, = S.unpack_from('<I', ref, 4)
start_v, nv, start_i, ni, start_g, ng = S.unpack_from('<6H', ref, 8)
blob = gen.child(lib[crc], 'VMeshData').blob
_, _, groups, indices, fvf, vertices = S.unpack_from('<II4H', blob)
desc = [S.unpack_from('<I4H', blob, 16 + 12 * g) for g in range(groups)]
ib = 16 + 12 * groups
vb = ib + 2 * indices
rows = []
offset = start_i
for g in range(start_g, start_g + ng):
    material, gv0, _, count, _ = desc[g]
    for t in range(0, count, 3):
        tri = []
        for k in range(3):
            idx, = S.unpack_from('<H', blob, ib + 2 * (offset + t + k))
            v = start_v + gv0 + idx
            tri.append((S.unpack_from('<3f', blob, vb + 32 * v), S.unpack_from('<3f', blob, vb + 32 * v + 12)))
        c = [sum(p[0][i] for p in tri) / 3 for i in range(3)]
        if xmin <= c[0] <= xmax and zmin <= c[2] <= zmax:
            ys = [p[0][1] for p in tri]
            n = tri[0][1]
            rows.append((round(c[0], 2), round(c[2], 2), round(min(ys), 3), round(max(ys), 3),
                         [round(x, 2) for x in n], hex(material)))
    offset += count
rows.sort(key=lambda r: -r[3])
for r in rows[:40]:
    print('centre x %6.2f z %6.2f  y %6.3f..%6.3f  normal %s  %s' % r)
print(len(rows), 'triangles in the box')
