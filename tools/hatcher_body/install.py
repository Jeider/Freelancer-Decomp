"""Install only the approved smoothed Hatcher body DFM through DataFolder, with rollback."""
import argparse,hashlib,json,sys,runpy
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import GAME,DataFolder
OUT=ROOT/'out/hatcher_body_full_smooth';REL='CHARACTERS/BODIES/li_hatcher_body.dfm'
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
report=json.loads((OUT/'report.json').read_text())
live=DataFolder(root=GAME);stage=DataFolder(root=OUT/'stage')
old=live.data_path(REL).read_bytes();desired=stage.data_path(REL).read_bytes()
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(desired)==report['prototype_sha256'],'Staged DFM does not match approved smooth prototype'
assert sha(old) in (report['source_sha256'],report['prototype_sha256'], 'fd990dfdb1716bd79aaafc4bf37f9c4c944a80d00b386722688cd98ed5e280f3', '863e06924587462c1db68d68db93495a2f5e99b9f0b14466e111cee8189ceb6b', 'd9b77c691fa4e355c8e1dadfe1e4801f5aa1444073379d749d3276286d4acf39'),'Live body changed independently'
if old==desired:
    print('Approved smooth prototype DFM already installed and verified.');raise SystemExit(0)
runpy.run_path(str(ROOT/'tools/hatcher_body/check_full_smooth.py'),run_name='__main__')
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

