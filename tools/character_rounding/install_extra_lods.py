"""Transactional installation of validated hand/body LODs and their runtime.

All game and rollback DATA writes use Pythonlancer DataFolder. Never launches
or terminates a game process. Temporary binaries/backups are removed on success.
"""
import argparse
import json
from pathlib import Path
import re
import shutil
import subprocess
from contours import ROOT,GAME,DataFolder,digest
from extra_lods import OUT,reconstruct
from hands import OUT as HANDS,NAMES

BUILD=OUT/'runtime'
MODULES=('Common.dll','Deformable2.dll','freelancer.exe')
FILES=MODULES+('Common.pdb','Deformable2.pdb','freelancer.pdb')


def sha(p):return digest(p.read_bytes())
def safe_remove(path,allowed_root=None):
    root=(allowed_root or OUT).resolve();path=path.absolute()
    assert path.resolve().is_relative_to(root) and path.resolve()!=root
    for p in (path,*path.parents):
        assert not p.is_symlink() and not p.is_junction(),p
        if p==root:break
    if path.is_dir():
        assert all(not p.is_symlink() and not p.is_junction() for p in path.rglob('*'))
        shutil.rmtree(path)
    elif path.exists():path.unlink()


def remove_transaction(path):
    folder=DataFolder(root=path);data=path/'DATA'
    if data.exists():
        for file in sorted(data.rglob('*')):
            assert not file.is_symlink() and not file.is_junction()
            if file.is_file():folder.remove_data_file(file.relative_to(data))
        for directory in sorted((p for p in data.rglob('*') if p.is_dir()),key=lambda p:len(p.parts),reverse=True):
            folder.remove_empty_data_directory(directory.relative_to(data))
        data.rmdir() # Empty transaction container, no DATA assets remain.
    safe_remove(path)


