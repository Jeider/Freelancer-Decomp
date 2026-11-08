"""Regression checks against the staged Pythonlancer code, without generating the game."""
import ast
from pathlib import Path
from types import SimpleNamespace

stage = Path('src/obj/exclusion_palette/staged')
ns = {}
exec(compile((stage / 'templates/nebula/exclusion.py').read_bytes(), 'exclusion.py', 'exec'), ns)
parse, palette, match = (ns[key] for key in ('palette_sections', 'cloud_palette', 'match_exclusion_palette'))

# Repeated layers must both contribute; a disabled section must not overwrite either.
header = '[TexturePanels]\nfile = solar/nebula/generic_shapes.ini\n'
def layer(rgb, count=100):
    return (f'[Clouds]\npuff_count = {count}\npuff_shape = generic_cloud1\n'
            f'puff_colora = {rgb}\npuff_colorb = {rgb}\npuff_weights = 1\n')
red = layer('255, 0, 0')
blue = layer('0, 0, 255')
mixed = palette(parse(header + red + blue))
assert mixed[0] > 0 and mixed[2] > 0 and mixed[1] == 0
assert abs(mixed[0] - mixed[2]) < 1
assert palette(parse(header + red + blue.replace('[Clouds]', '[;Clouds]'))) == palette(parse(header + red))
assert palette(parse(header + red + layer('0, 0, 255', 0))) == palette(parse(header + red))

# White puffs retain the texture's intrinsic hue; selecting a different atlas changes it.
generic = palette(parse(header + layer('255, 255, 255')))
edge = palette(parse((header + layer('255, 255, 255')).replace('generic', 'edge')))
assert abs(generic[0] - generic[1]) < 1
assert edge[1] > edge[0] * 1.4

# Check every referenced shape in every active authored layer is measured.
root = Path('D:/games/FL_MOD/Assets/Pythonlancer/templates/nebula')
checked = 0
for path in root.glob('*.py'):
    for cls in ast.parse(path.read_bytes()).body:
        if not isinstance(cls, ast.ClassDef):
            continue
        for stmt in cls.body:
            if not isinstance(stmt, ast.Assign) or not isinstance(stmt.value, ast.Constant):
                continue
            if not any(isinstance(t, ast.Name) and t.id == 'TEMPLATE' for t in stmt.targets):
                continue
            sections = parse(stmt.value.value)
            if any(name == 'clouds' and float(values.get('puff_count', ['0'])[-1]) > 0 for name, values in sections):
                assert palette(sections) is not None, (path, cls.name)
                checked += 1

# Actual staged Sigma-8 classes explicitly retain both original authored settings.
tree = ast.parse((stage / 'templates/nebula/sig8_nebula.py').read_bytes())
sigma = 0
for cls in tree.body:
    if not isinstance(cls, ast.ClassDef):
        continue
    attrs = {t.id: ast.literal_eval(stmt.value) for stmt in cls.body if isinstance(stmt, ast.Assign)
             for t in stmt.targets if isinstance(t, ast.Name) and t.id in ('TEMPLATE', 'MATCH_EXCLUSION_PALETTE')}
    for tint in ('100, 80, 10', '200, 255, 200'):
        params = {'zone_shell': ns['EDGE_EXCLUSION'], 'exclusion_tint': tint}
        assert match(SimpleNamespace(**attrs), params) == params
    sigma += 1
assert sigma == 3
print(f'PASS: repeated/disabled/zero-count layers, texture colour, {checked} cloud templates, all 3 Sigma-8 presets')
