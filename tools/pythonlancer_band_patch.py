"""Narrow, byte-preserving Pythonlancer patch; this module never writes game files."""

from __future__ import annotations

import ast
from pathlib import Path
import sys
from types import SimpleNamespace


BEGIN = b'# BEGIN ordinary-world mesh Band profiles v1'
END = b'# END ordinary-world mesh Band profiles v1'
ANCHOR = b'\n\nclass AsteroidDefinition(object):'
RETURN = b'        return AST_TEMPLATE.format(**params)'
CALL = b'        _ordinary_world_mesh_band(self, params)\n'
DEFAULT_ROOT = Path('D:/games/FL_MOD/Assets/Pythonlancer')

# Embedded constants deliberately make the installed generator independent of this repo.
ADDITION = '''# BEGIN ordinary-world mesh Band profiles v1
ORDINARY_WORLD_MESH_FAR_ROCKS = """[FarRocks]
type = mesh
count = 1000
model_scale = 3
start_dist = 4500
start_fade = 700
replace_band = 1"""

ORDINARY_WORLD_DEBRIS_FAR_ROCKS = """[FarRocks]
type = debris
count = 1000
model_scale = 2
size_power = 2.3
edge_softness = 1.2
clump_size = 3200
clump_coverage = 0.45
clump_softness = 0.2
clump_amount = 0.65
start_dist = 4500
start_fade = 700
far_dist = 55000
far_fade = 18000
color = 255, 255, 255
brightness = 1.0
ambient = 1.0
min_pixels = 1
solid_pixels = 5
replace_band = 1"""

ORDINARY_WORLD_DEBRIS_FIELD_DUST = """[FieldDust]
opacity = 0.06
max_opacity = 0.10
color = 110, 115, 120
brightness = 0.65
ambient = 0.18
forward = 0.35
forward_weight = 0.3
back = 0.1
noise_scale = 3200
coverage = 0.5
softness = 0.2
clump = 0.65
edge_softness = 1.2
clear_radius = 1000
steps = 8
lod_distance = 100000
far_dist = 55000
far_fade = 18000
exclude_zones = 1"""


def _ordinary_world_mesh_band(field, params):
    system = field.system
    name = str(getattr(system, 'NAME', '')).lower()
    if (getattr(system, 'SYSTEMS_ROOT', None) != 'SYSTEMS_MOD'
            or getattr(system, 'IS_STORY', False)
            or not name or name in ('om11', 'tau44', 'm8_tau44')
            or name.startswith('sphere')
            or not field.BELT or not field.DYNAST or not field.FAR_ROCKS):
        return
    # Even a non-asteroid Cube directive is conservatively considered filled.
    def active_lines(value):
        return [line.split(';', 1)[0].split('#', 1)[0].strip()
                for line in value.splitlines()
                if line.split(';', 1)[0].split('#', 1)[0].strip()]
    if active_lines(params['cube']):
        return
    if '[band]' not in [line.lower() for line in active_lines(params['belt'])]:
        return
    models = []
    section = ''
    for line in active_lines(params['dynasteroids']):
        if line.startswith('['):
            section = line.lower()
        elif section == '[dynamicasteroids]' and '=' in line:
            key, value = line.split('=', 1)
            if key.strip().lower() == 'asteroid' and value.strip():
                models.append(value.strip().split(',', 1)[0].strip())
    if not models or any(not model or '{' in model or '}' in model for model in models):
        return
    debris = isinstance(field, DebrisDefinition) or all(
        model.lower().startswith('din_debris_') for model in models)
    params['far_rocks'] = (ORDINARY_WORLD_DEBRIS_FAR_ROCKS if debris
                           else ORDINARY_WORLD_MESH_FAR_ROCKS)
    if debris and field.FIELD_DUST:
        params['field_dust'] = ORDINARY_WORLD_DEBRIS_FIELD_DUST
# END ordinary-world mesh Band profiles v1
'''.encode('ascii')


def patch_source(raw: bytes) -> bytes:
    """Insert the helper and one invocation, fail closed on unexpected/partial edits."""
    newline = b'\r\n' if b'\r\n' in raw else b'\n'
    if newline == b'\r\n' and b'\n' in raw.replace(b'\r\n', b''):
        raise ValueError('Mixed source newline styles')
    addition = ADDITION.replace(b'\n', newline)
    anchor = ANCHOR.replace(b'\n', newline)
    call = CALL.replace(b'\n', newline)
    if BEGIN in raw or END in raw or call.rstrip() in raw:
        if raw.count(addition) != 1 or raw.count(call + RETURN) != 1:
            raise ValueError('Incomplete or modified mesh Band patch')
        return raw
    if raw.count(anchor) != 1 or raw.count(RETURN) != 1:
        raise ValueError('Unrecognized AsteroidDefinition source layout')
    patched = raw.replace(anchor, newline + newline + addition + anchor, 1)
    patched = patched.replace(RETURN, call + RETURN, 1)
    compile(patched, 'asteroid_definition.py', 'exec')
    return patched


