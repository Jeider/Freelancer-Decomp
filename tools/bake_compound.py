"""Bake placed solars and their visual loadout meshes into one CMP and one SUR.

Each source keeps its MultiLevel LODs, hardpoints and VMeshData. Only the mesh
ids are retargeted into the compound library. Collision comes from the existing
SUR hulls, transformed with the same placement. A hull is dropped only when it
already sits inside another, and two hulls merge only when the convex union
adds no volume, so the solid stays the same while the hull count falls.

Output is staged. This tool does not write into the game tree.
"""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field
from pathlib import Path
import struct as S
import sys

import numpy as np
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import generate_station_lods as utf
import train_sur.build as sur


def find(node, name):
    if node.name.lower() == name.lower():
        yield node
    for child in node.children:
        yield from find(child, name)


def one(node, name):
    return next(find(node, name), None)


def text(blob):
    return blob.split(b'\0', 1)[0].decode('ascii') if blob else ''


def clone(node):
    out = utf.Node(node.name, None if node.blob is None else bytes(node.blob), bytes(node.raw))
    out.children = [clone(c) for c in node.children]
    return out


def ini_blocks(path):
    text_ = Path(path).read_text(encoding='utf-8', errors='replace')
    cur = None
    body = []
    out = []
    for line in text_.splitlines():
        s = line.split(';', 1)[0].strip()
        if s.startswith('[') and s.endswith(']'):
            if cur:
                out.append((cur, body))
            cur = s[1:-1]
            body = []
        elif s and '=' in s and cur:
            body.append(s)
    if cur:
        out.append((cur, body))
    return out


def fields(body):
    d = {}
    for line in body:
        k, v = line.split('=', 1)
        d.setdefault(k.strip().lower(), []).append(v.strip())
    return d


def euler(x, y, z):
    ax, ay, az = np.radians((x, y, z))
    cx, sx = np.cos(ax), np.sin(ax)
    cy, sy = np.cos(ay), np.sin(ay)
    cz, sz = np.cos(az), np.sin(az)
    rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
    ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return rz @ rx @ ry


def mat_from(blob):
    return np.array(S.unpack('<9f', blob), dtype=float).reshape(3, 3)


def hardpoints(root):
    found = {}
    node = one(root, 'Hardpoints')
    if not node:
        return found
    for kind in node.children:
        for hp in kind.children:
            ori = one(hp, 'Orientation')
            pos = one(hp, 'Position')
            if pos is None:
                continue
            found[hp.name.lower()] = (
                mat_from(ori.blob) if ori is not None else np.eye(3),
                np.array(S.unpack('<3f', pos.blob), dtype=float))
    return found


def compose(parent, child):
    pr, pt = parent
    cr, ct = child
    return pr @ cr, pr @ ct + pt


def inverse(xform):
    r, t = xform
    ri = r.T
    return ri, -(ri @ t)


@dataclass
class Piece:
    name: str
    root: object
    rotation: np.ndarray
    translation: np.ndarray
    hulls: list = field(default_factory=list)


def library_meshes(root):
    lib = one(root, 'VMeshLibrary')
    return {} if lib is None else {utf.crc(n.name): n for n in lib.children}


def retarget(node, mapping):
    for ref in find(node, 'VMeshRef'):
        old = S.unpack_from('<I', ref.blob, 4)[0]
        if old not in mapping:
            raise ValueError(f'VMeshRef {old:08x} has no library mesh')
        blob = bytearray(ref.blob)
        S.pack_into('<I', blob, 4, mapping[old])
        ref.blob = bytes(blob)


def referenced(node):
    ids = set()
    for ref in find(node, 'VMeshRef'):
        ids.add(S.unpack_from('<I', ref.blob, 4)[0])
    return ids


def adopt(piece, library, used):
    meshes = library_meshes(piece.root)
    needed = referenced(piece.root)
    mapping = {}
    for old, node in meshes.items():
        if needed and old not in needed:
            continue
        name = clip(f'{piece.name}_{node.name}', used)
        used.add(utf.crc(name))
        mapping[old] = utf.crc(name)
        copy = clone(node)
        copy.name = name
        library.children.append(copy)
    part = utf.Node(clip(f'{piece.name}.3db', used))
    for child in piece.root.children:
        if child.name.lower() == 'vmeshlibrary':
            continue
        part.children.append(clone(child))
    retarget(part, mapping)
    return part


