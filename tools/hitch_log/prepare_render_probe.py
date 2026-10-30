"""Stage client/RP9 rendering updates; no game writes or shader/config changes."""
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def main():
    stage = ROOT/'src/obj/render_hitch_install'/datetime.now().strftime('%Y%m%d_%H%M%S')
    paths = ['bin/freelancer.exe', 'bin/freelancer.pdb', 'bin/RP9.dll', 'bin/RP9.pdb']
    for rel in paths:
        (stage/rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT/rel, stage/rel)
    dependencies = ['bin/Common.dll', 'bin/DALib.dll', 'bin/dacom.dll', 'bin/alchemy.dll']
    manifest = {'game': str(GAME), 'files': [
        {'relative': rel, 'original': sha(GAME/rel), 'prepared': sha(stage/rel)} for rel in paths],
        'dependencies': [{'relative': rel, 'sha256': sha(GAME/rel)} for rel in dependencies]}
    (stage/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    shutil.copy2(ROOT/'tools/physics/install_server_asteroids.ps1', stage/'install.ps1')
    print(stage)
    print('Prepared client and RP9 rendering updates. Game unchanged.')


if __name__ == '__main__':
    main()
