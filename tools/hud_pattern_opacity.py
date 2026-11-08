"""Match Healing/Targeting background opacity to the installed retail HUD panels."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import struct
from repair_panel_normals import leaves

ROOT=Path(__file__).resolve().parents[1]
GAME=Path('D:/games/FL_MOD')
REL='DATA/INTERFACE/HUD/hud_target2.cmp'
OUT=ROOT/'src/obj/hud_pattern_opacity'

def digest(data):return hashlib.sha256(data).hexdigest()

def opacity(data):
    payload,entries=leaves(data)
    patterns=[p.rsplit('/',1)[0] for p,_,b in entries if p.endswith('/Dt_name') and b.rstrip(b'\0').lower()==b'backgroundpattern.tga']
    assert len(patterns)==1
    matches=[(at,b) for p,at,b in entries if p==patterns[0]+'/Oc']
    assert len(matches)==1 and len(matches[0][1])==4
    at,b=matches[0]
    return payload+struct.unpack_from('<I',data,at+16)[0],b

def stage():
    reference=[opacity((GAME/'DATA/INTERFACE/HUD'/n).read_bytes())[1] for n in ('HUD_target.cmp','HUD_shipinfo.cmp')]
    assert reference[0]==reference[1] and abs(struct.unpack('<f',reference[0])[0]-.4)<1e-6
    before=(GAME/REL).read_bytes();offset,old=opacity(before)
    after=before[:offset]+reference[0]+before[offset+4:]
    assert opacity(after)[1]==reference[0]
    assert len(before)==len(after) and before[:offset]==after[:offset] and before[offset+4:]==after[offset+4:]
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'hud_target2.cmp').write_bytes(after)
    (OUT/'manifest.json').write_text(json.dumps({'file':REL,'offset':offset,'before':digest(before),'after':digest(after),
        'old_oc':struct.unpack('<f',old)[0],'new_oc':struct.unpack('<f',reference[0])[0]},indent=2))
    print('Staged hud_target2.cmp: only the four-byte Oc field changes; matches HUD_target and HUD_shipinfo exactly')

def apply():
    record=json.loads((OUT/'manifest.json').read_text());assert record['file']==REL
    target=GAME/REL;staged=OUT/'hud_target2.cmp'
    assert digest(target.read_bytes())==record['before'],'Installed asset changed'
    assert digest(staged.read_bytes())==record['after'],'Staged asset changed'
    backup=OUT/('backup_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    backup.mkdir();shutil.copy2(target,backup/'hud_target2.cmp')
    assert digest((backup/'hud_target2.cmp').read_bytes())==record['before']
    try:
        shutil.copy2(staged,target)
        assert digest(target.read_bytes())==record['after']
    except Exception:
        shutil.copy2(backup/'hud_target2.cmp',target)
        raise
    print('Installed: Healing/Targeting background Oc = 0.4. Backup:',backup)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--apply',action='store_true')
    apply() if parser.parse_args().apply else stage()
