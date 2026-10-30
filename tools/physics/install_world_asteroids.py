"""Stage/apply server-owned dynamic asteroids in active ordinary-world systems.

Default mode writes only src/obj; --apply verifies dependencies and backs up changes.
Story/special/shared fields and all non-population field sections are preserved.
"""
import argparse
import ast
import datetime
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from install_band_mesh_fields import inventory, records, values, text, digest, safe, copy
from server_asteroid_rollout import CLIENT_SYSTEMS, convert_field, patch_generator

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'src/obj/world_server_asteroids'
GENERATOR = 'Assets/Pythonlancer/universe/content/asteroid_definition.py'
ARCH = 'DATA/SOLAR/solararch.ini'
BINARIES = ('bin/Server.dll', 'bin/Server.pdb')


def scope(game):
    fields, inputs = inventory(game)
    # Two StorySystem subclasses live under SYSTEMS_MOD (Malta and Omicron Minor).
    # Directory names alone are insufficient to honour the story-system exclusion.
    source = game / 'Assets/Pythonlancer/universe/sirius.py'
    inputs[source.relative_to(game).as_posix()] = digest(source)
    story = set()
    for node in ast.parse(source.read_bytes()).body:
        if not isinstance(node, ast.ClassDef):
            continue
        if any(isinstance(base, ast.Attribute) and base.attr in ('StorySystem', 'Dangeon') for base in node.bases):
            for attr in node.body:
                if isinstance(attr, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'NAME' for t in attr.targets):
                    story.add(ast.literal_eval(attr.value).lower())
    for f in fields:
        for owner in f['owners']:
            owner['protected'] = owner['protected'] or owner['system'].lower() in story
        f['reason'] = ('client asteroid system/shared resource' if any(o['system'].lower() in CLIENT_SYSTEMS for o in f['owners']) else
                       'protected system/shared resource' if any(o['protected'] for o in f['owners']) else
                       'no dynamic population' if not f['models'] else '')
    return fields, inputs


def unchanged(before, after):
    from install_asteroid_mesh_fields import sections
    def normalized(content):
        result = []
        for kind, a, _, b in sections(content):
            body = content[a:b].rstrip('\r\n')
            if kind == 'serverdynamicasteroids':
                continue
            if kind == 'dynamicasteroids':
                body = re.sub(r'(?mi)^([ \t]*count[ \t]*=[ \t]*)[^;\r\n]*', r'\g<1>0', body)
            result.append((kind, body))
        return result
    return normalized(before) == normalized(after)


