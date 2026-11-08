"""Stage the optional DX11/Feed v2 runtime; never modifies the running game."""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
REFERENCE = ROOT / 'out/base_neural/reference'
ARCHIVES = (
    ('feeder-0.7.0.zip', 'https://codeload.github.com/jlrouzies-fr/DLSS5-Feeder/zip/refs/tags/v0.7.0',
     'b1f7077e98b20d7e58e28146d96b1336159cab212f63f82066ffeceef9823814', ''),
    ('dgVoodoo2_87_6.zip', 'https://github.com/dege-diosg/dgVoodoo2/releases/download/2.87.6/dgVoodoo2_87_6.zip',
     '9afa493396feec7108f42a2d97661eef96bbaac5addf0dfb5cfbc3001cd76a0a', 'dgVoodoo'),
)

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--fetch', action='store_true')
    ap.add_argument('--reference', type=Path, default=Path('E:/games/freelancer game/FL_MOD/exe'))
    args = ap.parse_args()
    REFERENCE.mkdir(parents=True, exist_ok=True)
    for name, url, expected, subdir in ARCHIVES:
        archive = REFERENCE / name
        if not archive.exists():
            if not args.fetch:
                raise SystemExit(f'Missing {archive}; pass --fetch')
            urllib.request.urlretrieve(url, archive)
        if digest(archive) != expected:
            raise SystemExit(f'SHA256 mismatch: {archive}')
        target = (REFERENCE / subdir).resolve()
        with zipfile.ZipFile(archive) as z:
            for member in z.infolist():
                if not (target / member.filename).resolve().is_relative_to(target):
                    raise SystemExit('Archive contains an unsafe path')
            z.extractall(target)
    out = ROOT / 'out/base_neural/on/bin'
    host = out / 'neural/host64'
    host.mkdir(parents=True, exist_ok=True)
    files = {
        out / 'D3D9.dll': REFERENCE / 'dgVoodoo/MS/x86/D3D9.dll',
        out / 'dxgi.dll': args.reference / 'dxgi.dll',
    }
    for name in ['dxgi.dll', 'nvngx_dlss.dll',
                 'nvngx_dlssnr.dll', 'renodx-dlss5.addon64', 'ReShade.ini']:
        files[host / name] = args.reference / 'host64' / name
    # Previous staging used the generic extension; never load two NR add-ons.
    (host / 'renodx-dlss5.addon').unlink(missing_ok=True)
    # Check the complete source set before making a partial package.
    for source in files.values():
        if not source.is_file():
            raise SystemExit(f'Missing reference dependency: {source}')
    manifest = []
    for dest, source in files.items():
        shutil.copy2(source, dest)
        manifest.append({'path': dest.relative_to(out).as_posix(),
                         'source': str(source), 'sha256': digest(dest)})
    config = (REFERENCE / 'dgVoodoo/dgVoodoo.conf').read_text()
    config = config.replace('= bestavailable', '= d3d11_fl11_0')
    config = config.replace('dgVoodooWatermark                   = true', 'dgVoodooWatermark                   = false')
    config = config.replace('Antialiasing                        = appdriven', 'Antialiasing                        = off')
    (out / 'dgVoodoo.conf').write_text(config, encoding='utf-8')
    (out / 'neural/empty').mkdir(exist_ok=True)
    (out / 'ReShade.ini').write_text(
        '[ADDON]\nAddonPath=.\\\n\n[GENERAL]\nEffectSearchPaths=.\\neural\\empty\n'
        'TextureSearchPaths=.\\neural\\empty\nPresetPath=.\\neural\\empty\\preset.ini\n'
        'PerformanceMode=1\nSkipLoadingDisabledEffects=1\n\n[INPUT]\nKeyOverlay=0,0,0,0\n'
        'KeyScreenshot=0,0,0,0\n\n[OVERLAY]\nTutorialProgress=4\nShowFPS=0\nShowFrameTime=0\n',
        encoding='utf-8')
    notices = out / 'neural/licenses'
    notices.mkdir(exist_ok=True)
    license_file = REFERENCE / 'DLSS5-Feeder-0.7.0/LICENSE'
    if license_file.exists():
        shutil.copy2(license_file, notices / 'DLSS5-Feeder-MIT.txt')
    ngx_license=REFERENCE/'ngx/LICENSE.txt'
    if ngx_license.exists():shutil.copy2(ngx_license,notices/'NGX-LICENSE.txt')
    (out / 'neural/dependencies.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    # User-selected full-scene maximum profile; preserve it when restaging dependencies.
    from max_profile import apply_configs
    for relative,data in apply_configs(out).items():
        (out/relative).write_bytes(data)
    print(f'Staged optional runtime at {out}; game untouched')

if __name__ == '__main__':
    main()
