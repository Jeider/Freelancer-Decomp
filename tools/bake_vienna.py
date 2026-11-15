"""Bake the full Vienna station into a handful of compounds.

Each arm, the core and the caps become their own 3db, so NPC avoidance sees
those boxes and not one station-sized capsule. Girders stay separate objects:
their own radius is under the 100 m avoidance cutoff.
"""
from pathlib import Path
import struct as S
import sys

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import generate_station_lods as utf
import bake_compound as bake
import bake_one_part as part
import train_sur.build as sur

DATA = Path(r'D:\Games\FL_MOD\DATA')
SOURCE = DATA / 'UNIVERSE' / 'SYSTEMS_MOD' / 'RH_VIENNA' / 'rh_vien.ini'
LIVE = DATA / 'UNIVERSE' / 'SPECIAL' / 'RH_VIENNA' / 'rh_vien.ini'
OUT = DATA / 'SOLAR' / 'misc'
SOLARARCH = DATA / 'SOLAR' / 'solararch.ini'
LIMIT = 58000
SKIP = {'sw_center_300', 'space_industriala_base_root'}
MARK = '; vienna_opt'


def parse_objects(path):
    cur = {}
    rows = []
    for line in Path(path).read_text(encoding='utf-8', errors='replace').splitlines():
        s = line.split(';', 1)[0].strip()
        if s == '[Object]':
            if cur.get('archetype') and 'pos' in cur:
                rows.append(cur)
            cur = {}
            continue
        if '=' in s and not s.startswith('['):
            k, v = s.split('=', 1)
            cur[k.strip().lower()] = v.strip()
    if cur.get('archetype') and 'pos' in cur:
        rows.append(cur)
    return rows


def vec(text):
    return tuple(float(x) for x in text.replace(',', ' ').split()[:3])


def region(nick):
    upper = nick.upper()
    for name in ('FRONT', 'BACK', 'LEFT', 'RIGHT', 'TOP', 'BOTTOM', 'CORE'):
        if f'_{name}_' in upper:
            return name
    return 'ROOT'


def euler_matrix(x, y, z):
    # Common.dll EulerMatrix: solar "rotate" is degrees, not rz @ rx @ ry.
    k = 0.017453292
    pitch, yaw, roll = x * k, y * k, z * k
    sp, cp = np.sin(pitch), np.cos(pitch)
    sy, cy = np.sin(yaw), np.cos(yaw)
    sr, cr = np.sin(roll), np.cos(roll)
    srcp = np.float32(sr * cp)
    crcp = np.float32(cr * cp)
    sysp = sy * sp
    return np.array([
        [cr * cy, sysp * cr - srcp, crcp * sy + sr * sp],
        [sr * cy, sysp * sr + crcp, srcp * sy - cr * sp],
        [-sy, cy * sp, cy * cp],
    ], float)


def mesh_of(path):
    levels, root = part.model_levels(path)
    blob = levels[0] if levels else part.mesh_of(root, None)
    if not blob:
        raise ValueError(f'no mesh in {path}')
    return blob, root


def piece_counts(blob):
    _flags, _prim, _groups, indices, _fvf, vertices = S.unpack_from('<II4H', blob)
    return vertices, indices


def chunks_of(items):
    if not items:
        return []
    pts = np.array([item['pos'] for item in items])
    axis = int(np.argmax(pts.max(0) - pts.min(0)))
    ordered = sorted(items, key=lambda item: item['pos'][axis])
    groups = []
    current = []
    vertices = indices = 0
    for item in ordered:
        if current and (vertices + item['verts'] > LIMIT or indices + item['indices'] > LIMIT):
            groups.append(current)
            current = []
            vertices = indices = 0
        current.append(item)
        vertices += item['verts']
        indices += item['indices']
    if current:
        groups.append(current)
    return groups


def avoid_radius(points):
    ext = np.asarray(points).max(0) - np.asarray(points).min(0)
    ordered = sorted(float(x) for x in ext)
    return 0.5 * max(ordered[0], ordered[1]), ext


def hulls_for(points):
    solid = part.thicken(np.asarray(points, float))
    if solid is None:
        return None
    try:
        return sur.make_hull(solid, 0)
    except Exception:
        return None