def prepare(game):
    fields, inputs = scope(game)
    eligible = [f for f in fields if not f['reason']]
    systems = {o['system'] for f in eligible for o in f['owners']}
    models = {m for f in eligible for m in f['models']}
    data = dict(game=str(game), fields=fields, scope_inputs=inputs, files=[],
                systems=sorted(systems), models=sorted(models), adjustments=[])

    def dependency(rel):
        inputs[rel] = digest(safe(game, rel))
        return text(safe(game, rel))

    def stage(rel, raw):
        source = safe(game, rel)
        if source.read_bytes() == raw:
            return
        target = safe(STAGE, rel)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        data['files'].append(dict(relative=rel, original=digest(source), prepared=digest(target)))

    # Preserve duplicate material_library entries (e.g. Tekagi env maps).
    definitions = {}
    boot = dependency('EXE/freelancer.ini')
    arch_paths = re.findall(r'(?mi)^[ \t]*asteroids[ \t]*=[ \t]*([^;\r\n]+)', boot)
    for filename in arch_paths:
        path = safe(game / 'DATA', filename.strip())
        for body in records(dependency(path.relative_to(game).as_posix()), 'dynamicasteroid'):
            nickname = values(body)['nickname'].lower()
            if nickname in definitions:
                raise ValueError('Duplicate dynamic archetype: ' + nickname)
            definitions[nickname] = body
    arch = dependency(ARCH)
    solars = {values(b)['nickname'].lower(): values(b) for b in records(arch, 'solar')}
    addition = ''
    for model in sorted(models):
        body = definitions[model]
        v = values(body)
        mesh = safe(game / 'DATA', v['da_archetype'])
        for asset in [mesh, mesh.with_suffix('.sur')] + [safe(game / 'DATA', m.strip()) for m in
                re.findall(r'(?mi)^[ \t]*material_library[ \t]*=[ \t]*([^;\r\n]+)', body)]:
            inputs[asset.relative_to(game).as_posix()] = digest(asset)
        srv = 'srv_' + model
        if srv in solars:
            if solars[srv]['type'].lower() != 'server_asteroid' or solars[srv]['da_archetype'].lower() != v['da_archetype'].lower():
                raise ValueError('Incompatible existing server archetype: ' + srv)
            continue
        lines = []
        for line in body.splitlines():
            line = line.split(';', 1)[0].strip()
            if not line:
                continue
            key, value = map(str.strip, line.split('=', 1))
            if key.lower() == 'nickname':
                value = srv
            if key.lower() == 'hit_pts' and float(value) > 2000000000:
                # CSolarCreateInfo carries a signed 32-bit hull value on suspend/restore.
                data['adjustments'].append(dict(model=model, hit_pts_before=value, hit_pts_after=2000000000))
                value = '2000000000'
            lines.append(f'{key} = {value}')
        addition += '\r\n[Solar]\r\n' + '\r\n'.join(lines) + '\r\n'
        addition += ('ids_name = 60200\r\nids_info = 60200\r\ntype = SERVER_ASTEROID\r\n'
                     'destructible = true\r\nLODranges = 0, 20000\r\ndistance_render = 6000\r\n')
    stage(ARCH, (arch + addition).encode('latin1'))
    for f in eligible:
        before = text(safe(game, f['relative']))
        after = convert_field(before, models)
        assert unchanged(before, after), f['relative']
        assert convert_field(after, models) == after, f['relative']
        stage(f['relative'], after.encode('latin1'))
    original = safe(game, GENERATOR).read_bytes()
    inputs[GENERATOR] = digest(safe(game, GENERATOR))
    patched = patch_generator(original, systems, models)
    assert patch_generator(patched, systems, models) == patched
    stage(GENERATOR, patched)
    for rel in BINARIES:
        stage(rel, (ROOT / rel).read_bytes())
    for rel in ('bin/Common.dll', 'bin/freelancer.exe', 'bin/DALib.dll', 'bin/dacom.dll'):
        inputs[rel] = digest(safe(game, rel))
    STAGE.mkdir(parents=True, exist_ok=True)
    (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf8')
    print(f'Prepared {len(eligible)} fields / {len(systems)} systems / {len(models)} models; {len(data["files"])} changed files. Game untouched.')
    print('Protected fields:', sum(bool(f['reason']) for f in fields))
    print('Adjustments:', data['adjustments'])


def apply(game):
    import subprocess
    # Check all game executable variants, plus the standalone server.
    result = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, check=True)
    if re.search(rb'"(?:freelancer(?:_window)?(?:_en)?|flserver)\.exe"', result.stdout, re.I):
        raise RuntimeError('Close Freelancer/FLServer before installation')
    data = json.loads((STAGE / 'manifest.json').read_text(encoding='utf8'))
    if Path(data['game']).resolve() != game:
        raise ValueError('Wrong game root')
    current_fields, _ = scope(game)
    allowed = {f['relative'] for f in current_fields if not f['reason']} | {ARCH, GENERATOR, *BINARIES}
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel not in allowed or rel in seen:
            raise ValueError('Unexpected payload: ' + rel)
        seen.add(rel)
        if digest(safe(game, rel)) != item['original'] or digest(safe(STAGE, rel)) != item['prepared']:
            raise ValueError('Changed file: ' + rel)
    for rel, expected in data['scope_inputs'].items():
        if digest(safe(game, rel)) != expected:
            raise ValueError('Dependency changed; prepare again: ' + rel)
    if not data['files']:
        print('Already installed.')
        return
    backup = safe(game, 'BACKUP/codex_world_server_asteroids_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for item in data['files']:
        copy(safe(game, item['relative']), safe(backup, item['relative']))
        assert digest(safe(backup, item['relative'])) == item['original']
    copy(STAGE / 'manifest.json', backup / 'manifest.json')
    touched = []
    try:
        for item in data['files']:
            rel = item['relative']
            if digest(safe(game, rel)) != item['original']:
                raise ValueError('File changed during install: ' + rel)
            touched.append(item)
            copy(safe(STAGE, rel), safe(game, rel))
            assert digest(safe(game, rel)) == item['prepared']
        for f in data['fields']:
            if f['reason']:
                assert digest(safe(game, f['relative'])) == data['scope_inputs'][f['relative']]
    except Exception:
        for item in touched:
            copy(safe(backup, item['relative']), safe(game, item['relative']))
            assert digest(safe(game, item['relative'])) == item['original']
        raise
    print(f'Installed and SHA256 verified {len(data["files"])} files. Protected fields unchanged. Backup: {backup}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    (apply if args.apply else prepare)(args.game_root.resolve(strict=True))
