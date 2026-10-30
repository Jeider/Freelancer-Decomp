"""Install camera-facing ALE ribbons and leave volume beams opt-in by node name."""
import json
import re
import sys
from pathlib import Path

root=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(root/'tools/nomad_surfaces'))
import install as deployment

deployment.STAGE=root/'src/obj/beam_volume/ribbon_install'
CONFIG='bin/port.ini'
deployment.PAYLOAD=('bin/alchemy.dll','bin/alchemy.pdb','bin/RP9.dll','bin/RP9.pdb',CONFIG)
deployment.SCOPE='Single camera-facing ALE ribbon with native batching; volume beams opt-in by node name'

def prepare():
    game=Path('D:/games/FL_MOD')
    original=(game/CONFIG).read_bytes()
    newline=b'\r\n' if b'\r\n' in original else b'\n'
    sections=0
    def section(match):
        nonlocal sections
        sections+=1
        body=match[2]
        for key,value in ((b'beam_camera_facing',b'1'),(b'beam_volume_nodes',b''),(b'beam_volume',b'1')):
            # Horizontal whitespace only: never consume the next INI line.
            pattern=rb'(?im)^('+key+rb'[ \t]*=[ \t]*)[^\r\n]*'
            if re.search(pattern,body):body=re.sub(pattern,lambda m:m[1]+value,body)
            else:body=key+b' = '+value+newline+body
        return match[1]+body
    result=re.sub(rb'(?ims)(^\[Render\][^\r\n]*\r?\n)(.*?)(?=^\[|\Z)',section,original)
    assert sections==1,sections
    deployment.PAYLOAD=deployment.PAYLOAD[:-1]
    deployment.main()
    deployment.PAYLOAD+=(CONFIG,)
    target=deployment.safe(deployment.STAGE,CONFIG)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(result)
    manifest=deployment.STAGE/'manifest.json'
    data=json.loads(manifest.read_text())
    if result!=original:
        data['files'].append(dict(relative=CONFIG,original=deployment.digest(game/CONFIG),prepared=deployment.digest(target)))
    manifest.write_text(json.dumps(data,indent=2))
    print('Prepared beam_camera_facing = 1 and empty beam_volume_nodes; game unchanged.')

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    else:deployment.main()
