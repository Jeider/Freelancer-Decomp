"""Install tested station docking engine changes into the running mod's bin tree."""
import argparse, hashlib, json, os, shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GAME=Path('D:/Games/FL_MOD');OUT=ROOT/'out/stations/station_docking'
BUILD=ROOT/'src/obj/train_courier/rpg1/bin'
NAMES=('Common.dll','Common.pdb','freelancer.exe','freelancer.pdb')
SOURCES=('src/Common/common_aiintercept.cpp','src/Common/common_dockbehavior.cpp',
 'src/Common/common_archetype_ships.cpp','src/include/common_archetype.h',
 'src/freelancer/Client/player_route.cpp')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--prepare',action='store_true');ap.add_argument('--apply',action='store_true');args=ap.parse_args()
 if args.prepare:
  for name in ('resolver','range'):assert 'PASS ' in (OUT/(name+'.log')).read_text()
  log=(ROOT/'out/stations/station_batch/batch_cambridge_research/physics_candidate/result.log').read_text()
  assert str(BUILD/'Common.dll') in log and 'CLEAR_APPROACHES 8' in log and 'PASS: create, simulate, destroy' in log
  checked={str(p.relative_to(ROOT)):sha(p) for p in [*(BUILD/n for n in NAMES),*(ROOT/n for n in SOURCES),OUT/'resolver.log',OUT/'range.log']}
  (OUT/'validated.json').write_text(json.dumps(dict(checked=checked,before={n:sha(GAME/'bin'/n) for n in NAMES}),indent=2))
 report=json.loads((OUT/'validated.json').read_text())
 for name,digest in report['checked'].items():assert sha(ROOT/name)==digest,name
 for name,digest in report['before'].items():assert sha(GAME/'bin'/name)==digest,name+' changed since validation'
 if not args.apply:print('Validated Common + client; ready to install');return
 # One reusable engine rollback, no timestamped copies of the game/DATA tree.
 rollback=ROOT/'out/engine_rollback';rollback.mkdir(exist_ok=True)
 before={n:(GAME/'bin'/n).read_bytes() for n in NAMES}
 for n,raw in before.items():
  if not (rollback/n).exists():(rollback/n).write_bytes(raw)
 touched=[]
 try:
  for n in NAMES:
   target=GAME/'bin'/n;temporary=target.with_name(n+'.station_docking.tmp')
   assert sha(target)==report['before'][n]
   try:
    shutil.copyfile(BUILD/n,temporary);assert sha(temporary)==sha(BUILD/n)
    os.replace(temporary,target);touched.append(n)
   finally:temporary.unlink(missing_ok=True)
  for n in NAMES:assert sha(GAME/'bin'/n)==sha(BUILD/n)
 except Exception:
  for n in reversed(touched):(GAME/'bin'/n).write_bytes(before[n])
  raise
 baseline_path=ROOT/'out/pythonlancer_preservation/baseline.json'
 baseline=json.loads(baseline_path.read_text())
 # Record the previous baseline as well: older unrelated installs may not have updated it.
 report['previous_baseline']={n:baseline.get('bin/'+n) for n in NAMES}
 for n in NAMES:
  if 'bin/'+n in baseline:baseline['bin/'+n]=sha(GAME/'bin'/n)
 baseline_path.write_text(json.dumps(baseline,indent=2))
 report['installed']={n:sha(GAME/'bin'/n) for n in NAMES}
 (OUT/'installed.json').write_text(json.dumps(report,indent=2))
 print('Installed and verified bin/Common.dll + freelancer.exe and symbols. Pythonlancer not run.')
if __name__=='__main__':main()
