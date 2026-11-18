"""Reviewed damage-only repair. Never rewrites the ship CMP, shared MAT or INI."""
import argparse
import datetime
import json
import subprocess
from pathlib import Path
import install_rh_damage_revision as previous

ROOT=previous.ROOT
OUT=ROOT/'out/ship_design/rh_elite/rh_pir_elite/engine_damage_closed'
ASSETS=OUT/'assets'
GAME,PY,REL,SOURCE=previous.GAME,previous.PY,previous.REL,previous.SOURCE
sha,read,checked=previous.sha,previous.read,previous.checked


def main():
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');args=p.parse_args()
    build=json.loads((OUT/'build.json').read_text(encoding='utf8'))
    assert len(build['files'])==10
    for name,expected in build['source_hashes'].items():
        assert sha(Path(name).read_bytes())==expected,('Source changed',name)
    files={name:(ASSETS/name).read_bytes() for name in build['files']}
    for name,content in files.items():
        assert sha(content)==build['files'][name]['sha256'],name
        assert name.startswith('rh_pir_elite_dmg_') and Path(name).suffix in ('.sur','.3db')
    for part in build['parts'].values():
        assert not any(part['checks']['decoded_topology'].values())
        assert part['checks']['collision']['uncovered']==0
    mf=PY/SOURCE/'manifest.json';manifest=json.loads(mf.read_text(encoding='utf8'))
    for name,expected in manifest['files'].items():
        assert sha((PY/SOURCE/name).read_bytes())==expected['sha256'],('Edited source asset',name)
    assert manifest['files']['rh_pir_elite.cmp']['sha256']==build['source_cmp_sha256']
    manifest['files'].update(build['files'])
    manifest['engines']={s:build['parts'][s+'_engine'] for s in ('port','starboard')}
    manifest['damage_revision']=dict(name='closed custom engines / mechanical backing',
        salt=build['salt'],parts=build['parts'],build_report=str(OUT/'build.json'))
    # Preserve the CMP's existing salt; only damage VMS resources were re-exported.
    source={SOURCE+n:v for n,v in files.items()}
    source[SOURCE+'manifest.json']=json.dumps(manifest,indent=2,ensure_ascii=False).encode('utf8')
    game={REL+n:v for n,v in files.items()}
    DataFolder=previous.api(PY/'tools/data_folder.py');data=DataFolder(root=GAME)
    before_source={n:read(checked(PY,n)) for n in source}
    before_game={n:read(data.data_path(n)) for n in game}
    protected=[GAME/'DATA/SHIPS/shiparch.ini',GAME/'DATA/ships/rheinland/rh_pir_playerships.mat',
        GAME/'bin/EngBase.dll',PY/'tools/data_folder.py',
        PY/'templates/hardcoded_inis/shiparch/playerships/rh_pir_elite.ini']
    for n in ('rh_pir_elite.cmp','rh_pir_elite.sur'):
        protected.extend((GAME/'DATA'/REL/n,PY/SOURCE/n))
    preserve={str(p):sha(p.read_bytes()) for p in protected}
    assert preserve[str(protected[1])]==build['shared_mat_sha256']
    plan=dict(source_before={n:previous.digest(v) for n,v in before_source.items()},
        source_after={n:sha(v) for n,v in source.items()},
        game_before={n:previous.digest(v) for n,v in before_game.items()},
        game_after={n:sha(v) for n,v in game.items()},unchanged=preserve,salt=build['salt'])
    plan_path=OUT/'install_plan.json'
    if not args.apply:
        plan_path.write_text(json.dumps(plan,indent=2));print('READY: 10 damage assets + source manifest; main ship, MAT and INI preserved');return
    assert json.loads(plan_path.read_text())==plan,'State changed since review'
    proc=subprocess.run(['powershell','-NoProfile','-Command',
        'Get-Process freelancer,FLServer -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName'],
        capture_output=True,text=True)
    assert not proc.stdout.strip(),'Close Freelancer/FLServer first'
    transaction=checked(OUT,'install_transaction');transaction.mkdir(exist_ok=False)
    backups=[]
    for label,entries in [('source',before_source),('data',before_game)]:
        for n,old in entries.items():
            if old is None:continue
            backup=checked(transaction,label+'/'+n);backup.parent.mkdir(parents=True,exist_ok=True)
            backup.write_bytes(old);backups.append((backup,sha(old)))
    changed=[];game_started=False
    try:
        for n,content in source.items():
            target=checked(PY,n);assert read(target)==before_source[n]
            changed.append(n);target.write_bytes(content)
        # Exercise the normal-build source reader without touching DATA.
        captured={}
        class Capture(DataFolder):
            def sync_data_file(self,name,content):captured[name]=content
            def remove_data_file(self,name):raise AssertionError('Unexpected removal')
        Capture(root=GAME).sync_rh_pir_elite()
        assert len(captured)==12 and all(captured[n]==v for n,v in game.items())
        assert all(data.data_path(n).read_bytes()==v for n,v in captured.items() if n not in game)
        assert all(read(data.data_path(n))==v for n,v in before_game.items())
        game_started=True;data.sync_rh_pir_elite(game)
        assert all(data.data_path(n).read_bytes()==v for n,v in game.items())
        assert all(checked(PY,n).read_bytes()==v for n,v in source.items())
        assert all(sha(Path(n).read_bytes())==v for n,v in preserve.items())
    except BaseException:
        if game_started:data.sync_rh_pir_elite(before_game)
        for n in reversed(changed):
            target=checked(PY,n);old=before_source[n]
            if old is None:target.unlink(missing_ok=True)
            else:target.write_bytes(old)
        raise
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**plan,
        installed=True,game_launched=False,source_generation_verified=True,
        cmp_written=False,mat_written=False,ini_written=False,game_asset_count=10)
    (OUT/'installation.json').write_text(json.dumps(report,indent=2))
    for path,expected in backups:
        assert path.resolve().is_relative_to(transaction.resolve()) and not path.is_symlink()
        assert sha(path.read_bytes())==expected;path.unlink()
    for path in sorted((p for p in transaction.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):
        assert path.resolve().is_relative_to(transaction.resolve()) and not path.is_junction() and not path.is_symlink()
        path.rmdir()
    transaction.rmdir()
    print('INSTALLED: 10 damage files + Pythonlancer source; verified. CMP / main SUR / shared MAT / INI unchanged.')


if __name__=='__main__':main()
