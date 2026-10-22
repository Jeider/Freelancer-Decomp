"""Geometry, materials and joint data of selected .cmp parts (diagnostics)."""
import struct as S
import sys
from pathlib import Path
import generate_station_lods as gen
from generate_industrial_lods import geometry
from repair_panel_normals import triangles

data = Path(sys.argv[1]).read_bytes()
names = [n.lower() for n in sys.argv[2:]]
_, roots = gen.read_tree(data)
root = roots[0]
lib = {gen.crc(n.name): n for n in gen.child(root, 'VMeshLibrary').children}


def dump(node, depth=0):
    blob = '' if node.blob is None else f' [{len(node.blob)}] ' + node.blob[:96].hex()
    print('  ' * depth + node.name + blob)
    for c in node.children:
        dump(c, depth + 1)


# Joints that mention the parts.
cons = next(c for c in gen.child(root, 'Cmpnd').children if c.name.lower() == 'cons')
for kind in cons.children:
    blob = kind.blob or b''
    size = {'fix': 176, 'rev': 208, 'pris': 208, 'sphere': 212, 'loose': 176}.get(kind.name.lower(), 0)
    if not size:
        continue
    for i in range(0, len(blob) - size + 1, size):
        parent = blob[i:i + 64].split(b'\0')[0].decode()
        child = blob[i + 64:i + 128].split(b'\0')[0].decode()
        if any(n in child.lower() for n in names):
            origin = S.unpack_from('<3f', blob, i + 128)
            offset = S.unpack_from('<3f', blob, i + 140)
            rot = S.unpack_from('<9f', blob, i + 152)
            extra = S.unpack_from('<5f', blob, i + 188) if size >= 208 else ()
            print(kind.name, parent, '->', child, 'origin', [round(x, 3) for x in origin],
                  'offset', [round(x, 3) for x in offset], 'rot', [round(x, 3) for x in rot],
                  'axis/min/max', [round(x, 3) for x in extra])
for top in root.children:
    if any(n in top.name.lower() for n in names):
        print('==', top.name)
        for n in top.children:
            if n.name.lower() == 'multilevel':
                for lvl in n.children:
                    if lvl.name.lower().startswith('level'):
                        ref = gen.child(gen.child(lvl, 'VMeshPart'), 'VMeshRef').blob
                        crc, = S.unpack_from('<I', ref, 4)
                        start_v, nv, start_i, ni, start_g, ng = S.unpack_from('<6H', ref, 8)
                        bbox = S.unpack_from('<6f', ref, 20)
                        mesh = lib.get(crc)
                        print(' ', lvl.name, mesh.name if mesh else '?', 'verts', start_v, nv, 'idx', start_i, ni,
                              'groups', start_g, ng, 'bbox', [round(x, 3) for x in bbox])
                        if mesh is not None:
                            h, ds, gs = triangles(geometry(gen.child(mesh, 'VMeshData').blob))
                            for g in range(start_g, start_g + ng):
                                m, size, _ = ds[g]
                                print('    group', g, 'material', hex(m), 'triangles', size // 3)
