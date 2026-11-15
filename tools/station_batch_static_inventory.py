"""Read-only census of large numbered object groups in loaded systems."""
import json,re
from collections import defaultdict
import valensia_mega as m

systems=[]
for b in m.old.blocks((m.GAME/'DATA/UNIVERSE/universe.ini').read_text()):
    if b.lstrip().lower().startswith('[system]'):
        d=m.old.fields(b);systems.append((m.old.one(d,'nickname'),'DATA/UNIVERSE/'+m.old.one(d,'file').replace('\\','/')))
result=[]
for system,path in systems:
    p=m.GAME/path
    if not p.exists():continue
    groups=defaultdict(list)
    for row in m.b.placements_from_template(p.read_text(encoding='utf-8-sig',errors='replace')):
        match=re.match(r'^(.+?_\d{2})(?:_|$)',row.name)
        if match:groups[match[1]].append(row)
    for prefix,rows in groups.items():
        if len(rows)<40:continue
        optimized=any(r.archetype.startswith(('batch_','forbes_mega_','stuttgart_mega_','valensia_','ulster_','pdm_','tfm_','vienna_')) for r in rows)
        result.append(dict(system=system,path=path,prefix=prefix,objects=len(rows),optimized=optimized))
(m.REPO/'out/station_batch/static_inventory.json').write_text(json.dumps(result,indent=2))
print(json.dumps(sorted((r for r in result if not r['optimized']),key=lambda x:-x['objects']),indent=2))
