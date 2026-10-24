"""Audit and export the ordinary fields' own dynamic models for the D3D9 render check."""
import argparse
import json
import math
import re
import struct
from pathlib import Path
from repair_panel_normals import leaves, triangles
from generate_station_lods import crc
from install_asteroid_mesh_fields import field_candidates, sections, values

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('game_root', type=Path)
    args = parser.parse_args()
    game = args.game_root.resolve()
    root = game / 'DATA'
    out = Path(__file__).resolve().parents[1] / 'src/obj/asteroid_mesh_check'
    out.mkdir(parents=True, exist_ok=True)
    wanted = sorted({m.lower() for _, _, _, models in field_candidates(game) for m in models})
    text = (root / 'SOLAR/dasteroidarch.ini').read_bytes().decode('latin1')
    arch = {}
    for name, _, end, stop in sections(text):
        if name == 'dynamicasteroid':
            record = values(text[end:stop])
            record['libraries'] = re.findall(r'^material_library\s*=\s*([^;\r\n]+)', text[end:stop], re.M | re.I)
            arch[record['nickname'].lower()] = record
    cache = {}
    def nodes(path):
        if path not in cache:
            cache[path] = leaves(path.read_bytes())[1]
        return cache[path]
    report = []
    for name in wanted:
        record = arch[name]
        model = root / record['da_archetype']
        mesh_nodes = nodes(model)
        blobs = [b for n, _, b in mesh_nodes if n.lower().endswith('/vmeshdata')]
        if len(blobs) != 1:
            raise ValueError(f'Expected single-mesh dynamic model: {model}')
        _, descriptors, groups = triangles(blobs[0])
        if len(groups) != 1:
            raise ValueError(f'Expected single-material dynamic model: {model}')
        library = [node for path in record['libraries'] for node in nodes(root / path.strip())]
        texture_names = {crc(n.split('/')[-2]): b.rstrip(b'\0').decode('ascii')
                         for n, _, b in library if n.lower().endswith('/dt_name')}
        texture_name = texture_names[descriptors[0][0]]
        texture = next(b for n, _, b in library + mesh_nodes if
                       n.lower().endswith('/' + texture_name.lower() + '/mips') or
                       n.lower().endswith('/' + texture_name.lower() + '/mip0'))
        verts = [list(struct.unpack('<8f', v)) for v in groups[0]]
        centre = [(min(v[k] for v in verts) + max(v[k] for v in verts)) / 2 for k in range(3)]
        radius = max(math.dist(v[:3], centre) for v in verts)
        for v in verts:
            v[:3] = [(v[k] - centre[k]) / radius for k in range(3)]
        mesh_file, texture_file = out / (name + '.bin'), out / (name + '.texture')
        mesh_file.write_bytes(struct.pack('<I', len(verts)) + b''.join(struct.pack('<8f', *v) for v in verts))
        texture_file.write_bytes(texture)
        report.append(dict(name=name, triangles=len(verts)//3, radius=radius, texture_name=texture_name,
                           mesh=str(mesh_file), texture=str(texture_file)))
        print(f'{name}: {len(verts)//3} triangles, source radius {radius:.1f}, {texture_name}')
    (out / 'models.json').write_text(json.dumps(report, indent=2), encoding='utf8')

if __name__ == '__main__':
    main()
