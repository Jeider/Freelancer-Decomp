"""Audit staged rollout against active world, real archetypes and generator outputs."""
import ast
import collections
import json
import sys
from types import SimpleNamespace

from install_world_asteroids import (STAGE, ARCH, GENERATOR, scope, records, text, values,
                                    safe, digest, unchanged, convert_field, patch_generator)


def main():
    from pathlib import Path
    data = json.loads((STAGE / 'manifest.json').read_text(encoding='utf8'))
    game = Path(data['game'])
    files = {item['relative']: item for item in data['files']}
    fields, _ = scope(game)
    assert fields == data['fields']
    def prepared(rel):
        return text(safe(STAGE if rel in files else game, rel))
    solars = {values(b)['nickname'].lower(): values(b) for b in records(prepared(ARCH), 'solar')}
    field_count = section_count = 0
    for field in fields:
        rel = field['relative']
        if field['reason']:
            assert rel not in files, rel
            continue
        field_count += 1
        before, after = text(safe(game, rel)), prepared(rel)
        assert unchanged(before, after), rel
        assert convert_field(after, data['models']) == after, rel
        dyn = [values(b) for b in records(after, 'dynamicasteroids')]
        srv = [values(b) for b in records(after, 'serverdynamicasteroids')]
        assert all(float(d['count']) == 0 for d in dyn), rel
        assert collections.Counter('srv_' + d['asteroid'].lower() for d in dyn) == collections.Counter(s['asteroid'] for s in srv), rel
        section_count += len(srv)
        for s in srv:
            arch = solars[s['asteroid']]
            assert arch['type'] == 'SERVER_ASTEROID'
            assert 0 < float(arch['hit_pts']) <= 2000000000
            assert float(arch['mass']) > 0
            assert s['spawn_mode'] == 'forward'
            assert float(s['despawn_radius']) >= float(s['placement_radius'])*1.5
        old_dynamic = [values(b) for b in records(before, 'dynamicasteroids')]
        if not records(before, 'serverdynamicasteroids'):
            for d, s in zip(old_dynamic, srv):
                assert int(d['count']) == int(s['count'])
                for k in ('max_velocity', 'max_angular_velocity', 'band_thickness'):
                    if k in d:
                        assert float(d[k]) == float(s[k]), (rel, k)
    # Appended server definitions cannot alter existing solar archetypes.
    assert prepared(ARCH).startswith(text(safe(game, ARCH)))
    for rel, item in files.items():
        assert digest(safe(STAGE, rel)) == item['prepared']

    # Evaluate class definitions only; do not run the world generator or write game files.
    root = game / 'Assets/Pythonlancer'
    original = safe(game, GENERATOR).read_bytes()
    patched = safe(STAGE, GENERATOR).read_bytes() if GENERATOR in files else original
    assert patch_generator(patched, data['systems'], data['models']) == patched
    assert patch_generator(original, data['systems'], data['models']) == patched
    for package in ('world', 'text'):
        assert not (root / package / '__init__.py').read_bytes().strip()
    for rel in ('world/names.py', 'text/dividers.py'):
        assert not any(isinstance(n, (ast.Import, ast.ImportFrom)) for n in ast.walk(ast.parse((root / rel).read_bytes())))
    sys.path.insert(0, str(root))
    namespaces = []
    try:
        for source in (original, patched):
            tree = ast.parse(source)
            assert [ast.unparse(n) for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))] == [
                'from world.names import *', 'from text.dividers import SINGLE_DIVIDER']
            ns = {'__name__': '_server_asteroid_validation'}
            exec(compile(tree, 'asteroid_definition.py', 'exec'), ns)
            namespaces.append(ns)
    finally:
        sys.path.pop(0)
    before_ns, after_ns = namespaces
    assert 'tau29' not in data['systems']
    templates = ('Omega15AsteroidDefinition', 'CaliforniaAsteroidDefinition', 'Tau37AsteroidDefinition',
                 'TekagiAsteroidDefinition', 'CuracaoAsteroidDefinition', 'Tau29AsteroidDefinition', 'DebrisDefinition')
    checks = 0
    def output(ns, template, system):
        cls = type('TestField', (ns[template],), dict(BELT=True, DYNAST=True))
        return cls(SimpleNamespace(**system), None).get_file_content()
    tau29 = output(after_ns, 'Tau29AsteroidDefinition', dict(NAME='tau29', SYSTEMS_ROOT='SYSTEMS_MOD', IS_STORY=False))
    assert not records(tau29, 'serverdynamicasteroids')
    assert all(int(values(b)['count']) > 0 for b in records(tau29, 'dynamicasteroids'))
    for name in data['systems']:
        system = dict(NAME=name, SYSTEMS_ROOT='SYSTEMS_MOD', IS_STORY=False)
        for template in templates:
            old, new = (output(ns, template, system) for ns in namespaces)
            assert unchanged(old, new)
            assert all(float(values(b)['count']) == 0 for b in records(new, 'dynamicasteroids'))
            assert records(new, 'serverdynamicasteroids')
            if name == 'sig8' and template == 'Tau29AsteroidDefinition':
                assert all(values(b)['count'] == '60' for b in records(new, 'serverdynamicasteroids'))
            checks += 1
    for system in [dict(NAME='sig8', SYSTEMS_ROOT='SYSTEMS_MOD', IS_STORY=True),
                   dict(NAME='sig8', SYSTEMS_ROOT='SPECIAL', IS_STORY=False),
                   dict(NAME='sig8', SYSTEMS_ROOT='DANGEON', IS_STORY=False)] + [
                       dict(NAME=n, SYSTEMS_ROOT='SYSTEMS_MOD', IS_STORY=False)
                       for n in ('om11', 'tau44', 'm8_tau44', 'sphere', 'unknown')]:
        assert output(before_ns, templates[0], system) == output(after_ns, templates[0], system)
        checks += 1
    for field in fields:
        if field['reason']:
            continue
        body = text(safe(game, field['relative']))
        obj = SimpleNamespace(system=SimpleNamespace(NAME=field['owners'][0]['system'], SYSTEMS_ROOT='SYSTEMS_MOD', IS_STORY=False))
        generated = after_ns['_server_world_field'](obj, body)
        assert unchanged(body, generated)
        assert convert_field(generated, data['models']) == generated
        checks += 1
    # Fail closed on unknown models and partial conversions; duplicate models remain distinct.
    sample = '[DynamicAsteroids]\nasteroid = test\ncount = 3\n'
    duplicate = sample + sample.replace('count = 3', 'count = 5')
    converted = convert_field(duplicate, ['test'])
    assert [values(b)['count'] for b in records(converted, 'serverdynamicasteroids')] == ['3', '5']
    assert convert_field(converted, ['test']) == converted
    disabled = sample.replace('count = 3', 'count = 0')
    assert convert_field(convert_field(disabled, ['test']), ['test']) == convert_field(disabled, ['test'])
    for bad, models in ((sample, []), (sample.replace('count = 3', 'count = 300'), ['test']),
                        (sample + '[ServerDynamicAsteroids]\nasteroid = srv_test\ncount = 3\n', ['test'])):
        try:
            convert_field(bad, models)
        except ValueError:
            pass
        else:
            raise AssertionError('Unsafe conversion accepted')
    print(f'PASS: {field_count} fields, {section_count} server populations, {len(data["models"])} archetypes; original sections/densities/speeds preserved, protected files excluded')
    print(f'PASS: {checks} generator output checks; story/special guards, Sig8 density, duplicate models, disabled sections, idempotence and invalid-input rejection')


if __name__ == '__main__':
    main()
