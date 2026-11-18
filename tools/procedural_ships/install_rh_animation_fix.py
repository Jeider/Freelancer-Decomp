"""Install only the explicitly requested EngBase crash fix; no ship/DATA writes."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
STAGE=ROOT/'src/obj/ship_damage'
BIN=Path('D:/Games/FL_MOD/bin')
REPORT=ROOT/'out/ship_design/rh_elite/rh_pir_elite/damage_refinement/engine_install.json'
OLD={'EngBase.dll':'abf929691d5758988241806a08ec03341e119f364c29a464f8ae1093096b6666',
     'EngBase.pdb':'2e9b9e528259947ec14300eb5660b643361e82a0332d010d80691e8cb08ecb3e'}
NEW={'EngBase.dll':'d393140f150ecd541b35022a63c261162a2e6a344bbbba9a9a727e71ad8e1e8f',
     'EngBase.pdb':'bbee40f6b43ca7f4af96c2bb9fa28710a152c86f7bce6a0c57fd24c9d479da37'}
SOURCE='a70cc19c3341dac4724b2ce534c3487b7d8464ffa3df327fe847662723b9f61b'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def owned(path):
    root=STAGE.resolve();absolute=path.resolve()
    assert absolute.is_relative_to(root) and absolute!=root
    for p in [path,*path.parents]:
        if p==root.parent:break
        assert not p.is_symlink() and not p.is_junction(),p
    return absolute


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    assert sha(ROOT/'src/EngBase/EngBase.cpp')==SOURCE,'Source changed since checked build'
    native=json.loads((REPORT.parent/'native_check.json').read_text())
    assert native['dll_sha256']==NEW['EngBase.dll'] and len(native['models'])==2
    assert all(m['passes']==5 for m in native['models'])
    assert (STAGE/'check.log').read_text().count('PASS:')==3
    for name in NEW:
        assert sha(STAGE/'bin'/name)==NEW[name],name
        assert sha(BIN/name)==OLD[name],'Installed binary changed: '+name
    # Snapshot only this task's binaries/intermediates for removal after verification.
    cleanup={p:(sha(p),p.stat().st_mtime_ns) for p in STAGE.rglob('*') if p.is_file() and
             p.suffix.lower() in ('.dll','.pdb','.lib','.obj','.exe','.iobj','.ipdb','.res','.recipe','.tlog','.lastbuildstate')}
    for p in cleanup:owned(p)
    print(json.dumps(dict(target=str(BIN),files=NEW,ship_assets='untouched',cleanup_files=len(cleanup)),indent=2))
    if not args.apply:return
    processes=subprocess.run(['powershell','-NoProfile','-Command',
        'Get-Process freelancer,FLServer -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName'],
        capture_output=True,text=True)
    assert not processes.stdout.strip(),'Close Freelancer/FLServer before installing the DLL'
    backups=owned(STAGE/'install_transaction');backups.mkdir(exist_ok=True)
    old={name:(BIN/name).read_bytes() for name in NEW}
    for name,data in old.items():
        path=owned(backups/name);assert not path.exists();path.write_bytes(data)
    replaced=[]
    try:
        for name in NEW:
            # Check again immediately before replacement; never overwrite parallel work.
            assert sha(BIN/name)==OLD[name]
            replaced.append(name);(BIN/name).write_bytes((STAGE/'bin'/name).read_bytes())
        assert all(sha(BIN/name)==digest for name,digest in NEW.items())
    except BaseException:
        for name in reversed(replaced):(BIN/name).write_bytes(old[name])
        raise
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),files=NEW,previous=OLD,
        directory=str(BIN),source_sha256=SOURCE,native_checks=10,ship_assets_written=False,game_launched=False)
    REPORT.write_text(json.dumps(report,indent=2))
    for name,data in old.items():
        p=owned(backups/name);assert p.read_bytes()==data;p.unlink()
    backups.rmdir()
    deleted=[]
    for path,(digest,mtime) in cleanup.items():
        path=owned(path)
        assert path.stat().st_mtime_ns==mtime and sha(path)==digest,'Concurrent staging change; stop cleanup'
        path.unlink();deleted.append(str(path.relative_to(ROOT)))
    report['removed_staging_files']=deleted;REPORT.write_text(json.dumps(report,indent=2))
    print('INSTALLED AND VERIFIED; task build copies cleaned; model package retained')


if __name__=='__main__':main()
