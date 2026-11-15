"""Read-only audit of Valensia template variants and the live Order HQ station."""
import ast
from collections import Counter
import json
from pathlib import Path
import sys

import bake_compound as bake

GAME = Path('D:/Games/FL_MOD')
PYTHON = GAME/'Assets/Pythonlancer'


def templates():
    text = (PYTHON/'templates/dockable/valensia.py').read_text(encoding='utf-8-sig')
    result = {}
    for node in ast.parse(text).body:
        if isinstance(node, ast.ClassDef):
            for member in node.body:
                if isinstance(member, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'TEMPLATE' for t in member.targets):
                    result[node.name] = ast.literal_eval(member.value)
    return result


if __name__ == '__main__':
    solars, equipment, loadouts = bake.catalog(GAME/'DATA')
    sources = templates()
    live = GAME/'DATA/UNIVERSE/SPECIAL/ORDER_HQ/or_hq.ini'
    sources['or_hq_live'] = live.read_text()
    for name, text in sources.items():
        rows = bake.placements_from_template(text)
        if name == 'or_hq_live':
            rows = [r for r in rows if r.name.startswith('or_hq_station_1')]
        print(name, 'objects', len(rows))
        print('groups', Counter(next((s for s in r.name.split('_') if s.isupper()), 'OTHER') for r in rows))
        for arch, count in Counter(r.archetype for r in rows).most_common():
            a = solars.get(arch.lower(), {})
            print(count, arch, a.get('type'), a.get('da_archetype'), a.get('loadout'),
                  'object loadouts', sorted({r.loadout for r in rows if r.archetype == arch and r.loadout}))