def parse_surface(blob):
    if len(blob) < 48:
        return []
    nodes = S.unpack_from('<I', blob, 32)[0]
    if not (48 <= nodes <= len(blob)):
        return []
    rel = S.unpack_from('<i', blob, 48)[0]
    points_at = 48 + rel
    if not (48 < points_at <= nodes) or (nodes - points_at) % 16:
        return []
    count = (nodes - points_at) // 16
    points = np.array([S.unpack_from('<3f', blob, points_at + 16 * i) for i in range(count)])
    hulls = []
    at = 48
    while at + 16 <= points_at:
        packed, nfaces = S.unpack_from('<I H', blob, at + 8)
        kind = packed & 0xff
        end = at + 16 + nfaces * 16
        if end > points_at or nfaces == 0:
            break
        if kind != 5:
            ids = []
            for face in range(nfaces):
                base = at + 20 + face * 16
                for corner in range(3):
                    ids.append(S.unpack_from('<H', blob, base + 4 * corner)[0])
            ids = [i for i in ids if i < len(points)]
            if len(ids) >= 3:
                hulls.append(points[ids])
        at = end
    return hulls


def read_sur(path):
    if not path.exists():
        return {}
    data = path.read_bytes()
    if data[:4] != b'vers':
        return {}
    at = 8
    found = {}
    while at + 8 <= len(data):
        crc, _kind = S.unpack_from('<II', data, at)
        at += 8
        if data[at:at + 4] == b'!fxd':
            at += 4
        if data[at:at + 4] != b'exts':
            break
        at += 28
        if data[at:at + 4] != b'surf':
            break
        size = S.unpack_from('<I', data, at + 4)[0]
        found.setdefault(crc, []).extend(parse_surface(data[at + 8:at + 8 + size]))
        at += 8 + size
    return found


def load_model(path):
    header, roots = utf.read_tree(path.read_bytes())
    return header, roots[0]


def part_root(compound, library, file_node):
    node = utf.Node(file_node.name)
    node.children = [clone(library)]
    node.children.extend(clone(c) for c in file_node.children)
    return node


def pieces_from_model(path, name, rotation, translation):
    _, root = load_model(path)
    surs = read_sur(path.with_suffix('.sur'))
    compound = one(root, 'Cmpnd')
    if compound is None:
        return [Piece(name, root, rotation, translation, surs.get(utf.crc(path.stem), surs.get(0, [])) or next(iter(surs.values()), []))]
    library = one(root, 'VMeshLibrary')
    links = {}
    cons = one(compound, 'Cons')
    if cons:
        for kind in cons.children:
            if kind.name.lower() != 'fix' or not kind.blob:
                continue
            for offset in range(0, len(kind.blob), 176):
                rec = kind.blob[offset:offset + 176]
                child = text(rec[64:128])
                links[child] = (
                    np.array(S.unpack_from('<9f', rec, 140), dtype=float).reshape(3, 3),
                    np.array(S.unpack_from('<3f', rec, 128), dtype=float))
    pieces = []
    for entry in compound.children:
        obj = one(entry, 'Object name')
        file = one(entry, 'File name')
        if obj is None or file is None:
            continue
        part = text(obj.blob)
        local_r, local_t = links.get(part, (np.eye(3), np.zeros(3)))
        world_r, world_t = compose((rotation, translation), (local_r, local_t))
        label = name if part.lower() == 'root' else f'{name}_{part}'
        pieces.append(Piece(label, part_root(compound, library, one(root, text(file.blob))),
                            world_r, world_t, surs.get(utf.crc(part), [])))
    pieces.sort(key=lambda p: p.name != name)
    return pieces


def catalog(data):
    solars = {}
    equipment = {}
    loadouts = {}
    for folder, dest in (('SOLAR', solars), ('EQUIPMENT', equipment)):
        for path in (data / folder).rglob('*.ini'):
            if path.stat().st_size > 8_000_000:
                continue
            for kind, body in ini_blocks(path):
                d = fields(body)
                nick = d.get('nickname', [''])[0].lower()
                if nick:
                    d['section'] = kind.lower()
                    dest[nick] = d
    for path in (data / 'SOLAR').rglob('*.ini'):
        if path.name.lower().startswith('loadout') or 'loadout' in path.name.lower():
            for kind, body in ini_blocks(path):
                if kind.lower() != 'loadout':
                    continue
                d = fields(body)
                nick = d.get('nickname', [''])[0].lower()
                if nick:
                    loadouts[nick] = d
    return solars, equipment, loadouts


