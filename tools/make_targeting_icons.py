"""Make standalone HUD_target_view1..4 icons, without modifying shared libraries.

Extract only the referenced icon quad from a legacy shared VMS, or reuse an
already embedded mesh. Preserve the source texture, UVs, bounds and material
settings; assign unique names and CRCs to each icon's mesh/material/texture.
Outputs go to a separate directory. Optional --texture-dir supplies replacement
HUD_target_viewN_icon.tga files (32-bit TGA with alpha).
"""
import argparse
import copy
import hashlib
import json
import struct as S
from pathlib import Path

from generate_station_lods import Node, child, crc, read_tree, write_tree


def branch(name, children):
    node = Node(name)
    node.children = children
    return node


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def name_text(node):
    return node.blob.split(b'\0', 1)[0].decode('ascii')


def mesh_library(root):
    library = next((n for n in root.children if n.name.lower() == 'vmeshlibrary'), None)
    return {} if library is None else {
        crc(n.name): child(n, 'VMeshData').blob for n in library.children
    }


def geometry(blob, ref):
    _, _, base, count, first_index, index_count, first_group, group_count = S.unpack_from('<II6H', ref)
    flags, primitive, groups, indices, fvf, vertices = S.unpack_from('<II4H', blob)
    # These HUD icons are textured double-sided quads, XYZ/UV without normals.
    assert flags == 1 and primitive == 4 and fvf == 0x102
    assert group_count == 1 and (count, index_count) in ((4, 6), (8, 12))
    assert base + count <= vertices and first_group < groups and first_index + index_count <= indices
    assert len(blob) == 16 + 12 * groups + 2 * indices + 20 * vertices
    group = S.unpack_from('<I4H', blob, 16 + first_group * 12)
    assert group[1:4] == (0, count - 1, index_count)
    ib = 16 + 12 * groups
    vb = ib + 2 * indices
    index_bytes = blob[ib + 2 * first_index:ib + 2 * (first_index + index_count)]
    vertex_bytes = blob[vb + 20 * base:vb + 20 * (base + count)]
    assert all(i < count for i in S.unpack(f'<{index_count}H', index_bytes))
    return group, index_bytes, vertex_bytes


