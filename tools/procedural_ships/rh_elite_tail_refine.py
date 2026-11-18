"""Revision 03: 120% engines, complete pylon roots and close drum ties. Offline."""
import copy
import json
import sys
from pathlib import Path
import numpy as np

sys.dont_write_bytecode = True
import rh_elite_tail_mounts as m
r, f = m.r, m.f
PREVIOUS = m.OUT
OUT = r.OUT/'revision_03'
SOURCE = PREVIOUS/(m.NAME+'.cmp')
SOURCE_HASH = '61bdb6c6c96f6ab44fdb40a2e91e54c379201708f0ba2cd9e137c7191744d3e6'
OPEN_SOURCE_HASH = 'd94a233f032c705b452ac84a77c55b89ab38c01f0c1d35dbd3ace0455fecf881'
NAME = 'rh_pir_elite_tail_refine'
RATIO = 1.2/1.5
RISE = .225


def engine_transform(p, center):
    # Preserve the previous pod's upper attachment height while reducing radius.
    return (p-center)*RATIO+center+np.array([0, RISE, 0])


def configure():
    m.OUT = OUT; m.SOURCE = SOURCE; m.SOURCE_HASH = SOURCE_HASH; m.NAME = NAME
    m.ENGINE_SCALE = 1.2; m.ENGINE_DROP = .575
    m.engine_transform = engine_transform
    m.resize_tail = lambda x:x  # already narrowed in revision 02
    m.REFERENCE_IMAGES = (('single_top_chart', '6YTCXb'), ('pylon_gap', 'MqR8v7'), ('pylons_and_drum_tie', 'JQjUlw'))


def strip_exact(gs, remove):
    def key(mid, tri):return mid, tuple(np.round(tri[:, :3], 4).ravel())
    keys = {key(g['material'], tri) for g in remove for tri in g['corners']}
    found = 0; kept = []
    for g in gs:
        mask = np.array([key(g['material'], tri) in keys for tri in g['corners']])
        found += int(mask.sum())
        if (~mask).any():kept.append(dict(g, corners=g['corners'][~mask].copy()))
    assert found == sum(len(g['corners']) for g in remove), (found, len(keys))
    return kept


def geometry():
    assert f.digest(SOURCE) == SOURCE_HASH
    assert f.digest(PREVIOUS/'rh_pir_elite_tail_mounts_open.cmp') == OPEN_SOURCE_HASH, 'Preserve new manual HP edits first'
    previous = json.loads((PREVIOUS/'geometry.json').read_text())
    parts = r.world(r.load(SOURCE)[1]); centers = {}
    for owner in m.ENGINES:
        center = (r.points(parts[owner]).min(0)+r.points(parts[owner]).max(0))/2
        centers[owner] = center
        for g in parts[owner]:g['corners'][:, :, :3] = engine_transform(g['corners'][:, :, :3], center)
    # Reshape the feet and their longitudinal reach; keep the hull-side anchors fixed.
    supports = r.flatten_groups(previous['supports'])
    root = strip_exact(parts['Root'], supports)
    engine_z = centers[m.ENGINES[0]][2]
    for g in supports:
        a = g['corners']; p = a[:, :, :3]
        u = np.clip((-p[:, :, 1]-2.05)/.30, 0, 1)
        side = np.sign(p[:, :, 0]); cx = side*abs(centers[m.ENGINES[0]][0])
        p[:, :, 0] = p[:, :, 0]+((p[:, :, 0]-cx)*RATIO+cx-p[:, :, 0])*u
        p[:, :, 2] = engine_z+(p[:, :, 2]-engine_z)*RATIO
    m.normals(supports)
    root += supports

    # Replace the two repeated deck charts with one quad and one native atlas crop.
    root = strip_exact(root, r.flatten_groups(previous['flattened_deck']))
    y, z0, z1 = r.frame_profile()[0, 0], r.frame_profile()[0, 1], r.frame_profile()[1, 1]
    build = f.b.Builder()
    # Chart orientation follows the long axis; aspect ratio matches the real deck.
    uv_height = .492*1.04/(z1-z0)
    r.face(build, [[-.52, y, z0], [.52, y, z0], [.52, y, z1], [-.52, y, z1]],
           r.PALE, (.505, .258, .997, .258+uv_height), [0, 1, 0],
           np.array([[0, 0], [0, 1], [1, 1], [1, 0]]))
    deck = build.groups(); root += deck

    # The previous affine extension only buried the leading edge. Set the ENTIRE
    # inner root edge inside the tail side wall, leaving all outer pad vertices/HPs.
    tail = parts['Rh_tail_lod1']; comps = r.components(tail)
    pylon_comps = [c for c in comps if c['triangles'] == 14]
    assert len(pylon_comps) == 4
    tail_rest = m.without(tail, pylon_comps); pylons = []
    root_edges = []
    for comp in pylon_comps:
        gs = m.take(tail, comp); side = np.sign(np.mean(np.array(comp['bounds'])[:, 0]))
        for g in gs:
            a = g['corners']; inner = abs(a[:, :, 0]) < 1.5
            a[:, :, 0][inner] = side*.96
        m.normals(gs)
        p = r.points(gs); inner = p[np.isclose(abs(p[:, 0]), .96)]
        root_edges.append(dict(side=int(side), y_min=float(inner[:, 1].min()), y_max=float(inner[:, 1].max()),
                               z_min=float(inner[:, 2].min()), z_max=float(inner[:, 2].max()), x=side*.96))
        pylons += gs
    parts['Rh_tail_lod1'] = f.merge(tail_rest+pylons)

    # Remove the old displaced side ties INCLUDING their detached scaled end caps.
    to_remove = []
    for comp in r.components(root):
        lo, hi = np.array(comp['bounds'])
        if comp['triangles'] == 14 and .85 < lo[1] < .86 and 1.37 < hi[1] < 1.38 and lo[2] > 5.66:
            to_remove.append(comp)
        elif comp['triangles'] == 2 and abs(lo[2]-8.00293) < 1e-4 and abs(hi[2]-8.00293) < 1e-4 and .85 < lo[1] < .86:
            to_remove.append(comp)
    assert sorted(c['triangles'] for c in to_remove) == [2, 2, 14, 14]
    root = m.without(root, to_remove)
    native = r.world(r.load(r.OUT/'user_source.cmp')[1])['Root']
    ties = []
    for comp in r.components(native):
        lo, hi = np.array(comp['bounds'])
        if comp['triangles'] == 16 and .85 < lo[1] < .86 and 1.37 < hi[1] < 1.38 and lo[2] > 5.66:
            gs = m.take(native, comp)
            for g in gs:
                a = g['corners']; a[:, :, 0] -= np.sign(a[:, :, 0])*.38
            ties += gs
    assert sum(len(g['corners']) for g in ties) == 32
    # Inner tie face .79 seats into the drum's .80 side; aft end enters the tail sleeve.
    parts['Root'] = f.merge(root+ties)
    r.save(OUT/'geometry.json', dict(parts=parts, engine_centers=centers, supports=supports,
           flattened_deck=deck, tail_shell=previous['tail_shell'], tail_pylons=pylons,
           pylon_root_edges=root_edges, close_drum_ties=ties, deck_chart_count=1,
           deck_uv_box=[.505, .258, .997, .258+uv_height], engine_original_scale=1.2,
           engine_drop_from_original=.575, removed_disconnected_tie_caps=4))
    return parts, centers


