"""Stage small rigid Valensia compounds, retaining originals and exact SUR leaves.

Only decorative, equal-archetype neighbours are combined.
Their AI capsule is capped at 150 m (and twice the source radius), length 600 m.
All DATA output (including staging/backup/rollback) uses DataFolder.
"""
import argparse
import ast
from collections import defaultdict
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import re
import struct as S

import numpy as np
import bake_compound as b
import bake_part_cmp as cmp
from bake_vienna import euler_matrix
import generate_station_lods as utf
import train_sur.build as sur
from tradelane.docking_surface import parts
from train_courier.data_output import data_folder

REPO = Path(__file__).resolve().parents[1]
GAME = Path('D:/Games/FL_MOD')
OUT = REPO/'out/valensia_optimization'
TEMPLATE = 'Assets/Pythonlancer/templates/dockable/valensia.py'
ORIGINAL_TEMPLATE = 'Assets/Pythonlancer/templates/dockable/valensiaOriginal.py'
LIVE = 'UNIVERSE/SPECIAL/ORDER_HQ/or_hq.ini'
MARK = '; BEGIN VALENSIA COMPONENTS'


def blocks(text):
    return re.split(r'(?m)(?=^\[)', text)


def fields(block):
    return b.fields([line.split(';', 1)[0].strip() for line in block.splitlines()
                     if '=' in line.split(';', 1)[0]])


def one(d, key, default=''):
    return d.get(key, [default])[0]


@dataclass
class ExactHull(sur.Hull):
    raw: bytes = b''


def leaves(blob):
    """Read terminal hulls via BVH; retain face/opposite-edge topology verbatim."""
    result = []
    pending = [S.unpack_from('<I', blob, 32)[0]]
    seen = set()
    while pending:
        at = pending.pop()
        assert at not in seen and 48 <= at <= len(blob)-28
        seen.add(at)
        right, ledge = S.unpack_from('<ii', blob, at)
        if right:
            pending.extend([at+28, at+right])
            continue
        assert ledge
        h = at+ledge
        rel, ident, flags, count, unused = S.unpack_from('<iIIHH', blob, h)
        assert flags & 255 == 4 and count >= 2
        raw = bytearray(blob[h:h+16+count*16])
        assert len(raw) == 16+count*16
        indices = sorted({S.unpack_from('<H', raw, 20+16*f+4*c)[0]
                          for f in range(count) for c in range(3)})
        mapping = {old: new for new, old in enumerate(indices)}
        points = np.array([S.unpack_from('<3f', blob, h+rel+16*i) for i in indices])
        faces = []
        for f in range(count):
            face = []
            for c in range(3):
                offset = 20+16*f+4*c
                idx = mapping[S.unpack_from('<H', raw, offset)[0]]
                S.pack_into('<H', raw, offset, idx)
                face.append(idx)
            faces.append(face)
        result.append(ExactHull(points, np.array(faces), ident, False, bytes(raw)))
    return result


original_encode = sur.encode_hull


def exact_encode(hull, base):
    if not isinstance(hull, ExactHull):
        return original_encode(hull, base)
    raw = bytearray(hull.raw)
    S.pack_into('<II', raw, 0, 0, hull.hull_id)
    for f in range(len(hull.faces)):
        for c in range(3):
            S.pack_into('<H', raw, 20+16*f+4*c, base+int(hull.faces[f, c]))
    return raw


