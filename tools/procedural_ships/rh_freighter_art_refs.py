"""Prepare original RH pirate freighter references/prompts; no image-model calls."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import pirate_art_audit as a
from rh_redesign_paths import TOPIC

OUT = TOPIC / 'rh_freighter/concepts/round_02'


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    refs = OUT / 'references'
    refs.mkdir(exist_ok=True)
    source_dir = a.OUT / 'ships/rh_freighter_pir'
    row = json.loads((source_dir / 'source.json').read_text(encoding='utf8'))
    assert a.sha(a.source.DATA / row['model']) == row['sha256']
    scene, mats, stats = a.source.load(row)
    center, radius = np.array([0., -.7, -9.6]), 4.1
    panel = Image.new('RGB', (1800, 670), a.BG)
    draw = ImageDraw.Draw(panel)
    draw.text((12, 8), 'RH PIR FREIGHTER / EXACT ORIGINAL CABIN / preserve this component unchanged',
              font=a.FONT, fill='white')
    for i, (camera, label) in enumerate([((1, .35, -1.4), 'front 3/4'),
                                        ((0, 0, -1), 'front'), ((1, 0, 0), 'side')]):
        panel.paste(a.source.render(scene, mats, center, radius, camera, 600, 'texture'), (i * 600, 40))
        draw.text((i * 600 + 12, 30), label, font=a.SMALL, fill='white')
    draw.text((12, 645), 'Original CMP geometry. Camera close-ups, not an isolated mesh. Offline glass shading is approximate.',
              font=a.SMALL, fill=(190, 200, 210))
    cockpit = refs / 'cockpit_original.jpg'
    panel.save(cockpit, quality=96)
    record = dict(path=row['model'], constructs=row['constructs'], channels=row['wing_channels'])
    panel = Image.new('RGB', (1440, 790), a.BG)
    draw = ImageDraw.Draw(panel)
    for i, (time, label) in enumerate([(0, 'FLIGHT / cylinders extended'),
                                        (row['wing_duration'], 'STOWED / cylinders withdrawn')]):
        pose = a.motion.scene_at(record, scene, time, a.SCRIPT)
        im = a.source.render(pose, mats, np.array([0., 2., -.5]), 5.4, (1, .2, -.15), 720, 'texture')
        panel.paste(im, (i * 720, 40))
        draw.text((i * 720 + 12, 10), label, font=a.FONT, fill='white')
    draw.text((12, 765), 'Native RH pirate freighter side cylinders / offline reference / source geometry unchanged',
              font=a.SMALL, fill='white')
    panel.save(refs / 'side_cylinders_original.jpg', quality=95)
    from rh_freighter_multiview_prompts import main as write_prompts
    write_prompts()


if __name__ == '__main__':
    main()
