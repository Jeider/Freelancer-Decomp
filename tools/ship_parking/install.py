"""Stage, install with verified backups, or verify the local parking feature."""
from pathlib import Path
import argparse
import ast
import datetime
import hashlib
import json
import shutil
import subprocess
import sys

from generate import generate, sections, NAME_ID, data_folder_type
from data_folder_update import prepare

ROOT = Path(__file__).resolve().parents[2]
STAGE = ROOT / 'src/obj/ship_parking/stage'
BUILD = ROOT / 'src/obj/train_courier/rpg1/bin'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def copy(source, target):
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def localize(game, put):
    sys.path.insert(0, str(ROOT / 'tools/targeting_hud'))
    import stage_interface_strings as ids
    sys.path.insert(0, str(ROOT / 'tools/train_courier'))
    from launchers import startup_inis
    relative = 'Assets/Pythonlancer/text/static.py'
    source = (game / relative).read_text(encoding='utf-8-sig')
    rows = [n for n in ast.walk(ast.parse(source)) if isinstance(n, ast.Call) and
            isinstance(n.func, ast.Name) and n.func.id == 'Static' and n.args and
            isinstance(n.args[0], ast.Constant) and n.args[0].value == NAME_ID]
    ru, en = 'Смотритель стоянки', 'Parking manager'
    if rows:
        assert len(rows) == 1
        value = rows[0].args[1]
        assert isinstance(value, ast.Call) and isinstance(value.func, ast.Name) and value.func.id == 'MS'
        assert [ast.literal_eval(v) for v in value.args] == [ru, en], 'Parking IDS already owned by another string'
    else:
        assert 'STATIC_NAMES = [\n' in source
        source = source.replace('STATIC_NAMES = [\n', f'STATIC_NAMES = [\n    Static({NAME_ID}, MS({ru!r}, {en!r})),  # Ship parking\n', 1)
        ast.parse(source)
        put(relative, source.encode('utf-8'))
    visited = set()
    for ini in startup_inis(game):
        resource = next(r for k, r in sections(ini) if k == 'resources')['dll'][2]
        actual = (game / 'bin' / resource.replace('\\', '/')).resolve()
        assert actual.is_relative_to(game) and actual.name.lower() == 'nameresources.dll'
        if actual in visited:
            continue
        visited.add(actual)
        english = 'resources_eng' in str(actual).lower()
        before = ids.resources(actual)
        expected = dict(before)
        block, slot = (NAME_ID & 65535) // 16 + 1, NAME_ID % 16
        keys = [k for k in before if k[0] == 6 and k[1] == block] or [(6, block, 1033)]
        temporary = STAGE / ('parking_name_en.dll' if english else 'parking_name_ru.dll')
        copy(actual, temporary)
        handle = ids.check(ids.begin(str(temporary), False))
        try:
            for key in keys:
                strings = ids.decode_block(before.get(key, b'\0' * 32))
                assert not strings[slot] or (rows and strings[slot] == (en if english else ru)), 'Occupied parking IDS'
                strings[slot] = en if english else ru
                raw = ids.encode_block(strings)
                buffer = ids.c.create_string_buffer(raw)
                ids.check(ids.update(handle, *key, buffer, len(raw)))
                expected[key] = raw
        except Exception:
            ids.end(handle, True)
            raise
        ids.check(ids.end(handle, False))
        assert ids.resources(temporary) == expected, 'Unrelated resource changed'
        put(actual.relative_to(game).as_posix(), temporary.read_bytes())


