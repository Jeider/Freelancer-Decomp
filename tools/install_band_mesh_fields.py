"""Stage/install ordinary-world Band mesh fields and their PythonLancer generator patch.

Never scans unused field INIs into the rollout. Active universe ownership, Band and an
empty Cube are mandatory. Special systems and shared protected resources stay untouched.
"""
import argparse
import collections
import datetime
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

from install_asteroid_mesh_fields import sections
from pythonlancer_band_patch import patch_source, validate

REPO = Path(__file__).resolve().parents[1]
STAGE = REPO / 'src/obj/band_mesh_install'
GENERATOR = 'Assets/Pythonlancer/universe/content/asteroid_definition.py'


def values(content):
    return {m[1].lower(): m[2].strip() for m in re.finditer(
        r'^[ \t]*([\w]+)[ \t]*=[ \t]*([^;\r\n]*)', content, re.M)}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe(root, relative):
    path = (root / relative.replace('\\', '/')).resolve()
    if not path.is_relative_to(root.resolve()):
        raise ValueError(f'Path outside root: {relative}')
    return path


def text(path):
    raw = path.read_bytes()
    if raw.startswith(b'BINI'):
        raise ValueError(f'Binary INI needs explicit handling: {path}')
    return raw.decode('latin1')


def records(content, name):
    return [content[end:stop] for kind, _, end, stop in sections(content) if kind == name.lower()]


def filled(body):
    return any(line.split(';', 1)[0].strip() for line in body.splitlines())


def protected(name, path):
    parts = path.replace('\\', '/').lower().split('/')
    return (parts[0] not in ('systems_mod', 'systems') or name.lower() in ('om11', 'tau44', 'm8_tau44')
            or name.lower().startswith('sphere') or 'tau44' in parts[-1].lower())


def inventory(game):
    inputs = {}
    def read(path):
        inputs[path.relative_to(game).as_posix()] = digest(path)
        return text(path)
    # Use the active universe declared by the game, not test/old system files on disk.
    boot = read(game / 'EXE/freelancer.ini')
    universe_names = [values(body)['universe'] for body in records(boot, 'data') if 'universe' in values(body)]
    if len(universe_names) != 1:
        raise ValueError('Expected one active universe')
    universe_path = safe(game / 'DATA', universe_names[0])
    universe = read(universe_path)
    owners = collections.defaultdict(list)
    for body in records(universe, 'system'):
        system = values(body)
        name, file = system['nickname'], system['file']
        system_content = read(safe(universe_path.parent, file))
        for asteroid in records(system_content, 'asteroids'):
            field = safe(game / 'DATA', values(asteroid)['file'])
            owners[field].append(dict(system=name, protected=protected(name, file)))
    result = []
    for path, refs in sorted(owners.items()):
        content = read(path)
        models = [values(b).get('asteroid', '').lower() for b in records(content, 'dynamicasteroids')]
        models = [model for model in models if model]
        reason = ('protected system/shared resource' if any(r['protected'] for r in refs) else
                  'no Band' if not records(content, 'band') else
                  'populated Cube' if any(filled(b) for b in records(content, 'cube')) else
                  'no dynamic models' if not models else '')
        if not reason and len(models) > 4:
            raise ValueError(f'More than four dynamic models: {path}')
        shapes = '\n'.join(records(content, 'texturepanels') + records(content, 'band')).lower()
        debris = any('debris' in model for model in models) or 'debris' in shapes
        result.append(dict(relative=path.relative_to(game).as_posix(), owners=refs, models=models,
                           kind='debris' if debris else 'asteroid', reason=reason))
    return result, inputs


def update_section(content, section, profile):
    found = [s for s in sections(content) if s[0] == section.lower()]
    newline = '\r\n' if '\r\n' in content else '\n'
    if not found:
        return content + newline + f'[{section}]' + newline + ''.join(f'{k} = {v}{newline}' for k, v in profile.items())
    if len(found) != 1:
        raise ValueError(f'Duplicate section: {section}')
    _, start, end, stop = found[0]
    body = content[end:stop]
    existing = values(body)
    for key, value in profile.items():
        pattern = re.compile(r'^' + re.escape(key) + r'[ \t]*=[^\r\n]*', re.M | re.I)
        if len(pattern.findall(body)) > 1:
            raise ValueError(f'Duplicate {section}/{key}')
        if existing.get(key) == value:
            continue
        if pattern.search(body):
            body = pattern.sub(f'{key} = {value}', body)
        else:
            body = body.rstrip('\r\n') + newline + f'{key} = {value}' + newline + newline
    return content[:end] + body + content[stop:]


