"""Read-only native freighter baydoor poses; render source meshes, no AI image edits."""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import pirate_art_audit as a
from rh_redesign_paths import TOPIC

OUT = TOPIC / 'rh_freighter/references/baydoor'


def main():
    assert shutil.disk_usage(TOPIC.anchor).free > 1024**3
    OUT.mkdir(parents=True, exist_ok=True)
    source = json.loads((TOPIC / 'pirate_art/ships/rh_freighter_pir/source.json').read_text())
    path = a.source.DATA / source['model']
    assert a.sha(path) == source['sha256']
    scene, mats, stats = a.source.load(source)
    # Cmpnd lookup is case-insensitive; the renderer preserves original spelling.
    scene = [dict(g, part=g['part'].lower()) for g in scene]
    _, nodes = a.source.mesh.read_tree(path.read_bytes())
    flat = {p.lower(): n.blob for p, n in a.source.mesh.walk(nodes)}
    constructs = a.full.constructs(flat)
    channels = a.full.channels(flat, constructs)
    door = next(c for c in channels if c['script'] == 'sc_rh_freighter')
    assert door['bound_joint'] and door['native_size_valid'] and not door.get('parent_mismatch')
    # Sample wing t=0 plus bay time by remapping the four constant flight values
    # into the same temporary sampler script. This does not change the CMP.
    sampled = [door] + [dict(c, script=door['script'], times=[0, door['duration']],
                             values=[c['first'], c['first']])
                         for c in channels if c['script'] == a.SCRIPT]
    record = dict(path=source['model'], constructs=constructs, channels=sampled)
    poses = [a.motion.scene_at(record, scene, t, door['script'])
             for t in (0, door['duration'] / 2, door['duration'])]
    sheet = Image.new('RGB', (1800, 1280), a.BG)
    d = ImageDraw.Draw(sheet)
    d.text((15, 10), 'ACTUAL RH FREIGHTER / rotating curved cargo shutter / unchanged source mesh', font=a.FONT, fill='white')
    for row, camera in enumerate(((1, .55, -1.2), (1, 0, 0))):
        for col, pose in enumerate(poses):
            # Focus on the curved roof rather than the lower belly and engines.
            im = a.source.render(pose, mats, np.array([0., 3.0, .94]), 11.5, camera, 600, 'texture')
            sheet.paste(im, (col * 600, 60 + row * 600))
            d.text((col * 600 + 12, 40 + row * 600),
                   ['CLOSED / 0 deg', 'OPENING / 60 deg', 'OPEN / 120 deg'][col], font=a.FONT, fill='white')
    d.text((15, 1255), 'Offline native-key reconstruction. Roof side cheeks are fixed; curved shutter rotates about transverse X.', font=a.SMALL, fill='white')
    sheet.save(OUT / 'native_baydoor_motion.jpg', quality=96)
    bounds = []
    for pose in poses:
        p = np.concatenate([g['corners'][..., :3].reshape(-1, 3) for g in pose if 'baydoor' in g['part']])
        bounds.append(dict(min=p.min(0).tolist(), max=p.max(0).tolist(), center=p.mean(0).tolist()))
    report = dict(source=str(path), sha256=source['sha256'],
                  joint=next(c for c in constructs if c['name'].lower() == door['child'].lower()),
                  channel=door, moving_part_bounds=bounds,
                  native_baydoor_triangles=sum(len(g['corners']) for g in scene if 'baydoor' in g['part']),
                  runtime='CShip::open_bay EvalPlayback reverse=0; close_bay reverse=1; common_cship.cpp',
                  limitations='Offline reconstruction, not an in-game observation or collision clearance validation.')
    (OUT / 'audit.json').write_text(json.dumps(report, indent=2), encoding='utf8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
