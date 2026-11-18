"""Update canonical Pythonlancer SOURCE assets; never deploy to live DATA."""
import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/ship_design/rh_freighter/rh_pir_freighter/hold_damage'
REVIEW=OUT/'pythonlancer';PY=Path('D:/Games/FL_MOD/Assets/Pythonlancer')
BASE=Path('assets/ships/rheinland/rh_pir_freighter')
DATA_BASE='ships/rheinland/rh_pir_freighter/'
DOC=Path('docs/rh_pir_freighter.md')
def sha(payload):return hashlib.sha256(payload).hexdigest()
def read(path):return json.loads(path.read_text(encoding='utf8'))
def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf8')

def live_hashes():
    game=PY.parents[1];names=[game/'DATA/SHIPS/shiparch.ini',game/'DATA/ships/rheinland/rh_pir_playerships.mat']
    names+=list((game/'DATA'/DATA_BASE).glob('*.cmp'))+list((game/'DATA'/DATA_BASE).glob('*.sur'))+list((game/'DATA'/DATA_BASE).glob('*.3db'))
    return {str(p):sha(p.read_bytes()) for p in names}

def staged_check(payloads):
    spec=importlib.util.spec_from_file_location('rpf_source_data_folder',PY/'tools/data_folder.py')
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    root=(REVIEW/'staged_build').resolve();assert root.is_relative_to(ROOT.resolve())
    folder=mod.DataFolder(root=root);folder.sync_rh_pir_freighter({DATA_BASE+n:p for n,p in payloads.items()})
    result={}
    for name,payload in payloads.items():
        path=folder.data_path(DATA_BASE+name);assert path.is_relative_to(root)
        assert path.read_bytes()==payload;result[name]=sha(payload)
    assert not folder.data_path('SHIPS/shiparch.ini').exists()
    return result

def prepare():
    REVIEW.mkdir(exist_ok=True)
    delivery=read(OUT/'delivery_manifest.json');validation=read(OUT/'validation.json');motion=read(OUT/'motion_check.json')
    assert validation['cmp_sha256']==motion['cmp_sha256']==delivery['files']['rh_pir_freighter.cmp']['sha256']
    manifest=read(PY/BASE/'manifest.json');payloads={};changes={}
    for name,entry in manifest['files'].items():
        old=(PY/BASE/name).read_bytes();assert sha(old)==entry['sha256'],('User changed source',name)
        new=(OUT/name).read_bytes() if name in delivery['files'] else old
        if name in delivery['files']:
            assert sha(new)==delivery['files'][name]['sha256'];changes[str(BASE/name)]=dict(before=sha(old),after=sha(new),from_file=str(OUT/name))
        payloads[name]=new;manifest['files'][name]=dict(bytes=len(new),sha256=sha(new))
    assert len(changes)==5
    manifest.update(cmp_sha256=validation['cmp_sha256'],revision='hold_damage',lod_triangles=validation['counts'],
                    authoring_report=str(OUT/'README.md'))
    save(REVIEW/'manifest.json',manifest)
    changes[str(BASE/'manifest.json')]=dict(before=sha((PY/BASE/'manifest.json').read_bytes()),after=sha((REVIEW/'manifest.json').read_bytes()),from_file=str(REVIEW/'manifest.json'))
    old=(PY/DOC).read_bytes();text=old.decode('utf8')
    text+='''\n## Latest source revision: narrow hold and deep panel wounds\n\nCanonical source assets now use hold_damage: 26961 / 1776 / 494 triangles.\nThe cargo walls are inside the retracted btn paths; floor Y=0.355 is unchanged.\nBoth panel caps have recessed internal structure; ten light hardpoints moved.\nThe 398-edge HUD wire, other hardpoints and native animations are preserved.\nOnly five binary source assets and the hash manifest were updated. Existing\nshiparch bindings, main SUR, engine wounds and the user's shared MAT remain.\nDeployment belongs to the user. This source update does not synchronize DATA.\n'''
    (REVIEW/'rh_pir_freighter.md').write_text(text,encoding='utf8',newline='\n')
    changes[str(DOC)]=dict(before=sha(old),after=sha((REVIEW/'rh_pir_freighter.md').read_bytes()),from_file=str(REVIEW/'rh_pir_freighter.md'))
    before=live_hashes();staged=staged_check(payloads);assert live_hashes()==before
    save(REVIEW/'plan.json',dict(changes=changes,staged_hashes=staged,live_hashes=before,
        source_only=True,shiparch_changes=False,mat_changes=False))
    print('PREPARED: five source assets, manifest, source documentation; staged DataFolder check passed')

def apply():
    plan=read(REVIEW/'plan.json');changes=plan['changes'];allowed={str(DOC),str(BASE/'manifest.json')}|{str(BASE/n) for n in read(OUT/'delivery_manifest.json')['files']}
    assert set(changes)==allowed
    # Validate every source and destination before any write. Transaction backup
    # is in memory only, not another retained binary copy.
    snapshots={};updates={};guard=live_hashes()
    for rel,c in changes.items():
        dst=(PY/rel).resolve();assert dst.is_relative_to(PY.resolve()) and not dst.is_relative_to((PY.parents[1]/'DATA').resolve())
        old=dst.read_bytes();assert sha(old) in (c['before'],c['after']),('Concurrent source change',rel)
        payload=Path(c['from_file']).read_bytes();assert sha(payload)==c['after']
        snapshots[dst]=old;updates[dst]=payload
    try:
        for dst,payload in updates.items():dst.write_bytes(payload)
        for dst,payload in updates.items():assert dst.read_bytes()==payload
        manifest=read(PY/BASE/'manifest.json');payloads={}
        for name,entry in manifest['files'].items():
            payload=(PY/BASE/name).read_bytes();assert sha(payload)==entry['sha256'];payloads[name]=payload
        staged_check(payloads);assert live_hashes()==guard
    except BaseException:
        for dst,payload in snapshots.items():dst.write_bytes(payload)
        raise
    save(REVIEW/'applied.json',dict(source_files={str(p):sha(v) for p,v in updates.items()},
        all_ten_source_hashes_valid=True,live_data_unchanged=True,game_launched=False,installed_to_game=False))
    print('APPLIED: Pythonlancer sources updated and verified; live DATA unchanged')

def cleanup():
    assert read(REVIEW/'applied.json')['all_ten_source_hashes_valid']
    root=(REVIEW/'staged_build').resolve();assert root.is_relative_to(ROOT.resolve())
    removed=[];parents=set()
    for name,digest in read(REVIEW/'plan.json')['staged_hashes'].items():
        path=root/'DATA'/DATA_BASE/name
        assert path.resolve().is_relative_to(root)
        for item in [path]+list(path.parents):
            if not item.is_relative_to(root):break
            assert not (getattr(item.stat(),'st_file_attributes',0)&0x400),('Reparse point',item)
        assert sha(path.read_bytes())==digest
        path.unlink();removed.append(str(path))
        parents.update(p for p in path.parents if p.is_relative_to(root))
    for path in sorted(parents,key=lambda p:len(p.parts),reverse=True):
        if path.is_dir() and not any(path.iterdir()):path.rmdir()
    save(REVIEW/'cleanup.json',dict(removed=removed,authoring_assets_preserved=True))
    print('REMOVED verified temporary staged DATA copies only')

if __name__=='__main__':cleanup() if '--cleanup' in sys.argv else apply() if '--apply' in sys.argv else prepare()
