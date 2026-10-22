"""Repair planar solar-panel normals directly in legacy UTF .3db files.

Writes a new file, never overwrites the input. Splits triangle corners to remove
exported smoothing across hard edges. Supports full-mesh VMeshRefs and XYZ/N/UV
vertices only; refuses wireframes and partial references rather than guessing.
"""
import argparse
import hashlib
import math
import struct
from pathlib import Path


def leaves(data):
    magic, version, tree, _, _, stride, strings, _, _, payload = struct.unpack_from('<10I', data)
    if (magic, version, stride) != (0x20465455, 0x101, 44):
        raise ValueError('Expected legacy UTF 0x101 with 44-byte nodes')
    result = []
    seen = set()

    def visit(offset, parent):
        while True:
            if offset in seen:
                raise ValueError('Cyclic UTF tree')
            seen.add(offset)
            absolute = tree + offset
            sibling, name_offset, flags = struct.unpack_from('<3I', data, absolute)
            begin = strings + name_offset
            name = data[begin:data.index(0, begin)].decode('ascii')
            path = parent + '/' + name
            child = struct.unpack_from('<I', data, absolute + 16)[0]
            if flags & 16:
                if child:
                    visit(child, path)
            else:
                size = struct.unpack_from('<I', data, absolute + 28)[0]
                result.append((path, absolute, data[payload + child:payload + child + size]))
            if not sibling:
                break
            offset = sibling

    visit(0, '')
    return payload, result


def face_normal(vertices):
    p, q, r = [struct.unpack_from('<3f', v) for v in vertices]
    a = [q[i] - p[i] for i in range(3)]
    b = [r[i] - p[i] for i in range(3)]
    n = (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
    length = math.sqrt(sum(v*v for v in n))
    return tuple(v/length for v in n) if length > 1e-10 else None


def triangles(blob):
    flags, primitive, groups, count, fvf, vertices = struct.unpack_from('<II4H', blob)
    if primitive != 4 or fvf != 0x112 or count % 3:
        raise ValueError('Expected triangle-list XYZ/N/UV mesh')
    start = 16 + 12*groups
    vertex_offset = start + 2*count
    if vertex_offset + 32*vertices != len(blob):
        raise ValueError('Unexpected VMeshData size')
    index = start
    output = []
    descriptors = []
    for g in range(groups):
        material, lo, hi, size, unused = struct.unpack_from('<I4H', blob, 16 + 12*g)
        if size % 3:
            raise ValueError('Non-triangular facegroup')
        ids = struct.unpack_from('<' + 'H'*size, blob, index)
        descriptors.append((material, size, unused))
        index += 2*size
        corners = []
        for i in ids:
            v = i + lo if flags & 1 else i
            if v >= vertices:
                raise ValueError('Vertex index out of bounds')
            corners.append(blob[vertex_offset+32*v:vertex_offset+32*(v+1)])
        output.append(corners)
    if index != vertex_offset:
        raise ValueError('Facegroup index counts disagree')
    return (flags, primitive, groups, count, fvf, vertices), descriptors, output


def repair_mesh(blob):
    header, descriptors, groups = triangles(blob)
    flags, primitive, ng, count, fvf, old_vertices = header
    if count > 65535:
        raise ValueError('16-bit vertex limit exceeded')
    result = bytearray(struct.pack('<II4H', flags, primitive, ng, count, fvf, count))
    indices = bytearray()
    vertices = bytearray()
    offset = 0
    for (material, size, unused), corners in zip(descriptors, groups):
        result.extend(struct.pack('<I4H', material, offset, offset+size-1, size, unused))
        indices.extend(struct.pack('<'+'H'*size, *range(size)) if flags & 1 else
                       struct.pack('<'+'H'*size, *range(offset, offset+size)))
        for t in range(0, size, 3):
            face = corners[t:t+3]
            normal = face_normal(face)
            for corner in face:
                vertices.extend(corner[:12])
                vertices.extend(struct.pack('<3f', *normal) if normal else corner[12:24])
                vertices.extend(corner[24:])
        offset += size
    result.extend(indices)
    result.extend(vertices)
    # Compare actual rendered triangle attributes, not just array sizes.
    _, check_descriptors, check_groups = triangles(result)
    assert descriptors == check_descriptors
    for before, after in zip(groups, check_groups):
        for a, b in zip(before, after):
            assert a[:12] == b[:12] and a[24:] == b[24:]
        for t in range(0, len(after), 3):
            expected = face_normal(after[t:t+3])
            if expected:
                for b in after[t:t+3]:
                    n = struct.unpack_from('<3f', b, 12)
                    assert sum(x*y for x,y in zip(n, expected)) > .999999
    return bytes(result), old_vertices, count


def repair(source, destination):
    if source.resolve() == destination.resolve():
        raise ValueError('Use a separate output file')
    original = source.read_bytes()
    payload, nodes = leaves(original)
    if any(path.lower().endswith('/vwiredata') for path, _, _ in nodes):
        raise ValueError('Wireframe requires a separate vertex remap')
    output = bytearray(original)
    changes = []
    mesh_counts = set()
    for path, node, blob in nodes:
        if not path.lower().endswith('/vmeshdata'):
            continue
        fixed, old_count, new_count = repair_mesh(blob)
        changes.append((path, old_count, new_count))
        mesh_counts.add((old_count, new_count))
        output.extend(b'\0' * ((-len(output)) % 4))
        position = len(output) - payload
        output.extend(fixed)
        struct.pack_into('<4I', output, node+16, position, len(fixed), len(fixed), len(fixed))
    if not changes:
        raise ValueError('No mesh found')
    for path, node, blob in nodes:
        if not path.lower().endswith('/vmeshref'):
            continue
        if len(blob) != 60:
            raise ValueError('Unexpected VMeshRef size')
        start, count, index_start, index_count, group_start = struct.unpack_from('<5H', blob, 8)
        candidates = [new for old, new in mesh_counts if old == count and new == index_count]
        if start or index_start or group_start or len(candidates) != 1:
            raise ValueError('Partial or ambiguous mesh reference')
        position = payload + struct.unpack_from('<I', original, node+16)[0]
        struct.pack_into('<H', output, position+10, candidates[0])
    _, verified_nodes = leaves(output)
    for (path, _, before), (check_path, _, after) in zip(nodes, verified_nodes):
        assert path == check_path
        if path.lower().endswith('/vmeshref'):
            assert before[:10] == after[:10] and before[12:] == after[12:]
        elif not path.lower().endswith('/vmeshdata'):
            assert before == after, path
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(output)
    print(source.name, changes)
    print('Source SHA256:', hashlib.sha256(original).hexdigest())
    print('Output SHA256:', hashlib.sha256(output).hexdigest())
    print('Verified triangle positions/UVs/materials, planar normals, references and all other UTF leaves.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    repair(args.source, args.destination)
