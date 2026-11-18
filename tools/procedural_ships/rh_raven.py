"""Second RH pirate concept: a new airframe around the unmodified RH cockpit.

Offline only. Writes a separate CMP/OBJ and review renders, never game DATA.
"""
import argparse
import collections
import copy
import hashlib
import json
import math
import shutil
import struct
import subprocess
import zipfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import rh_pirate_prototype as base
from rh_redesign_paths import PROTOTYPE_V2

mesh, audit = base.mesh, base.audit
OUT = PROTOTYPE_V2
DEST = OUT / 'rh_raven.cmp'
PANEL = mesh.crc('pir_r_panel02_256')
METAL = mesh.crc('metal03D')
DARK = mesh.crc('metal03DK')
GRILL = mesh.crc('engine_grill01')
ARMOR_UV = (.675, .015, .985, .195)
RED_UV = (.025, .055, .14, .435)
SERVICE_UV = (.68, .22, .975, .47)


class Builder:
    def __init__(self):
        self.tris = collections.defaultdict(list)

    def face(self, points, material=PANEL, uvbox=ARMOR_UV, normal=None, uv=None):
        p = np.asarray(points, float)
        if normal is not None and np.dot(np.cross(p[1]-p[0], p[2]-p[0]), normal) < 0:
            p = p[::-1]
            if uv is not None:
                uv = np.asarray(uv)[::-1]
        if uv is None:
            n = abs(np.cross(p[1]-p[0], p[2]-p[0]))
            axes = np.delete(np.arange(3), np.argmax(n))
            q = p[:, axes]
            uv = (q-q.min(axis=0))/np.maximum(np.ptp(q, axis=0), 1e-5)
        uv = np.asarray(uv) * (np.array(uvbox[2:])-uvbox[:2]) + uvbox[:2]
        for i in range(1, len(p)-1):
            ids = [0, i, i+1]
            tri = p[ids]
            n = np.cross(tri[1]-tri[0], tri[2]-tri[0])
            if np.linalg.norm(n) < 1e-7:
                continue
            self.tris[material].append(np.column_stack((tri, np.tile(mesh.unit(n), (3, 1)), uv[ids])))

    def groups(self):
        return [dict(material=m, unused=204, corners=np.array(t)) for m, t in self.tris.items()]

    def plate(self, outline, bottom, top, side=1, inset=.9, material=PANEL,
              uvbox=ARMOR_UV, bevel=METAL, slope=0):
        """A convex plate with a continuous bevel, including its bottom face."""
        polygon = np.asarray(outline, float)
        center = polygon.mean(axis=0)
        small = center+(polygon-center)*inset
        lower = np.array([[side*x, bottom+slope*(x-polygon[0, 0]), z] for x, z in polygon])
        upper = np.array([[side*x, top+slope*(x-polygon[0, 0]), z] for x, z in small])
        uv = (small-polygon.min(axis=0))/np.maximum(np.ptp(polygon, axis=0), 1e-5)
        self.face(upper, material, uvbox, [0, 1, 0], uv)
        self.face(lower, bevel, (.1, .1, .4, .4), [0, -1, 0])
        center3 = np.concatenate((lower, upper)).mean(axis=0)
        for i in range(len(polygon)):
            j = (i+1) % len(polygon)
            points = np.array([lower[i], lower[j], upper[j], upper[i]])
            self.face(points, bevel, (.1, .1, .4, .4), points.mean(axis=0)-center3)

    def loft(self, sections, x=0, material=PANEL, caps=True, omit_top=False, rear_cap=True):
        """Octagonal cross sections (z, half width, bottom, top)."""
        rings = []
        for z, w, bottom, top in sections:
            h = top-bottom
            rings.append(np.array([(x-w*.7, top, z), (x+w*.7, top, z),
                (x+w, top-h*.23, z), (x+w, bottom+h*.23, z),
                (x+w*.7, bottom, z), (x-w*.7, bottom, z),
                (x-w, bottom+h*.23, z), (x-w, top-h*.23, z)]))
        for a, b in zip(rings, rings[1:]):
            center = np.concatenate((a, b)).mean(axis=0)
            for i in range(8):
                if omit_top and i == 0:
                    continue
                j = (i+1) % 8
                q = np.array([a[i], a[j], b[j], b[i]])
                self.face(q, material if i in (0, 1, 6, 7) else METAL,
                          ARMOR_UV, q.mean(axis=0)-center,
                          [[0, 0], [1, 0], [1, 1], [0, 1]])
        if caps:
            self.face(rings[0], METAL, ARMOR_UV, [0, 0, -1])
            if rear_cap:
                self.face(rings[-1], METAL, ARMOR_UV, [0, 0, 1])

    def tube(self, center, sections, sides=12, material=METAL, disk=False):
        """Open exhaust or hinge: (z, radius) sections, no fake emissive paint."""
        rings = []
        for z, r in sections:
            a = np.arange(sides)*2*np.pi/sides + np.pi/8
            rings.append(np.column_stack((center[0]+r*np.cos(a), center[1]+r*np.sin(a), np.full(sides, z))))
        for k, (a, b) in enumerate(zip(rings, rings[1:])):
            for i in range(sides):
                j = (i+1) % sides
                q = np.array([a[i], a[j], b[j], b[i]])
                # Correct winding for outer walls, rim and inward-facing throat.
                c = q.mean(axis=0)-np.array([*center, q[:, 2].mean()])
                if k >= 2:
                    c = -c
                self.face(q, material if k < 2 else DARK, (.1, .1, .5, .5), c)
        if disk:
            self.face(rings[-1], GRILL, (0, 0, 1, 1), [0, 0, 1])

    def fin(self, side):
        # Faceted, outward-canted rear blade. It is part of the detachable tail.
        yz = np.array([[.05, 3.45], [2.05, 5.8], [2.25, 7.85], [.15, 6.75]])
        faces = []
        for thickness in (-.12, .12):
            faces.append(np.array([[side*(1.4+.34*y+thickness), y, z] for y, z in yz]))
        self.face(faces[0], PANEL, ARMOR_UV, [-side, 0, 0])
        self.face(faces[1], PANEL, SERVICE_UV, [side, 0, 0])
        center = np.concatenate(faces).mean(axis=0)
        for i in range(4):
            j = (i+1) % 4
            q = np.array([faces[0][i], faces[0][j], faces[1][j], faces[1][i]])
            self.face(q, METAL, ARMOR_UV, q.mean(axis=0)-center)


