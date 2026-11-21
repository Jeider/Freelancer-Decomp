"""Read-only Pythonlancer integration review against the current shiparch V2.

All generated DATA goes through DataFolder to an explicit offline root. Source
files and live DATA are never updated by this tool.
"""
import hashlib
import difflib
import json
from pathlib import Path
import re
import sys
from types import SimpleNamespace

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/ship_design/rh_elite/rh_pir_elite/tail_rim/release'
PY=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
ASSETS=OUT/'assets'
TEMPLATE=Path('templates/hardcoded_inis/shiparch/simples/pir_nmd.ini')


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    sys.path.insert(0,str(PY))
    from managers.ids import IDsManager
    from managers.jinja_manager import JinjaTemplateManager
    from managers.shiparch import ShiparchManagerV2
    from tools.data_folder import DataFolder
    from jinja2 import FileSystemLoader,ChoiceLoader

    # Overlay only five pirate damage ranges. Retail/nomad instances use this
    # same template and must retain their original settings exactly.
    original=(PY/TEMPLATE).read_text(encoding='utf8')
    chunks=re.split(r'(?m)(?=^\[)',original)
    changed=[]
    for i,block in enumerate(chunks):
        match=re.search(r'^nickname = rh\{\{ prefix \}\}_elite_dmg_(port_wing|starboard_wing|tail|portengine|starengine)_cap$',block,re.M)
        if not match:continue
        assert 'LODranges = 0, 1000, 2000' in block
        chunks[i]=block.replace('LODranges = 0, 1000, 2000',
            "LODranges = {% if prefix == '_pir' %}0, 180, 550, 10000{% else %}0, 1000, 2000{% endif %}")
        changed.append(match[1])
    assert len(changed)==5
    staged=''.join(chunks)
    target=OUT/'pythonlancer'/TEMPLATE
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text(staged,encoding='utf8',newline='\n')
    patch=''.join(difflib.unified_diff(original.splitlines(True),staged.splitlines(True),
                                     fromfile='a/'+TEMPLATE.as_posix(),tofile='b/'+TEMPLATE.as_posix()))
    (OUT/'pythonlancer.patch').write_text(patch,encoding='utf8',newline='\n')
    (OUT/'pythonlancer_source_changes.json').write_text(json.dumps({TEMPLATE.as_posix():dict(before=sha(PY/TEMPLATE),after=sha(target))},indent=2)+'\n')

    core=SimpleNamespace(write=False,build_folder=None,misc_equip=None)
    core.ids=IDsManager(core);core.tpl_manager=JinjaTemplateManager()
    core.tpl_manager.environment.loader=FileSystemLoader(str(PY/'templates'))
    # Defence against accidental output during initialization, including future
    # API additions: no DataFolder may target a root outside this review.
    old_path=DataFolder.data_path
    offline=(OUT/'pythonlancer_review').resolve()
    def guarded(self,relative):
        result=old_path(self,relative)
        assert result.is_relative_to(offline),('Live DATA writes forbidden',result)
        return result
    DataFolder.data_path=guarded
    manager=ShiparchManagerV2(core)
    for ship in manager.ships:ship.used=True
    baseline=manager.get_shiparch_content()
    core.ids=IDsManager(core)
    core.tpl_manager.environment.loader=ChoiceLoader([FileSystemLoader(str(OUT/'pythonlancer/templates')),FileSystemLoader(str(PY/'templates'))])
    core.tpl_manager.environment.cache.clear()
    manager=ShiparchManagerV2(core)
    for ship in manager.ships:ship.used=True
    content=manager.get_shiparch_content()
    blocks=re.split(r'(?m)(?=^\[)',content)
    ship=None;groups=[];simples={};capture=False
    def values(block):
        v={}
        for line in block.splitlines():
            line=line.split(';',1)[0].strip()
            if '=' in line:
                k,x=line.split('=',1);v.setdefault(k.strip().lower(),[]).append(x.strip())
        return v
    for block in blocks:
        v=values(block)
        if block.startswith('[Ship]'):
            capture=v.get('nickname')==['rh_elite_pir']
            if capture:ship=block
        elif block.startswith('[CollisionGroup]') and capture:
            groups.append(block)
        elif block.startswith('[Simple]'):
            capture=False
            if v.get('nickname'):simples[v['nickname'][0].lower()]=block
        else:capture=False
    assert ship and len(groups)==5
    assert values(ship)['da_archetype']==[r'ships\rheinland\rh_pir_elite\rh_pir_elite.cmp']
    assert values(ship)['lodranges']==['0, 180, 550, 10000']
    expected={
        'rh_port_wing_lod1':('DpPort_Wing','rh_pir_elite_dmg_port_wing_cap','port_wing'),
        'rh_starboard_wing_lod1':('DpStarboard_Wing','rh_pir_elite_dmg_starboard_wing_cap','starboard_wing'),
        'rh_port_engine_lod1':('DpPort_Engine','rh_pir_elite_dmg_portengine_cap','port_engine'),
        'rh_starboard_engine_lod1':('DpStarboard_Engine','rh_pir_elite_dmg_starengine_cap','starboard_engine'),
        'rh_tail_lod1':('DpTail','rh_pir_elite_dmg_tail_cap','tail')}
    report=[];simpleblocks=[]
    for block in groups:
        v=values(block);hp,simple,zone=expected[v['obj'][0].lower()]
        assert v['dmg_hp'][0].lower()==hp.lower() and v['dmg_obj'][0].lower()==simple
        assert not any(k.startswith('group_dmg_') for k in v)
        sv=values(simples[simple]);filename='rh_pir_elite_dmg_'+zone+'.3db'
        assert sv['da_archetype'][0].lower()==(r'ships\rheinland\rh_pir_elite'+'\\'+filename).lower(), (simple,sv['da_archetype'],filename)
        assert r'ships\rheinland\rh_pir_playerships.mat' in [v.lower() for v in sv['material_library']]
        assert sv['lodranges']==['0, 180, 550, 10000']
        assert (ASSETS/filename).exists()
        simpleblocks.append(simples[simple]);report.append(dict(object=v['obj'][0],dmg_hp=hp,simple=simple,file=filename))
    ab=re.split(r'(?m)(?=^\[)',baseline)
    assert len(ab)==len(blocks)
    changed_blocks=[]
    for a,c in zip(ab,blocks):
        va,vc=values(a),values(c)
        if va==vc:continue
        nickname=vc['nickname'][0]
        assert nickname in {row['simple'] for row in report}, (nickname,{k:(va[k],vc.get(k)) for k in va if va[k]!=vc.get(k)})
        assert set(k for k in va if va[k]!=vc.get(k))=={'lodranges'}
        changed_blocks.append(nickname)
    assert len(changed_blocks)==5
    manifest=json.loads((ASSETS/'manifest.json').read_text())
    payload={}
    for filename,info in manifest['files'].items():
        path=ASSETS/filename;assert sha(path)==info['sha256']
        payload['ships/rheinland/rh_pir_elite/'+filename]=path.read_bytes()
    assert len(payload)==12 and not any(p.endswith('.mat') for p in payload)
    folder=DataFolder(root=offline)
    folder.sync_rh_pir_elite(payload)
    for relative,blob in payload.items():assert folder.data_path(relative).read_bytes()==blob
    folder.sync_data_file('SHIPS/shiparch.ini',content)
    (OUT/'shiparch_review.ini').write_text('; Generated review only; five pirate damage LOD ranges updated.\n\n'+ship+''.join(groups)+''.join(simpleblocks),encoding='utf8')
    # Do not keep another redundant set of binaries after this staging test.
    # Exact individually verified paths only; the original assets remain.
    for relative in payload:folder.remove_data_file(relative)
    guard=json.loads((OUT/'sources.json').read_text())['files']
    assert all(sha(Path(p))==h for p,h in guard.items())
    result=dict(ships_rendered=len(manager.ships),target='rh_elite_pir',bindings=report,
                damage_bindings_already_match=True,source_changes_required=True,
                source_patch_applied=False,changed_simple_lodranges=changed_blocks,
                ship_balance_and_lod_ranges_unchanged=True,all_other_generated_sections_unchanged=True,asset_api_verified=len(payload),
                redundant_staged_binaries_removed=True,game_DATA_unchanged=True,
                generated_shiparch=str(folder.data_path('SHIPS/shiparch.ini')),
                cmp_sha256=manifest['files']['rh_pir_elite.cmp']['sha256'])
    (OUT/'pythonlancer_check.json').write_text(json.dumps(result,indent=2)+'\n')
    assert sha(PY/TEMPLATE)==json.loads((OUT/'pythonlancer_source_changes.json').read_text())[TEMPLATE.as_posix()]['before']
    print('PYTHONLANCER: five pirate damage LOD ranges staged; all other sections identical; isolated DataFolder verified',flush=True)


if __name__=='__main__':main()
