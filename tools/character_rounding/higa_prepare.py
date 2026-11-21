"""Pin Kaitlyn body, head and hands for the Higa costume study. No game writes."""
import gzip
import hashlib
import io
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image

import contours as c
from hands import skeleton

OUT = c.ROOT / 'out/character_rounding/higa'
ASSETS = {
    'body': 'BODIES/br_kaitlyn_body.dfm',
    'head': 'HEADS/br_kaitlyn_head.dfm',
    'left_hand': 'HANDS/benchmarkfemalehandleft.dfm',
    'right_hand': 'HANDS/benchmarkfemalehandright.dfm',
}
ART = Path('D:/work/MESHY/higa1')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    assert shutil.disk_usage(c.ROOT).free > 3 * 1024 ** 3
    (OUT / 'source').mkdir(parents=True, exist_ok=True)
    (OUT / 'textures').mkdir(exist_ok=True)
    (OUT / 'art').mkdir(exist_ok=True)
    report = {'installed': False, 'native': {}, 'art': {}}
    for name in ('hg1.png', 'hg2.png'):
        src = ART / name
        dest = OUT / 'art' / name
        if not dest.exists() or digest(dest.read_bytes()) != digest(src.read_bytes()):
            shutil.copy2(src, dest)
        report['art'][name] = {'path': str(src), 'sha256': digest(src.read_bytes())}
    for label, rel in ASSETS.items():
        path = c.GAME / 'DATA/CHARACTERS' / rel
        raw = path.read_bytes()
        root = c.read_tree(raw)[1][0]
        snapshot = OUT / 'source' / path.name
        if snapshot.exists():
            assert digest(snapshot.read_bytes()) == digest(raw), label
        else:
            snapshot.write_bytes(raw)
        records, groups, faces = c.as_records(root)
        bones = skeleton(root)
        hardpoints = {}
        names = {c.blob(n, 'File name').rstrip(b'\0').decode(): c.blob(n, 'Object name').rstrip(b'\0').decode()
                 for n in c.child(root, 'Cmpnd').children if any(x.name == 'File name' for x in n.children)}
        resources = [n for n in root.children if n.name.lower().endswith('.3db')]
        for bone, node in zip(bones, resources):
            packed = np.array(bone['native_bind'])
            inverse = np.eye(4)
            inverse[:3, :3] = packed[:9].reshape(3, 3)
            inverse[:3, 3] = packed[9:]
            bind = np.linalg.inv(inverse)
            hp = next((n for n in node.children if n.name == 'Hardpoints'), None)
            if not hp:
                continue
            for kind in hp.children:
                for point in kind.children:
                    mat = np.eye(4)
                    mat[:3, :3] = c.arr(point, 'Orientation', '<f4', 3)
                    mat[:3, 3] = c.arr(point, 'Position', '<f4').ravel()
                    hardpoints[point.name] = {
                        'bone': bone['name'], 'kind': kind.name,
                        'matrix': (bind @ mat).tolist(), 'local': mat.tolist(),
                    }
        data = {
            'points': [r['p'].tolist() for r in records],
            'normals': [r['n'].tolist() for r in records],
            'uv': [r['uv'].tolist() for r in records],
            'skin': [r['skin'] for r in records],
            'bones': bones, 'hardpoints': hardpoints, 'groups': [],
            'source': str(path), 'sha256': digest(raw),
        }
        for group, group_faces in zip(groups, faces):
            name = c.blob(group, 'Material_name').rstrip(b'\0').decode()
            mat = next(n for n in c.child(root, 'Material library').children if n.name.lower() == name.lower())
            texture_name = next((n.blob.rstrip(b'\0').decode() for n in mat.children if n.name == 'Dt_name'), None)
            texpath = None
            if texture_name:
                tex = next(n for n in c.child(root, 'Texture library').children if n.name.lower() == texture_name.lower())
                payload = next(n.blob for n in tex.children if n.name in ('MIP0', 'MIPS'))
                texpath = OUT / 'textures' / (digest(payload)[:16] + '.png')
                if not texpath.exists():
                    Image.open(io.BytesIO(payload)).save(texpath)
            data['groups'].append({'name': name, 'texture': str(texpath) if texpath else None, 'faces': group_faces})
        packed = gzip.compress(json.dumps(data).encode(), mtime=0)
        (OUT / 'source' / (label + '.json.gz')).write_bytes(packed)
        report['native'][label] = {
            'path': str(path), 'sha256': digest(raw), 'bones': len(bones),
            'records': len(records), 'hardpoints': sorted(hardpoints),
            'groups': [g['name'] for g in data['groups']],
            'triangles': sum(len(g['faces']) for g in data['groups']),
        }
    (OUT / 'source_audit.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