def cockpit(groups):
    """All complete nose faces through the aft cockpit bulkhead, unchanged."""
    out = []
    for g in groups:
        mask = g['corners'][..., 2].max(axis=1) < -3.5
        if mask.any():
            item = copy.deepcopy(g)
            item['corners'] = item['corners'][mask]
            out.append(item)
    return out


def design(part, original, detail):
    b = Builder()
    name = part.lower()
    if name.startswith('rh_elite_'):
        # Broad low body; the cockpit module is neither scaled nor moved.
        b.loft([(-4.55, .96, -1.8, .63), (-3.5, 1.4, -1.65, .92),
                (-1.7, 2.18, -1.4, 1.05), (1.65, 2.25, -1.15, 1.05),
                (4.8, 1.72, -.85, .55), (6.1, 1.15, -.65, .18)], omit_top=True)
        # Roof flanks leave a real opening beneath the two animated hatch leaves.
        for side in (-1, 1):
            b.plate([(.80, -1.7), (1.52, -1.7), (1.575, 1.65), (.80, 1.65)], .90, 1.05, side)
            b.plate([(1.05, -3.7), (2.65, -2.4), (3.30, -.8), (2.8, 1.1), (1.6, .6)], -.2, .55, side)
            # A short lower blade projects behind the cabin, never over its glass.
            b.plate([(1.1, -3.9), (2.5, -3.55), (4.5, -1.0), (3.3, -.4), (1.5, -1.8)], -1.17, -.88, side)
            if detail:
                b.plate([(1.48, -3.15), (1.85, -2.92), (2.5, -.9), (2.08, -.7)], .34, .63, side, uvbox=RED_UV)
                b.plate([(1.35, .45), (2.10, .45), (2.1, 1.4), (1.35, 1.4)], 1.03, 1.12, side, material=METAL)
        b.face([[-.98, .63, -4.55], [.98, .63, -4.55], [1.52, 1.05, -1.7], [-1.52, 1.05, -1.7]],
               PANEL, ARMOR_UV, [0, 1, 0])
        b.face([[-1.575, 1.05, 1.65], [1.575, 1.05, 1.65], [1.204, .55, 4.8], [-1.204, .55, 4.8]],
               PANEL, SERVICE_UV, [0, 1, 0])
        b.face([[-1.204, .55, 4.8], [1.204, .55, 4.8], [.805, .18, 6.1], [-.805, .18, 6.1]],
               PANEL, ARMOR_UV, [0, 1, 0])
        if detail:
            # Individual radiator vanes give scale without covering the new form.
            for z in np.linspace(2.0, 4.3, 7):
                y = 1.05-(z-1.65)*.5/3.15
                b.plate([(-.7, z), (.7, z), (.7, z+.13), (-.7, z+.13)], y-.02, y+.09, material=DARK)
        return cockpit(original)+b.groups()
    if '_engine_' in name:
        side = -1 if '_port_' in name else 1
        x = side*2.85
        b.loft([(-2.7, .48, -.65, .15), (-1.55, .93, -1.25, .85),
                (2.6, 1.02, -1.30, .95), (4.65, .85, -1.1, .65),
                (5.25, .68, -.98, .48)], x=x, rear_cap=False)
        b.tube((x, -.27), [(4.9, .66), (5.7, .83), (5.78, .60), (5.02, .40)], disk=True)
        b.plate([(2.30, -1.5), (3.38, -1.5), (3.55, 2.4), (2.15, 2.4)], .75, 1.02, side)
        b.plate([(2.32, -1.42), (3.32, -1.42), (3.39, -.60), (2.25, -.60)], 1.005, 1.085, side, uvbox=RED_UV)
        if detail:
            for z in np.linspace(-.15, 1.9, 6):
                b.plate([(2.45, z), (3.23, z), (3.23, z+.13), (2.45, z+.13)], 1.0, 1.11, side, material=DARK)
            b.plate([(2.35, 3.05), (3.3, 3.05), (3.38, 3.70), (2.33, 3.70)], .64, .80, side, uvbox=RED_UV)
        return b.groups()
    if '_wing_' in name:
        side = -1 if '_port_' in name else 1
        # Entirely new, substantial wing. Same rotation channel, relocated hinge.
        b.plate([(3.55, -.35), (5.35, .40), (9.75, 5.55), (8.15, 6.15), (3.65, 3.10)],
                -.98, -.53, side, inset=.88, slope=.025)
        b.plate([(4.28, .65), (5.25, 1.04), (8.92, 5.40), (7.85, 5.52), (4.35, 2.86)],
                -.50, -.35, side, inset=.94, slope=.025)
        # A separate forward root pad gives the gun a real seating surface.
        b.plate([(4.0, .4), (5.0, .70), (5.20, 1.75), (4.15, 1.55)], -.45, -.16, side, material=METAL)
        if detail:
            b.plate([(5.5, 1.63), (5.98, 2.15), (7.48, 4.56), (6.98, 4.32)],
                    -.30, -.23, side, uvbox=RED_UV, slope=.025)
            b.plate([(6.0, 3.55), (7.28, 4.93), (7.05, 5.03), (5.73, 3.72)],
                    -.34, -.26, side, material=DARK, slope=.025)
        # Exposed hinge barrel, carried by the rotating component.
        b.tube((side*3.65, -.75), [(.15, .30), (2.5, .30)], sides=10)
        return b.groups()
    if name.startswith('baydoor'):
        side = -1 if name.startswith('baydoor01') else 1
        b.plate([(.015, -1.7), (.795, -1.7), (.795, 1.65), (.015, 1.65)], .93, 1.07, side,
                inset=.96, uvbox=RED_UV)
        return b.groups()
    if '_tail_' in name:
        # Low detachable spine and a forked tail replace the original vertical wheel.
        b.loft([(3.45, 1.45, -.7, .45), (5.65, 1.7, -.6, .25), (7.15, 1.35, -.45, .05)])
        for side in (-1, 1):
            b.fin(side)
            b.tube((side*.88, -.15), [(6.9, .23), (7.45, .29), (7.48, .18), (7.18, .11)], sides=8, disk=True)
        return b.groups()
    return original


