"""Keep authored non-orthonormal bases; Blender dump represents rotation only."""
import json
from inventory import OUT

count=0
for path in (OUT/'Pythonlancer/story/cutscenes/story_scenes').glob('*.py'):
    name=path.stem
    source=json.loads((OUT/name/'source.json').read_text())
    report=json.loads((OUT/name/'report.json').read_text())
    dump=json.loads((OUT/'SCENES/DUMPS'/f'{name}.json').read_text())
    additions=[]
    for e in source['entities']:
        n=e['entity_name'];matrix=e.get('spatialprops',{}).get('orient')
        if not matrix or 'subtitle' in n.lower() or n.lower().startswith('cam_dbg'): continue
        if not any(abs(sum(x*x for x in row)-1)>0.001 for row in matrix):continue
        point=report['point_names'][n]
        if point not in dump:continue
        q=dump[point]['orientation']; q=[q[0],-q[1],-q[2],-q[3]]
        obj=report['entity_names'][n]
        additions.append(f'        preserve_spatial(self.get_entity({obj!r}), source_basis={matrix!r}, reference_orientation={q!r})')
        count+=1
    text=path.read_text(encoding='utf-8')
    text='\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('preserve_spatial('))+'\n'
    text=text.replace('        restore_dialogue(self)','\n'.join(additions+['        restore_dialogue(self)']))
    path.write_text(text,encoding='utf-8')
print('Preserved scaled/source bases',count)