def detail_previews():
    from PIL import Image, ImageDraw
    from preview import render
    data = json.loads((OUT/'review_data.json').read_text())
    parts = {k:r.flatten_groups(v) for k, v in data['parts'].items()}
    mats = f.audit.material_table([r.MAT, r.ENV])
    def pic(cam, center, radius):
        gs = []
        for groups in parts.values():
            for g in groups:
                a = g['corners']; n = np.cross(a[:, 1, :3]-a[:, 0, :3], a[:, 2, :3]-a[:, 0, :3]); keep = n@np.array(cam) > 1e-9
                if keep.any():gs.append(dict(g, corners=a[keep]))
        return render(gs, mats, np.array(center), radius, cam, 900, 'texture')
    shots = [('pylons_top', (.002, 1, .02), (0, 1.12, 8.2), 2.75),
             ('pylons_below', (1, .35, 1), (1.15, 1.05, 8.35), 2.05),
             ('tie_contact', (1, 1.7, -.4), (.8, 1.0, 6.5), 2.6)]
    for name, cam, center, radius in shots:pic(cam, center, radius).save(OUT/(name+'.png'))
    sheet = Image.new('RGB', (1800, 1200)); draw = ImageDraw.Draw(sheet)
    for i, name in enumerate(['overview', 'flat_deck', 'pylons_top', 'mounts', 'pylons_below', 'tie_contact']):
        im = Image.open(OUT/(name+'.png')).resize((600, 600)); x, y = i%3*600, i//3*600
        sheet.paste(im, (x, y)); draw.text((x+15, y+15), name.upper(), fill='white')
    sheet.save(OUT/'review.png')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT/'validation.json').exists():
        rep = json.loads((OUT/'validation.json').read_text())
        for suffix, key in (('', 'cmp_sha256'), ('_open', 'open_cmp_sha256')):
            assert f.digest(OUT/(NAME+suffix+'.cmp')) == rep[key], 'Preserve user edits before rebuilding'
    guard = {str(p):f.digest(p) for p in [r.LIVE, r.MAT, r.OUT/'rh_pir_elite_dmg_tail.3db', SOURCE, PREVIOUS/'rh_pir_elite_tail_mounts_open.cmp']}
    parts, centers = geometry()
    m.export(parts, centers); m.previews(); detail_previews()
    assert all(f.digest(Path(p)) == value for p, value in guard.items())
    rep = json.loads((OUT/'validation.json').read_text())
    rep.update(unchanged_external_files=guard, engine_relative_to_previous=RATIO, engine_rise_from_previous=RISE,
               single_top_chart=True, entire_pylon_root_buried=True, drum_tie_inward_shift=.38)
    r.save(OUT/'validation.json', rep)
    print('READY REVISION 03', OUT, rep['triangles'], flush=True)


if __name__ == '__main__':
    configure()
    m.check() if sys.argv[1:] == ['check'] else main()
