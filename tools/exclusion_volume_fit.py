"""Fit the unlit shell to representative GPU-rendered surrounding cloud midtones."""
import io
import json
from pathlib import Path
import statistics
from PIL import Image, ImageChops, ImageDraw
from generate_station_lods import read_tree

OUT = Path('src/obj/exclusion_volume')
GAME = Path('D:/games/FL_MOD')


def main():
    _, roots = read_tree((GAME / 'DATA/SOLAR/NEBULA_MOD/exclusion_walker_new.3db').read_bytes())
    lib = next(n for n in roots[0].children if n.name.lower() == 'texture library')
    tex = lib.children[0]
    leaf = next(n for n in tex.children if n.name.lower() in ('mip0', 'mips'))
    shell = Image.open(io.BytesIO(leaf.blob)).convert('RGB').resize((288, 216))
    sample = json.loads(Path('src/obj/exclusion_palette/textures.json').read_text())
    mean = sample['solar\\nebula_mod\\exclusion_walker_new.3db']['mean_rgb']
    targets, rows = {}, []
    for source in sorted(OUT.glob('*.bin')):
        name = source.stem
        colours = []
        for i in range(6):
            im = Image.open(OUT / f'{name}_surrounding_{i}.png').convert('RGB')
            pixels = sorted(im.getdata(), key=lambda p: .2126*p[0]+.7152*p[1]+.0722*p[2])
            middle = pixels[int(len(pixels)*.4):int(len(pixels)*.75)]
            colours.append([sum(p[c] for p in middle)/len(middle) for c in range(3)])
        target = [round(statistics.median(p[c] for p in colours), 2) for c in range(3)]
        tint = [min(255, round(255*x/m)) for x,m in zip(target,mean)]
        targets[name] = {'rgb': target, 'tint': tint, 'view_midtones': colours,
                         'method': 'median of six views; mean of 40th..75th luminance percentile per view'}
        row = Image.new('RGB', (1180, 290), '#202027'); d = ImageDraw.Draw(row)
        d.text((8, 5), name + ' - diagnostic GPU reference, not an in-game screenshot', fill='white')
        for x, label, img in [
            (8, 'Volume: side light', Image.open(OUT/f'{name}_surrounding_1.png').resize((288,216))),
            (302, 'Volume: toward sun', Image.open(OUT/f'{name}_surrounding_0.png').resize((288,216))),
            (596, 'Shell before (unlit texture)', shell),
            (890, 'Shell after (unlit texture)', ImageChops.multiply(shell, Image.new('RGB',shell.size,tuple(tint))))]:
            row.paste(img,(x,42)); d.text((x,25),label,fill='white')
        d.text((8,270), f'Target RGB: {target}; tint: {tint}. Shell swatches omit alpha/background; geometry and max_alpha unchanged.', fill='white')
        rows.append(row)
    sheet=Image.new('RGB',(1180,len(rows)*290))
    for i,row in enumerate(rows):sheet.paste(row,(0,i*290))
    sheet.save(OUT/'om15_comparison.png')
    (OUT/'targets.json').write_text(json.dumps(targets,indent=2))
    print(json.dumps({k:v['tint'] for k,v in targets.items()},indent=2))


if __name__=='__main__': main()
