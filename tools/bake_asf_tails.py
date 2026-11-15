"""Bake the four ASF HQ tails into one mesh each, with a part-id 0 SUR.

The core stays asf_hq_core.3db. A tail is every hardpoint equip whose name
contains FRONT, BACK, LEFT or RIGHT. Vertices and collision share that
hardpoint transform. Each component is hulled on its own so an arch does
not become one solid block.
"""
from pathlib import Path
import struct as S
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_station_lods as utf
import bake_compound as bake
import bake_one_part as part
import asf_hq_open_sur as opensur
import train_sur.build as sur

DATA = Path(r'D:\Games\FL_MOD\DATA')
CORE = DATA / 'SOLAR' / 'misc' / 'asf_hq_core.3db'
OUT = DATA / 'SOLAR' / 'misc'
GROUPS = ('FRONT', 'BACK', 'LEFT', 'RIGHT')


def group_of(hp):
    upper = hp.upper()
    for name in GROUPS:
        if f'_{name}_' in upper:
            return name
    return None


def loadout_rows():
    lines = (DATA / 'SOLAR' / 'loadouts.ini').read_text(encoding='utf-8', errors='replace').splitlines()
    rows = []
    on = False
    for line in lines:
        if line.startswith('nickname = asf_hq_core_optimal'):
            on = True
            continue
        if on and line.startswith('['):
            break
        if not on:
            continue
        text = line.split(';', 1)[0].strip()
        if not text.startswith('equip'):
            continue
        rest = text.split('=', 1)[1]
        nick, _, hp = rest.partition(',')
        rows.append((nick.strip(), hp.strip()))
    return rows


def level_mesh(path):
    levels, root = part.model_levels(path)
    if levels:
        return levels[0], root
    blob = part.mesh_of(root, None)
    if blob:
        return blob, root
    raise ValueError(f'no mesh in {path}')


def chunk_rows(rows, equipment):
    chunks = []
    current = []
    indices = 0
    vertices = 0
    for nick, hp in rows:
        eq = equipment.get(nick.lower())
        if not eq or 'da_archetype' not in eq:
            continue
        path = bake.model_path(DATA, eq['da_archetype'][0])
        blob, _child = level_mesh(path)
        _flags, _prim, _groups, count, _fvf, nverts = S.unpack_from('<II4H', blob)
        if current and (indices + count > 60000 or vertices + nverts > 60000):
            chunks.append(current)
            current = []
            indices = 0
            vertices = 0
        current.append((nick, hp))
        indices += count
        vertices += nverts
    if current:
        chunks.append(current)
    return chunks


def cut_rows():
    lines = (DATA / 'SOLAR' / 'loadouts.ini').read_text(encoding='utf-8', errors='replace').splitlines()
    rows = []
    on = False
    for line in lines:
        if line.startswith('nickname = asf_hq_core_optimal'):
            on = True
            continue
        if on and line.startswith('['):
            break
        if not on or not line.strip().startswith('; equip'):
            continue
        text = line.strip().lstrip(';').strip()
        if not text.startswith('equip'):
            continue
        rest = text.split('=', 1)[1]
        nick, _, hp = rest.partition(',')
        rows.append((nick.strip(), hp.strip()))
    return rows


def bake_group(name, rows, equipment, core_hps, write_sur=True):
    groups, verts = [], []
    hulls = []
    mats = []
    cache = {}
    for nick, hp in rows:
        eq = equipment.get(nick.lower())
        if not eq or 'da_archetype' not in eq:
            continue
        path = bake.model_path(DATA, eq['da_archetype'][0])
        blob, child = level_mesh(path)
        anchor = eq.get('hp_child', ['HpRoot'])[0].lower()
        rotation, translation = bake.compose(
            core_hps[hp.lower()],
            bake.inverse(bake.hardpoints(child).get(anchor, (np.eye(3), np.zeros(3)))))
        part.append_mesh(groups, verts, blob, rotation, translation)
        if write_sur:
            hulls.extend(opensur.component_hulls(path, nick, rotation, translation, 0, cache))
        for lib in eq.get('material_library', []):
            if lib not in mats:
                mats.append(lib)
    if len(verts) > 65535:
        raise ValueError(f'{name} has {len(verts)} vertices')
    mesh = part.write_mesh(part.coalesce(groups), verts)
    library = utf.Node('VMeshLibrary')
    mesh_name = f'asf_hq_tail_{name.lower()}'
    node = utf.Node(mesh_name)
    node.children = [utf.Node('VMeshData', mesh)]
    library.children = [node]
    vm = utf.Node('VMeshPart')
    vm.children = [utf.Node('VMeshRef', part.ref_bytes(utf.crc(mesh_name), mesh))]
    root = utf.Node('\\')
    root.children = [library, vm]
    header = [0x20465455, 0x101, 0, 0, 0, 44, 0, 0, 0, 0, 0, 0, 0, 0]
    stem = OUT / mesh_name
    stem.with_suffix('.3db').write_bytes(utf.write_tree(header, [root]))
    sur_bytes = 0
    if write_sur:
        if not hulls:
            pts = np.array([S.unpack_from('<3f', raw, 0) for raw in verts])
            hulls = [sur.make_hull(pts, 0)]
        surface, lo, hi = sur.encode_surface(hulls)
        sur_out = bytearray(b'vers' + S.pack('<f', 2.0))
        sur_out.extend(S.pack('<II', 0, 3))
        sur_out.extend(b'!fxd')
        sur_out.extend(b'exts' + S.pack('<6f', *lo, *hi))
        sur_out.extend(b'surf' + S.pack('<I', len(surface)) + surface)
        stem.with_suffix('.sur').write_bytes(sur_out)
        sur_bytes = len(sur_out)
    return {
        'name': name,
        'verts': len(verts),
        'groups': len(part.coalesce(groups)),
        'hulls': len(hulls),
        'bytes': stem.with_suffix('.3db').stat().st_size,
        'sur': sur_bytes,
        'materials': mats,
    }


def bake_cut():
    _, equipment, _ = bake.catalog(DATA)
    _, roots = utf.read_tree(CORE.read_bytes())
    core_hps = bake.hardpoints(roots[0])
    buckets = {name: [] for name in ('FRONT', 'BACK')}
    for nick, hp in cut_rows():
        group = group_of(hp)
        if group in buckets and hp.lower() in core_hps:
            buckets[group].append((nick, hp))
    made = []
    for name, rows in buckets.items():
        chunks = chunk_rows(rows, equipment)
        for index, chunk in enumerate(chunks, 3):
            made.append(bake_group(f'{name}_{index}', chunk, equipment, core_hps, write_sur=False))
    for item in made:
        print(item)
    return made


def main():
    _, equipment, _ = bake.catalog(DATA)
    _, roots = utf.read_tree(CORE.read_bytes())
    core_hps = bake.hardpoints(roots[0])
    buckets = {name: [] for name in GROUPS}
    for nick, hp in loadout_rows():
        group = group_of(hp)
        if group and hp.lower() in core_hps:
            buckets[group].append((nick, hp))
    made = []
    for name in GROUPS:
        chunks = chunk_rows(buckets[name], equipment)
        for index, rows in enumerate(chunks):
            suffix = name if len(chunks) == 1 else f'{name}_{index + 1}'
            made.append(bake_group(suffix, rows, equipment, core_hps))
    for item in made:
        print(item)


if __name__ == '__main__':
    main()
