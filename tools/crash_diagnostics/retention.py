"""Keep ten game crash dumps; stage exact INI edits with hash guards."""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/crash_diagnostics'
GAME=Path('D:/games/FL_MOD')
TARGETS=(ROOT/'bin/port.ini',GAME/'bin/port.ini')
def sha(data):return hashlib.sha256(data).hexdigest()

def stage():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for i,p in enumerate(TARGETS):
        before=p.read_bytes()
        after,count=re.subn(rb'(?m)^(crash_dumps_keep\s*=\s*)\d+',rb'\g<1>10',before)
        assert count==1,p
        staged=OUT/f'port_{i}.ini';staged.write_bytes(after)
        manifest.append({'path':str(p),'staged':str(staged),'before':sha(before),'after':sha(after)})
    (OUT/'retention.json').write_text(json.dumps(manifest,indent=2))
    print('Staged crash_dumps_keep = 10 for source and installed INI')

def apply():
    manifest=json.loads((OUT/'retention.json').read_text())
    assert [Path(x['path']) for x in manifest]==list(TARGETS)
    for x in manifest:
        assert sha(Path(x['path']).read_bytes())==x['before']
        assert sha(Path(x['staged']).read_bytes())==x['after']
    previous=[Path(x['path']).read_bytes() for x in manifest]
    touched=[]
    try:
        for i,x in enumerate(manifest):
            touched.append(i);shutil.copy2(x['staged'],x['path']);assert sha(Path(x['path']).read_bytes())==x['after']
    except Exception:
        for i in touched:Path(manifest[i]['path']).write_bytes(previous[i])
        raise
    print('Verified: source + installed INI retain 10 dumps. Applies on next game launch.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true')
    apply() if parser.parse_args().apply else stage()