def compact(groups, verts):
    # One material group must own a tight vertex slice. A span across the whole
    # station makes ModStudio draw the unused vertices and inflates the group.
    by_mat = {}
    order = []
    for mat, lo, _hi, _unused, ids in groups:
        if mat not in by_mat:
            order.append(mat)
            by_mat[mat] = []
        by_mat[mat].extend(lo + i for i in ids)
    packed = []
    out = []
    for mat in order:
        remap = {}
        local = []
        for index in by_mat[mat]:
            slot = remap.get(index)
            if slot is None:
                slot = len(packed)
                remap[index] = slot
                packed.append(verts[index])
            local.append(slot)
        base = min(local)
        out.append((mat, base, max(local), 204, [i - base for i in local]))
    return out, packed


def write_part(name, items):
    groups, verts = [], []
    clouds = []
    for item in items:
        part.append_mesh(groups, verts, item['blob'], item['rotation'], item['translation'])
        pts = np.array([
            S.unpack_from('<3f', part.xform_vert(raw, item['rotation'], item['translation']), 0)
            for raw in part.read_mesh(item['blob'])[1]])
        clouds.append(pts)
    stacked = np.concatenate(clouds)
    center = (stacked.min(0) + stacked.max(0)) * 0.5
    verts = [part.xform_vert(raw, np.eye(3), -center) for raw in verts]
    groups, verts = compact(groups, verts)
    hulls = []
    for cloud in clouds:
        hull = hulls_for(cloud - center)
        if hull is not None:
            hulls.append(hull)
    mesh = part.write_mesh(groups, verts)
    library = utf.Node('VMeshLibrary')
    node = utf.Node(name)
    node.children = [utf.Node('VMeshData', mesh)]
    library.children = [node]
    vm = utf.Node('VMeshPart')
    vm.children = [utf.Node('VMeshRef', part.ref_bytes(utf.crc(name), mesh))]
    root = utf.Node('\\')
    root.children = [library, vm]
    header = [0x20465455, 0x101, 0, 0, 0, 44, 0, 0, 0, 0, 0, 0, 0, 0]
    stem = OUT / name
    stem.with_suffix('.3db').write_bytes(utf.write_tree(header, [root]))
    if hulls:
        surface, lo, hi = sur.encode_surface(hulls)
        sur_out = bytearray(b'vers' + S.pack('<f', 2.0))
        sur_out.extend(S.pack('<II', 0, 3))
        sur_out.extend(b'!fxd')
        sur_out.extend(b'exts' + S.pack('<6f', *lo, *hi))
        sur_out.extend(b'surf' + S.pack('<I', len(surface)) + surface)
        stem.with_suffix('.sur').write_bytes(sur_out)
    radius, ext = avoid_radius(np.array([S.unpack_from('<3f', raw, 0) for raw in verts]))
    return {
        'name': name,
        'pieces': len(items),
        'verts': len(verts),
        'hulls': len(hulls),
        'avoid': round(radius, 1),
        'ext': [round(float(x), 1) for x in ext],
        'pos': tuple(round(float(x), 3) for x in center),
    }


def solar_block(name, libraries):
    lines = [
        MARK,
        '[Solar]',
        f'nickname = {name}',
        'ids_name = 238129',
        'ids_info = 1',
        'type = NON_TARGETABLE',
        f'DA_archetype = solar\\misc\\{name}.3db',
    ]
    for lib in libraries:
        lines.append(f'material_library = {lib}')
    lines.extend([
        'envmap_material = envmapsolar01',
        'LODranges = 0, 80000',
        'mass = 10000',
        'solar_radius = 800',
        'hit_pts = 999999961690316250000000000000000000',
        'distance_render = 40000',
        'phantom_physics = false',
        '',
    ])
    return '\n'.join(lines)


def install_solars(names, libraries):
    text = SOLARARCH.read_text(encoding='utf-8', errors='replace')
    if MARK in text:
        text = text[:text.index(MARK)].rstrip() + '\n\n'
    else:
        text = text.rstrip() + '\n\n'
    blocks = [solar_block(name, libraries) for name in names]
    SOLARARCH.write_text(text + '\n'.join(blocks), encoding='utf-8')


