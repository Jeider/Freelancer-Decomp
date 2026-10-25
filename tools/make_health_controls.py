"""Create native play/pause/lock mesh glyphs with independent UI materials.

The HUD sets their displayed size; no shared library or projection art is edited.
"""
import json
import math
import struct as S
from pathlib import Path
from generate_station_lods import child, crc, read_tree, write_tree
from make_targeting_icons import generate

repo = Path(__file__).resolve().parents[1]
source = Path('D:/games/FL_MOD/DATA/INTERFACE/HUD/HUD_health.3db')
out = repo / 'src/obj/health_controls/icons'
out.mkdir(parents=True, exist_ok=True)

def rect(x0, y0, x1, y1):
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

play = [[(-.009, -.013), (.013, 0), (-.009, .013)]]
pause = [rect(-.011, -.013, -.004, .013), rect(.004, -.013, .011, .013)]
lock = [rect(-.011, -.013, -.008, .002), rect(.008, -.013, .011, .002),
        rect(-.011, -.013, .011, -.010), rect(-.011, 0, .011, .003),
        rect(-.007, .002, -.004, .006), rect(.004, .002, .007, .006),
        rect(-.0015, -.004, .0015, -.001), rect(-.0008, -.007, .0008, -.004)]
for i in range(12):
    a, b = math.pi * i / 12, math.pi * (i+1) / 12
    lock.append([(r * math.cos(angle), .006 + r * math.sin(angle))
                 for r, angle in ((.007,a),(.007,b),(.004,b),(.004,a))])

reports = []
for stem, polygons in [('HUD_health_wing', play), ('HUD_health_pause', pause), ('HUD_health_wing_lock', lock)]:
    data, _, _ = generate(source, {}, stem)
    header, roots = read_tree(data)
    root = roots[0]
    vertices, indices, edges = [], [], []
    for polygon in polygons:
        base = len(vertices)
        vertices.extend((x, y, 0., .5, .5) for x, y in polygon)
        for i in range(1, len(polygon)-1):
            indices.extend((base, base+i, base+i+1))
            indices.extend((base, base+i+1, base+i))
        for i in range(len(polygon)):
            edges.extend((base+i, base+(i+1)%len(polygon)))
    mesh_name, material_name, texture_name = stem+'_icon.lod0.vms', 'UI_'+stem+'_icon_mat', stem+'_icon.tga'
    mesh = S.pack('<II4H', 1, 4, 1, len(indices), 0x102, len(vertices))
    mesh += S.pack('<I4H', crc(material_name), 0, len(vertices)-1, len(indices), 0)
    mesh += S.pack(f'<{len(indices)}H', *indices)
    mesh += b''.join(S.pack('<5f', *vertex) for vertex in vertices)
    child(child(child(root, 'VMeshLibrary'), mesh_name), 'VMeshData').blob = mesh
    xs, ys = [v[0] for v in vertices], [v[1] for v in vertices]
    radius = max(math.hypot(x, y) for x, y in zip(xs, ys))
    child(child(root, 'VMeshPart'), 'VMeshRef').blob = S.pack('<II6H10f',
        60, crc(mesh_name), 0, len(vertices), 0, len(indices), 0, 1,
        max(xs), min(xs), max(ys), min(ys), 0, 0, 0, 0, 0, radius)
    child(child(root, 'VMeshWire'), 'VWireData').blob = S.pack('<II4H',
        16, crc(mesh_name), 0, len(vertices), len(edges), len(vertices)) + S.pack(f'<{len(edges)}H', *edges)
    child(child(child(root, 'Texture library'), texture_name), 'MIP0').blob = S.pack(
        '<BBBHHBHHHHBB', 0, 0, 2, 0, 0, 0, 0, 0, 1, 1, 32, 8) + bytes([255]*4)
    result = write_tree(header, roots)
    checked = read_tree(result)[1][0]
    assert child(child(child(checked, 'VMeshLibrary'), mesh_name), 'VMeshData').blob == mesh
    assert max(indices) < len(vertices) and len(indices)%3 == 0
    assert child(child(checked, 'Material library'), material_name).name.startswith('UI_')
    (out / (stem+'.3db')).write_bytes(result)
    reports.append(dict(file=stem+'.3db', mesh=mesh_name, material=material_name, texture=texture_name,
                        vertices=len(vertices), triangles=len(indices)//3))
(out / 'report.json').write_text(json.dumps(reports, indent=2))
print('Validated three native Health glyph assets:', out)
