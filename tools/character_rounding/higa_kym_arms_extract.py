"""Extract ku_kym_body sleeves exactly. Hands are not in this body."""
import gzip
import hashlib
import io
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hatcher_hair'))
import contours as c
from hands import skeleton

OUT = c.ROOT / 'out/character_rounding/higa/kym_arms'
SRC = c.GAME / 'DATA/CHARACTERS/BODIES/ku_kym_body.dfm'
ARM = {'LUpArm', 'RUpArm', 'LLowArm', 'RLowArm'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'textures').mkdir(exist_ok=True)
    root = c.read_tree(SRC.read_bytes())[1][0]
    bones = skeleton(root)
    names = [b['name'] for b in bones]
    records, groups, face_sets = c.as_records(root)
    arm_weight = np.zeros(len(records))
    weights = np.zeros((len(records), len(names)), np.float32)
    for i, record in enumerate(records):
        for key, value in record['skin'].items():
            weights[i, int(key)] = value
            if names[int(key)] in ARM:
                arm_weight[i] += value
    arm_vert = arm_weight > 0.5
    kept_faces = []
    materials = []
    for group, faces in zip(groups, face_sets):
        name = c.blob(group, 'Material_name').rstrip(b'\0').decode()
        mat = next(n for n in c.child(root, 'Material library').children if n.name.lower() == name.lower())
        texture_name = next((n.blob.rstrip(b'\0').decode() for n in mat.children if n.name == 'Dt_name'), None)
        texpath = None
        if texture_name:
            tex = next(n for n in c.child(root, 'Texture library').children if n.name.lower() == texture_name.lower())
            payload = next(n.blob for n in tex.children if n.name in ('MIP0', 'MIPS'))
            texpath = OUT / 'textures' / (hashlib.sha256(payload).hexdigest()[:16] + '.png')
            if not texpath.exists():
                Image.open(io.BytesIO(payload)).save(texpath)
        selected = [face for face in faces if sum(arm_vert[i] for i in face) >= 2]
        if not selected:
            continue
        materials.append({'name': name, 'texture': str(texpath) if texpath else None, 'faces': selected})
        kept_faces.extend(selected)
    used = sorted({i for face in kept_faces for i in face})
    mapping = {old: new for new, old in enumerate(used)}
    points = np.array([records[i]['p'] for i in used], np.float32)
    normals = np.array([records[i]['n'] for i in used], np.float32)
    uv = np.array([records[i]['uv'] for i in used], np.float32)
    skin = weights[used]
    # Cut anything below the wrist cuff. Kym has no hand mesh; this only drops a stray.
    cuff = points[:, 1] > -0.04
    faces_out = []
    face_mat = []
    for mat_i, mat in enumerate(materials):
        for face in mat['faces']:
            if all(cuff[mapping[i]] for i in face):
                faces_out.append([mapping[i] for i in face])
                face_mat.append(mat_i)
    np.savez_compressed(
        OUT / 'arms.npz', points=points, normals=normals, uv=uv, weights=skin,
        faces=np.array(faces_out, np.int32), face_material=np.array(face_mat, np.int32),
        bone_names=np.array(names))
    (OUT / 'materials.json').write_text(json.dumps([
        {'name': m['name'], 'texture': m['texture']} for m in materials], indent=2), encoding='utf8')
    print('arm verts', len(used), 'faces', len(faces_out), 'materials', [m['name'] for m in materials])


if __name__ == '__main__':
    main()
