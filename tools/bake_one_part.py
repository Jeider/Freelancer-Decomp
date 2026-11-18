"""Bake one station part into a single 3db so close-up is one draw, not 46.

Each cargo pod keeps the distances in its own LODranges. A baked level contains
only the meshes that would be visible in that band, at the pod's own LOD.
Facegroups of the same material are merged: the UTF editor rejects a meshgroup
with a group per source mesh. The node stays named Switch2.
"""
from pathlib import Path
import struct as S
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_station_lods as utf
import bake_compound as bake
import train_sur.build as sur

DATA = Path(r'D:\Games\FL_MOD\DATA')
PART = DATA / 'SOLAR' / 'misc' / 'space_trade_station_part.3db'
OUT = Path(__file__).resolve().parents[1] / 'out' / 'stations' / 'bake_compound' / 'part.3db'
ROOT_NAME = 'Root'
LOADOUT = 'space_trade_part_attacher'
MAX_LEVELS = 8


def floats(text):
    return [float(x) for x in text.replace(',', ' ').split() if x]


def mesh_of(root, level):
    part = bake.one(root, 'VMeshPart')
    if part is None and level is not None:
        part = bake.one(level, 'VMeshPart')
    if part is None:
        multi = bake.one(root, 'MultiLevel')
        if multi is None:
            return None
        level0 = bake.one(multi, 'Level0')
        part = bake.one(level0, 'VMeshPart') if level0 else None
    if part is None:
        return None
    ref = bake.one(part, 'VMeshRef')
    if ref is None:
        return None
    mesh_id = S.unpack_from('<I', ref.blob, 4)[0]
    lib = bake.library_meshes(root)
    node = lib.get(mesh_id)
    if node is None:
        return None
    return bake.one(node, 'VMeshData').blob


def model_levels(path):
    _, roots = utf.read_tree(Path(path).read_bytes())
    root = roots[0]
    multi = bake.one(root, 'MultiLevel')
    if multi is None:
        blob = mesh_of(root, None)
        return [blob] if blob else [], root
    levels = []
    for child in multi.children:
        if child.name.lower().startswith('level'):
            blob = mesh_of(root, child)
            if blob:
                levels.append(blob)
    return levels, root


def read_mesh(blob):
    flags, prim, groups, count, fvf, vertices = S.unpack_from('<II4H', blob)
    if (flags, prim, fvf) != (1, 4, 0x112):
        raise ValueError('unsupported mesh')
    index_at = 16 + 12 * groups
    cursor = 0
    parsed = []
    for g in range(groups):
        mat, lo, hi, nidx, unused = S.unpack_from('<I4H', blob, 16 + 12 * g)
        ids = S.unpack_from('<' + 'H' * nidx, blob, index_at + 2 * cursor)
        parsed.append((mat, lo, hi, unused, ids))
        cursor += nidx
    vert_at = index_at + 2 * count
    verts = [blob[vert_at + 32 * i:vert_at + 32 * (i + 1)] for i in range(vertices)]
    return parsed, verts


def write_mesh(groups, verts):
    count = sum(len(ids) for *_, ids in groups)
    out = bytearray(S.pack('<II4H', 1, 4, len(groups), count, 0x112, len(verts)))
    index = bytearray()
    for mat, lo, hi, unused, ids in groups:
        out.extend(S.pack('<I4H', mat, lo, hi, len(ids), unused))
        index.extend(S.pack('<' + 'H' * len(ids), *ids))
    out.extend(index)
    out.extend(b''.join(verts))
    return bytes(out)


def xform_vert(raw, rotation, translation):
    pos = rotation @ np.array(S.unpack_from('<3f', raw, 0)) + translation
    normal = rotation @ np.array(S.unpack_from('<3f', raw, 12))
    length = np.linalg.norm(normal)
    if length > 1e-8:
        normal = normal / length
    out = bytearray(raw)
    S.pack_into('<3f', out, 0, *pos)
    S.pack_into('<3f', out, 12, *normal)
    return bytes(out)


def append_mesh(groups, verts, blob, rotation, translation):
    added, source = read_mesh(blob)
    base = len(verts)
    for mat, lo, hi, unused, ids in added:
        groups.append((mat, base + lo, base + hi, unused, ids))
    verts.extend(xform_vert(raw, rotation, translation) for raw in source)


