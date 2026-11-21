"""See whether Kym gen and Kaitlyn share the female skeleton."""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hatcher_hair'))
import contours as c
from hands import skeleton


def joints(rel):
    root = c.read_tree((c.GAME / 'DATA/CHARACTERS' / rel).read_bytes())[1][0]
    out = {}
    for bone in skeleton(root):
        packed = np.array(bone['native_bind'])
        inverse = np.eye(4)
        inverse[:3, :3] = packed[:9].reshape(3, 3)
        inverse[:3, 3] = packed[9:]
        out[bone['name']] = np.linalg.inv(inverse)[:3, 3]
    return out


if __name__ == '__main__':
    a = joints('BODIES/br_kaitlyn_body.dfm')
    b = joints('BODIES/ku_kym_body_gen.dfm')
    print('same names', set(a) == set(b))
    for name in a:
        if name not in b:
            print('missing', name)
            continue
        delta = np.linalg.norm(a[name] - b[name])
        if delta > 1e-4:
            print(name, 'delta', round(float(delta), 5), a[name].round(4), b[name].round(4))
    print('max delta', max(np.linalg.norm(a[n] - b[n]) for n in a if n in b))
