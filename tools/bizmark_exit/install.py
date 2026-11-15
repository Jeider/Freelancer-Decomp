import hashlib
import json
from pathlib import Path
import shutil
ROOT=Path(__file__).resolve().parent
manifest=json.loads((ROOT/'manifest.json').read_text())
for name,item in manifest.items():
    target=Path(item['target'])
    assert hashlib.sha256(target.read_bytes()).hexdigest()==item['sha256'],f'User file changed: {target}'
    compile((ROOT/name).read_bytes(),name,'exec')
for name,item in manifest.items():
    target=Path(item['target'])
    backup=target.with_name(target.name+'.before_fixed_exit.bak')
    if backup.exists():
        assert backup.read_bytes()==(ROOT/(name+'.before')).read_bytes()
    else:
        shutil.copyfile(target,backup)
    shutil.copyfile(ROOT/name,target)
    print(f'Installed {target}; backup {backup.name}')
