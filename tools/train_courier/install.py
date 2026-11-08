"""Install a verified staged courier build into FL_MOD/bin and DATA, with backups."""
from pathlib import Path
import argparse
import datetime
import hashlib
import json
import shutil
import subprocess
from verify import main as verify
from data_output import data_folder

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/train_courier'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
def copy(source,target):
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args();verify()
    manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
    game=Path(manifest['game']).resolve();payload=OUT/'payload'
    def copy_game_file(source,root,relative):
        if relative.startswith('DATA/'):
            data_folder(game,root).sync_data_file(relative.removeprefix('DATA/'),source.read_bytes())
        else:copy(source,root/relative)
    for relative,expected in manifest.get('dependencies',{}).items():
        assert digest(game/relative)==expected,'Dependency changed after staging: '+relative
    for relative,item in manifest['files'].items():
        target=(game/relative).resolve()
        assert target.is_relative_to(game),'Unexpected manifest path'
        assert digest(target)==item['before'],'Installed file changed: '+relative
    if not args.apply:
        print(f'Ready: {len(manifest["files"])} staged files; use --apply to install.');return
    processes=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True).stdout.lower()
    assert not any(b'"'+name+b'"' in processes for name in [b'freelancer.exe',b'flserver.exe',b'freelancer_window.exe',b'freelancer_en.exe',b'freelancer_window_en.exe']), 'Close Freelancer/FLServer before installation'
    backup=OUT/'backups'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    for relative,item in manifest['files'].items():
        if item['before'] is not None:
            copy_game_file(game/relative,backup,relative)
            assert digest(backup/relative)==item['before'],'Backup verification failed'
    copy(OUT/'manifest.json',backup/'manifest.json')
    touched=[]
    try:
        for relative,item in manifest['files'].items():
            touched.append(relative);copy_game_file(payload/relative,game,relative)
            assert digest(game/relative)==item['after'],'Installed hash mismatch: '+relative
    except Exception:
        for relative in reversed(touched):
            target=(game/relative).resolve();assert target.is_relative_to(game)
            if manifest['files'][relative]['before'] is None:
                if relative.startswith('DATA/'):
                    data_folder(game,game).remove_data_file(relative.removeprefix('DATA/'))
                else:target.unlink(missing_ok=True)
            else:copy_game_file(backup/relative,game,relative)
        raise
    copy(OUT/'manifest.json',OUT/'installed.json')
    print('Installed courier build. Backups:',backup)

if __name__=='__main__':main()
