"""Keep hud_target2's root_second panel, centred in model XY space.

Reads the shared VMS only to measure the panel. Mesh references and shared
geometry are preserved; the output contains no VMeshLibrary or VMeshData.
Writes a separate CMP and validation report, never overwrites the inputs.
"""
import argparse
import hashlib
import json
import struct as S
from pathlib import Path

from generate_station_lods import Node, child, crc, read_tree, write_tree
from repair_panel_normals import leaves


def text(node):
    return node.blob.split(b'\0', 1)[0].decode('ascii')


def walk(node):
    yield node
    for item in node.children:
        yield from walk(item)


def joints(root):
    blob = child(child(child(root, 'Cmpnd'), 'Cons'), 'Fix').blob
    assert len(blob) % 176 == 0
    return [blob[i:i + 176] for i in range(0, len(blob), 176)]


def names(record):
    return tuple(record[i:i + 64].split(b'\0', 1)[0].decode('ascii') for i in (0, 64))


def transform(record, point):
    values = S.unpack_from('<12f', record, 128)
    # This asset has diagonal scale matrices, so row/column convention is immaterial.
    assert all(values[3 + i] == 0 for i in (1, 2, 3, 5, 6, 7))
    return tuple(values[k] + values[3 + 4*k] * point[k] for k in range(3))


def bounds(points):
    return [[min(p[k] for p in points), max(p[k] for p in points)] for k in range(3)]


def panel_points(root, library):
    links = {names(r)[1]: r for r in joints(root)}
    points = []
    materials = set()
    refs = {}
    for part in child(root, 'Cmpnd').children:
        if not part.name.startswith('Part_'):
            continue
        obj = text(child(part, 'Object name'))
        model = child(root, text(child(part, 'File name')))
        for ref in (n for n in walk(model) if n.name == 'VMeshRef'):
            mesh_id, base, count, first_index, _, first_group, groups = S.unpack_from('<I6H', ref.blob, 4)
            blob = library[mesh_id]
            _, primitive, ng, ni, fvf, nv = S.unpack_from('<II4H', blob)
            assert primitive == 4 and fvf == 0x112
            ib = 16 + 12*ng
            vb = ib + 2*ni
            assert len(blob) >= vb + 32*nv
            assert base + count <= nv and first_group + groups <= ng
            cursor = first_index
            for group in range(first_group, first_group + groups):
                material, lo, hi, size, _ = S.unpack_from('<I4H', blob, 16 + 12*group)
                materials.add(material)
                assert size % 3 == 0 and cursor + size <= ni
                for index in S.unpack_from(f'<{size}H', blob, ib + 2*cursor):
                    assert lo <= lo + index <= hi and lo + index < count
                    point = S.unpack_from('<3f', blob, vb + 32*(base + lo + index))
                    current = obj
                    visited = set()
                    while current != 'Root':
                        assert current not in visited
                        visited.add(current)
                        record = links[current]
                        point = transform(record, point)
                        current = names(record)[0]
                    points.append(point)
                cursor += size
            refs[model.name] = ref.blob
    return points, materials, refs


