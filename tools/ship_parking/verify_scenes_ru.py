"""Verify installed RU parking speech and optionally remove its rollback copies.

Does not build scenes, write game DATA, or launch the game. Backup deletion uses
DataFolder and is restricted to this topic's verified scene transactions.
"""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'out/ship_parking/audio_ru'
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path.insert(0, str(PROJECT))
sys.dont_write_bytecode = True

from managers.parking_commandants import parse, one
from managers.rpg_scene import RpgSceneManager
from story.rpg.script import RpgScript
from tools.data_folder import DataFolder


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def confined(path, root):
    assert path.resolve().is_relative_to(root.resolve()), path
    for part in (path, *path.parents):
        if part.exists():
            assert not (getattr(part.lstat(), 'st_file_attributes', 0)
                        & stat.FILE_ATTRIBUTE_REPARSE_POINT), part


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--clean-backups', action='store_true')
    args = parser.parse_args()
    folder = DataFolder(root=PROJECT.parent.parent)
    registry = read(PROJECT / 'story/rpg/parking_commandants.json')['bases']
    installed = read(OUT / 'installed.json')
    contacts = {one(row, 'base'): row for kind, row in
                parse(folder.data_path('RPG/parking_contacts.ini').read_bytes())
                if kind == 'rpgcontact'}
    launch = folder.rpg_bin_path('freelancer.ini').read_text(encoding='utf-8-sig').lower()
    verified, transactions, fragments = {}, [], 0
    assert len(registry) == len(installed['groups']) == 55
    for base in registry:
        group = base['group']
        script = RpgScript.load(PROJECT / f'story/rpg/{group}.json')
        files, catalogs = RpgSceneManager(PROJECT, script).plan(('ru',))
        report = read(OUT / f'scenes/{group}/scene_build.json')
        assert not report['dry_run'] and set(report['files']) == set(files)
        assert report['fragments'] == len(script.fragments) == 23
        for relative, raw in files.items():
            assert folder.data_path(relative).read_bytes() == raw, relative
            verified[relative] = digest(raw)
        for relative, expected in installed['groups'][group]['files'].items():
            assert digest(folder.data_path(relative).read_bytes()) == expected, relative
        graph_path = f'RPG/{group}_dialog.ini'
        graph_bytes = folder.data_path(graph_path).read_bytes()
        assert digest(graph_bytes) == installed['graphs'][graph_path], graph_path
        graph = parse(graph_bytes)
        header = next(row for kind, row in graph if kind == 'dialog')
        assert one(header, 'scene_group') == group
        bound = {value for _, row in graph for value in row.get('fragment', [])}
        assert bound == {row['id'] for row in script.fragments}, group
        contact = contacts[base['base']]
        assert one(contact, 'enabled').lower() == 'true'
        encounter = parse(folder.data_path(one(contact, 'rtc')).read_bytes())
        assert any(one(row, 'dialog').replace('\\', '/') == graph_path
                   for kind, row in encounter if kind == 'characterencounter')
        actors = {one(row, 'actor') for kind, row in encounter if kind == 'char'}
        assert script.data['binding']['vendor'] in actors
        session_path = (f'SCRIPTS/RPG/{group}/conversation.thn' if
                        script.data.get('local_scene') else 'SCRIPTS/RPG/conversation.thn')
        session = folder.data_path(session_path).read_bytes()
        assert b'RpgCamera_vendor' in session and b'RpgCamera_player' in session
        assert f'audio\\rpg\\{group}_sounds.ini' in launch
        catalog = catalogs['ru']
        for row in catalog['fragments']:
            assert row['scene_seconds'] >= row['speech_seconds'] > 0
        subtitles = ET.fromstring(files[f'SCRIPTS/RPG/{group}/ru/subtitles.xml'])
        assert [row.text for row in subtitles] == [row['ru'] for row in script.fragments]
        fragments += len(catalog['fragments'])
        backup_root = OUT / f'scenes/{group}/backups'
        confined(backup_root, OUT / 'scenes')
        for backup in backup_root.iterdir():
            confined(backup, backup_root)
            transaction = read(backup / 'transaction.json')
            assert transaction['group'] == group and not transaction['bin_files']
            assert Path(transaction['destination']).resolve() == folder.get_root().resolve()
            assert set(transaction['data_files']) <= set(files)
            for relative, existed in transaction['data_files'].items():
                target = backup / 'DATA' / relative
                confined(target, backup)
                if existed and target.exists():
                    transactions.append((backup, relative, digest(target.read_bytes())))

    # All groups pass before any temporary rollback copy is removed.
    if args.clean_backups:
        for backup, relative, before in transactions:
            confined(backup / 'DATA' / relative, OUT / 'scenes')
            assert digest((backup / 'DATA' / relative).read_bytes()) == before
            assert digest(folder.data_path(relative).read_bytes()) == verified[relative]
            DataFolder(root=backup).remove_data_file(relative)
    verification = {'groups': len(registry), 'fragments': fragments,
                    'language': 'ru', 'runtime_bindings_verified': True,
                    'files': verified, 'game_launched': False,
                    'backup_files_removed': len(transactions) if args.clean_backups else 0}
    (OUT / 'scenes_verified.json').write_text(
        json.dumps(verification, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    installed.update(thn_built=True, runtime_bindings_verified=True,
                     scenes_report='scenes_verified.json')
    installed.pop('pending_command', None)
    (OUT / 'installed.json').write_text(
        json.dumps(installed, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'PASS: {len(registry)} commandants, {fragments} RU speech scenes, '
          f'{len(verified)} installed scene files and runtime bindings verified; '
          f'{verification["backup_files_removed"]} rollback files removed.')


if __name__ == '__main__':
    main()
