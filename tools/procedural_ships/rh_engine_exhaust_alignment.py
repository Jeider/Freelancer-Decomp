"""Place RH fighter/freighter exhaust HPs on their actual nozzle grilles.

Offline CMP patch only. Preserve every other leaf, except fresh private export
identities. Use the installed accepted meshes and the matching edited reviews.
"""
import copy
import hashlib
import json
from pathlib import Path
import secrets
import struct
import sys

sys.dont_write_bytecode = True
import numpy as np
import rh_freighter_final as d
from rh_pir_elite_build import salt_tree
from ship_collision_audit import sur_parts, surface

f = d.f
GAP = 0.005
KEYS = {'hpengine01', 'hpengine02', 'hpengineglow'}
ROOTS = {
    'rh_pir_fighter': d.ROOT / 'out/ship_design/rh_fighter/rh_pir_fighter',
    'rh_pir_freighter': d.OUT,
}


def nozzle_targets(nodes, pose=('Sc_extend wing', 0)):
    """Area-weighted centers of the actual planar engine_grill01 faces."""
    hp = d.hardpoints(nodes, pose)
    geometry = d.world(nodes, pose)
    targets, evidence = {}, {}
    for key in ('hpengine01', 'hpengine02'):
        h = hp[key]
        triangles = np.concatenate([g['corners'][..., :3] for g in geometry[h['owner']]
                                    if g['material'] == f.mesh.crc('engine_grill01')])
        cross = np.cross(triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0])
        area = np.linalg.norm(cross, axis=1)
        center = np.average(triangles.mean(1), weights=area, axis=0)
        normal = cross.sum(0)
        normal /= np.linalg.norm(normal)
        assert np.ptp(triangles.reshape(-1, 3) @ normal) < 1e-5, 'Nozzle is not planar'
        assert np.dot(normal, h['orientation'][:, 2]) > 0.9999, 'Check nozzle direction'
        targets[key] = center + normal * GAP
        evidence[key] = dict(owner=h['owner'], grille_center=center, grille_normal=normal,
                             grille_triangles=len(triangles), before=h['position'], after=targets[key],
                             before_gap=float(np.dot(h['position'] - center, normal)), after_gap=GAP)
    targets['hpengineglow'] = (targets['hpengine01'] + targets['hpengine02']) * 0.5
    evidence['hpengineglow'] = dict(owner=hp['hpengineglow']['owner'], before=hp['hpengineglow']['position'],
                                    after=targets['hpengineglow'], placement='midpoint of nozzle exhaust points')
    return targets, evidence


def patch_positions(nodes, targets, pose=('Sc_extend wing', 0)):
    """Edit only Position leaves; no HP recreation or orientation round trips."""
    transforms, _ = f.audit.transforms(nodes, pose)
    changed = []
    for file in f.component_map(nodes):
        part = f.mesh.child(nodes[0], file)
        r, t = transforms[file.lower()]
        for path, node in f.mesh.walk([part]):
            components = path.lower().split('/')
            if components[-1] != 'position' or 'hardpoints' not in components:
                continue
            if components[-2] in targets:
                node.blob = np.array(r.T @ (targets[components[-2]] - t), '<f4').tobytes()
                changed.append(components[-2])
    assert set(changed) == KEYS and len(changed) == 3


def check_exact(before, after, mapping, targets, pose):
    """Reverse the salt in a verification copy, then compare every leaf byte."""
    normalized = copy.deepcopy(after)
    reverse = {new: old for old, new in mapping.items()}
    crc_reverse = {f.mesh.crc(new): f.mesh.crc(old) for old, new in mapping.items() if old.endswith('.vms')}
    for path, node in f.mesh.walk(normalized):
        if path.lower().endswith(('/vmeshref', '/vwiredata')):
            raw = bytearray(node.blob)
            struct.pack_into('<I', raw, 4, crc_reverse[struct.unpack_from('<I', raw, 4)[0]])
            node.blob = bytes(raw)
        if node.name.lower() == 'file name':
            old = f.mesh.string(node.blob)
            if old in reverse:
                node.blob = reverse[old].encode() + b'\0'
    def restore_names(items):
        for node in items:
            if node.name in reverse:
                node.name = reverse[node.name]
            if node.children:
                restore_names(node.children)
    restore_names(normalized)
    flatten = lambda ns: {p: n.blob for p, n in f.mesh.walk(ns) if not n.children}
    a, b = flatten(before), flatten(normalized)
    assert a.keys() == b.keys()
    changed = [p for p in a if a[p] != b[p]]
    assert len(changed) == 3 and {p.lower().split('/')[-2] for p in changed} == KEYS
    assert all(p.lower().endswith('/position') for p in changed)
    ahp, bhp = d.hardpoints(before, pose), d.hardpoints(after, pose)
    assert ahp.keys() == bhp.keys()
    for key in ahp:
        assert ahp[key]['owner'] == bhp[key]['owner']
        assert np.array_equal(ahp[key]['orientation'], bhp[key]['orientation'])
        expected = targets[key] if key in KEYS else ahp[key]['position']
        assert np.allclose(bhp[key]['position'], expected, atol=2e-6, rtol=0), key
    return dict(changed_leaves=changed, unchanged_hardpoints=len(ahp) - 3,
                geometry_uv_lods_wire_animation_identical=True, orientations_and_owners_identical=True)