def model_path(data, archetype):
    rel = archetype.replace('\\', '/')
    path = data / rel
    if not path.exists():
        raise FileNotFoundError(path)
    return path


@dataclass
class Placement:
    name: str
    archetype: str
    loadout: str = ''
    pos: tuple = (0, 0, 0)
    rotate: tuple = (0, 0, 0)
    parent: str = ''


def expand(placements, data, solars, equipment, loadouts):
    pieces = []
    residual = []
    skipped = []
    for item in placements:
        solar = solars.get(item.archetype.lower())
        if not solar or 'da_archetype' not in solar:
            skipped.append(item.name)
            continue
        arch = solar['da_archetype'][0]
        if not arch.lower().endswith(('.3db', '.cmp')):
            skipped.append(item.name + ' ' + arch)
            continue
        rotation = euler(*item.rotate)
        translation = np.array(item.pos, dtype=float)
        base = pieces_from_model(model_path(data, arch), item.name, rotation, translation)
        pieces.extend(base)
        if not item.loadout:
            continue
        spec = loadouts.get(item.loadout.lower())
        if not spec:
            residual.append((item.name, item.loadout, 'missing loadout'))
            continue
        hps = hardpoints(base[0].root)
        for line in spec.get('equip', []):
            nick, _, hp = line.partition(',')
            nick, hp = nick.strip(), hp.strip()
            eq = equipment.get(nick.lower())
            if not eq or 'da_archetype' not in eq or eq.get('section') not in ('cargopod', 'attachedfx', ''):
                residual.append((item.name, nick, hp or eq.get('section', 'no mesh') if eq else 'no mesh'))
                continue
            if hp.lower() not in hps:
                residual.append((item.name, nick, 'missing ' + hp))
                continue
            child_path = model_path(data, eq['da_archetype'][0])
            _, child_root = load_model(child_path)
            anchor = eq.get('hp_child', ['HpRoot'])[0].lower()
            child_hps = hardpoints(child_root)
            placed = compose(hps[hp.lower()], inverse(child_hps.get(anchor, (np.eye(3), np.zeros(3)))))
            world = compose((rotation, translation), placed)
            piece = Piece(f'{item.name}_{nick}_{hp}', child_root, world[0], world[1],
                          read_sur(child_path.with_suffix('.sur')))
            pieces.append(piece)
    return pieces, residual, skipped


def contained(points, hull):
    padded = np.concatenate([points, np.ones((len(points), 1))], axis=1)
    return np.all(padded @ hull.equations.T <= 1e-3)


def thicken(points, skin=0.15):
    pts = np.unique(np.round(np.asarray(points, float), 4), axis=0)
    if len(pts) < 3:
        return None
    if np.linalg.matrix_rank(pts - pts[0]) >= 3:
        return pts
    a, b, c = pts[:3]
    normal = np.cross(b - a, c - a)
    length = np.linalg.norm(normal)
    if length < 1e-8:
        return None
    return np.concatenate([pts + normal / length * skin, pts - normal / length * skin])


