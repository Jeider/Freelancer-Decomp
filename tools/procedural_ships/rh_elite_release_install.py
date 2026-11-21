"""Install this accepted RH elite release only after an explicit install request.

--plan is read-only. --apply writes the 12 model files through DataFolder and
updates the matching Pythonlancer source assets plus the reviewed template.
Never edits active shiparch.ini, writes MAT files, runs a full generator or
launches Freelancer/FLServer. No historical installer is invoked.
"""
import argparse
import datetime
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

sys.dont_write_bytecode=True
REPO=Path(__file__).resolve().parents[2]
OUT=REPO/'out/ship_design/rh_elite/rh_pir_elite/tail_rim/release'
ASSETS=OUT/'assets'
GAME=Path('D:/Games/FL_MOD')
PY=GAME/'Assets/Pythonlancer'
BASE='ships/rheinland/rh_pir_elite/'
TEMPLATE='templates/hardcoded_inis/shiparch/simples/pir_nmd.ini'
SCRIPT=Path(__file__).resolve()


def digest(data):return hashlib.sha256(data).hexdigest()


def sha(path):return digest(path.read_bytes())


def read(name):return json.loads((OUT/name).read_text(encoding='utf8'))


def save(name,obj):
    (OUT/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


def checked(root,relative):
    root=root.resolve();path=root/relative
    assert path.resolve().is_relative_to(root) and path.resolve()!=root, str(path)
    for current in [path,*path.parents]:
        if current==root:break
        assert not current.is_symlink() and not current.is_junction(),('Reparse path',current)
    return path.resolve()


def api():
    spec=importlib.util.spec_from_file_location('rh_release_data_folder',PY/'tools/data_folder.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod.DataFolder


def plan():
    handoff=read('handoff.json');manifest=read('export.json')
    assert handoff['cmp_sha256']==manifest['files']['rh_pir_elite.cmp']['sha256']
    assert handoff['files']==manifest['files'] and len(manifest['files'])==12
    expected={'rh_pir_elite.cmp','rh_pir_elite.sur'}
    expected|={'rh_pir_elite_dmg_'+z+ext for z in ('port_wing','starboard_wing','port_engine','starboard_engine','tail') for ext in ('.3db','.sur')}
    assert set(manifest['files'])==expected
    for name,entry in manifest['files'].items():assert sha(ASSETS/name)==entry['sha256']
    for name,h in handoff['review_files'].items():assert sha(OUT/name)==h,(name,'review changed')
    for p,h in read('sources.json')['files'].items():assert sha(Path(p))==h,(p,'source changed since review')
    changes=read('pythonlancer_source_changes.json');assert set(changes)=={TEMPLATE}
    assert sha(PY/TEMPLATE)==changes[TEMPLATE]['before']
    assert sha(OUT/'pythonlancer'/TEMPLATE)==changes[TEMPLATE]['after']
    data=api()(root=GAME)
    source={f'assets/{BASE}{name}':(ASSETS/name).read_bytes() for name in expected}
    source[f'assets/{BASE}manifest.json']=(ASSETS/'manifest.json').read_bytes()
    source[TEMPLATE]=(OUT/'pythonlancer'/TEMPLATE).read_bytes()
    payload={BASE+name:(ASSETS/name).read_bytes() for name in expected}
    destinations=[checked(PY,p) for p in source]+[checked(GAME/'DATA',p) for p in payload]
    assert len(destinations)==26
    before={str(p):sha(p) if p.exists() else None for p in destinations}
    protected={str(p):sha(p) for p in (GAME/'DATA/SHIPS/shiparch.ini',GAME/'DATA/ships/rheinland/rh_pir_playerships.mat',PY/'tools/data_folder.py')}
    save('installation_plan.json',dict(game_files=12,source_files=14,source_template=TEMPLATE,
         files_before=before,protected=protected,active_shiparch_written=False,game_launched=False))
    print('PLAN: 12 game assets + 12 source assets, manifest and one reviewed template. No MAT or active shiparch writes.',flush=True)
    return data,payload,source,before,protected


def verify_installed():
    sys.path.insert(0,str(PY))
    from types import SimpleNamespace
    from managers.ids import IDsManager
    from managers.jinja_manager import JinjaTemplateManager
    from managers.shiparch import ShiparchManagerV2
    from tools.data_folder import DataFolder
    from jinja2 import FileSystemLoader
    offline=checked(OUT,'installed_review')
    original_path=DataFolder.data_path
    def guarded(self,relative):
        result=original_path(self,relative)
        assert result.is_relative_to(offline),('Unexpected DATA output',result)
        return result
    DataFolder.data_path=guarded
    core=SimpleNamespace(write=False,build_folder=None,misc_equip=None)
    core.ids=IDsManager(core);core.tpl_manager=JinjaTemplateManager()
    core.tpl_manager.environment.loader=FileSystemLoader(str(PY/'templates'))
    manager=ShiparchManagerV2(core)
    for ship in manager.ships:ship.used=True
    generated=manager.get_shiparch_content()
    expected=(OUT/'pythonlancer_review/DATA/SHIPS/shiparch.ini').read_text(encoding='utf8')
    assert generated==expected,'Installed source generation differs from reviewed draft'
    folder=DataFolder(root=offline)
    folder.sync_rh_pir_elite()  # exercise actual installed source manifest
    manifest=read('export.json')
    for name,entry in manifest['files'].items():
        assert sha(folder.data_path(BASE+name))==entry['sha256']
    for name in manifest['files']:folder.remove_data_file(BASE+name)
    save('installed_source_check.json',dict(cmp_sha256=manifest['files']['rh_pir_elite.cmp']['sha256'],
         generated_shiparch_matches_review=True,ships=len(manager.ships),source_manifest_load_verified=True,
         active_shiparch_written=False))
    print('Installed source verified: generation matches review; source manifest loads all 12 assets.',flush=True)


def apply():
    data,payload,source,before,protected=plan()
    assert shutil.disk_usage(OUT).free>100*1024**2
    transaction=checked(OUT,'installation_transaction')
    transaction.mkdir(exist_ok=True)
    assert not list(transaction.iterdir()),'Previous installation transaction requires inspection'
    backups={}
    for index,(name,h) in enumerate(before.items()):
        path=Path(name);assert (sha(path) if path.exists() else None)==h
        if h is not None:
            backup=checked(transaction,f'{index:02d}.backup')
            backup.write_bytes(path.read_bytes());assert sha(backup)==h
            backups[name]=backup
    save('installation_transaction/before.json',dict(before=before,backups={p:str(v) for p,v in backups.items()}))
    done=[]
    try:
        for relative,blob in source.items():
            path=checked(PY,relative);path.parent.mkdir(parents=True,exist_ok=True)
            done.append(path);path.write_bytes(blob)
        # All working DATA writes, including recovery, use its single public API.
        data.sync_rh_pir_elite(payload)
        for relative,blob in source.items():assert checked(PY,relative).read_bytes()==blob
        for relative,blob in payload.items():assert data.data_path(relative).read_bytes()==blob
        subprocess.run([str(PY/'.venv/Scripts/python.exe'),'-B',str(SCRIPT),'--verify-installed'],cwd=str(REPO),check=True)
        assert all(sha(Path(p))==h for p,h in protected.items())
    except BaseException:
        # Recover only this interrupted transaction, never a prior installation.
        old_game={relative:(backups[str(data.data_path(relative))].read_bytes() if before[str(data.data_path(relative))] else None) for relative in payload}
        data.sync_rh_pir_elite(old_game)
        for path in reversed(done):
            if before[str(path)] is None:path.unlink(missing_ok=True)
            else:path.write_bytes(backups[str(path)].read_bytes())
        assert all((sha(Path(p)) if Path(p).exists() else None)==h for p,h in before.items())
        raise
    report=dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                authorization='User explicitly requested: установи комплект',
                game_files={relative:digest(blob) for relative,blob in payload.items()},
                source_files={relative:digest(blob) for relative,blob in source.items()},protected=protected,
                active_shiparch_written=False,shared_mat_written=False,game_launched=False,
                installed_generation_matches_review=True,staging_binaries_removed=False)
    save('installation.json',report)
    # Verify both installed copies before deleting each exact package/backup path.
    for name,info in read('export.json')['files'].items():
        assert sha(checked(GAME/'DATA',BASE+name))==sha(checked(PY,'assets/'+BASE+name))==info['sha256']
        stage=checked(ASSETS,name);assert sha(stage)==info['sha256'];stage.unlink()
    for name,backup in backups.items():
        assert backup.parent==transaction.resolve() and sha(backup)==before[name]
        backup.unlink()
    checked(transaction,'before.json').unlink()
    transaction.rmdir()
    report['staging_binaries_removed']=True;report['transaction_backups_removed']=True
    save('installation.json',report)
    print('INSTALLED AND VERIFIED. Package binaries and transaction backups removed; authoring sources retained.',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--plan',action='store_true')
    parser.add_argument('--apply',action='store_true')
    parser.add_argument('--verify-installed',action='store_true')
    args=parser.parse_args()
    if args.apply:apply()
    elif args.verify_installed:verify_installed()
    else:plan()
