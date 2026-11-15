"""Install only Python parser sources and regression tests; never writes DATA."""
import hashlib
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
TARGET = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
ORIGINAL = '04213eb83404dd35156e999e0d75ffa716639341426bfcade3801360f9d288d3'
FILES = {
    'thn_parser.py': 'story/cutscenes/thn_parser.py',
    'old_format.py': 'story/cutscenes/old_format.py',
    'test_old_format.py': 'tests/test_old_format.py',
}

# Preflight every destination before writing any of them.
for source, relative in FILES.items():
    destination = TARGET / relative
    if not destination.exists():
        continue
    data = destination.read_bytes()
    if data == (ROOT / source).read_bytes():
        continue
    if source != 'old_format.py' or hashlib.sha256(data).hexdigest() != ORIGINAL:
        raise RuntimeError(f'Refusing to overwrite unexpected edits: {destination}')
    backup = ROOT / 'old_format.before.py'
    if backup.exists() and backup.read_bytes() != data:
        raise RuntimeError('Existing backup does not match the original')
    if not backup.exists():
        backup.write_bytes(data)

for source, relative in FILES.items():
    destination = TARGET / relative
    shutil.copyfile(ROOT / source, destination)
    print(f'Installed {destination}')
