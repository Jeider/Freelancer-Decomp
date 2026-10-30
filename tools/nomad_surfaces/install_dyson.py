"""Install single-layer Dyson bump and its own direct Render settings."""
import json
import re
import sys
from pathlib import Path
import install as deployment

deployment.STAGE=deployment.REPO/'src/obj/dyson_bump/install'
CONFIG='bin/port.ini'
deployment.PAYLOAD=('bin/RP9.dll','bin/RP9.pdb','bin/Shading.dll','bin/Shading.pdb',
                    'DATA_EXTRA/SHADERS/surface_material.hlsl',CONFIG)
deployment.SCOPE='Single-layer Dyson brick bump: dyson_shader=1, dyson_relief=1; BEAST and Lair keep their own profiles/settings'

def prepare():
    game=Path('D:/games/FL_MOD');original=(game/CONFIG).read_bytes()
    newline=b'\r\n' if b'\r\n' in original else b'\n'
    count=0
    def section(match):
        nonlocal count
        count+=1;body=match[2]
        for key,value in ((b'dyson_shader',b'1'),(b'dyson_relief',b'1.0')):
            pattern=rb'(?im)^('+key+rb'[ \t]*=[ \t]*)[^\r\n;]*'
            if re.search(pattern,body):body=re.sub(pattern,lambda m:m[1]+value+b' ',body)
            else:body=key+b' = '+value+newline+body
        return match[1]+body
    result=re.sub(rb'(?ims)(^\[Render\][^\r\n]*\r?\n)(.*?)(?=^\[|\Z)',section,original)
    assert count==1,count
    deployment.PAYLOAD=deployment.PAYLOAD[:-1];deployment.main();deployment.PAYLOAD+=(CONFIG,)
    target=deployment.safe(deployment.STAGE,CONFIG);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(result)
    manifest=deployment.STAGE/'manifest.json';data=json.loads(manifest.read_text())
    if result!=original:data['files'].append(dict(relative=CONFIG,original=deployment.digest(game/CONFIG),prepared=deployment.digest(target)))
    manifest.write_text(json.dumps(data,indent=2))
    print('Prepared direct [Render] Dyson controls; other settings unchanged.')

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    else:deployment.main()
