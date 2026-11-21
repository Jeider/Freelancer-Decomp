"""Render native BH glazing and nearby original frame surfaces only.

Read-only CMP inspection. A spatial clip excludes the old nose/chin and fins.
This is source-geometry rendering, not an edit of existing concept images.
The spatial clip is a reference crop, not a proposed export boundary.
"""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

import numpy as np

import bw_family_audit as layout

ROOT = Path(__file__).resolve().parents[2]
TOPIC = ROOT / 'out/ship_design/bh_family'
OUT = TOPIC / 'references/glazing_only'


def clip(poly, axis, value, greater):
    result = []
    for i, current in enumerate(poly):
        previous = poly[i-1]
        a = (previous[axis] >= value) if greater else (previous[axis] <= value)
        b = (current[axis] >= value) if greater else (current[axis] <= value)
        if a != b:
            t = (value-previous[axis]) / (current[axis]-previous[axis])
            result.append(previous+t*(current-previous))
        if b:
            result.append(current)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', choices=('bh', 'li'), default='bh')
    args = parser.parse_args()
    out = OUT if args.source == 'bh' else TOPIC/'references/li_glazing_only'
    label = 'BH' if args.source == 'bh' else 'LI FREIGHTER'
    assert shutil.disk_usage(ROOT).free > 256*1024**2
    report_path = TOPIC/('elite/source_audit.json' if args.source == 'bh' else 'references/li_freighter/source_audit.json')
    report = json.loads(report_path.read_text(encoding='utf8'))
    values = report['archetype']
    spec = dict(model=values['da_archetype'][0].replace('\\', '/').lower(),
                materials=[p.replace('\\', '/').lower() for p in values['material_library']])
    scene, mats, stats = layout.a.source.load(spec)
    assert stats['sha256'] == report['source_sha256']
    glass = [g for g in scene if 'glass' in mats[g['material']]['name'].lower()]
    points = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in glass])
    low, high = points.min(0), points.max(0)
    # Keep real source surface immediately surrounding the panes; no constructed
    # rim, guessed pane contours or retained lower nose pod.
    padding = np.array([.13, .13, .13])
    lo, hi = low-padding, high+padding
    crop = []
    for g in scene:
        triangles = []
        for tri in g['corners']:
            if np.any(tri[:, :3].max(0) < lo) or np.any(tri[:, :3].min(0) > hi):
                continue
            poly = list(tri)
            for axis in range(3):
                poly = clip(poly, axis, lo[axis], True)
                if not poly:
                    break
                poly = clip(poly, axis, hi[axis], False)
                if not poly:
                    break
            for i in range(1, len(poly)-1):
                triangles.append([poly[0], poly[i], poly[i+1]])
        if triangles:
            crop.append(dict(g, corners=np.array(triangles)))
    center = (lo+hi)/2
    radius = float(np.linalg.norm(hi-lo)/2)*1.1
    cams = [((1, .55, -1.4), 'FRONT 3/4'), ((1, 0, 0), 'SIDE'),
            ((0, 0, -1), 'FRONT'), ((0, 1, .000001), 'TOP')]
    out.mkdir(parents=True, exist_ok=True)
    for source, filename, heading in [
        (crop, 'native_glazing_frame.jpg', label+' / ORIGINAL GLAZING + NEARBY NATIVE FRAME / NO NOSE POD'),
        (glass, 'native_glazing_only.jpg', label+' / EXACT ORIGINAL GLASS / THREE PANES')]:
        rows = [[(label, layout.a.source.render(source, mats, center, radius, cam, 550, 'texture'))
                 for cam, label in cams[i:i+2]] for i in (0, 2)]
        layout.sheet(out/filename, rows, 2, heading,
                     'Native mesh / only glass and frame locked / pylon, antennas, old chin and surrounding body are optional', size=550)
    model = Path(report['source_model'])
    audit = dict(source_model=model.as_posix(), source_sha256=stats['sha256'],
                 source_unchanged=hashlib.sha256(model.read_bytes()).hexdigest()==stats['sha256'],
                 glazing_bounds=dict(min=low.tolist(), max=high.tolist()),
                 glass_triangles=sum(len(g['corners']) for g in glass),
                 crop_bounds=dict(min=lo.tolist(), max=hi.tolist()),
                 method='Original pane geometry and original shell clipped to pane AABB + 0.13 units. No generated frame; reference crop is not an exact export selection.',
                 user_constraint='Only original glazing and its frame are immutable. Roof pylon is optional, not a cockpit component. Chin, forehead beyond frame, nose pod, hull, fins and engines may be redesigned.',
                 references=[dict(path=p.as_posix(), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(out.glob('*.jpg'))])
    assert audit['source_unchanged']
    (out/'audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    print(json.dumps(dict(glass_triangles=audit['glass_triangles'], source_unchanged=True, output=str(out))))


if __name__ == '__main__':
    main()
