"""Stage the shared Capital.get_damage fix used by ShiparchManagerV2 and V1."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path('D:/games/FL_MOD/Assets/Pythonlancer')
OUT = Path(__file__).resolve().parents[2] / 'src/obj/targeting_world_install'
RELATIVE = 'Assets/Pythonlancer/world/capital.py'


def patch(raw):
    text = raw.decode('utf-8')
    newline = '\r\n' if '\r\n' in text else '\n'
    text = text.replace('\r\n', '\n')
    begin = text.index('        init_dmg_fuse_name =')
    end = text.index('        params.extend([', begin)
    text = text[:begin] + "        params.append('vulnerable = true')\n\n" + text[end:]
    assert text.count('self.get_part_hit_pts(hit_pts_multipler)+init_damage') == 1
    text = text.replace('self.get_part_hit_pts(hit_pts_multipler)+init_damage', 'self.get_part_hit_pts(hit_pts_multipler)')
    begin = text.index('    def add_initial_damage_fuse(')
    end = text.index('    def get_part_fuses_definitions(', begin)
    text = text[:begin] + text[end:]
    assert text.count('    INITIAL_PART_DAMAGE_FACTOR = 0.5\n') == 1
    text = text.replace('    INITIAL_PART_DAMAGE_FACTOR = 0.5\n\n', '')
    ast.parse(text)
    return text.replace('\n', newline).encode('utf-8')


def validate(before, after):
    # Run the actual generator methods, including the unchanged combat fuse
    # builder, without constructing Core or writing generated game/IDS files.
    def make_class(raw):
        tree = ast.parse(raw.decode('utf-8'))
        capital = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Capital')
        methods = {'get_damage', 'get_part_hit_pts', 'get_hit_pts', 'add_extra_damage_fuse',
                   'add_initial_damage_fuse', 'get_part_fuses_definitions'}
        body = [n for n in capital.body if isinstance(n, ast.FunctionDef) and n.name in methods]
        cls = ast.ClassDef(name='Fixture', bases=[], keywords=[], body=body, decorator_list=[])
        module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
        scope = dict(DEBRIS='debris', RESIST_DEFAULT=1.5, SINGLE_DIVIDER='\n')
        exec(compile(module, 'capital.py generator fixture', 'exec'), scope)
        return scope['Fixture']
    old, new = make_class(before), make_class(after)
    cases = 0
    for multiplier in (0.25, 0.5, 1, 2, 4):
        for silent in (False, True):
            for immortal in (False, True):
                pair = []
                for cls in (old, new):
                    obj = cls()
                    obj.ARCHETYPE = 'check_cruiser'
                    obj.PARTS_HP = 10000
                    obj.HIT_PTS = 250000
                    obj.EXTRA_DAMAGE = 20000
                    obj.INITIAL_PART_DAMAGE_FACTOR = 0.5
                    obj.NO_DEATH_FUSE = immortal
                    obj.DAMAGE_FX = obj.DAMAGE_FX_LARGE = 'explosion_test'
                    obj.HURT_FX, obj.HURT_HP = 'sound_test', 'HpMount'
                    obj.used_parts, obj.fuses_definitions = [], []
                    result = obj.get_damage('tower', 'Tower_lod1', 'DpTower',
                        hit_pts_multipler=multiplier, silent=silent, is_large=True)
                    pair.append((obj, result))
                (a, old_params), (b, new_params) = pair
                assert a.fuses_definitions[0] == b.fuses_definitions[0]
                assert len(a.fuses_definitions) == 2 and len(b.fuses_definitions) == 1
                assert '_init_dmg_' not in new_params and 'vulnerable = true' in new_params
                assert f'hit_pts = {b.get_part_hit_pts(multiplier)}' in new_params
                assert 'root_health_proxy = true' in new_params
                assert 'explosion_resistance = 1.5' in new_params
                cases += 1
    return cases


if __name__ == '__main__':
    raw = (ROOT / 'world/capital.py').read_bytes()
    prepared = patch(raw)
    cases = validate(raw, prepared)
    target = OUT / RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(prepared)
    report = dict(relative=RELATIVE, original=hashlib.sha256(raw).hexdigest(),
                  prepared=hashlib.sha256(prepared).hexdigest(), validated_cases=cases)
    (OUT / 'generator.json').write_text(json.dumps(report, indent=2))
    print(f'Staged Capital generator: {cases} cases passed; combat fuse unchanged, no startup damage or HP padding.')
