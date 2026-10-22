"""Print the triangles (position, normal, UV) a .cmp part's VMeshRef draws (diagnostics).
usage: cmp_group_vertices.py <file> <part .3db name substring>
Vertex index = VMeshRef start vertex + group start vertex + stored index (FVF 0x112, 32 bytes)."""
import struct as S
import sys
from pathlib import Path
import generate_station_lods as gen

data = Path(sys.argv[1]).read_bytes()
_, roots = gen.read_tree(data)
root = roots[0]
lib = {gen.crc(n.name): n for n in gen.child(root, 'VMeshLibrary').children}
part = next(n for n in root.children if sys.argv[2].lower() in n.name.lower())
level0 = gen.child(gen.child(part, 'MultiLevel'), 'Level0')
ref = gen.child(gen.child(level0, 'VMeshPart'), 'VMeshRef').blob
crc, = S.unpack_from('<I', ref, 4)
start_v, nv, start_i, ni, start_g, ng = S.unpack_from('<6H', ref, 8)
blob = gen.child(lib[crc], 'VMeshData').blob
mesh_type, surface, groups, indices, fvf, vertices = S.unpack_from('<II4H', blob)
assert fvf == 0x112, hex(fvf)
desc = [S.unpack_from('<I4H', blob, 16 + 12 * g) for g in range(groups)]
index_base = 16 + 12 * groups
vertex_base = index_base + 2 * indices
index_offset = sum(d[3] for d in desc[:start_g]) + 0  # indices before this part's first group
index_offset = start_i
for g in range(start_g, start_g + ng):
    material, gv0, gv1, count, _ = desc[g]
    print(part.name, 'group', g, 'material', hex(material), 'indices', count)
    for k in range(count):
        idx, = S.unpack_from('<H', blob, index_base + 2 * (index_offset + k))
        v = start_v + gv0 + idx
        p = S.unpack_from('<3f', blob, vertex_base + 32 * v)
        n = S.unpack_from('<3f', blob, vertex_base + 32 * v + 12)
        uv = S.unpack_from('<2f', blob, vertex_base + 32 * v + 24)
        print(' ', k, 'pos', [round(x, 3) for x in p], 'normal', [round(x, 3) for x in n],
              'uv', [round(x, 3) for x in uv])
    index_offset += count
