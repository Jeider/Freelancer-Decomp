"""Second intact-only tail/rim review. Never deploys or rebuilds damage assets."""
import collections
import copy
import json
import secrets
import struct
import sys
from pathlib import Path
import numpy as np

sys.dont_write_bytecode = True
import rh_elite_tail_rim as r
f = r.f
b = r.b
OUT = r.OUT / 'revision_02'
SOURCE = r.OUT / 'rh_pir_elite_tail_rim.cmp'
NAME = 'rh_pir_elite_tail_mounts'
SOURCE_HASH = '08ed338643a2c774b8b98c7c6717e5414b5e19f0ebc2732c27e9d96541b22be2'
PALE, RED, BROWN = r.PALE, r.RED, r.BROWN
ENGINES = ('Rh_port_engine_lod1', 'Rh_starboard_engine_lod1')
ENGINE_SCALE = 1.5
ENGINE_DROP = .80
TAIL_HALF = 1.08
REFERENCE_IMAGES = (('tail_width_pylons', 'Qt4jlN'), ('flat_top', '4MDGGG'), ('engine_supports', 'MhAmau'))


def normals(gs):
    for g in gs:
        a = g['corners']
        n = np.cross(a[:, 1, :3]-a[:, 0, :3], a[:, 2, :3]-a[:, 0, :3])
        assert np.min(np.linalg.norm(n, axis=1)) > 1e-9
        a[:, :, 3:6] = (n/np.linalg.norm(n, axis=1)[:, None])[:, None, :]
    return gs


def take(gs, comp):
    by = collections.defaultdict(list)
    for gi, ti in comp['indices']:
        by[gi].append(ti)
    return [dict(gs[gi], corners=gs[gi]['corners'][ids].copy()) for gi, ids in by.items()]


def without(gs, comps):
    cut = collections.defaultdict(set)
    for c in comps:
        for gi, ti in c['indices']:
            cut[gi].add(ti)
    return [dict(g, corners=g['corners'][[i for i in range(len(g['corners'])) if i not in cut[gi]]].copy())
            for gi, g in enumerate(gs) if len(cut[gi]) < len(g['corners'])]


def resize_tail(x):
    return np.sign(x)*np.where(abs(x) <= .56, abs(x), .56+(abs(x)-.56)*(TAIL_HALF-.56)/(1.32-.56))


def engine_transform(p, center):
    return (p-center)*ENGINE_SCALE+center+np.array([0, -ENGINE_DROP, 0])


def solid_xy(poly, z0, z1):
    """Broad closed support, pale faces and a dark lower return, no bevels."""
    q = np.asarray(poly, float)
    build = f.b.Builder()
    for z, n in ((z0, [0, 0, -1]), (z1, [0, 0, 1])):
        uv = (q-q.min(0))/np.ptp(q, axis=0)
        r.face(build, np.column_stack((q, np.full(len(q), z))), PALE, (.505, .258, .997, .854), n, uv)
    area = np.sum(q[:, 0]*np.roll(q[:, 1], -1)-q[:, 1]*np.roll(q[:, 0], -1))
    phase = 0
    for a, c in zip(q, np.roll(q, -1, axis=0)):
        d = c-a
        n = np.r_[d[1], -d[0], 0]*np.sign(area)
        length = np.linalg.norm(d)
        # Wrap within the selected atlas crop, not across neighbouring atlas regions.
        end = phase+length/2.3
        cuts = [phase]+[float(i) for i in range(int(phase)+1, int(end)+1) if i < end-1e-8]+[end]
        for u, v in zip(cuts, cuts[1:]):
            p0 = a+d*(u-phase)/(end-phase); p1 = a+d*(v-phase)/(end-phase)
            origin = np.floor(u+1e-8)
            uv = np.array([[u-origin, 0], [v-origin, 0], [v-origin, 1], [u-origin, 1]])
            r.face(build, [[*p0, z0], [*p1, z0], [*p1, z1], [*p0, z1]],
                   BROWN if n[1] < -.5 else PALE, (.505, .258, .997, .854), n, uv)
        phase = end
    return build.groups()


