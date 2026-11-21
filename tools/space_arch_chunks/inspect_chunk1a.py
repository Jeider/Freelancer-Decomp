"""Read-only shape notes for arch_ast1. Does not write game files."""
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from repair_panel_normals import triangles
from generate_station_lods import read_tree

SOURCE = Path(r"D:\Games\FL_MOD\DATA\SOLAR\MISC\arch_ast1.3db")


def mesh(path):
    _, roots = read_tree(path.read_bytes())

    def find(nodes, name):
        for node in nodes:
            if node.name == name:
                return node
            hit = find(node.children, name)
            if hit:
                return hit
        return None

    blob = find(roots, "VMeshData").blob
    _, descriptors, groups = triangles(blob)
    corners = []
    materials = []
    for (material, _, _), group in zip(descriptors, groups):
        for corner in group:
            px, py, pz, nx, ny, nz, u, v = struct.unpack("<8f", corner)
            corners.append((px, py, pz, nx, ny, nz, u, v))
            materials.append(material)
    data = np.array(corners, dtype=np.float64)
    return data.reshape(-1, 3, 8), np.array(materials[::3])


def main():
    faces, materials = mesh(SOURCE)
    points = faces[:, :, :3]
    flat = points.reshape(-1, 3)
    lo, hi = flat.min(0), flat.max(0)
    center = (lo + hi) / 2
    radius = np.linalg.norm(flat - center, axis=1).max()
    edges = {}
    for tri in np.round(points, 3):
        for a, b in ((0, 1), (1, 2), (2, 0)):
            key = tuple(sorted((tuple(tri[a]), tuple(tri[b]))))
            edges[key] = edges.get(key, 0) + 1
    boundary = sum(count == 1 for count in edges.values())
    area = 0.0
    for tri in points:
        area += np.linalg.norm(np.cross(tri[1] - tri[0], tri[2] - tri[0])) * 0.5
    print("triangles", len(faces), "materials", {hex(int(m)): int((materials == m).sum()) for m in set(materials)})
    print("extent", [round(float(v), 1) for v in hi - lo], "radius", round(float(radius), 1))
    print("center", [round(float(v), 1) for v in center], "boundary_edges", boundary, "area", round(float(area), 1))


if __name__ == "__main__":
    main()
