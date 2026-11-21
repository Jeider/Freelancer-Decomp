"""Fighter source integration; model installation and live DATA remain separate."""
import difflib,json,re,sys,hashlib
from pathlib import Path
sys.dont_write_bytecode=True
import rh_freighter_final_pythonlancer as shared
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/ship_design/rh_fighter/rh_pir_fighter'
PY=shared.PY;STAGE=OUT/'pythonlancer';TPL=shared.TPL
save,sha=shared.save,shared.sha

def prepare():
    build=json.loads((OUT/'build.json').read_text());updates={};rel='world/ship.py';text=(PY/rel).read_text(encoding='utf8')
    start=text.index('class PirateBanshee(Banshee):');end=text.index('\nclass ',start+1);block=text[start:end]
    assert 'SHIPARCH_TEMPLATE' not in block
    block=block.replace('class PirateBanshee(Banshee):',"class PirateBanshee(Banshee):\n    SHIPARCH_TEMPLATE = 'rh_pir_fighter'\n    ENGINE_TYPE = ENGINE_DOUBLE_SAME")
    block=block.replace("MAIN_WEAPONS = ['HpTorpedo01', 'HpWeapon01', 'HpWeapon02', 'HpWeapon03', 'HpWeapon04']", "MAIN_WEAPONS = ['HpTorpedo01', 'HpWeapon01', 'HpWeapon02', 'HpWeapon03', 'HpWeapon04', 'HpWeapon05', 'HpWeapon06']")
    updates[rel]=text[:start]+block+text[end:]
    template=(PY/(TPL+'rh_fighter.ini')).read_text(encoding='utf8').split('[CollisionGroup]')[0]
    template=template.replace('rh{{ prefix }}_','rh_pir_').replace('LODranges = 0, 1000, 5000, 10000','LODranges = 0, 180, 550, 10000').replace('num_exhaust_nozzles = 1','num_exhaust_nozzles = 2')
    template=template.replace('material_library = fx\\envmapbasic.mat','material_library = ships\\rheinland\\rh_pir_fighter\\rh_pir_fighter_lods.mat\nmaterial_library = fx\\envmapbasic.mat')
    for zone in build['damage']:
        key=zone['zone'];wing=key.endswith('wing');side='Port' if key.startswith('port') else 'Starboard';parttype=side+('_Wing' if wing else '_Engine')
        prop=('wing' if wing else 'eng')+('1' if side=='Port' else '2')
        template+='\n[CollisionGroup]\nobj = '+zone['part']+'\nseparable = true\nparent_impulse = '+('60' if wing else '250')+'\nchild_impulse = '+('30' if wing else '7')+'\ndebris_type = debris_small_ship\ndmg_hp = '+zone['hardpoint']+'\ndmg_obj = '+zone['archetype']+'\nseparation_explosion = explosion_small_ship_breakoff\nmass = 5\ntype = '+parttype+'\n{{ rf.'+prop+' }}\n'
    updates[TPL+'rh_pir_fighter.ini']='; F14/F01 production fighter. Assets installed by the user.\n'+template
    rel='templates/hardcoded_inis/shiparch/simples/pir_nmd.ini';text=(PY/rel).read_text(encoding='utf8')
    pattern=r'\[Simple\]\nnickname = rh\{\{ prefix \}\}_fighter_dmg_engine_cap\n.*?(?=\n\s*\[Simple\])'
    match=re.search(pattern,text,re.S);assert match
    engine=''
    for z in build['damage']:
        if not z['zone'].endswith('engine'):continue
        engine+='[Simple]\nnickname = '+z['archetype']+'\nDA_archetype = ships\\rheinland\\rh_pir_fighter\\'+z['file']+'\nmaterial_library = ships\\rheinland\\rh_pir_playerships.mat\nmass = 5\nLODranges = 0, 180, 550, 10000\n\n'
    text=text[:match.start()]+"{% if prefix == '_pir' %}\n"+engine+'{% else %}\n'+match[0]+'\n{% endif %}\n'+text[match.end():]
    for side in ('port','starboard'):
        pattern=r'(\[Simple\]\nnickname = rh\{\{ prefix \}\}_fighter_dmg_'+side+r'_wing_cap\n.*?LODranges = )[^\n]+'
        text,count=re.subn(pattern,lambda m:m[1]+"{% if prefix == '_pir' %}0, 180, 550, 10000{% else %}0, 1000, 2000{% endif %}",text,flags=re.S)
        assert count==1
    updates[rel]=text
    manifest={};diff=[]
    for rel,text in updates.items():
        source=PY/rel;old=source.read_bytes() if source.exists() else None;save(STAGE/rel,text)
        manifest[rel]=dict(before=sha(old) if old else None,after=sha((STAGE/rel).read_bytes()))
        diff+=list(difflib.unified_diff(old.decode('utf8').splitlines(True) if old else [],text.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    save(OUT/'source_changes.json',json.dumps(manifest,indent=2));save(OUT/'pythonlancer.patch',''.join(diff))

def check():
    a=(OUT/'review_data/baseline/DATA/SHIPS/shiparch.ini').read_text(encoding='utf8');b=(OUT/'review_data/staged/DATA/SHIPS/shiparch.ini').read_text(encoding='utf8')
    old,new=shared.blocks(a),shared.blocks(b);assert old.keys()==new.keys()
    norm=lambda s:[v.split(';',1)[0].strip() for v in s.splitlines() if v.split(';',1)[0].strip()]
    changed=[k for k in old if norm(old[k])!=norm(new[k])];assert changed==['rh_fighter_pir'],changed
    block=new[changed[0]];simples={}
    for s in re.split(r'(?m)(?=^\[)',b):
        if s.startswith('[Simple]'):
            nick=re.search(r'(?m)^nickname\s*=\s*(.+)$',s)[1].strip();assert nick not in simples;simples[nick]=s
    build=json.loads((OUT/'build.json').read_text())
    for z in build['damage']:
        assert 'dmg_hp = '+z['hardpoint'] in block and 'dmg_obj = '+z['archetype'] in block
        s=simples[z['archetype']];assert z['file'] in s and 'rh_pir_playerships.mat' in s
        assert 'LODranges = 0, 180, 550, 10000' in s and z['switches']==[0,180,550,10000]
    assert 'group_dmg_' not in block and 'rh_pir_fighter_dmg_engine_cap' not in simples
    assert 'HpWeapon05' in block and 'HpWeapon06' in block
    states=[]
    for rel,entry in json.loads((OUT/'source_changes.json').read_text()).items():
        p=PY/rel;current=sha(p.read_bytes()) if p.exists() else None
        assert current in (entry['before'],entry['after']),('Concurrent source edit',rel)
        states.append(current==entry['after'])
    assert all(states) or not any(states),'Source integration only partially applied'
    if all(states):
        actual=OUT/'review_data/applied/DATA/SHIPS/shiparch.ini'
        assert actual.read_bytes()==(OUT/'review_data/staged/DATA/SHIPS/shiparch.ini').read_bytes(),'Actual source generation differs from reviewed overlay'
    old_simples={re.search(r'(?m)^nickname\s*=\s*(.+)$',s)[1].strip():s for s in re.split(r'(?m)(?=^\[)',a) if s.startswith('[Simple]')}
    changed_simples=[key for key in old_simples.keys() & simples.keys() if norm(old_simples[key])!=norm(simples[key])]
    assert sorted(changed_simples)==['rh_pir_fighter_dmg_port_wing_cap','rh_pir_fighter_dmg_starboard_wing_cap'],changed_simples
    assert set(old_simples)-set(simples)=={'rh_pir_fighter_dmg_engine_cap'}
    assert set(simples)-set(old_simples)=={'rh_pir_fighter_dmg_port_engine_cap','rh_pir_fighter_dmg_starboard_engine_cap'}
    save(OUT/'shiparch_review.ini',block)
    save(OUT/'rh_pir_fighter_integration.ini',block+'\n\n'+''.join(simples[z['archetype']] for z in build['damage']))
    save(OUT/'pythonlancer_check.json',json.dumps(dict(cmp_sha256=build['cmp_sha256'],changed_ship=changed[0],unaffected_ships=len(old)-1,damage_zones=4,all_simple_references_resolve=True,
        damage_lods={z['zone']:z['lod_triangles'] for z in build['damage']},other_simples_unchanged=True,
        new_weapon_mounts=['HpWeapon05','HpWeapon06'],engine_class='ENGINE_DOUBLE_SAME',live_source_changed=all(states),applied_generation_matches_review=all(states),live_DATA_written=False),indent=2))
    print('STAGED PYTHONLANCER PASS',len(old)-1,'other ships unchanged')

def apply_sources():
    """Apply exactly the three reviewed source files. No DATA/model writes."""
    manifest=json.loads((OUT/'source_changes.json').read_text())
    allowed={'world/ship.py',TPL+'rh_pir_fighter.ini','templates/hardcoded_inis/shiparch/simples/pir_nmd.ini'}
    assert set(manifest)==allowed
    report=json.loads((OUT/'pythonlancer_check.json').read_text())
    assert report['damage_zones']==4 and report['unaffected_ships']==152 and report['other_simples_unchanged']
    live=PY.parents[1]/'DATA/SHIPS/shiparch.ini'
    live_hash=sha(live.read_bytes()) if live.exists() else None
    for rel,entry in manifest.items():
        dst=PY/rel;src=STAGE/rel
        assert dst.resolve().is_relative_to(PY.resolve()) and 'DATA' not in dst.relative_to(PY).parts
        assert sha(src.read_bytes())==entry['after']
        current=sha(dst.read_bytes()) if dst.exists() else None
        assert current in (entry['before'],entry['after']),('Concurrent source edit',dst)
    for rel,entry in manifest.items():
        dst=PY/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((STAGE/rel).read_bytes())
        assert sha(dst.read_bytes())==entry['after']
    assert (sha(live.read_bytes()) if live.exists() else None)==live_hash
    save(OUT/'source_applied.json',json.dumps(dict(files=manifest,live_shiparch_sha256=live_hash,game_assets_copied=False,live_DATA_written=False),indent=2))
    print('APPLIED THREE PYTHONLANCER SOURCE FILES; live DATA unchanged')

if __name__=='__main__':
    shared.OUT=OUT;shared.STAGE=STAGE
    if sys.argv[1]=='prepare':prepare()
    elif sys.argv[1] in ('baseline','staged','applied'):shared.render(sys.argv[1])
    elif sys.argv[1]=='check':check()
    elif sys.argv[1]=='apply-sources':apply_sources()
    else:raise SystemExit('Only prepare/baseline/staged/applied/check/apply-sources; ship deployment belongs to user')
