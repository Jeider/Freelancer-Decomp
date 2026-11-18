"""One station part as a CMP: the shell plus each loadout mesh, not one meshgroup.

Identical pods share one VMeshData. Each part keeps the source Switch2, so the
distances stay per piece. part_lod.ini is the [LOD] block the solar must carry.
"""
from pathlib import Path
import struct as S
import sys
import time

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_station_lods as utf
import bake_compound as bake
import train_sur.build as sur

DATA = Path(r'D:\Games\FL_MOD\DATA')
PART = DATA / 'SOLAR' / 'misc' / 'space_trade_station_part.3db'
OUT = Path(__file__).resolve().parents[1] / 'out' / 'stations' / 'bake_compound'
LOADOUT = 'space_trade_part_attacher'
STEM = 'tgkp01'


def fragment_stamp():
    # MAXLancer CreateFragmentTimeStamp: YY MM DD HH MM SS.
    now = time.localtime()
    return f'{now.tm_year % 100:02d}{now.tm_mon:02d}{now.tm_mday:02d}{now.tm_hour:02d}{now.tm_min:02d}{now.tm_sec:02d}'


def visual_root(path):
    _, roots = utf.read_tree(Path(path).read_bytes())
    root = roots[0]
    compound = bake.one(root, 'Cmpnd')
    if compound is None:
        return root, bake.library_meshes(root)
    for entry in compound.children:
        obj = bake.one(entry, 'Object name')
        file = bake.one(entry, 'File name')
        if obj and bake.text(obj.blob).lower() == 'root' and file:
            return bake.one(root, bake.text(file.blob)), bake.library_meshes(root)
    raise ValueError(f'no root visual in {path}')


def retarget(node, mapping):
    for ref in bake.find(node, 'VMeshRef'):
        old = S.unpack_from('<I', ref.blob, 4)[0]
        blob = bytearray(ref.blob)
        S.pack_into('<I', blob, 4, mapping[old])
        ref.blob = bytes(blob)


def share(library, meshes, used, prefix, stamp):
    mapping = {}
    for old, node in meshes.items():
        key = bake.one(node, 'VMeshData').blob
        if key in used:
            mapping[old] = used[key]
            continue
        taken = {n.name for n in library.children}
        name = bake.clip(f'{prefix}_v{len(library.children):02d}{stamp}.vms', taken)
        crc = utf.crc(name)
        copy = bake.clone(node)
        copy.name = name
        library.children.append(copy)
        used[key] = crc
        mapping[old] = crc
    return mapping


def part_node(name, visual, mapping):
    node = utf.Node(name)
    for child in visual.children:
        if child.name.lower() in ('vmeshlibrary', 'exporter version'):
            continue
        cloned = bake.clone(child)
        retarget(cloned, mapping)
        node.children.append(cloned)
    return node


def part_points(node, library):
    ref = None
    for item in bake.find(node, 'VMeshRef'):
        ref = item.blob
        break
    if ref is None:
        return None
    mesh_id = S.unpack_from('<I', ref, 4)[0]
    data = None
    for entry in library.children:
        if utf.crc(entry.name) == mesh_id:
            data = bake.one(entry, 'VMeshData').blob
            break
    if data is None:
        return None
    flags, prim, groups, count, fvf, vertices = S.unpack_from('<II4H', data)
    if vertices < 4:
        return None
    base = 16 + 12 * groups + 2 * count
    return np.array([S.unpack_from('<3f', data, base + 32 * i) for i in range(vertices)])