def validate(original: bytes, patched: bytes, pythonlancer_root: Path = DEFAULT_ROOT) -> dict:
    """Run isolated class-output checks; import only names/dividers, never the generator.

    Returns a JSON-serializable check summary, raising on any regression. Supports an
    already patched original, so repeat installer dry runs exercise the same tests.
    """
    if patch_source(original) != patched or patch_source(patched) != patched:
        raise AssertionError('Patch is not deterministic/idempotent')
    nl = b'\r\n' if b'\r\n' in patched else b'\n'
    baseline = patched.replace(nl + nl + ADDITION.replace(b'\n', nl), b'', 1)
    baseline = baseline.replace(CALL.replace(b'\n', nl), b'', 1)
    if BEGIN not in original and baseline != original:
        raise AssertionError('Untargeted source bytes changed')
    root = Path(pythonlancer_root)
    for package in ('world', 'text'):
        if (root / package / '__init__.py').read_bytes().strip():
            raise ValueError('Unexpected package initialization code')
    for relative in ('world/names.py', 'text/dividers.py'):
        tree = ast.parse((root / relative).read_bytes())
        if any(isinstance(node, (ast.Import, ast.ImportFrom)) for node in ast.walk(tree)):
            raise ValueError('Unexpected dependency imports')
    sys.path.insert(0, str(root))
    old_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        namespaces = []
        for source in (baseline, patched):
            tree = ast.parse(source)
            imports = [ast.unparse(node) for node in ast.walk(tree)
                       if isinstance(node, (ast.Import, ast.ImportFrom))]
            if imports != ['from world.names import *', 'from text.dividers import SINGLE_DIVIDER']:
                raise ValueError('Unexpected generator imports')
            namespace = {'__name__': '_band_patch_validation'}
            exec(compile(tree, 'asteroid_definition.py', 'exec'), namespace)
            namespaces.append(namespace)
    finally:
        sys.path.pop(0)
        sys.dont_write_bytecode = old_bytecode
    before, after = namespaces
    ordinary = dict(NAME='br_cam', SYSTEMS_ROOT='SYSTEMS_MOD', IS_STORY=False)
    checks = []

    def outputs(base='Omega15AsteroidDefinition', system=None, **attrs):
        result = []
        for namespace in namespaces:
            cls = type('CheckField', (namespace[base],), dict(BELT=True, DYNAST=True) | attrs)
            result.append(cls(SimpleNamespace(**(ordinary if system is None else system)), None).get_file_content())
        return result

    def unchanged(label, **kwargs):
        old, new = outputs(**kwargs)
        assert old == new, label
        checks.append(label)

    for name in ('om11', 'OM11', 'tau44', 'm8_tau44', 'sphere', 'sphere2_inside', 'sphere3b'):
        for base in ('Omega15AsteroidDefinition', 'DebrisDefinition'):
            unchanged('protected:' + name + ':' + base, base=base, system=ordinary | dict(NAME=name))
    for root_name in ('SPECIAL', 'DANGEON', 'SYSTEMS', ''):
        unchanged('root:' + root_name, system=ordinary | dict(SYSTEMS_ROOT=root_name))
    unchanged('story', system=ordinary | dict(IS_STORY=True))
    unchanged('unknown system', system={})
    unchanged('no name', system=dict(SYSTEMS_ROOT='SYSTEMS_MOD'))
    for attrs in (dict(BELT=False), dict(DYNAST=False), dict(FAR_ROCKS=False),
                  dict(DYNAST_TEMPLATE=''), dict(DYNAST_TEMPLATE='[DynamicAsteroids]\nasteroid = '),
                  dict(DYNAST_TEMPLATE='[DynamicAsteroids]\nasteroid = {model}'),
                  dict(CUBE=True, CUBE_TEMPLATE='asteroid = static_rock'),
                  dict(CUBE=True, CUBE_TEMPLATE='rotation = 1, 2, 3')):
        unchanged('ineligible:' + repr(attrs), **attrs)
    unchanged('debris opt out', base='DebrisDefinition', FAR_ROCKS=False)
    for base in ('Omega15AsteroidDefinition', 'CaliforniaAsteroidDefinition',
                 'Tau37AsteroidDefinition', 'TekagiAsteroidDefinition',
                 'CuracaoAsteroidDefinition', 'Tau29AsteroidDefinition', 'DebrisDefinition'):
        for cube in ('', '; no static asteroids\n # comment'):
            old, new = outputs(base=base, CUBE=True, CUBE_TEMPLATE=cube)
            far = after['ORDINARY_WORLD_DEBRIS_FAR_ROCKS' if base == 'DebrisDefinition'
                        else 'ORDINARY_WORLD_MESH_FAR_ROCKS']
            expected = old.replace(before['FAR_ROCKS_TEMPLATE'], far, 1)
            if base == 'DebrisDefinition':
                expected = expected.replace(before['FIELD_DUST_TEMPLATE'], after['ORDINARY_WORLD_DEBRIS_FIELD_DUST'], 1)
            assert new == expected, base
            checks.append('profile:' + base + ':' + repr(cube))
    for base in ('Omega15AsteroidDefinition', 'DebrisDefinition'):
        old, new = outputs(base=base, FIELD_DUST=False)
        assert '[FieldDust]' not in new and 'count = 1000' in new
        checks.append('dust opt out:' + base)
    custom_dust = '[FieldDust]\nopacity = 0.0123\nbrightness = 0.75'
    old, new = outputs(FIELD_DUST_TEMPLATE=custom_dust)
    assert new == old.replace(before['FAR_ROCKS_TEMPLATE'], after['ORDINARY_WORLD_MESH_FAR_ROCKS'], 1)
    checks.append('ordinary custom dust preserved')
    for newline in (b'\n', b'\r\n'):
        variant = baseline.replace(b'\r\n', b'\n').replace(b'\n', newline)
        changed = patch_source(variant)
        assert patch_source(changed) == changed
        restored = changed.replace(newline + newline + ADDITION.replace(b'\n', newline), b'', 1)
        restored = restored.replace(CALL.replace(b'\n', newline), b'', 1)
        assert restored == variant
        checks.append('source newline preserved:' + repr(newline))
    return {'checks_passed': len(checks), 'checks': checks,
            'byte_preserving': True, 'idempotent': True}


if __name__ == '__main__':
    import json
    source = (DEFAULT_ROOT / 'universe/content/asteroid_definition.py').read_bytes()
    print(json.dumps(validate(source, patch_source(source)), indent=2))
