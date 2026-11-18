"""Install the verified Omega-15 changes, using DataFolder for all DATA writes."""
import json
import os
from pathlib import Path
import sys
from prepare_omega15 import ROOT,OUT,VOLUME,STAGE,GAME,PY,FIELD,CONFIG,GENERATOR,data_folder,digest

sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
BUILD=OUT/'build';base.OUT,base.BUILD=OUT,BUILD
PLAN=OUT/'omega15_install.json'
FILES={'bin/freelancer.exe':BUILD/'bin/freelancer.exe','bin/freelancer.pdb':BUILD/'bin/freelancer.pdb',
       'DATA_EXTRA/SHADERS/far_rocks.hlsl':ROOT/'DATA_EXTRA/SHADERS/far_rocks.hlsl',
       'DATA/'+FIELD:STAGE/'DATA'/FIELD,CONFIG:STAGE/CONFIG,GENERATOR:STAGE/GENERATOR}
CHECKS=[OUT/'checks.json',VOLUME/'checks.json',OUT/'content_plan.json']

def optional(p):return digest(p) if p.exists() else None

def prepare():
    mesh,volume,content=[json.loads(p.read_text()) for p in CHECKS]
    assert mesh['passed'] and volume['passed']
    binary=digest(BUILD/'bin/freelancer.exe');assert binary==mesh['binary']==volume['binary']
    assert digest(STAGE/CONFIG)==volume['staged_profile']
    assert digest(PY/'tools/data_folder.py')==content['data_folder_api']
    sources={**mesh['sources'],**volume['sources'],**content['sources']}
    for n,h in sources.items():assert digest(ROOT/n)==h,n
    for n,h in mesh['assets'].items():assert digest(Path(n))==h,n
    for n,h in content['files'].items():assert digest(GAME/n)==h['before'] and digest(STAGE/n)==h['after'],n
    deps,count=base.verify_imports(('freelancer.exe',))
    guards={str(GAME/'bin'/n):optional(GAME/'bin'/n) for n in ('RP9.dll','RP9.pdb','Server.dll','Content.dll','D3D9.dll','dgVoodoo.conf','port.ini')}
    guards[str(PY/'tools/data_folder.py')]=content['data_folder_api']
    guards[str(GAME/'DATA/UNIVERSE/SYSTEMS_MOD/OMEGA15/om15.ini')]=digest(GAME/'DATA/UNIVERSE/SYSTEMS_MOD/OMEGA15/om15.ini')
    for n,h in volume['sources'].items():
        if n.startswith('DATA_EXTRA/SHADERS/'):
            assert digest(GAME/n)==h,n
            guards[str(GAME/n)]=h
    cache={}
    for folder,checks in [(OUT/'probe/cache',mesh),(VOLUME/'probe/cache',volume)]:
        for n,h in checks['cache_files'].items():
            assert digest(folder/n)==h,n
            if n in cache:assert cache[n]['sha256']==h
            cache[n]={'source':str(folder/n),'sha256':h}
    plan={'files':{n:{'before':optional(GAME/n),'after':digest(p)} for n,p in FILES.items()},
          'checks':{str(p):digest(p) for p in CHECKS},'dependencies':deps,'guards':guards,'sources':sources,'assets':mesh['assets'],
          'verified_imports':count,'embedded_bytes':base.verify_resource(BUILD/'bin/freelancer.exe'),
          'cache_files':cache,'physical_population':180,'quality':{'off':'vanilla','low':'vanilla','medium':'volume, 64 steps','high':'volume, 96 steps'},'game_launched':False}
    PLAN.write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(f'Ready: {len(FILES)} files; {count} imports; 180 physical asteroids; full volume on medium/high; stable mesh fades')

def apply():
    base.idle();plan=json.loads(PLAN.read_text())
    for n,h in plan['checks'].items():assert digest(Path(n))==h,n
    for n,h in plan['dependencies'].items():assert digest(GAME/'bin'/n)==h,n
    for n,h in plan['guards'].items():assert optional(Path(n))==h,n
    for n,h in plan['sources'].items():assert digest(ROOT/n)==h,n
    for n,h in plan['assets'].items():assert digest(Path(n))==h,n
    before={}
    for n,p in FILES.items():
        target=base.safe(GAME/n,GAME);assert optional(target)==plan['files'][n]['before'],n
        assert digest(p)==plan['files'][n]['after'],n
        before[n]=target.read_bytes() if target.exists() else None
    cache=base.safe(base.cache_path(),base.cache_path());created=[];written=[]
    for info in plan['cache_files'].values():assert digest(Path(info['source']))==info['sha256']
    data=data_folder(GAME)
    def write(n,raw):
        if n.startswith('DATA/'):
            if raw is None:data.remove_data_file(n[5:])
            else:data.sync_data_file(n[5:],raw)
        else:
            target=base.safe(GAME/n,GAME)
            if raw is None:target.unlink(missing_ok=True)
            else:target.write_bytes(raw)
    try:
        for n,p in FILES.items():written.append(n);write(n,p.read_bytes())
        for n in FILES:assert digest(GAME/n)==plan['files'][n]['after'],n
        for n,h in plan['guards'].items():assert optional(Path(n))==h,n
        base.verify_resource(GAME/'bin/freelancer.exe')
        cache.mkdir(parents=True,exist_ok=True)
        for n,info in plan['cache_files'].items():
            target=base.safe(cache/n,cache)
            if target.exists():continue
            with target.open('xb') as f:created.append(target);f.write(Path(info['source']).read_bytes())
            assert digest(target)==info['sha256']
    except BaseException:
        for p in reversed(created):base.safe(p,cache).unlink(missing_ok=True)
        for n in reversed(written):write(n,before[n])
        raise
    before.clear()
    plan.update(installed=True,warmed_shader_entries=len(created))
    (OUT/'omega15_installed.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    removed=base.cleanup()
    for folder in (OUT/'probe',VOLUME/'probe'):
        folder=base.safe(folder,ROOT/'out/graphics_settings')
        candidates=[]
        for directory,children,files in os.walk(folder,followlinks=False):
            for child in children:base.safe(Path(directory)/child,folder)
            for name in files:
                path=base.safe(Path(directory)/name,folder);s=path.stat();candidates.append((path,s.st_size,s.st_mtime_ns))
        for path,size,mtime in candidates:
            s=path.stat();assert (s.st_size,s.st_mtime_ns)==(size,mtime),path
            removed+=size;path.unlink()
    plan['removed_build_bytes']=removed
    (OUT/'omega15_installed.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
    print(f'Installed and verified {len(FILES)} files; {len(created)} shader cache entries added; {removed/1024**2:.1f} MiB build/probe binaries removed; game not launched')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
