"""Pure field conversion, also embedded into PythonLancer to survive regeneration."""

CLIENT_SYSTEMS = frozenset({'tau29'})

def convert_field(content, models, population_scale=1):
    import collections
    import math
    import re

    header = re.compile(r'^\[([^\]\r\n]+)\][ \t]*\r?$', re.M)
    headers = list(header.finditer(content))
    parts = [(m[1].lower(), m.start(), headers[i+1].start() if i+1 < len(headers) else len(content))
             for i, m in enumerate(headers)]

    def values(body):
        return {m[1].lower(): m[2].strip() for m in re.finditer(
            r'^[ \t]*(\w+)[ \t]*=[ \t]*([^;\r\n]*)', body, re.M)}

    dynamic = [values(content[a:b]) for kind, a, b in parts if kind == 'dynamicasteroids']
    existing = [values(content[a:b]) for kind, a, b in parts if kind == 'serverdynamicasteroids']
    if existing:
        expected = collections.Counter('srv_' + d['asteroid'].lower() for d in dynamic)
        actual = collections.Counter(s['asteroid'].lower() for s in existing)
        if expected != actual or any(float(d['count']) != 0 for d in dynamic):
            raise ValueError('Partial/ambiguous server asteroid conversion')
        return content
    newline = '\r\n' if '\r\n' in content else '\n'
    additions = []
    for index, d in enumerate(dynamic):
        model = d['asteroid'].lower()
        if model not in models:
            raise ValueError('Unregistered server asteroid model: ' + model)
        count = int(d['count']) * population_scale
        if not 0 <= count <= 256:
            raise ValueError('Unsupported asteroid count: ' + str(count))
        # Keep authored density/speeds, with Sig8's distant ship-based formation.
        radius = max(3000.0, float(d.get('placement_radius', 3000)))
        if not math.isfinite(radius) or radius > 100000:
            raise ValueError('Invalid placement radius')
        settings = dict(asteroid='srv_' + model, spawn_mode='forward', count=str(count),
                        placement_radius=f'{radius:g}', placement_offset=f'{radius*.85:g}',
                        despawn_radius=f'{radius*1.5:g}',
                        max_velocity=d.get('max_velocity', '10'),
                        max_angular_velocity=d.get('max_angular_velocity', '0.1'), seed=str(801+index))
        if 'band_thickness' in d:
            settings['band_thickness'] = d['band_thickness']
        additions.append('[ServerDynamicAsteroids]' + newline +
                         ''.join(f'{k} = {v}{newline}' for k, v in settings.items()))
    if not additions:
        return content
    result = content
    for kind, a, b in reversed(parts):
        if kind != 'dynamicasteroids':
            continue
        body, count = re.subn(r'(?mi)^([ \t]*count[ \t]*=[ \t]*)[^;\r\n]*',
                             r'\g<1>0', content[a:b])
        if count != 1:
            raise ValueError('Missing/duplicate dynamic count')
        result = result[:a] + body + result[b:]
    return result + newline + newline.join(additions)


def patch_generator(raw, systems, models):
    import inspect
    import re
    systems = set(systems) - CLIENT_SYSTEMS
    newline = '\r\n' if b'\r\n' in raw else '\n'
    begin = '# BEGIN server asteroid ordinary world v1'
    end = '# END server asteroid ordinary world v1'
    original = '        return AST_TEMPLATE.format(**params)'
    replacement = '        return _server_world_field(self, AST_TEMPLATE.format(**params))'
    helper = inspect.getsource(convert_field).replace('def convert_field(', 'def _convert_server_field(', 1)
    addition = (begin + '\n_SERVER_ASTEROID_SYSTEMS = ' + repr(tuple(sorted(systems))) +
                '\n_SERVER_ASTEROID_MODELS = ' + repr(tuple(sorted(models))) + '\n\n' + helper + '''
def _server_world_field(field, content):
    system = field.system
    if (getattr(system, 'SYSTEMS_ROOT', None) != 'SYSTEMS_MOD'
            or getattr(system, 'IS_STORY', False)
            or str(getattr(system, 'NAME', '')).lower() not in _SERVER_ASTEROID_SYSTEMS):
        return content
    scale = 2 if str(system.NAME).lower() == 'sig8' else 1
    return _convert_server_field(content, _SERVER_ASTEROID_MODELS, scale)
''' + end + '\n').replace('\n', newline).encode('ascii')
    if begin.encode() in raw:
        # Allow a scope-only update of our known block, keeping the helper fail-closed.
        updated = raw
        for key in (b'_SERVER_ASTEROID_SYSTEMS', b'_SERVER_ASTEROID_MODELS'):
            pattern = rb'(?m)^' + key + rb' = [^\r\n]*'
            desired = re.search(pattern, addition).group(0)
            updated, count = re.subn(pattern, lambda _: desired, updated)
            if count != 1:
                raise ValueError('Missing/duplicate server asteroid scope')
        if updated.count(addition) != 1 or updated.count(replacement.encode()) != 1:
            raise ValueError('Changed server asteroid generator patch; review before updating')
        compile(updated, 'asteroid_definition.py', 'exec')
        return updated
    anchor = (newline + newline + 'class AsteroidDefinition(object):').encode()
    if raw.count(anchor) != 1 or raw.count(original.encode()) != 1:
        raise ValueError('Unknown generator layout')
    result = raw.replace(anchor, newline.encode()*2 + addition + anchor, 1)
    result = result.replace(original.encode(), replacement.encode(), 1)
    compile(result, 'asteroid_definition.py', 'exec')
    return result
