"""Install the checked shared-mesh lifetime fix into the running mod's bin."""
import argparse
import json
from pathlib import Path
from owners import digest, install

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
OUT = ROOT / 'out/train_courier/mesh_lifetime'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.apply:
        manifest = json.loads((OUT / 'manifest.json').read_text())
        for name, expected in manifest['sources'].items():
            assert digest(ROOT / name) == expected, 'Changed source: ' + name
        install(manifest['files'], OUT / 'payload', GAME, OUT / 'backups', True)
        return
    rows = {}
    for name in ('RendComp.dll', 'RendComp.pdb'):
        source = ROOT / 'src/obj/train_courier/rpg1/bin' / name
        target = OUT / 'payload/bin' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(source.read_bytes())
        rows['bin/' + name] = {'before': digest(GAME / 'bin' / name), 'after': digest(target)}
    sources = {name: digest(ROOT / name) for name in (
        'src/RendComp/VMeshPart.cpp', 'src/RendComp/VMeshLibrary.cpp',
        'tools/train_courier/check_mesh_lifetime.py')}
    (OUT / 'manifest.json').write_text(json.dumps({'files': rows, 'sources': sources}, indent=2))
    print('Staged RendComp.dll/PDB; --apply checks hashes, closed game and creates backups')


if __name__ == '__main__':
    main()
