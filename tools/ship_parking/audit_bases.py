"""Read actual Pythonlancer dockables and compare them with installed parking."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path.insert(0, str(PROJECT))
sys.dont_write_bytecode = True
from core import get_core
from tools.ship_parking import sections, one, datafile


def source_bases(universe):
    rows = []
    for system in universe.universe_root.get_all_systems():
        if not system.have_dynamic_content():
            continue
        for base in system.get_dockable_objects():
            if not base.IS_BASE:
                continue
            name = base.get_ru_name()
            rows.append(dict(base=base.get_base_nickname().lower(), system=system.NAME,
                             cls=base.__class__.__name__, faction=base.get_faction().CODE,
                             name_ru=name.get_ru(), name_en=name.get_en(),
                             shipdealer=bool(base.have_shipdealer()), bar=bool(base.have_bar()),
                             locked=bool(base.LOCKED_DOCK), story=bool(base.STORY)))
    return rows


def main():
    core = get_core()
    rows = source_bases(core.universe)
    game = PROJECT.parent.parent
    contacts = {one(row,'base').lower(): one(row,'rtc') for kind,row in
                sections(game/'DATA/RPG/parking_contacts.ini') if kind=='rpgcontact' and one(row,'enabled')=='true'}
    for row in rows:
        row['contact'] = contacts.get(row['base'])
    output = ROOT/'src/obj/ship_parking/commandants'
    output.mkdir(parents=True,exist_ok=True)
    (output/'source_bases.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
    wanted = [r for r in rows if r['shipdealer']]
    print(json.dumps({'bases':len(rows),'shipdealers':len(wanted),
                      'missing_contact':[r for r in wanted if not r['contact']],
                      'no_bar':[r for r in wanted if not r['bar']]},ensure_ascii=False,indent=2))


if __name__=='__main__':
    main()
