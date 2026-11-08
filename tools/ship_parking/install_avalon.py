"""Install the authored Avalon parking conversation through Pythonlancer."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
OUT = ROOT / 'src/obj/ship_parking/avalon'
ACTOR = '''

class RpgAvalonParkingOfficer(Actor):
    NAME = 'rpg_avalon_parking_officer'
    TYPE = ACTOR_MALE
    RU_NAME = MS('Капитан стоянки Авалона', 'Avalon Parking Captain')
    VOICE_DELIVERY = NEUTRAL
    STEOS_SPEED = 1
    COMM_APPEARANCE = 'br_captain_head, br_male_elite_body'
    # Own reference: Assets/VOICE_SOURCE_EN/RpgAvalonParkingOfficer.wav.
'''


def install_sources():
    stamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup = OUT / 'source_backups' / stamp
    source = Path(__file__).with_name('rm0002.json').read_bytes()
    target = PROJECT / 'story/rpg/actors.py'
    current = target.read_bytes()
    actor = current if b'class RpgAvalonParkingOfficer(' in current else current + ACTOR.encode('utf-8')
    changes = {'story/rpg/rm0002.json': source, 'story/rpg/actors.py': actor,
               'managers/rpg_parking.py': (ROOT / 'tools/rpg_cutscenes/pythonlancer/managers/rpg_parking.py').read_bytes(),
               'tools/ship_parking.py': Path(__file__).with_name('generate.py').read_bytes()}
    def patch(relative, old, new):
        raw = (PROJECT / relative).read_bytes()
        newline = '\r\n' if b'\r\n' in raw else '\n'
        text = raw.decode('utf-8-sig').replace('\r\n', '\n')
        if new not in text:
            if text.count(old) != 1:
                raise ValueError('Source changed; review additive patch: ' + relative)
            text = text.replace(old, new, 1)
        changes[relative] = text.replace('\n', newline).encode('utf-8')
    # Add only the parking extension; retain the other agent's latest rm0001 work.
    renderer = 'files/rpg_runtime.py'
    anchor = "    rep = data['rules']['reputation']\n"
    patch(renderer, anchor,
          "    if 'parking' in data:\n"
          "        lines += ['parking_base = ' + data['parking']['base'],\n"
          "                  'parking_seller = ' + data['parking']['seller']]\n" + anchor)
    raw = changes[renderer]
    for lang in ('ru', 'en'):
        old = f"'text_{lang} = ' + rows[0]['{lang}']".encode()
        new = f"'text_{lang} = ' + node.get('text_{lang}', rows[0]['{lang}'])".encode()
        if new not in raw:
            assert raw.count(old) == 1
            raw = raw.replace(old, new, 1)
    changes[renderer] = raw
    anchor = 'def install_runtime(project, script, game_root, output, dry_run=False):\n'
    patch('managers/rpg_runtime.py', anchor, anchor +
          "    if script.name == 'rm0002':\n"
          "        from managers.rpg_parking import install_parking_runtime\n"
          "        return install_parking_runtime(project, script, game_root, output, dry_run)\n")
    methods = (ROOT / 'tools/rpg_cutscenes/data_folder_rpg.inc').read_text(encoding='utf-8')
    method = methods[methods.index('    def sync_rpg_parking_runtime'):methods.index('    # END RPG AUDIO OUTPUT')]
    patch('tools/data_folder.py', '    # END RPG AUDIO OUTPUT', method + '    # END RPG AUDIO OUTPUT')
    for relative, content in changes.items():
        path = PROJECT / relative
        if path.exists() and path.read_bytes() == content:
            continue
        if path.exists():
            saved = backup / relative
            saved.parent.mkdir(parents=True, exist_ok=True)
            saved.write_bytes(path.read_bytes())
        if path.suffix == '.py':
            compile(content, str(path), 'exec')
        path.write_bytes(content)
    sys.path.insert(0, str(PROJECT))
    from story.rpg.script import RpgScript
    from managers.rpg_voice import RpgVoiceManager
    script = RpgScript.load(PROJECT / 'story/rpg/rm0002.json')
    assert script.recording_group().get_sounds()[0].line.actor.__name__ == 'RpgAvalonParkingOfficer'
    RpgVoiceManager(PROJECT, PROJECT / 'story/rpg/rm0002.json').prepare(OUT / 'recordings')
    print(f'Installed rm0002: {len(script.fragments)} fragments; actor RpgAvalonParkingOfficer', flush=True)


def install_engine():
    game = PROJECT.parent.parent
    names = ('Content.dll', 'Content.pdb')
    build = ROOT / 'src/obj/train_courier/rpg1/bin'
    before = {name: (game / 'bin' / name).read_bytes() for name in names}
    after = {name: (build / name).read_bytes() for name in names}
    processes = subprocess.run(['tasklist', '/FO', 'CSV', '/NH'], capture_output=True, check=True).stdout.lower()
    if any(b'"' + name + b'"' in processes for name in
           (b'freelancer.exe', b'freelancer_en.exe', b'freelancer_window.exe', b'freelancer_window_en.exe', b'flserver.exe')):
        raise RuntimeError('Close the game/server before installing Content.dll')
    backup = OUT / 'engine_backups' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    backup.mkdir(parents=True)
    for name in names:
        (backup / name).write_bytes(before[name])
    touched = []
    try:
        for name in names:
            target = game / 'bin' / name
            assert target.read_bytes() == before[name], 'Game binary changed during installation'
            touched.append(name)
            target.write_bytes(after[name])
            assert target.read_bytes() == after[name]
    except BaseException:
        for name in reversed(touched):
            (game / 'bin' / name).write_bytes(before[name])
        raise
    (backup / 'manifest.json').write_text(json.dumps({name: hashlib.sha256(after[name]).hexdigest()
                                                   for name in names}, indent=2))
    print('Installed and verified voiced parking Content.dll in game bin; backup:', backup)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['sources', 'engine'])
    args = parser.parse_args()
    if args.command == 'sources':
        install_sources()
    elif args.command == 'engine':
        install_engine()


if __name__ == '__main__':
    main()
