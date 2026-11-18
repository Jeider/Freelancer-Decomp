"""Read-only candidate discovery; match every placement against loaded systems."""
import ast,json,re
from collections import defaultdict
import valensia_mega as m
from check_valensia_mega import templates

OUT=m.REPO/'out/stations/station_batch'

def inventory():
    py=m.GAME/'Assets/Pythonlancer'
    uses=defaultdict(set)
    for path in (py/'universe/systems').glob('*.py'):
        for mod,cls in re.findall(r'SPACE_OBJECT_TEMPLATE\s*=\s*(\w+)\.(\w+)',path.read_text(encoding='utf-8-sig')):
            uses[mod,cls].add(path.stem)
    systems={}
    for block in m.old.blocks((m.GAME/'DATA/UNIVERSE/universe.ini').read_text(encoding='utf-8-sig')):
        if not block.lstrip().lower().startswith('[system]'):continue
        d=m.old.fields(block)
        systems[m.old.one(d,'nickname')]='DATA/UNIVERSE/'+m.old.one(d,'file').replace('\\','/')
    candidates=[];excluded=[]
    for path in (py/'templates/dockable').glob('*.py'):
        if 'Original' in path.stem:continue
        sources=templates(path.read_text(encoding='utf-8-sig'))
        for cls,text in sources.items():
            if (path.stem,cls) not in uses or text.count('[Object]')<40:continue
            if cls+'Original' in sources:
                excluded.append(dict(template=path.stem,cls=cls,reason='already optimized'));continue
            if '{root_props}' not in text and '{dock_props}' not in text:
                excluded.append(dict(template=path.stem,cls=cls,reason='decorative debris, no station root/dock'));continue
            rows=m.b.placements_from_template(text)
            node=next(n for n in ast.parse(path.read_text(encoding='utf-8-sig')).body if isinstance(n,ast.ClassDef) and n.name==cls)
            prefix=next((ast.literal_eval(n.value) for n in node.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='SPACE_OBJECT_NAME' for t in n.targets)),rows[0].name)
            instances=[];errors=[]
            for system in sorted(uses[path.stem,cls]):
                if system not in systems:
                    errors.append(system+': not a loaded system');continue
                live=m.b.placements_from_template((m.GAME/systems[system]).read_text(encoding='utf-8-sig'))
                found=[]
                for root in live:
                    if root.archetype.lower()!=rows[0].archetype.lower():continue
                    suffix=rows[0].name[len(prefix):]
                    if suffix and not root.name.endswith(suffix):continue
                    live_prefix=root.name[:-len(suffix)] if suffix else root.name
                    offset=[a-b for a,b in zip(root.pos,rows[0].pos)]
                    actual={r.name:r for r in live}
                    wanted={r.name.replace(prefix,live_prefix):r for r in rows}
                    if not wanted.keys()<=actual.keys():continue
                    if not all((actual[n].archetype.lower(),actual[n].rotate,actual[n].loadout)==(r.archetype.lower(),r.rotate,r.loadout)
                        and all(abs(a+b-c)<.0001 for a,b,c in zip(r.pos,offset,actual[n].pos)) for n,r in wanted.items()):continue
                    found.append(dict(system=system,path=systems[system],prefix=live_prefix,offset=offset))
                if not found:errors.append(system+': no exact translation-only instance')
                instances.extend(found)
            config=dict(task='batch_'+re.sub(r'(?<!^)(?=[A-Z])','_',cls).lower(),template=path.relative_to(m.GAME).as_posix(),
                **{'class':cls},source_prefix=prefix,instances=instances,before=len(rows))
            if errors:
                excluded.append(dict(config,reason=errors));continue
            candidates.append(config)
    candidates.sort(key=lambda c:(not any(i['system']=='li_mnh' for i in c['instances']),-c['before']))
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'inventory.json').write_text(json.dumps(dict(candidates=candidates,excluded=excluded),indent=2))
    print(json.dumps(dict(candidates=[(c['class'],c['before'],[i['system'] for i in c['instances']]) for c in candidates],excluded=excluded),indent=2))
    return candidates

if __name__=='__main__':inventory()