def unchanged_sections(before, after):
    # Everything gameplay-facing and the legacy fallback Band remains byte-identical.
    def keep(content):
        return [(kind, content[start:stop]) for kind, start, _, stop in sections(content)
                if kind not in ('farrocks', 'fielddust')]
    # Appending a new visual section can add separator newlines to the preceding section only.
    return [(k, b.rstrip('\r\n')) for k, b in keep(before)] == [(k, b.rstrip('\r\n')) for k, b in keep(after)]


def copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/games/FL_MOD'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--restore', type=Path)
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if not (args.apply or args.restore):
        fields, inputs = inventory(game)
        profiles = text(REPO / 'DATA_EXTRA/ASTEROIDS/br_cam_debris.ini')
        debris = values(records(profiles, 'farrocks')[0])
        dust = values(records(profiles, 'fielddust')[0])
        ordinary = values(records(text(REPO / 'DATA_EXTRA/ASTEROIDS/dynamic_mesh_fields.ini'), 'farrocks')[0])
        data = dict(game=str(game), scope_inputs=inputs, fields=fields, files=[])
        def stage(rel, raw):
            source = safe(game, rel)
            if source.read_bytes() == raw:
                return
            target = safe(STAGE, rel)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
            data['files'].append(dict(relative=rel, original=digest(source), prepared=digest(target)))
        for field in fields:
            if field['reason']:
                continue
            original = text(safe(game, field['relative']))
            prepared = update_section(original, 'FarRocks', debris if field['kind'] == 'debris' else ordinary)
            if field['kind'] == 'debris':
                prepared = update_section(prepared, 'FieldDust', dust)
            assert unchanged_sections(original, prepared), field['relative']
            assert update_section(prepared, 'FarRocks', debris if field['kind'] == 'debris' else ordinary) == prepared
            stage(field['relative'], prepared.encode('latin1'))
        original = safe(game, GENERATOR).read_bytes()
        prepared = patch_source(original)
        data['generator_validation'] = validate(original, prepared, game / 'Assets/Pythonlancer')
        stage(GENERATOR, prepared)
        STAGE.mkdir(parents=True, exist_ok=True)
        (STAGE / 'manifest.json').write_text(json.dumps(data, indent=2), encoding='utf8')
        counts = collections.Counter(f['kind'] for f in fields if not f['reason'])
        print(f'Eligible fields: {dict(counts)}; {len(data["files"])} changed files staged; game untouched.')
        return
    tasklist = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq freelancer.exe', '/FO', 'CSV', '/NH'], capture_output=True, check=True)
    if b'freelancer.exe' in tasklist.stdout.lower():
        raise RuntimeError('Close Freelancer before installation/restoration.')
    source = args.restore.resolve(strict=True) if args.restore else STAGE
    data = json.loads((source / 'manifest.json').read_text(encoding='utf8'))
    if Path(data['game']).resolve() != game:
        raise ValueError('Manifest game root mismatch')
    allowed = {f['relative'] for f in data['fields'] if not f['reason']} | {GENERATOR}
    seen = set()
    for item in data['files']:
        rel = item['relative']
        if rel not in allowed or rel in seen or not (rel == GENERATOR or (rel.lower().startswith('data/solar/') and rel.lower().endswith('.ini'))):
            raise ValueError(f'Unexpected target: {rel}')
        seen.add(rel)
        if digest(safe(game, rel)) != item['prepared' if args.restore else 'original'] or digest(safe(source, rel)) != item['original' if args.restore else 'prepared']:
            raise ValueError(f'File changed: {rel}')
    if not args.restore:
        for rel, expected in data['scope_inputs'].items():
            if digest(safe(game, rel)) != expected:
                raise ValueError(f'Field ownership/scope changed: {rel}; prepare again')
    if args.restore:
        for item in data['files']:
            copy(safe(source, item['relative']), safe(game, item['relative']))
            assert digest(safe(game, item['relative'])) == item['original']
        print(f'Restored and verified {len(data["files"])} files.')
        return
    backup = safe(game, 'BACKUP/codex_band_mesh_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for item in data['files']:
        copy(safe(game, item['relative']), safe(backup, item['relative']))
        assert digest(safe(backup, item['relative'])) == item['original']
    copy(source / 'manifest.json', backup / 'manifest.json')
    try:
        for item in data['files']:
            copy(safe(source, item['relative']), safe(game, item['relative']))
            assert digest(safe(game, item['relative'])) == item['prepared']
    except Exception:
        for item in data['files']:
            copy(safe(backup, item['relative']), safe(game, item['relative']))
        raise
    for field in data['fields']:
        if field['reason']:
            assert digest(safe(game, field['relative'])) == data['scope_inputs'][field['relative']]
    print(f'Installed and verified {len(data["files"])} files. Protected fields unchanged. Backup: {backup}')


if __name__ == '__main__':
    main()
