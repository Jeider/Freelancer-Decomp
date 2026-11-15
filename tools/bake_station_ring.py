"""Merge the 16 Yokohama trading-station parts into one small compound.

The dock core stays a separate solar. Each ring segment keeps the part's own
LOD switch, but every segment of the same loadout shares one mesh. Cargo-pod
geometry is appended to Level0 only, so the far dummy LOD is unchanged.
"""
from __future__ import annotations

from pathlib import Path
import struct as S
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import generate_station_lods as utf
import bake_compound as bake


DATA = Path(r'D:\Games\FL_MOD\DATA')
PART = DATA / 'SOLAR' / 'misc' / 'space_trade_station_part.3db'
TEMPLATE = Path(r'D:\Games\FL_MOD\Assets\Pythonlancer\templates\dockable\tekagi_megabase.py')
OUT = ROOT / 'out' / 'bake_compound'


def mesh_blob(root):
    lib = bake.one(root, 'VMeshLibrary')
    part = bake.one(root, 'VMeshPart')
    if part is None:
        level = bake.one(bake.one(root, 'MultiLevel'), 'Level0')
        part = bake.one(level, 'VMeshPart')
    ref = bake.one(part, 'VMeshRef').blob
    mesh_id = S.unpack_from('<I', ref, 4)[0]
    node = bake.library_meshes(root).get(mesh_id)
    if node is None and lib is not None:
        node = lib.children[0]
    return bake.one(node, 'VMeshData').blob


def read_mesh(blob):
    flags, prim, groups, count, fvf, vertices = S.unpack_from('<II4H', blob)
    if (flags, prim, fvf) != (1, 4, 0x112):
        raise ValueError('unsupported mesh')
    cursor = 0
    index_at = 16 + 12 * groups
    parsed = []
    for g in range(groups):
        mat, lo, hi, nidx, unused = S.unpack_from('<I4H', blob, 16 + 12 * g)
        ids = S.unpack_from('<' + 'H' * nidx, blob, index_at + 2 * cursor)
        parsed.append((mat, lo, hi, unused, ids))
        cursor += nidx
    vert_at = index_at + 2 * count
    verts = [blob[vert_at + 32 * i:vert_at + 32 * (i + 1)] for i in range(vertices)]
    return parsed, verts


def write_mesh(groups, verts):
    count = sum(len(ids) for *_, ids in groups)
    out = bytearray(S.pack('<II4H', 1, 4, len(groups), count, 0x112, len(verts)))
    cursor = 0
    index = bytearray()
    for mat, lo, hi, unused, ids in groups:
        out.extend(S.pack('<I4H', mat, lo, hi, len(ids), unused))
        index.extend(S.pack('<' + 'H' * len(ids), *ids))
        cursor += len(ids)
    out.extend(index)
    out.extend(b''.join(verts))
    return bytes(out)


def xform_vert(raw, rotation, translation):
    pos = rotation @ np.array(S.unpack_from('<3f', raw, 0)) + translation
    normal = rotation @ np.array(S.unpack_from('<3f', raw, 12))
    length = np.linalg.norm(normal)
    if length > 1e-8:
        normal = normal / length
    out = bytearray(raw)
    S.pack_into('<3f', out, 0, *pos)
    S.pack_into('<3f', out, 12, *normal)
    return bytes(out)


def append_mesh(groups, verts, blob, rotation, translation):
    added, source = read_mesh(blob)
    base = len(verts)
    for mat, lo, hi, unused, ids in added:
        groups.append((mat, base + lo, base + hi, unused, ids))
    verts.extend(xform_vert(v, rotation, translation) for v in source)


def cargo_equips(loadouts, equipment, name):
    spec = loadouts[name.lower()]
    found = []
    for line in spec.get('equip', []):
        nick, _, hp = line.partition(',')
        eq = equipment.get(nick.strip().lower())
        if not eq or eq.get('section') != 'cargopod' or 'da_archetype' not in eq:
            continue
        found.append((eq, hp.strip()))
    return found


def baked_level0(loadout, solars, equipment, loadouts):
    _, root = bake.load_model(PART)
    groups, verts = read_mesh(mesh_blob(root))
    # Stored groups use indices relative to lo. Rebase them onto absolute 0
    # before appending so a later writer can keep that rule.
    absolute = []
    for mat, lo, hi, unused, ids in groups:
        absolute.append((mat, lo, hi, unused, ids))
    hps = bake.hardpoints(root)
    hulls = list(bake.read_sur(PART.with_suffix('.sur')).get(0, []))
    for eq, hp in cargo_equips(loadouts, equipment, loadout):
        if hp.lower() not in hps:
            continue
        path = bake.model_path(DATA, eq['da_archetype'][0])
        _, child = bake.load_model(path)
        anchor = eq.get('hp_child', ['HpRoot'])[0].lower()
        placed = bake.compose(hps[hp.lower()], bake.inverse(
            bake.hardpoints(child).get(anchor, (np.eye(3), np.zeros(3)))))
        append_mesh(absolute, verts, mesh_blob(child), *placed)
        for cloud in bake.read_sur(path.with_suffix('.sur')).get(0, []):
            if getattr(cloud, 'ndim', 0) == 2 and len(cloud) >= 3:
                hulls.append(cloud @ placed[0].T + placed[1])
    return write_mesh(absolute, verts), hulls, root


