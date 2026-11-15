"""Stage/install the tested nose-contact Common.dll without replacing other modules."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

root = Path(__file__).resolve().parents[2]
source = root/'src/obj/train_consist/Common.dll'
target = Path('D:/Games/FL_MOD/bin/Common.dll')
package = root/'out/train_nose'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    package.mkdir(parents=True, exist_ok=True)
    manifest = package/'install.json'
    if not args.apply:
        for report in (root/'out/train_yard/checked.json', root/'src/obj/train_consist/check.json'):
            checks = json.loads(report.read_text())
            assert checks[str(source)] == digest(source), 'Tests do not cover this build'
            for name, expected in checks.items():
                assert digest(Path(name)) == expected, 'Test input changed: '+name
        shutil.copy2(source, package/'Common.dll')
        manifest.write_text(json.dumps({'before':digest(target),'after':digest(source)}, indent=2))
        print(manifest.read_text())
        return
    processes = subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+name+b'"' in processes for name in (b'freelancer.exe',b'flserver.exe',b'freelancer_window.exe')), 'Close game/server first'
    record=json.loads(manifest.read_text())
    assert digest(target)==record['before'] and digest(package/'Common.dll')==record['after'], 'Files changed since staging'
    backup=package/'backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    shutil.copy2(target,backup/'Common.dll')
    try:
        shutil.copy2(package/'Common.dll',target)
        assert digest(target)==record['after'], 'Installed hash mismatch'
    except Exception:
        shutil.copy2(backup/'Common.dll',target)
        raise
    print('Installed',target,'; backup:',backup)

if __name__=='__main__':
    main()
