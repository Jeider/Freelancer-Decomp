"""Explicitly authorized Q13 installation; never launches the game or rewrites live shiparch."""
import difflib,hashlib,importlib.abc,importlib.util,json,re,sys,shutil
from pathlib import Path
from types import SimpleNamespace
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/ship_design/rh_freighter/rh_pir_freighter'
WORK=OUT/'integration'
STAGE=WORK/'pythonlancer'
PY=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
GAME=PY.parents[1]
BASE='ships/rheinland/rh_pir_freighter/'
ASSET_REL='assets/'+BASE
TPL='templates/hardcoded_inis/shiparch/playerships/rh_pir_freighter.ini'
def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf8'))
def save(p,s):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s if isinstance(s,str) else json.dumps(s,ensure_ascii=False,indent=2),encoding='utf8',newline='\n')
def checked(root,rel):
    root=root.resolve();p=(root/rel).resolve()
    assert p.is_relative_to(root) and p!=root,('Path outside task',p)
    # Never clean through junctions/symlinks.
    current=p
    while current!=root:
        if current.exists():assert not getattr(current.stat(follow_symlinks=False),'st_file_attributes',0)&0x400,('Reparse point',current)
        current=current.parent
    return p

API='''
    # BEGIN RH PIR FREIGHTER ASSET OUTPUT
    def sync_rh_pir_freighter(self, files=None):
        """Q13 ship and four surviving damage replacements; shared MAT stays user-owned.

        Normal builds load canonical source assets. Explicit payloads also serve
        staging and rollback. This entry point never writes a MAT or shiparch.ini.
        """
        import hashlib
        base = 'ships/rheinland/rh_pir_freighter/'
        allowed = {'rh_pir_freighter.cmp', 'rh_pir_freighter.sur'}
        for zone in ('port_engine', 'starboard_engine', 'port_side_panel', 'starboard_side_panel'):
            for extension in ('.3db', '.sur'):
                allowed.add('rh_pir_freighter_dmg_' + zone + extension)
        if files is None:
            source = pathlib.Path(__file__).resolve().parents[1] / 'assets' / base
            manifest = json.loads((source / 'manifest.json').read_text(encoding='utf-8'))
            if set(manifest['files']) != allowed:
                raise ValueError('Incomplete Q13 source asset manifest')
            files = {}
            for name, entry in manifest['files'].items():
                payload = (source / name).read_bytes()
                if hashlib.sha256(payload).hexdigest() != entry['sha256']:
                    raise ValueError('Q13 source asset hash mismatch: ' + name)
                files[base + name] = payload
        for name, payload in files.items():
            if name not in {base + item for item in allowed}:
                raise ValueError('Unexpected Q13 target: ' + name)
            if payload is not None and not isinstance(payload, bytes):
                raise TypeError('Q13 payload must be bytes or None')
            self.data_path(name)
        for name, payload in files.items():
            if payload is None:
                self.remove_data_file(name)
            else:
                self.sync_data_file(name, payload)
    # END RH PIR FREIGHTER ASSET OUTPUT
'''

DOC='''# RH pirate freighter Q13

The user explicitly authorized this ship installation on 18 November 2026,
including continuing while the game is running; the user restarts it themselves.
This exception does not authorize future ship installations implicitly.

PirateHumpback uses the rh_pir_freighter template; nickname remains rh_freighter_pir.
The four CollisionGroups use unique DpRPF_* receiving points and existing pirate
Simple archetypes for the new damaged engines and torn panels. No flying debris caps.
The source assets are under assets/ships/rheinland/rh_pir_freighter with SHA256 manifest.
ShiparchManagerV2 publishes them through DataFolder.sync_rh_pir_freighter during
normal write=True builds, before writing shiparch.ini. write=False stays read-only.
The initial installation does not generate or overwrite active shiparch.ini.

LOD material handoff: rh_pir_freighter_projection_lod, texture
rh_pir_freighter_projection_lod.tga, DXT1 2048x2048 with 12 mips.
The user merges these into rh_pir_playerships.mat. Preserve these external names.
Do not ship, copy, overwrite or offer another LOD MAT in subsequent revisions.
The one-time authoring handoff is in the workspace ship's assets/rh_pir_freighter_lods.mat.
The merge is user-owned and is not claimed complete by this integration.
The template now uses the shared MAT only, plus envmapbasic.
'''

