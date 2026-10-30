"""Install source-nebula shadow permission, disabled for Sphere."""
import json
import re
import sys
from pathlib import Path
root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/nomad_surfaces'))
import install as deployment

deployment.STAGE=root/'src/obj/nebula_control/shadows_install'
NEBULA='DATA/SOLAR/NEBULA_MOD/sphere_nebula.ini'
deployment.PAYLOAD=('bin/freelancer.exe','bin/freelancer.pdb',NEBULA)
deployment.SCOPE='NebulaLight shadows permission; Sphere skips local shadow caster collection, map rendering and shadow receivers'

def prepare():
    game=Path('D:/games/FL_MOD');original=(game/NEBULA).read_bytes();count=0
    def section(m):
        nonlocal count
        count+=1;body=m[2];key=rb'(?im)^(shadows\s*=\s*)[^\r\n]*'
        if re.search(key,body):body=re.sub(key,rb'\g<1>false',body)
        else:body=b'shadows = false'+(b'\r\n' if b'\r\n' in original else b'\n')+body
        return m[1]+body
    result=re.sub(rb'(?ims)(^\[NebulaLight\][^\r\n]*\r?\n)(.*?)(?=^\[|\Z)',section,original)
    assert count==1,count
    deployment.PAYLOAD=deployment.PAYLOAD[:-1];deployment.main();deployment.PAYLOAD+=(NEBULA,)
    target=deployment.safe(deployment.STAGE,NEBULA);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(result)
    manifest=deployment.STAGE/'manifest.json';data=json.loads(manifest.read_text())
    if result!=original:data['files'].append(dict(relative=NEBULA,original=deployment.digest(game/NEBULA),prepared=deployment.digest(target)))
    manifest.write_text(json.dumps(data,indent=2))
    print('Prepared sphere_nebula.ini [NebulaLight] shadows = false; no overrides changed.')

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    else:deployment.main()
