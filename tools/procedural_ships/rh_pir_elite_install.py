"""Install the explicitly requested canonical ship and Pythonlancer source only.

Does not generate or patch active shiparch.ini and never starts the game.
"""
import argparse
import datetime
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import rh_pir_elite_pythonlancer as p

GAME = Path('D:/Games/FL_MOD')
DATA_BASE = 'ships/rheinland/rh_pir_elite/'


def checked_path(root, relative):
    root = root.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root) or path == root:
        raise ValueError('Path escapes owned directory: ' + str(path))
    return path


def load_api():
    spec = importlib.util.spec_from_file_location('rh_pir_data_folder', p.STAGE / 'tools/data_folder.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.DataFolder


def cleanup():
    report = json.loads((p.OUT / 'installation.json').read_text())
    build = json.loads((p.OUT / 'build.json').read_text())
    DataFolder = load_api()
    game = DataFolder(root=GAME)
    for relative, digest in report['game_assets'].items():
        assert p.sha(game.data_path(relative).read_bytes()) == digest
    # Keep the authored CMP/MAT/SUR in OUT/assets for subsequent model editing.
    # Remove only extra installation and validation copies with verified hashes.
    for name in [*build['files'], 'manifest.json']:
        path = checked_path(p.STAGE, p.ASSET_REL + '/' + name)
        if path.exists():
            assert p.sha(path.read_bytes()) == report['source_files'][p.ASSET_REL + '/' + name]
            path.unlink()
    staged = DataFolder(root=p.OUT / 'validation_stage')
    staged.sync_rh_pir_elite({DATA_BASE + name: None for name in build['files']})
    staged.remove_data_file('SHIPS/shiparch.ini')
    print('Redundant install/validation binary copies removed; authoring assets retained')


def main():
    args = argparse.ArgumentParser()
    args.add_argument('--apply', action='store_true')
    args.add_argument('--cleanup', action='store_true')
    options = args.parse_args()
    if options.cleanup:
        cleanup()
        return
    apply = options.apply
    manifest = json.loads((p.OUT / 'source_changes.json').read_text())
    checks = json.loads((p.OUT / 'integration_check.json').read_text())
    build = json.loads((p.OUT / 'build.json').read_text())
    preview = json.loads((p.OUT / 'wire_preview.json').read_text())
    assert checks['parent_caps'] == 5 and checks['debris_caps'] == 0
    assert preview['cmp_sha256'] == build['cmp_sha256']
    assert build['files'] == manifest['assets']
    assert len(manifest['assets']) == 13
    source_payloads = {}
    source_before = {}
    for relative, expected in manifest['files'].items():
        path = checked_path(p.PY, relative)
        old = path.read_bytes() if path.exists() else None
        assert (p.sha(old) if old is not None else None) == expected['before'], relative
        new = checked_path(p.STAGE, relative).read_bytes()
        assert p.sha(new) == expected['after'], relative
        source_before[relative] = old
        source_payloads[relative] = new
    for name in [*manifest['assets'], 'manifest.json']:
        relative = p.ASSET_REL + '/' + name
        path = checked_path(p.PY, relative)
        # Never replace an unreviewed source asset.
        assert not path.exists(), str(path)
        new = checked_path(p.STAGE, relative).read_bytes()
        if name != 'manifest.json':
            assert p.sha(new) == manifest['assets'][name]['sha256']
        source_before[relative] = None
        source_payloads[relative] = new
    DataFolder = load_api()
    game = DataFolder(root=GAME)
    game_payloads = {DATA_BASE + name: source_payloads[p.ASSET_REL + '/' + name]
                     for name in manifest['assets']}
    for relative in game_payloads:
        # The user removed the old folder; fail if it was repopulated while preparing.
        assert not game.data_path(relative).exists(), relative
    unchanged_paths = [GAME / 'DATA/SHIPS/shiparch.ini',
                       GAME / 'DATA/ships/rheinland/rh_pir_playerships.mat']
    untouched = {str(path): p.sha(path.read_bytes()) for path in unchanged_paths}
    print(json.dumps({'source_files': len(source_payloads), 'game_assets': len(game_payloads),
                      'game_directory': str(game.data_path(DATA_BASE)),
                      'active_shiparch': 'unchanged; user runs normal Pythonlancer generation',
                      'debris_caps': 0, 'salt': manifest['salt']}, indent=2), flush=True)
    if not apply:
        return
    processes = subprocess.run(['powershell', '-NoProfile', '-Command',
        'Get-Process freelancer,FLServer -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName'],
        capture_output=True, text=True)
    if processes.stdout.strip():
        raise RuntimeError('Close Freelancer/FLServer before installing assets')
    transaction = checked_path(p.OUT, 'install_transaction')
    transaction.mkdir(exist_ok=True)
    for relative, data in source_before.items():
        if data is not None:
            file = checked_path(transaction, 'source/' + relative)
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_bytes(data)
    p.save(transaction / 'before.json', json.dumps({k: p.sha(v) if v is not None else None
                                                   for k, v in source_before.items()}, indent=2))
    changed_sources = []
    try:
        for relative, data in source_payloads.items():
            file = checked_path(p.PY, relative)
            file.parent.mkdir(parents=True, exist_ok=True)
            changed_sources.append(relative)
            file.write_bytes(data)
        game.sync_rh_pir_elite(game_payloads)
        for relative, data in source_payloads.items():
            assert checked_path(p.PY, relative).read_bytes() == data
        for relative, data in game_payloads.items():
            assert game.data_path(relative).read_bytes() == data
        # Exercise installed modules in a new process; output is workspace-only.
        subprocess.run([sys.executable, '-B', str(p.REPO / 'tools/procedural_ships/rh_pir_elite_pythonlancer.py'),
                        'installed'], cwd=p.REPO, check=True)
        assert (p.OUT / 'installed_shiparch.ini').read_bytes() == (p.OUT / 'staged_shiparch.ini').read_bytes()
        assert {str(path): p.sha(path.read_bytes()) for path in unchanged_paths} == untouched
    except BaseException:
        # DATA rollback uses the same DataFolder entry point.
        game.sync_rh_pir_elite({name: None for name in game_payloads})
        for relative in reversed(changed_sources):
            file = checked_path(p.PY, relative)
            old = source_before[relative]
            if old is None:
                file.unlink(missing_ok=True)
            else:
                file.write_bytes(old)
        raise
    report = dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  source_files={name: p.sha(data) for name, data in source_payloads.items()},
                  game_assets={name: p.sha(data) for name, data in game_payloads.items()},
                  unchanged=untouched, active_shiparch_written=False,
                  fresh_installed_generation_matches_review=True,
                  debris_caps=0, salt=manifest['salt'], game_launched=False)
    p.save(p.OUT / 'installation.json', json.dumps(report, indent=2))
    # Delete only transaction files we created, without recursive traversal.
    for relative, data in source_before.items():
        if data is not None:
            checked_path(transaction, 'source/' + relative).unlink()
    checked_path(transaction, 'before.json').unlink()
    print('INSTALLED AND VERIFIED; ACTIVE SHIPARCH AND SHARED MAT UNCHANGED', flush=True)


if __name__ == '__main__':
    sys.dont_write_bytecode = True
    main()