def prepare():
    assert shutil.disk_usage(ROOT).free>1024**3
    manifest=read(OUT/'assets/manifest.json');files={n:e for n,e in manifest['files'].items() if not n.endswith('.mat')};assert len(files)==10
    for n,e in files.items():assert sha((OUT/'assets'/n).read_bytes())==e['sha256'],n
    user=read(OUT/'panel_damage/acceptance.json')['accepted_assets_sha256']
    assert all(files[n]['sha256']==h for n,h in user.items())
    world=(PY/'world/ship.py').read_text(encoding='utf8')
    assert "class PirateHumpback(Humpback):\n    SHIPARCH_TEMPLATE = 'rh_pir_freighter'" in world
    updates={}
    api=(PY/'tools/data_folder.py').read_text(encoding='utf8');assert 'def sync_rh_pir_freighter(' not in api
    updates['tools/data_folder.py']=api.rstrip()+'\n'+API
    manager=(PY/'managers/shiparch.py').read_text(encoding='utf8')
    assert manager.count('        data_folder.sync_rh_pir_elite()')==1
    updates['managers/shiparch.py']=manager.replace('        data_folder.sync_rh_pir_elite()','        data_folder.sync_rh_pir_elite()\n        data_folder.sync_rh_pir_freighter()',1)
    template=(PY/TPL).read_text(encoding='utf8')
    template=template.replace('material_library = ships\\rheinland\\rh_pir_freighter\\rh_pir_freighter_lods.mat\n','')
    template=template.replace('; Accepted Q13 pirate freighter. Source-only integration; assets installed by the user.','; Accepted Q13. Model assets are synchronized through DataFolder; shared MAT is user-owned.')
    updates[TPL]=template;updates['docs/rh_pir_freighter.md']=DOC
    changes={};diff=[]
    for rel,text in updates.items():
        path=PY/rel;old=path.read_bytes() if path.exists() else None;save(STAGE/rel,text)
        changes[rel]=dict(before=sha(old) if old is not None else None,after=sha((STAGE/rel).read_bytes()))
        diff.extend(difflib.unified_diff(old.decode('utf8').splitlines(True) if old else [],text.splitlines(True),fromfile='a/'+rel,tofile='b/'+rel))
    for name,entry in files.items():
        p=STAGE/ASSET_REL/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((OUT/'assets'/name).read_bytes())
    save(STAGE/ASSET_REL/'manifest.json',dict(files=files,lod_material='rh_pir_freighter_projection_lod',lod_storage='user-owned rh_pir_playerships.mat',cmp_sha256=manifest['cmp_sha256']))
    for name in [*files,'manifest.json']:
        rel=ASSET_REL+name;p=PY/rel
        changes[rel]=dict(before=sha(p.read_bytes()) if p.exists() else None,after=sha((STAGE/rel).read_bytes()))
    save(WORK/'changes.json',dict(files=changes,assets=files,explicit_install_exception=True,live_shiparch_write=False,game_may_be_running=True))
    save(WORK/'pythonlancer.patch',''.join(diff))
    print('PREPARED',len(updates),'source changes and',len(files),'source assets')

class Overlay(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path,target=None):
        p=STAGE/(fullname.replace('.','/')+'.py')
        if p.is_file():return importlib.util.spec_from_file_location(fullname,p)

