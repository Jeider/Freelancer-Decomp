"""Stage the built binaries and independent filter icons; never modify game data."""
from pathlib import Path
from datetime import datetime
import hashlib
import json
import shutil
import argparse

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().upper() if path.exists() else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--ui-only', action='store_true', help='Install only client and Keys icon')
    parser.add_argument('--boosters-only', action='store_true', help='Install only client and Boosters/RepairDroid icon')
    parser.add_argument('--client-only', action='store_true', help='Install only client binaries')
    parser.add_argument('--keys-asset-only', action='store_true', help='Install only the editable Keys icon')
    args = parser.parse_args()
    ui_only = args.ui_only or args.boosters_only or args.client_only or args.keys_asset_only
    stage = ROOT/'src/obj/inventory_categories_install'/datetime.now().strftime('%Y%m%d_%H%M%S')
    stage.mkdir(parents=True)
    entries = []
    binaries = () if args.keys_asset_only else ('freelancer.exe', 'freelancer.pdb') if ui_only else (
        'Common.dll', 'Common.pdb', 'Content.dll', 'Content.pdb', 'freelancer.exe', 'freelancer.pdb')
    sources = {f'bin/{name}': ROOT/'bin'/name for name in binaries}
    for name in (() if args.client_only else ('boosters.3db',) if args.boosters_only else ('keys.3db',) if args.ui_only or args.keys_asset_only else ('boosters.3db', 'keys.3db')):
        sources['DATA/INTERFACE/NEURONET/INVENTORY/'+name] = ROOT/'assets/inventory_categories'/name
    for relative, source in sources.items():
        target = stage/relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        entries.append(dict(relative=relative, original=digest(GAME/relative), prepared=digest(target)))
    (stage/'manifest.json').write_text(json.dumps(dict(game=str(GAME), files=entries), indent=2)+'\n')
    installer = Path(__file__).with_name('install.ps1').read_text()
    if ui_only:
        installer = installer.replace('$manifest.files.Count -ne 8', f'$manifest.files.Count -ne {len(sources)}')
        installer = installer.replace('Unique).Count -ne 8', f'Unique).Count -ne {len(sources)}')
        installer = installer.replace('all 8 SHA256', f'all {len(sources)} SHA256')
        lines = installer.splitlines()
        lines = ["$allowed=@(" + ','.join("'" + p + "'" for p in sources) + ')' if line.startswith('$allowed=') else line for line in lines]
        installer = '\n'.join(lines) + '\n'
    (stage/'install.ps1').write_text(installer)
    print(stage/'install.ps1')


if __name__ == '__main__':
    main()
