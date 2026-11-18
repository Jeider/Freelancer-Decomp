"""Install only the approved v3 body DFM through DataFolder, with rollback."""
import argparse,hashlib,json,sys,runpy
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import GAME,DataFolder
OUT=ROOT/'out/reichman_body_test_v3';REL='CHARACTERS/BODIES/rh_reichman_body.dfm'
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
report=json.loads((OUT/'report.json').read_text())
live=DataFolder(root=GAME);stage=DataFolder(root=OUT/'stage')
old=live.data_path(REL).read_bytes();desired=stage.data_path(REL).read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(desired)==report['prototype_sha256'],'Staged DFM does not match approved v3'
assert sha(old) in (report['source_sha256'],report['prototype_sha256']),'Live body changed independently'
if old==desired:
    print('Approved v3 DFM already installed and verified.');raise SystemExit(0)
runpy.run_path(str(ROOT/'tools/reichman_body/check.py'),run_name='__main__')
if not args.apply:
    print('Validated. Use --apply to install only the DFM.');raise SystemExit(0)
backup=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
DataFolder(root=backup).sync_data_file(REL,old)
try:
    live.sync_data_file(REL,desired)
    assert live.data_path(REL).read_bytes()==desired
except Exception:
    live.sync_data_file(REL,old)
    raise
result=dict(file=str(live.data_path(REL)),sha256=sha(desired),backup=str(backup),mesh_only=True,preview_shader_maps_installed=False)
(OUT/'installed.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
