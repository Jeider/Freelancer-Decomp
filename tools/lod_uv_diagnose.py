"""Break down the UV guard's verdicts for one model's simplified levels (diagnostics only)."""
import collections
import ctypes as C
import struct as S
import sys
from pathlib import Path
import generate_station_lods as gen
from generate_industrial_lods import geometry
from repair_panel_normals import triangles
from lod_uv_guard import UvGuard
from rebuild_uv_safe_lods import source_mesh, DATA


def main(relative, ratio, error):
    data = (DATA / relative).read_bytes()
    _, roots = gen.read_tree(data)
    _, near = source_mesh(roots[0], 0)
    original = geometry(near.blob)
    h, ds, gs = triangles(original)
    guard = UvGuard(ds, gs)
    print(f'{relative}: {h[-1]} vertices, {h[3]//3} triangles, {len(ds)} groups')
    us = [S.unpack_from('<2f', v, 24) for cs in gs for v in cs]
    print('  uv range u %.2f..%.2f v %.2f..%.2f' % (min(u for u, _ in us), max(u for u, _ in us),
                                                     min(v for _, v in us), max(v for _, v in us)))
    dll = C.CDLL(str(Path('bin/lod_meshopt.dll').resolve()))
    dll.simplify_lod.argtypes = [C.POINTER(C.c_uint), C.POINTER(C.c_uint), C.c_size_t, C.POINTER(C.c_float),
                                 C.c_size_t, C.POINTER(C.c_ubyte), C.c_size_t, C.c_float, C.POINTER(C.c_float)]
    dll.simplify_lod.restype = C.c_size_t
    blob, stats = gen.simplify(original, dll, ratio, error, retain_missing_materials=True)
    for row in stats:
        print('  material', row['material'], row['triangles_before'], '->', row['triangles_after'],
              'rejected' if row['uv_rejected'] else '', row['uv_rejected'])


if __name__ == '__main__':
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else .55,
         float(sys.argv[3]) if len(sys.argv) > 3 else .02)
