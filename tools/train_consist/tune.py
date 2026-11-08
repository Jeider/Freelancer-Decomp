"""Stage/verify train runtime tuning and persistent camera/LOD; preserve saves."""
import json
from pathlib import Path
from datetime import datetime
import shutil
from player import ROOT,GAME,GEN,PLAYER,PLAYER_TEMPLATE,NPC_MODEL,CAMERA_OFFSET,LOD_RANGES,section,value,set_value,sha

OUT=ROOT/'out/train_consist/tune'
BIN=ROOT/'src/obj/train_consist'
CONFIGS=[GEN+'templates/'+PLAYER_TEMPLATE,'DATA/SHIPS/shiparch.ini','DATA/SHIPS/shiparch2.ini']
FILES=set(CONFIGS+['bin/Common.dll','bin/Common.pdb'])


def adjust(text):
    a,b,ship=section(text,'Ship',PLAYER)
    ship=set_value(ship,'camera_offset',CAMERA_OFFSET)
    ship=set_value(ship,'LODranges',LOD_RANGES)
    return text[:a]+ship+text[b:]


def prepare():
    OUT.mkdir(parents=True,exist_ok=True)
    native=json.loads((BIN/'check.json').read_text())
    for p,digest in native.items():assert sha(Path(p).read_bytes())==digest,'Native checked input changed: '+p
    previous=json.loads((ROOT/'out/train_consist/player20/installed.json').read_text())
    # Subsequent tuning starts from the last installed tuning, including its
    # checked runtime, while retaining the 20-wagon model dependency records.
    if (OUT/'installed.json').exists():
        previous['files'].update(json.loads((OUT/'installed.json').read_text())['files'])
    dependencies={n:r['installed'] for n,r in previous['files'].items()
                  if n.startswith('bin/') or n.endswith(('.cmp','.sur'))}
    build=json.loads((BIN/'build.json').read_text())
    assert sha((BIN/'Common.dll').read_bytes())==build['dll'],'Runtime differs from recorded build'
    current_dll=sha((GAME/'bin/Common.dll').read_bytes())
    if current_dll!=dependencies['bin/Common.dll']:
        # Another workspace build may have been installed while testing. Accept
        # it only when it is exactly the baseline this tested DLL was built on.
        assert current_dll==build['baseline']==sha((ROOT/'bin/Common.dll').read_bytes()),'Unrecognized concurrent runtime'
        current_pdb=sha((GAME/'bin/Common.pdb').read_bytes())
        assert current_pdb in [dependencies['bin/Common.pdb'],sha((ROOT/'bin/Common.pdb').read_bytes())],'Unrecognized concurrent symbols'
        dependencies['bin/Common.dll']=current_dll
        dependencies['bin/Common.pdb']=current_pdb
        print('PASS: concurrently installed runtime matches the tested build baseline exactly.')
    dependencies.update({GEN+'templates/'+n:sha((GAME/GEN/'templates'/n).read_bytes()) for n in
                         ['hardcoded_inis/static_content/shiparch.ini','hardcoded_inis/shiparch/shiparch2.ini']})
    for n,digest in dependencies.items():assert sha((GAME/n).read_bytes())==digest,'Installed dependency changed: '+n
    payload={n:adjust((GAME/n).read_bytes().decode('utf-8')).encode('utf-8') for n in CONFIGS}
    payload.update({'bin/'+n:(BIN/n).read_bytes() for n in ['Common.dll','Common.pdb']})
    records={}
    for n,raw in payload.items():
        p=OUT/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
        records[n]={'original':sha((GAME/n).read_bytes()),'installed':sha(raw)}
    manifest={'files':records,'dependencies':dependencies,'camera_offset':CAMERA_OFFSET,'lodranges':LOD_RANGES,'baseline':build['baseline']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    # Execute both actual generators with staged source precedence and no writes.
    import check_player as check
    check.OUT=OUT
    for manager in [check.ShiparchManager,check.ShiparchManagerV2]:
        before=check.generate(manager,False);after=check.generate(manager,True)
        assert after==adjust(before),'Generator changed unrelated content'
        assert value(section(after,'Ship','ge_train')[2],'DA_archetype')==NPC_MODEL
    for n in CONFIGS:
        before=(GAME/n).read_text(encoding='utf-8');after=(OUT/n).read_text(encoding='utf-8')
        assert after==adjust(before)
        ship=section(after,'Ship',PLAYER)[2]
        assert value(ship,'camera_offset')==CAMERA_OFFSET and value(ship,'LODranges')==LOD_RANGES
    (OUT/'checked.json').write_text(json.dumps({'manifest':sha((OUT/'manifest.json').read_bytes()),
        'files':{n:r['installed'] for n,r in records.items()}},indent=2))
    print('PASS: both live generators preserve NPCs; only player camera/LOD and tested runtime staged.')
    print('camera_offset =',CAMERA_OFFSET,'; LODranges =',LOD_RANGES)


def install(apply):
    from install import replace,idle,sha as file_sha
    m=json.loads((OUT/'manifest.json').read_text());checked=json.loads((OUT/'checked.json').read_text())
    assert sha((OUT/'manifest.json').read_bytes())==checked['manifest']
    records=m['files'];assert set(records)==set(checked['files'])==FILES
    for n,r in records.items():
        assert file_sha(GAME/n)==r['original'],'Concurrent target change: '+n
        assert file_sha(OUT/n)==r['installed']==checked['files'][n],'Staged artifact changed: '+n
    for n,digest in m['dependencies'].items():assert file_sha(GAME/n)==digest,'Dependency changed: '+n
    native=json.loads((BIN/'check.json').read_text())
    for n,digest in native.items():assert file_sha(Path(n))==digest,'Checked native input changed'
    assert file_sha(OUT/'bin/Common.dll')==file_sha(BIN/'Common.dll')
    assert file_sha(OUT/'bin/Common.pdb')==file_sha(BIN/'Common.pdb')
    print('Validated update:',', '.join(records))
    if not apply:return
    idle()
    backup=GAME/'BACKUP'/('codex_train_tune_'+datetime.now().strftime('%Y%m%d_%H%M%S_%f'))
    for n,r in records.items():
        p=backup/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/n,p)
        assert file_sha(p)==r['original']
    (backup/'manifest.json').write_text(json.dumps(records,indent=2))
    changed=[]
    try:
        for n,r in records.items():
            assert file_sha(GAME/n)==r['original'],'Concurrent target change: '+n
            replace(OUT/n,GAME/n);changed.append(n)
            assert file_sha(GAME/n)==r['installed']
    except BaseException:
        for n in reversed(changed):replace(backup/n,GAME/n)
        raise
    (OUT/'installed.json').write_text(json.dumps({'backup':str(backup),'files':records},indent=2))
    print('Installed. Backup:',backup)


if __name__=='__main__':prepare()
