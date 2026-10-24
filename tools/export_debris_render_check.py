"""Export existing FL_MOD debris assets into ignored src/obj for the D3D9 check."""
import argparse
import math
import struct
from pathlib import Path
from repair_panel_normals import leaves, triangles
from generate_station_lods import crc

parser = argparse.ArgumentParser()
parser.add_argument('game_root', type=Path)
args = parser.parse_args()
root = args.game_root / 'DATA/SOLAR/ASTEROIDS_MOD/DEBRIS'
out = Path(__file__).resolve().parents[1] / 'src/obj'
out.mkdir(parents=True, exist_ok=True)
material_nodes = leaves((root / 'dyn_debris.mat').read_bytes())[1]
textures = {crc(n.split('/')[-2]): b.rstrip(b'\0').decode('ascii')
            for n, _, b in material_nodes if n.endswith('/Dt_name')}
for i in range(1, 5):
    nodes = leaves((root / f'dyn_debris_{i}.3db').read_bytes())[1]
    blob = next(b for n, _, b in nodes if n.lower().endswith('/vmeshdata'))
    _, descriptors, groups = triangles(blob)
    assert len(groups) == 1, 'Check expects one material, as the dynamic renderer does'
    verts = [list(struct.unpack('<8f', v)) for v in groups[0]]
    centre = [(min(v[k] for v in verts) + max(v[k] for v in verts)) / 2 for k in range(3)]
    radius = max(math.dist(v[:3], centre) for v in verts)
    for v in verts:
        v[:3] = [(v[k] - centre[k]) / radius for k in range(3)]
    (out / f'br_cam_mesh_{i}.bin').write_bytes(struct.pack('<I', len(verts)) +
        b''.join(struct.pack('<8f', *v) for v in verts))
    name = textures[descriptors[0][0]]
    texture = next(b for n, _, b in material_nodes if n.endswith('/' + name + '/MIPS') or
                   n.endswith('/' + name + '/MIP2'))
    (out / f'br_cam_mesh_{i}.texture').write_bytes(texture)
    print(f'Model {i}: {len(verts)//3} triangles, radius {radius:.1f}, texture {name}')