def validate(data, stem, expected_indices, expected_vertices, expected_texture):
    _, roots = read_tree(data)
    root = roots[0]
    mesh_name = stem + '_icon.lod0.vms'
    material_name = 'UI_' + stem + '_icon_mat'
    texture_name = stem + '_icon.tga'
    local = mesh_library(root)
    assert list(local) == [crc(mesh_name)]
    ref = child(child(root, 'VMeshPart'), 'VMeshRef').blob
    vertices_count, indices_count = len(expected_vertices) // 20, len(expected_indices) // 2
    assert S.unpack_from('<II6H', ref) == (60, crc(mesh_name), 0, vertices_count, 0, indices_count, 0, 1)
    group, indices, vertices = geometry(local[crc(mesh_name)], ref)
    assert group[0] == crc(material_name)
    assert indices == expected_indices and vertices == expected_vertices
    wire = child(child(root, 'VMeshWire'), 'VWireData').blob
    edge_indices = (len(wire) - 16) // 2
    assert S.unpack_from('<II4H', wire) == (16, crc(mesh_name), 0, vertices_count, edge_indices, vertices_count)
    assert all(i < vertices_count for i in S.unpack_from(f'<{edge_indices}H', wire, 16))
    materials = child(root, 'Material library')
    assert len(materials.children) == 2
    assert child(materials, 'Material count').blob == S.pack('<I', 1)
    material = child(materials, material_name)
    assert name_text(child(material, 'Dt_name')) == texture_name
    textures = child(root, 'Texture library')
    assert len(textures.children) == 1
    assert child(child(textures, texture_name), 'MIP0').blob == expected_texture
    return {'mesh': mesh_name, 'mesh_crc': f'{crc(mesh_name):08x}',
            'material': material_name, 'material_crc': f'{crc(material_name):08x}',
            'texture': texture_name, 'texture_crc': f'{crc(texture_name):08x}',
            'vertices': vertices_count, 'triangles': indices_count // 3, 'sha256': digest(data)}


def generate(source, shared, stem, texture_path=None):
    source_bytes = source.read_bytes()
    header, roots = read_tree(source_bytes)
    root = roots[0]
    ref_node = child(child(root, 'VMeshPart'), 'VMeshRef')
    ref = ref_node.blob
    mesh_id = S.unpack_from('<I', ref, 4)[0]
    local = mesh_library(root)
    blob = local.get(mesh_id)
    if blob is None:
        blob = shared[mesh_id]
    group, indices, vertices = geometry(blob, ref)
    materials = child(root, 'Material library')
    material = copy.deepcopy(next(n for n in materials.children if n.children and crc(n.name) == group[0]))
    texture = copy.deepcopy(child(child(root, 'Texture library'), name_text(child(material, 'Dt_name'))))
    assert [n.name for n in texture.children] == ['MIP0']
    texture_bytes = texture.children[0].blob
    if texture_path is not None:
        texture_bytes = texture_path.read_bytes()
        assert len(texture_bytes) >= 18
        _, cmap, kind, _, _, _, _, _, width, height, bpp, _ = S.unpack_from('<BBBHHBHHHHBB', texture_bytes)
        assert cmap == 0 and kind in (2, 10) and bpp == 32 and width > 0 and height > 0
    texture.children[0].blob = texture_bytes

    # dacom.ini maps ^ui_.* to HUDIconMaterial, which consumes the button's
    # instance tint. Keep this prefix even though each material is unique.
    mesh_name, material_name, texture_name = stem + '_icon.lod0.vms', 'UI_' + stem + '_icon_mat', stem + '_icon.tga'
    material.name = material_name
    child(material, 'Dt_name').blob = texture_name.encode('ascii') + b'\0'
    texture.name = texture_name
    materials.children = [Node('Material count', S.pack('<I', 1)), material]
    child(root, 'Texture library').children = [texture]
    vertices_count, indices_count = len(vertices) // 20, len(indices) // 2
    standalone_mesh = S.pack('<II4H', 1, 4, 1, indices_count, 0x102, vertices_count)
    standalone_mesh += S.pack('<I4H', crc(material_name), 0, vertices_count - 1, indices_count, group[4]) + indices + vertices
    root.children = [n for n in root.children if n.name.lower() != 'vmeshlibrary']
    root.children.insert(1, branch('VMeshLibrary', [branch(mesh_name, [Node('VMeshData', standalone_mesh)])]))
    ref_node.blob = S.pack('<II6H', 60, crc(mesh_name), 0, vertices_count, 0, indices_count, 0, 1) + ref[20:]
    wire_node = child(child(root, 'VMeshWire'), 'VWireData')
    wire = bytearray(wire_node.blob)
    assert S.unpack_from('<I', wire, 4)[0] == mesh_id
    assert S.unpack_from('<H', wire, 8)[0] == S.unpack_from('<H', ref, 8)[0]
    S.pack_into('<I', wire, 4, crc(mesh_name))
    S.pack_into('<H', wire, 8, 0)
    wire_node.blob = bytes(wire)
    output = write_tree(header, roots)
    report = validate(output, stem, indices, vertices, texture_bytes)
    report.update(source=str(source), source_sha256=digest(source_bytes),
                  texture_sha256=digest(texture_bytes), embedded_mesh_bytes=len(standalone_mesh))
    return output, texture_bytes, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, required=True)
    parser.add_argument('--shared-vms', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--texture-dir', type=Path)
    args = parser.parse_args()
    assert args.source_dir.resolve() != (args.out / 'DATA/INTERFACE/HUD').resolve(), 'Output must be separate'
    shared_bytes = args.shared_vms.read_bytes()
    shared = mesh_library(read_tree(shared_bytes)[1][0])
    fallback = args.source_dir / 'HUD_target_view1.3db'
    assert fallback.exists()
    report = {'shared_vms': str(args.shared_vms), 'shared_sha256': digest(shared_bytes), 'icons': []}
    for number in range(1, 5):
        stem = f'HUD_target_view{number}'
        source = args.source_dir / (stem + '.3db')
        if not source.exists():
            source = fallback
        replacement = args.texture_dir / (stem + '_icon.tga') if args.texture_dir else None
        data, texture, info = generate(source, shared, stem, replacement)
        destination = args.out / 'DATA/INTERFACE/HUD' / (stem + '.3db')
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(data)
        textures = args.out / 'textures'
        textures.mkdir(parents=True, exist_ok=True)
        (textures / (stem + '_icon.tga')).write_bytes(texture)
        info['file'] = str(destination)
        report['icons'].append(info)
    for key in ('mesh_crc', 'material_crc', 'texture_crc'):
        assert len({i[key] for i in report['icons']}) == 4
    assert not ({int(i['mesh_crc'], 16) for i in report['icons']} & set(shared))
    assert args.shared_vms.read_bytes() == shared_bytes
    (args.out / 'report.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('Validated 4 standalone icons: unique meshes/materials/textures; original quad/UVs retained.')
    print('Shared VMS unchanged. Replace each Texture library / *_icon.tga / MIP0 to change its image.')


if __name__ == '__main__':
    main()
