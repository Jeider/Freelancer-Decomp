"""Install checked server-only 2 km / 1 km procedural asteroid physics radii."""
from pathlib import Path
import json,os,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff/radius'
BUILD=OUT/'build';PLAN=OUT/'install.json'
base.OUT,base.BUILD=OUT,BUILD
NAMES=('Server.dll','Server.pdb')

def prepare():
    check=json.loads((OUT/'cpu_checks.json').read_text());assert check['passed']
    content=json.loads((OUT/'content_checks.json').read_text());assert content['passed']
    sources=check['sources']
    for name in ('tools/nebula_control/check_asteroid_handoff.py','tools/nebula_control/check_asteroid_handoff.cpp'):
        sources[name]=base.digest(ROOT/name)
    for name,h in sources.items():assert base.digest(ROOT/name)==h
    for name,h in content['assets'].items():assert base.digest(Path(name))==h
    deps,count=base.verify_imports(('Server.dll',))
    previous=json.loads((OUT.parent/'performance/install.json').read_text())
    guards={n:base.digest(Path(n)) for n in previous['guards']}
    for name in previous['files']:
        p=Path(name)
        if p not in (GAME/'bin'/'Server.dll',GAME/'bin'/'Server.pdb'):guards[name]=base.digest(p)
    guards.update(content['assets'])
    plan={'installed':False,'game_launched':False,'sources':sources,'guards':guards,'dependencies':deps,
          'verified_imports':count,'checks':{n:base.digest(OUT/n) for n in ('cpu_checks.json','content_checks.json')},
          'files':{n:{'before':base.digest(GAME/'bin'/n),'after':base.digest(BUILD/'bin'/n)} for n in NAMES},
          'installer':base.digest(Path(__file__))}
    PLAN.write_text(json.dumps(plan,indent=2));print(f'Ready: Server.dll/PDB; {count} resolved imports; installed visuals/physics assets preserved')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert base.digest(Path(__file__))==plan['installer']
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h
    for name,h in plan['checks'].items():assert base.digest(OUT/name)==h
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h
    for name,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/name)==h
    before={};after={}
    for name in NAMES:
        p=base.safe(GAME/'bin'/name,GAME);s=base.safe(BUILD/'bin'/name,BUILD)
        assert base.digest(p)==plan['files'][name]['before'] and base.digest(s)==plan['files'][name]['after']
        before[p]=p.read_bytes();after[p]=s.read_bytes()
    written=[]
    try:
        for p,b in after.items():written.append(p);p.write_bytes(b)
        for p,b in after.items():assert p.read_bytes()==b
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h
    except BaseException:
        for p in reversed(written):p.write_bytes(before[p])
        raise
    before.clear();after.clear();plan['installed']=True;PLAN.write_text(json.dumps(plan,indent=2))
    removed=base.cleanup()
    for folder,dirs,names in os.walk(base.safe(OUT/'probe',OUT),followlinks=False):
        for name in dirs:base.safe(Path(folder)/name,OUT/'probe')
        for name in names:
            p=base.safe(Path(folder)/name,OUT/'probe')
            if p.suffix.lower() in ('.exe','.obj','.pdb','.ilk','.lib','.exp'):
                state=p.stat();assert state.st_mtime_ns==p.stat().st_mtime_ns;p.unlink();removed+=state.st_size
    plan['removed_bytes']=removed;PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed and hash-verified Server.dll/PDB; cleaned {removed/1024**2:.1f} MiB; no game launch')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
