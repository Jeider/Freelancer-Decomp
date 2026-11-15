"""Add only authoritative story/dev stations with verified live roundtrips."""
import json,re
import valensia_mega as m
from sync_story_dev import generator_static,semantic

out=m.REPO/'out/station_batch'
inventory=json.loads((out/'inventory.json').read_text())
census=json.loads((out/'static_inventory.json').read_text())
known={(i['path'].lower(),i['prefix']) for c in inventory['candidates'] for i in c['instances']}
for path in out.glob('*/installed.json'):
    config=json.loads((path.parent/'manifest.json').read_text())['config']
    known.update((i['path'].lower(),i['prefix']) for i in config['instances'])
direct=set(re.findall(r"DIRECT_TEMPLATE_NAME\s*=\s*'([^']+)'",(m.GAME/'Assets/Pythonlancer/universe/sirius.py').read_text(encoding='utf-8-sig')))
pending=[];deferred=[]
for row in census:
    if row['optimized'] or (row['path'].lower(),row['prefix']) in known:continue
    stem=row['system']+'_dev'
    dev=(m.GAME/row['path']).with_name(stem+'.ini')
    if stem not in direct or not dev.exists():
        deferred.append(dict(row,reason='not a verified StorySystem dev source'));continue
    try:
        assert semantic(generator_static(dev.read_bytes()))==semantic((m.GAME/row['path']).read_text(encoding='utf-8-sig'))
    except (AssertionError,UnicodeError):
        deferred.append(dict(row,reason='existing dev/live mismatch'));continue
    c=dict(task='batch_static_'+row['prefix'].lower(),static=True,template=dev.relative_to(m.GAME).as_posix(),
        **{'class':'Static_'+row['prefix']},source_prefix=row['prefix'],before=row['objects'],
        instances=[dict(system=row['system'],path=row['path'],prefix=row['prefix'],offset=[0,0,0])])
    pending.append(c)
inventory['candidates'].extend(pending)
(out/'inventory.json').write_text(json.dumps(inventory,indent=2))
(out/'static_deferred.json').write_text(json.dumps(deferred,indent=2))
print('Added static/dev stations:',[(c['class'],c['before']) for c in pending])
print('Other static groups:',[(r['prefix'],r['reason']) for r in deferred])
