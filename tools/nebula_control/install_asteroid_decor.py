"""Install the requested decorations-only diagnostic; never launch the game."""
from pathlib import Path
import json,os,re,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff/decor_only'
BUILD=OUT/'build';PLAN=OUT/'install.json'
base.OUT,base.BUILD=OUT,BUILD
KEY=b'procedural_asteroid_decor_only'

def configuration(raw):
    match=re.search(rb'(?mi)^\[Render\][ \t]*\r?\n',raw);assert match
    following=re.search(rb'(?m)^\[',raw[match.end():])
    end=match.end()+following.start() if following else len(raw)
    section=raw[match.end():end];pattern=rb'(?mi)^'+KEY+rb'[ \t]*=[^\r\n]*'
    if re.search(pattern,section):
        section,count=re.subn(pattern,KEY+b' = 1',section);assert count==1
    else:section=KEY+b' = 1'+(b'\r\n' if b'\r\n' in raw else b'\n')+section
    return raw[:match.end()]+section+raw[end:]

def prepare():
    check=json.loads((OUT/'checks.json').read_text());assert check['passed'] and check['cpu']['passed']
    sources=check['sources']
    for name in ('tools/nebula_control/check_asteroid_handoff.py','tools/nebula_control/check_asteroid_handoff.cpp'):
        sources[name]=base.digest(ROOT/name)
    for name,h in sources.items():assert base.digest(ROOT/name)==h,name
    for name,h in check['assets'].items():assert base.digest(Path(name))==h,name
    for name,h in check['binaries'].items():assert base.digest(BUILD/'bin'/name)==h,name
    deps,count=base.verify_imports(('Server.dll','freelancer.exe'))
    files={GAME/'bin'/n:BUILD/'bin'/n for n in ('Server.dll','Server.pdb','freelancer.exe','freelancer.pdb')}
    files[GAME/'DATA_EXTRA/SHADERS/far_rocks.hlsl']=ROOT/'DATA_EXTRA/SHADERS/far_rocks.hlsl'
    config=OUT/'port.ini';config.write_bytes(configuration((GAME/'bin/port.ini').read_bytes()))
    files[GAME/'bin/port.ini']=config
    for name,h in check['cache_files'].items():
        p=OUT/'gpu_probe/cache'/name;assert base.digest(p)==h
        files[base.cache_path()/name]=p
    previous=json.loads((OUT.parent/'radius/install.json').read_text())
    guards={n:base.digest(Path(n)) for n in previous['guards'] if Path(n) not in files}
    guards.update(check['assets'])
    plan={'installed':False,'game_launched':False,'cache_cleared':False,'sources':sources,'guards':guards,
          'dependencies':deps,'verified_imports':count,'checks':base.digest(OUT/'checks.json'),
          'files':{str(p):{'source':str(s),'before':base.digest(p) if p.exists() else None,'after':base.digest(s)} for p,s in files.items()},
          'embedded_animation_bytes':base.verify_resource(BUILD/'bin/freelancer.exe'),'installer':base.digest(Path(__file__))}
    PLAN.write_text(json.dumps(plan,indent=2));print(f'Ready: client/Server with symbols, mesh shader and one diagnostic setting; {count} verified imports')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert base.digest(Path(__file__))==plan['installer'] and base.digest(OUT/'checks.json')==plan['checks']
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    for name,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/name)==h,name
    before={};after={};cache=base.cache_path().resolve()
    for name,item in plan['files'].items():
        p=Path(name);base.safe(p,cache if p.resolve().is_relative_to(cache) else GAME)
        source=Path(item['source']);assert base.digest(source)==item['after']
        assert (base.digest(p) if p.exists() else None)==item['before']
        before[p]=p.read_bytes() if p.exists() else None;after[p]=source.read_bytes()
    written=[]
    try:
        for p,b in after.items():written.append(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
        for p,b in after.items():assert p.read_bytes()==b,p
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
        base.verify_resource(GAME/'bin/freelancer.exe')
    except BaseException:
        for p in reversed(written):
            if before[p] is None:p.unlink(missing_ok=True)
            else:p.write_bytes(before[p])
        raise
    before.clear();after.clear();plan['installed']=True;PLAN.write_text(json.dumps(plan,indent=2))
    removed=base.cleanup()
    for directory in (OUT/'probe',OUT/'gpu_probe'):
        for folder,dirs,names in os.walk(base.safe(directory,OUT),followlinks=False):
            for name in dirs:base.safe(Path(folder)/name,directory)
            for name in names:
                p=base.safe(Path(folder)/name,directory)
                if p.suffix.lower() in ('.exe','.obj','.pdb','.ilk','.lib','.exp','.bin','.texture'):
                    state=p.stat();assert state.st_mtime_ns==p.stat().st_mtime_ns;p.unlink();removed+=state.st_size
    plan['removed_bytes']=removed;PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed and hash-verified decorations-only mode; cleaned {removed/1024**2:.1f} MiB; no game launch')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