def surface_file(entries):
    out = bytearray(b'vers'+S.pack('<f', 2))
    sur.encode_hull = exact_encode
    original_tree = sur.tree
    def stable_tree(hulls):
        tree = original_tree(hulls)
        if tree.left:
            # Structural BVH wrapper only (kind 5), never a collision leaf.
            # A box avoids numerically unstable tiny facets on a convex union.
            lo, hi = tree.lo, tree.hi
            corners = np.array([[x,y,z] for x in (lo[0],hi[0]) for y in (lo[1],hi[1]) for z in (lo[2],hi[2])])
            tree.hull = sur.make_hull(corners, 0, True)
        return tree
    sur.tree = stable_tree
    try:
        for index, (name, hulls) in enumerate(entries):
            surface, lo, hi = sur.encode_surface(hulls)
            out.extend(S.pack('<II', utf.crc(name), 3 if index == 0 else 2))
            if index == 0:
                out.extend(b'!fxd')
            out.extend(b'exts'+S.pack('<6f', *lo, *hi))
            out.extend(b'surf'+S.pack('<I', len(surface))+surface)
    finally:
        sur.encode_hull = original_encode
        sur.tree = original_tree
    return bytes(out)


def load_asset(data, arch):
    path = b.model_path(data, one(arch, 'da_archetype'))
    header, root = b.load_model(path)
    assert b.one(root, 'Cmpnd') is None
    assert {n.name.lower() for n in root.children} <= {'vmeshlibrary', 'vmeshpart', 'multilevel', 'hardpoints', 'exporter version'}
    source_parts = parts(path.with_suffix('.sur').read_bytes())
    assert len(source_parts) == 1 and source_parts[0][0] == 0
    hulls = leaves(dict(source_parts[0][1])[b'surf'])
    # Bounds include every visual LOD and collision point.
    boxes = []
    for ref in b.find(root, 'VMeshRef'):
        x = S.unpack_from('<6f', ref.blob, 20)
        boxes.extend([[x[1], x[3], x[5]], [x[0], x[2], x[4]]])
    points = np.concatenate([np.array(boxes), *[h.points for h in hulls]])
    return header, root, hulls, points.min(0), points.max(0)


def component(items, asset, arch, nick):
    header, visual, hulls, _, _ = asset
    anchor = items[0]
    rotation = euler_matrix(*anchor.rotate)
    # Keep the original mesh CRCs: many components reuse the same GPU buffers.
    library = b.clone(b.one(visual, 'VMeshLibrary'))
    mapping = {ident: ident for ident in b.library_meshes(visual)}
    root = utf.Node('\\')
    root.children.append(library)
    compound = utf.Node('Cmpnd')
    root.children.append(compound)
    fix = bytearray()
    entries, own, all_hulls, lods = [], [], [], []
    for i, item in enumerate(items):
        name = 'Root' if i == 0 else f'part{i:02d}'
        filename = f'{nick}_{i:02d}.3db'
        node = cmp.part_node(filename, visual, mapping)
        root.children.append(node)
        entry = utf.Node('Root' if i == 0 else f'Part_{i}')
        entry.children = [utf.Node('Object name', (name+'\0').encode()),
                          utf.Node('File name', (filename+'\0').encode()),
                          utf.Node('Index', S.pack('<I', i))]
        entries.append(entry)
        offset = (np.array(item.pos)-anchor.pos) @ rotation
        relative = rotation.T @ euler_matrix(*item.rotate)
        if i == 0:
            relative = np.eye(3)
        if i:
            rec = bytearray(176)
            rec[:4] = b'Root'
            rec[64:64+len(name)] = name.encode()
            S.pack_into('<3f', rec, 128, *offset)
            # EngBase copies these nine floats; X86Math multiplies column vectors.
            S.pack_into('<9f', rec, 140, *relative.flatten())
            fix.extend(rec)
        local = [ExactHull(h.points.copy(), h.faces, utf.crc(name), False, h.raw) for h in hulls]
        own.append((name, local))
        all_hulls.extend(ExactHull(h.points @ relative.T+offset, h.faces, h.hull_id, False, h.raw) for h in local)
        lods.append(f'[LOD]\nobj = {name}\nLODranges = {one(arch, "lodranges")}\n')
    cons = utf.Node('Cons')
    cons.children.append(utf.Node('Fix', bytes(fix)))
    compound.children = [cons, *entries]
    # Root aggregate contains the original hulls, never a replacement convex shell.
    collision = surface_file([('Root', all_hulls), *own[1:]])
    definition = ['[Solar]', f'nickname = {nick}']
    for key, values in arch.items():
        if key in ('nickname', 'section', 'da_archetype', 'lodranges'):
            continue
        definition.extend(f'{key} = {value}' for value in values)
    definition.extend([f'da_archetype = solar\\OPTIMIZED\\valensia_opt\\{nick}.cmp', '', *lods])
    return utf.write_tree(header, [root]), collision, '\n'.join(definition)+'\n'


