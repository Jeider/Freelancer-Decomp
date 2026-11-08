"""Stage and validate the Pythonlancer-only palette patch; --apply installs exact staged bytes."""
import argparse
import ast
import hashlib
import io
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace, ModuleType
from PIL import Image, ImageDraw, ImageChops
import exclusion_palette_runtime as palette_runtime
from generate_station_lods import read_tree
from exclusion_palette_runtime import match_exclusion_palette

ROOT = Path('D:/games/FL_MOD/Assets/Pythonlancer')
OUT = Path('src/obj/exclusion_palette')
FILES = ('templates/nebula/exclusion.py', 'universe/content/zones.py', 'templates/nebula/sig8_nebula.py')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def prepare():
    manifest = {}
    cloud_samples = json.loads((OUT / 'cloud_samples.json').read_text())
    palette_runtime.CLOUD_TEXTURE_SAMPLES = cloud_samples
    for relative in FILES:
        original = (ROOT / relative).read_bytes()
        text = original.decode('utf-8')
        newline = '\r\n' if '\r\n' in text else '\n'
        text = text.replace('\r\n', '\n')
        if relative.endswith('exclusion.py'):
            marker = '# Texture averages measured from the installed exclusion .3db texture libraries.'
            if marker in text:
                text = text[:text.index(marker)]
            runtime = Path('tools/exclusion_palette_runtime.py').read_text()
            runtime = runtime.replace('{}  # CLOUD_SAMPLES', repr(cloud_samples))
            text = text.rstrip() + '\n\n\n' + runtime
        elif relative.endswith('zones.py'):
            old = "            excl_params.update(params)\n"
            if old in text:
                assert text.count(old) == 1
                text = text.replace(old, "            from templates.nebula.exclusion import match_exclusion_palette\n"
                                "            excl_params.update(match_exclusion_palette(self.CONTENT_TEMPLATE, params))\n")
            else:
                assert 'excl_params.update(match_exclusion_palette(self.CONTENT_TEMPLATE, params))' in text
        else:
            for name in ('Sig8BrownNebulaTemplate', 'Sig8LargeEdgeNebulaTemplate', 'Sig8SmallEdgeNebulaTemplate'):
                header = f'class {name}(SimpleTemplate):\n'
                assert text.count(header) == 1
                text = text.replace(header, header + '\t# Hand-tuned to the cloud palette; retain the system exclusion tint.\n'
                                    '\tMATCH_EXCLUSION_PALETTE = False\n')
        ast.parse(text)
        data = text.replace('\n', newline).encode('utf-8')
        staged = OUT / 'staged' / relative
        staged.parent.mkdir(parents=True, exist_ok=True)
        staged.write_bytes(data)
        manifest[relative] = {'before': digest(original), 'after': digest(data)}

    # Exercise every current template, including ones with no installed exclusions yet.
    templates = []
    for path in (ROOT / 'templates/nebula').glob('*.py'):
        template_path = OUT / 'staged' / 'templates/nebula' / path.name if path.name == 'sig8_nebula.py' else path
        for cls in ast.parse(template_path.read_text(encoding='utf-8')).body:
            if not isinstance(cls, ast.ClassDef):
                continue
            for stmt in cls.body:
                if isinstance(stmt, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TEMPLATE' for t in stmt.targets):
                    if isinstance(stmt.value, ast.Constant):
                        templates.append(SimpleNamespace(TEMPLATE=stmt.value.value,
                            MATCH_EXCLUSION_PALETTE=path.name != 'sig8_nebula.py'))
    samples = json.loads((OUT / 'textures.json').read_text())
    for template in templates:
        for shell in samples:
            params = {'zone_shell': shell, 'exclusion_tint': '150, 160, 170', 'max_alpha': .5}
            result = match_exclusion_palette(template, params)
            assert params['exclusion_tint'] == '150, 160, 170'
            assert result['max_alpha'] == .5 and result['zone_shell'] == shell
            assert all(0 <= int(x) <= 255 for x in result['exclusion_tint'].split(','))

    # Run the actual staged serializer with the actual staged palette module.
    module = ModuleType('templates.nebula.exclusion')
    exec(compile((OUT / 'staged' / FILES[0]).read_bytes(), FILES[0], 'exec'), module.__dict__)
    sys.modules[module.__name__] = module
    tree = ast.parse((OUT / 'staged' / FILES[1]).read_bytes())
    zone = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'NebulaZone')
    method = next(n for n in zone.body if isinstance(n, ast.FunctionDef) and n.name == 'get_exclusions_content')
    namespace = {'SINGLE_DIVIDER': '\n', 'DIVIDER': '\n\n'}
    exec(compile(ast.Module(body=[method], type_ignores=[]), FILES[1], 'exec'), namespace)
    params = {'zone_shell': next(iter(samples)), 'exclusion_tint': '100, 255, 155',
              'max_alpha': .5, 'shell_scalar': 1.1, 'fog_far': 15000}
    snapshot = dict(params)
    instance = SimpleNamespace(CONTENT_TEMPLATE=templates[0], exclusions={'test_zone': params})
    output = namespace['get_exclusions_content'](instance)
    expected = module.match_exclusion_palette(templates[0], params)
    assert output == '\n'.join(f'{k} = {v}' for k, v in {'exclusion': 'test_zone', **expected}.items())
    assert params == snapshot
    assert module.match_exclusion_palette(SimpleNamespace(TEMPLATE='', MATCH_EXCLUSION_PALETTE=False), params) == params
    assert module.match_exclusion_palette(SimpleNamespace(TEMPLATE='[Fog]\nfog_enabled = 0\ncolor = 1, 2, 3'), params) == params
    assert module.match_exclusion_palette(templates[0], {'zone_shell': 'unknown.3db'}) == {'zone_shell': 'unknown.3db'}

    rows, report, cache = [], [], {}
    for path in sorted((ROOT.parents[1] / 'DATA/SOLAR/NEBULA_MOD/GENERATED').glob('*.ini')):
        content = path.read_text(encoding='utf-8-sig')
        seen = set()
        for block in re.split(r'(?im)^exclusion\s*=', content)[1:]:
            block = block.split('[', 1)[0]
            params = dict((k.strip().lower(), v.strip()) for k, v in re.findall(r'(?m)^([^=\n]+)=(.*)$', block))
            shell = params.get('zone_shell')
            if shell not in samples:
                continue
            old = params.get('exclusion_tint', '255, 255, 255')
            if (shell, old) in seen:
                continue
            seen.add((shell, old))
            preview_template = SimpleNamespace(TEMPLATE=content, MATCH_EXCLUSION_PALETTE=not path.name.startswith('gen_sig8_'))
            result = match_exclusion_palette(preview_template, params)
            new = result['exclusion_tint']
            report.append({'file': path.name, 'shell': shell, 'old': old, 'new': new})
            if shell not in cache:
                _, roots = read_tree((ROOT.parents[1] / 'DATA' / shell.replace('\\', '/')).read_bytes())
                lib = next(n for n in roots[0].children if n.name.lower() == 'texture library')
                leaf = next(n for n in lib.children[0].children if n.name.lower() in ('mip0', 'mips'))
                im = Image.open(io.BytesIO(leaf.blob)).convert('RGB')
                im = im.resize((150, 110))
                cache[shell] = im
            row = Image.new('RGB', (850, 145), '#202027')
            draw = ImageDraw.Draw(row)
            draw.text((8, 5), path.stem + ' / ' + Path(shell.replace('\\', '/')).stem, fill='white')
            for x, label, tint in [(8, 'before', old), (175, 'after', new)]:
                rgb = tuple(int(v.strip()) for v in tint.split(','))
                row.paste(ImageChops.multiply(cache[shell], Image.new('RGB', (150, 110), rgb)), (x, 30))
                draw.text((x + 335, 35 if label == 'before' else 60), label + ': ' + tint, fill='white')
            fog = re.search(r'(?is)\[fog\].*?\bcolor\s*=\s*([\d ,]+)', content)
            if fog:
                colour = tuple(int(v) for v in fog[1].strip().split(','))
                draw.rectangle((690, 35, 820, 110), fill=colour)
                draw.text((690, 115), 'fog colour', fill='white')
            cloud = palette_runtime.cloud_palette(palette_runtime.palette_sections(content))
            if cloud:
                # Normalise the swatch to show hue; brightness is not an in-game prediction.
                colour = tuple(round(c / max(cloud) * 180) for c in cloud)
                draw.rectangle((540, 80, 670, 115), fill=colour)
                draw.text((540, 120), 'cloud hue', fill='white')
            rows.append(row)
    # Split the sheet into readable pages.
    for start in range(0, len(rows), 10):
        chunk = rows[start:start + 10]
        page = Image.new('RGB', (850, 145 * len(chunk)))
        for i, row in enumerate(chunk):
            page.paste(row, (0, i * 145))
        page.save(OUT / f'cloud_comparison_{start // 10 + 1}.png')
    (OUT / 'changes.json').write_text(json.dumps(report, indent=2))
    (OUT / 'manifest.json').write_text(json.dumps(manifest, indent=2))
    print(f'PASS: {len(templates)} templates x {len(samples)} shells; {len(report)} installed combinations previewed')


def apply():
    manifest = json.loads((OUT / 'manifest.json').read_text())
    for relative, hashes in manifest.items():
        assert digest((ROOT / relative).read_bytes()) == hashes['before'], relative + ' changed since staging'
        assert digest((OUT / 'staged' / relative).read_bytes()) == hashes['after']
    backup = OUT / ('backup_' + datetime.now().strftime('%Y%m%d_%H%M%S'))
    for relative in manifest:
        dest = backup / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes((ROOT / relative).read_bytes())
    for relative, hashes in manifest.items():
        (ROOT / relative).write_bytes((OUT / 'staged' / relative).read_bytes())
        assert digest((ROOT / relative).read_bytes()) == hashes['after']
    print(f'Installed and verified {len(manifest)} Pythonlancer source files. Backup:', backup)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    apply() if args.apply else prepare()
