"""Explicitly requested ship update; DATA writes exclusively via DataFolder.

Preserves active shiparch.ini and the user-owned shared MAT. Refreshes source
assets and the two reviewed Pythonlancer lines so normal builds keep this model.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/ship_design/rh_elite/rh_pir_elite/damage_refinement'
ASSETS=OUT/'assets'
GAME=Path('D:/Games/FL_MOD')
PY=GAME/'Assets/Pythonlancer'
REL='ships/rheinland/rh_pir_elite/'
SOURCE='assets/'+REL
PLAN=OUT/'install_plan.json'


def sha(data):return hashlib.sha256(data).hexdigest()
def read(path):return path.read_bytes() if path.exists() else None
def digest(data):return sha(data) if data is not None else None


def checked(root,relative):
    root=root.resolve();path=(root/relative).resolve()
    assert path!=root and path.is_relative_to(root),(root,path)
    return path


def api(path):
    spec=importlib.util.spec_from_file_location('rh_damage_data_folder',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.DataFolder


def payloads():
    build=json.loads((ASSETS/'manifest.json').read_text(encoding='utf8'))
    native=json.loads((OUT/'native_check.json').read_text())
    assert build['separate_lod_mat_required'] is False and len(build['files'])==12
    assert native['models'][-1]['sha256']==build['files']['rh_pir_elite.cmp']['sha256']
    assert all(m['passes']==5 for m in native['models'])
    assert sha((GAME/'bin/EngBase.dll').read_bytes())==native['dll_sha256']
    files={name:(ASSETS/name).read_bytes() for name in build['files']}
    for name,data in files.items():assert sha(data)==build['files'][name]['sha256'],name
    assert sha((GAME/'DATA/ships/rheinland/rh_pir_playerships.mat').read_bytes())==build['shared_mat_sha256']
    assert sha((GAME/'DATA'/REL/'rh_pir_elite.cmp').read_bytes())==build['source_sha256'],'Preserve newer user edits'
    source={SOURCE+name:data for name,data in files.items()}
    source[SOURCE+'manifest.json']=(ASSETS/'manifest.json').read_bytes()
    # Keep the separate atlas only in the local authoring reference requested by the user.
    source[SOURCE+'rh_pir_elite_lods.mat']=None
    edits=[('tools/data_folder.py',
        b"allowed = {'rh_pir_elite.cmp', 'rh_pir_elite.sur', 'rh_pir_elite_lods.mat'}",
        b"allowed = {'rh_pir_elite.cmp', 'rh_pir_elite.sur'}")]
    for rel,old,new in edits:
        raw=(PY/rel).read_bytes();assert raw.count(old)==1,rel
        source[rel]=raw.replace(old,new)
    rel='templates/hardcoded_inis/shiparch/playerships/rh_pir_elite.ini'
    raw=(PY/rel).read_bytes()
    lines=raw.splitlines(keepends=True)
    target=b'material_library = ships\\rheinland\\rh_pir_elite\\rh_pir_elite_lods.mat'
    assert sum(line.strip()==target for line in lines)==1
    source[rel]=b''.join(line for line in lines if line.strip()!=target)
    game={REL+name:data for name,data in files.items()}
    return source,game,build


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    source,game,build=payloads()
    before_source={name:read(checked(PY,name)) for name in source}
    DataFolder=api(PY/'tools/data_folder.py');data=DataFolder(root=GAME)
    before_game={name:read(data.data_path(name)) for name in game}
    untouched=[GAME/'DATA/SHIPS/shiparch.ini',GAME/'DATA/ships/rheinland/rh_pir_playerships.mat',GAME/'bin/EngBase.dll']
    preserve={str(p):sha(p.read_bytes()) for p in untouched}
    plan=dict(source_before={n:digest(v) for n,v in before_source.items()},
        source_after={n:digest(v) for n,v in source.items()},
        game_before={n:digest(v) for n,v in before_game.items()},game_after={n:sha(v) for n,v in game.items()},
        unchanged=preserve,salt=build['salt'])
    if not args.apply:
        PLAN.write_text(json.dumps(plan,indent=2))
        print('READY: 12 game assets, 12 source assets + manifest, 2 Pythonlancer lines; active shiparch/shared MAT unchanged')
        return
    assert json.loads(PLAN.read_text())==plan,'State changed after preparation; review again'
    process=subprocess.run(['powershell','-NoProfile','-Command',
        'Get-Process freelancer,FLServer -ErrorAction SilentlyContinue | Select-Object -ExpandProperty ProcessName'],capture_output=True,text=True)
    assert not process.stdout.strip(),'Close Freelancer/FLServer before replacing models'
    transaction=checked(OUT,'ship_install_transaction');transaction.mkdir(exist_ok=True)
    backups=[]
    for kind,entries in [('source',before_source),('data',before_game)]:
        for name,old in entries.items():
            if old is None:continue
            path=checked(transaction,kind+'/'+name);assert not path.exists()
            path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(old);backups.append((path,sha(old)))
    changed_source=[];game_started=False
    try:
        for name,new in source.items():
            path=checked(PY,name);assert read(path)==before_source[name],name
            changed_source.append(name)
            if new is None:path.unlink(missing_ok=True)
            else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(new)
        # The real normal-build entry point loads the newly installed source manifest.
        Updated=api(PY/'tools/data_folder.py');updated=Updated(root=GAME)
        assert all(read(updated.data_path(n))==v for n,v in before_game.items())
        game_started=True;updated.sync_rh_pir_elite()
        for name,new in source.items():assert read(checked(PY,name))==new,name
        for name,new in game.items():assert updated.data_path(name).read_bytes()==new,name
        assert {str(p):sha(p.read_bytes()) for p in untouched}==preserve
    except BaseException:
        # Roll back only our own changed paths through the existing central DATA API.
        if game_started:data.sync_rh_pir_elite(before_game)
        for name in reversed(changed_source):
            path=checked(PY,name);old=before_source[name]
            if old is None:path.unlink(missing_ok=True)
            else:path.write_bytes(old)
        raise
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),**plan,
        installed=True,game_launched=False,game_asset_count=12,source_generation_verified=True,
        active_shiparch_written=False,shared_mat_written=False,lod_mat_supplied=False)
    (OUT/'ship_install.json').write_text(json.dumps(report,indent=2))
    # Only checked transaction files, no recursive deletion or symlink traversal.
    for path,expected in backups:
        assert path.resolve().is_relative_to(transaction.resolve()) and not path.is_symlink()
        assert sha(path.read_bytes())==expected;path.unlink()
    dirs=sorted((p for p in transaction.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True)
    for path in dirs:
        assert path.resolve().is_relative_to(transaction.resolve()) and not path.is_junction() and not path.is_symlink()
        path.rmdir()
    transaction.rmdir()
    print('INSTALLED: new ship, static unfolded wire, both full broken engines; source sync matches; temporary backups cleaned')


if __name__=='__main__':
    sys.dont_write_bytecode=True
    main()
