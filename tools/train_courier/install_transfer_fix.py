"""Install only client + Content transfer fixes; never start the game or write DATA."""
import argparse
import json
import os
from pathlib import Path
import shutil
import install_evacuation as evacuation
from stage_evacuation import ROOT, GAME, OUT, digest

PACKAGE = OUT/'transfer_fix'
MANIFEST = OUT/'transfer_fix.json'
SOURCES = {name: evacuation.SOURCES[name] for name in
           ('freelancer.exe', 'freelancer.pdb', 'Content.dll', 'Content.pdb')}
CODE = evacuation.CODE + ['src/Content/DockQueues.h',
                          'tools/train_courier/check_transfer_controls.py',
                          'tools/train_courier/check_transfer_queue.py',
                          'tools/train_courier/install_transfer_fix.py']


def stage():
    # Server/Common remain exactly the installed versions; validate the new
    # images against them as well as every other installed import dependency.
    for name in ('Server.dll', 'Content.dll', 'freelancer.exe'):
        evacuation.SOURCES[name] = SOURCES.get(name, GAME/'bin'/name)
    evacuation.verify_imports()
    PACKAGE.mkdir(parents=True, exist_ok=True)
    files = {}
    for name, source in SOURCES.items():
        target = PACKAGE/name
        shutil.copy2(source, target)
        files[name] = {'before': digest(GAME/'bin'/name), 'after': digest(target)}
    manifest = {'files': files, 'sources': {name: digest(ROOT/name) for name in CODE},
                'dependencies': {p.name: digest(p) for p in (GAME/'bin').glob('*.dll')
                                 if p.name not in SOURCES},
                'checks': ['check_transfer_controls', 'check_evacuation', 'check_transfer_binding',
                           'check_transfer_docking', 'check_transfer_queue'], 'game_launched': False}
    if 'freelancer.exe' not in SOURCES:
        manifest['dependencies']['freelancer.exe'] = digest(GAME/'bin/freelancer.exe')
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Ready:', ', '.join(files), '; no DATA changes')


def clean(backup):
    suffixes = {'.obj', '.pch', '.pdb', '.dll', '.exe', '.lib', '.exp', '.res',
                '.ilk', '.idb', '.iobj', '.ipdb'}
    paths = []
    folders = [OUT/'runtime', OUT/'imports', OUT/'checks', PACKAGE, backup,
               ROOT/'src/obj/train_courier/rpg1/Content', ROOT/'src/obj/train_courier/order_state']
    for folder in folders:
        if not folder.exists():
            continue
        evacuation.safe_file(folder, ROOT)
        for current, dirs, files in os.walk(folder, followlinks=False):
            for name in dirs:
                evacuation.safe_file(Path(current)/name, folder)
            for name in files:
                path = Path(current)/name
                if folder == backup or path.suffix.lower() in suffixes:
                    paths.append(path)
    binary = ROOT/'src/obj/train_courier/rpg1/bin'
    paths += [binary/name for name in ('Content.dll', 'Content.pdb', 'Content.lib', 'Content.exp', 'Common.lib')]
    paths += [ROOT/'out/train_space_transfer/check'/(stem+ext)
              for stem in ('binding', 'docking') for ext in ('.obj', '.exe')]
    guards = {evacuation.safe_file(p, ROOT): digest(p) for p in paths if p.exists()}
    for path, expected in guards.items():
        evacuation.safe_file(path, ROOT)
        assert digest(path) == expected, 'Cleanup input changed: '+str(path)
        path.unlink()
    print('Cleaned', len(guards), 'verified task build/staging/rollback files')


def apply():
    evacuation.idle()
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    assert shutil.disk_usage(GAME).free > 1024**3
    for name, expected in manifest['sources'].items():
        assert digest(ROOT/name) == expected, 'Source changed: '+name
    for name, expected in manifest['dependencies'].items():
        assert digest(GAME/'bin'/name) == expected, 'Dependency changed: '+name
    backup = OUT/'transfer_fix_backup'
    backup.mkdir(parents=True, exist_ok=True)
    for name, record in manifest['files'].items():
        for path, root in ((GAME/'bin'/name, GAME), (PACKAGE/name, PACKAGE), (backup/name, ROOT)):
            evacuation.safe_file(path, root)
        assert digest(GAME/'bin'/name) == record['before'], 'Live file changed: '+name
        assert digest(PACKAGE/name) == record['after'], 'Package changed: '+name
        shutil.copy2(GAME/'bin'/name, backup/name)
        assert digest(backup/name) == record['before']
    changed = []
    try:
        for name, record in manifest['files'].items():
            assert digest(GAME/'bin'/name) == record['before'], 'Concurrent update: '+name
            changed.append(name)
            shutil.copy2(PACKAGE/name, GAME/'bin'/name)
            assert digest(GAME/'bin'/name) == record['after']
        for name, record in manifest['files'].items():
            assert digest(GAME/'bin'/name) == record['after']
    except BaseException:
        for name in reversed(changed):
            shutil.copy2(backup/name, GAME/'bin'/name)
            assert digest(GAME/'bin'/name) == manifest['files'][name]['before']
        raise
    (OUT/'transfer_fix_installed.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    clean(backup)
    print('Installed and hash-verified:', ', '.join(manifest['files']), '. Game not launched.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--content-only', action='store_true', help='Stage only Content and its symbols')
    args = parser.parse_args()
    if args.content_only:
        SOURCES = {name: path for name, path in SOURCES.items() if name.startswith('Content.')}
    apply() if args.apply else stage()