def geometry():
    assert f.digest(SOURCE) == SOURCE_HASH, 'Prototype has user edits; rebase first'
    ns = r.load(SOURCE)[1]
    parts = r.world(ns)
    accepted = json.loads((r.OUT/'geometry.json').read_text())
    shell = r.flatten_groups(accepted['tail_shell'])
    hatch = r.flatten_groups(accepted['tail_hatch'])
    pylons = r.flatten_groups(accepted['tail_pylons'])
    for g in shell:
        g['corners'][:, :, 0] = resize_tail(g['corners'][:, :, 0])
    for g in hatch:
        g['corners'][:, :, 0] *= TAIL_HALF/1.32
    # Keep the mounting pads and HPs where the user placed them, extending roots only.
    for g in pylons:
        a = g['corners']; x = a[:, :, 0]
        u = np.clip((1.60-abs(x))/(1.60-1.297), 0, 1)
        a[:, :, 0] -= np.sign(x)*.32*u
    parts['Rh_tail_lod1'] = f.merge(normals(shell+hatch+pylons))

    # Delete the recess, its walls and four crossbars; rebuild the whole top plane.
    root = []
    removed_top = 0
    roof_y, roof_z0, roof_z1 = r.frame_profile()[0, 0], r.frame_profile()[0, 1], r.frame_profile()[1, 1]
    for g in parts['Root']:
        a = g['corners']; p = a[:, :, :3]
        pocket = (p[:, :, 1].min(1) > 4.55) & (abs(p[:, :, 0]).max(1) < .371)
        top = (abs(p[:, :, 1]-roof_y).max(1) < 2e-5) & (abs(p[:, :, 0]).max(1) < .521)
        remove = pocket | top
        removed_top += int(remove.sum())
        if (~remove).any():
            root.append(dict(g, corners=a[~remove].copy()))
    assert removed_top == 66, removed_top
    deck = f.b.Builder()
    for a, c in zip(np.linspace(roof_z0, roof_z1, 3)[:-1], np.linspace(roof_z0, roof_z1, 3)[1:]):
        r.face(deck, [[-.52, roof_y, a], [.52, roof_y, a], [.52, roof_y, c], [-.52, roof_y, c]],
               PALE, (.505, .258, .997, .854), [0, 1, 0])
    root += deck.groups()

    # The fixed wing socket and shoulder share an exact seam. Remove their paired
    # internal faces and make the exposed shoulder rise continuously into the hull.
    comps = r.components(root)
    shoulders = [c for c in comps if c['triangles'] == 16 and c['bounds'][1][1] < 0
                 and c['bounds'][0][2] > 2.4 and c['bounds'][1][2] < 5.5]
    assert len(shoulders) == 2
    root_rest = without(root, shoulders)
    joined = []
    joins = []
    for side, owner in ((-1, 'Rh_port_upperarm'), (1, 'Rh_starboard_upperarm')):
        comp = next(c for c in shoulders if np.sign(np.mean(np.array(c['bounds'])[:, 0])) == side)
        shoulder = take(root, comp)
        socket = copy.deepcopy(parts[owner])
        a = np.array([2.11946, 4.06652]); c = np.array([2.74493, 5.40785]); v = c-a
        def seam(gs):
            kept = []; count = 0
            for g in gs:
                p = g['corners'][:, :, :3].copy(); p[:, :, 0] *= side
                d = p[:, :, [0, 2]]-a
                distance = abs(d[:, :, 0]*v[1]-d[:, :, 1]*v[0])/np.linalg.norm(v)
                mask = distance.max(1) < 2e-5
                count += int(mask.sum())
                if (~mask).any():kept.append(dict(g, corners=g['corners'][~mask].copy()))
            assert count == 2, (owner, count)
            return kept
        shoulder, socket = seam(shoulder), seam(socket)
        for g in shoulder:
            a = g['corners']; p = a[:, :, :3]
            p[:, :, 1] += np.where(p[:, :, 1] > -1.4, np.clip((2.12-abs(p[:, :, 0]))/.92, 0, 1)*.34, 0)
        # Same chart at the shared top/bottom seam, instead of stretched separate strips.
        for gs in (shoulder, socket):
            normals(gs)
            for g in gs:
                for t in g['corners']:
                    if g['material'] == PALE and abs(t[0, 4]) > .65:
                        t[:, 6] = .505+(abs(t[:, 0])-1.2)/3.0*.492
                        t[:, 7] = .258+(t[:, 2]-2.41192)/3.0*.596
        joined += shoulder
        parts[owner] = f.merge(socket)
        joins.append(dict(part=owner, removed_internal_triangles=4))
    parts['Root'] = f.merge(root_rest+joined)

    centers = {}
    supports = []
    for side, owner in zip((-1, 1), ENGINES):
        comps = r.components(parts[owner])
        barrel = next(c for c in comps if c['triangles'] == 100)
        center = np.mean(np.array(barrel['bounds']), axis=0)
        centers[owner] = center
        gs = take(parts[owner], barrel)
        for g in gs:g['corners'][:, :, :3] = engine_transform(g['corners'][:, :, :3], center)
        parts[owner] = gs
        # Forward knee ties the pod to the existing hull/wing shoulder. Its head
        # penetrates the shoulder; the lower broad foot enters the engine shell.
        p = np.array([[1.18, -1.79], [2.17, -1.90], [2.25, -2.54],
                      [1.42, -2.64], [1.18, -2.30]])
        p[:, 0] *= side
        supports += solid_xy(p, 3.05, 4.02)
        # A second short cradle runs out of the bottom of the narrow drum frame.
        # Physical thickness .34-.40, comparable to the wing, with a broad chord.
        p = np.array([[.35, -1.92], [.64, -1.92], [1.53, -2.25], [2.20, -2.31],
                      [2.20, -2.65], [1.40, -2.61], [.35, -2.28]])
        p[:, 0] *= side
        supports += solid_xy(p, 5.82, 6.97)
    parts['Root'] = f.merge(parts['Root']+supports)
    r.save(OUT/'geometry.json', dict(parts=parts, engine_centers=centers, supports=supports,
           flattened_deck=deck.groups(), tail_shell=shell, tail_pylons=pylons,
           removed_top_triangles=removed_top, wing_joins=joins))
    return parts, centers