def coalesce(groups):
    # Indices are relative to VertexBegin. Merge by material into one group so
    # the meshgroup stays small enough for the editor and one draw per material.
    merged = {}
    order = []
    for mat, lo, hi, unused, ids in groups:
        if mat not in merged:
            order.append(mat)
            merged[mat] = []
        merged[mat].extend(i + lo for i in ids)
    out = []
    for mat in order:
        absolute = merged[mat]
        while absolute:
            chunk = absolute[:65535]
            absolute = absolute[65535:]
            lo = min(chunk)
            hi = max(chunk)
            out.append((mat, lo, hi, 204, [i - lo for i in chunk]))
    return out


def piece_ranges(eq, level_count):
    raw = floats(eq.get('lodranges', ['0, 10000'])[0])
    if len(raw) < 2:
        raw = [0.0, 10000.0]
    used = min(level_count, len(raw) - 1)
    return raw[:used + 1]


def active_level(ranges, distance):
    for index in range(len(ranges) - 1):
        if ranges[index] <= distance < ranges[index + 1]:
            return index
    return None


def merge_bands(edges):
    edges = sorted(set(edges))
    while len(edges) - 1 > MAX_LEVELS:
        gaps = [(edges[i + 1] - edges[i], i) for i in range(1, len(edges) - 1)]
        _, index = min(gaps)
        del edges[index]
    return edges


def sur_leaves(path):
    data = Path(path).with_suffix('.sur').read_bytes()
    if data[:4] != b'vers':
        return []
    parsed = []
    at = 8
    while at + 8 <= len(data):
        part_id, count = S.unpack_from('<II', data, at)
        at += 8
        chunks = {}
        for _ in range(count):
            tag = data[at:at + 4]
            at += 4
            if tag == b'exts':
                chunks[tag] = data[at:at + 24]
                at += 24
            elif tag == b'surf':
                size = S.unpack_from('<I', data, at)[0]
                at += 4
                chunks[tag] = data[at:at + size]
                at += size
            elif tag == b'hpid':
                n = S.unpack_from('<I', data, at)[0]
                at += 4 + n * 4
            elif tag != b'!fxd':
                return []
        parsed.append((part_id, chunks.get(b'surf')))
    surface = None
    for part_id, blob in parsed:
        if part_id in (0, 0x12688F2D):
            surface = blob
            break
    if surface is None and parsed:
        surface = parsed[0][1]
    if not surface:
        return []
    root = S.unpack_from('<i', surface, 32)[0]
    leaves = []

    def walk(offset):
        right, ledge = S.unpack_from('<ii', surface, offset)
        if right:
            walk(offset + 28)
            walk(offset + right)
            return
        start = offset + ledge
        poff, _client, _flags, count, _unused = S.unpack_from('<iIIHH', surface, start)
        indices = set()
        for face in range(count):
            base = start + 16 + face * 16
            for edge in range(3):
                indices.add(S.unpack_from('<H', surface, base + 4 + edge * 4)[0])
        if len(indices) >= 3:
            leaves.append(np.array([S.unpack_from('<3f', surface, start + poff + i * 16) for i in indices]))

    walk(root)
    return leaves


def thicken(points):
    pts = np.unique(np.round(points, 3), axis=0)
    if len(pts) < 3:
        return None
    centered = pts - pts.mean(axis=0)
    _u, sv, vt = np.linalg.svd(centered, full_matrices=False)
    if len(pts) >= 4 and sv[-1] > 0.4:
        return pts
    normal = vt[-1]
    return np.vstack((pts + normal * 0.5, pts - normal * 0.5))


def bounds(verts):
    pts = np.array([S.unpack_from('<3f', raw, 0) for raw in verts])
    lo, hi = pts.min(axis=0), pts.max(axis=0)
    center = (lo + hi) / 2
    radius = float(np.max(np.linalg.norm(pts - center, axis=1))) * 1.02
    return lo, hi, center, radius


