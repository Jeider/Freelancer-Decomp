"""Stage/install the tested single-player coupling yard, with guarded backups."""
import argparse,json,shutil,subprocess
from datetime import datetime
from pathlib import Path
from install import sha,replace
ROOT=Path(__file__).resolve().parents[2];GAME=Path('D:/games/FL_MOD');OUT=ROOT/'out/train_yard';PAYLOAD=OUT/'payload'
BIN=ROOT/'src/obj/train_consist'

def validate_checks():
    for file in [OUT/'checked.json',BIN/'check.json']:
        for name,h in json.loads(file.read_text()).items():assert sha(Path(name))==h,'Checked input changed: '+name
    config=json.loads((OUT/'config_checked.json').read_text())
    assert sha(OUT/'assets.json')==config['manifest']
    for name,r in config['files'].items():assert sha(PAYLOAD/name)==r['installed'],name

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true');args=parser.parse_args()
    validate_checks()
    if not args.apply:
        assets=json.loads((OUT/'assets.json').read_text());records=assets['files']
        sources={}
        for module,folder,ext in [('Common',BIN,'dll'),('Server',ROOT/'src/obj/train_yard/Server/bin','dll'),('freelancer',ROOT/'src/obj/train_yard/freelancer/bin','exe')]:
            for suffix in [ext,'pdb']:
                name='bin/'+module+'.'+suffix;source=folder/(module+'.'+suffix)
                target=PAYLOAD/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
                records[name]={'original':sha(GAME/name),'installed':sha(target)};sources[name]=str(source)
        tlog=ROOT/'src/obj/train_yard/freelancer/obj/freelancer.tlog/CL.command.1.tlog'
        rows=tlog.read_text(encoding='utf-16').splitlines()
        commands=[rows[i+1] for i,r in enumerate(rows[:-1]) if r.startswith('^')]
        assert commands and all('FREELANCER_RPG_WORLD' in c for c in commands),'Client must retain RPG=1'
        assert sha(GAME/'bin/Common.dll')==json.loads((BIN/'build.json').read_text())['baseline'],'Installed Common updated during build'
        for name,r in records.items():assert sha(GAME/name)==r['original'],name
        dependencies={name:sha(GAME/name) for name in ['bin/Content.dll','DATA/COCKPITS/UTILITY/ge_train_player.ini','DATA/SHIPS/UTILITY/FREIGHT_TRAIN/train_consist.cmp','DATA/SHIPS/UTILITY/FREIGHT_TRAIN/train_consist.sur','SAVE/Accts/SinglePlayer/biz_le2_train20.fl']}
        manifest={'files':records,'sources':sources,'dependencies':dependencies,'save':assets['save'],'FreelancerRpgWorld':1}
        (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2));print('Staged and verified',len(records),'files; RPG=1, existing train and saves preserved.');return
    m=json.loads((OUT/'manifest.json').read_text())
    expected=set(json.loads((OUT/'assets.json').read_text())['files'])|{'bin/'+n+'.'+e for n,e in [('Common','dll'),('Common','pdb'),('Server','dll'),('Server','pdb'),('freelancer','exe'),('freelancer','pdb')]}
    assert set(m['files'])==expected
    listing=subprocess.check_output(['tasklist','/FO','CSV','/NH']).lower()
    assert not any(b'"'+p+b'"' in listing for p in [b'freelancer.exe',b'freelancer_window.exe',b'freelancer_en.exe',b'freelancer_window_en.exe',b'flserver.exe']),'Close game before installation'
    for name,r in m['files'].items():
        assert (GAME/name).resolve().is_relative_to(GAME.resolve())
        assert sha(GAME/name)==r['original'] and sha(PAYLOAD/name)==r['installed'],name
    for name,path in m['sources'].items():assert sha(Path(path))==m['files'][name]['installed'],name
    for name,h in m['dependencies'].items():assert sha(GAME/name)==h,name
    backup=GAME/'BACKUP'/('codex_train_yard_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'));backup.mkdir(parents=True)
    for name,r in m['files'].items():
        if r['original'] is not None:
            target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/name,target);assert sha(target)==r['original']
    shutil.copy2(OUT/'manifest.json',backup/'manifest.json')
    changed=[]
    try:
        for name,r in m['files'].items():
            assert sha(GAME/name)==r['original'],'Concurrent target edit: '+name
            replace(PAYLOAD/name,GAME/name);changed.append(name);assert sha(GAME/name)==r['installed']
    except BaseException:
        for name in reversed(changed):
            if m['files'][name]['original'] is None:(GAME/name).unlink()
            else:replace(backup/name,GAME/name)
        raise
    m['backup']=str(backup);(OUT/'installed.json').write_text(json.dumps(m,indent=2))
    print('Installed and verified. Save: biz_le2_train_yard. Backup:',backup)
if __name__=='__main__':main()
