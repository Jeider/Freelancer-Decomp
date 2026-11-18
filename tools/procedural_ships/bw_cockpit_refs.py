"""Render exact native BW glazing contours and shell for image-generator guidance.

Reads current CMP only; produces new source-geometry reference renders, not edits
of concept images. Pane outlines are boundary edges from the original triangles.
"""
import collections
import hashlib
import json
import shutil

import numpy as np
from PIL import Image, ImageDraw

import pirate_art_audit as a
from rh_redesign_paths import TOPIC

OUT = TOPIC/'bw_family/references/cockpit_lock'


def main():
    assert shutil.disk_usage(TOPIC).free > 256*1024**2
    OUT.mkdir(parents=True, exist_ok=True)
    source = json.loads((a.OUT/'ships/bw_elite2_pir/source.json').read_text(encoding='utf8'))
    scene, mats, stats = a.source.load(source)
    assert stats['sha256'] == source['sha256']
    glass = [g for g in scene if 'glass' in mats[g['material']]['name'].lower()]
    pts = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in glass])
    center = (pts.min(0)+pts.max(0))/2
    radius = 2.35
    size = 800
    cameras = [((-1., .65, -1.4), 'THREE-QUARTER / nose points LEFT'),
               ((0., 1., .000001), 'TOP / nose points UP'),
               ((0., 0., -1.), 'FRONT'), ((-1., 0., 0.), 'SIDE / nose points LEFT')]
    # Geometric boundaries, not intermediate triangle edges or guessed contours.
    counts = collections.Counter()
    for g in glass:
        for tri in g['corners'][..., :3]:
            keys = [tuple(np.round(v, 5)) for v in tri]
            for i in range(3):
                counts[tuple(sorted((keys[i], keys[(i+1)%3])))] += 1
    edges = [edge for edge, count in counts.items() if count == 1]
    adjacency = collections.defaultdict(set)
    for p, q in edges:
        adjacency[p].add(q)
        adjacency[q].add(p)
    assert all(len(v) == 2 for v in adjacency.values())
    unseen = set(adjacency)
    panes = []
    while unseen:
        start = min(unseen)
        loop = [start]
        previous, current = None, start
        while True:
            following = next(v for v in sorted(adjacency[current]) if v != previous)
            if following == start:
                break
            loop.append(following)
            previous, current = current, following
        unseen.difference_update(loop)
        panes.append(loop)
    assert len(panes) == 3, len(panes)
    for textured, name in [(True, 'native_cockpit_textured.jpg'), (False, 'native_cockpit_shape.jpg')]:
        render_mats = mats if textured else {k:dict(v, image=None, colour=np.ones(3)) for k,v in mats.items()}
        board = Image.new('RGB', (2*size, 2*size+105), a.BG)
        d = ImageDraw.Draw(board)
        d.text((18, 10), 'ORIGINAL BW CABIN / THREE NATIVE GLASS PANES / EXACT SOURCE GEOMETRY', font=a.FONT, fill='white')
        for i, (cam, label) in enumerate(cameras):
            x, y = (i%2)*size, 45+(i//2)*(size+25)
            im = a.source.render(scene, render_mats, center, radius, cam, size, 'texture')
            board.paste(im, (x, y+23))
            d.text((x+14, y), label, font=a.SMALL, fill='white')
        d.text((18, board.height-25), 'Glazing rises along the sloping cabin crown. The top view is essential. No canopy redesign.', font=a.SMALL, fill='white')
        board.save(OUT/name, quality=97)
    # Standalone technical projections from the source glass triangles; thin
    # cyan perimeter lines distinguish the pane boundary from triangulation.
    board = Image.new('RGB', (2*size, 2*size+105), a.BG)
    d = ImageDraw.Draw(board)
    d.text((18, 10), 'NATIVE GLASS ONLY / EXACT OUTLINES / DO NOT REPLACE WITH RECTANGULAR WINDSHIELD', font=a.FONT, fill='white')
    for i, (cam, label) in enumerate(cameras):
        x, y = (i%2)*size, 45+(i//2)*(size+25)
        im = a.source.render(glass, mats, center, radius, cam, size, 'texture')
        draw = ImageDraw.Draw(im)
        forward = np.array(cam)/np.linalg.norm(cam)
        right = np.cross([0,1,0], forward); right /= np.linalg.norm(right)
        up = np.cross(forward, right)
        rot = np.stack((right, up, forward))
        # All panes are shown as technical contours, including hidden edges.
        for edge in edges:
            q = (np.array(edge)-center)@rot.T
            xy = q[:,:2]*size*.46/radius
            xy[:,0] += size/2; xy[:,1] = size/2-xy[:,1]
            draw.line([tuple(v) for v in xy], fill=(94,200,220), width=3)
        board.paste(im, (x, y+23))
        d.text((x+14, y), label, font=a.SMALL, fill='white')
    d.text((18, board.height-25), 'Cyan = original boundary edges. Hidden contours also shown. Three glass panes; no invented mullions.', font=a.SMALL, fill='white')
    board.save(OUT/'native_glass_contours.jpg', quality=97)
    report = dict(source_model=(a.source.DATA/source['model']).as_posix(), source_sha256=stats['sha256'],
                  source_unchanged=a.sha(a.source.DATA/source['model'])==stats['sha256'],
                  boundary_panes=panes, pane_count=len(panes), boundary_edges=len(edges),
                  source_glass_triangles=sum(len(g['corners']) for g in glass),
                  extraction='True boundary edges of native glass triangles, rounded to 1e-5 only for shared-vertex matching.',
                  previous_prompt_error='Previous instruction asked for solid roof and a front windshield; native central glazing continues up the sloping cabin crown.',
                  render_notes='Native source geometry only, software opaque glass; no source edits; no model installation.',
                  references=[dict(path=p.as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(OUT.glob('*.jpg'))])
    (OUT/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print(json.dumps(dict(panes=len(panes),edges=len(edges),vertices_per_pane=[len(p) for p in panes],source_unchanged=report['source_unchanged'],out=str(OUT))))


if __name__ == '__main__':
    main()