def hull_from_points(points, hull_id):
    pts = np.unique(np.round(points, 3), axis=0)
    if len(pts) < 4:
        return None
    try:
        return sur.make_hull(pts, hull_id)
    except Exception:
        lo, hi = pts.min(axis=0), pts.max(axis=0)
        box = np.array([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        return sur.make_hull(box, hull_id)


def write_fitted_sur(part_nodes, library):
    out = bytearray(b'vers' + S.pack('<f', 2.0))
    for name, node, is_root in part_nodes:
        points = part_points(node, library)
        if points is None:
            continue
        hull = hull_from_points(points, utf.crc(name))
        if hull is None:
            continue
        surface, lo, hi = sur.encode_surface([hull])
        out.extend(S.pack('<II', utf.crc(name), 3 if is_root else 2))
        if is_root:
            out.extend(b'!fxd')
        out.extend(b'exts' + S.pack('<6f', *lo, *hi))
        out.extend(b'surf' + S.pack('<I', len(surface)) + surface)
    return bytes(out)


def sur_body(path, root):
    data = Path(path).read_bytes()
    if data[:4] != b'vers':
        return None
    at = 8
    if at + 8 > len(data):
        return None
    at += 8
    if data[at:at + 4] == b'!fxd':
        at += 4
    if data[at:at + 4] != b'exts' or data.find(b'surf', at) < 0:
        return None
    surf = data.find(b'surf', at)
    size = S.unpack_from('<I', data, surf + 4)[0]
    body = data[at:surf + 8 + size]
    if root:
        return b'!fxd' + body
    return body


def main():
    _, equipment, loadouts = bake.catalog(DATA)
    stamp = fragment_stamp()
    shell, shell_lib = visual_root(PART)
    library = utf.Node('VMeshLibrary')
    shared = {}
    shell_map = share(library, shell_lib, shared, STEM + 's', stamp)
    root_file_name = f'{STEM}_shell{stamp}.3db'
    root_obj = STEM + '_root'
    root_file = part_node(root_file_name, shell, shell_map)
    root = utf.Node('\\')
    root.children.append(library)
    root.children.append(root_file)
    hps = bake.hardpoints(shell)
    fix = bytearray()
    entries = [utf.Node('Root')]
    entries[0].children = [
        utf.Node('Object name', (root_obj + '\0').encode('ascii')),
        utf.Node('Index', S.pack('<I', 0)),
        utf.Node('File name', (root_file_name + '\0').encode('ascii')),
    ]
    lod = ['[LOD]', f'obj = {root_obj}', 'LODranges = 0, 8000, 27000', '']
    sur_nodes = [(root_obj, root_file, True)]
    used_names = {root_obj, root_file_name, STEM + '_PartRoot'}
    files = {}
    index = 1
    for line in loadouts[LOADOUT].get('equip', []):
        nick, _, hp = line.partition(',')
        nick, hp = nick.strip(), hp.strip()
        eq = equipment.get(nick.lower())
        if not eq or eq.get('section') != 'cargopod' or 'da_archetype' not in eq:
            continue
        if hp.lower() not in hps:
            continue
        path = bake.model_path(DATA, eq['da_archetype'][0])
        key = str(path).lower()
        if key not in files:
            visual, meshes = visual_root(path)
            files[key] = (visual, share(library, meshes, shared, STEM + 'a', stamp))
        visual, mapping = files[key]
        name = bake.clip(f'{STEM}_e{index:02d}', used_names)
        file_name = bake.clip(f'{STEM}_e{index:02d}{stamp}.3db', used_names)
        root.children.append(part_node(file_name, visual, mapping))
        entry = utf.Node('Part_' + name)
        entry.children = [
            utf.Node('Object name', name.encode('ascii') + b'\0'),
            utf.Node('Index', S.pack('<I', index)),
            utf.Node('File name', (file_name + '\0').encode('ascii')),
        ]
        entries.append(entry)
        child_visual, _ = visual_root(path)
        anchor = eq.get('hp_child', ['HpRoot'])[0].lower()
        rotation, translation = bake.compose(
            hps[hp.lower()],
            bake.inverse(bake.hardpoints(child_visual).get(anchor, (np.eye(3), np.zeros(3)))))
        rec = bytearray(176)
        rec[:len(root_obj)] = root_obj.encode('ascii')
        rec[64:64 + len(name)] = name.encode('ascii')
        S.pack_into('<3f', rec, 128, *translation)
        S.pack_into('<9f', rec, 140, *rotation.reshape(-1))
        fix.extend(rec)
        lod += [f'obj = {name}', 'LODranges = ' + eq.get('lodranges', ['0, 10000'])[0], '']
        sur_nodes.append((name, root.children[-1], False))
        index += 1
    cons = utf.Node('Cons')
    cons.children = [utf.Node('Fix', bytes(fix))]
    compound = utf.Node('Cmpnd')
    compound.children = [cons, *entries]
    root.children.append(compound)
    header = [0x20465455, 0x101, 0, 0, 0, 44, 0, 0, 0, 0, 0, 0, 0, 0]
    raw = utf.write_tree(header, [root])
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'part.cmp').write_bytes(raw)
    (OUT / 'part_lod.ini').write_text('\n'.join(lod) + '\n', encoding='utf-8')
    sur = write_fitted_sur(sur_nodes, library)
    written = sur.count(b'surf')
    (OUT / 'part.sur').write_bytes(sur)
    broken = OUT / 'part.3db'
    if broken.exists():
        broken.unlink()
    print({'bytes': len(raw), 'sur': len(sur), 'sur_parts': written, 'parts': index})


if __name__ == '__main__':
    main()
