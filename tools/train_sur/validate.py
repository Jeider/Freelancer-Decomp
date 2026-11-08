"""Independent readback: serialized hulls cover mesh samples and preserve cargo gap."""
from pathlib import Path
import json
import struct as S
import sys

import numpy as np
from scipy.spatial import ConvexHull

import build
sys.path.insert(0, str(build.ROOT / 'tools/tradelane'))
from docking_surface import parts as read_sur


def leaf_hulls(surface):
    root = S.unpack_from('<i', surface, 32)[0]
    result = []
    def walk(offset):
        right, ledge = S.unpack_from('<ii', surface, offset)
        if right:
            walk(offset+28)
            walk(offset+right)
            return
        start = offset+ledge
        poff, hull_id, flags, count, unused = S.unpack_from('<iIIHH', surface, start)
        indices = set()
        for f in range(count):
            for e in range(3):
                indices.add(S.unpack_from('<H', surface, start+16+f*16+4+e*4)[0])
        vertices = np.array([S.unpack_from('<3f', surface, start+poff+i*16) for i in sorted(indices)])
        result.append((hull_id, ConvexHull(vertices)))
    walk(root)
    return result


def ray_hits(hulls, origin, direction):
    for _, hull in hulls:
        near, far = 0.0, float('inf')
        for eq in hull.equations:
            a = float(eq[:3] @ direction)
            b = float(eq[:3] @ origin + eq[3])
            if abs(a) < 1e-10:
                if b > 0:
                    far = -1
                    break
            elif a < 0:
                near = max(near, -b/a)
            else:
                far = min(far, -b/a)
        if far >= near:
            return True
    return False


def validate(path):
    parts = build.read_cmp(path.with_suffix('.cmp'))
    decoded = {pid: leaf_hulls(dict(chunks)[b'surf']) for pid, chunks in read_sur(path.read_bytes())}
    assert set(decoded) == {build.utf.crc(name) for name in parts}
    sample_count = 0
    for name, part in parts.items():
        tris = part.triangles
        samples = np.concatenate([tris.reshape(-1, 3), tris.mean(axis=1),
                                  ((tris+np.roll(tris, 1, axis=1))/2).reshape(-1, 3)])
        # Include all fixed descendants, transformed independently at every ancestor.
        ancestor = part
        while True:
            hulls = decoded[build.utf.crc(ancestor.name)]
            coverage = np.zeros(len(samples), dtype=bool)
            for hull_id, hull in hulls:
                if hull_id == build.utf.crc(name):
                    coverage |= np.all(samples @ hull.equations[:, :3].T + hull.equations[:, 3] <= .002, axis=1)
            assert np.all(coverage), (name, ancestor.name, samples[~coverage][:3])
            sample_count += len(samples)
            if ancestor.parent is None:
                break
            samples = samples @ ancestor.rotation + ancestor.translation
            ancestor = parts[ancestor.parent]
    rays = None
    if path.stem == 'train_cargo':
        root = decoded[build.utf.crc('Root')]
        direction = np.array([0., 1., 0.])
        # Real empty frame opening: shoot vertically through the middle of the wagon.
        assert not ray_hits(root, np.array([-.1, -50., 21.]), direction)
        assert ray_hits(root, np.array([-5., -50., 21.]), direction)
        assert ray_hits(root, np.array([4.8, -50., 21.]), direction)
        rays = 'central opening misses; both side rails hit'
    return {'file': path.name, 'mesh_samples_covered': sample_count, 'ray_checks': rays}


if __name__ == '__main__':
    folder = build.ROOT / 'out/train_sur'
    results = [validate(folder / name) for name in ('train_car.sur', 'train_cargo.sur')]
    (folder / 'validation.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results))
