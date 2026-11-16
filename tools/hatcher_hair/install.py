"""Install/restore the single Hatcher asset via the central DATA API."""
import argparse,hashlib,json
from datetime import datetime
from build import OUT,REL,GAME,DataFolder
from check import check

parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');parser.add_argument('--restore',action='store_true');args=parser.parse_args()
if args.apply and args.restore:parser.error('Choose apply or restore')
check()
live=DataFolder(root=GAME);stage=DataFolder(root=OUT/'stage')
old=live.data_path(REL).read_bytes();original=(OUT/'original.dfm').read_bytes();new=stage.data_path(REL).read_bytes()
installed=OUT/'installed.json'
previous_hash=json.loads(installed.read_text())['sha256'] if installed.exists() else None
if old not in (original,new) and hashlib.sha256(old).hexdigest()!=previous_hash:
    raise SystemExit('Live head changed independently; refusing to overwrite it.')
desired=original if args.restore else new
if not(args.apply or args.restore):raise SystemExit('Validated. Use --apply to install, --restore to roll back.')
backup=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
DataFolder(root=backup).sync_data_file(REL,old)
try:
    live.sync_data_file(REL,desired)
    assert live.data_path(REL).read_bytes()==desired
except Exception:
    live.sync_data_file(REL,old)
    raise
manifest=dict(file=REL,backup=str(backup),sha256=hashlib.sha256(desired).hexdigest(),restored=args.restore)
(OUT/'installed.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest))
