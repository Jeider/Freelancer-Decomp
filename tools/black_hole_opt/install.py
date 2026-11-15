"""Install the validated black-hole shader only, with source-hash guard and backup."""
from pathlib import Path
from datetime import datetime
import argparse,hashlib,shutil

root=Path(__file__).resolve().parents[2]
game=Path('D:/Games/FL_MOD')
source=root/'DATA_EXTRA/SHADERS/black_hole.hlsl'
target=game/'DATA_EXTRA/SHADERS/black_hole.hlsl'
baseline=root/'tools/black_hole_opt/baseline.hlsl'
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--apply',action='store_true')
args=parser.parse_args()
if digest(target)==digest(source):
    print('Already installed');raise SystemExit
assert digest(target)==digest(baseline),'Installed shader changed; review before replacing'
if not args.apply:
    print('Ready:',target);raise SystemExit
backup=game/'BACKUP'/('codex_black_hole_opt_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))/'black_hole.hlsl'
backup.parent.mkdir(parents=True,exist_ok=False)
shutil.copy2(target,backup)
assert digest(backup)==digest(baseline)
try:
    shutil.copy2(source,target)
    assert digest(source)==digest(target)
except Exception:
    shutil.copy2(backup,target)
    raise
print('Installed, SHA256 verified. Backup:',backup)
