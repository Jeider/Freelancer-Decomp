import sys,json,hashlib,argparse
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/hatcher_hair'))
from build import GAME,DataFolder
OUT=ROOT/'out/nomad_character/game_body_v3';manifest=json.loads((OUT/'manifest.json').read_text())
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
live=DataFolder(root=GAME);stage=DataFolder(root=OUT/'stage');sha=lambda b:hashlib.sha256(b).hexdigest()
old={};wanted={}
for rel,info in manifest['files'].items():
 old[rel]=live.data_path(rel).read_bytes() if live.data_path(rel).exists() else None;wanted[rel]=stage.data_path(rel).read_bytes()
 assert sha(wanted[rel])==info['after']
 assert (sha(old[rel]) if old[rel] is not None else None) in (info['before'],info['after']),rel+' changed independently'
if not args.apply:print('Validated staged DFM and both registrations.');raise SystemExit(0)
backup_root=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f');backup=DataFolder(root=backup_root)
for rel,b in old.items():
 if b is not None:backup.sync_data_file(rel,b)
changed=[]
try:
 for rel,b in wanted.items():
  changed.append(rel);live.sync_data_file(rel,b);assert live.data_path(rel).read_bytes()==b
except Exception:
 for rel in reversed(changed):
  if old[rel] is None:live.remove_data_file(rel)
  else:live.sync_data_file(rel,old[rel])
 raise
receipt=dict(backup=str(backup_root),files=list(wanted),body=manifest['body'],costume=manifest['costume'])
(OUT/'installed.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
