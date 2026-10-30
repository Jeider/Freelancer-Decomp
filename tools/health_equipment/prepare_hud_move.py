"""Stage HUD asset relocation and update path strings in the installed client.

Only existing .rdata string slots change; code, imports, offsets and DLL ABI stay
identical. This lets a content migration use the installed working build even
while unrelated source changes are being developed. Source paths are updated too.
"""
from pathlib import Path
import datetime
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
GAME = Path('D:/games/FL_MOD')
sys.path.insert(0, str(ROOT / 'tools/beta_evade_patch'))
from verify import PE


def sha(data):
    return hashlib.sha256(data).hexdigest().upper()


def main():
    pe = PE(GAME / 'bin/freelancer.exe')
    data = bytearray(pe.data)
    replacements = [
        (r'%s..\DATA_EXTRA\FLIGHT_ACTIONS\%s', r'%s..\DATA\INTERFACE\HUD\EXTRA\%s'),
        (r'..\DATA_EXTRA\FLIGHT_ACTIONS\%s', r'INTERFACE\HUD\EXTRA\%s'),
        (r'..\DATA_EXTRA\HEALTH\HUD_DefCloak.3db', r'INTERFACE\HUD\EXTRA\HUD_DefCloak.3db'),
        ('HUD_corkscrewevade.3db', 'HUD_drasticevade.3db'),
    ]
    changed = set()
    slots = []
    for old, new in replacements:
        old, new = old.encode() + b'\0', new.encode() + b'\0'
        assert data.count(old) == 1, ('Unexpected installed path count', old)
        assert len(new) <= len(old)
        offset = data.index(old)
        section = next(s for s in pe.sections if s[4] <= offset and offset + len(old) <= s[4] + s[3])
        assert section[0].rstrip(b'\0') == b'.rdata'
        data[offset:offset + len(old)] = new.ljust(len(old), b'\0')
        changed.update(range(offset, offset + len(old)))
        slots.append(dict(offset=offset, old=old[:-1].decode(), new=new[:-1].decode()))
    assert len(data) == len(pe.data)
    assert all(a == b or i in changed for i, (a, b) in enumerate(zip(pe.data, data)))
    for name, _, _, size, offset in pe.sections:
        if name.rstrip(b'\0') != b'.rdata':
            assert data[offset:offset + size] == pe.data[offset:offset + size]
    assert b'DATA_EXTRA\\FLIGHT_ACTIONS' not in data and b'DATA_EXTRA\\HEALTH' not in data

    stage = ROOT / 'src/obj/hud_assets_install' / datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    payload = {'bin/freelancer.exe': bytes(data)}
    removals = []
    for folder in ('FLIGHT_ACTIONS', 'HEALTH'):
        for path in sorted((GAME / 'DATA_EXTRA' / folder).glob('*.3db')):
            name = 'HUD_drasticevade.3db' if path.name == 'HUD_corkscrewevade.3db' else path.name
            relative = 'DATA/INTERFACE/HUD/EXTRA/' + name
            assert relative not in payload
            payload[relative] = path.read_bytes()
            assert (ROOT / 'assets/hud/extra' / name).read_bytes() == path.read_bytes()
            removals.append(dict(relative=path.relative_to(GAME).as_posix(), original=sha(path.read_bytes())))
    for name in ('HUD_drasticevade.3db', 'HUD_turntoface.3db', 'hud_mnvrstrafe.3db', 'hud_mnvrevade.3db', 'HUD_DefCloak.3db'):
        assert 'DATA/INTERFACE/HUD/EXTRA/' + name in payload
    for name in ('HUD_health_cloak_icon.tga', 'README.txt'):
        payload['DATA/INTERFACE/HUD/EXTRA/' + name] = (ROOT / 'assets/hud/extra' / name).read_bytes()
    files = []
    for relative, content in payload.items():
        target = stage / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        original = GAME / relative
        files.append(dict(relative=relative, original=sha(original.read_bytes()) if original.exists() else None,
                          prepared=sha(content)))
    manifest = dict(game=str(GAME), files=files, removals=removals, path_slots=slots)
    (stage / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    script = Path(__file__).with_name('install_hud_move.ps1').read_text()
    allowed = ', '.join("'" + entry['relative'] + "'" for entry in files + removals)
    script = script.replace('@ALLOWED@', '@(' + allowed + ')')
    (stage / 'install.ps1').write_text(script)
    print('PASS: only four .rdata strings changed; executable code/imports and all other bytes preserved')
    print(f'Prepared {len(files)} files and relocation of {len(removals)} old assets: {stage}')


if __name__ == '__main__':
    main()