def update_wire(ns, centers):
    from rh_pir_elite_refine_damage import decoded_wire
    tr, _ = f.audit.transforms(ns, ('Sc_extend wing', 0))
    lines = decoded_wire(ns, tr)
    changes = {part:engine_transform(np.array(lines[part]), centers[part]) for part in ENGINES}
    tail = np.array(lines['Rh_tail_lod1']).copy(); tail[:, :, 0] = resize_tail(tail[:, :, 0])
    changes['Rh_tail_lod1'] = tail
    lib = f.mesh.child(ns[0], 'VMeshLibrary'); names = f.component_map(ns)
    for owner, ls in changes.items():
        file = next(k for k, v in names.items() if v == owner); rot, t = tr[file.lower()]
        local = (ls-t)@rot
        ps = {b.key(q):q for q in local.reshape(-1, 3)}; keys = sorted(ps); lookup = {k:i for i, k in enumerate(keys)}
        triangle = np.zeros((1, 3, 8)); triangle[0, :, :3] = [[0, 0, 0], [.001, 0, 0], [0, .001, 0]]; triangle[0, :, 5] = 1
        blob, verts = f.mesh.pack([dict(material=PALE, corners=triangle, unused=204)])
        raw = bytearray(blob); base = len(verts)
        extra = np.zeros((len(keys), 8)); extra[:, :3] = [ps[k] for k in keys]; extra[:, 5] = 1
        struct.pack_into('<H', raw, 14, base+len(keys)); raw += extra.astype('<f4').tobytes()
        vn = 'mounts_wire_'+owner+'.vms'; lib.children.append(f.folder(vn, f.mesh.Node('VMeshData', bytes(raw))))
        ids = [lookup[b.key(q)] for line in local for q in line]
        payload = struct.pack('<II4H', 16, f.mesh.crc(vn), base, len(keys), len(ids), len(keys))+np.array(ids, '<u2').tobytes()
        f.mesh.child(f.mesh.child(f.mesh.child(ns[0], file), 'VMeshWire'), 'VWireData').blob = payload


