"""Install the checked Omega-15 decorative mesh trial; no DATA writes or game launch."""
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh'
BUILD=OUT/'build'
GAME=Path('D:/Games/FL_MOD')
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
base.OUT,base.BUILD=OUT,BUILD
FILES={'bin/freelancer.exe':BUILD/'bin/freelancer.exe','bin/freelancer.pdb':BUILD/'bin/freelancer.pdb',
       'DATA_EXTRA/SHADERS/far_rocks.hlsl':ROOT/'DATA_EXTRA/SHADERS/far_rocks.hlsl'}
PLAN=OUT/'install.json'

def optional(path):return base.digest(path) if path.exists() else None

def prepare():
    checks=json.loads((OUT/'checks.json').read_text())
    assert checks['passed'] and checks['binary']==base.digest(BUILD/'bin/freelancer.exe')
    for name,h in checks['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in checks['assets'].items():assert base.digest(Path(name))==h,name
    deps,count=base.verify_imports(('freelancer.exe',))
    guards={str(GAME/'bin'/n):optional(GAME/'bin'/n) for n in ('RP9.dll','D3D9.dll','dgVoodoo.conf','port.ini')}
    for p in ('DATA/SOLAR/ASTEROIDS_MOD/GENERATED/om15_ast1_asteroids.ini','DATA/SOLAR/solararch.ini'):
        guards[str(GAME/p)]=base.digest(GAME/p)
    plan=dict(files={n:dict(before=optional(GAME/n),after=base.digest(p)) for n,p in FILES.items()},
              dependencies=deps,guards=guards,verified_imports=count,checks=base.digest(OUT/'checks.json'),
              sources=checks['sources'],assets=checks['assets'],cache_files=checks['cache_files'],
              cache_directory=str(base.cache_path()),embedded_bytes=base.verify_resource(BUILD/'bin/freelancer.exe'),
              zone='Zone_om15_ast1_asteroids',physical_population_changed=False,game_launched=False)
    PLAN.write_text(json.dumps(plan,indent=2),encoding='utf8')
    print(f'Ready: client, symbols, far-rock shader; {count} imports; physical population unchanged')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert base.digest(OUT/'checks.json')==plan['checks']
    for n,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/n)==h,n
    for n,h in plan['guards'].items():assert optional(Path(n))==h,n
    for n,h in plan['sources'].items():assert base.digest(ROOT/n)==h,n
    for n,h in plan['assets'].items():assert base.digest(Path(n))==h,n
    prior={}
    for name,source in FILES.items():
        target=base.safe(GAME/name,GAME)
        assert optional(target)==plan['files'][name]['before'],name
        assert base.digest(source)==plan['files'][name]['after'],name
        prior[name]=target.read_bytes() if target.exists() else None
    cache=base.safe(Path(plan['cache_directory']),base.cache_path());created=[];written=[]
    for name,h in plan['cache_files'].items():assert base.digest(OUT/'probe/cache'/name)==h,name
    try:
        for name,source in FILES.items():written.append(name);(GAME/name).write_bytes(source.read_bytes())
        for name in FILES:assert base.digest(GAME/name)==plan['files'][name]['after'],name
        for n,h in plan['guards'].items():assert optional(Path(n))==h,n
        base.verify_resource(GAME/'bin/freelancer.exe')
        cache.mkdir(parents=True,exist_ok=True)
        for name,h in plan['cache_files'].items():
            target=base.safe(cache/name,cache)
            if target.exists():continue
            with target.open('xb') as stream:
                created.append(target);stream.write((OUT/'probe/cache'/name).read_bytes())
            assert base.digest(target)==h
    except BaseException:
        for p in reversed(created):base.safe(p,cache).unlink(missing_ok=True)
        for name in reversed(written):
            target=base.safe(GAME/name,GAME)
            if prior[name] is None:target.unlink(missing_ok=True)
            else:target.write_bytes(prior[name])
        raise
    prior.clear();removed=base.cleanup();probe=base.safe(OUT/'probe',OUT)
    for directory,children,files in os.walk(probe,followlinks=False):
        for child in children:base.safe(Path(directory)/child,probe)
        for name in files:
            path=base.safe(Path(directory)/name,probe);before=path.stat()
            assert path.stat().st_mtime_ns==before.st_mtime_ns
            removed+=before.st_size;path.unlink()
    plan.update(installed=True,removed_build_bytes=removed,warmed_shader_entries=len(created))
    (OUT/'installed.json').write_text(json.dumps(plan,indent=2),encoding='utf8')
    print(f'Installed and verified {len(FILES)} files; {len(created)} cache entries added; {removed/1024**2:.1f} MiB staging cleaned')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
