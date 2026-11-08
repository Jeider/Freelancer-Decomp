"""Restore player cloak behavior in live data and its Pythonlancer source."""
from pathlib import Path
import argparse
from datetime import datetime
import hashlib
import json
import re
import shutil
from prepare import configure

ROOT=Path(__file__).resolve().parents[2]
GAME=Path('D:/games/FL_MOD')
OUT=ROOT/'src/obj/cloak_config'
FILES=('DATA/EQUIPMENT/weapon_equip.ini',
       'Assets/Pythonlancer/templates/hardcoded_inis/static_content/weapon_equip.ini')
def sha(data):return hashlib.sha256(data).hexdigest()

def restore(data):
    data=configure(data)
    blocks=re.split(br'(?m)(?=^\[)',data)
    for i,b in enumerate(blocks):
        if not b.startswith(b'[CloakingDevice]'):continue
        if not re.search(br'(?m)^nickname\s*=\s*pl_cloak_(fast|slow)\s*$',b):continue
        if not re.search(br'(?m)^hp_type\s*=',b):
            nl=b'\r\n' if b'\r\n' in b else b'\n'
            at=b.index(b'\n',b.index(b'nickname'))+1
            blocks[i]=b[:at]+b'hp_type = hp_hardware_special_1'+nl+b[at:]
    return b''.join(blocks)

def stage():
    OUT.mkdir(parents=True,exist_ok=True);manifest={}
    for rel in FILES:
        before=(GAME/rel).read_bytes();after=restore(before)
        assert restore(after)==after
        path=OUT/'staged'/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(after)
        manifest[rel]={'before':sha(before),'after':sha(after)}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print('Staged live data + Pythonlancer template: visible default, 30s duration, 20s recharge, 0.3s toggle interval; restored hardware class')

def apply():
    manifest=json.loads((OUT/'manifest.json').read_text());assert tuple(manifest)==FILES
    for rel,item in manifest.items():
        assert sha((GAME/rel).read_bytes())==item['before'],rel+' changed'
        assert sha((OUT/'staged'/rel).read_bytes())==item['after']
    backup=OUT/('backup_'+datetime.now().strftime('%Y%m%d_%H%M%S'))
    for rel in FILES:
        p=backup/rel;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(GAME/rel,p)
    touched=[]
    try:
        for rel,item in manifest.items():
            touched.append(rel);shutil.copy2(OUT/'staged'/rel,GAME/rel)
            assert sha((GAME/rel).read_bytes())==item['after']
    except Exception:
        for rel in touched:shutil.copy2(backup/rel,GAME/rel)
        raise
    print('Installed and hash-verified live configuration and Pythonlancer source. Backup:',backup)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true')
    apply() if p.parse_args().apply else stage()