def export(parts, centers):
    header, source = r.load(SOURCE); ns = copy.deepcopy(source)
    names = f.component_map(ns); tr, _ = f.audit.transforms(ns, ('Sc_extend wing', 0))
    lib = f.mesh.child(ns[0], 'VMeshLibrary')
    modified = {'Root', 'Rh_tail_lod1', 'Rh_port_upperarm', 'Rh_starboard_upperarm', *ENGINES}
    hp_changes = {}
    for file, owner in names.items():
        if owner not in modified:continue
        rot, t = tr[file.lower()]
        gs = f.base.world(parts[owner], rot.T, -rot.T@t)
        blob, verts = f.mesh.pack(f.merge(gs)); vn = 'mounts_'+owner+'.vms'
        lib.children.append(f.folder(vn, f.mesh.Node('VMeshData', blob)))
        ref = f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(f.mesh.child(ns[0], file), 'MultiLevel'), 'Level0'), 'VMeshPart'), 'VMeshRef')
        ref.blob = f.fresh_ref(vn, blob, verts)
        if owner in ENGINES:
            for path, node in f.mesh.walk([f.mesh.child(ns[0], file)]):
                if '/Hardpoints/' not in path or not path.endswith('/Position'):continue
                name = path.split('/')[-2]
                if not name.lower().startswith('hp'):continue  # damage rig is postponed
                before = rot@np.frombuffer(node.blob, '<f4')+t
                after = engine_transform(before, centers[owner])
                node.blob = ((after-t)@rot).astype('<f4').tobytes()
                hp_changes[name] = dict(before=before, after=after, owner=owner)
    update_wire(ns, centers)
    used = {struct.unpack_from('<I', n.blob, 4)[0] for p, n in f.mesh.walk(ns) if p.lower().endswith(('/vmeshref', '/vwiredata'))}
    lib.children = [n for n in lib.children if f.mesh.crc(n.name) in used]
    salt = secrets.token_hex(6); mapping = b.salt_tree(ns, salt)
    target = OUT/(NAME+'.cmp'); target.write_bytes(f.mesh.write_tree(header, ns))
    ns = r.load(target)[1]
    before_hp, after_hp = r.hp_bytes(source), r.hp_bytes(ns)
    changed_hp = [key for key in before_hp if before_hp[key] != after_hp[key]]
    assert len(changed_hp) == 7, changed_hp
    assert all(key.split('/')[-2] in hp_changes and key.endswith('/Position') for key in changed_hp)
    for tag in ('Animation', 'Cons'):
        get = lambda a:f.mesh.child(a[0], tag) if tag == 'Animation' else f.mesh.child(f.mesh.child(a[0], 'Cmpnd'), tag)
        assert {p:n.blob for p, n in f.mesh.walk([get(source)])} == {p:n.blob for p, n in f.mesh.walk([get(ns)])}
    after = r.world(ns); before = r.world(source)
    for owner in before:
        if owner in modified:continue
        for a, c in zip(before[owner], after[owner]):
            assert a['material'] == c['material'] and np.allclose(a['corners'], c['corners'], atol=3e-6), owner
    available = collections.Counter((g['material'], tuple(np.round(t, 5).ravel())) for g in after['Root'] for t in g['corners'])
    drum_count = 0
    for comp in r.components(before['Root']):
        if comp['triangles'] in (160, 138) and comp['bounds'][0][2] > 2.5 and comp['bounds'][1][2] < 6.6:
            for gi, ti in comp['indices']:
                g = before['Root'][gi]; assert available[g['material'], tuple(np.round(g['corners'][ti], 5).ravel())]
                drum_count += 1
    assert drum_count == 436
    mats = f.audit.material_table([r.MAT, r.ENV]); limits = []
    for path, node in f.mesh.walk(ns):
        assert node.name.lower() not in ('material library', 'texture library')
        if path.lower().endswith('/vmeshdata'):
            verts, groups, indices = f.audit.decode(node.blob)
            assert len(verts) < 65536 and len(indices) < 65536 and np.isfinite(verts).all()
            for mid, lo, hi, num, _ in groups:assert mid in mats and num % 3 == 0 and 0 <= lo <= hi < len(verts)
            limits.append(dict(vertices=len(verts), indices=len(indices)))
    opened = copy.deepcopy(ns); tr, _ = f.audit.transforms(opened, ('Sc_extend wing', 0)); fixed = b''
    s64 = lambda s:s.encode().ljust(64, b'\0')
    for file, owner in f.component_map(opened).items():
        if owner == 'Root':continue
        rot, t = tr[file.lower()]; fixed += s64('Root')+s64(owner)+np.r_[t, rot.ravel()].astype('<f4').tobytes()
    f.mesh.child(f.mesh.child(opened[0], 'Cmpnd'), 'Cons').children = [f.mesh.Node('Fix', fixed)]
    opened[0].children = [n for n in opened[0].children if n.name != 'Animation']
    open_salt = secrets.token_hex(6); open_mapping = b.salt_tree(opened, open_salt)
    open_path = OUT/(NAME+'_open.cmp'); open_path.write_bytes(f.mesh.write_tree(header, opened))
    r.save(OUT/'review_data.json', dict(parts=after, hardpoints=f.hp_world(r.load(open_path)[1]), cmp_sha256=f.digest(target), open_cmp_sha256=f.digest(open_path)))
    motion = []
    base_tr, _ = f.audit.transforms(ns, ('Sc_extend wing', 0))
    for phase in np.linspace(0, 1, 65):
        sampled = copy.deepcopy(ns)
        for path, node in f.mesh.walk(sampled):
            if '/animation/script/sc_extend wing/' in path.lower() and path.lower().endswith('/channel/frames'):
                frames = np.frombuffer(node.blob, '<f4').copy().reshape(-1, 2)
                angle = np.interp(phase*frames[-1, 0], frames[:, 0], frames[:, 1])
                frames[0, 1] = angle; node.blob = frames.tobytes()
        posed, _ = f.audit.transforms(sampled, ('Sc_extend wing', 0))
        delta = {}
        for file, owner in f.component_map(ns).items():
            if not owner.endswith('_wing_mesh'):continue
            sr, st = base_tr[file.lower()]; pr, pt = posed[file.lower()]
            dr = pr@sr.T; delta[owner] = dict(rotation=dr, position=pt-dr@st)
        motion.append(dict(phase=float(phase), transforms=delta))
    r.save(OUT/'motion_input.json', dict(poses=motion, source_parts=before,
           fixed_parts=['Root', *ENGINES, 'Rh_port_upperarm', 'Rh_starboard_upperarm', 'Rh_tail_lod1']))
    r.save(OUT/'validation.json', dict(source=str(SOURCE), source_sha256=SOURCE_HASH, cmp_sha256=f.digest(target),
        open_cmp_sha256=f.digest(open_path), salt=salt, resources=mapping, open_salt=open_salt, open_resources=open_mapping,
        engine_scale=ENGINE_SCALE, engine_drop=ENGINE_DROP, tail_width=2*TAIL_HALF, hp_changes=hp_changes,
        all_other_hp_bytes_preserved=True, drum_triangles_unchanged=drum_count, animation_and_cons_unchanged=True,
        wing_meshes_unchanged=True, mesh_limits=limits, triangles=sum(len(g['corners']) for gs in after.values() for g in gs),
        installed=False, lods=1, damage_deferred=True, sur_not_generated=True))


