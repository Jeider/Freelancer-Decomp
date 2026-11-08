"""Coverage and transactional checks for every declared shipdealer commandant."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
PROJECT=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
sys.path.insert(0,str(PROJECT))
sys.dont_write_bytecode=True
from managers.parking_commandants import plan,assign_registry,parse,one,session
from tools.data_folder import DataFolder
from story.rpg.script import RpgScript
from managers.rpg_scene import RpgSceneManager

OUT=ROOT/'src/obj/ship_parking/commandants'
registry=json.loads((PROJECT/'story/rpg/parking_commandants.json').read_text(encoding='utf-8'))
source=json.loads((OUT/'source_bases.json').read_text(encoding='utf-8'))
expected={r['base'] for r in source if r['shipdealer']}
assert expected=={r['base'] for r in registry['bases']}
assert len({r['group'] for r in registry['bases']})==len(expected)
costumes={(r['appearance']['head'],r['appearance']['body']) for r in registry['bases'] if not r.get('authored')}
assert len(costumes)==len(expected)-1 and ('br_captain_head','br_male_elite_body') not in costumes
folder=DataFolder(root=PROJECT.parent.parent)
files,scripts,report=plan(PROJECT,folder,registry)
assert len(report)==len(expected)
room_paths=set()
for base in report:
    assert base['parking_rooms'],base['base']
    for room in base['parking_rooms']:
        path=room['file']; room_paths.add(path.lower())
        actual=parse(folder.data_path(path).read_bytes())
        assert sum(k=='hotspot' and one(r,'behavior').lower()=='startshippark'
                   for k,r in actual)==1,path
biz=next(r for r in report if r['base']=='rh_biz_01_base')
assert any(r['room'].lower()=='shipdealer' for r in biz['parking_rooms'])
assert all(r.get('authored') or r['voiced']==len(scripts[r['group']]['fragments']) for r in report)
assert len({data['fragments'][0]['en'] for data in scripts.values()})==len(scripts)
for group,data in scripts.items():
    script=RpgScript(data)
    generated,catalogs=RpgSceneManager(PROJECT,script).plan(('en',))
    for path,content in generated.items(): assert folder.data_path(path).read_bytes()==content,path
    for row in catalogs['en']['fragments']:
        assert row['scene_seconds']>=row['speech_seconds']>0
    if data['vendor_posture']=='sit':
        assert b'RpgVendor"},{animation="Sc_MLBODY_CHRB_IDLE' in session(script)
        for path,content in generated.items():
            if '/gestures/vendor_' in path:
                assert b'_STND_' not in content and b'_CHRB_' in content
for path,content in files.items(): assert folder.data_path(path).read_bytes()==content,path
catalog={one(r,'base'):r for k,r in parse(folder.data_path('RPG/parking_contacts.ini').read_bytes()) if k=='rpgcontact'}
assert expected<=set(catalog)
# The universe hook reuses group IDs and never adds a duplicate seller/catalog row.
fresh=assign_registry(PROJECT,[{k:v for k,v in r.items() if k in ('base','system','faction','name_ru','name_en','locked')}
                               for r in registry['bases']])
assert {r['base']:r['group'] for r in fresh['bases']}=={r['base']:r['group'] for r in registry['bases']}
# Exercise the central writer's rollback after the second write actually happens.
with tempfile.TemporaryDirectory(dir=OUT) as temporary:
    class FailingFolder(DataFolder):
        count=0
        def sync_data_file(self,path,content):
            result=super().sync_data_file(path,content)
            self.count+=1
            if self.count==2: raise RuntimeError('injected write failure')
            return result
    local=FailingFolder(root=Path(temporary)/'game')
    DataFolder.sync_data_file(local,'RPG/ship_parking.ini',b'original')
    try:
        local.sync_parking_commandants({'RPG/ship_parking.ini':b'new','RPG/parking/test_base.ini':b'new'},Path(temporary)/'backup')
    except RuntimeError: pass
    else: raise AssertionError('Expected injected failure')
    assert local.data_path('RPG/ship_parking.ini').read_bytes()==b'original'
    assert not local.data_path('RPG/parking/test_base.ini').exists()
    try: local.sync_parking_commandants({'../escape.ini':b'bad'},Path(temporary)/'bad')
    except ValueError: pass
    else: raise AssertionError('Expected confined DATA paths')
print(f'PASS: {len(expected)}/{len(expected)} source shipdealers covered; parking in {len(room_paths)} actual room files; unique costumes/scripts, complete English audio/THN, seated poses, stable IDs and DATA rollback')
