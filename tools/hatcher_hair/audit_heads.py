"""Read-only material inventory before extending hair shading to other heads."""
import json
from build import GAME,OUT,read_tree,child,blob
rows=[]
for path in sorted((GAME/'DATA/CHARACTERS/HEADS').rglob('*.dfm')):
    try:
        root=read_tree(path.read_bytes())[1][0]
        groups=child(child(child(root,'MultiLevel'),'Mesh0'),'Face_groups')
        materials=sorted({blob(g,'Material_name').rstrip(b'\0').decode('ascii','replace') for g in groups.children if g.children})
        explicit=[m for m in materials if 'hair' in m.lower()]
        rows.append(dict(file=path.name,materials=materials,explicit_hair=explicit))
    except Exception as e:rows.append(dict(file=path.name,error=str(e)))
(OUT/'head_material_audit.json').write_text(json.dumps(rows,indent=2))
print('Heads:',len(rows),'explicit hair:',sum(bool(r.get('explicit_hair')) for r in rows),'errors:',sum('error' in r for r in rows))
for r in rows:
    if r.get('explicit_hair'):print(r['file'],r['explicit_hair'])
