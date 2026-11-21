"""Extract rounded pl_female1_peasant_body sleeves and copy native skin weights."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hatcher_hair'))
import contours as c
from hands import skeleton

OUT = c.ROOT / 'out/character_rounding/higa/peasant_arms'
SRC = c.GAME / 'DATA/CHARACTERS/BODIES/pl_female1_peasant_body.dfm'
ROUNDED = c.ROOT / 'out/character_rounding/all_bodies/pl_female1_peasant_body/after.json'
ARM = {'LUpArm', 'RUpArm', 'LLowArm', 'RLowArm'}


def main():
    root = c.read_tree(SRC.read_bytes())[1][0]
    names = [b['name'] for b in skeleton(root)]
    records, _, _ = c.as_records(root)
    native = np.array([r['p'] for r in records], np.float32)
    native_w = np.zeros((len(records), len(names)), np.float32)
    for i, record in enumerate(records):
        for key, value in record['skin'].items():
            native_w[i, int(key)] = value
    raw = json.loads(ROUNDED.read_text(encoding='utf8'))
    points = np.array(raw['points'], np.float32)
    nearest = np.empty(len(points), np.int32)
    for i in range(0, len(points), 400):
        delta = points[i:i + 400, None, :] - native[None, :, :]
        nearest[i:i + 400] = np.linalg.norm(delta, axis=2).argmin(1)
    weights = native_w[nearest]
    arm = {names.index(name) for name in ARM}
    dominant = weights.argmax(1)
    materials, faces, face_mat = [], [], []
    for group in raw['groups']:
        selected = [face for face in group['faces'] if sum(int(dominant[i] in arm) for i in face) >= 2 and min(points[i][1] for i in face) > -0.045]
        if not selected:
            continue
        materials.append({'name': group['name'], 'texture': group['texture']})
        faces.extend(selected)
        face_mat.extend([len(materials) - 1] * len(selected))
    used = sorted({i for face in faces for i in face})
    mapping = {old: new for new, old in enumerate(used)}
    np.savez_compressed(
        OUT / 'arms.npz',
        points=points[used],
        normals=np.array(raw['normals'], np.float32)[used],
        uv=np.array(raw['uv'], np.float32)[used],
        weights=weights[used],
        faces=np.array([[mapping[i] for i in face] for face in faces], np.int32),
        face_material=np.array(face_mat, np.int32),
        bone_names=np.array(names))
    (OUT / 'materials.json').write_text(json.dumps(materials, indent=2), encoding='utf8')
    print('verts', len(used), 'faces', len(faces), 'y', float(points[used, 1].min()), float(points[used, 1].max()))


if __name__ == '__main__':
    main()
