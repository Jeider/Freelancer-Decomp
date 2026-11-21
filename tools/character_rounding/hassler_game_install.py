"""Prepare/apply only rh_hassler_body and its costume/communication references."""
import sys,json,re,hashlib,argparse,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(Path(__file__).parent),str(ROOT/'tools/hatcher_hair')]
from build import GAME,DataFolder
TOP=ROOT/'out/character_rounding/hassler/native_upper';OUT=TOP/'game';STAGE=OUT/'stage'
sha=lambda b:hashlib.sha256(b).hexdigest()
def fingerprint(p):return sha(p.read_bytes()) if p.is_file() else None
def safe(root,relative):
    root=root.resolve();p=(root/relative).resolve();assert p.is_relative_to(root) and p!=root;return p
def put(root,relative,data):
    if relative.startswith('DATA/'):return DataFolder(root=root).sync_data_file(relative[5:],data)
    p=safe(root,relative);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);return p
def remove(root,relative):
    p=safe(root,relative)
    if relative.startswith('DATA/'):DataFolder(root=root).remove_data_file(relative[5:])
    else:p.unlink(missing_ok=True)

def prepare():
    native=json.loads((OUT/'native_build.json').read_text(encoding='utf8'));preview=json.loads((OUT/'preview_validation.json').read_text(encoding='utf8'))
    assert native['native_export_validated'] and preview['native_dfm_sha256']==native['sha256']
    assert fingerprint(Path(native['dfm']))==native['sha256'];wanted={};changes={}
    wanted['DATA/'+native['relative']]=Path(native['dfm']).read_bytes()
    rel='DATA/CHARACTERS/bodyparts.ini';old=safe(GAME,rel).read_bytes();assert b'nickname = rh_hassler_body' not in old
    pattern=rb'(\[Body\]\r?\nnickname = rh_male_elite_body\r?\nmesh = [^\r\n]+\r?\n)';newline=b'\r\n' if b'\r\n' in old else b'\n'
    addition=newline+newline.join([b'[Body]',b'nickname = rh_hassler_body',b'mesh = characters\\bodies\\rh_hassler_body.dfm',b''])
    new,count=re.subn(pattern,lambda m:m.group(0)+addition,old);assert count==1;wanted[rel]=new;changes[rel]='Add male body after rh_male_elite in the same male animation/skeleton context'
    rel='DATA/CHARACTERS/costumes.ini';old=safe(GAME,rel).read_bytes();pattern=rb'(\[Costume\]\r?\nnickname = hassler\r?\nhead = rh_hassler_head\r?\nbody = )rh_male_elite_body\b'
    new,count=re.subn(pattern,rb'\1rh_hassler_body',old);assert count==1;wanted[rel]=new;changes[rel]='Only costume hassler; order/epilogue and other users of the same head unchanged'
    for rel in ('DATA/MISSIONS/M03/m03.ini','DATA/MISSIONS/M04/m04.ini','Assets/Pythonlancer/story/actors.py'):
        old=safe(GAME,rel).read_bytes();new,count=re.subn(rb'(rh_hassler_head\s*,\s*)rh_male_elite_body\b',rb'\1rh_hassler_body',old);assert count>0
        wanted[rel]=new;changes[rel]={'hassler_comm_appearance_replacements':count}
    for rel in ('DATA/RPG/space.ini','Assets/Pythonlancer/tools/rpg_contacts.py'):
        old=safe(GAME,rel).read_bytes();new,count=re.subn(rb'(head = rh_hassler_head\r?\nbody = )rh_male_elite_body\b',rb'\1rh_hassler_body',old);assert count==1
        wanted[rel]=new;changes[rel]='Existing Hassler RPG contact appearance only'
    rel='DATA_EXTRA/ROOM_MATERIALS/profiles.txt';old=safe(GAME,rel).read_bytes()
    existing={line.split(None,5)[5] for line in old.splitlines() if len(line.split(None,5))==6};newkeys={line.encode().split(None,5)[5] for line in native['profiles']};assert not existing&newkeys
    wanted[rel]=old.rstrip(b'\r\n')+b'\n'+('\n'.join(native['profiles'])+'\n').encode();changes[rel]='Append only 17 unique Hassler clothing profiles, character quality scope'
    for name,digest in native['sidecars'].items():
        rel='DATA_EXTRA/ROOM_MATERIALS/'+name;payload=safe(STAGE,rel).read_bytes();assert sha(payload)==digest;wanted[rel]=payload
    files=[]
    for rel,data in wanted.items():
        before=fingerprint(safe(GAME,rel));after=sha(data);put(STAGE,rel,data)
        files.append({'relative':rel,'before':before,'after':after,'bytes':len(data),'note':changes.get(rel,'New model or material map')})
    protected={}
    for rel in ('DATA/CHARACTERS/BODIES/rh_male_elite_body.dfm','DATA/CHARACTERS/HEADS/rh_hassler_head.dfm','DATA/CHARACTERS/HANDS/rh_male_glove_left.dfm','DATA/CHARACTERS/HANDS/rh_male_glove_right.dfm'):
        protected[rel]=fingerprint(safe(GAME,rel))
    result={'body':'rh_hassler_body','game':str(GAME),'files':files,'protected':protected,'native_dfm_sha256':native['sha256'],'preview_blend_sha256':preview['preview_blend_sha256'],'prepared':True,'game_launched':False}
    (OUT/'install_plan.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'prepared_files':len(files),'references':changes},ensure_ascii=False,indent=2))

def prepare_update():
    native=json.loads((OUT/'native_build.json').read_text(encoding='utf8'));preview=json.loads((OUT/'preview_validation.json').read_text(encoding='utf8'))
    sleeves=json.loads((TOP/'step_27/validation.json').read_text(encoding='utf8'))
    assert sleeves['all_passed'] and sleeves['rig_unchanged'] and sleeves['source_blend_sha256']==native['source_blend_sha256']
    collar=json.loads((OUT/'collar_validation.json').read_text(encoding='utf8'));assert collar['native_dfm_sha256']==native['sha256'] and collar['max_neck_seam_error_m']<4e-6
    regression=json.loads((OUT/'neck_regression.json').read_text(encoding='utf8'));assert regression['dfm_sha256']==native['sha256'] and regression['passes'] and regression['uses_separate_hp_head_hp_neck']
    opacity=json.loads((OUT/'collar_opacity_validation.json').read_text(encoding='utf8'));assert opacity['native_dfm_sha256']==native['sha256'] and opacity['all_passed'] and opacity['backface_culling']
    side=json.loads((OUT/'collar_end_validation.json').read_text(encoding='utf8'));assert side['native_dfm_sha256']==native['sha256'] and side['all_passed'] and side['backface_culling']
    assert side['previous_rays_reaching_other_materials']>=6 or (side.get('previous_already_verified') and side.get('rays_per_case',0)>=60)
    previous=json.loads((OUT/'installation.json').read_text(encoding='utf8'))
    assert previous['verified'] and previous['body']=='rh_hassler_body'
    assert native['native_export_validated'] and preview['native_dfm_sha256']==native['sha256']
    assert fingerprint(Path(native['dfm']))==native['sha256']
    assert fingerprint(safe(GAME,'DATA/'+native['relative']))==previous['native_dfm_sha256'],'Installed Hassler changed independently'
    # Existing costume/configuration/source links are already installed. Verify
    # their current presence without overwriting unrelated concurrent edits.
    for rel in ('DATA/CHARACTERS/bodyparts.ini','DATA/CHARACTERS/costumes.ini','DATA/MISSIONS/M03/m03.ini','DATA/MISSIONS/M04/m04.ini','DATA/RPG/space.ini','Assets/Pythonlancer/story/actors.py','Assets/Pythonlancer/tools/rpg_contacts.py'):
        assert b'rh_hassler_body' in safe(GAME,rel).read_bytes(),rel
    wanted={'DATA/'+native['relative']:Path(native['dfm']).read_bytes()}
    rel='DATA_EXTRA/ROOM_MATERIALS/profiles.txt';old=safe(GAME,rel).read_bytes();kept=[];removed=[]
    for line in old.splitlines():
        parts=line.split(None,5)
        if len(parts)==6 and re.fullmatch(rb'rh_hassler_\d\d\|rh_hassler_\d\d\.tga',parts[5]):removed.append(line)
        else:kept.append(line)
    assert len(removed)==17
    wanted[rel]=b'\n'.join(kept).rstrip(b'\r\n')+b'\n'+('\n'.join(native['profiles'])+'\n').encode()
    for name,digest in native['sidecars'].items():
        rel='DATA_EXTRA/ROOM_MATERIALS/'+name;data=safe(STAGE,rel).read_bytes();assert sha(data)==digest;wanted[rel]=data
    files=[]
    for rel,data in wanted.items():
        put(STAGE,rel,data);files.append({'relative':rel,'before':fingerprint(safe(GAME,rel)),'after':sha(data),'bytes':len(data),'note':'Fuller sleeve cap below the unchanged pad, smooth clavicle-to-arm skin transition. Torso, sewn boundaries, epaulettes, collar and native bones preserved'})
    for rel,digest in previous['protected'].items():assert fingerprint(safe(GAME,rel))==digest
    history=OUT/'history';history.mkdir(exist_ok=True)
    (history/(previous['native_dfm_sha256'][:16]+'_installation.json')).write_text(json.dumps(previous,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    result={'body':'rh_hassler_body','game':str(GAME),'files':files,'protected':previous['protected'],'native_dfm_sha256':native['sha256'],'preview_blend_sha256':preview['preview_blend_sha256'],'prepared':True,'update_of':previous['native_dfm_sha256'],'game_launched':False}
    (OUT/'install_plan.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'prepared_update_files':len(files),'previous':previous['native_dfm_sha256']},ensure_ascii=False))

def apply():
    plan=json.loads((OUT/'install_plan.json').read_text(encoding='utf8'));assert Path(plan['game']).resolve()==GAME.resolve()
    preview=json.loads((OUT/'preview_validation.json').read_text(encoding='utf8'));assert preview['native_dfm_sha256']==plan['native_dfm_sha256'];assert fingerprint(OUT/'rh_hassler_body.blend')==plan['preview_blend_sha256']
    for rel,digest in plan['protected'].items():assert fingerprint(safe(GAME,rel))==digest,('Protected source changed',rel)
    for f in plan['files']:
        assert fingerprint(safe(GAME,f['relative'])) in (f['before'],f['after']),('Live file changed after preparation',f['relative'])
        assert fingerprint(safe(STAGE,f['relative']))==f['after'],('Staged file changed',f['relative'])
    backup=OUT/'transactions'/datetime.datetime.now().strftime('%Y%m%d_%H%M%S_%f');old={};touched=[]
    for f in plan['files']:
        rel=f['relative'];p=safe(GAME,rel);old[rel]=p.read_bytes() if p.is_file() else None
        if old[rel] is not None:put(backup,rel,old[rel])
    try:
        for f in plan['files']:
            rel=f['relative'];current=fingerprint(safe(GAME,rel));assert current in (f['before'],f['after'])
            if current==f['after']:continue
            touched.append(rel);put(GAME,rel,safe(STAGE,rel).read_bytes());assert fingerprint(safe(GAME,rel))==f['after']
        for f in plan['files']:assert fingerprint(safe(GAME,f['relative']))==f['after']
        for rel,digest in plan['protected'].items():assert fingerprint(safe(GAME,rel))==digest
    except BaseException:
        for rel in reversed(touched):
            if old[rel] is None:remove(GAME,rel)
            else:put(GAME,rel,old[rel])
        raise
    receipt={**plan,'installed':True,'installed_at':datetime.datetime.now().isoformat(),'verified':True,'changed_files':touched,'game_launched':False}
    (OUT/'installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    # Delete only this transaction's exact files, without traversing any tree.
    for rel,data in old.items():
        if data is not None:remove(backup,rel)
    removed=[]
    for f in plan['files']:
        rel=f['relative']
        if Path(rel).suffix.lower() in ('.dfm','.dds'):remove(STAGE,rel);removed.append(rel)
    for p in list(OUT.glob('mesh[0-4].json.gz'))+list(OUT.glob('decoded_mesh[0-4].json.gz')):
        assert p.resolve().is_relative_to(OUT.resolve()) and not p.is_symlink();p.unlink();removed.append(p.name)
    receipt['staging_binaries_and_intermediates_removed']=removed;receipt['rollback_copies_removed']=True
    (OUT/'installation.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'installed':'rh_hassler_body','verified_files':len(plan['files']),'game':str(GAME),'game_launched':False,'cleanup':len(removed)},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--apply',action='store_true');ap.add_argument('--update',action='store_true');args=ap.parse_args();apply() if args.apply else prepare_update() if args.update else prepare()
