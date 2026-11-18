"""Return Lutz's misclassified forehead triangles to native skin shading."""
import argparse
from collections import Counter
from datetime import datetime
import hashlib
import json
import subprocess
import numpy as np

from build import ROOT, GAME, DataFolder, read_tree, write_tree, child, blob, arr, faces, triangles
from repair_panel_normals import leaves
from short_hair import BOUNDARIES

OUT = ROOT / 'out/hair_lighting/lutz'
REL = 'CHARACTERS/HEADS/rh_sales_head.dfm'
SKIN = 'rh_sales_head01'
HAIR = 'short_hair_' + SKIN
digest = lambda data: hashlib.sha256(data).hexdigest()


def inside(coords):
    for a in range(5):
        for b in range(5-a):
            u, v = (coords[0]*a + coords[1]*b + coords[2]*(4-a-b))/4
            if not (0 <= u <= 1 and 0 <= v <= 1):
                return False
            limit = np.interp(u, [0,.16,.22,.29,.40,.50,.60,.71,.78,.84,1], BOUNDARIES[58])
            if 1-v > limit-.008:
                return False
    return True


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    source = (GAME/'DATA'/REL).read_bytes()
    header, roots = read_tree(source)
    root = roots[0]
    rows = []
    for mesh in child(root, 'MultiLevel').children:
        if not mesh.name.startswith('Mesh'):
            continue
        groups = child(mesh, 'Face_groups')
        skin = next(g for g in groups.children if g.children and blob(g, 'Material_name').rstrip(b'\0').decode() == SKIN)
        hair = next(g for g in groups.children if g.children and blob(g, 'Material_name').rstrip(b'\0').decode() == HAIR)
        geo = child(mesh, 'Geometry')
        uv = arr(geo, 'UV0', '<f4', 2)
        ui = arr(geo, 'UV0_indices', '<u4').ravel()
        before = Counter(tuple(t) for g in groups.children if g.children for t in triangles(g))
        original_skin, original_hair = triangles(skin), triangles(hair)
        keep, restore = [], []
        for tri in original_hair:
            (keep if inside(uv[ui[tri]]) else restore).append(tri)
        if not keep:
            raise ValueError(f'No hair left at {mesh.name}')
        faces(skin, original_skin + restore)
        faces(hair, keep)
        after = Counter(tuple(t) for g in groups.children if g.children for t in triangles(g))
        assert before == after, mesh.name
        assert set(map(tuple, original_skin)).issubset(set(map(tuple, triangles(skin))))
        rows.append({'lod': mesh.name, 'hair_before': len(original_hair), 'hair_after': len(keep),
                     'returned_to_native': len(restore), 'all_triangles_preserved': True})
    data = write_tree(header, roots)
    old = {p: b for p, _, b in leaves(source)[1]}
    new = {p: b for p, _, b in leaves(data)[1]}
    for path, value in old.items():
        if '/Face_groups/' not in path:
            assert new[path] == value, path
    # No texture, UV, vertex, normal, material property, rig or animation changes.
    DataFolder(root=OUT/'original').sync_data_file(REL, source)
    DataFolder(root=OUT/'stage').sync_data_file(REL, data)
    report = {'file': REL, 'before': digest(source), 'after': digest(data),
              'boundary_method': 'Manually traced conservative hairline on current rh_sales atlas; whole triangles only',
              'geometry_textures_uv_normals_rig_unchanged': True, 'lods': rows}
    (OUT/'fix_manifest.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


def install():
    tasks = subprocess.run(['tasklist','/FO','CSV','/NH'], capture_output=True, check=True).stdout.lower()
    if any(b'"'+name+b'"' in tasks for name in (b'freelancer.exe', b'freelancer_window.exe', b'flserver.exe')):
        raise SystemExit('Game/server is running; prepared head retained without installation.')
    report = json.loads((OUT/'fix_manifest.json').read_text())
    assert report['file'] == REL
    live, stage = DataFolder(root=GAME), DataFolder(root=OUT/'stage')
    before, after = live.data_path(REL).read_bytes(), stage.data_path(REL).read_bytes()
    assert digest(before) == report['before'], 'Live head changed since preparation'
    assert digest(after) == report['after'], 'Staged head changed'
    backup = DataFolder(root=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    backup.sync_data_file(REL, before)
    assert digest(backup.data_path(REL).read_bytes()) == report['before']
    try:
        live.sync_data_file(REL, after)
        assert digest(live.data_path(REL).read_bytes()) == report['after']
    except BaseException:
        live.sync_data_file(REL, before)
        raise
    result = {'file': str(live.data_path(REL)), 'sha256': report['after'],
              'backup': str(backup.data_path(REL)), 'game_launched': False,
              'changed_game_files': [REL]}
    (OUT/'installed.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    install() if args.apply else prepare()
