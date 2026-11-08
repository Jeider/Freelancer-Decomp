"""Stage/install the optional base NR runtime into FL_MOD/bin, with verified rollback."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import re
import shutil
import subprocess

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/base_neural'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None

def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(source,target)

def path_under(root,relative):
    path=(root/relative).resolve()
    if not path.is_relative_to(root.resolve()):raise RuntimeError('Unexpected manifest path')
    return path

def stopped():
    names=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    if any(b'"'+n+b'"' in names for n in [b'freelancer.exe',b'freelancer_window.exe',b'freelancer_en.exe',b'flserver.exe']):
        raise RuntimeError('Close Freelancer/FLServer before installing or restoring binaries')

def stage(game):
    binary=OUT/'on/bin'
    names=['freelancer.exe','RP9.dll','fl_base_neural.addon32','D3D9.dll','dxgi.dll','dgVoodoo.conf','ReShade.ini',
           'neural/host64/fl_base_neural_host.exe','neural/host64/dxgi.dll','neural/host64/nvngx_dlss.dll',
           'neural/host64/nvngx_dlssnr.dll','neural/host64/renodx-dlss5.addon64','neural/host64/ReShade.ini',
           'neural/licenses/DLSS5-Feeder-MIT.txt','neural/licenses/NGX-LICENSE.txt','neural/dependencies.json']
    for name in names:
        if not (binary/name).is_file():raise RuntimeError(f'Missing staged dependency: {name}')
    # Only verified binaries may enter the install package.
    results=json.loads((OUT/'checks/results.json').read_text())
    required={'identity','neural1440','kill_host','cancel_startup','transport'}
    if {r['test'] for r in results if r['exit_code']==0}!=required:raise RuntimeError('Run check.py --gpu first')
    verified=json.loads((OUT/'checks/binaries.json').read_text())
    for name,expected in verified.items():
        if digest(binary/name)!=expected:raise RuntimeError(f'Binary changed after GPU tests: {name}')
    payload=OUT/'package'
    files={}
    for name in names:
        relative='bin/'+name
        copy(binary/name,payload/relative)
        files[relative]={'before':digest(game/relative),'after':digest(payload/relative)}
    original=(game/'bin/port.ini').read_bytes()
    config=re.sub(rb'(?ims)^\[BaseNeural\][^\r\n]*\r?\n.*?(?=^\[|\Z)',b'',original).rstrip()+b'\r\n\r\n'
    config+=b'[BaseNeural]\r\nenabled=0\r\nmode=2\r\nresult_deadline_ms=250\r\nblend_strength=1\r\nsupersample_scale=1.0\r\n'
    (payload/'bin/port.ini').write_bytes(config)
    files['bin/port.ini']={'before':digest(game/'bin/port.ini'),'after':digest(payload/'bin/port.ini')}
    deps={p.relative_to(game).as_posix():digest(p) for p in (game/'bin').glob('*.dll') if p.name.lower()!='rp9.dll'}
    for name in ('freelancer.ini','dacom.ini'):
        p=game/'bin'/name
        if p.is_file():deps['bin/'+name]=digest(p)
    manifest={'game':str(game),'files':files,'dependencies':deps}
    (OUT/'package.json').write_text(json.dumps(manifest,indent=2))
    return manifest

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--game',type=Path,default=Path('D:/Games/FL_MOD'))
    ap.add_argument('--stage',action='store_true')
    ap.add_argument('--apply',action='store_true')
    ap.add_argument('--restore',type=Path,help='Backup directory printed by --apply')
    args=ap.parse_args()
    if args.restore:
        backup=args.restore.resolve()
        if not backup.is_relative_to((OUT/'backups').resolve()):raise RuntimeError('Backup must be under out/base_neural/backups')
        manifest=json.loads((backup/'manifest.json').read_text())
        game=Path(manifest['game']).resolve()
        changed_configs=[]
        for name,item in manifest['files'].items():
            if digest(path_under(game,name))!=item['after']:
                if Path(name).suffix.lower() in ('.ini','.conf'):changed_configs.append(name)
                else:raise RuntimeError('File changed since installation: '+name)
            if item['before'] and digest(path_under(backup,name))!=item['before']:raise RuntimeError('Backup hash mismatch: '+name)
        if not args.apply:print('Rollback verified; add --apply to restore');return
        stopped()
        for name in changed_configs:
            current=path_under(game,name)
            if current.is_file():copy(current,path_under(backup/'runtime_config',name))
        for name,item in manifest['files'].items():
            target=path_under(game,name)
            if item['before']:copy(path_under(backup,name),target)
            else:target.unlink(missing_ok=True)
        print('Restored original binaries, wrappers and configuration');return
    manifest=stage(args.game.resolve()) if args.stage else json.loads((OUT/'package.json').read_text())
    game=Path(manifest['game']).resolve()
    for name,expected in manifest['dependencies'].items():
        if digest(path_under(game,name))!=expected:raise RuntimeError('Game dependency changed after staging: '+name)
    for name,item in manifest['files'].items():
        if digest(path_under(game,name))!=item['before']:raise RuntimeError('Game file changed after staging: '+name)
        if digest(path_under(OUT/'package',name))!=item['after']:raise RuntimeError('Package hash mismatch: '+name)
    if not args.apply:print(f'Ready: {len(manifest["files"])} files for {game}/bin; no game files changed');return
    stopped()
    backup=OUT/'backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    for name,item in manifest['files'].items():
        if item['before']:
            copy(path_under(game,name),path_under(backup,name))
            if digest(path_under(backup,name))!=item['before']:raise RuntimeError('Backup verification failed')
    (backup/'manifest.json').write_text(json.dumps(manifest,indent=2))
    touched=[]
    try:
        for name,item in manifest['files'].items():
            touched.append(name)
            copy(path_under(OUT/'package',name),path_under(game,name))
            if digest(path_under(game,name))!=item['after']:raise RuntimeError('Installed hash mismatch')
        (game/'bin/neural/empty').mkdir(parents=True,exist_ok=True)
    except Exception:
        for name in reversed(touched):
            target=path_under(game,name)
            if manifest['files'][name]['before']:copy(path_under(backup,name),target)
            else:target.unlink(missing_ok=True)
        raise
    print('Installed into',game/'bin','; rollback:',backup)

if __name__=='__main__':main()
