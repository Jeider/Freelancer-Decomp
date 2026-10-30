"""Make an independently editable Cloak icon from the Health button (no atlas)."""
from pathlib import Path
import argparse
import json
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from generate_station_lods import child, read_tree
from make_targeting_icons import generate, geometry, mesh_library


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game', type=Path, default=Path('D:/games/FL_MOD'))
    parser.add_argument('--texture', type=Path, help='Replacement 32-bit TGA with alpha')
    args = parser.parse_args()
    source = args.game / 'DATA/INTERFACE/HUD/HUD_targetedobject.3db'
    shared = mesh_library(read_tree((args.game / 'DATA/INTERFACE/interface.generic.vms').read_bytes())[1][0])
    data, texture, report = generate(source, shared, 'HUD_health_cloak', args.texture)

    # Reject any future source that switches to a tile of a texture atlas.
    root = read_tree(data)[1][0]
    ref = child(child(root, 'VMeshPart'), 'VMeshRef').blob
    _, _, vertices = geometry(next(iter(mesh_library(root).values())), ref)
    uv = [v[3:] for v in struct.iter_unpack('<5f', vertices)]
    assert all(min(v[axis] for v in uv) < 0.01 and max(v[axis] for v in uv) > 0.99
               for axis in (0, 1)), 'Cloak needs a full-texture quad, not an atlas tile'

    out = ROOT / 'assets/hud/extra'
    out.mkdir(parents=True, exist_ok=True)
    # Keep the installed client's path; all embedded resources use new names.
    (out / 'HUD_DefCloak.3db').write_bytes(data)
    (out / report['texture']).write_bytes(texture)
    report['file'] = 'HUD_DefCloak.3db'
    report['note'] = 'Standalone Health button copy; unique mesh/material/texture; one full-icon MIP0, no atlas.'
    (out / 'health_sources.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print('PASS: standalone Cloak; full-texture UVs, geometry, material references and texture verified')
    print('Edit Texture library / ' + report['texture'] + ' / MIP0 in ' + str(out / report['file']))


if __name__ == '__main__':
    main()