def generate(source, shared, destination):
    assert destination.resolve() not in (source.resolve(), shared.resolve())
    original = source.read_bytes()
    shared_bytes = shared.read_bytes()
    header, roots = read_tree(original)
    root = roots[0]
    _, shared_tree = read_tree(shared_bytes)
    library = {crc(n.name): child(n, 'VMeshData').blob
               for n in child(shared_tree[0], 'VMeshLibrary').children}
    assert not any(n.name in ('VMeshLibrary', 'VMeshData') for n in walk(root))
    compound = child(root, 'Cmpnd')
    keep = {'root_second', 'edgepulse03_lod1', 'windowframe08_lod1', 'scanline04_lod1'}
    parts = [n for n in compound.children if n.name.startswith('Part_')
             and text(child(n, 'Object name')) in keep]
    assert {text(child(n, 'Object name')) for n in parts} == keep
    old_links = joints(root)
    retained_links = [r for r in old_links if names(r)[1] in keep]
    assert len(retained_links) == 4
    assert all(names(r)[0] == ('Root' if names(r)[1] == 'root_second' else 'root_second')
               for r in retained_links)

    root_part = child(compound, 'Root')
    empty_file = 'hud_target2_center_root.3db'
    child(root_part, 'File name').blob = empty_file.encode('ascii') + b'\0'
    child(root_part, 'Index').blob = S.pack('<I', 0)
    for i, part in enumerate(parts, 1):
        child(part, 'Index').blob = S.pack('<I', i)
    cons = child(compound, 'Cons')
    assert [n.name for n in cons.children] == ['Fix']
    compound.children = [root_part, *parts, cons]
    child(cons, 'Fix').blob = b''.join(retained_links)
    files = {text(child(p, 'File name')) for p in parts}
    removed_files = [n.name for n in root.children if n.name.lower().endswith('.3db') and n.name not in files]
    assert len(removed_files) == 6
    root.children = [n for n in root.children if n.name not in removed_files]
    root.children.append(Node(empty_file))

    before, used_materials, original_refs = panel_points(root, library)
    old_bounds = bounds(before)
    shift = [-(a + b)*0.5 for a, b in old_bounds[:2]] + [0.0]
    changed_links = []
    for record in retained_links:
        if names(record)[1] == 'root_second':
            updated = bytearray(record)
            origin = S.unpack_from('<3f', record, 128)
            S.pack_into('<3f', updated, 128, *(origin[k] + shift[k] for k in range(3)))
            record = bytes(updated)
        changed_links.append(record)
    child(cons, 'Fix').blob = b''.join(changed_links)

    # Remove materials/animations used only by the deleted panel; keep shared textures intact.
    materials = child(root, 'Material library')
    retained_materials = [n for n in materials.children if n.children and crc(n.name) in used_materials]
    assert {crc(n.name) for n in retained_materials} == used_materials
    materials.children = [Node('Material count', S.pack('<I', len(retained_materials))), *retained_materials]
    animations = child(root, 'MaterialAnim')
    animations.children = [n for n in animations.children if crc(n.name) in used_materials]

    output = write_tree(header, roots)
    _, parsed = read_tree(output)
    checked = parsed[0]
    after, after_materials, after_refs = panel_points(checked, library)
    assert original_refs == after_refs and used_materials == after_materials
    assert len(before) == len(after) == 180  # all 60 original triangles retained
    assert all(abs(b[k] - (a[k] + shift[k])) < 1e-7
               for a, b in zip(before, after) for k in range(3))
    new_bounds = bounds(after)
    assert all(abs(a + b) < 1e-7 for a, b in new_bounds[:2])
    assert not child(checked, empty_file).children
    assert not any(n.name in ('VMeshLibrary', 'VMeshData') for n in walk(checked))
    assert not any(n.name in removed_files for n in walk(checked))
    # Retained 3db subtrees and texture payloads must remain byte-identical.
    original_leaves = {p: b for p, _, b in leaves(original)[1]}
    for path, _, blob in leaves(output)[1]:
        if any('/' + f + '/' in path for f in files) or '/Texture library/' in path:
            assert original_leaves[path] == blob, path
    for old, new in zip(retained_links, joints(checked)):
        assert old[:128] == new[:128] and old[140:] == new[140:]
        if names(old)[1] != 'root_second':
            assert old == new
    assert source.read_bytes() == original and shared.read_bytes() == shared_bytes
    report = dict(source=str(source), shared_vms=str(shared),
                  source_sha256=hashlib.sha256(original).hexdigest(),
                  shared_vms_sha256=hashlib.sha256(shared_bytes).hexdigest(),
                  output_sha256=hashlib.sha256(output).hexdigest(),
                  removed_parts=removed_files, retained_objects=sorted(keep),
                  empty_root=empty_file, translation=shift, bounds_before=old_bounds,
                  bounds_after=new_bounds, triangles=60, mesh_references_unchanged=True,
                  shared_geometry_embedded=False, size_before=len(original), size_after=len(output))
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(output)
    destination.with_suffix('.report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('shared_vms', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    generate(args.source, args.shared_vms, args.destination)
