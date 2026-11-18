"""Stage/apply the isolated Nomad shader, map and matching RP9 build."""
import argparse,hashlib,json,shutil,subprocess
from pathlib import Path
from datetime import datetime
ROOT=Path(__file__).resolve().parents[2];GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/nomad_character/surface/install'
FILES={
 'bin/RP9.dll':ROOT/'out/base_neural/on/bin/RP9.dll',
 'bin/RP9.pdb':ROOT/'out/base_neural/on/bin/RP9.pdb',
 'DATA_EXTRA/SHADERS/room_material.hlsl':ROOT/'DATA_EXTRA/SHADERS/room_material.hlsl',
 'DATA_EXTRA/ROOM_MATERIALS/alien_nomad_surface.png':ROOT/'DATA_EXTRA/ROOM_MATERIALS/alien_nomad_surface.png',
}
for name in ('the_n_city','n_city2'):
 rel='DATA_EXTRA/ROOM_MATERIALS/nomad_city_'+name+'.png'
 FILES[rel]=ROOT/rel
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None
def copy(a,b):b.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(a,b)
ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
if not args.apply:
 records={}
 for rel,src in FILES.items():
  if sha(src)==sha(GAME/rel):continue
  copy(src,OUT/'stage'/rel);records[rel]=dict(before=sha(GAME/rel),after=sha(OUT/'stage'/rel))
 (OUT/'manifest.json').write_text(json.dumps(records,indent=2));print('Staged Nomad surface renderer');raise SystemExit(0)
records=json.loads((OUT/'manifest.json').read_text());assert set(records)<=set(FILES)
if any(rel.startswith('bin/') for rel in records):
 tasks=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
 if any(b'"'+n+b'"' in tasks for n in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')):
  raise SystemExit('Installation staged; game/server is running. No files changed.')
for rel,v in records.items():
 assert sha(GAME/rel)==v['before'],rel+' changed since staging'
 assert sha(OUT/'stage'/rel)==v['after'],rel+' staged hash mismatch'
backup=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
for rel,v in records.items():
 if v['before'] is not None:copy(GAME/rel,backup/rel)
copy(OUT/'manifest.json',backup/'manifest.json')
changed=[]
try:
 for rel,v in records.items():
  changed.append(rel);copy(OUT/'stage'/rel,GAME/rel);assert sha(GAME/rel)==v['after']
except Exception:
 for rel in reversed(changed):
  if records[rel]['before'] is None:(GAME/rel).unlink(missing_ok=True)
  else:copy(backup/rel,GAME/rel)
 raise
(OUT/'installed.json').write_text(json.dumps(dict(backup=str(backup),files=records),indent=2))
print('Installed and hash-verified Nomad renderer. Backup:',backup)
