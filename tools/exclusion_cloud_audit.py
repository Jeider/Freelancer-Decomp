"""Measure the actual cloud atlas regions referenced by Pythonlancer panels."""
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat
from generate_station_lods import read_tree

DATA = Path('D:/games/FL_MOD/DATA')
OUT = Path('src/obj/exclusion_palette')


def main():
    samples, rows, cache = {}, [], {}
    for family in ('generic', 'edge', 'crow', 'walker', 'white'):
        panel = f'solar/nebula/{family}_shapes.ini'
        file = texture = shape = None
        for raw in (DATA / panel).read_text().splitlines():
            if '=' not in raw:
                continue
            key, value = (s.strip() for s in raw.split('=', 1))
            if key == 'file':
                file = value
            elif key == 'texture_name':
                texture = value
            elif key == 'shape_name':
                shape = value
            elif key == 'dim' and '_cloud' in shape:
                if (file, texture) not in cache:
                    _, roots = read_tree((DATA / file.replace('\\', '/')).read_bytes())
                    lib = next(n for n in roots[0].children if n.name.lower() == 'texture library')
                    tex = next(n for n in lib.children if n.name.lower() == texture.lower())
                    leaf = next(n for n in tex.children if n.name.lower() in ('mip0', 'mips'))
                    cache[file, texture] = Image.open(io.BytesIO(leaf.blob)).convert('RGBA')
                atlas = cache[file, texture]
                x, y, w, h = map(float, value.split(','))
                im = atlas.crop((round(x * atlas.width), round(y * atlas.height),
                                 round((x + w) * atlas.width), round((y + h) * atlas.height)))
                # Full-resolution, alpha-weighted colour; transparent RGB is not visible.
                mean = ImageStat.Stat(im.convert('RGB'), im.getchannel('A')).mean
                coverage = ImageStat.Stat(im.getchannel('A')).mean[0] / 255
                samples.setdefault(panel.replace('/', '\\'), {})[shape] = [mean, coverage]
                im.thumbnail((140, 140))
                row = Image.new('RGB', (500, 165), '#202027')
                row.paste(im, (0, 20), im)
                ImageDraw.Draw(row).text((155, 30), f'{shape}\nRGB {tuple(round(v, 1) for v in mean)}\nalpha {coverage:.3f}', fill='white')
                rows.append(row)
    sheet = Image.new('RGB', (1000, ((len(rows) + 1) // 2) * 165))
    for i, row in enumerate(rows):
        sheet.paste(row, ((i % 2) * 500, (i // 2) * 165))
    sheet.save(OUT / 'cloud_textures.png')
    (OUT / 'cloud_samples.json').write_text(json.dumps(samples, indent=2))
    print(f'Measured {sum(map(len, samples.values()))} cloud atlas regions')


if __name__ == '__main__':
    main()
