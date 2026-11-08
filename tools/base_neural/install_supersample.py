"""Install the tested base-only 1.5x scene supersampling package."""
from pathlib import Path
import argparse
import json
import shutil
import install_slider as installer
from max_profile import update

installer.PACKAGE=installer.OUT/'supersample'
installer.PAYLOAD=installer.PACKAGE/'payload'

def stage():
    verified=json.loads((installer.OUT/'checks/supersample/verified.json').read_text())
    rows=[]
    for name,digest in verified.items():
        source=installer.OUT/'on/bin'/name
        assert installer.sha(source)==digest,'Supersampling-tested binary changed: '+name
        relative='bin/'+name;target=installer.PAYLOAD/relative
        target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
        rows.append({'relative':relative,'before':installer.sha(installer.GAME/relative),'after':digest})
    relative='bin/port.ini';source=installer.GAME/relative;target=installer.PAYLOAD/relative
    target.write_bytes(update(source.read_bytes(),'BaseNeural',{'supersample_scale':'1.5'}))
    rows.append({'relative':relative,'before':installer.sha(source),'after':installer.sha(target)})
    guards={name:installer.sha(installer.GAME/name) for name in (
        'bin/Common.dll','bin/Server.dll','bin/Content.dll','bin/ReShade.ini','bin/neural/host64/ReShade.ini')}
    (installer.PACKAGE/'manifest.json').write_text(json.dumps({'files':rows,'guards':guards},indent=2))
    print('Prepared base-only 1.5x supersampling: client, matching RP9 v2, adapter and port.ini; backup/hash guards enabled')

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);mode=ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stage',action='store_true');mode.add_argument('--apply',action='store_true');args=ap.parse_args()
    if args.stage:stage()
    else:installer.apply()
