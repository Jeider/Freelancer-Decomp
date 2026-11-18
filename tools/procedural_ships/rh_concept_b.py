"""Low-poly CMP implementation of rh_concept_B. Offline; never installs/launches."""
import argparse
import copy
import hashlib
import json
import math
import shutil
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import rh_raven as common
from rh_redesign_paths import CONCEPT_B_MODEL, CONCEPTS

mesh, audit, base = common.mesh, common.audit, common.base
OUT = CONCEPT_B_MODEL
DEST = OUT / 'rh_elite_concept_b.cmp'
PANEL, METAL, DARK, GRILL = common.PANEL, common.METAL, common.DARK, common.GRILL
UV, RED = common.ARMOR_UV, common.RED_UV
PANEL1 = mesh.crc('pir_r_panel01_256')
PLAIN_UV = (.53, .18, .985, .82)


class Builder(common.Builder):
    def face(self, points, material=PANEL, uvbox=UV, normal=None, uv=None):
        # Broad existing armor region: panel-scale detail, without stretched bullet holes.
        if material == PANEL and uvbox == UV:
            material, uvbox = PANEL1, PLAIN_UV
        return super().face(points, material, uvbox, normal, uv)

    def loft(self, sections, omit_top=False):
        rings = []
        for z, w, bottom, top in sections:
            h = top-bottom
            rings.append(np.array([(-w*.7, top, z), (w*.7, top, z),
                (w, top-h*.23, z), (w, bottom+h*.23, z), (w*.7, bottom, z),
                (-w*.7, bottom, z), (-w, bottom+h*.23, z), (-w, top-h*.23, z)]))
        for a, b in zip(rings, rings[1:]):
            center = np.concatenate((a, b)).mean(axis=0)
            for i in range(8):
                if omit_top and i == 0:
                    continue
                j = (i+1) % 8
                q = np.array([a[i], a[j], b[j], b[i]])
                self.face(q, METAL if i == 4 else PANEL, UV, q.mean(axis=0)-center,
                          [[0, 0], [1, 0], [1, 1], [0, 1]])
        self.face(rings[0], PANEL, UV, [0, 0, -1])
        self.face(rings[-1], PANEL, UV, [0, 0, 1])

    def beam(self, a, b, width, depth=None, material=PANEL):
        a, b = np.asarray(a, float), np.asarray(b, float)
        direction = mesh.unit(b-a)
        helper = np.array([1., 0, 0]) if abs(direction[0]) < .8 else np.array([0., 1, 0])
        u = mesh.unit(np.cross(direction, helper))*width/2
        v = mesh.unit(np.cross(direction, u))*(depth if depth is not None else width)/2
        pts = np.array([p+su*u+sv*v for p in (a, b) for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
        center = (a+b)/2
        for face in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            p = pts[list(face)]
            self.face(p, material, UV, p.mean(axis=0)-center)

    def radial(self, center, stations, sides, axis=0, material=PANEL, cap=METAL, cap_uv=None):
        """Closed cylinder/stepped housing, no geometric bolt or vent pattern."""
        center = np.asarray(center, float)
        axes = [i for i in range(3) if i != axis]
        rings = []
        for offset, radius in stations:
            a = np.arange(sides)*2*np.pi/sides + np.pi/sides
            ring = np.tile(center, (sides, 1))
            ring[:, axis] += offset
            ring[:, axes[0]] += radius*np.cos(a)
            ring[:, axes[1]] += radius*np.sin(a)
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for i in range(sides):
                j = (i+1) % sides
                p = np.array([a[i], a[j], b[j], b[i]])
                n = p.mean(axis=0)-center
                n[axis] = 0
                self.face(p, material, UV, n)
        normal = np.zeros(3)
        normal[axis] = 1
        cap_uv = cap_uv if cap_uv is not None else (0, 0, 1, 1) if cap == GRILL else UV
        self.face(rings[0], cap, cap_uv, -normal)
        self.face(rings[-1], cap, cap_uv, normal)

    def frame(self, lod):
        # The upright frame lies in YZ, just like the original RH rear disk.
        center = np.array([1.7, 4.65])
        outer = np.array([[4.9, 3.0], [4.9, 6.1], [3.7, 7.45],
                          [-.05, 7.45], [-1.4, 6.0], [-1.4, 3.0],
                          [-.05, 1.85], [3.7, 1.85]])
        inner = center+(outer-center)*.73
        if lod == 0:
            # A bevel only along the silhouette; the large open cells remain real holes.
            rings = [(.66, center+(outer-center)*.96), (.66, center+(inner-center)*1.04),
                     (.50, inner), (-.50, inner), (-.66, center+(inner-center)*1.04),
                     (-.66, center+(outer-center)*.96), (-.50, outer), (.50, outer)]
        else:
            rings = [(.60, outer), (.60, inner), (-.60, inner), (-.60, outer)]
        for k, ((x1, a), (x2, b)) in enumerate(zip(rings, rings[1:]+rings[:1])):
            for i in range(8):
                j = (i+1) % 8
                p = np.array([[x1, *a[i]], [x1, *a[j]], [x2, *b[j]], [x2, *b[i]]])
                # The contour order and cross-section order give outward normals.
                self.face(p, PANEL, RED if i in (0, 4) and k in (0, 4, 5) else UV)

    def far_paddle(self, side):
        # Six triangles: a quad upper surface and a very shallow pyramidal underside.
        p = np.array([[side*2.25, -1.57, 1.35], [side*7.2, -1.57, 1.60],
                      [side*7.1, -1.57, 3.15], [side*2.25, -1.57, 3.0]])
        bottom = p.mean(axis=0)+[0, -.16, 0]
        self.face(p, PANEL, UV, [0, 1, 0])
        for i in range(4):
            q = np.array([p[i], p[(i+1) % 4], bottom])
            self.face(q, PANEL, UV, q.mean(axis=0)-(bottom+[0, .08, 0]))


def design(part, original, lod):
    b = Builder()
    name = part.lower()
    if name.startswith('rh_elite_'):
        # Cabin copied separately, with an open neck connecting it to a stepped torso.
        if lod < 2:
            b.loft([(-1.95, 1.0, -1.5, .55), (-.55, 1.55, -1.6, 1.65),
                    (1.50, 1.55, -1.6, 2.25), (3.4, 1.10, -1.55, 1.3)], omit_top=True)
            b.face([[-.7, .55, -1.95], [.7, .55, -1.95], [1.085, 1.65, -.55], [-1.085, 1.65, -.55]], PANEL, UV, [0, 1, 0])
            b.face([[-1.085, 2.25, 1.5], [1.085, 2.25, 1.5], [.77, 1.3, 3.4], [-.77, 1.3, 3.4]], PANEL, RED, [0, 1, 0])
            for side in (-1, 1):
                # Sloping roof margins around the animated bay-door opening.
                b.face([[side*.7, 1.65, -.55], [side*1.085, 1.65, -.55],
                        [side*1.085, 2.25, 1.5], [side*.7, 2.25, 1.5]], PANEL, UV, [0, 1, 0])
                b.beam((side*.68, -1.2, -3.73), (side*.68, -1.2, -1.80), .21, .22)
                b.beam((side*.68, .1, -3.72), (side*.68, .45, -1.80), .18, .19)
                if lod == 0:
                    b.beam((side*.68, -1.1, -3.55), (side*.68, .38, -1.95), .17, .17, METAL)
                    # Structural brace, separate from wing and gun motion.
                    b.beam((side*1.78, -1.4, 2.35), (side*.82, 2.65, 2.6), .42, .48)
                    b.plate([(1.15, -.2), (1.65, -.2), (1.65, .7), (1.15, .7)], 1.3, 1.9, side,
                            material=METAL, inset=.9)
        else:
            # Remove side bevels, preserving the roof and hatch fit at every LOD.
            sections = [(-1.95, 1.0, -1.5, .55), (-.55, 1.55, -1.6, 1.65),
                        (1.50, 1.55, -1.6, 2.25), (3.4, 1.10, -1.55, 1.3)]
            rings = [np.array([[-w*.7, top, z], [w*.7, top, z],
                               [w, bottom, z], [-w, bottom, z]]) for z, w, bottom, top in sections]
            for a, c in zip(rings, rings[1:]):
                center = np.concatenate((a, c)).mean(axis=0)
                for i in (1, 2, 3):
                    j = (i+1) % 4
                    q = np.array([a[i], a[j], c[j], c[i]])
                    b.face(q, PANEL, UV, q.mean(axis=0)-center)
            b.face(rings[0], PANEL, UV, [0, 0, -1])
            b.face(rings[-1], PANEL, UV, [0, 0, 1])
            for a, c in ((rings[0], rings[1]), (rings[2], rings[3])):
                b.face([a[0], a[1], c[1], c[0]], PANEL, UV, [0, 1, 0])
            for side in (-1, 1):
                b.face([[side*.7, 1.65, -.55], [side*1.085, 1.65, -.55],
                        [side*1.085, 2.25, 1.5], [side*.7, 2.25, 1.5]], PANEL, UV, [0, 1, 0])
            b.beam((0, -.8, -3.75), (0, -.4, -1.8), .65, .65)
        return common.cockpit(original)+b.groups()
    if '_tail_' in name:
        b.frame(lod)
        center = np.array([0, 1.7, 4.65])
        stations = [(-.58, 1.13), (-.42, 1.32), (.42, 1.32), (.58, 1.13)] if lod == 0 else [(-.48, 1.25), (.48, 1.25)]
        b.radial(center, stations, 12 if lod == 0 else 8 if lod == 1 else 6,
                 cap=PANEL1, cap_uv=(.162, .573, .438, .817))
        if lod == 0:
            for angle in (0, np.pi/2, np.pi, np.pi*1.5):
                v = np.array([0, np.cos(angle), np.sin(angle)])
                b.beam(center+v*1.12, center+v*2.5, .25, .35, METAL)
        elif lod == 1:
            b.beam(center-[0, 2.45, 0], center+[0, 2.45, 0], .24, .28, METAL)
            b.beam(center-[0, 0, 2.25], center+[0, 0, 2.25], .24, .28, METAL)
        else:
            for x, normal in ((-.1, [-1, 0, 0]), (.1, [1, 0, 0])):
                b.face([[x, -.75, 4.52], [x, 4.15, 4.52], [x, 4.15, 4.78], [x, -.75, 4.78]], METAL, UV, normal)
                b.face([[x, 1.57, 2.4], [x, 1.83, 2.4], [x, 1.83, 6.9], [x, 1.57, 6.9]], METAL, UV, normal)
        return b.groups()
    if '_engine_' in name:
        side = -1 if '_port_' in name else 1
        center = (side*2.03, -1.63, 0)
        if lod == 0:
            b.radial(center, [(.38, .62), (.62, .82), (3.4, .82), (3.65, .66)], 10, axis=2, cap=GRILL)
            # A second ring at the exhaust creates depth without high-sided cylinders.
            b.radial(center, [(3.66, .57), (3.90, .57)], 10, axis=2, material=METAL, cap=GRILL)
        else:
            b.radial(center, [(.4, .75), (3.8, .75)], 8 if lod == 1 else 6, axis=2, cap=GRILL)
        return b.groups()
    if '_wing_' in name:
        side = -1 if '_port_' in name else 1
        if lod == 2:
            b.far_paddle(side)
        else:
            if lod == 0:
                b.beam((side*2.23, -1.65, 2.25), (side*4.2, -1.65, 2.25), .5, .62, METAL)
                b.radial((0, -1.65, 2.25), [(side*3.50, .36), (side*3.90, .36)] if side == 1
                         else [(side*3.90, .36), (side*3.50, .36)], 8, axis=0, material=METAL)
                b.plate([(3.9, 1.42), (6.9, 1.55), (7.25, 1.92), (7.05, 3.12), (3.9, 3.12)],
                        -1.90, -1.48, side, inset=.91)
                # Empty pad for the actual weapon model; no barrel/turret geometry.
                b.plate([(5.20, 1.94), (5.96, 1.94), (5.96, 2.68), (5.20, 2.68)],
                        -1.49, -1.43, side, material=METAL)
            else:
                b.plate([(2.25, 1.35), (7.2, 1.6), (7.1, 3.15), (2.25, 3.0)],
                        -1.80, -1.48, side, inset=1)
        return b.groups()
    if name.startswith('baydoor'):
        side = -1 if name.startswith('baydoor01') else 1
        # Door outline follows the sloped roof; the construct axis follows its hinge.
        p = np.array([[side*.015, 1.65, -.55], [side*.70, 1.65, -.55],
                      [side*.70, 2.25, 1.50], [side*.015, 2.25, 1.50]])
        b.face(p, PANEL, RED, [0, 1, 0])
        b.face(p, METAL, UV, [0, -1, 0])
        return b.groups()
    return original


def relocate(nodes):
    for p, n in mesh.walk(nodes):
        if '/cmpnd/cons/' not in p.lower():
            continue
        size = 176 if p.lower().endswith('/fix') else 208
        blob = bytearray(n.blob)
        for at in range(0, len(blob), size):
            name = mesh.string(blob[at+64:at+128]).lower()
            f = np.frombuffer(blob, '<f4', (size-128)//4, at+128)
            side = -1 if '_port_' in name else 1
            if '_engine_' in name:
                f[:3] = (side*2.03, -1.63, 2.0)
            elif '_wing_' in name:
                f[:3] = (side*2.25, -1.65, 2.25)
                f[15:18] = (0, 0, side)  # Close upward beside the frame.
            elif '_tail_' in name:
                f[:3] = (0, 1.7, 4.65)
            elif name.startswith('baydoor'):
                side = -1 if name.startswith('baydoor01') else 1
                f[:3] = (side*.7, 1.65, -.55)
                f[3:6] = 0
                f[6:15] = np.eye(3).ravel()
                f[15:18] = mesh.unit(np.array([0, .60, 2.05]))*(-side)
        n.blob = bytes(blob)
    transforms, _ = audit.transforms(nodes)
    for p, n in mesh.walk(nodes):
        if '/hardpoints/' not in p.lower() or not p.lower().endswith('/position'):
            continue
        part = p.split('/')[2].lower()
        hp = p.split('/')[-2].lower()
        side = -1 if '_port_' in part else 1
        target = None
        if '_wing_' in part:
            if hp.startswith('hpweapon'):
                target = (side*5.58, -1.425, 2.31)
            elif hp.startswith(('hpcontrail', 'hpdocklight')):
                target = (side*7.05, -1.60, 2.85)
        elif '_engine_' in part:
            if hp.startswith('hpengine'):
                target = (side*2.03, -1.63, 3.91)
            elif hp.startswith('hprunninglight'):
                target = (side*2.03, -1.63, .38)
            elif hp.startswith('hpmass'):
                target = (side*2.03, -1.63, 2.0)
        elif '_tail_' in part:
            target = {'hpcm01': (.58, .0, 7.3), 'hpmine01': (-.58, .0, 7.3),
                'hprunninglight03': (0, 4.9, 4.65), 'hprunninglight04': (0, -1.4, 4.65),
                'hpthruster01': (-.5, .6, 7.45), 'hpthruster02': (.5, .6, 7.45),
                'hpturret01': (0, 1.7, 7.45), 'hpturret02': (0, 4.9, 5.5),
                'hpturret03': (0, -1.4, 5.5)}.get(hp)
        elif part.startswith('rh_elite_'):
            target = {'hpweapon03': (-1.40, 1.905, .25), 'hpweapon04': (1.40, 1.905, .25),
                'hpshield01': (0, 2.26, 1.45), 'hpcontrail03': (-1.45, .8, 1.9),
                'hpcontrail04': (1.45, .8, 1.9), 'hprunninglight01': (.85, .55, -1.9),
                'hprunninglight02': (-.85, .55, -1.9), 'hpbaydoor01': (0, 1.8, -.1),
                'hpbaydoor02': (0, 2.1, 1.0), 'dpport_engine': (-2.03, -1.63, 2),
                'dpstarboard_engine': (2.03, -1.63, 2), 'dpport_wing': (-2.25, -1.65, 2.25),
                'dpstarboard_wing': (2.25, -1.65, 2.25), 'dptail': (0, 1.7, 3.0)}.get(hp)
        if target is not None:
            r, t = transforms[part]
            n.blob = np.asarray(r.T@(np.asarray(target)-t), '<f4').tobytes()


def merge(groups):
    # Avoid multiplying draw groups when separate armor pieces use the same material.
    by_material = {}
    for g in groups:
        by_material.setdefault(g['material'], []).append(g['corners'])
    return [dict(material=m, unused=204, corners=np.concatenate(v)) for m, v in by_material.items()]


def feature_wire(blob, mesh_crc, angle=35):
    """Feature edges using original vertex indices, including double-sided hatches."""
    vertices, groups, indices = audit.decode(blob)
    points = vertices[:, :3]
    representative = {}
    remap = [representative.setdefault(tuple(p.round(4)), i) for i, p in enumerate(points)]
    edges, triangles = {}, set()
    at = 0
    for _, base_index, _, count, _ in groups:
        for tri in (indices[at:at+count]+base_index).reshape(-1, 3):
            ids = tuple(remap[i] for i in tri)
            key = tuple(sorted(ids))
            # Front/back copies must not hide the boundary of a thin door.
            if key in triangles:
                continue
            triangles.add(key)
            a, b, c = points[list(ids)]
            n = np.cross(b-a, c-a)
            if np.linalg.norm(n) < 1e-8:
                continue
            n = mesh.unit(n)
            for u, v in zip(ids, ids[1:]+ids[:1]):
                edges.setdefault(tuple(sorted((u, v))), []).append(n)
        at += count
    threshold = math.cos(math.radians(angle))
    kept = [edge for edge, normals in edges.items() if len(normals) == 1 or
            (len(normals) == 2 and float(normals[0]@normals[1]) < -.99999) or
            any(abs(float(a@b)) < threshold for i, a in enumerate(normals) for b in normals[i+1:])]
    flat = [i for edge in sorted(kept) for i in edge]
    assert flat and len(flat) < 65536 and max(flat) < len(points)
    return common.struct.pack('<II4H', 16, mesh_crc, 0, len(set(flat)), len(flat), len(points)) + np.asarray(flat, '<u2').tobytes()


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    src = base.SOURCE.read_bytes()
    header, nodes = mesh.read_tree(src)
    before = {p: n.blob for p, n in mesh.walk(nodes)}
    tr0, _ = audit.transforms(nodes)
    libs = {mesh.crc(p.split('/')[-2]): audit.decode(n.blob)
            for p, n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    relocate(nodes)
    tr, _ = audit.transforms(nodes)
    library = mesh.child(nodes[0], 'VMeshLibrary')
    report, cockpit_checks, wire_meshes = [], [], {}
    for p, n in list(mesh.walk(nodes)):
        if not p.lower().endswith('/vmeshref'):
            continue
        part, lod = p.split('/')[2], int(p.split('/')[-3][-1])
        r0, t0 = tr0[part.lower()]
        old = base.world(audit.extract(n.blob, libs), r0, t0)
        new = old if '_glass_' in part.lower() else merge(design(part, old, lod))
        report.append(dict(part=part, lod=lod, before=sum(len(g['corners']) for g in old),
                           after=sum(len(g['corners']) for g in new), groups=len(new)))
        if '_glass_' in part.lower():
            continue
        if part.lower().startswith('rh_elite_'):
            cockpit_checks.append((p, common.cockpit(old)))
        r, t = tr[part.lower()]
        blob, verts = mesh.pack(base.world(new, r.T, -r.T@t))
        name = 'rh_b_'+hashlib.sha256((p+hashlib.sha256(blob).hexdigest()).encode()).hexdigest()[:16]+'.vms'
        child = mesh.Node(name)
        child.children = [mesh.Node('VMeshData', blob)]
        library.children.append(child)
        n.blob = mesh.make_ref(n.blob, name, blob, verts)
        if lod == 0:
            wire_meshes[part] = (blob, mesh.crc(name))
    totals = {str(lod): dict(before=sum(r['before'] for r in report if r['lod']==lod),
                            after=sum(r['after'] for r in report if r['lod']==lod)) for lod in range(3)}
    # Doors have Level0/Level1 only; their last LOD remains present at far distance.
    for key in ('before', 'after'):
        totals['2'][key] += sum(r[key] for r in report if r['lod']==1 and r['part'].lower().startswith('baydoor'))
    for lod, counts in totals.items():
        assert counts['after'] <= counts['before'], f'LOD{lod} over budget: {counts}'
    # Native per-component HUD wires reference the new mesh. Keep actual features,
    # not triangulation diagonals or UV seams. Glass retains its original wire.
    wire_count = 0
    for p, n in mesh.walk(nodes):
        part = p.split('/')[2] if len(p.split('/')) > 2 else ''
        if p.lower().endswith('/vwiredata') and part in wire_meshes:
            blob, crc = wire_meshes[part]
            n.blob = feature_wire(blob, crc)
            wire_count += 1
    assert wire_count == len(wire_meshes) == 8
    output = mesh.write_tree(header, nodes)
    _, decoded = mesh.read_tree(output)
    after = {p: n.blob for p, n in mesh.walk(decoded)}
    protected = [p for p in before if '/animation/' in p.lower() or '/rh_glass_' in p.lower()
                 or '/hpcockpit/' in p.lower() or '/hppilot/' in p.lower()]
    assert all(before[p] == after[p] for p in protected)
    dl = {mesh.crc(p.split('/')[-2]): audit.decode(n.blob)
          for p, n in mesh.walk(decoded) if p.lower().endswith('/vmeshdata')}
    for p, expected in cockpit_checks:
        actual = audit.extract(after[p], dl)
        for g in expected:
            # Original corner records survive material merging, in their original order.
            a = next(a for a in actual if a['material']==g['material'])
            assert np.array_equal(a['corners'][:len(g['corners'])].astype('<f4'), g['corners'].astype('<f4'))
    mats = audit.material_table([audit.DATA/p for p in base.ROW['materials']]+[base.SOURCE])
    for p, n in mesh.walk(decoded):
        if p.lower().endswith('/vmeshref'):
            for g in audit.extract(n.blob, dl):
                assert np.isfinite(g['corners']).all()
                assert g['material'] in mats
                assert np.allclose(np.linalg.norm(g['corners'][..., 3:6], axis=-1), 1, atol=1e-5)
        elif p.lower().endswith('/vwiredata'):
            _, mid, start, unique, count, maximum = common.struct.unpack_from('<II4H', n.blob)
            vertices = dl[mid][0]
            indices = np.frombuffer(n.blob, '<u2', count, 16).astype(int)+start
            assert indices.max() < len(vertices)
    assert base.SOURCE.read_bytes() == src
    DEST.write_bytes(output)
    stats = dict(source=str(base.SOURCE), concept=str(CONCEPTS/'rh_concept_B.png'),
        source_sha256=hashlib.sha256(src).hexdigest(), output_sha256=hashlib.sha256(output).hexdigest(),
        lods=totals, parts=report, protected_leaves=len(protected), updated_wireframes=wire_count,
        unchanged=['cockpit corner data at every LOD', 'glass', 'pilot/cockpit hardpoints', 'native animation channels'],
        limitations=['offline prototype; not installed', 'SUR and damage caps require rebuilding',
                     'full equipment clearance needs review'])
    (OUT/'checks.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
    print('PASS cockpit, animations, material refs. LOD triangle budgets:', totals, flush=True)
    return nodes


def preview(nodes, video=False):
    _, original = mesh.read_tree(base.SOURCE.read_bytes())
    old, new = common.scene(original), common.scene(nodes)
    mats = audit.material_table([audit.DATA/p for p in base.ROW['materials']]+[base.SOURCE])
    base.export_obj(OUT/'rh_concept_b.obj', new, mats)
    base.export_obj(OUT/'rh_source.obj', old, mats)
    for m in mats.values():
        if m['image'] is not None:
            m['image'] = m['image'].resize((512, 512), Image.Resampling.LANCZOS)
    poses = [common.scene(nodes, float(t), 1-float(t)) for t in np.linspace(0, 1, 25)]
    points = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for s in [old]+poses for g in s])
    assert np.isfinite(points).all()
    center = (points.min(axis=0)+points.max(axis=0))/2
    radius = np.linalg.norm(points-center, axis=1).max()
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 22)
    def render(sc, cam, size=700, mode='texture'):
        return audit.render(sc, mats, center, radius, cam, size, mode)
    views = [((1, .72, -1.3), 'texture'), ((1, .15, .01), 'texture'), ((0, 1, .001), 'texture')]
    pic = Image.new('RGB', (1400, 2230), (24, 29, 37))
    d = ImageDraw.Draw(pic)
    for col, (label, sc) in enumerate((('SOURCE / 1514 triangles', old),
                                     ('CONCEPT B / '+str(sum(len(g['corners']) for g in new))+' triangles', new))):
        d.text((col*700+15, 10), label, font=font, fill='white')
        for row, (cam, mode) in enumerate(views):
            pic.paste(render(sc, cam, 700, mode), (col*700, 50+row*720))
    pic.save(OUT/'comparison.jpg', quality=94)
    hero = render(new, (1, .6, -1.25), 1200)
    ImageDraw.Draw(hero).text((20, 15), 'RH / CONCEPT B / LOW-POLY MESH', font=font, fill='white')
    hero.save(OUT/'model.jpg', quality=95)
    pic = Image.new('RGB', (1400, 1500), (24, 29, 37))
    for col, (label, sc) in enumerate((('OPEN WINGS / CLOSED HATCH', new),
                                     ('FOLDED WINGS / OPEN HATCH', common.scene(nodes, 0, 1)))):
        ImageDraw.Draw(pic).text((700*col+15, 10), label, font=font, fill='white')
        for row, mode in enumerate(('texture', 'clay')):
            pic.paste(render(sc, (1, .7, -1.3), 700, mode), (700*col, 45+row*720))
    pic.save(OUT/'mechanics.jpg', quality=94)
    if video:
        ffmpeg = shutil.which('ffmpeg')
        assert ffmpeg
        size, fps, count = 600, 15, 120
        proc = subprocess.Popen([ffmpeg, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{2*size}x{size+40}', '-r', str(fps), '-i', '-', '-an', '-c:v', 'libx264',
            '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT/'animation.mp4')], stdin=subprocess.PIPE)
        for i in range(count):
            phase = .5+.5*math.cos(2*np.pi*i/(count-1))
            angle = .65-2*np.pi*i/(count-1)
            cam = (math.sin(angle), .6, -math.cos(angle))
            frame = Image.new('RGB', (2*size, size+40), (24, 29, 37))
            for col, (ns, label) in enumerate(((original, 'SOURCE'), (nodes, 'CONCEPT B'))):
                frame.paste(render(common.scene(ns, phase, 1-phase), cam, size), (col*size, 40))
                ImageDraw.Draw(frame).text((col*size+15, 5), label, font=font, fill='white')
            proc.stdin.write(frame.tobytes())
            if i % 30 == 0:
                print('Video', i, '/', count, flush=True)
        proc.stdin.close()
        assert proc.wait()==0
    stats = json.loads((OUT/'checks.json').read_text())
    stats['sampled_poses'] = 25
    (OUT/'checks.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
    (OUT/'README.txt').write_text(
        'RH CONCEPT B — малополигональный прототип по выбранному эскизу.\n'
        'Модель: rh_elite_concept_b.cmp. Статичная поза для Blender: rh_concept_b.obj.\n'
        'Материалы исходного rh_elite_pir; пушки отдельные, в геометрию не включены.\n'
        'Кабина, стекло и её точки сохранены; родные каналы анимации используются с новыми шарнирами.\n'
        'Треугольники по LOD (исходник -> прототип): '+str(stats['lods'])+'\n'
        'Каждый LOD проверяется на бюджет исходной модели, включая последние доступные LOD люка.\n'
        'Открытая рама и ферма — геометрия. Мелкие решётки, болты и швы — исходные текстуры.\n'
        'HUD wire обновлён по новой геометрии деталей, без диагоналей триангуляции.\n'
        'Это офлайн-прототип: SUR и damage caps ещё не приведены к новой форме.\n'
        'Игра не запускалась и не изменялась.\n', encoding='utf-8')
    with zipfile.ZipFile(OUT/'rh_concept_b.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in OUT.iterdir():
            if p.is_file() and p.suffix != '.zip':
                z.write(p, p.name)
    print('Ready:', OUT, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', action='store_true')
    args = parser.parse_args()
    preview(build(), args.video)
