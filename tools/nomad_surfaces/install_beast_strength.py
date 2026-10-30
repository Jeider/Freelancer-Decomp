"""Set BEAST (or --dyson) bump strength to its maximum, with verified backup/restore."""
import json
import re
import sys
from pathlib import Path
import install as deployment

family='dyson' if '--dyson' in sys.argv else 'beast'
if '--dyson' in sys.argv:sys.argv.remove('--dyson')
key=(family+'_relief').encode('ascii')
deployment.STAGE=deployment.REPO/f'src/obj/{family}_relief/max_strength_install'
CONFIG='bin/port.ini'
deployment.PAYLOAD=(CONFIG,)
deployment.SCOPE=f'{family.upper()} maximum supported bump strength: [Render] {family}_relief = 2.0; shader and geometry unchanged'
# A runtime strength constant does not invalidate shader bytecode or its cache.
deployment.warm_game=lambda game:None

def prepare():
    game=Path('D:/games/FL_MOD')
    original=(game/CONFIG).read_bytes()
    newline=b'\r\n' if b'\r\n' in original else b'\n'
    count=0
    def section(match):
        nonlocal count
        count+=1
        body=match[2]
        pattern=rb'(?im)^('+key+rb'[ \t]*=[ \t]*)[^\r\n;]*'
        if re.search(pattern,body):
            body=re.sub(pattern,lambda m:m[1]+b'2.0 ',body)
        else:
            body=key+b' = 2.0'+newline+body
        return match[1]+body
    result=re.sub(rb'(?ims)(^\[Render\][^\r\n]*\r?\n)(.*?)(?=^\[|\Z)',section,original)
    assert count==1,count
    target=deployment.safe(deployment.STAGE,CONFIG)
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(result)
    items=[]
    if result!=original:
        items.append(dict(relative=CONFIG,original=deployment.digest(game/CONFIG),prepared=deployment.digest(target)))
    (deployment.STAGE/'manifest.json').write_text(json.dumps(dict(game=str(game.resolve()),files=items,scope=deployment.SCOPE),indent=2))
    print(f'Prepared [Render] {family}_relief = 2.0; game untouched.')

if __name__=='__main__':
    if len(sys.argv)==1:prepare()
    else:deployment.main()