def render(mode):
    sys.path.insert(0,str(PY))
    if mode=='staged':sys.meta_path.insert(0,Overlay())
    from managers.ids import IDsManager
    from managers.jinja_manager import JinjaTemplateManager
    from managers.shiparch import ShiparchManagerV2
    from tools.data_folder import DataFolder
    from jinja2 import ChoiceLoader,FileSystemLoader
    core=SimpleNamespace(write=False,build_folder=None,misc_equip=None);core.ids=IDsManager(core);core.tpl_manager=JinjaTemplateManager()
    roots=([STAGE/'templates'] if mode=='staged' else [])+[PY/'templates']
    core.tpl_manager.environment.loader=ChoiceLoader([FileSystemLoader(str(p)) for p in roots])
    sync=DataFolder.sync_data_file
    def forbidden(*args,**kw):raise AssertionError('Read-only construction attempted a DATA write')
    DataFolder.sync_data_file=forbidden
    manager=ShiparchManagerV2(core)
    for ship in manager.ships:ship.used=True
    content=manager.get_shiparch_content();DataFolder.sync_data_file=sync
    folder=DataFolder(root=WORK/'validation'/mode);folder.sync_data_file('SHIPS/shiparch.ini',content)
    if mode!='baseline':
        # Invoke the exact normal-build path against an explicit workspace root.
        # Other writers are intercepted so no unrelated model is staged.
        manager.core.write=True;manager.core.build_folder=None
        module=sys.modules[ShiparchManagerV2.__module__];module.DataFolder=lambda **kw:folder
        calls=[];native_sync=folder.sync_rh_pir_freighter
        folder.sync_rh_pir_elite=lambda:calls.append('elite')
        def own_sync():calls.append('freighter');native_sync()
        folder.sync_rh_pir_freighter=own_sync
        folder.sync_shiparch_alt=lambda value:(calls.append('shiparch'),folder.sync_data_file('SHIPS/shiparch.ini',value))
        manager.sync_data();assert calls==['elite','freighter','shiparch'],calls
        files=read(WORK/'changes.json')['assets']
        for name,e in files.items():assert sha(folder.data_path(BASE+name).read_bytes())==e['sha256']
        assert not list(folder.data_path(BASE).glob('*.mat'))
    print('RENDERED AND CHECKED',mode)

def check():
    sys.path.insert(0,str(Path(__file__).parent));from rh_freighter_final_pythonlancer import blocks
    baseline=(WORK/'validation/baseline/DATA/SHIPS/shiparch.ini').read_text(encoding='utf8')
    staged=(WORK/'validation/staged/DATA/SHIPS/shiparch.ini').read_text(encoding='utf8')
    a,b=blocks(baseline),blocks(staged);assert a.keys()==b.keys()
    normalize=lambda s:[l.strip() for l in s.splitlines() if l.strip() and not l.strip().startswith(';')]
    assert [n for n in a if normalize(a[n])!=normalize(b[n])]==['rh_freighter_pir']
    old=[l for l in normalize(a['rh_freighter_pir']) if 'rh_pir_freighter_lods.mat' not in l]
    assert old==normalize(b['rh_freighter_pir'])
    simple={}
    for s in re.split(r'(?m)(?=^\[)',staged):
        if s.startswith('[Simple]'):simple[re.search(r'(?m)^nickname\s*=\s*(.+)$',s)[1].strip()]=s
    for zone in read(OUT/'build.json')['damage']:
        assert 'dmg_hp = '+zone['hardpoint'] in b['rh_freighter_pir']
        assert zone['file'].lower() in simple[zone['archetype']].lower()
        assert 'rh_pir_playerships.mat' in simple[zone['archetype']]
    assert 'group_dmg_' not in b['rh_freighter_pir']
    save(WORK/'shiparch_review.ini',b['rh_freighter_pir'])
    save(WORK/'check.json',dict(unaffected_ships=len(a)-1,damage_groups=4,assets=10,read_only_construction=True,normal_build_sync_verified=True,shared_mat_only=True,live_data_written=False))
    print('INTEGRATION PASS: 10 assets, four damage groups, 152 other ships unchanged')