def optimize(text, label, solars, assets, emit, prefix=None):
    rows = b.placements_from_template(text)
    raw = {one(fields(block), 'nickname'): block for block in blocks(text) if block.startswith('[Object]')}
    eligible = defaultdict(list)
    referenced = {p.parent for p in rows}
    allowed = {'nickname', 'pos', 'rotate', 'archetype', 'parent'}
    for p in rows:
        a = solars.get(p.archetype.lower(), {})
        semantic = next((x for x in p.name.split('_') if x.isupper()), '')
        if (not semantic or not p.archetype.startswith('space_industrial') or
                (prefix and not p.name.startswith(prefix)) or
                p.name in referenced or set(fields(raw[p.name]))-allowed or
                one(a, 'type').lower() != 'satellite' or one(a, 'loadout') or
                not one(a, 'da_archetype').lower().endswith('.3db')):
            continue
        if p.archetype not in assets:
            assets[p.archetype] = load_asset(GAME/'DATA', a)
        asset = assets[p.archetype]
        extent = asset[4]-asset[3]
        if sorted(extent)[1]/2 >= 99:
            continue
        eligible[(semantic, p.archetype, p.parent)].append(p)
    replacements, removed, groups, definitions = {}, set(), [], []
    for (semantic, archetype, parent), items in eligible.items():
        asset = assets[archetype]
        corners = np.array([[x, y, z] for x in (asset[3][0], asset[4][0])
                            for y in (asset[3][1], asset[4][1]) for z in (asset[3][2], asset[4][2])])
        remaining = sorted(items, key=lambda p: p.name)
        while remaining:
            group = [remaining.pop(0)]
            rotation = euler_matrix(*group[0].rotate)
            def bounds(p):
                points = (corners @ euler_matrix(*p.rotate).T + np.array(p.pos)-group[0].pos) @ rotation
                return points.min(0), points.max(0)
            lo, hi = bounds(group[0])
            boxes = [(lo, hi)]
            while len(group) < 8:
                candidates = []
                for p in remaining:
                    low, high = bounds(p)
                    a, z = np.minimum(lo, low), np.maximum(hi, high)
                    extent = z-a
                    gap = min(np.linalg.norm(np.maximum(0, np.maximum(qlo-high, low-qhi))) for qlo, qhi in boxes)
                    radius_limit = min(150, sorted(asset[4]-asset[3])[1])
                    if sorted(extent)[1]/2 <= radius_limit and max(extent) <= 600 and gap <= 120:
                        candidates.append((float(np.prod(extent)), p.name, p, (low, high), a, z))
                if not candidates:
                    break
                _, _, p, box, lo, hi = min(candidates, key=lambda c: c[:2])
                group.append(p)
                boxes.append(box)
                remaining.remove(p)
            if len(group) < 2:
                continue
            nick = f'vl_{label}_{len(groups):03d}'
            mesh, collision, definition = component(group, asset, solars[archetype], nick)
            emit(f'SOLAR/OPTIMIZED/valensia_opt/{nick}.cmp', mesh)
            emit(f'SOLAR/OPTIMIZED/valensia_opt/{nick}.sur', collision)
            definitions.append(definition)
            first = group[0]
            replacements[first.name] = re.sub(r'(?m)^(archetype\s*=\s*).+$', lambda m: m[1]+nick, raw[first.name])
            removed.update(p.name for p in group[1:])
            groups.append(dict(archetype=nick, semantic=semantic, members=[p.name for p in group],
                               bounds=[lo.tolist(), hi.tolist()], avoidance_radius=float(sorted(hi-lo)[1]/2),
                               source_hulls=len(asset[2]), hulls=len(asset[2])*len(group)))
    output = ''.join('' if one(fields(block), 'nickname') in removed else replacements.get(one(fields(block), 'nickname'), block)
                     for block in blocks(text))
    assert len(b.placements_from_template(output)) == len(rows)-len(removed)
    return output, definitions, dict(before=len(rows), after=len(rows)-len(removed), components=groups)


