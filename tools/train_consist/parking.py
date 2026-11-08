"""Stage/install only the tested Common runtime for wagon parking or coupling."""
import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from install import ROOT, GAME, BIN, MODEL, GEN, sha, replace, idle

FILES={'bin/Common.dll','bin/Common.pdb'}
CHECKS=[ROOT/'out/train_yard/checked.json',BIN/'check.json']
PROFILES={'parking':'fixed wagon parking','coupling':'automatic coupling alignment',
          'finalization':'smooth coupling finalization at render frame rates',
          'lane':'gradual train straightening on tradelane entry'}


def validate_checks():
    for check in CHECKS:
        for name,digest in json.loads(check.read_text()).items():
            assert sha(Path(name))==digest,'Checked artifact changed: '+name
    assert sha(BIN/'Common.dll')==json.loads((BIN/'build.json').read_text())['dll']


def prepare(kind='parking'):
    assert kind in PROFILES
    out=ROOT/'out/train_consist'/kind
    validate_checks()
    yard=json.loads((ROOT/'out/train_yard/installed.json').read_text())
    build=json.loads((BIN/'build.json').read_text())
    allowed={yard['files']['bin/Common.dll']['installed'],build['baseline']}
    for path in (ROOT/'out/train_consist').glob('*/installed.json'):
        record=json.loads(path.read_text()).get('files',{}).get('bin/Common.dll')
        if record:allowed.add(record['installed'])
    assert sha(GAME/'bin/Common.dll') in allowed,'Unrecognized installed runtime'
    dependencies=['bin/freelancer.exe','bin/Server.dll','bin/Content.dll',
                  'DATA/SHIPS/shiparch.ini','DATA/SHIPS/shiparch2.ini',
                  'DATA/COCKPITS/UTILITY/ge_train_player.ini','SAVE/Accts/SinglePlayer/biz_le2_train_yard.fl']
    dependencies += [GEN+'templates/hardcoded_inis/shiparch/playerships/'+name+'.ini'
                     for name in ['ge_train_player','ge_train_yard']]
    for name in ['train_consist','train_locomotive','train_wagons']:
        for ext in ['cmp','sur']:
            path=MODEL+name+'.'+ext;dependencies.append(path)
            if name!='train_consist':assert sha(GAME/path)==yard['files'][path]['installed'],'Yard model changed'
    records={}
    for name in sorted(FILES):
        source=BIN/Path(name).name;target=out/name
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        records[name]={'original':sha(GAME/name),'installed':sha(target)}
    manifest={'files':records,'dependencies':{name:sha(GAME/name) for name in dependencies},
              'checks':{str(p):sha(p) for p in CHECKS}}
    assert all(manifest['dependencies'].values()),'Missing live dependency'
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Staged checked Common.dll/PDB; client, server, PythonLancer, strafe, models and save preserved.')


def install(apply,kind='parking'):
    assert kind in PROFILES
    out=ROOT/'out/train_consist'/kind
    validate_checks()
    m=json.loads((out/'manifest.json').read_text());records=m['files']
    assert set(records)==FILES
    for name,r in records.items():
        assert sha(GAME/name)==r['original'],'Concurrent target edit: '+name
        assert sha(out/name)==sha(BIN/Path(name).name)==r['installed'],'Staged artifact changed: '+name
    for name,h in m['dependencies'].items():assert sha(GAME/name)==h,'Dependency changed: '+name
    for name,h in m['checks'].items():assert sha(Path(name))==h,'Check record changed: '+name
    if not apply:
        print('Validated Common-only update:',PROFILES[kind]);return
    idle()
    backup=GAME/'BACKUP'/('codex_train_'+kind+'_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for name,r in records.items():
        target=backup/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/name,target)
        assert sha(target)==r['original']
    (backup/'manifest.json').write_text(json.dumps(records,indent=2))
    changed=[]
    try:
        for name,r in records.items():
            assert sha(GAME/name)==r['original'],'Concurrent target edit: '+name
            replace(out/name,GAME/name);changed.append(name)
            assert sha(GAME/name)==r['installed']
    except BaseException:
        for name in reversed(changed):replace(backup/name,GAME/name)
        raise
    for name,h in m['dependencies'].items():assert sha(GAME/name)==h,'Dependency changed: '+name
    m['backup']=str(backup);(out/'installed.json').write_text(json.dumps(m,indent=2))
    print('Installed and verified',PROFILES[kind]+'. Backup:',backup)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group()
    mode.add_argument('--coupling',action='store_true')
    mode.add_argument('--finalization',action='store_true')
    mode.add_argument('--lane',action='store_true')
    args=parser.parse_args()
    prepare('lane' if args.lane else 'finalization' if args.finalization else 'coupling' if args.coupling else 'parking')