def install_system(names, girders):
    lines = LIVE.read_text(encoding='utf-8', errors='replace').splitlines()
    head = []
    keep = []
    on = False
    block = []
    keep_tokens = ('docking_fixture', 'sw_center', 'jumpgate')
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('[') and stripped != '[Object]':
            if on and any(token in x for x in block for token in keep_tokens):
                keep.extend(block)
            on = False
            block = []
            head.append(line)
            continue
        if stripped == '[Object]':
            if on and any(token in x for x in block for token in keep_tokens):
                keep.extend(block)
            on = True
            block = [line]
            continue
        if on:
            block.append(line)
            continue
        head.append(line)
    if on and any(token in x for x in block for token in ('docking_fixture', 'sw_center', 'jumpgate')):
        keep.extend(block)
    out = head[:]
    if out and out[-1].strip():
        out.append('')
    out.extend([
        '[Object]',
        'nickname = rh_vien_station_1',
        'ids_name = 238129',
        'pos = 0, 0, 0',
        'rotate = 0, 0, 0',
        'archetype = hidden_connect',
        'ids_info = 1',
        '',
    ])
    for item in names:
        pos = '{:.3f}, {:.3f}, {:.3f}'.format(*item['pos'])
        out.extend([
            '[Object]',
            f"nickname = rh_vien_{item['name']}",
            f'pos = {pos}',
            'rotate = 0, 0, 0',
            f"archetype = {item['name']}",
            'parent = rh_vien_station_1',
            '',
        ])
    for row in girders:
        out.extend([
            '[Object]',
            f"nickname = {row['nickname']}",
            f"pos = {row['pos']}",
            f"rotate = {row.get('rotate', '0, 0, 0')}",
            f"archetype = {row['archetype']}",
            'parent = rh_vien_station_1',
            '',
        ])
    out.extend(keep)
    LIVE.write_text('\n'.join(out).rstrip() + '\n', encoding='utf-8')


def main():
    solars, equipment, loadouts = bake.catalog(DATA)
    items = []
    girders = []
    libraries = []
    for row in parse_objects(SOURCE):
        arch = row['archetype']
        if 'girder' in arch:
            girders.append(row)
            continue
        if arch.lower() in SKIP:
            continue
        solar = solars.get(arch.lower())
        if not solar or 'da_archetype' not in solar:
            continue
        path = bake.model_path(DATA, solar['da_archetype'][0])
        if path.suffix.lower() not in ('.3db', '.cmp'):
            continue
        blob, root = mesh_of(path)
        rotation = euler_matrix(*vec(row.get('rotate', '0, 0, 0')))
        translation = np.array(vec(row['pos']), float)
        verts, indices = piece_counts(blob)
        items.append({
            'region': region(row['nickname']),
            'pos': translation,
            'rotation': rotation,
            'translation': translation,
            'blob': blob,
            'verts': verts,
            'indices': indices,
        })
        for lib in solar.get('material_library', []):
            if lib not in libraries:
                libraries.append(lib)
        spec = loadouts.get(row.get('loadout', '').lower())
        if not spec:
            continue
        hps = bake.hardpoints(root)
        for line in spec.get('equip', []):
            nick, _, hp = line.partition(',')
            eq = equipment.get(nick.strip().lower())
            if not eq or 'da_archetype' not in eq or hp.strip().lower() not in hps:
                continue
            child = bake.model_path(DATA, eq['da_archetype'][0])
            child_blob, child_root = mesh_of(child)
            anchor = eq.get('hp_child', ['HpRoot'])[0].lower()
            placed = bake.compose(
                hps[hp.strip().lower()],
                bake.inverse(bake.hardpoints(child_root).get(anchor, (np.eye(3), np.zeros(3)))))
            world_r, world_t = bake.compose((rotation, translation), placed)
            cv, ci = piece_counts(child_blob)
            items.append({
                'region': region(row['nickname']),
                'pos': world_t,
                'rotation': world_r,
                'translation': world_t,
                'blob': child_blob,
                'verts': cv,
                'indices': ci,
            })
    made = []
    for name in ('CORE', 'FRONT', 'BACK', 'LEFT', 'RIGHT', 'TOP', 'BOTTOM', 'ROOT'):
        group = [item for item in items if item['region'] == name]
        for index, chunk in enumerate(chunks_of(group), 1):
            made.append(write_part(f'vienna_{name.lower()}_{index}', chunk))
    names = [item['name'] for item in made]
    install_solars(names, libraries)
    install_system(made, girders)
    for item in made:
        print(item)
    print({'parts': len(made), 'girders': len(girders), 'baked': len(items)})


if __name__ == '__main__':
    main()
