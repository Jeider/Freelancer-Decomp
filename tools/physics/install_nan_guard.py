"""Install only the tested Common DLL/PDB, retaining one rollback set."""
import argparse,hashlib,json,shutil,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/physics_nan_guard'
BUILD=ROOT/'src/obj/train_courier/rpg1/bin'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');args=ap.parse_args()
    report=json.loads((OUT/'validated.json').read_text())
    for name,digest in report['checked'].items():assert sha(ROOT/name)==digest,name+' changed after tests'
    assert 'PASS dump replay' in (OUT/'guarded.log').read_text()
    for task in ('batch_california_tradestation','batch_odissey'):
        log=(ROOT/'out/station_batch'/task/'physics_candidate/result.log').read_text()
        assert 'COMMON '+str(BUILD/'Common.dll') in log and 'PASS: create, simulate, destroy' in log
    names=('Common.dll','Common.pdb');before={n:(GAME/'bin'/n).read_bytes() if (GAME/'bin'/n).exists() else None for n in names}
    baseline_path=ROOT/'out/pythonlancer_preservation/baseline.json';baseline=json.loads(baseline_path.read_text())
    assert baseline['bin/Common.dll']==hashlib.sha256(before['Common.dll']).hexdigest()
    if not args.apply:print('Validated engine install');return
    rollback=OUT/'rollback';rollback.mkdir(exist_ok=True)
    for name,raw in before.items():
        if raw is not None and not (rollback/name).exists():(rollback/name).write_bytes(raw)
    touched=[]
    try:
        for name in names:
            target=GAME/'bin'/name
            assert (target.read_bytes() if target.exists() else None)==before[name]
            # Do not force replacement of a running/locked engine.
            temporary=target.with_name(name+'.nan_guard.tmp')
            try:
                shutil.copyfile(BUILD/name,temporary)
                assert sha(temporary)==sha(BUILD/name)
                os.replace(temporary,target);touched.append(name)
            finally:temporary.unlink(missing_ok=True)
            assert sha(target)==sha(BUILD/name)
    except Exception:
        for name in reversed(touched):
            if before[name] is None:(GAME/'bin'/name).unlink()
            else:(GAME/'bin'/name).write_bytes(before[name])
        raise
    baseline['bin/Common.dll']=sha(GAME/'bin/Common.dll');baseline_path.write_text(json.dumps(baseline,indent=2))
    (OUT/'installed.json').write_text(json.dumps({n:sha(GAME/'bin'/n) for n in names},indent=2))
    print('Installed and verified Common.dll/Common.pdb; single rollback retained. No Pythonlancer generation.')
if __name__=='__main__':main()
