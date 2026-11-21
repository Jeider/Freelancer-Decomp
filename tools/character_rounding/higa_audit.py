"""Read-only audit of the Kaitlyn body used as the Higa construction base."""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'hatcher_hair'))
import contours as c
from hands import skeleton

OUT = c.ROOT / 'out/character_rounding/higa'
BODY = c.GAME / 'DATA/CHARACTERS/BODIES/br_kaitlyn_body.dfm'


def main():
    raw = BODY.read_bytes()
    root = c.read_tree(raw)[1][0]
    bones = skeleton(root)
    bone_rows = []
    for i, bone in enumerate(bones):
        inverse = np.eye(4)
        packed = np.array(bone['native_bind'])
        inverse[:3, :3] = packed[:9].reshape(3, 3)
        inverse[:3, 3] = packed[9:]
        bind = np.linalg.inv(inverse)
        bone_rows.append({
            'index': i,
            'name': bone['name'],
            'parent': bone['parent'],
            'position': bind[:3, 3].round(5).tolist(),
        })
    ml = c.child(root, 'MultiLevel')
    lods = []
    for node in ml.children:
        if not node.name.startswith('Mesh'):
            continue
        records, groups_raw, face_sets = c.as_records(root) if node.name == 'Mesh0' else (None, None, None)
        geo = c.child(node, 'Geometry')
        points = c.arr(geo, 'Points', '<f4', 3)
        groups = []
        if records is not None:
            positions = np.array([r['p'] for r in records])
            for group, faces in zip(groups_raw, face_sets):
                used = positions[[i for tri in faces for i in tri]]
                groups.append({
                    'name': c.blob(group, 'Material_name').rstrip(b'\0').decode(),
                    'triangles': len(faces),
                    'bounds': [used.min(0).round(4).tolist(), used.max(0).round(4).tolist()],
                })
        else:
            groups.append({'name': 'deferred', 'triangles': sum(len(c.triangles(g)) for g in c.child(node, 'Face_groups').children if g.children)})
        lods.append({
            'name': node.name,
            'points': len(points),
            'triangles': sum(g['triangles'] for g in groups),
            'bounds': [points.min(0).round(4).tolist(), points.max(0).round(4).tolist()],
            'groups': groups,
        })
    materials = []
    for node in c.child(root, 'Material library').children:
        if node.name == 'Material count':
            continue
        texture = next((child.blob.rstrip(b'\0').decode() for child in node.children if child.name == 'Dt_name'), None)
        materials.append({'name': node.name, 'texture': texture})
    report = {
        'source': str(BODY),
        'bytes': len(raw),
        'bones': bone_rows,
        'lods': lods,
        'materials': materials,
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'kaitlyn_audit.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps({
        'bones': [(b['index'], b['name'], b['position']) for b in bone_rows],
        'lod0_groups': lods[0]['groups'],
        'lod_counts': [(n['name'], n['points'], n['triangles']) for n in lods],
    }, indent=2))


if __name__ == '__main__':
    main()