def stage(game):
    DataFolder, support_files = prepare(game, STAGE)
    folder = DataFolder(root=STAGE)
    files, report = generate(game, STAGE, folder=folder)
    payload = set(files) | set(support_files)

    def put(relative, content):
        if relative.startswith('DATA/'):
            folder.sync_data_file(relative.removeprefix('DATA/'), content)
        else:
            path = STAGE / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        payload.add(relative)

    for name in ('Server.dll', 'Server.pdb', 'Content.dll', 'Content.pdb', 'freelancer.exe', 'freelancer.pdb'):
        put('bin/' + name, (BUILD / name).read_bytes())
    put('Assets/Pythonlancer/tools/ship_parking.py', Path(__file__).with_name('generate.py').read_bytes())
    localize(game, put)
    # Only changed files enter the transaction; unrelated stale staging files are ignored.
    manifest = dict(game=str(game), managers=len(report['managers']), files=[
        dict(path=p, before=digest(game / p), after=digest(STAGE / p))
        for p in sorted(payload) if digest(game / p) != digest(STAGE / p)])
    (STAGE / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(f'Staged {len(manifest["files"])} changed files, including {manifest["managers"]} managers: {STAGE}')


def checked_manifest(game):
    manifest = json.loads((STAGE / 'manifest.json').read_text())
    assert Path(manifest['game']).resolve() == game
    for item in manifest['files']:
        assert (game / item['path']).resolve().is_relative_to(game)
        assert (STAGE / item['path']).resolve().is_relative_to(STAGE.resolve())
    return manifest


def verify(game, manifest):
    for item in manifest['files']:
        assert digest(game / item['path']) == item['after'], 'Installed file differs: ' + item['path']
    for binary, markers in [('Server.dll', (b'PlayerShipParking_Status', b'PlayerShipParking_Buy')),
                            ('Content.dll', (b'RpgDialogBeginSession', b'buy_parking')),
                            ('freelancer.exe', (b'PlayerShipParking_Status', b'RpgDialogRenderText'))]:
        contents = (game / 'bin' / binary).read_bytes()
        assert all(marker in contents for marker in markers), binary
    print(f'PASS: installed hashes, Server/Content/client APIs in {game / "bin"}; {manifest["managers"]} managers')


def install(game):
    manifest = checked_manifest(game)
    processes = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, check=True).stdout.lower()
    for name in (b'freelancer.exe', b'freelancer_window.exe', b'freelancer_en.exe', b'freelancer_window_en.exe', b'flserver.exe'):
        assert b'"' + name + b'"' not in processes, 'Close the game before installing'
    for item in manifest['files']:
        assert digest(game / item['path']) == item['before'], 'Changed since staging: ' + item['path']
        assert digest(STAGE / item['path']) == item['after'], 'Staged file changed: ' + item['path']
    backup = ROOT / 'src/obj/ship_parking/backups' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    for item in manifest['files']:
        if item['before'] is not None:
            copy(game / item['path'], backup / item['path'])
            assert digest(backup / item['path']) == item['before'], 'Backup verification failed'
    copy(STAGE / 'manifest.json', backup / 'manifest.json')
    touched = []
    folder = None
    try:
        for item in manifest['files']:
            touched.append(item)
            if item['path'].startswith('DATA/'):
                # Assets sort before DATA: the extended entry point is already installed.
                if folder is None:
                    folder = data_folder_type(game)(root=game)
                folder.sync_data_file(item['path'].removeprefix('DATA/'), (STAGE / item['path']).read_bytes())
            else:
                copy(STAGE / item['path'], game / item['path'])
        verify(game, manifest)
    except Exception:
        for item in reversed(touched):
            target = game / item['path']
            if item['path'].startswith('DATA/'):
                if folder is None:
                    folder = data_folder_type(game)(root=game)
                relative = item['path'].removeprefix('DATA/')
                if item['before'] is None:
                    folder.remove_data_file(relative)
                else:
                    folder.sync_data_file(relative, (backup / item['path']).read_bytes())
            elif item['before'] is None:
                target.unlink(missing_ok=True)
            else:
                copy(backup / item['path'], target)
        raise
    print('Backup:', backup)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--game-root', type=Path, default=Path('D:/Games/FL_MOD'))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--apply', action='store_true')
    mode.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    game = args.game_root.resolve(strict=True)
    if args.apply:
        install(game)
    elif args.verify:
        verify(game, checked_manifest(game))
    else:
        stage(game)
