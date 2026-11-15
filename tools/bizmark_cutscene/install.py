"""Install the reviewed scene, blend and dump; retain previous versions locally."""
import hashlib
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parent
ASSETS = Path('D:/Games/FL_MOD/Assets')
FILES = {
    'content.py': ASSETS / 'Pythonlancer/story/cutscenes/content.py',
    'light.lua': ASSETS / 'Pythonlancer/templates/cutscenes/entity/light.lua',
    'path_anim.lua': ASSETS / 'Pythonlancer/templates/cutscenes/event/path_anim.lua',
    'm01_bizmark.py': ASSETS / 'Pythonlancer/story/cutscenes/story_scenes/m01_bizmark.py',
    'm01_bizmark.blend': ASSETS / 'SCENES/m01_bizmark.blend',
    'm01_bizmark.json': ASSETS / 'SCENES/DUMPS/m01_bizmark.json',
}
BACKUP = ROOT / 'previous'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None


if '--prepare' in sys.argv:
    BACKUP.mkdir(exist_ok=True)
    manifest = {}
    for name, target in FILES.items():
        backup = BACKUP / name
        if backup.exists() and digest(backup) != digest(target):
            raise RuntimeError(f'Existing backup differs from live file: {target}')
        if target.exists():
            shutil.copyfile(target, backup)
        manifest[name] = {'old':digest(target), 'new':digest(ROOT / name)}
    (BACKUP / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Prepared backups of existing scene and generator files; installation manifest saved.')
elif '--apply' in sys.argv:
    manifest = json.loads((BACKUP / 'manifest.json').read_text())
    for name, target in FILES.items():
        assert digest(ROOT / name) == manifest[name]['new'], f'Staged file changed: {name}'
        assert digest(target) in (manifest[name]['old'], manifest[name]['new']), f'Live file changed: {target}'
    for name, target in FILES.items():
        shutil.copyfile(ROOT / name, target)
        assert digest(target) == manifest[name]['new']
        print(f'Installed and verified: {target}')
else:
    raise SystemExit('Use --prepare or --apply')
