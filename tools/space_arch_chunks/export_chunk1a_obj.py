"""Export arch_ast1 triangles for an offline Blender preview. No game writes."""
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
from generate_station_lods import read_tree
from repair_panel_normals import triangles

SOURCE = Path(r"D:\Games\FL_MOD\DATA\SOLAR\MISC\arch_ast1.3db")
OUT = ROOT / "out" / "space_arch_chunks" / "chunk1a"


def load():
    _, roots = read_tree(SOURCE.read_bytes())

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
    rows = []
    for (material, _, _), group in zip(descriptors, groups):
        for corner in group:
            px, py, pz, nx, ny, nz, u, v = struct.unpack("<8f", corner)
            rows.append((material, px, py, pz, nx, ny, nz, u, v))
    return np.array(rows, dtype=np.float64)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    data = load()
    points = data[:, 1:4]
    lo, hi = points.min(0), points.max(0)
    center = (lo + hi) / 2
    extent = hi - lo
    # Principal axes of the visible mass, for the redesign, not a replacement mesh.
    centered = points - points.mean(0)
    _, axes = np.linalg.eigh(centered.T @ centered)
    print("bbox_min", [round(float(v), 1) for v in lo])
    print("bbox_max", [round(float(v), 1) for v in hi])
    print("center", [round(float(v), 1) for v in center])
    print("extent", [round(float(v), 1) for v in extent])
    print("axes", np.round(axes, 3).tolist())
    lines = ["o arch_ast1"]
    for material, px, py, pz, nx, ny, nz, u, v in data:
        lines.append(f"v {px:.5f} {pz:.5f} {-py:.5f}")
        lines.append(f"vn {nx:.5f} {nz:.5f} {-ny:.5f}")
        lines.append(f"vt {u:.5f} {v:.5f}")
    count = len(data)
    for index in range(0, count, 3):
        a, b, c = index + 1, index + 2, index + 3
        lines.append(f"f {a}/{a}/{a} {b}/{b}/{b} {c}/{c}/{c}")
    target = OUT / "arch_ast1_source.obj"
    target.write_text("\n".join(lines) + "\n", encoding="ascii")
    print("obj", target, "corners", count)


if __name__ == "__main__":
    main()
