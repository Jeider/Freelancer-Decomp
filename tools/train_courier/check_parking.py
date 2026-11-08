"""Read-only checks of parking geometry, solar configs and existing refusal audio.

Does not export Pythonlancer, compile, stage or install anything.
"""
from pathlib import Path
import json
import math
import sys

sys.dont_write_bytecode = True
from export import sections, one, fixture_pose, triple
from stage import parked_solar, section, boarding_objects


def main():
    game = Path('D:/Games/FL_MOD')
    root = Path(__file__).resolve().parents[2]
    catalog = json.loads((root/'out/train_courier/catalog.json').read_text(encoding='utf-8'))
    rings = {one(s, 'nickname') for k, s in sections(game/'DATA/SOLAR/solararch.ini')
             if k == 'solar' and one(s, 'type').upper() == 'DOCKING_RING'}
    parking = []
    for kind, system in sections(game/'DATA/UNIVERSE/universe.ini'):
        if kind != 'system' or not one(system, 'file'):
            continue
        path = game/'DATA/UNIVERSE'/one(system, 'file').replace('\\', '/')
        if not path.exists():
            continue
        objects = [s for k, s in sections(path) if k == 'object']
        planets = {one(s, 'dock_with') for s in objects if one(s, 'archetype') in rings}
        for fixture in objects:
            base = one(fixture, 'dock_with')
            if one(fixture, 'archetype') != 'docking_fixture' or base not in planets or base not in catalog['bases']:
                continue
            position, angles, quaternion = fixture_pose(game, fixture)
            center = triple(one(fixture, 'pos'))
            assert 150 < position[1]-center[1] < 200
            assert one(fixture, 'reputation'), base
            assert abs(sum(v*v for v in quaternion)-1) < 1.e-6
            toward = [center[0]-position[0], center[2]-position[2]]
            yaw = math.radians(angles[1])
            assert (-math.sin(yaw)*toward[0]-math.cos(yaw)*toward[1])/math.hypot(*toward) > .9999
            parking.append(base)
    assert 'rh_biz_01_base' in parking
    assert 'archetype = tc_boarding_solar' in boarding_objects(game)
    solar = (game/'DATA/SOLAR/train_courier.ini').read_text(encoding='utf-8-sig')
    upgraded = parked_solar(solar)
    assert parked_solar(upgraded) == upgraded, 'Repeated staging must not duplicate the parked solar'
    initial = section(upgraded, 'Solar', 'tc_boarding_solar')
    parked = section(upgraded, 'Solar', 'tc_parked_locomotive')
    assert initial.strip() == parked.replace('tc_parked_locomotive', 'tc_boarding_solar').strip()
    for language in ('ru', 'en'):
        sounds = sections(game/f'DATA/AUDIO/voices_static_{language}.ini')
        sound = next(s for k, s in sounds if k == 'sound' and one(s, 'msg') == 'info_access_denied')
        assert (game/'DATA'/one(sound, 'file').replace('\\', '/')).is_file()
    print(f'PASS: {len(parking)} graph bases with planet fixtures, parking poses, solar clone, RU/EN access-denied files; no build/install')


if __name__ == '__main__':
    main()