def previews():
    from PIL import Image, ImageDraw
    from preview import render
    data = json.loads((OUT/'review_data.json').read_text()); parts = {k:r.flatten_groups(v) for k, v in data['parts'].items()}
    mats = f.audit.material_table([r.MAT, r.ENV])
    def pic(cam, center, radius, size=1000):
        gs = []
        for groups in parts.values():
            for g in groups:
                a = g['corners']; n = np.cross(a[:, 1, :3]-a[:, 0, :3], a[:, 2, :3]-a[:, 0, :3]); keep = n@np.array(cam) > 1e-9
                if keep.any():gs.append(dict(g, corners=a[keep]))
        return render(gs, mats, np.array(center), radius, cam, size, 'texture')
    shots = [('overview', (-1, .55, 1), (0, .4, 0), 11),
             ('mounts', (-1, -.8, 1), (0, -1.6, 4.8), 5.7),
             ('rear', (0, 0, 1), (0, .1, 5), 5.9),
             ('side', (1, 0, 0), (0, 0, 0), 11),
             ('flat_deck', (-1, 1.4, -.35), (0, 3.5, 4.8), 3.7),
             ('wing_join', (-1, .85, -.7), (-2.4, -1.9, 3.7), 3.9)]
    for name, cam, center, radius in shots:pic(cam, center, radius).save(OUT/(name+'.png'))
    sheet = Image.new('RGB', (1800, 1200)); d = ImageDraw.Draw(sheet)
    for i, (name, _, _, _) in enumerate(shots):
        im = Image.open(OUT/(name+'.png')).resize((600, 600)); x, y = (i % 3)*600, (i//3)*600
        sheet.paste(im, (x, y)); d.text((x+15, y+15), name.upper(), fill='white')
    sheet.save(OUT/'review.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT/'validation.json').exists():
        previous = json.loads((OUT/'validation.json').read_text())
        for suffix, key in (('', 'cmp_sha256'), ('_open', 'open_cmp_sha256')):
            target = OUT/(NAME+suffix+'.cmp')
            assert not target.exists() or f.digest(target) == previous[key], 'Preserve user edits before rebuilding '+str(target)
    guard = {str(p):f.digest(p) for p in [r.LIVE, r.MAT, r.OUT/'rh_pir_elite_dmg_tail.3db']}
    parts, centers = geometry()
    export(parts, centers)
    previews()
    assert all(f.digest(Path(p)) == h for p, h in guard.items())
    report = json.loads((OUT/'validation.json').read_text()); report['unchanged_external_files'] = guard
    r.save(OUT/'validation.json', report)
    print('READY', OUT, 'triangles', report['triangles'], flush=True)


def check():
    report = json.loads((OUT/'validation.json').read_text())
    assert f.digest(SOURCE) == SOURCE_HASH
    target, opened = OUT/(NAME+'.cmp'), OUT/(NAME+'_open.cmp')
    assert f.digest(target) == report['cmp_sha256'] and f.digest(opened) == report['open_cmp_sha256']
    assert all(f.digest(Path(p)) == digest for p, digest in report['unchanged_external_files'].items())
    for name in ('blender_check', 'connection_check', 'motion_check'):
        item = json.loads((OUT/(name+'.json')).read_text()); assert item['cmp_sha256'] == report['cmp_sha256']
        if name == 'blender_check':assert item['reopened'] and f.digest(OUT/(NAME+'.blend')) == item['blend_sha256']
        if name == 'motion_check':assert not item['after'] and item['phases'] == 65
    an, op = r.world(r.load(target)[1]), r.world(r.load(opened)[1], None)
    for owner in an:
        for a, c in zip(an[owner], op[owner]):
            assert a['material'] == c['material'] and np.allclose(a['corners'], c['corners'], atol=5e-6)
    closed = {}
    for owner in ENGINES:
        unique, ids = [], []
        for v in r.points(an[owner]):
            index = next((i for i, p in enumerate(unique) if np.linalg.norm(p-v) < 1e-4), None)
            if index is None:index = len(unique); unique.append(v)
            ids.append(index)
        edges = collections.Counter()
        for tri in np.array(ids).reshape(-1, 3):
            for a, c in zip(tri, np.roll(tri, -1)):edges[tuple(sorted((a, c)))]+=1
        assert all(count == 2 for count in edges.values()), owner
        closed[owner] = dict(weld_tolerance=.0001, boundary_edges=0, nonmanifold_edges=0)
    geometry = json.loads((OUT/'geometry.json').read_text()); mats = f.audit.material_table([r.MAT, r.ENV])
    for g in geometry['supports']:
        a = np.array(g['corners']); uv = a[:, :, 6:8]; u, v = uv[:, 1]-uv[:, 0], uv[:, 2]-uv[:, 0]
        assert abs(u[:, 0]*v[:, 1]-u[:, 1]*v[:, 0]).min() > 1e-9
        m = mats[g['material']]; assert 'metal' not in (m['name']+' '+m['texture']).lower()
    references = OUT/'references'; references.mkdir(exist_ok=True); refs = {}
    for name, code in REFERENCE_IMAGES:
        source = Path('C:/Users/Freel/AppData/Local/Temp')/('codex-clipboard-'+code+'.png')
        dest = references/(name+'.png')
        if not dest.exists():dest.write_bytes(source.read_bytes())
        assert f.digest(source) == f.digest(dest)
        refs[name] = dict(source=str(source), file=dest.name, sha256=f.digest(dest))
    r.save(references/'manifest.json', refs)
    report.update(static_animated_pose_match=True, engine_closed=closed, new_support_uvs_valid=True,
                  new_support_exterior_materials_valid=True, checks_complete=True,
                  previews={p.name:f.digest(p) for p in OUT.glob('*.png')})
    r.save(OUT/'validation.json', report)
    print('CHECKED: CMP/Blender hashes, 65 motion samples, attachments, closed engines, UVs, unchanged game and damage files')


if __name__ == '__main__':
    check() if sys.argv[1:] == ['check'] else main()
