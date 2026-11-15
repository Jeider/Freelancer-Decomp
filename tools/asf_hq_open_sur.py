"""Rebuild asf_hq.sur from each baked component, not one hull of the arch.

The tails already contain the commented loadout pieces. A convex hull of a
whole arch fills the opening, and a slab along the long axis still bridges
the two legs. Each piece is hulled on its own. Arches are cut into short
cells so the gap stays open, then placed with the same hardpoint transform
the mesh bake uses.
"""
from pathlib import Path
import struct as S
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_station_lods as utf
import bake_compound as bake
import bake_one_part as part
import train_sur.build as sur

DATA = Path(r'D:\Games\FL_MOD\DATA')
CORE = DATA / 'SOLAR' / 'misc' / 'asf_hq_core.3db'
OUT = DATA / 'SOLAR' / 'misc' / 'asf_hq.sur'
ARCH_CELL = 96.0
POINT_BUDGET = 60000


def baked_rows():
    lines = (DATA / 'SOLAR' / 'loadouts.ini').read_text(encoding='utf-8', errors='replace').splitlines()
    on = False
    found = []
    for line in lines:
        if line.strip() == 'nickname = asf_hq_core_optimal':
            on = True
            continue
        if on and line.startswith('['):
            break
        if not on or not line.strip().startswith(';'):
            continue
        text = line.strip().lstrip(';').strip()
        if not text.startswith('equip'):
            continue
        rest = text.split('=', 1)[1]
        nick, _, hp = rest.partition(',')
        nick, hp = nick.strip(), hp.strip()
        if any(f'_{g}_' in hp.upper() for g in ('FRONT', 'BACK', 'LEFT', 'RIGHT')):
            found.append((nick, hp))
    return found


def triangles(path):
    levels, root = part.model_levels(path)
    blob = levels[0] if levels else part.mesh_of(root, None)
    parsed, verts = part.read_mesh(blob)
    points = np.array([S.unpack_from('<3f', raw, 0) for raw in verts])
    tris = []
    for _mat, lo, _hi, _unused, ids in parsed:
        for i in range(0, len(ids) - 2, 3):
            tris.append(points[[lo + ids[i], lo + ids[i + 1], lo + ids[i + 2]]])
    return np.asarray(tris) if tris else np.zeros((0, 3, 3))


def clip_cell(poly, index, cell):
    for axis, i in enumerate(index):
        if len(poly) == 0 or getattr(poly, 'ndim', 1) != 2:
            return np.zeros((0, 3))
        poly = sur.clip(poly, axis, float(i) * cell, True)
        if len(poly) == 0 or getattr(poly, 'ndim', 1) != 2:
            return np.zeros((0, 3))
        poly = sur.clip(poly, axis, float(i + 1) * cell, False)
    if len(poly) == 0 or getattr(poly, 'ndim', 1) != 2 or len(poly) < 3:
        return np.zeros((0, 3))
    return poly


def cell_clouds(tris, cell):
    bins = {}
    for tri in tris:
        lo = np.floor(tri.min(0) / cell).astype(int)
        hi = np.floor(tri.max(0) / cell).astype(int)
        if np.prod(hi - lo + 1) > 48:
            key = tuple(np.floor(tri.mean(0) / cell).astype(int))
            bins.setdefault(key, []).append(tri)
            continue
        for ix in range(int(lo[0]), int(hi[0]) + 1):
            for iy in range(int(lo[1]), int(hi[1]) + 1):
                for iz in range(int(lo[2]), int(hi[2]) + 1):
                    poly = clip_cell(tri, (ix, iy, iz), cell)
                    if len(poly) >= 3:
                        bins.setdefault((ix, iy, iz), []).append(poly)
    return [np.concatenate(polys) for polys in bins.values() if polys]


def local_hulls(path, nick, cache):
    key = (str(path).lower(), 'arch' in nick.lower())
    if key in cache:
        return cache[key]
    tris = triangles(path)
    if len(tris) == 0:
        cache[key] = []
        return cache[key]
    clouds = cell_clouds(tris, ARCH_CELL) if key[1] else [tris.reshape(-1, 3)]
    cache[key] = [h for cloud in clouds if (h := hull_from(cloud, 0))]
    return cache[key]


def hull_from(cloud, part_id):
    solid = part.thicken(np.asarray(cloud, float))
    if solid is None:
        return None
    try:
        return sur.make_hull(solid, part_id)
    except Exception:
        return None


def place(hull, rotation, translation, part_id):
    points = hull.points @ rotation.T + translation
    faces = hull.faces
    if np.linalg.det(rotation) < 0:
        faces = faces[:, [0, 2, 1]]
    return sur.Hull(points, faces.copy(), part_id)


def component_hulls(path, nick, rotation, translation, part_id, cache):
    return [place(local, rotation, translation, part_id) for local in local_hulls(path, nick, cache)]


def section(part_id, hulls):
    surface, lo, hi = sur.encode_surface(hulls)
    out = bytearray(S.pack('<II', part_id, 3))
    out.extend(b'!fxd')
    out.extend(b'exts' + S.pack('<6f', *lo, *hi))
    out.extend(b'surf' + S.pack('<I', len(surface)) + surface)
    return bytes(out)


def opening_blocked(hulls, point):
    for hull in hulls:
        outside = False
        for face in hull.faces:
            a, b, c = hull.points[face]
            normal = np.cross(b - a, c - a)
            if np.dot(normal, point - a) > 1.0:
                outside = True
                break
        if not outside:
            return True
    return False


def collect():
    _, equipment, _ = bake.catalog(DATA)
    _, roots = utf.read_tree(CORE.read_bytes())
    core_hps = bake.hardpoints(roots[0])
    cache = {}
    hulls = []
    arch_checks = []
    skipped = 0
    for nick, hp in baked_rows():
        eq = equipment.get(nick.lower())
        if not eq or 'da_archetype' not in eq or hp.lower() not in core_hps:
            skipped += 1
            continue
        path = bake.model_path(DATA, eq['da_archetype'][0])
        anchor = eq.get('hp_child', ['HpRoot'])[0].lower()
        _, child = part.model_levels(path)
        rotation, translation = bake.compose(
            core_hps[hp.lower()],
            bake.inverse(bake.hardpoints(child).get(anchor, (np.eye(3), np.zeros(3)))))
        piece = component_hulls(path, nick, rotation, translation, 0, cache)
        if not piece:
            skipped += 1
            continue
        if 'arch' in nick.lower() and 'part' not in nick.lower():
            local = np.array([0.0, 0.0, -150.0])
            arch_checks.append((nick, piece, rotation @ local + translation))
        hulls.extend(piece)
    return hulls, arch_checks, skipped


def main():
    hulls, arch_checks, skipped = collect()
    points = sum(len(h.points) for h in hulls)
    blocked = sum(1 for _nick, piece, point in arch_checks if opening_blocked(piece, point))
    report = {
        'hulls': len(hulls),
        'points': points,
        'arches': len(arch_checks),
        'openings_blocked': blocked,
        'skipped': skipped,
    }
    print(report)
    if not hulls or blocked or points > POINT_BUDGET:
        raise SystemExit('refusing to write a SUR that still fills arches or exceeds the point budget')
    root_id = utf.crc('Root')
    rooted = [place(h, np.eye(3), np.zeros(3), root_id) for h in hulls]
    out = bytearray(b'vers' + S.pack('<f', 2.0))
    out.extend(section(0, hulls))
    out.extend(section(root_id, rooted))
    OUT.write_bytes(out)
    print({'bytes': len(out), 'root': hex(root_id)})


if __name__ == '__main__':
    main()
