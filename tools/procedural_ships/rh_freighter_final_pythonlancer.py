"""Stage/verify source-only integration; never installs models or writes live DATA."""
import argparse,difflib,hashlib,importlib.abc,importlib.util,json,re,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/ship_design/rh_freighter/rh_pir_freighter'
PY=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
STAGE=OUT/'pythonlancer'
TPL='templates/hardcoded_inis/shiparch/playerships/'
def sha(b):return hashlib.sha256(b).hexdigest()
def save(path,text):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text,encoding='utf8',newline='\n')

def prepare():
    build=json.loads((OUT/'build.json').read_text());updates={}
    text=(PY/'world/ship.py').read_text(encoding='utf8')
    assert 'class PirateHumpback(Humpback):\n    SHIPARCH_TEMPLATE' not in text
    text=text.replace('class PirateHumpback(Humpback):',"class PirateHumpback(Humpback):\n    SHIPARCH_TEMPLATE = 'rh_pir_freighter'",1)
    updates['world/ship.py']=text
    text=(PY/(TPL+'rh_freighter.ini')).read_text(encoding='utf8')
    text=text.replace(';RH_SHIP','; Accepted Q13 pirate freighter. Source-only integration; assets installed by the user.')
    text=text.replace('LODranges = 0, 1000, 5000, 10000','LODranges = 0, 250, 750, 10000')
    text=text.replace('rh{{ prefix }}_','rh_pir_')
    if not (OUT/'lod_material_handoff.json').exists():
        text=text.replace('material_library = fx\\envmapbasic.mat','material_library = ships\\rheinland\\rh_pir_freighter\\rh_pir_freighter_lods.mat\nmaterial_library = fx\\envmapbasic.mat')
    chunks=re.split(r'(?m)(?=^\[CollisionGroup\])',text);changed=[]
    for i,block in enumerate(chunks):
        for zone in build['damage']:
            if re.search(r'(?m)^obj = '+re.escape(zone['part'])+r'\s*$',block):
                block=re.sub(r'(?m)^dmg_hp = .*$', 'dmg_hp = '+zone['hardpoint'],block)
                block=re.sub(r'(?m)^dmg_obj = .*$', 'dmg_obj = '+zone['archetype'],block);changed.append(zone['part'])
        chunks[i]=block
    assert len(changed)==4
    updates[TPL+'rh_pir_freighter.ini']=''.join(chunks)
    manifest={};diff=[]
    for rel,text in updates.items():
        path=PY/rel;old=path.read_bytes() if path.exists() else None;save(STAGE/rel,text)
        manifest[rel]=dict(before=sha(old) if old is not None else None,after=sha((STAGE/rel).read_bytes()))
        diff+=list(difflib.unified_diff(old.decode('utf8').splitlines(True) if old else [],text.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    save(OUT/'pythonlancer.patch',''.join(diff));save(OUT/'source_changes.json',json.dumps(manifest,indent=2))

class Overlay(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path,target=None):
        file=STAGE/(fullname.replace('.','/')+'.py')
        if file.is_file():return importlib.util.spec_from_file_location(fullname,file)

def render(mode):
    sys.path.insert(0,str(PY))
    if mode=='staged':sys.meta_path.insert(0,Overlay())
    from types import SimpleNamespace
    from managers.ids import IDsManager
    from managers.jinja_manager import JinjaTemplateManager
    from managers.shiparch import ShiparchManagerV2
    from tools.data_folder import DataFolder
    from jinja2 import ChoiceLoader,FileSystemLoader
    core=SimpleNamespace(write=False,build_folder=None,misc_equip=None);core.ids=IDsManager(core);core.tpl_manager=JinjaTemplateManager()
    directories=([STAGE/'templates'] if mode=='staged' else [])+[PY/'templates']
    core.tpl_manager.environment.loader=ChoiceLoader([FileSystemLoader(str(p)) for p in directories])
    # Block all accidental DATA output during construction, including new methods.
    def forbidden(*a,**kw):raise AssertionError('Live DATA output is forbidden in this source-only review')
    original=DataFolder.sync_data_file;DataFolder.sync_data_file=forbidden
    manager=ShiparchManagerV2(core)
    for ship in manager.ships:ship.used=True
    content=manager.get_shiparch_content();DataFolder.sync_data_file=original
    # Even draft DATA output uses the single required API, with an explicit safe root.
    stage=OUT/'review_data'/mode;folder=DataFolder(root=stage)
    dest=folder.sync_data_file('SHIPS/shiparch.ini',content)
    print('READ-ONLY GENERATION',mode,len(content),dest)

def blocks(text):
    result={};current=None
    for b in re.split(r'(?m)(?=^\[)',text):
        if b.startswith('[Ship]'):
            current=re.search(r'(?m)^nickname\s*=\s*(.+)$',b)[1].strip();result[current]=b
        elif b.startswith('[CollisionGroup]') and current:result[current]+=b
        else:current=None
    return result

def check():
    a=(OUT/'review_data/baseline/DATA/SHIPS/shiparch.ini').read_text(encoding='utf8')
    b=(OUT/'review_data/staged/DATA/SHIPS/shiparch.ini').read_text(encoding='utf8')
    old,new=blocks(a),blocks(b);assert old.keys()==new.keys()
    normalize=lambda block:[s.split(';',1)[0].strip() for s in block.splitlines() if s.split(';',1)[0].strip()]
    changed=[k for k in old if normalize(old[k])!=normalize(new[k])];assert changed==['rh_freighter_pir'],changed
    block=new[changed[0]];build=json.loads((OUT/'build.json').read_text())
    simples={}
    for section in re.split(r'(?m)(?=^\[)',b):
        if section.startswith('[Simple]'):
            nick=re.search(r'(?m)^nickname\s*=\s*(.+)$',section)[1].strip();assert nick not in simples,nick;simples[nick]=section
    for zone in build['damage']:
        assert 'dmg_hp = '+zone['hardpoint'] in block
        assert 'dmg_obj = '+zone['archetype'] in block
        simple=simples[zone['archetype']]
        assert zone['file'].lower() in simple.lower()
        assert 'rh_pir_playerships.mat' in simple
    assert 'group_dmg_' not in block
    before=[line for line in old[changed[0]].splitlines() if line.startswith(('hit_pts','root_health_proxy','type =','mass ='))]
    after=[line for line in block.splitlines() if line.startswith(('hit_pts','root_health_proxy','type =','mass ='))]
    assert before==after
    save(OUT/'pythonlancer_check.json',json.dumps(dict(changed_ship=changed[0],unaffected_ships=len(old)-1,damage_zones=4,all_simple_references_resolve=True,balance_unchanged=True,data_synchronization_run=False),indent=2))
    save(OUT/'shiparch_review.ini',block)
    print('PYTHONLANCER PASS',changed,len(old)-1,'other ships unchanged')

def apply():
    # Explicit source-only allowlist. This command cannot deploy ship assets.
    manifest=json.loads((OUT/'source_changes.json').read_text());allowed={'world/ship.py',TPL+'rh_pir_freighter.ini'}
    assert set(manifest)==allowed
    for rel,entry in manifest.items():
        src=STAGE/rel;dst=PY/rel;assert sha(src.read_bytes())==entry['after']
        current=sha(dst.read_bytes()) if dst.exists() else None
        assert current in (entry['before'],entry['after']),('Concurrent source edit',dst)
    for rel in manifest:
        dst=PY/rel;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((STAGE/rel).read_bytes())
        assert sha(dst.read_bytes())==manifest[rel]['after']
    save(OUT/'source_applied.json',json.dumps(dict(files=manifest,game_assets_copied=False,live_DATA_written=False),indent=2))
    print('APPLIED TWO SOURCE FILES ONLY')

if __name__=='__main__':
    command=sys.argv[1]
    if command=='prepare':prepare()
    elif command in ('baseline','staged'):render(command)
    elif command=='check':check()
    elif command=='apply':apply()
