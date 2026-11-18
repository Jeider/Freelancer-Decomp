"""User-authorized RU bar scenes; existing single.py builder and DataFolder only."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import wave
from install_evacuation import safe_file

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'out/train_courier/audio_ru/scenes'
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
GAME = PROJECT.parent.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(PROJECT))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    from managers.rpg_scene import RpgSceneManager
    from story.rpg.script import RpgScript
    script = RpgScript.load(PROJECT/'story/rpg/rm0001.json')
    scenes = RpgSceneManager(PROJECT, script, GAME)
    files, catalogs = scenes.plan(('ru',))
    assert len(catalogs['ru']['fragments']) == 32
    for name, expected in files.items():
        assert (GAME/'DATA'/name).read_bytes() == expected, name
    for row in catalogs['ru']['fragments']:
        path = GAME/'DATA'/row['audio']
        with wave.open(str(path), 'rb') as audio:
            assert audio.getnframes()/audio.getframerate() == row['speech_seconds']
        text = files[row['path']].decode('utf-8')
        assert text.count('START_SOUND') == 1 and row['sound'] in text
        assert row['speech_seconds'] < row['scene_seconds'] < row['speech_seconds']+2
        for start, props in re.findall(r'\{\s*([0-9.]+),\s*START_MOTION,\s*\{[^}]+\},\s*\{([^}]+)\}', text):
            duration = float(re.search(r'duration=([0-9.]+)', props)[1])
            assert float(start)+duration <= row['scene_seconds']+.02
    report = {'language':'ru', 'fragments':32, 'files':{name:sha(GAME/'DATA'/name) for name in files},
              'validation':'Installed hashes, RU WAV duration, sound IDs, facial event bounds; no game launch'}
    (OUT/'verified.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report


def build():
    # Preserve every unrelated source edit while adapting the inherited facial API.
    source = PROJECT/'story/rpg/scene.py'
    content = source.read_bytes()
    old = b'def lookup_single_sound(self, index):'
    new = b'def lookup_single_sound(self, index, props=None):'
    assert content.count(old)+content.count(new)==1
    if old in content:
        source.write_bytes(content.replace(old, new))
    en = {str(p):sha(p) for p in (GAME/'DATA/SCRIPTS/RPG/rm0001/en').glob('*') if p.is_file()}
    subprocess.run([sys.executable, '-B', 'single.py', 'rpg', 'scenes', '--group', 'rm0001',
                    '--language', 'ru', '--output', str(OUT)], cwd=PROJECT, check=True)
    report = verify()
    assert all(sha(Path(p))==digest for p,digest in en.items()), 'EN scenes changed'
    report['english_scene_files_unchanged'] = len(en)
    (OUT/'verified.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print('PASS: 32 RU scenes installed; RU audio/facial timing verified; EN files preserved')


def connect(apply=False):
    from files.rpg_runtime import dialog_ini
    from story.rpg.script import RpgScript
    from tools.data_folder import DataFolder
    script = RpgScript.load(PROJECT/'story/rpg/rm0001.json')
    verify()
    registry = json.loads((PROJECT/'story/rpg/courier_owners.json').read_text(encoding='utf-8'))
    files = {}
    before_hashes = {}
    report = []
    without_fragments = lambda text: re.sub(r'(?m)^fragment = [^\n]*\n', '', text)
    for entry in registry['bases']:
        if entry['voice_group'] != 'rm0001':
            continue
        base, group = entry['base'], entry['group']
        name = f'RPG/courier/{base}_dialog.ini'
        before = (GAME/'DATA'/name).read_text(encoding='utf-8-sig')
        after = dialog_ini(script, {r['id'] for r in script.fragments})
        after = after.replace('nickname = rm0001\n', 'nickname = '+entry['actor']+'_dialog\n', 1)
        after = after.replace('[Dialog]\n', f'[Dialog]\ncourier_base = {base}\nsession_group = {group}\n', 1)
        after = after.replace('reputation_faction = rh_grp', 'reputation_faction = '+entry['faction'])
        assert without_fragments(before)==without_fragments(after), 'Unrelated dialogue changes: '+name
        assert set(re.findall(r'(?m)^fragment = (.*)$', after)) <= {r['id'] for r in script.fragments}
        if before != after:
            files[name] = after.encode('utf-8')
            before_hashes[name] = sha(GAME/'DATA'/name)
        report.append({'base':base, 'before':before.count('fragment = '), 'after':after.count('fragment = ')})
    (OUT/'connection_plan.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    if apply:
        folder = DataFolder(root=GAME)
        backup = OUT/'connection_backup'
        assert not (backup/'transaction.json').exists(), 'Previous transaction requires review'
        folder.sync_courier_owners(files, backup)
        for name, content in files.items():
            assert (GAME/'DATA'/name).read_bytes()==content
        (OUT/'connected.json').write_text(json.dumps({'owners':len(report), 'files':{
            name:sha(GAME/'DATA'/name) for name in files}}, indent=2), encoding='utf-8')
        # The transaction succeeded. Remove only its exact, scoped rollback files.
        transaction = json.loads((backup/'transaction.json').read_text(encoding='utf-8'))
        rollback = DataFolder(root=backup)
        for name, existed in transaction['data_files'].items():
            assert name in files and name.startswith('RPG/courier/')
            if existed:
                assert sha(safe_file(backup/'DATA'/name, OUT)) == before_hashes[name]
                rollback.remove_data_file(name)
    print(('Connected' if apply else 'Planned'), len(report), 'owners; only fragment bindings change')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('build','verify','plan-connection','connect'))
    args=parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.action=='build': build()
    elif args.action in ('plan-connection','connect'): connect(args.action=='connect')
    else: verify()
