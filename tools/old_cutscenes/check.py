"""Read-only regression and real-source checks; --installed checks live modules."""
import importlib.util
import hashlib
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent
PYTHONLANCER = pathlib.Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path.insert(0, str(PYTHONLANCER))


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


if '--installed' not in sys.argv:
    load('story.cutscenes.thn_parser', ROOT / 'thn_parser.py')
    old = load('story.cutscenes.old_format', ROOT / 'old_format.py')
    old._DB = PYTHONLANCER / 'story/cutscenes/db/facial_anims.json'

tests = load('test_old_format', ROOT / 'test_old_format.py')
result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(tests))
if not result.wasSuccessful():
    sys.exit(1)

from story.cutscenes.old_format import parse_old_motions
from story.cutscenes.thn_parser import _tokens

files = motions = facial = binary = 0
failures = []
# Verified defects in the existing corpus, pinned to exact source bytes.
# A changed file must either parse successfully or be investigated again.
known_invalid = {
    'm05_equip_start.thn': (
        'de0c36426e1bc895784715f5c9973c292e4a1641a80296cef5f2582d0825927d',
        'Unclosed delimiter at line 406, column 8'),
    'm05_equip_support.thn': (
        '3950dbc72d67fd47c61a720d58d3eeec7e0ad78fc5b8c69a537a6ad52caa3115',
        'START_MOTION requires delay, type, targets and properties at line 1371, column 2'),
}
rejected = 0
for path in sorted(pathlib.Path('D:/Games/FL_MOD/DATA/SCRIPTS/MOD').rglob('*.thn')):
    raw = path.read_bytes()
    if raw.startswith(b'\x1bLua'):
        binary += 1
        continue
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('cp1251')
    try:
        events = parse_old_motions(text)
        # Independent lexical count catches unrecognized/lost motion tables.
        expected = sum(t.kind == 'name' and t.value == 'START_MOTION' for t in _tokens(text))
        if len(events) != expected:
            raise AssertionError(f'{len(events)} parsed versus {expected} active START_MOTION tokens')
    except Exception as error:
        if known_invalid.get(path.name) == (hashlib.sha256(raw).hexdigest(), str(error)):
            rejected += 1
            print(f'Expected source rejection: {path.name}: {error}')
            continue
        failures.append((path.name, str(error)))
        continue
    files += 1
    motions += len(events)
    facial += sum(e['facial'] for e in events)
print(f'Corpus: {files} THN files, {motions} motions, {facial} facial; no lost motion tokens.')
print(f'Binary Lua files outside the text parser scope: {binary}.')
print(f'Known malformed sources correctly rejected: {rejected}.')
for name, error in failures:
    print(f'REJECTED {name}: {error}')
if failures:
    sys.exit(1)
