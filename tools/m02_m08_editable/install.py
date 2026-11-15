"""Install reviewed edits only if the live files still match the snapshot."""
import hashlib
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parent
ASSETS=Path('D:/Games/FL_MOD/Assets')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None

def prepare():
    checks=json.loads((ROOT/'check_results.json').read_text())
    blends=json.loads((ROOT/'blender_results.json').read_text())
    assert len(checks)==len(blends)==101 and all(x.get('ok') for x in checks.values())
    assert all(x['points_unchanged'] for x in blends.values())
    plan=[]
    for source in sorted((ROOT/'staged').rglob('*')):
        if not source.is_file():continue
        rel=source.relative_to(ROOT/'staged');target=ASSETS/rel;backup=ROOT/'before'/rel
        assert not target.exists() or sha(target)==sha(backup),f'Live changes: {target}'
        if sha(source)!=sha(target):plan.append({'path':rel.as_posix(),'old':sha(target),'new':sha(source)})
    (ROOT/'install_manifest.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print('Prepared',len(plan),'changed files; existing mission bindings, ready m08 scenes, DATA untouched.')

def apply():
    plan=json.loads((ROOT/'install_manifest.json').read_text())
    for e in plan:
        assert sha(ROOT/'staged'/e['path'])==e['new']
        assert sha(ASSETS/e['path']) in (e['old'],e['new']),f"Live edit: {e['path']}"
    for e in plan:
        target=ASSETS/e['path']
        if sha(target)==e['new']:continue
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes((ROOT/'staged'/e['path']).read_bytes())
        assert sha(target)==e['new']
    print('Installed and hash-verified',len(plan),'files. Backups:',ROOT/'before')

if '--prepare' in sys.argv:prepare()
elif '--apply' in sys.argv:apply()
else:raise SystemExit('Use --prepare or --apply')
