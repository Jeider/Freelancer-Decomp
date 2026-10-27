"""Apply environment/native-face scopes to existing generated profiles, no DDS rebuild."""
import collections
import json
from pathlib import Path
from profile_scope import scope_flag, normal_scale

root=Path(__file__).resolve().parents[2]/'src/obj/room_materials'
report=json.loads((root/'generation.json').read_text(encoding='utf8'))
scopes={}
for m in report['materials']:
    key=(m['material']+'|'+m['texture']).lower()
    flag=scope_flag(m['source'],m['material'],m['role'])
    scopes[key]=max(scopes.get(key,-1),flag)
path=root/'assets/DATA_EXTRA/ROOM_MATERIALS/profiles.txt'
lines=[];counts=collections.Counter()
for line in path.read_text(encoding='latin1').splitlines():
    fields=line.split(' ',5)
    if len(fields)!=6:raise ValueError('Unexpected profile format')
    flag=scopes[fields[5]]
    material,texture=fields[5].split('|',1)
    fields[0]=f'{normal_scale(material,texture,float(fields[0])):.4f}'
    fields[3]=f'{flag:.4f}'
    lines.append(' '.join(fields));counts[flag]+=1
path.write_bytes(('\n'.join(lines)+'\n').encode('latin1'))
report['runtime_scopes']={'interior_max':counts[-1.0],'clothing_max':counts[-0.25],'character_finish':counts[0.0],'native_skin':counts[1.0]}
(root/'generation.json').write_text(json.dumps(report,indent=2),encoding='utf8')
print(report['runtime_scopes'])
