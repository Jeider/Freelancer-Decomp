"""Read the installed shell textures; export an audit sheet without changing assets."""
import ast
import io
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageStat
from generate_station_lods import read_tree

ROOT = Path('D:/games/FL_MOD')
OUT = Path('src/obj/exclusion_palette')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source = ROOT / 'Assets/Pythonlancer/templates/nebula/exclusion.py'
    paths = {}
    for node in ast.parse(source.read_text()).body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant):
            if isinstance(node.value.value, str) and node.value.value.endswith('.3db'):
                paths[node.targets[0].id] = node.value.value
    rows, report = [], {}
    for name, relative in paths.items():
        _, roots = read_tree((ROOT / 'DATA' / relative.replace('\\', '/')).read_bytes())
        lib = next(n for n in roots[0].children if n.name.lower() == 'texture library')
        row = Image.new('RGB', (1100, 230), '#202027')
        draw = ImageDraw.Draw(row)
        draw.text((8, 5), name, fill='white')
        means, textures = [], []
        for i, tex in enumerate(lib.children):
            leaf = next(n for n in tex.children if n.name.lower() in ('mip0', 'mips'))
            im = Image.open(io.BytesIO(leaf.blob)).convert('RGBA')
            im.thumbnail((300, 175))
            mean = ImageStat.Stat(im.convert('RGB'), im.getchannel('A')).mean
            means.append(mean)
            textures.append({'name': tex.name, 'mean_rgb': mean})
            row.paste(im, (8 + i * 360, 30), im)
            draw.text((8 + i * 360, 208), tex.name, fill='white')
        report[relative] = {'textures': textures,
                            'mean_rgb': [sum(m[c] for m in means) / len(means) for c in range(3)]}
        rows.append(row)
    sheet = Image.new('RGB', (1100, len(rows) * 230))
    for i, row in enumerate(rows):
        sheet.paste(row, (0, i * 230))
    sheet.save(OUT / 'textures.png')
    (OUT / 'textures.json').write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v['mean_rgb'] for k, v in report.items()}, indent=2))


if __name__ == '__main__':
    main()