def fast_tree(hulls):
    nodes = [sur.Node(h.points.min(axis=0), h.points.max(axis=0), h) for h in hulls]

    def split(ns):
        if len(ns) == 1:
            return ns[0]
        centers = np.array([(n.lo + n.hi) / 2 for n in ns])
        axis = int(np.argmax(centers.max(axis=0) - centers.min(axis=0)))
        ns.sort(key=lambda n: (n.lo[axis] + n.hi[axis]) / 2)
        mid = max(1, len(ns) // 2)
        left, right = split(ns[:mid]), split(ns[mid:])
        return sur.Node(np.minimum(left.lo, right.lo), np.maximum(left.hi, right.hi),
                        left=left, right=right)

    root = split(nodes)
    if len(hulls) > 1:
        root.hull = sur.make_hull(np.concatenate([h.points for h in hulls]), 0, True)
    return root


sur.tree = fast_tree


def optimize(clouds, touch=0.75):
    items = []
    for cloud in clouds:
        arr = np.asarray(cloud, float)
        if arr.ndim != 2 or len(arr) < 3:
            continue
        pts = np.unique(np.round(arr, 3), axis=0)
        if len(pts) < 3:
            continue
        a, b, c = pts[:3]
        normal = np.cross(b - a, c - a)
        length = np.linalg.norm(normal)
        if length < 1e-8:
            continue
        normal = normal / length
        if normal[2] < 0:
            normal = -normal
        items.append((tuple(np.round(normal, 1)), pts.min(axis=0), pts.max(axis=0), pts))
    parent = list(range(len(items)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    bins = {}
    for i, (key, lo, hi, pts) in enumerate(items):
        bins.setdefault(key, []).append(i)
    for group in bins.values():
        for a in range(len(group)):
            i = group[a]
            lo, hi = items[i][1], items[i][2]
            for b in range(a + 1, len(group)):
                j = group[b]
                if find(i) == find(j):
                    continue
                olo, ohi = items[j][1], items[j][2]
                if np.all(lo <= ohi + touch) and np.all(olo <= hi + touch):
                    parent[find(j)] = find(i)
    groups = {}
    for i, item in enumerate(items):
        groups.setdefault(find(i), []).append(item[3])
    return [np.concatenate(pts) for pts in groups.values()]


def clip(name, used):
    raw = ''.join(ch if ch.isalnum() or ch in '._-' else '_' for ch in name)
    if len(raw) <= 63 and raw not in used:
        used.add(raw)
        return raw
    digest = format(utf.crc(raw) & 0xffffffff, '08x')
    out = f'{raw[:54]}_{digest}'
    while out in used:
        digest = format((utf.crc(out) + 1) & 0xffffffff, '08x')
        out = f'{raw[:54]}_{digest}'
    used.add(out)
    return out


def write_cmp(pieces):
    root = utf.Node('\\')
    library = utf.Node('VMeshLibrary')
    root.children.append(library)
    used = {'Root'}
    for piece in pieces:
        piece.name = clip(piece.name, used)
    part_nodes = [adopt(p, library, used) for p in pieces]
    for node in part_nodes:
        root.children.append(node)
    compound = utf.Node('Cmpnd')
    root.children.append(compound)
    fix = bytearray()
    entries = []
    for index, (piece, node) in enumerate(zip(pieces, part_nodes)):
        part = utf.Node(clip(f'Part_{piece.name}', used))
        part.children = [
            utf.Node('Object name', piece.name.encode('ascii') + b'\0'),
            utf.Node('Index', S.pack('<I', index)),
            utf.Node('File name', (node.name + '\0').encode('ascii')),
        ]
        entries.append(part)
        if index == 0:
            part.children[0].blob = b'Root\0'
            continue
        rec = bytearray(176)
        rec[:4] = b'Root'
        rec[64:64 + len(piece.name)] = piece.name.encode('ascii')
        S.pack_into('<3f', rec, 128, *piece.translation)
        S.pack_into('<9f', rec, 140, *piece.rotation.reshape(-1))
        fix.extend(rec)
    cons = utf.Node('Cons')
    if fix:
        cons.children.append(utf.Node('Fix', bytes(fix)))
    compound.children = [cons, *entries]
    header = [0x20465455, 0x101, 0, 0, 0, 44, 0, 0, 0, 0, 0, 0, 0, 0]
    return utf.write_tree(header, [root])


def solid(cloud, hull_id):
    pts = thicken(cloud)
    if pts is None or len(pts) < 4:
        return None
    try:
        return sur.make_hull(pts, hull_id)
    except Exception:
        return None


def packable(clouds, hull_id, limit=48000):
    boxes = []
    for cloud in clouds:
        arr = np.asarray(cloud, float)
        if arr.ndim != 2 or len(arr) < 3:
            continue
        lo, hi = arr.min(axis=0), arr.max(axis=0)
        if np.linalg.norm(hi - lo) < 1e-4:
            continue
        corners = np.array([[lo[0], lo[1], lo[2]], [hi[0], lo[1], lo[2]],
                            [lo[0], hi[1], lo[2]], [hi[0], hi[1], lo[2]],
                            [lo[0], lo[1], hi[2]], [hi[0], lo[1], hi[2]],
                            [lo[0], hi[1], hi[2]], [hi[0], hi[1], hi[2]]])
        boxes.append(corners)
    cell = 12.0
    while len(boxes) * 8 > limit and cell < 200:
        cell *= 2
        bins = {}
        for box in boxes:
            key = tuple(np.round(box.mean(axis=0) / cell).astype(int))
            bins.setdefault(key, []).append(box)
        boxes = [np.concatenate(group) for group in bins.values()]
    return [h for box in boxes if (h := solid(box, hull_id))]


def write_sur(pieces, optimized):
    root_hulls = packable(optimized, utf.crc('Root'))
    out = bytearray(b'vers' + S.pack('<f', 2.0))
    surface, lo, hi = sur.encode_surface(root_hulls or [sur.make_hull(
        np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float), 1)])
    out.extend(S.pack('<II', utf.crc('Root'), 3))
    out.extend(b'!fxd')
    out.extend(b'exts' + S.pack('<6f', *lo, *hi))
    out.extend(b'surf' + S.pack('<I', len(surface)) + surface)
    for piece in pieces:
        hulls = []
        for cloud in optimize(piece.hulls):
            hull = solid(cloud, utf.crc(piece.name))
            if hull is not None:
                hulls.append(hull)
        if not hulls:
            continue
        surface, lo, hi = sur.encode_surface(hulls)
        out.extend(S.pack('<II', utf.crc(piece.name), 2))
        out.extend(b'exts' + S.pack('<6f', *lo, *hi))
        out.extend(b'surf' + S.pack('<I', len(surface)) + surface)
    return bytes(out)


def bake(placements, data):
    solars, equipment, loadouts = catalog(data)
    pieces, residual, skipped = expand(placements, data, solars, equipment, loadouts)
    if not pieces:
        raise ValueError('nothing to bake')
    clouds = []
    before = 0
    for piece in pieces:
        before += len(piece.hulls)
        for cloud in piece.hulls:
            if getattr(cloud, 'ndim', 0) != 2 or len(cloud) < 3:
                continue
            clouds.append(cloud @ piece.rotation.T + piece.translation)
    optimized = optimize(clouds)
    return {
        'cmp': write_cmp(pieces),
        'sur': write_sur(pieces, optimized),
        'pieces': [p.name for p in pieces],
        'hulls_before': before,
        'hulls_after': len(optimized),
        'residual': residual,
        'skipped': skipped,
    }


def placements_from_template(text):
    cur = None
    body = []
    blocks = []
    for line in text.splitlines():
        s = line.split(';', 1)[0].strip()
        if s.startswith('[') and s.endswith(']'):
            if cur:
                blocks.append((cur, body))
            cur = s[1:-1]
            body = []
        elif s and '=' in s and cur:
            body.append(s)
    if cur:
        blocks.append((cur, body))
    placed = []
    for kind, raw in blocks:
        if kind.lower() != 'object':
            continue
        d = fields(raw)
        pos = tuple(float(x) for x in d.get('pos', ['0,0,0'])[0].replace(',', ' ').split()[:3])
        rot = tuple(float(x) for x in d.get('rotate', ['0,0,0'])[0].replace(',', ' ').split()[:3])
        placed.append(Placement(
            d.get('nickname', ['part'])[0],
            d.get('archetype', [''])[0],
            d.get('loadout', [''])[0],
            pos, rot, d.get('parent', [''])[0]))
    return placed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data', type=Path, default=Path(r'D:\Games\FL_MOD\DATA'))
    parser.add_argument('--template', type=Path)
    parser.add_argument('--output', type=Path, default=ROOT / 'out' / 'bake_compound')
    parser.add_argument('--name', default='baked')
    args = parser.parse_args()
    if args.template:
        source = args.template.read_text(encoding='utf-8')
        if 'TEMPLATE' in source and "'''" in source:
            source = source.split("'''", 2)[1]
        placed = placements_from_template(source)
    else:
        parser.error('pass --template')
    # The far impostor and the planet core stay separate: one is the distance
    # stand-in, the other is a planet shader rather than a mesh compound.
    placed = [p for p in placed if 'full_lod' not in p.archetype.lower() and not p.archetype.lower().startswith('sw_center')]
    if placed:
        root = placed[0]
        placed[0] = Placement(root.name, root.archetype, root.loadout, (0, 0, 0), (0, 0, 0), root.parent)
    result = bake(placed, args.data)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / f'{args.name}.cmp').write_bytes(result['cmp'])
    (args.output / f'{args.name}.sur').write_bytes(result['sur'])
    report = {k: v for k, v in result.items() if k not in ('cmp', 'sur')}
    report['sur_bytes'] = len(result['sur'])
    report['cmp_bytes'] = len(result['cmp'])
    (args.output / f'{args.name}.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('pieces', 'hulls_before', 'hulls_after', 'cmp_bytes', 'sur_bytes', 'skipped')}))


if __name__ == '__main__':
    main()