def build():
    out = OUT/'stage'
    folder = data_folder(GAME, out)
    sources, payload, reports = {}, {}, {}
    def read(relative):
        data = (GAME/relative).read_bytes()
        sources[relative] = sha256(data).hexdigest()
        return data
    def emit(relative, content):
        if isinstance(content, str): content = content.encode('utf-8')
        folder.sync_data_file(relative, content)
        payload['DATA/'+relative] = sha256(content).hexdigest()
    solar_source = read('DATA/SOLAR/solararch.ini').decode('utf-8-sig')
    solars = {one(fields(block), 'nickname').lower():fields(block) for block in blocks(solar_source)
              if block.lower().startswith('[solar]')}
    original_bytes = read(TEMPLATE)
    original = original_bytes.decode('utf-8-sig')
    tree = ast.parse(original)
    assets, definitions, appended = {}, [], []
    renamed = original
    for cls in tree.body:
        if not isinstance(cls, ast.ClassDef) or cls.name.endswith('Original'): continue
        value = next(m.value for m in cls.body if isinstance(m, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TEMPLATE' for t in m.targets))
        text = ast.literal_eval(value)
        optimized, defs, report = optimize(text, 'v1' if cls.name == 'ValensiaOutside' else 'v2', solars, assets, emit)
        renamed = renamed.replace(f'class {cls.name}(SpaceObjectTemplate):', f'class {cls.name}Original(SpaceObjectTemplate):', 1)
        assert "'''" not in optimized
        appended.append(f"\n\nclass {cls.name}({cls.name}Original):\n    TEMPLATE = '''"+optimized+"'''\n")
        definitions.extend(defs)
        reports[cls.name] = report
    updated = renamed+''.join(appended)
    compile(updated, TEMPLATE, 'exec')
    path = out/TEMPLATE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(updated.encode('utf-8'))
    payload[TEMPLATE] = sha256(path.read_bytes()).hexdigest()
    original_path = out/ORIGINAL_TEMPLATE
    original_path.write_bytes(original_bytes)
    payload[ORIGINAL_TEMPLATE] = sha256(original_bytes).hexdigest()
    live = read('DATA/'+LIVE)
    optimized, defs, report = optimize(live.decode('utf-8-sig'), 'hq', solars, assets, emit, 'or_hq_station_1')
    emit(LIVE.replace('.ini', 'Original.ini'), live)
    emit(LIVE, optimized)
    reports['or_hq_live'] = report
    definitions.extend(defs)
    assert MARK not in solar_source, 'Already optimized: rebuild from preserved originals explicitly'
    emit('SOLAR/solararch.ini', solar_source+'\n'+MARK+'\n'+'\n'.join(definitions)+'; END VALENSIA COMPONENTS\n')
    # Hash every model/surface used, so installation cannot silently race asset edits.
    for archetype in assets:
        model = b.model_path(GAME/'DATA', one(solars[archetype], 'da_archetype'))
        for path in (model, model.with_suffix('.sur')):
            read(path.relative_to(GAME).as_posix())
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'manifest.json').write_text(json.dumps(dict(sources=sources, payload=payload, reports=reports), indent=2), encoding='utf-8')
    for label, report in reports.items():
        print(label, report['before'], '->', report['after'], 'components', len(report['components']))


if __name__ == '__main__':
    build()
