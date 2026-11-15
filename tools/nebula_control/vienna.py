"""Stage/install the Vienna continuous-volume experiment with verified backups."""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/Games/FL_MOD')
OUT = ROOT/'out/vienna_volume'
STAGE = OUT/'staged'
VOLUME = 'DATA_EXTRA/VOLUMETRIC/volumetric.ini'
NEBULA = 'DATA/SOLAR/NEBULA_MOD/m11_vienna_nebula.ini'
sys.path.insert(0, str(ROOT/'tools/train_courier'))
from data_output import data_folder
from sphere_exterior import edit_section


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write(root, relative, data):
    if relative.startswith('DATA/'):
        data_folder(GAME, root).sync_data_file(relative[5:], data)
    else:
        path = root/relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)


def prepare():
    source = (ROOT/VOLUME).read_text(encoding='utf-8-sig')
    profiles = [m[0] for m in re.finditer(r'(?ims)^\[NebulaOverride\][^\n]*\n.*?(?=^\[|\Z)', source)
                if re.search(r'(?im)^file\s*=\s*m11_vienna_nebula\s*$', m[0])]
    assert len(profiles) == 1
    profile = profiles[0].strip()+'\n'
    manifest = {}
    for relative in ('bin/freelancer.exe', 'bin/freelancer.pdb', VOLUME):
        original = (GAME/relative).read_bytes()
        if relative.startswith('bin/'):
            data = (ROOT/'src/obj/train_courier/rpg1'/relative).read_bytes()
        else:
            text = original.decode('utf-8-sig').replace('\r\n', '\n')
            if relative == VOLUME:
                if re.search(r'(?im)^file\s*=\s*m11_vienna_nebula\s*$', text):
                    text = edit_section(text, 'NebulaOverride',
                        r'^file\s*=\s*m11_vienna_nebula\s*$',
                        {'render_in_exclusion':'1', 'exclusion_march_distance':'6000',
                         'exclusion_transition_fraction':'0.2'})
                else:
                    text = text.rstrip()+'\n\n'+profile
            else:
                text = edit_section(text, 'Exclusion Zones',
                    r'^exclusion\s*=\s*Zone_m11_rh_vienna_CORE_exclusion\s*$', {'max_alpha':'0.5'})
            data = text.replace('\n', '\r\n' if b'\r\n' in original else '\n').encode('utf-8')
            if original.startswith(b'\xef\xbb\xbf'):
                data = b'\xef\xbb\xbf'+data
        write(STAGE, relative, data)
        manifest[relative] = {'before':sha(original), 'after':sha(data)}
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2))
    print('Staged client + Vienna override; live shell settings and other profiles preserved')


def restore_shell():
    original = (GAME/NEBULA).read_bytes()
    text = original.decode('utf-8-sig').replace('\r\n', '\n')
    text = edit_section(text, 'Exclusion Zones',
        r'^exclusion\s*=\s*Zone_m11_rh_vienna_CORE_exclusion\s*$', {'max_alpha':'0.5'})
    data = text.replace('\n', '\r\n' if b'\r\n' in original else '\n').encode('utf-8')
    if original.startswith(b'\xef\xbb\xbf'):
        data = b'\xef\xbb\xbf'+data
    write(STAGE, NEBULA, data)
    (OUT/'manifest.json').write_text(json.dumps(
        {NEBULA: {'before':sha(original), 'after':sha(data)}}, indent=2))
    print('Staged original shell opacity 0.5; continuous volume unchanged')


def apply():
    manifest = json.loads((OUT/'manifest.json').read_text())
    processes = subprocess.check_output(['tasklist', '/FO', 'CSV', '/NH']).lower()
    assert not any(b'"'+name+b'"' in processes for name in
        (b'freelancer.exe', b'flserver.exe', b'freelancer_window.exe', b'freelancer_en.exe', b'freelancer_window_en.exe')), 'Close the game before installing'
    for relative, item in manifest.items():
        target = (GAME/relative).resolve()
        assert target.is_relative_to(GAME.resolve()), 'Path outside game'
        before = sha(target.read_bytes()) if target.exists() else None
        assert before == item['before'], relative+' changed since staging'
        assert sha((STAGE/relative).read_bytes()) == item['after']
    backup = OUT/'backups'/datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    for relative in manifest:
        if manifest[relative]['before'] is not None:
            write(backup, relative, (GAME/relative).read_bytes())
            assert sha((backup/relative).read_bytes()) == manifest[relative]['before']
    backup.mkdir(parents=True, exist_ok=True)
    (backup/'manifest.json').write_text(json.dumps(manifest, indent=2))
    touched = []
    try:
        for relative, item in manifest.items():
            touched.append(relative)
            write(GAME, relative, (STAGE/relative).read_bytes())
            assert sha((GAME/relative).read_bytes()) == item['after']
    except Exception:
        for relative in reversed(touched):
            if manifest[relative]['before'] is not None:
                write(GAME, relative, (backup/relative).read_bytes())
            elif relative.startswith('DATA/'):
                data_folder(GAME, GAME).remove_data_file(relative[5:])
            else:
                (GAME/relative).unlink(missing_ok=True)
        raise
    print('Installed and SHA256 verified. Backup:', backup)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--restore-shell', action='store_true')
    args = parser.parse_args()
    if args.restore_shell:
        restore_shell()
    elif args.apply:
        apply()
    else:
        prepare()
