"""Render the real Shiparch V2 templates before/after the staged generator change, without writes."""
import ast
import sys
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True
root = Path('D:/games/FL_MOD/Assets/Pythonlancer')
repo = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root))
from jinja2 import Environment, FileSystemLoader, StrictUndefined
from managers.shiparch import ShiparchManagerV2
from world.capital import Capital
from prepare_vulnerable import sections, values

env = Environment(loader=FileSystemLoader(str(root / 'templates')), undefined=StrictUndefined)


class IDs:
    def __init__(self):
        self.next_id = 1000

    def new_name(self, *args, **kwargs):
        self.next_id += 1
        return SimpleNamespace(id=self.next_id)

    new_info = new_name


def build():
    core = SimpleNamespace(misc_equip=None, ids=SimpleNamespace(ship=IDs()), write=False,
        tpl_manager=SimpleNamespace(get_result=lambda template, context: env.get_template(template).render(context)))
    manager = ShiparchManagerV2(core)
    return manager, env.get_template('hardcoded_inis/shiparch/shiparch2.ini').render(manager.shiparch_context)


old_manager, before = build()
tree = ast.parse((repo / 'src/obj/targeting_world_install/Assets/Pythonlancer/world/capital.py').read_text(encoding='utf-8'))
cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == 'Capital')
method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'get_damage')
import world.capital as capital_module
namespace = dict(vars(capital_module))
exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), 'staged Capital.get_damage', 'exec'), namespace)
Capital.get_damage = namespace['get_damage']
new_manager, after = build()
old_sections, new_sections = list(sections(before)), list(sections(after))
assert len(old_sections) == len(new_sections)
changed = 0
for a, b in zip(old_sections, new_sections):
    assert a[0] == b[0]
    old, new = values(a[3]), values(b[3])
    init = [f for f in old.get('fuse', []) if '_init_dmg_' in f]
    if init:
        assert len(init) == 1 and a[0] == 'collisiongroup'
        assert new.pop('vulnerable') == ['true']
        old['fuse'].remove(init[0])
        assert abs(float(new.pop('hit_pts')[0]) * 1.5 - float(old.pop('hit_pts')[0])) < 1e-6
        changed += 1
    assert old == new, (a[0], old, new)
for old, new in zip(old_manager.capitals, new_manager.capitals):
    assert [f for f in old.fuses_definitions if '_init_dmg_' not in f] == new.fuses_definitions
assert changed == 134
print(f'PASS: real ShiparchManagerV2 templates render {changed} vulnerable groups; effective HP preserved; other fields and combat fuses identical. Core.write=False, game untouched.')