def run(ship):
    root = ROOTS[ship]
    out = root / 'exhaust_alignment'
    out.mkdir(exist_ok=True)
    live = d.GAME / 'DATA/ships/rheinland' / ship / (ship + '.cmp')
    review = root / (('hold_repair/' if ship.endswith('freighter') else '') + ship + '_review_open.cmp')
    _, nodes = d.tree(live)
    targets, evidence = nozzle_targets(nodes)
    # Keep all accepted manual HP changes; reject stale review copies.
    original_hp = d.hardpoints(nodes, ('Sc_extend wing', 0))
    _, review_nodes = d.tree(review)
    review_hp = d.hardpoints(review_nodes)
    assert original_hp.keys() == review_hp.keys()
    for key, h in original_hp.items():
        assert h['owner'] == review_hp[key]['owner']
        assert np.allclose(h['position'], review_hp[key]['position'], atol=2e-5, rtol=0), key
        assert np.allclose(h['orientation'], review_hp[key]['orientation'], atol=2e-5, rtol=0), key
    sur = live.with_suffix('.sur')
    ids = set()
    for part, chunks in sur_parts(sur.read_bytes()):
        ids.add(part)
        for tag, blob in chunks:
            if tag == b'hpid':
                ids.update(np.frombuffer(blob, '<u4').tolist())
            elif tag == b'surf':
                ids.update(h['client'] for h in surface(blob)['hulls'])
    assert all(f.mesh.crc(n) not in ids for n in KEYS), 'Exhaust has an embedded collision hull'
    files = {}
    for source, pose in ((live, ('Sc_extend wing', 0)), (review, None)):
        header, before = d.tree(source)
        changed = copy.deepcopy(before)
        patch_positions(changed, targets, pose)
        salt = secrets.token_hex(6)
        mapping = salt_tree(changed, salt)
        target = out / source.name
        target.write_bytes(f.mesh.write_tree(header, changed))
        _, saved = d.tree(target)
        checks = check_exact(before, saved, mapping, targets, pose)
        if pose:
            for time in (0, 1, 2):
                current = d.hardpoints(saved, ('Sc_extend wing', time))
                assert all(np.allclose(current[k]['position'], targets[k], atol=2e-6, rtol=0) for k in KEYS)
        files[source.name] = dict(path=str(target), source=str(source), source_sha256=f.digest(source),
                                 sha256=f.digest(target), export_salt=salt, private_resources=mapping, checks=checks)
    report = dict(model=ship, installed=False, files=files, changes=evidence, nozzle_clearance=GAP,
                  unchanged_sur=dict(path=str(sur), sha256=f.digest(sur), exhaust_has_embedded_hull=False),
                  shared_mat=dict(path=str(d.MAT), sha256=f.digest(d.MAT)),
                  policy='Offline HP patch. Game DATA and Pythonlancer source assets were not written.')
    d.dump(out / 'manifest.json', report)
    text = [f'# {ship}: точки выхлопа у сопел', '',
            'Только три HP: HpEngine01, HpEngine02 и общая HpEngineGlow. Зазор до решётки — 0,005.',
            'Взяты текущие принятые игровые CMP; все остальные HP сохранены побайтно.',
            'Геометрия, UV, LOD, анимация и вайрфрейм идентичны. Для экспортов создана новая соль.',
            'SUR сохраняется: у этих трёх точек нет встроенных коллизионных оболочек.', '',
            '| HP | Было X/Y/Z | Стало X/Y/Z |', '|---|---|---|']
    for key, e in evidence.items():
        fmt = lambda v: ', '.join(f'{x:.6f}' for x in v)
        text.append(f"| {key} | {fmt(e['before'])} | {fmt(e['after'])} |")
    text += ['', '## Файлы', '']
    for info in files.values():
        p = Path(info['path']).as_posix()
        text.append(f'- [{p}]({p})')
    text += ['', 'Комплект офлайн. В игре пока предыдущие CMP. Конфиги и материалы менять не нужно.',
             'При следующей полной сборке использовать обновлённый review_open как источник HP.',
             'Для freighter также заменить CMP в источнике Pythonlancer и обновить его manifest при разрешённой установке.', '']
    (out / 'README.md').write_text('\n'.join(text), encoding='utf8')
    print(ship, 'READY:', str(out / (ship + '.cmp')), flush=True)
    print('  untouched HP:', len(original_hp) - 3, '; nozzle gap:', GAP, '; all other data checked byte-for-byte', flush=True)


if __name__ == '__main__':
    for model in ROOTS:
        run(model)