def ref_bytes(mesh_id, blob):
    flags, prim, groups, count, fvf, vertices = S.unpack_from('<II4H', blob)
    lo, hi, center, radius = bounds(
        [blob[16 + 12 * groups + 2 * count + 32 * i:16 + 12 * groups + 2 * count + 32 * i + 12]
         for i in range(vertices)])
    out = bytearray(60)
    S.pack_into('<2I6H', out, 0, 60, mesh_id, 0, vertices, 0, count, 0, groups)
    S.pack_into('<6f', out, 0x14, *lo, *hi)
    S.pack_into('<3f', out, 0x2C, *center)
    S.pack_into('<f', out, 0x38, radius)
    return bytes(out)


def sur_section(part_id, hulls, fixed):
    surface, lo, hi = sur.encode_surface(hulls)
    out = bytearray(S.pack('<II', part_id, 3 if fixed else 2))
    if fixed:
        out.extend(b'!fxd')
    out.extend(b'exts' + S.pack('<6f', *lo, *hi))
    out.extend(b'surf' + S.pack('<I', len(surface)) + surface)
    return bytes(out)


def fix_record(parent, child, rotation, translation):
    rec = bytearray(176)
    rec[:len(parent)] = parent.encode('ascii')
    rec[64:64 + len(child)] = child.encode('ascii')
    S.pack_into('<3f', rec, 128, *translation)
    S.pack_into('<9f', rec, 140, *rotation.reshape(-1))
    return rec


def part_entry(folder, obj, index, file_name):
    entry = utf.Node(folder)
    entry.children = [
        utf.Node('Object name', (obj + '\0').encode('ascii')),
        utf.Node('Index', S.pack('<I', index)),
        utf.Node('File name', (file_name + '\0').encode('ascii')),
    ]
    return entry