def imports():
    compiler=sorted(Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC').iterdir())[-1]/'bin/Hostx64/x86'
    def dump(option,p):return subprocess.check_output([str(compiler/'dumpbin.exe'),option,str(p)],text=True)
    def exports(p):return set(re.findall(r'^\s+\d+\s+[0-9A-F]+\s+[0-9A-F]+\s+(\S+)',dump('/exports',p),re.M))
    dependencies={};compatibility={}
    for name in MODULES:
        old=exports(GAME/'bin'/name);new=exports(BUILD/'bin'/name)
        assert old<=new,(name,'Removed exports',sorted(old-new)[:10]);compatibility[name]=len(old)
        current=None
        for line in dump('/imports',BUILD/'bin'/name).splitlines():
            m=re.fullmatch(r'    (\S+\.dll)',line,re.I)
            if m:
                dep=m[1];target=BUILD/'bin'/dep if dep.lower() in {n.lower() for n in MODULES} else GAME/'bin'/dep
                current=dep if target.exists() else None
                if current and current not in dependencies:dependencies[current]=dict(path=str(target),sha256=sha(target),names=exports(target),checked=0)
            elif current:
                m=re.fullmatch(r'\s+[0-9A-F]+ (\S+)',line)
                if m:
                    assert m[1] in dependencies[current]['names'],(name,current,m[1]);dependencies[current]['checked']+=1
    return dict(dependencies={n:{k:v for k,v in r.items() if k!='names'} for n,r in dependencies.items()},backward_compatible_exports=compatibility)


def evidence():
    hand=json.loads((HANDS/'validation.json').read_text());blends=json.loads((HANDS/'blend_validation.json').read_text())
    assert hand['valid']==8 and {r['name'] for r in blends['valid']}==set(NAMES)
    for r in hand['results']:assert sha(HANDS/r['name']/'edited.json.gz')==r['edited_sha256']
    for r in blends['valid']:assert sha(HANDS/r['name']/'hand.blend')==r['blend_sha256']
    assert 'PASS production loader' in (OUT/'check_loader/result.txt').read_text()
    return dict(hands=hand['valid'],native_animation_samples=sum(r['native_sample_times'] for r in hand['results']),blends=len(blends['valid']))


def prepare():
    models=json.loads((OUT/'models.json').read_text());checks=evidence();binary=imports()
    for r in models['files']:
        path=GAME/'DATA'/r['relative_path'];patch=Path(r['patch']);assert sha(path)==r['before_sha256'] and sha(patch)==r['patch_sha256']
        assert digest(reconstruct(path.read_bytes(),patch))==r['after_sha256']
    for rel,wanted in models['protected'].items():assert sha(GAME/'DATA'/rel)==wanted,rel
    files={n:dict(before=sha(GAME/'bin'/n),after=sha(BUILD/'bin'/n)) for n in FILES}
    data=dict(models=models,files=files,checks=checks,**binary)
    (OUT/'install_manifest.json').write_text(json.dumps(data,indent=2))
    print('READY:',len(models['files']),'models,',len(FILES),'runtime files; imports, exports, animations and Blender sources checked')


def apply():
    data=json.loads((OUT/'install_manifest.json').read_text());models=data['models'];files=data['files'];evidence()
    result=subprocess.run(['tasklist','/FO','CSV','/NH'],capture_output=True,check=True)
    tasks=result.stdout.lower()
    assert not any(b'"'+n+b'"' in tasks for n in (b'freelancer.exe',b'freelancer_window.exe',b'flserver.exe')),'Close game/server before installation'
    for n,r in files.items():assert sha(GAME/'bin'/n)==r['before'] and sha(BUILD/'bin'/n)==r['after'],n
    for r in data['dependencies'].values():assert sha(Path(r['path']))==r['sha256']
    for r in models['files']:
        assert sha(GAME/'DATA'/r['relative_path'])==r['before_sha256'] and sha(Path(r['patch']))==r['patch_sha256']
    for rel,wanted in models['protected'].items():assert sha(GAME/'DATA'/rel)==wanted,rel
    transaction=OUT/'transaction';assert not transaction.exists(),'Review unfinished installation transaction'
    transaction.mkdir();backup=DataFolder(root=transaction);live=DataFolder(root=GAME)
    for n in files:shutil.copy2(GAME/'bin'/n,transaction/n)
    changed=[]
    try:
        for r in models['files']:
            rel=r['relative_path'];before=live.data_path(rel).read_bytes();assert digest(before)==r['before_sha256']
            backup.sync_data_file(rel,before);changed.append(r)
            output=reconstruct(before,Path(r['patch']));assert digest(output)==r['after_sha256']
            live.sync_data_file(rel,output);assert sha(live.data_path(rel))==r['after_sha256']
        for n in files:shutil.copy2(BUILD/'bin'/n,GAME/'bin'/n)
        for n,r in files.items():assert sha(GAME/'bin'/n)==r['after'],n
        for r in models['files']:assert sha(live.data_path(r['relative_path']))==r['after_sha256']
        for rel,wanted in models['protected'].items():assert sha(live.data_path(rel))==wanted,rel
    except BaseException:
        failures=[]
        for r in reversed(changed):
            try:
                rel=r['relative_path'];live.sync_data_file(rel,backup.data_path(rel).read_bytes());assert sha(live.data_path(rel))==r['before_sha256']
            except Exception as error:failures.append((r['relative_path'],repr(error)))
        for n,r in files.items():
            try:shutil.copy2(transaction/n,GAME/'bin'/n);assert sha(GAME/'bin'/n)==r['before']
            except Exception as error:failures.append((n,repr(error)))
        (OUT/'rollback.json').write_text(json.dumps(dict(failures=failures),indent=2))
        if not failures:remove_transaction(transaction)
        raise
    data.update(installed=True,hashes_verified=True,game_launched=False,dlss5=True,rpg_world=True)
    (OUT/'installed.json').write_text(json.dumps(data,indent=2))
    for name in MODULES:
        module=Path(name).stem;shutil.copy2(BUILD/'obj'/module/'build.log',OUT/(module+'_build.log'))
    remove_transaction(transaction);safe_remove(BUILD)
    # Compact LOD subtrees are authoring sources, not duplicate game builds.
    # Keep them for reproducible editing and restoration of native mesh levels.
    check_root=ROOT/'out/character_rounding/lods/check_loader'
    for name in ('check.exe','check.obj','build.cmd'):safe_remove(check_root/name,check_root)
    print('INSTALLED AND VERIFIED:',len(models['files']),'models;',len(models['protected']),'protected models unchanged;',MODULES,'and symbols. Temporary runtime/rollback removed.')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--remaining',action='store_true');args=p.parse_args()
    if args.remaining:
        from remaining_lods import OUT,reconstruct,evidence
        BUILD=OUT/'runtime';MODULES=('Deformable2.dll',);FILES=MODULES+('Deformable2.pdb',)
    apply() if args.apply else prepare()