def ref_for(mesh_id, blob):
    flags, prim, groups, count, fvf, vertices = S.unpack_from('<II4H', blob)
    center = np.zeros(3)
    radius = 1.0
    if vertices:
        pts = np.array([S.unpack_from('<3f', blob, 16 + 12 * groups + 2 * count + 32 * i)
                        for i in range(0, vertices, max(1, vertices // 32))])
        center = pts.mean(axis=0)
        radius = float(np.max(np.linalg.norm(pts - center, axis=1))) * 1.05
    out = bytearray(60)
    S.pack_into('<2I6H4f', out, 0, 60, mesh_id, 0, vertices, 0, count, 0, groups, *center, radius)
    return bytes(out)


def build():
    solars, equipment, loadouts = bake.catalog(DATA)
    text = TEMPLATE.read_text(encoding='utf-8').split("'''", 2)[1]
    placed = [p for p in bake.placements_from_template(text)
              if p.archetype.lower() == 'space_trade_station_part']
    meshes = {}
    hulls = {}
    sample = None
    for item in placed:
        if item.loadout.lower() in meshes:
            continue
        blob, local_hulls, sample = baked_level0(item.loadout, solars, equipment, loadouts)
        meshes[item.loadout.lower()] = blob
        hulls[item.loadout.lower()] = local_hulls
    library = utf.Node('VMeshLibrary')
    ids = {}
    for name, blob in meshes.items():
        node = utf.Node(bake.clip(name + '_lod0', set()))
        node.children = [utf.Node('VMeshData', blob)]
        library.children.append(node)
        ids[name] = utf.crc(node.name)
    _, source = bake.load_model(PART)
    level1 = bake.one(bake.one(source, 'MultiLevel'), 'Level1')
    far_ref = bake.one(bake.one(level1, 'VMeshPart'), 'VMeshRef').blob
    far_id = S.unpack_from('<I', far_ref, 4)[0]
    far_node = bake.library_meshes(source)[far_id]
    far_copy = bake.clone(far_node)
    far_copy.name = 'ring_lod1'
    library.children.append(far_copy)
    far_crc = utf.crc(far_copy.name)
    switch = bake.one(bake.one(source, 'MultiLevel'), 'Switch2').blob

    root = utf.Node('\\')
    root.children.append(library)
    compound = utf.Node('Cmpnd')
    fix = bytearray()
    entries = [utf.Node('Part_Root')]
    entries[0].children = [
        utf.Node('Object name', b'Root\0'),
        utf.Node('Index', S.pack('<I', 0)),
        utf.Node('File name', b'ring_lod1.3db\0'),
    ]
    far_part = utf.Node('ring_lod1.3db')
    far_level = utf.Node('MultiLevel')
    far_vm = utf.Node('VMeshPart')
    far_vm.children = [utf.Node('VMeshRef', bytearray(far_ref))]
    S.pack_into('<I', far_vm.children[0].blob, 4, far_crc)
    far_level.children = [utf.Node('Level0'), utf.Node('Level1', None), utf.Node('Switch2', switch)]
    # A root anchor only needs the dummy mesh.
    dummy_level = utf.Node('Level0')
    dummy_level.children = [far_vm]
    far_part.children = [utf.Node('MultiLevel')]
    far_part.children[0].children = [dummy_level, utf.Node('Switch2', switch)]
    root.children.append(far_part)

    used = {'Root', 'ring_lod1'}
    local_opt = {key: bake.optimize(clouds) for key, clouds in hulls.items()}
    clouds = []
    for index, item in enumerate(placed, start=1):
        key = item.loadout.lower()
        name = bake.clip(item.name, used)
        file_name = bake.clip(name + '.3db', used)
        rotation = bake.euler(*item.rotate)
        translation = np.array(item.pos, dtype=float)
        ref = ref_for(ids[key], meshes[key])
        level0 = utf.Node('Level0')
        vm = utf.Node('VMeshPart')
        vm.children = [utf.Node('VMeshRef', ref)]
        level0.children = [vm]
        level1 = bake.clone(dummy_level)
        level1.name = 'Level1'
        part = utf.Node(file_name)
        multi = utf.Node('MultiLevel')
        multi.children = [level0, level1, utf.Node('Switch2', switch)]
        part.children = [multi]
        root.children.append(part)
        entry = utf.Node(bake.clip('Part_' + name, used))
        entry.children = [
            utf.Node('Object name', name.encode('ascii') + b'\0'),
            utf.Node('Index', S.pack('<I', index)),
            utf.Node('File name', (file_name + '\0').encode('ascii')),
        ]
        entries.append(entry)
        rec = bytearray(176)
        rec[:4] = b'Root'
        rec[64:64 + len(name)] = name.encode('ascii')
        S.pack_into('<3f', rec, 128, *translation)
        S.pack_into('<9f', rec, 140, *rotation.reshape(-1))
        fix.extend(rec)
        for cloud in local_opt[key]:
            if getattr(cloud, 'ndim', 0) == 2 and len(cloud) >= 3:
                clouds.append(cloud @ rotation.T + translation)
    cons = utf.Node('Cons')
    cons.children = [utf.Node('Fix', bytes(fix))]
    compound.children = [cons, *entries]
    root.children.append(compound)
    header = [0x20465455, 0x101, 0, 0, 0, 44, 0, 0, 0, 0, 0, 0, 0, 0]
    cmp_bytes = utf.write_tree(header, [root])
    sur_bytes = bake.write_sur([], clouds)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'part.cmp').write_bytes(cmp_bytes)
    (OUT / 'part.sur').write_bytes(sur_bytes)
    print({'parts': len(placed), 'cmp': len(cmp_bytes), 'sur': len(sur_bytes),
           'hulls': len(clouds), 'meshes': list(meshes)})


if __name__ == '__main__':
    build()