def main():
    header, roots = utf.read_tree(PART.read_bytes())
    header[0] = 0x20465455
    header[1] = 0x101
    header[5] = 44
    root = roots[0]
    part_levels, _ = model_levels(PART)
    _, equipment, loadouts = bake.catalog(DATA)
    part_eq = {'lodranges': ['0, 8000, 27000'], 'section': 'part'}
    pieces = [(part_levels, piece_ranges(part_eq, len(part_levels)), np.eye(3), np.zeros(3), PART)]
    domes = []
    hps = bake.hardpoints(root)
    for line in loadouts[LOADOUT].get('equip', []):
        nick, _, hp = line.partition(',')
        eq = equipment.get(nick.strip().lower())
        if not eq or eq.get('section') != 'cargopod' or 'da_archetype' not in eq:
            continue
        if hp.strip().lower() not in hps:
            continue
        path = bake.model_path(DATA, eq['da_archetype'][0])
        if path.name.lower() == 'space_dome.cmp':
            anchor = eq.get('hp_child', ['HpRoot'])[0].lower()
            _, dome_roots = utf.read_tree(path.read_bytes())
            body = bake.one(dome_roots[0], 'space_dome_lod1021003093018.3db')
            rotation, translation = bake.compose(
                hps[hp.strip().lower()],
                bake.inverse(bake.hardpoints(body).get(anchor, (np.eye(3), np.zeros(3)))))
            domes.append((rotation, translation, path))
            continue
        levels, child = model_levels(path)
        if not levels:
            continue
        anchor = eq.get('hp_child', ['HpRoot'])[0].lower()
        rotation, translation = bake.compose(
            hps[hp.strip().lower()],
            bake.inverse(bake.hardpoints(child).get(anchor, (np.eye(3), np.zeros(3)))))
        pieces.append((levels, piece_ranges(eq, len(levels)), rotation, translation, path))
    edges = [0.0]
    for _levels, ranges, _rotation, _translation, _path in pieces:
        edges.extend(ranges[1:])
    edges = merge_bands(edges)
    library = bake.one(root, 'VMeshLibrary')
    library.children = []
    multi = bake.one(root, 'MultiLevel')
    multi.children = []
    for index in range(len(edges) - 1):
        mid = (edges[index] + edges[index + 1]) * 0.5
        groups, verts = [], []
        for levels, ranges, rotation, translation, _path in pieces:
            level = active_level(ranges, mid)
            if level is None:
                continue
            append_mesh(groups, verts, levels[level], rotation, translation)
        if not verts:
            groups, verts = read_mesh(part_levels[-1])
        blob = write_mesh(coalesce(groups), verts)
        name = f'part_lod{index}'
        node = utf.Node(name)
        node.children = [utf.Node('VMeshData', blob)]
        library.children.append(node)
        level = utf.Node(f'Level{index}')
        vm = utf.Node('VMeshPart')
        vm.children = [utf.Node('VMeshRef', ref_bytes(utf.crc(name), blob))]
        level.children = [vm]
        multi.children.append(level)
    multi.children.append(utf.Node('Switch2', S.pack('<' + 'f' * len(edges), *edges)))
    shell = utf.Node('tgk_shell.3db')
    shell.children = [child for child in root.children if child.name.lower() != 'vmeshlibrary']
    compound = utf.Node('\\')
    compound.children = [library, shell]
    entries = [part_entry('Root', ROOT_NAME, 0, shell.name)]
    fix = bytearray()
    if domes:
        _, dome_roots = utf.read_tree(domes[0][2].read_bytes())
        dome_root = dome_roots[0]
        for mesh in bake.one(dome_root, 'VMeshLibrary').children:
            library.children.append(bake.clone(mesh))
        body_src = bake.one(dome_root, 'space_dome_lod1021003093018.3db')
        cap_src = bake.one(dome_root, 'dome_lod1021003093018.3db')
        for index, (rotation, translation, _path) in enumerate(domes):
            body_obj = f'dome{index:02d}'
            cap_obj = f'dome{index:02d}_cap'
            body_file = f'{body_obj}.3db'
            cap_file = f'{cap_obj}.3db'
            body = bake.clone(body_src)
            body.name = body_file
            # Level 0 holds tree_64 and forest. The source switch drops them at 100.
            switch = bake.one(bake.one(body, 'MultiLevel'), 'Switch2')
            switch.blob = S.pack('<4f', 0.0, 2000.0, 5000.0, 1000000.0)
            cap = bake.clone(cap_src)
            cap.name = cap_file
            compound.children.extend((body, cap))
            entries.append(part_entry('Part_' + body_obj, body_obj, len(entries), body_file))
            entries.append(part_entry('Part_' + cap_obj, cap_obj, len(entries), cap_file))
            fix.extend(fix_record(ROOT_NAME, body_obj, rotation, translation))
            fix.extend(fix_record(body_obj, cap_obj, np.eye(3), np.zeros(3)))
    cons = utf.Node('Cons')
    cons.children = [utf.Node('Fix', bytes(fix))]
    cmpnd = utf.Node('Cmpnd')
    cmpnd.children = [cons, *entries]
    compound.children.append(cmpnd)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    cmp_path = OUT.with_suffix('.cmp')
    cmp_path.write_bytes(utf.write_tree(header, [compound]))
    root_id = utf.crc(ROOT_NAME)
    hulls = []
    for _levels, _ranges, rotation, translation, path in pieces:
        for local in sur_leaves(path):
            solid = thicken(local @ rotation.T + translation)
            if solid is None:
                continue
            try:
                hulls.append(sur.make_hull(solid, root_id))
            except Exception:
                continue
    sur_out = bytearray(b'vers' + S.pack('<f', 2.0))
    for rotation, translation, path in domes:
        for local in sur_leaves(path):
            solid = thicken(local @ rotation.T + translation)
            if solid is None:
                continue
            try:
                hulls.append(sur.make_hull(solid, root_id))
            except Exception:
                continue
    sur_out.extend(sur_section(root_id, hulls, True))
    for index, (_rotation, _translation, path) in enumerate(domes):
        # The Fix joint already places the part. The surface stays in part space.
        leaves = []
        for local in sur_leaves(path):
            solid = thicken(local)
            if solid is not None:
                leaves.append(solid)
        for obj in (f'dome{index:02d}', f'dome{index:02d}_cap'):
            part_id = utf.crc(obj)
            taken = []
            for solid in leaves:
                try:
                    taken.append(sur.make_hull(solid, part_id))
                except Exception:
                    continue
            if taken:
                sur_out.extend(sur_section(part_id, taken, False))
    OUT.with_suffix('.sur').write_bytes(sur_out)
    print({'levels': len(edges) - 1, 'switch': edges, 'bytes': cmp_path.stat().st_size,
           'sur': len(sur_out), 'hulls': len(hulls), 'domes': len(domes)})


if __name__ == '__main__':
    main()
