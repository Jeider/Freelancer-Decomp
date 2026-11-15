"""Stage/install the physical TLR experiment with checked inputs and rollback."""
from physical_model import ROOT,GAME,OUT,DataFolder,digest
import argparse
from datetime import datetime
import json
import shutil
import subprocess


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    stage=OUT/'stage';data=DataFolder(root=stage);live=DataFolder(root=GAME)
    manifest=json.loads((OUT/'manifest.json').read_text())
    records=manifest['files']
    sources={}
    for report in ('src/obj/tradelane_physical_check/verified.json','src/obj/tradelane_server_check/verified.json'):
        sources.update(json.loads((ROOT/report).read_text()))
    for path,sha in sources.items():assert digest(__import__('pathlib').Path(path).read_bytes())==sha,'Changed verified input: '+path
    if not args.apply:
        bins={}
        for name in ('Common.dll','Common.pdb','Server.dll','Server.pdb','freelancer.exe','freelancer.pdb'):
            source=ROOT/('out/base_neural/on/bin' if name.startswith('freelancer') else 'src/obj/train_courier/rpg1/bin')/name
            target=stage/'bin'/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
            bins[name]={'before':digest((GAME/'bin'/name).read_bytes()),'after':digest(target.read_bytes())}
        for name,paths in {'Common.dll':['src/Common/solar_animation.cpp','src/include/solar_animation.h'],
                           'Server.dll':['src/Server/server_solar_animation.cpp','src/Server/server_tradelane_physics.inl','src/Server/server_classes.cpp'],
                           'freelancer.exe':['src/freelancer/Client/tradelane_ring_anim.cpp','src/include/solar_animation.h']}.items():
            assert (stage/'bin'/name).stat().st_mtime>=max((ROOT/p).stat().st_mtime for p in paths),'Rebuild '+name
        dependencies={p:digest((GAME/p).read_bytes()) for p in ('bin/Content.dll','bin/RP9.dll','bin/EngBase.dll','bin/ReadFile.dll','bin/DALib.dll','bin/rpclocal.dll','bin/remoteclient.dll','DATA/SOLAR/DOCKABLE/tlr_root.3db') if (GAME/p).exists()}
        sources[str(ROOT/'tools/tradelane/physical_model.py')]=digest((ROOT/'tools/tradelane/physical_model.py').read_bytes())
        (OUT/'install.json').write_text(json.dumps({'bins':bins,'dependencies':dependencies,'sources':sources},indent=2))
        print('Staged 4 DATA files and 6 client/Common/Server binaries. No Content or RP9 replacement.');return
    package=json.loads((OUT/'install.json').read_text())
    for path,sha in package['sources'].items():assert digest(__import__('pathlib').Path(path).read_bytes())==sha,'Prepared source changed: '+path
    processes=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+n+b'"' in processes for n in (b'freelancer.exe',b'freelancer_window.exe',b'freelancer_en.exe',b'flserver.exe')),'Close game and server'
    for p,sha in package['dependencies'].items():assert digest((GAME/p).read_bytes())==sha,'Live dependency changed: '+p
    for rel,entry in records.items():
        assert digest(live.data_path(rel).read_bytes())==entry['before'],'Live DATA changed: '+rel
        assert digest(data.data_path(rel).read_bytes())==entry['after'],'Staged DATA changed: '+rel
    for name,entry in package['bins'].items():
        assert digest((GAME/'bin'/name).read_bytes())==entry['before'],'Live binary changed: '+name
        assert digest((stage/'bin'/name).read_bytes())==entry['after'],'Staged binary changed: '+name
    backup=OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S');saved=DataFolder(root=backup)
    for rel,entry in records.items():
        saved.sync_data_file(rel,live.data_path(rel).read_bytes())
        assert digest(saved.data_path(rel).read_bytes())==entry['before']
    (backup/'bin').mkdir(parents=True,exist_ok=True)
    for name,entry in package['bins'].items():
        shutil.copy2(GAME/'bin'/name,backup/'bin'/name)
        assert digest((backup/'bin'/name).read_bytes())==entry['before']
    shutil.copy2(OUT/'manifest.json',backup/'manifest.json');shutil.copy2(OUT/'install.json',backup/'install.json')
    changed_data=[];changed_bin=[]
    try:
        for name,entry in package['bins'].items():
            changed_bin.append(name);shutil.copy2(stage/'bin'/name,GAME/'bin'/name)
            assert digest((GAME/'bin'/name).read_bytes())==entry['after']
        for rel,entry in records.items():
            changed_data.append(rel);live.sync_data_file(rel,data.data_path(rel).read_bytes())
            assert digest(live.data_path(rel).read_bytes())==entry['after']
    except BaseException:
        for rel in reversed(changed_data):live.sync_data_file(rel,saved.data_path(rel).read_bytes())
        for name in reversed(changed_bin):shutil.copy2(backup/'bin'/name,GAME/'bin'/name)
        raise
    print('Installed physical TLR; all hashes verified. Backup:',backup)


if __name__=='__main__':main()
