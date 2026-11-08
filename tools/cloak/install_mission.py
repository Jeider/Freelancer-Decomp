"""Install verified mission cloak conditions, preserving other installed modules."""
import argparse
import json
from pathlib import Path
import shutil
import install_visual as installer
from build_mission import ROOT,OUT,digest

installer.OUT=OUT
installer.PAYLOAD=('bin/Server.dll','bin/Server.pdb','bin/Content.dll','bin/Content.pdb')

def stage():
    build=json.loads((OUT/'build.json').read_text())
    assert all(digest(ROOT/p)==h for p,h in build['sources'].items()),'Source changed since build'
    for name,record in build['modules'].items():
        assert digest(installer.GAME/'bin'/(name+'.dll'))==record['before'],'Installed '+name+' changed'
        assert digest(OUT/(name+'.dll'))==record['after'],'Built '+name+' changed'
    manifest={}
    for rel in installer.PAYLOAD:
        target=OUT/'staged'/rel;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(OUT/Path(rel).name,target)
        manifest[rel]={'before':installer.current(installer.GAME/rel),'after':digest(target)}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Staged Server/Content and matching symbols; baseline/source hashes verified')

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    if parser.parse_args().apply:
        installer.apply()
        print('Installed Cnd_CloakState and Cnd_ActCloak')
    else:stage()
