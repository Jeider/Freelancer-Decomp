"""Install the reviewed upgrade only if the user's current script is unchanged."""
import hashlib
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parent
meta=json.loads((ROOT/'baseline.json').read_text())
target=Path(meta['target'])
helper=target.parent.parent/'ru_dialogue_timing.py'
original=Path(meta['backup']).read_bytes()
assert hashlib.sha256(original).hexdigest()==meta['sha256']
assert target.read_bytes()==original, 'Live scene changed since backup; do not overwrite user edits'
if helper.exists():
    assert helper.read_bytes()==(ROOT/'ru_dialogue_timing.py').read_bytes(), 'Existing helper differs'
for name in ('m01_bizmark.py','ru_dialogue_timing.py'):
    compile((ROOT/name).read_bytes(),name,'exec')
side_backup=target.with_name(target.name+'.ru_backup_20261113_014240.bak')
if side_backup.exists():
    assert side_backup.read_bytes()==original, 'Existing backup differs'
else:
    side_backup.write_bytes(original)
shutil.copyfile(ROOT/'ru_dialogue_timing.py',helper)
shutil.copyfile(ROOT/'m01_bizmark.py',target)
assert target.read_bytes()==(ROOT/'m01_bizmark.py').read_bytes()
assert helper.read_bytes()==(ROOT/'ru_dialogue_timing.py').read_bytes()
print(f'Backup: {side_backup}')
print(f'Installed: {target}')
print(f'Installed: {helper}')