def apply():
    assert read(WORK/'check.json')['normal_build_sync_verified']
    spec=importlib.util.spec_from_file_location('q13_data_output',STAGE/'tools/data_folder.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    DataFolder=mod.DataFolder;game=DataFolder(root=GAME)
    manifest=read(WORK/'changes.json');payloads={};before={}
    for rel,e in manifest['files'].items():
        p=checked(PY,rel);old=p.read_bytes() if p.exists() else None
        assert (sha(old) if old is not None else None)==e['before'],('Concurrent source change',rel)
        data=checked(STAGE,rel).read_bytes();assert sha(data)==e['after']
        before[rel]=old;payloads[rel]=data
    data={BASE+n:payloads[ASSET_REL+n] for n in manifest['assets']}
    olddata={name:game.data_path(name).read_bytes() if game.data_path(name).exists() else None for name in data}
    # This one-time exception explicitly allows updating models while the user plays.
    untouched=[GAME/'DATA/SHIPS/shiparch.ini',GAME/'DATA/ships/rheinland/rh_pir_playerships.mat']
    unchanged={str(p):sha(p.read_bytes()) for p in untouched}
    backup=WORK/'transaction';backup_api=DataFolder(root=backup)
    for rel,old in before.items():
        if old is not None:
            p=checked(backup,'source/'+rel);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(old)
    backup_api.sync_rh_pir_freighter({n:b for n,b in olddata.items() if b is not None})
    touched=[];data_started=False
    try:
        for rel,value in payloads.items():
            p=checked(PY,rel);p.parent.mkdir(parents=True,exist_ok=True);touched.append(rel);p.write_bytes(value)
        data_started=True;game.sync_rh_pir_freighter(data)
        for rel,e in manifest['files'].items():assert sha(checked(PY,rel).read_bytes())==e['after']
        for rel,value in data.items():assert game.data_path(rel).read_bytes()==value
        assert {str(p):sha(p.read_bytes()) for p in untouched}==unchanged
    except BaseException:
        if data_started:game.sync_rh_pir_freighter(olddata)
        for rel in reversed(touched):
            p=checked(PY,rel);old=before[rel]
            if old is None:p.unlink(missing_ok=True)
            else:p.write_bytes(old)
        raise
    save(WORK/'installation.json',dict(source_files={r:sha(b) for r,b in payloads.items()},game_assets={r:sha(b) for r,b in data.items()},unchanged=unchanged,active_shiparch_written=False,installed=True,game_launched=False,user_authorized_running_game=True,lod_mat_not_installed=True))
    # Delete only verified transaction files; no recursive traversal or external cleanup.
    for rel,old in before.items():
        if old is not None:
            p=checked(backup,'source/'+rel);assert p.read_bytes()==old;p.unlink()
    for rel,old in olddata.items():
        if old is not None:
            p=checked(backup,'DATA/'+rel);assert p.read_bytes()==old;backup_api.remove_data_file(rel)
    print('INSTALLED 10 MODEL FILES AND PYTHONLANCER SOURCES; SHARED MAT AND LIVE SHIPARCH UNCHANGED')

def cleanup():
    report=read(WORK/'installation.json');manifest=read(WORK/'changes.json')
    for rel,h in report['game_assets'].items():assert sha((GAME/'DATA'/rel).read_bytes())==h
    for rel,h in report['source_files'].items():assert sha((PY/rel).read_bytes())==h
    for name in [*manifest['assets'],'manifest.json']:
        rel=ASSET_REL+name;p=checked(STAGE,rel)
        if p.exists():assert sha(p.read_bytes())==report['source_files'][rel];p.unlink()
    # Validation DATA output is deleted through the same module's API.
    spec=importlib.util.spec_from_file_location('q13_cleanup_api',STAGE/'tools/data_folder.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    for mode in ('staged','installed'):
        root=checked(WORK,'validation/'+mode);folder=mod.DataFolder(root=root)
        for name,e in manifest['assets'].items():
            p=checked(root,'DATA/'+BASE+name)
            if p.exists():assert sha(p.read_bytes())==e['sha256'];folder.remove_data_file(BASE+name)
    save(WORK/'cleanup.json',dict(installed_files_verified=True,staging_binary_copies_removed=True,rollback_binary_copies_removed=True,authoring_and_source_assets_preserved=True))
    print('CLEANED redundant staging/rollback binaries; kept authoring and canonical Pythonlancer sources')

if __name__=='__main__':
    command=sys.argv[1]
    if command=='prepare':prepare()
    elif command in ('baseline','staged','installed'):render(command)
    elif command=='check':check()
    elif command=='apply':apply()
    elif command=='cleanup':cleanup()
