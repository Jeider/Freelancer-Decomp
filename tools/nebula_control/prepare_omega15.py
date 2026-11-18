"""Historical full-fog trial (rejected); explicit opt-in required. DATA uses DataFolder."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh'
VOLUME=ROOT/'out/graphics_settings/nebula_object_fog/full_volume'
GAME=Path('D:/Games/FL_MOD')
PY=GAME/'Assets/Pythonlancer'
STAGE=OUT/'stage'
FIELD='SOLAR/ASTEROIDS_MOD/GENERATED/om15_ast1_asteroids.ini'
GENERATOR='Assets/Pythonlancer/universe/content/asteroid_definition.py'
CONFIG='DATA_EXTRA/VOLUMETRIC/volumetric.ini'

def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def data_folder(root):
    spec=importlib.util.spec_from_file_location('omega15_data_folder',PY/'tools/data_folder.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module.DataFolder(root=root)

def sections(text):
    heads=list(re.finditer(r'^\[([^\]\r\n]+)\][ \t]*\r?$',text,re.M))
    return [(m[1].lower(),m.start(),heads[i+1].start() if i+1<len(heads) else len(text)) for i,m in enumerate(heads)]

def counts(text,kind):
    return [int(re.search(r'(?mi)^count\s*=\s*(\d+)',text[a:b])[1]) for n,a,b in sections(text) if n==kind]

def profile(text):
    block=(ROOT/'tools/nebula_control/omega15_volume.ini').read_text()
    begin='; BEGIN Omega-15 full volume trial';end='; END Omega-15 full volume trial'
    if begin in text:
        assert text.count(begin)==text.count(end)==1
        return text[:text.index(begin)]+block+text[text.index(end)+len(end):].lstrip('\r\n')
    assert 'om15_full_volume' not in text
    assert not re.search(r'(?mi)^file\s*=\s*gen_om15_(?:neb[123]|story_neb1)_nebula\s*$',text)
    return text.rstrip()+'\n\n'+block

def main():
    OUT.mkdir(parents=True,exist_ok=True);VOLUME.mkdir(parents=True,exist_ok=True)
    original=(GAME/'DATA'/FIELD).read_text()
    assert counts(original,'serverdynamicasteroids') in ([30,30,30],[60,60,60])
    updated=original
    for kind,a,b in reversed(sections(original)):
        if kind=='serverdynamicasteroids':
            body,n=re.subn(r'(?mi)^(count\s*=\s*)\d+',r'\g<1>60',original[a:b]);assert n==1
            updated=updated[:a]+body+updated[b:]
    assert counts(updated,'serverdynamicasteroids')==[60]*3
    assert counts(updated,'dynamicasteroids')==[0]*3
    # Only the count lines change, with all spawn geometry/speed/seed/loot intact.
    assert re.sub(r'(?mi)^count\s*=\s*\d+','count=<checked>',original)==re.sub(r'(?mi)^count\s*=\s*\d+','count=<checked>',updated)
    data_folder(STAGE).sync_data_file(FIELD,updated)
    raw=(GAME/GENERATOR).read_bytes()
    old=b"scale = 2 if str(system.NAME).lower() == 'sig8' else 1"
    new=b"scale = 2 if str(system.NAME).lower() in ('sig8', 'om15') else 1"
    assert raw.count(old)+raw.count(new)==1
    patched=raw.replace(old,new)
    dest=STAGE/GENERATOR;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(patched)
    # Execute only the two isolated conversion helpers, never the universe generator.
    tree=ast.parse(patched);nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('_convert_server_field','_server_world_field')]
    scope={'_SERVER_ASTEROID_SYSTEMS':('om15','sig8','rh_biz'),'_SERVER_ASTEROID_MODELS':tuple('ast_om15_normal_'+c for c in 'abc')}
    exec(compile(ast.Module(body=nodes,type_ignores=[]),GENERATOR,'exec'),scope)
    native='\n'.join('[DynamicAsteroids]\nasteroid = ast_om15_normal_'+c+'\ncount = 30\n' for c in 'abc')
    for name,want in [('om15',60),('sig8',60),('rh_biz',30)]:
        field=SimpleNamespace(system=SimpleNamespace(NAME=name,SYSTEMS_ROOT='SYSTEMS_MOD',IS_STORY=False))
        got=scope['_server_world_field'](field,native)
        assert counts(got,'serverdynamicasteroids')==[want]*3
        assert scope['_server_world_field'](field,got)==got
    for name,path in [('repository',ROOT/CONFIG),('installed',GAME/CONFIG)]:
        text=path.read_text(encoding='utf-8-sig');after=profile(text)
        if name=='repository':path.write_text(after,encoding='utf-8')
        else:
            dest=STAGE/CONFIG;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_text(after,encoding='utf-8')
    targets=['DATA/'+FIELD,GENERATOR,CONFIG]
    plan={'files':{n:{'before':digest(GAME/n),'after':digest(STAGE/n)} for n in targets},
          'physical_count_before':sum(counts(original,'serverdynamicasteroids')),'physical_count_after':180,
          'sources':{n:digest(ROOT/n) for n in ['tools/nebula_control/omega15_volume.ini','tools/physics/server_asteroid_rollout.py']},
          'data_folder_api':digest(PY/'tools/data_folder.py'),'generator_checks':'PASS; Omega-15 x2, Sig8 unchanged x2, other systems x1; idempotent',
          'game_launched':False}
    (OUT/'content_plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print('Prepared 90 -> 180 physical asteroids; generator verified; isolated full-volume profile; live game unchanged')

if __name__=='__main__':
    if '--full-volume-trial' not in sys.argv:
        raise SystemExit('Full-volume trial was reverted. Re-enable only deliberately with --full-volume-trial.')
    main()
