"""Install only the GPU-verified RenoDX upgrade, profile and dependency manifest."""
from pathlib import Path
import argparse
import json
import shutil
import subprocess
import install_slider as installer
from renodx_runtime import CACHED, VERSION, verify

installer.PACKAGE = installer.OUT / 'renodx_upgrade'
installer.PAYLOAD = installer.PACKAGE / 'payload'
HOST = 'neural/host64/'

def stage():
    binary = installer.OUT / 'on/bin'
    verify(CACHED)
    verify(binary / HOST / 'renodx-dlss5.addon64')
    results = json.loads((installer.OUT / 'checks/results.json').read_text())
    required = {'identity', 'neural1440', 'kill_host', 'cancel_startup', 'transport'}
    if {r['test'] for r in results if r['exit_code'] == 0} != required:
        raise RuntimeError('Run check.py --gpu first')
    verified = json.loads((installer.OUT / 'checks/binaries.json').read_text())
    for name, digest in verified.items():
        if installer.sha(binary / name) != digest:
            raise RuntimeError('GPU-tested file changed: ' + name)
    strength = json.loads((installer.OUT / 'checks/strength/verified.json').read_text())
    if strength['addon_sha256'] != installer.sha(binary / 'fl_base_neural.addon32'):
        raise RuntimeError('Strength-tested bridge changed')
    runtime = strength.get('runtime', {})
    if not all(HOST+n in runtime for n in ('ReShade.ini','renodx-dlss5.addon64',
               'nvngx_dlss.dll','nvngx_dlssnr.dll','fl_base_neural_host.exe','dxgi.dll')):
        raise RuntimeError('Run check_strength_gpu.py to verify the migrated profile')
    for name, digest in runtime.items():
        if installer.sha(binary / name) != digest:
            raise RuntimeError('Strength-tested runtime/profile changed: '+name)
    # The game must use the same bridge, host and NVIDIA runtime as the probes.
    guards = {}
    for name in ('fl_base_neural.addon32', HOST+'fl_base_neural_host.exe',
                 HOST+'dxgi.dll', HOST+'nvngx_dlss.dll', HOST+'nvngx_dlssnr.dll',
                 'D3D9.dll', 'dxgi.dll'):
        relative = 'bin/' + name
        guards[relative] = installer.sha(installer.GAME / relative)
        if guards[relative] != installer.sha(binary / name):
            raise RuntimeError('Game/test dependency mismatch: ' + name)
    for name in ('freelancer.exe', 'RP9.dll', 'Common.dll', 'Server.dll', 'Content.dll',
                 'port.ini', 'ReShade.ini'):
        guards['bin/'+name] = installer.sha(installer.GAME / 'bin' / name)
    deps = json.loads((installer.GAME / 'bin/neural/dependencies.json').read_text())
    replacements = (HOST+'renodx-dlss5.addon64', HOST+'ReShade.ini')
    for name in replacements:
        row = next(r for r in deps if r['path'] == name)
        row.update(sha256=installer.sha(binary / name),
                   source=str(CACHED if name.endswith('.addon64') else binary / name))
        if name.endswith('.addon64'):
            row['version'] = VERSION
    (binary / 'neural/dependencies.json').write_text(json.dumps(deps, indent=2))
    rows = []
    for name in (*replacements, 'neural/dependencies.json'):
        relative = 'bin/' + name
        target = installer.PAYLOAD / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(binary / name, target)
        rows.append(dict(relative=relative, before=installer.sha(installer.GAME / relative),
                         after=installer.sha(target)))
    (installer.PACKAGE / 'manifest.json').write_text(json.dumps(
        dict(files=rows, guards=guards, version=VERSION), indent=2))
    print('Prepared verified RenoDX v'+VERSION+': addon, migrated profile, manifest; NVIDIA DLLs unchanged')

def apply():
    processes = subprocess.check_output(['tasklist','/FO','CSV','/NH'],text=True,errors='replace').lower()
    for name in ('freelancer.exe','freelancer_window.exe','freelancer_en.exe',
                 'flserver.exe','fl_base_neural_host.exe','probe_wrapper.exe','probe_feed.exe'):
        if '"'+name+'"' in processes:
            raise RuntimeError('Close this process before installing: '+name)
    installer.apply()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--stage', action='store_true')
    mode.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    if args.stage: stage()
    else: apply()
