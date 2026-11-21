"""Compare standard female head mounts on Kym gen and Kaitlyn bodies."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hatcher_hair'))
import contours as c
from hands import skeleton


def report(rel):
    path = c.GAME / 'DATA/CHARACTERS' / rel
    root = c.read_tree(path.read_bytes())[1][0]
    bones = skeleton(root)
    names = {
        c.blob(n, 'File name').rstrip(b'\0').decode(): c.blob(n, 'Object name').rstrip(b'\0').decode()
        for n in c.child(root, 'Cmpnd').children if any(x.name == 'File name' for x in n.children)
    }
    print('==', rel, 'bones', len(bones))
    resources = [n for n in root.children if n.name.lower().endswith('.3db')]
    for bone, node in zip(bones, resources):
        hp = next((x for x in node.children if x.name == 'Hardpoints'), None)
        if not hp:
            continue
        packed = np.array(bone['native_bind'])
        inverse = np.eye(4)
        inverse[:3, :3] = packed[:9].reshape(3, 3)
        inverse[:3, 3] = packed[9:]
        bind = np.linalg.inv(inverse)
        for kind in hp.children:
            for point in kind.children:
                mat = np.eye(4)
                mat[:3, :3] = c.arr(point, 'Orientation', '<f4', 3)
                mat[:3, 3] = c.arr(point, 'Position', '<f4').ravel()
                world = bind @ mat
                print(bone['name'], point.name, 'world', np.round(world[:3, 3], 4).tolist())
    mesh = c.child(c.child(root, 'MultiLevel'), 'Mesh0')
    pts = c.arr(c.child(mesh, 'Geometry'), 'Points', '<f4', 3)
    print('mesh0', len(pts), 'ymax', round(float(pts[:, 1].max()), 4), 'neckband',
          int(((pts[:, 1] > 0.45) & (np.abs(pts[:, 0]) < 0.08)).sum()))


if __name__ == '__main__':
    report('BODIES/ku_kym_body_gen.dfm')
    report('BODIES/br_kaitlyn_body.dfm')
    report('HEADS/ku_kym_head_gen.dfm')
    report('HEADS/pl_female4_head.dfm')
