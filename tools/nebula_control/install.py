"""Install native per-nebula volumetric control and disable it in active Sphere INI."""
import json
import re
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/nomad_surfaces'))
import install as deployment

deployment.STAGE=root/'src/obj/nebula_control/install'
SYSTEM='DATA/UNIVERSE/SPECIAL/SPHERE/sphere.ini'
deployment.PAYLOAD=('bin/freelancer.exe','bin/freelancer.pdb',SYSTEM)
deployment.SCOPE='System [Nebula] volumetric flag; disabled in Sphere; skip volume in authored exclusion zones'

def prepare():
    game=Path('D:/games/FL_MOD')
    original=(game/SYSTEM).read_bytes()
    count=0
    def section(m):
        nonlocal count
        body=m[2]
        if not re.search(rb'(?im)^file\s*=\s*solar\\nebula_mod\\sphere_nebula.ini\s*$',body):
            raise ValueError('Unexpected Sphere nebula; review config before staging')
        count+=1
        key=rb'(?im)^(volumetric\s*=\s*)[^\r\n]*'
        if re.search(key,body):body=re.sub(key,rb'\g<1>false',body)
        else:body=b'volumetric = false'+(b'\r\n' if b'\r\n' in original else b'\n')+body
        return m[1]+body
    result=re.sub(rb'(?ims)(^\[Nebula\][^\r\n]*\r?\n)(.*?)(?=^\[|\Z)',section,original)
    assert count==1,count
    deployment.PAYLOAD=deployment.PAYLOAD[:-1];deployment.main()
    deployment.PAYLOAD+= (SYSTEM,)
    target=deployment.safe(deployment.STAGE,SYSTEM);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(result)
    manifest=deployment.STAGE/'manifest.json';data=json.loads(manifest.read_text())
    if result!=original:data['files'].append(dict(relative=SYSTEM,original=deployment.digest(game/SYSTEM),prepared=deployment.digest(target)))
    manifest.write_text(json.dumps(data,indent=2))
    print('Prepared Sphere [Nebula] volumetric = false; no volumetric.ini overrides changed.')

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    else:deployment.main()
