"""Stage the user's original, self-contained Beta HUD models (no behavioral patch).

The models contain their own materials and textures. Nothing is installed outside
the workspace; pass the destination explicitly when preparing a game installation.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--beta-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[2] / 'assets/hud/extra')
    args = parser.parse_args()
    base = args.beta_root / 'data/Interface/HUD'
    names = ['HUD_drasticevade.3db', 'maneuvers/HUD_turntoface.3db',
             'maneuvers/hud_mnvrstrafe.3db', 'maneuvers/hud_mnvrevade.3db']
    sources = [base / name for name in names]
    for source in sources:
        if source.read_bytes()[:4] != b'UTF ': raise ValueError(f'Not UTF: {source}')
    args.output.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for source in sources:
        target = args.output / source.name
        if target.exists() and target.read_bytes() != source.read_bytes():
            raise ValueError(f'Refusing to replace a different asset: {target}')
        shutil.copyfile(source, target)
        manifest[source.name] = hashlib.sha256(source.read_bytes()).hexdigest()
    (args.output / 'flight_sources.json').write_text(json.dumps(manifest, indent=2)+'\n')
    print(f'Staged {len(sources)} original icons in {args.output}')

if __name__ == '__main__': main()
