"""Install the verified minimal asteroid material and embedded LODs; never start the game."""
from pathlib import Path
import json,os,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/lod';BUILD=OUT/'build';PLAN=OUT/'install.json'
base.OUT,base.BUILD=OUT,BUILD
def prepare():
    check=json.loads((OUT/'checks.json').read_text());cpu=json.loads((OUT/'client_checks.json').read_text())
    assert check['passed'] and cpu['passed'];sources={**check['sources'],**cpu['sources']}
    for name,h in sources.items():assert base.digest(ROOT/name)==h,name
    for name,h in check['assets'].items():assert base.digest(Path(name))==h,name
    for name,h in check['binaries'].items():assert base.digest(BUILD/'bin'/name)==h,name
    assert check['geometry']['header_sha256']==base.digest(ROOT/'src/freelancer/Client/asteroid_lod_data.h')
    deps,count=base.verify_imports(('RP9.dll','freelancer.exe'))
    files={GAME/'bin'/n:BUILD/'bin'/n for n in check['binaries']}
    files[GAME/'DATA_EXTRA/SHADERS/asteroid_simple.hlsl']=ROOT/'DATA_EXTRA/SHADERS/asteroid_simple.hlsl'
    previous=json.loads((OUT.parent/'handoff/decor_only/install.json').read_text())
    guards={n:base.digest(Path(n)) for n in previous['guards'] if Path(n) not in files}
    for name in previous['files']:
        p=Path(name)
        if p not in files and p.resolve().is_relative_to(GAME.resolve()):guards[name]=base.digest(p)
    guards.update(check['assets'])
    # The previous no-hide material is the fallback; keep it and the diagnostic switch intact.
    assert base.digest(GAME/'DATA_EXTRA/SHADERS/far_rocks.hlsl')==sources['DATA_EXTRA/SHADERS/far_rocks.hlsl']
    assert b'procedural_asteroid_decor_only = 1' in (GAME/'bin/port.ini').read_bytes()
    for name,h in check['cache_files'].items():
        src=OUT/'probe/cache'/name;assert base.digest(src)==h
        target=base.cache_path()/name
        if target.exists() and base.digest(target)==h:continue
        files[target]=src
    plan={'installed':False,'game_launched':False,'cache_cleared':False,'sources':sources,'guards':guards,
      'dependencies':deps,'verified_imports':count,'checks':base.digest(OUT/'checks.json'),
      'client_checks':base.digest(OUT/'client_checks.json'),
      'files':{str(p):{'source':str(s),'before':base.digest(p) if p.exists() else None,'after':base.digest(s)} for p,s in files.items()},
      'embedded_animation_bytes':base.verify_resource(BUILD/'bin/freelancer.exe'),'installer':base.digest(Path(__file__))}
    PLAN.write_text(json.dumps(plan,indent=2));print(f'Ready: RP9/client and symbols, minimal shader, additive cache; {count} verified imports')
def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert base.digest(Path(__file__))==plan['installer']
    for name,key in [('checks.json','checks'),('client_checks.json','client_checks')]:assert base.digest(OUT/name)==plan[key]
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    for name,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/name)==h,name
    before={};after={};cache=base.cache_path().resolve()
    for name,item in plan['files'].items():
        p=Path(name);base.safe(p,cache if p.resolve().is_relative_to(cache) else GAME)
        source=Path(item['source']);assert base.digest(source)==item['after']
        assert (base.digest(p) if p.exists() else None)==item['before'],p
        before[p]=p.read_bytes() if p.exists() else None;after[p]=source.read_bytes()
    written=[]
    try:
        for p,data in after.items():written.append(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
        for p,data in after.items():assert p.read_bytes()==data,p
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
        base.verify_resource(GAME/'bin/freelancer.exe')
    except BaseException:
        for p in reversed(written):
            if before[p] is None:p.unlink(missing_ok=True)
            else:p.write_bytes(before[p])
        raise
    before.clear();after.clear();plan['installed']=True;PLAN.write_text(json.dumps(plan,indent=2))
    removed=base.cleanup()
    for directory in (OUT/'probe',OUT/'client_probe'):
        for folder,dirs,names in os.walk(base.safe(directory,OUT),followlinks=False):
            for name in dirs:base.safe(Path(folder)/name,directory)
            for name in names:
                p=base.safe(Path(folder)/name,directory)
                if p.suffix.lower() in ('.exe','.obj','.pdb','.ilk','.lib','.exp','.bin','.texture'):
                    state=p.stat();assert state.st_mtime_ns==p.stat().st_mtime_ns;p.unlink();removed+=state.st_size
    plan['removed_bytes']=removed;PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed and hash-verified minimal shader + embedded LODs; cleaned {removed/1024**2:.1f} MiB; no game launch')
if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
