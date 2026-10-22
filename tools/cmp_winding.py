"""Compare triangle winding with stored normals for .cmp parts (diagnostics): for each
triangle, the sign of dot(cross(v1-v0, v2-v0), stored normal). Parts drawn with one winding
convention should all agree.
usage: cmp_winding.py <file> <part substring> [<part substring> ...]"""
import struct as S
import sys
from pathlib import Path
import generate_station_lods as gen

data = Path(sys.argv[1]).read_bytes()
_, roots = gen.read_tree(data)
root = roots[0]
lib = {gen.crc(n.name): n for n in gen.child(root, 'VMeshLibrary').children}
for want in sys.argv[2:]:
    part = next(n for n in root.children if want.lower() in n.name.lower())
    level0 = gen.child(gen.child(part, 'MultiLevel'), 'Level0')
    ref = gen.child(gen.child(level0, 'VMeshPart'), 'VMeshRef').blob
    crc, = S.unpack_from('<I', ref, 4)
    start_v, nv, start_i, ni, start_g, ng = S.unpack_from('<6H', ref, 8)
    blob = gen.child(lib[crc], 'VMeshData').blob
    _, _, groups, indices, fvf, vertices = S.unpack_from('<II4H', blob)
    desc = [S.unpack_from('<I4H', blob, 16 + 12 * g) for g in range(groups)]
    ib = 16 + 12 * groups
    vb = ib + 2 * indices
    agree = disagree = 0
    offset = start_i
    for g in range(start_g, start_g + ng):
        material, gv0, _, count, _ = desc[g]
        a = d = 0
        for t in range(0, count, 3):
            ps, ns = [], []
            for k in range(3):
                idx, = S.unpack_from('<H', blob, ib + 2 * (offset + t + k))
                v = start_v + gv0 + idx
                ps.append(S.unpack_from('<3f', blob, vb + 32 * v))
                ns.append(S.unpack_from('<3f', blob, vb + 32 * v + 12))
            e1 = [ps[1][i] - ps[0][i] for i in range(3)]
            e2 = [ps[2][i] - ps[0][i] for i in range(3)]
            c = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
            n = [sum(x[i] for x in ns) for i in range(3)]
            dot = sum(c[i] * n[i] for i in range(3))
            if dot > 0: a += 1
            elif dot < 0: d += 1
        print(f'{part.name} group {g} material {hex(material)}: cross along normal {a}, against normal {d}')
        agree += a
        disagree += d
        offset += count
    print(f'== {part.name}: along {agree}, against {disagree}')
