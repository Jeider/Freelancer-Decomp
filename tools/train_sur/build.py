"""Build staged SUR 2.0 files for rigid train CMPs; never writes into the game.

The SUR serialization follows MAXLancer Surface.ms (MIT, see LICENSE.MAXLancer).
Input coordinates are already in Freelancer space, so no Max axis conversion.
Requires numpy/scipy/Pillow. Collision hulls approximate the render mesh;
axial slabs limit how far convexification fills longitudinal recesses.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import struct as S
import sys

import numpy as np
from scipy.spatial import ConvexHull

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
import generate_station_lods as utf


def child(node, name):
    return next((n for n in node.children if n.name.lower() == name.lower()), None)


def string(node):
    return node.blob.split(b'\0')[0].decode('ascii')


@dataclass
class Part:
    name: str
    triangles: np.ndarray
    hardpoints: dict
    parent: str | None = None
    rotation: np.ndarray | None = None
    translation: np.ndarray | None = None


def read_cmp(path):
    root = utf.read_tree(path.read_bytes())[1][0]
    library = {utf.crc(n.name): child(n, 'VMeshData').blob
               for n in child(root, 'VMeshLibrary').children}
    compound = child(root, 'Cmpnd')
    parts = {}
    for entry in compound.children:
        if child(entry, 'Object name') is None:
            continue
        name = string(child(entry, 'Object name'))
        node = child(root, string(child(entry, 'File name')))
        vpart = child(node, 'VMeshPart')
        if vpart is None:
            vpart = child(child(child(node, 'MultiLevel'), 'Level0'), 'VMeshPart')
        ref = child(vpart, 'VMeshRef').blob
        mesh_id = S.unpack_from('<I', ref, 4)[0]
        base, nv, start_i, ni, start_g, ng = S.unpack_from('<6H', ref, 8)
        blob = library[mesh_id]
        flags, prim, groups, count, fvf, vertices = S.unpack_from('<II4H', blob)
        if (flags, prim, fvf) != (1, 4, 0x112):
            raise ValueError('Only relative-index XYZ/N/UV triangle meshes supported')
        voff = 16 + 12 * groups + 2 * count
        assert voff + 32 * vertices == len(blob)
        points = np.frombuffer(blob, dtype='<f4', offset=voff).reshape(-1, 8)[:, :3]
        idx_offset = 16 + 12 * groups
        tris = []
        for g in range(groups):
            mat, lo, hi, nidx, unused = S.unpack_from('<I4H', blob, 16 + 12*g)
            indices = np.frombuffer(blob, dtype='<u2', count=nidx, offset=idx_offset)
            idx_offset += nidx * 2
            if start_g <= g < start_g + ng:
                actual = indices.astype(int) + base + lo
                assert np.all(actual >= base) and np.all(actual < base + nv)
                tris.extend(points[actual].reshape(-1, 3, 3))
        assert len(tris) * 3 == ni
        hp = {}
        hpnode = child(node, 'Hardpoints')
        if hpnode:
            for kind in hpnode.children:
                for h in kind.children:
                    p = child(h, 'Position')
                    if p:
                        hp[h.name] = list(S.unpack('<3f', p.blob))
        parts[name] = Part(name, np.asarray(tris, dtype=float), hp,
                           rotation=np.eye(3), translation=np.zeros(3))
    cons = child(compound, 'Cons')
    if cons:
        for kind in cons.children:
            if kind.name.lower() != 'fix':
                raise ValueError('This builder supports fixed CMP subparts only')
            for offset in range(0, len(kind.blob), 176):
                b = kind.blob[offset:offset+176]
                parent = b[:64].split(b'\0')[0].decode()
                name = b[64:128].split(b'\0')[0].decode()
                parts[name].parent = parent
                parts[name].translation = np.array(S.unpack_from('<3f', b, 128))
                # FMatrix multiplies column vectors; numpy points here are row vectors.
                parts[name].rotation = np.array(S.unpack_from('<9f', b, 140)).reshape(3, 3).T
    assert len([p for p in parts.values() if p.parent is None]) == 1
    return parts


def clip(poly, axis, bound, greater):
    result = []
    for a, b in zip(poly, np.roll(poly, -1, axis=0)):
        ia = a[axis] >= bound if greater else a[axis] <= bound
        ib = b[axis] >= bound if greater else b[axis] <= bound
        if ia:
            result.append(a)
        if ia != ib:
            result.append(a + (b-a) * ((bound-a[axis])/(b[axis]-a[axis])))
    return np.asarray(result)


@dataclass
class Hull:
    points: np.ndarray
    faces: np.ndarray
    hull_id: int
    wrap: bool = False


def make_hull(points, hull_id, wrap=False):
    points = np.unique(np.asarray(points, dtype='<f4'), axis=0).astype(float)
    hull = ConvexHull(points)
    faces = hull.simplices.copy()
    for i, f in enumerate(faces):
        a, b, c = points[f]
        if np.dot(np.cross(b-a, c-a), hull.equations[i, :3]) < 0:
            faces[i] = f[[0, 2, 1]]
    selected = np.unique(faces)
    remap = {v: i for i, v in enumerate(selected)}
    faces = np.array([[remap[v] for v in f] for f in faces])
    return Hull(points[selected], faces, hull_id, wrap)


def hulls_for(part, slab_length, regions=None):
    tris = part.triangles
    lo = tris.min(axis=(0, 1))
    hi = tris.max(axis=(0, 1))
    axis = int(np.argmax(hi-lo))
    count = max(1, int(np.ceil((hi[axis]-lo[axis]) / slab_length)))
    bounds = np.linspace(lo[axis], hi[axis], count+1)
    if regions is None:
        regions = [[(axis, float(a), float(b))] for a, b in zip(bounds[:-1], bounds[1:])]
    result = []
    for region in regions:
        points = []
        for tri in tris:
            poly = tri
            for axis, a, b in region:
                if len(poly) and a is not None:
                    poly = clip(poly, axis, a, True)
                if len(poly) and b is not None:
                    poly = clip(poly, axis, b, False)
            points.extend(poly)
        if len(points) < 4 or np.linalg.matrix_rank(np.array(points)-points[0]) < 3:
            raise ValueError(f'Degenerate slab in {part.name}')
        result.append(make_hull(points, utf.crc(part.name)))
    return result


@dataclass
class Node:
    lo: np.ndarray
    hi: np.ndarray
    hull: Hull | None = None
    left: Node | None = None
    right: Node | None = None


def tree(hulls):
    nodes = [Node(h.points.min(axis=0), h.points.max(axis=0), h) for h in hulls]
    while len(nodes) > 1:
        _, a, b = min((np.linalg.norm((x.lo+x.hi)-(y.lo+y.hi)), i, j)
                      for i, x in enumerate(nodes) for j, y in enumerate(nodes) if i < j)
        x, y = nodes[a], nodes[b]
        nodes = [n for i, n in enumerate(nodes) if i not in (a, b)]
        nodes.append(Node(np.minimum(x.lo, y.lo), np.maximum(x.hi, y.hi), left=x, right=y))
    root = nodes[0]
    if len(hulls) > 1:
        root.hull = make_hull(np.concatenate([h.points for h in hulls]), 0, True)
    return root


def encode_hull(hull, point_base):
    p, faces = hull.points, hull.faces
    assert len(faces) < 4096 and len(faces) % 2 == 0
    edges = {(int(f[j]), int(f[(j+1) % 3])): (i, j)
             for i, f in enumerate(faces) for j in range(3)}
    assert len(edges) == len(faces) * 3
    normals = np.cross(p[faces[:, 1]]-p[faces[:, 0]], p[faces[:, 2]]-p[faces[:, 0]])
    normals /= np.linalg.norm(normals, axis=1)[:, None]
    plane = np.einsum('ij,ij->i', normals, p[faces[:, 0]])
    out = bytearray(S.pack('<IIIHH', 0, hull.hull_id,
                          (((12 + len(faces)*6)//4) << 8) | (5 if hull.wrap else 4), len(faces), 0))
    for i, f in enumerate(faces):
        # Ray from the face centre into the convex body, as in MAXLancer.
        origin = p[f].mean(axis=0)
        direction = -normals[i]
        denom = normals @ direction
        distance = np.full(len(faces), np.inf)
        valid = denom > 1e-8
        distance[valid] = (plane[valid]-normals[valid] @ origin)/denom[valid]
        opposite = int(np.argmin(distance))
        assert np.isfinite(distance[opposite]) and distance[opposite] > 0
        out.extend(S.pack('<I', i | (opposite << 12) | (0x80000000 if hull.wrap else 0)))
        for j in range(3):
            other_i, other_j = edges[(int(f[(j+1) % 3]), int(f[j]))]
            delta = 4*(other_i-i) + other_j-j
            assert -16384 <= delta < 16384
            out.extend(S.pack('<HH', point_base+int(f[j]), (delta & 0x7fff) | (0x8000 if hull.wrap else 0)))
    return out


def encode_surface(hulls):
    root = tree(hulls)
    all_hulls = hulls + ([root.hull] if root.left else [])
    data = bytearray(48)
    offsets = {}
    points = []
    for h in all_hulls:
        offsets[id(h)] = len(data)
        data.extend(encode_hull(h, len(points)))
        points.extend((p, h.hull_id) for p in h.points)
    assert len(points) <= 65535
    points_start = len(data)
    for p, hull_id in points:
        data.extend(S.pack('<3fI', *p, hull_id))
    nodes_start = len(data)
    for h in all_hulls:
        offset = offsets[id(h)]
        S.pack_into('<i', data, offset, points_start-offset)
        if h.wrap:
            S.pack_into('<i', data, offset+4, nodes_start-offset)

    def emit(n):
        offset = len(data)
        center = (n.lo+n.hi)/2
        half = (n.hi-n.lo)/2
        radius = np.linalg.norm(half) * (1+1e-6)
        # Round upward so the quantized box encloses the actual geometry.
        scales = np.minimum(250, np.ceil(250*half/radius)).astype(int)
        data.extend(S.pack('<ii3ff4B', 0, offsets[id(n.hull)]-offset if n.hull else 0,
                           *center, radius, *scales, 0))
        if n.left:
            emit(n.left)
            right = len(data)
            emit(n.right)
            S.pack_into('<i', data, offset, right-offset)
    emit(root)
    all_points = np.array([p for p, _ in points])
    radius = float(np.max(np.linalg.norm(all_points, axis=1))) * (1+1e-6)
    lo, hi = all_points.min(axis=0), all_points.max(axis=0)
    # Uniform bounding-box inertia per unit mass; ship INI can override it.
    size2 = (hi-lo)**2
    inertia = (size2.sum()-size2)/12
    S.pack_into('<3f3ffII3f', data, 0, 0, 0, 0, *inertia, radius,
                (len(data) << 8) | 250, nodes_start, 0, 0, 0)
    return bytes(data), lo, hi


def transformed_hulls(name, parts, own):
    result = list(own[name])
    for p in parts.values():
        if p.parent == name:
            for h in transformed_hulls(p.name, parts, own):
                result.append(Hull(h.points @ p.rotation + p.translation, h.faces, h.hull_id))
    return result


def build(path, output, slab_length, recipe):
    parts = read_cmp(path)
    source_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    spec = recipe.get(path.name, {})
    if spec and spec['source_sha256'] != source_hash:
        raise ValueError('Model changed: review the geometry-specific hull regions before rebuilding')
    own = {name: hulls_for(p, slab_length, spec.get('regions', {}).get(name)) for name, p in parts.items()}
    root_name = next(p.name for p in parts.values() if p.parent is None)
    out = bytearray(b'vers' + S.pack('<f', 2.0))
    report = {'source': str(path), 'source_sha256': source_hash,
              'approximation': 'convex hull of clipped render triangles per axial slab',
              'region_override': spec,
              'slab_length': slab_length, 'parts': [], 'coupling_hardpoints_present': False}
    for name, p in parts.items():
        hulls = transformed_hulls(name, parts, own)
        surface, lo, hi = encode_surface(hulls)
        out.extend(S.pack('<II', utf.crc(name), 3 if p.parent is None else 2))
        if p.parent is None:
            out.extend(b'!fxd')
        out.extend(b'exts' + S.pack('<6f', *lo, *hi))
        out.extend(b'surf' + S.pack('<I', len(surface)) + surface)
        report['parts'].append({'name': name, 'id': utf.crc(name), 'parent': p.parent,
                                'triangles': len(p.triangles), 'hulls': len(hulls),
                                'bounds_min': lo.tolist(), 'bounds_max': hi.tolist(),
                                'hardpoints': p.hardpoints})
    output.mkdir(parents=True, exist_ok=True)
    target = output / (path.stem + '.sur')
    if target.resolve() == path.with_suffix('.sur').resolve():
        raise ValueError('Output must be staged outside the source directory')
    target.write_bytes(out)
    (output / path.name).write_bytes(path.read_bytes())
    report['sur_sha256'] = hashlib.sha256(out).hexdigest()
    report['sur_bytes'] = len(out)
    (output / (path.stem + '.json')).write_text(json.dumps(report, indent=2), encoding='utf-8')
    preview(path.stem, parts, own, root_name, output)
    print(json.dumps({'file': str(target), 'parts': [(p['name'], p['hulls']) for p in report['parts']],
                      'bytes': len(out)}))


def preview(name, parts, own, root_name, output):
    from PIL import Image, ImageDraw
    hulls = transformed_hulls(root_name, parts, own)
    def render_tris(n):
        t = [parts[n].triangles]
        for p in parts.values():
            if p.parent == n:
                t.append(render_tris(p.name) @ p.rotation + p.translation)
        return np.concatenate(t)
    triangles = render_tris(root_name)
    canvas = Image.new('RGB', (1400, 1000), '#f5f7fa')
    draw = ImageDraw.Draw(canvas)
    draw.text((25, 15), name + ': render mesh (gray), collision hull outlines (orange)', fill='#172b44')
    for row, ((a, b), title) in enumerate(zip([(2, 0), (2, 1), (0, 1)], ['Top Z/X', 'Side Z/Y', 'Front X/Y'])):
        xy = triangles[:, :, [a, b]].reshape(-1, 2)
        lo, hi = xy.min(axis=0), xy.max(axis=0)
        scale = min(1280/(hi[0]-lo[0]), 250/(hi[1]-lo[1]))
        center = (lo+hi)/2
        def screen(p):
            q = (p-center)*scale
            return [(float(x+700), float(200+row*310-y)) for x, y in q]
        draw.text((25, 55+row*310), title, fill='#172b44')
        for tri in triangles:
            draw.polygon(screen(tri[:, [a, b]]), fill='#a0a8b2')
        for h in hulls:
            points = h.points[:, [a, b]]
            boundary = points[ConvexHull(points).vertices]
            outline = screen(boundary)
            draw.line(outline+[outline[0]], fill='#d84c20', width=2)
    canvas.save(output / (name + '_collision.png'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('models', type=Path, nargs='+')
    parser.add_argument('--output', type=Path, default=ROOT / 'out/train_sur')
    parser.add_argument('--slab-length', type=float, default=12.0)
    parser.add_argument('--recipe', type=Path, default=Path(__file__).with_name('regions.json'))
    args = parser.parse_args()
    if args.slab_length <= 0:
        parser.error('slab length must be positive')
    for path in args.models:
        build(path, args.output, args.slab_length, json.loads(args.recipe.read_text()))


if __name__ == '__main__':
    main()
