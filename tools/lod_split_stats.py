"""How a model's vertices are split: by UV seams, by hard normals, or not at all (diagnostics)."""
import struct as S
import sys
import generate_station_lods as gen
from generate_industrial_lods import geometry
from repair_panel_normals import triangles
from rebuild_uv_safe_lods import source_mesh, DATA

for relative in sys.argv[1:]:
    _, roots = gen.read_tree((DATA / relative).read_bytes())
    h, ds, gs = triangles(geometry(source_mesh(roots[0], 0)[1].blob))
    corners = [(m, v) for (m, _, _), cs in zip(ds, gs) for v in cs]
    full = {(m, v) for m, v in corners}
    pos_uv = {(m, v[:12], v[24:32]) for m, v in corners}
    pos = {(m, v[:12]) for m, v in corners}
    tris = len(corners) // 3
    print(f'{relative.split("/")[-1]:32s} tris {tris:5d}  vertices {len(full):5d}  '
          f'welded by position+UV {len(pos_uv):5d}  by position {len(pos):5d}')