def relocate(nodes):
    """Reuse native components/channels with explicit new mechanical origins."""
    for p, n in mesh.walk(nodes):
        if '/cmpnd/cons/' not in p.lower():
            continue
        size = 176 if p.lower().endswith('/fix') else 208
        blob = bytearray(n.blob)
        for at in range(0, len(blob), size):
            name = mesh.string(blob[at+64:at+128]).lower()
            f = np.frombuffer(blob, '<f4', (size-128)//4, at+128)
            side = -1 if 'port_' in name else 1
            if '_engine_' in name:
                f[:3] = (side*2.85, -.27, 2.2)
            elif '_wing_' in name:
                f[:3] = (side*3.65, -.75, .15)
            elif name.startswith('baydoor'):
                side = -1 if name.startswith('baydoor01') else 1
                f[:3] = (side*.795, 1.0, 0)
                f[3:6] = 0
                f[6:15] = np.eye(3).ravel()
                f[15:18] = (0, 0, -side)
            elif '_tail_' in name:
                f[:3] = (0, 0, 5.5)
        n.blob = bytes(blob)
    trans, _ = audit.transforms(nodes)
    for p, n in mesh.walk(nodes):
        if '/hardpoints/' not in p.lower() or not p.lower().endswith('/position'):
            continue
        part = p.split('/')[2].lower()
        hp = p.split('/')[-2].lower()
        side = -1 if '_port_' in part else 1
        target = None
        if '_wing_' in part:
            if hp.startswith('hpweapon'):
                target = (side*4.62, -.15, 1.12)
            elif hp.startswith(('hpcontrail', 'hpdocklight')):
                target = (side*9.35, -.55, 5.53)
        elif '_engine_' in part:
            if hp.startswith('hpengine'):
                target = (side*2.85, -.27, 5.71)
            elif hp.startswith('hprunninglight'):
                target = (side*2.85, .3, -2.25)
            elif hp.startswith('hpmass'):
                target = (side*2.85, -.27, 2.2)
        elif '_tail_' in part:
            target = {'hpcm01': (.8, -.3, 7.14), 'hpmine01': (-.8, -.3, 7.14),
                'hprunninglight03': (-2.08, 2.02, 7.5), 'hprunninglight04': (2.08, 2.02, 7.5),
                'hpthruster01': (-.88, -.15, 7.28), 'hpthruster02': (.88, -.15, 7.28),
                'hpturret01': (0, -.1, 7.1), 'hpturret02': (0, .35, 4.9),
                'hpturret03': (0, -.7, 4.9)}.get(hp)
        elif part.startswith('rh_elite_'):
            target = {'hpweapon03': (-1.72, 1.13, .94), 'hpweapon04': (1.72, 1.13, .94),
                'hpshield01': (0, .77, 3.35), 'hpcontrail03': (-4.35, -.95, -.95),
                'hpcontrail04': (4.35, -.95, -.95), 'hprunninglight01': (.98, .68, -3.9),
                'hprunninglight02': (-.98, .68, -3.9), 'hpbaydoor01': (0, 1.08, -.7),
                'hpbaydoor02': (0, 1.08, .7), 'dpport_engine': (-2.85, -.27, 2.2),
                'dpstarboard_engine': (2.85, -.27, 2.2), 'dpport_wing': (-3.65, -.75, .15),
                'dpstarboard_wing': (3.65, -.75, .15), 'dptail': (0, 0, 5.5)}.get(hp)
        if target is not None:
            r, t = trans[part]
            n.blob = np.asarray(r.T@(np.asarray(target)-t), '<f4').tobytes()


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    src = base.SOURCE.read_bytes()
    header, nodes = mesh.read_tree(src)
    before = {p: n.blob for p, n in mesh.walk(nodes)}
    original_transform, _ = audit.transforms(nodes)
    libs = {mesh.crc(p.split('/')[-2]): audit.decode(n.blob)
            for p, n in mesh.walk(nodes) if p.lower().endswith('/vmeshdata')}
    relocate(nodes)
    transforms, _ = audit.transforms(nodes)
    library = mesh.child(nodes[0], 'VMeshLibrary')
    report, nose_checks = [], []
    for p, n in list(mesh.walk(nodes)):
        if not p.lower().endswith('/vmeshref'):
            continue
        part = p.split('/')[2]
        if '_glass_' in part.lower():
            continue
        r0, t0 = original_transform[part.lower()]
        old = base.world(audit.extract(n.blob, libs), r0, t0)
        new = design(part, old, '/level0/' in p.lower())
        for g in new:
            g.setdefault('unused', 204)
        r, t = transforms[part.lower()]
        blob, verts = mesh.pack(base.world(new, r.T, -r.T@t))
        name = 'rh_raven_' + hashlib.sha256((p+hashlib.sha256(blob).hexdigest()).encode()).hexdigest()[:16]+'.vms'
        item = mesh.Node(name)
        item.children = [mesh.Node('VMeshData', blob)]
        library.children.append(item)
        n.blob = mesh.make_ref(n.blob, name, blob, verts)
        report.append(dict(part=part, lod=p.split('/')[-3],
            before=sum(len(g['corners']) for g in old), after=sum(len(g['corners']) for g in new)))
        if part.lower().startswith('rh_elite_'):
            nose_checks.append((p, cockpit(old)))
    out = mesh.write_tree(header, nodes)
    DEST.write_bytes(out)
    _, decoded = mesh.read_tree(out)
    after = {p: n.blob for p, n in mesh.walk(decoded)}
    # The actual cockpit assets and native animation scripts are protected.
    protected = [p for p in before if '/animation/' in p.lower() or '/rh_glass_' in p.lower()
                 or '/hpcockpit/' in p.lower() or '/hppilot/' in p.lower()]
    assert all(before[p] == after[p] for p in protected)
    dl = {mesh.crc(p.split('/')[-2]): audit.decode(n.blob)
          for p, n in mesh.walk(decoded) if p.lower().endswith('/vmeshdata')}
    count = 0
    for p, expected in nose_checks:
        actual = audit.extract(after[p], dl)
        for g in expected:
            # pack() may merge vertex indices, but the corner data must survive exactly.
            matches = [a for a in actual if a['material'] == g['material']]
            assert any(np.array_equal(a['corners'].astype('<f4'), g['corners'].astype('<f4')) for a in matches)
            count += len(g['corners'])
    for p, n in mesh.walk(decoded):
        if p.lower().endswith('/vmeshref'):
            for g in audit.extract(n.blob, dl):
                assert np.isfinite(g['corners']).all()
    assert base.SOURCE.read_bytes() == src
    stats = dict(source=str(base.SOURCE), source_sha256=hashlib.sha256(src).hexdigest(),
        output_sha256=hashlib.sha256(out).hexdigest(), protected_leaves=len(protected),
        cockpit_triangles_preserved_all_lods=count, modifications=report,
        unchanged=['cockpit exterior vertices/normals/UV/materials', 'glass', 'HpCockpit', 'HpPilot', 'native animation scripts'],
        changed=['hull', 'wings', 'engines', 'tail', 'bay doors', 'joint origins', 'non-cockpit equipment hardpoint locations'],
        limitations=['offline geometry prototype', 'SUR and damage caps not rebuilt',
                     'HUD wire still original', 'full equipment loadout clearance not tested in game'])
    (OUT/'checks.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
    print('PASS: cockpit faces, glass, pilot/cockpit points, native animation channels preserved', flush=True)
    return nodes


def scene(nodes, wing=1, door=0):
    posed = copy.deepcopy(nodes)
    data = {p.lower(): n.blob for p, n in mesh.walk(posed)}
    angles = {}
    for p, blob in data.items():
        if not p.endswith('/channel/frames'):
            continue
        phase = wing if '/sc_extend wing/' in p else door if '/sc_open baydoor/' in p else None
        if phase is None:
            continue
        frames = np.frombuffer(blob, '<f4').reshape(-1, 2)
        child = mesh.string(data[p.rsplit('/channel/', 1)[0]+'/child name']).lower()
        angles[child] = frames[0, 1]*(1-phase)+frames[-1, 1]*phase
    # Preview two native channels together; no animation bytes in the CMP are changed.
    for p, n in mesh.walk(posed):
        if '/cmpnd/cons/rev' not in p.lower():
            continue
        buf = bytearray(n.blob)
        for at in range(0, len(buf), 208):
            name = mesh.string(buf[at+64:at+128]).lower()
            f = np.frombuffer(buf, '<f4', 20, at+128)
            angle = angles.get(name, 0)
            if angle:
                axis = mesh.unit(f[15:18].astype(float))
                x, y, z = axis
                cross = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
                rot = np.eye(3)*math.cos(angle)+(1-math.cos(angle))*np.outer(axis, axis)+math.sin(angle)*cross
                f[6:15] = (rot@f[6:15].reshape(3, 3)).ravel()
        n.blob = bytes(buf)
    tr, _ = audit.transforms(posed)
    libs = {mesh.crc(p.split('/')[-2]): audit.decode(n.blob)
            for p, n in mesh.walk(posed) if p.lower().endswith('/vmeshdata')}
    out = []
    for p, n in mesh.walk(posed):
        if not p.lower().endswith('/vmeshref') or ('/multilevel/' in p.lower() and '/level0/' not in p.lower()):
            continue
        part = p.split('/')[2]
        r, t = tr[part.lower()]
        for g in base.world(audit.extract(n.blob, libs), r, t):
            g['part'] = part
            out.append(g)
    return out


def previews(nodes, video=False):
    _, original = mesh.read_tree(base.SOURCE.read_bytes())
    mats = audit.material_table([audit.DATA/p for p in base.ROW['materials']]+[base.SOURCE])
    old, new = scene(original), scene(nodes)
    base.export_obj(OUT/'rh_raven.obj', new, mats)
    base.export_obj(OUT/'rh_source.obj', old, mats)
    # Texture sampling mip for this offline rasterizer; original textures exported above.
    for m in mats.values():
        if m['image'] is not None:
            m['image'] = m['image'].resize((512, 512), Image.Resampling.LANCZOS)
    states = [scene(nodes, float(t), float(t)) for t in np.linspace(0, 1, 25)]
    allp = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for s in [old]+states for g in s])
    assert np.isfinite(allp).all()
    center = (allp.min(axis=0)+allp.max(axis=0))/2
    radius = np.linalg.norm(allp-center, axis=1).max()
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 23)
    small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
    def render(sc, cam, size=700, mode='texture', c=center, r=radius):
        return audit.render(sc, mats, c, r, cam, size, mode)
    def sheet(name, rows, columns):
        size = 700
        pic = Image.new('RGB', (size*len(columns), 60+(size+32)*len(rows)), (24, 29, 37))
        d = ImageDraw.Draw(pic)
        for col, (label, sc) in enumerate(columns):
            d.text((size*col+20, 10), label, font=font, fill='white')
            for row, (mode, camera, label2) in enumerate(rows):
                y = 55+row*(size+32)
                pic.paste(render(sc, camera, size, mode), (size*col, y+25))
                d.text((size*col+20, y), label2, font=small, fill=(166, 184, 199))
        pic.save(OUT/name, quality=94)
    sheet('comparison.jpg', [('texture', (1, .85, -1.4), 'FRONT / THREE QUARTER'),
                            ('texture', (0, 1, .001), 'TOP'),
                            ('texture', (-1, .65, 1.4), 'REAR / THREE QUARTER')],
          [('SOURCE / RH PIRATE', old), ('V2 / RAVEN / ORIGINAL RH COCKPIT', new)])
    sheet('mechanics.jpg', [('texture', (1, .7, -1.3), 'TEXTURED'),
                           ('clay', (1, .7, -1.3), 'GEOMETRY')],
          [('WINGS EXTENDED / HATCH CLOSED', new), ('WINGS FOLDED / HATCH OPEN', scene(nodes, 0, 1))])
    hero = render(new, (1, .65, -1.35), 1100, c=np.array([0, -.2, .5]), r=10.5)
    ImageDraw.Draw(hero).text((25, 20), 'RH / RAVEN — V2', font=font, fill='white')
    hero.save(OUT/'raven.jpg', quality=95)
    # A separate, identical-camera cockpit inspection pair.
    cp = Image.new('RGB', (1400, 730), (24, 29, 37))
    for col, (label, sc) in enumerate((('SOURCE', old), ('V2 / COCKPIT UNCHANGED', new))):
        cp.paste(render(sc, (1, .4, -1.5), 700, c=np.array([0, -.5, -6.2]), r=3), (col*700, 30))
        ImageDraw.Draw(cp).text((col*700+15, 5), label, font=small, fill='white')
    cp.save(OUT/'cockpit.jpg', quality=95)
    stats = json.loads((OUT/'checks.json').read_text())
    stats.update(triangles_before=sum(len(g['corners']) for g in old),
                 triangles_after=sum(len(g['corners']) for g in new), sampled_mechanical_poses=25)
    (OUT/'checks.json').write_text(json.dumps(stats, indent=2), encoding='utf-8')
    print('Renders and OBJ ready. Triangles:', stats['triangles_after'], flush=True)
    if video:
        ffmpeg = shutil.which('ffmpeg')
        assert ffmpeg
        size, fps, count = 640, 15, 120
        proc = subprocess.Popen([ffmpeg, '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24',
            '-s', f'{size*2}x{size+40}', '-r', str(fps), '-i', '-', '-an', '-c:v', 'libx264',
            '-crf', '19', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(OUT/'raven_animation.mp4')], stdin=subprocess.PIPE)
        for i in range(count):
            t = i/(count-1)
            wing = .5+.5*math.cos(2*np.pi*t)
            angle = -.6+2*np.pi*t
            cam = (math.sin(angle), .65, -math.cos(angle))
            pic = Image.new('RGB', (size*2, size+40), (24, 29, 37))
            for col, (ns, label) in enumerate(((original, 'SOURCE'), (nodes, 'V2 / RAVEN'))):
                pic.paste(render(scene(ns, wing, 1-wing), cam, size), (size*col, 40))
                ImageDraw.Draw(pic).text((size*col+15, 7), label, font=font, fill='white')
            proc.stdin.write(pic.tobytes())
            if i % 30 == 0:
                print('Video frame', i, '/', count, flush=True)
        proc.stdin.close()
        assert proc.wait() == 0
    (OUT/'README.txt').write_text(
        'RH RAVEN V2 — новый корпус вокруг неизменной кабины RH.\n'
        'Низкий корпус, мотогондолы, складывающиеся крылья, носовые консоли, раздвоенная корма.\n'
        'Кабина: исходные координаты, нормали, UV, материалы и стекло; HpCockpit/HpPilot не изменены.\n'
        'Существующие каналы анимации сохранены, шарниры и точки оборудования перенесены на новые детали.\n'
        'Видео: офлайн-оборот модели, складывание крыльев и открытие люка; это не запись игры.\n'
        'CMP использует исходные библиотеки материалов rh_elite_pir. OBJ — статичная поза для Blender.\n'
        'Первый вариант находится рядом, в ../v1/.\n'
        'Прототип формы: SUR, damage caps, HUD wire и проверка полного вооружения ещё требуют работы.\n'
        'Игра не запускалась и не изменялась.\n', encoding='utf-8')
    with zipfile.ZipFile(OUT/'rh_raven_v2.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for p in OUT.iterdir():
            if p.is_file() and p.suffix != '.zip':
                z.write(p, p.name)
    print('Ready:', OUT, flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--video', action='store_true')
    args = parser.parse_args()
    previews(build(), args.video)
