"""Install the paired per-light ambient fix; never launch or stop the game."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2];GAME=Path('D:/Games/FL_MOD');OUT=ROOT/'out/hair_lighting'
FILES={'bin/RP9.dll':ROOT/'out/base_neural/on/bin/RP9.dll','bin/RP9.pdb':ROOT/'out/base_neural/on/bin/RP9.pdb','DATA_EXTRA/SHADERS/room_material.hlsl':ROOT/'DATA_EXTRA/SHADERS/room_material.hlsl'}
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args();manifest=OUT/'install_manifest.json'
if not args.apply:
 records={}
 for rel,source in FILES.items():
  dest=OUT/'stage'/rel;copy(source,dest);records[rel]=dict(before=digest(GAME/rel),after=digest(dest))
 manifest.write_text(json.dumps(records,indent=2));print('Prepared paired RP9/shader update:',manifest)
else:
 tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
 if any(b'"'+n+b'"' in tasks for n in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')):raise SystemExit('Game/server running; update staged, no files changed.')
 records=json.loads(manifest.read_text());assert set(records)==set(FILES)
 for rel,r in records.items():assert digest(GAME/rel)==r['before'] and digest(OUT/'stage'/rel)==r['after'],rel
 backup=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
 for rel in FILES:copy(GAME/rel,backup/rel)
 copy(manifest,backup/'manifest.json')
 try:
  for rel in FILES:copy(OUT/'stage'/rel,GAME/rel)
  for rel,r in records.items():assert digest(GAME/rel)==r['after'],rel
 except BaseException:
  for rel in FILES:copy(backup/rel,GAME/rel)
  raise
 result=dict(backup=str(backup),files=list(FILES),verified=True,game_launched=False)
 (OUT/'installed.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
