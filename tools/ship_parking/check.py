"""Compile production parking and dialogue code against fake game I/O and exercise transactions."""
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/rpg_cutscenes/pythonlancer'))
sys.path.insert(0, str(ROOT / 'tools/nebula_control'))
from build_asf_hq import compiler_env
from generate import generate, dialogue
from data_folder_update import prepare


def main():
    out = ROOT / 'src/obj/ship_parking/check'
    out.mkdir(parents=True, exist_ok=True)
    for source, name in [('src/Server/ship_cache.cpp', 'cache.inc'),
                         ('src/include/ship_cache.h', 'cache_types.inc'),
                         ('src/Content/RpgDialog.cpp', 'dialog.inc')]:
        text = (ROOT / source).read_text(encoding='utf-8-sig')
        text = re.sub(r'^#include "[^"\n]+"\n', '', text, flags=re.M)
        text = text.replace('#pragma once', '')
        (out / name).write_text(text, encoding='utf-8')
    # Overrides intentionally precede defaults to test order independence.
    (out / 'RPG').mkdir(exist_ok=True)
    (out / 'RPG/ship_parking.ini').write_text('''[ParkingBase]
base = base_a
seller = seller_a
reputation_faction = faction_a
[ParkingBase]
base = base_b
seller = seller_b
reputation_faction = faction_b
slot_price = 12000
[ParkingBase]
base = invalid_price
seller = seller_c
slot_price = -100
[ParkingDefaults]
max_slots = 3
initial_slots = 0
slot_price = 20000
''')
    (out / 'dialog.ini').write_text(dialogue('base_a', 'seller_a'), encoding='utf-8')
    # Exercise the production spoken graph alongside parking regression coverage.
    sys.path.insert(0, str(ROOT / 'tools/rpg_cutscenes/pythonlancer'))
    from files.rpg_runtime import dialog_ini
    from story.rpg.script import RpgScript
    scenario = RpgScript.load(Path('D:/Games/FL_MOD/Assets/Pythonlancer/story/rpg/rm0001.json'))
    (out / 'rm0001.ini').write_text(dialog_ini(scenario), encoding='utf-8')
    (out / 'owner.ini').write_text(dialog_ini(scenario).replace('nickname = rm0001\n',
        'nickname = owner_test\ncourier_base = base_b\nsession_group = rm0201\n',1), encoding='utf-8')
    parking = RpgScript.load(Path(__file__).with_name('rm0002.json'))
    parking.data['parking'] = {'base': 'base_a', 'seller': 'seller_a'}
    (out / 'rm0002.ini').write_text(dialog_ini(parking).replace('[Dialog]\n', '[Dialog]\nlocal_scene = 1\n'), encoding='utf-8')
    compiler, env = compiler_env()
    subprocess.run([str(compiler / 'cl.exe'), '/nologo', '/std:c++17', '/EHsc', '/W4', '/MT', '/utf-8', '/D_CRT_SECURE_NO_WARNINGS',
                    '/I' + str(out), '/I' + str(ROOT / 'src/include'), '/I' + str(ROOT / 'src/Content'),
                    str(Path(__file__).with_name('test.cpp')), '/Fe:' + str(out / 'test.exe'),
                    '/Fo:' + str(out / 'test.obj')], cwd=out, env=env, check=True)
    subprocess.run([str(out / 'test.exe')], cwd=out, check=True)
    DataFolder, _ = prepare(Path('D:/Games/FL_MOD'), out / 'support')
    class ObservedFolder(DataFolder):
        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.written = []

        def sync_data_file(self, relative, content):
            self.written.append(relative)
            return super().sync_data_file(relative, content)

    folder = ObservedFolder(root=out / 'generation')
    files, report = generate(Path('D:/Games/FL_MOD'), out / 'generation', folder=folder)
    assert set(folder.written) == {p.removeprefix('DATA/') for p in files}
    # Check the central writer's explicit root, build output and exact-byte rollback API.
    isolated = DataFolder('EN_TEST', root=out / 'writer')
    assert isolated.get_root() == (out / 'writer/BUILDS/EN_TEST').resolve()
    original = b'[ParkingDefaults]\r\nslot_price = 20000\r\n'
    target = isolated.sync_data_file('RPG/ship_parking.ini', original)
    assert target.read_bytes() == original
    isolated.sync_data_file('RPG/ship_parking.ini', b'changed')
    isolated.sync_data_file('RPG/ship_parking.ini', original)
    assert target.read_bytes() == original
    isolated.remove_data_file('RPG/ship_parking.ini')
    assert not target.exists()
    for invalid in ('../escape.ini', 'RPG/../../escape.ini', str(out / 'escape.ini'), 'C:escape.ini', 'RPG/file:stream', '.'):
        try:
            isolated.sync_data_file(invalid, b'invalid')
        except ValueError:
            pass
        else:
            raise AssertionError('Accepted invalid DATA destination: ' + invalid)
    assert len({r['base'] for r in report['managers']}) == len(report['managers'])
    for base in ('rh_biz_01_base', 'rh_biz_02_base', 'om15_01_base'):
        assert any(r['base'] == base for r in report['managers']), base
    print('PASS: generated sellers have free, authored placements and camera/player markers')
    print('PASS: all parking DATA output uses DataFolder; explicit/build roots, exact-byte restore and path confinement')


if __name__ == '__main__':
    main()
