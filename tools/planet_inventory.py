"""Inventory of planet archetypes in a Freelancer mod: models, material libraries, usage counts."""
import collections
import re
import sys
from pathlib import Path

DATA = Path(sys.argv[1] if len(sys.argv) > 1 else 'D:/games/FL_MOD/DATA')
text = (DATA / 'SOLAR/solararch.ini').read_text(encoding='latin-1')
planets = []
for block in re.split(r'(?im)^\s*\[', text):
    if not block.lower().startswith('solar]'):
        continue
    kv = collections.defaultdict(list)
    for line in block.splitlines()[1:]:
        line = line.split(';', 1)[0].strip()
        if '=' in line:
            k, v = line.split('=', 1)
            kv[k.strip().lower()].append(v.strip())
    if kv.get('type', [''])[0].lower() != 'planet':
        continue
    planets.append(dict(nickname=kv['nickname'][0], archetype=kv.get('da_archetype', [''])[0],
                        materials=kv.get('material_library', []), radius=kv.get('solar_radius', [''])[0]))
# How often each archetype appears in system files.
uses = collections.Counter()
for ini in (DATA / 'UNIVERSE/SYSTEMS').rglob('*.ini'):
    for m in re.finditer(r'(?im)^\s*archetype\s*=\s*(\S+)', ini.read_text(encoding='latin-1', errors='replace')):
        uses[m.group(1).lower()] += 1
print(len(planets), 'planet archetypes')
for p in sorted(planets, key=lambda p: -uses[p['nickname'].lower()]):
    print(f"{uses[p['nickname'].lower()]:3d}  {p['nickname']:32s} {p['archetype']:48s} r={p['radius']:>8s}  {', '.join(p['materials'])}")
