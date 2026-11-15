"""Stage the non-DLSS renderer loader fix with a guarded backup installer."""
from pathlib import Path
import hashlib
import json
import shutil
import sys

root=Path(__file__).resolve().parents[2]
game=Path('D:/Games/FL_MOD')
stage=root/'src/obj/base_neural_loader_install'
paths=['bin/RP9.dll','bin/RP9.pdb']
source=root/'src/obj/train_courier/rpg1'
if '--dlss-menu' in sys.argv:
    stage=root/'src/obj/base_neural_menu_install'
    source=root/'out/base_neural/on'
    paths+=['bin/freelancer.exe','bin/freelancer.pdb']
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.exists() else None
for relative in paths:
    target=stage/relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source/relative, target)
(stage/'manifest.json').write_text(json.dumps(dict(game=str(game), files=[
    dict(relative=p, original=digest(game/p), prepared=digest(stage/p)) for p in paths
], dependencies=[]), indent=2), encoding='utf-8')
installer=(root/'tools/graphics_settings/install.ps1').read_text(encoding='utf-8')
start=installer.index('$allowed=@(')
end=installer.index('\n', start)
installer=installer[:start]+'$allowed=@('+','.join(repr(p) for p in paths)+')'+installer[end:]
installer=installer.replace('Count -ne 7','Count -ne '+str(len(paths))).replace('codex_graphics_settings_', 'codex_neural_loader_')
(stage/'install.ps1').write_text(installer, encoding='utf-8')
print(stage/'install.ps1')
