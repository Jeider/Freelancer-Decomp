"""Independent inventory filter icons; optional Boosters texture replacement."""
from pathlib import Path
import argparse
import json
import math
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
from generate_station_lods import child, read_tree, write_tree
from make_targeting_icons import digest, generate, mesh_library


def machines_icon(source, out, texture_path=None):
    """Adapt the Beta icon's own quad/UVs to the filter row and HUD UI material."""
    original = source.read_bytes()
    header, roots = read_tree(original)
    root = roots[0]
    mesh = child(root, 'VMeshLibrary').children[0]
    blob = child(mesh, 'VMeshData').blob
    flags, primitive, groups, indices, fvf, vertices = struct.unpack_from('<II4H', blob)
    assert (flags, primitive, groups, indices, fvf, vertices) == (1, 4, 1, 6, 0x112, 4)
    points = [struct.unpack_from('<8f', blob, 40 + 32 * i) for i in range(4)]
    center = [(min(p[i] for p in points) + max(p[i] for p in points))/2 for i in range(3)]
    # Inventory uses native size; Health normalizes this asset to its own fixed radius.
    scale = 0.0425 / max(max(p[i] for p in points)-min(p[i] for p in points) for i in (0, 1))
    points = [tuple((p[i]-center[i])*scale for i in range(3)) + p[6:8] for p in points]
    child(mesh, 'VMeshData').blob = (struct.pack('<II4H', flags, primitive, groups, indices, 0x102, vertices)
        + blob[16:40] + b''.join(struct.pack('<5f', *p) for p in points))
    ref = child(child(root, 'VMeshPart'), 'VMeshRef')
    bounds = [v for i in range(3) for v in (max(p[i] for p in points), min(p[i] for p in points))]
    radius = max(math.sqrt(sum(p[i]**2 for i in range(3))) for p in points)
    ref.blob = ref.blob[:20] + struct.pack('<10f', *bounds, 0, 0, 0, radius)
    prepared = out/'machines_ui_source.3db'
    prepared.write_bytes(write_tree(header, roots))
    data, texture, report = generate(prepared, {}, 'inventory_boosters', texture_path)
    report.update(source=str(source), source_sha256=digest(original))
    return data, texture, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--boosters-texture', type=Path)
    parser.add_argument('--keys-texture', type=Path)
    parser.add_argument('--boosters-source', type=Path, default=Path(
        'D:/games/Freelancer Beta/data/Equipment/models/commodities/nn_icons/machines.3db'))
    parser.add_argument('--keys-only', action='store_true', help='Preserve the staged Boosters icon')
    parser.add_argument('--boosters-only', action='store_true', help='Preserve the staged Keys icon')
    args = parser.parse_args()
    game = Path('D:/games/FL_MOD/DATA/INTERFACE')
    out = ROOT/'assets/inventory_categories'
    out.mkdir(parents=True, exist_ok=True)
    assert not (args.keys_only and args.boosters_only)
    stems = ['keys'] if args.keys_only else ['boosters'] if args.boosters_only else ['boosters', 'keys']
    reports = [r for r in json.loads((out/'sources.json').read_text()) if r['file'] not in [s+'.3db' for s in stems]] if len(stems) == 1 else []
    for stem in stems:
        if stem == 'keys':
            shared = mesh_library(read_tree((game/'interface.generic.vms').read_bytes())[1][0])
            data, texture, report = generate(game/'NEURONET/INVENTORY/cargobay.3db',
                                             shared, 'inventory_keys', args.keys_texture)
        else:
            data, texture, report = machines_icon(args.boosters_source, out, args.boosters_texture)
        (out/(stem+'.3db')).write_bytes(data)
        (out/report['texture']).write_bytes(texture)
        report['file'] = stem+'.3db'
        reports.append(report)
    for key in ('mesh_crc', 'material_crc', 'texture_crc'):
        assert len({r[key] for r in reports}) == 2
    (out/'sources.json').write_text(json.dumps(reports, indent=2)+'\n', encoding='utf-8')
    print('PASS: independent Boosters/Keys meshes, materials and textures; original assets unchanged')
    print(out)


if __name__ == '__main__':
    main()
