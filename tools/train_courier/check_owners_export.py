"""Exercise fresh world export, transfer registration and repeated owner generation."""
import contextlib
import importlib.util
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT = ROOT / 'out/train_courier/owners_export_check'
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(PROJECT))
sys.dont_write_bytecode = True


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


staged = ROOT / 'out/train_courier/owners/sources'
DataFolder = load('tools.data_folder', staged / 'tools/data_folder.py').DataFolder
owners = load('checked_courier_owners', staged / 'managers/courier_owners.py')
from managers.parking_commandants import parse, one
from core import get_core

os.chdir(PROJECT)
with (OUT / 'universe.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log):
    universe = get_core().universe
raw_universe = universe.get_universe_file_content()
raw_mbases = universe.get_mbases_file_content()
with tempfile.TemporaryDirectory(dir=OUT) as temporary:
    root = Path(temporary)
    folder = DataFolder(root=root / 'game', build_to_folder='regression')
    folder.sync_data_file('UNIVERSE/universe.ini', raw_universe)
    folder.sync_data_file('MISSIONS/mbases.ini', raw_mbases)
    registry = owners.assign_registry(PROJECT, owners.source_bases(universe))
    try:
        owners.extend_catalog(universe, folder, registry, PROJECT)
    except ValueError as error:
        assert 'tc_br_avl_base' in str(error), error
    else:
        raise AssertionError('Fresh universe must reproduce missing transfer registration')
    files, registry, report = owners.generate(universe, folder, PROJECT, root / 'report', dry_run=True)
    assert len(report) == 19
    definitions = {one(r, 'nickname'): r for k, r in parse(files['UNIVERSE/universe.ini']) if k == 'base'}
    mission = [one(r, 'nickname') for k, r in parse(files['MISSIONS/mbases.ini']) if k == 'mbase']
    transfer_bases = set()
    for kind, row in parse(files['MISSIONS/TrainCourier/catalog.ini']):
        if kind not in ('courierpoint', 'courierparking'):
            continue
        base, system = one(row, 'transfer_base'), one(row, 'system')
        transfer_bases.add(base)
        assert one(definitions[base], 'system') == system
        assert mission.count(base) == 1
        assert f'UNIVERSE/TrainCourier/{base}.ini' in files
        assert f'MISSIONS/TrainCourier/launch_{system}.ini' in files
    assert 'tc_br_avl_base' in transfer_bases and len(transfer_bases) == 27
    folder.sync_courier_owners(files, root / 'backup')
    repeated, _, _ = owners.generate(universe, folder, PROJECT, root / 'repeat', dry_run=True)
    assert repeated == files, 'Second export changed output'
    # Another full universe export replaces registrations; generation restores them.
    folder.sync_data_file('UNIVERSE/universe.ini', raw_universe)
    folder.sync_data_file('MISSIONS/mbases.ini', raw_mbases)
    rebuilt, _, _ = owners.generate(universe, folder, PROJECT, root / 'rebuilt', dry_run=True)
    assert rebuilt == files
    # Existing transfer definitions must never be silently rebound to another system.
    folder.sync_data_file('UNIVERSE/universe.ini', files['UNIVERSE/universe.ini'].replace(
        b'nickname = tc_br_avl_base\nsystem = br_avl', b'nickname = tc_br_avl_base\nsystem = rh_biz'))
    try:
        owners.transfer_plan(PROJECT, folder, registry)
    except ValueError as error:
        assert 'Conflicting locomotive transfer definition' in str(error)
    else:
        raise AssertionError('Conflicting transfer definition accepted')
print('PASS: fresh universe reproduces failure; 27 transfer bases and 19 owners restored; isolated build, repeat export and conflict checks')
