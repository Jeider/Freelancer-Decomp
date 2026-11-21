"""Install checked client/renderer solar fog scopes; no DATA or cloud changes."""
from pathlib import Path
import hashlib
import json
import re
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
import install_asteroid_fog as cleanup
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/solar_scope'
BUILD=OUT/'build'
GAME=Path('D:/Games/FL_MOD')
PLAN=OUT/'install.json'
base.OUT,base.BUILD=OUT,BUILD
cleanup.OUT=OUT
FILES={f'bin/{n}':BUILD/'bin'/n for n in ('RP9.dll','RP9.pdb','freelancer.exe','freelancer.pdb')}

def prepare():
    checks=json.loads((OUT/'checks.json').read_text())
    assert all(checks[n] for n in ('passed','policy','solar','layered','regression','manifest'))
    for name,h in checks['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in checks['binaries'].items():assert base.digest(BUILD/'bin'/name)==h,name
    dependencies,count=base.verify_imports()
    resource=base.verify_resource(BUILD/'bin/freelancer.exe')
    guards=[GAME/'bin'/n for n in ('Common.dll','Server.dll','Content.dll','port.ini','D3D9.dll','dgVoodoo.conf')]
    guards += [GAME/'DATA_EXTRA/VOLUMETRIC/volumetric.ini',GAME/'DATA/UNIVERSE/universe.ini']
    for system,folder in (('om15','OMEGA15'),('om7','OMEGA7'),('rh_stut','RH_STUTTGART')):
        guards += [GAME/f'DATA/UNIVERSE/SYSTEMS_MOD/{folder}/{system}.ini']
        guards += list((GAME/'DATA/SOLAR/NEBULA_MOD/GENERATED').glob(f'gen_{system}_*_nebula.ini'))
        guards += list((GAME/'DATA/SOLAR/ASTEROIDS_MOD/GENERATED').glob(f'{system}_*_asteroids.ini'))
    for root in (ROOT,GAME):
        guards += [root/'DATA_EXTRA/SHADERS'/n for n in ('surface_material.hlsl','far_rocks.hlsl','nebula_volume.hlsl','nebula_volume.hlsli','nebula_composite.hlsl')]
    for name,h in checks['cache_files'].items():
        assert re.fullmatch(r'[0-9a-f]{64}\.bin',name) and base.digest(OUT/'probe/manifest_cache'/name)==h
    plan={'installed':False,'game_launched':False,'nebula_changed':False,'cache_cleared':False,
        'files':{n:{'before':base.digest(GAME/n),'after':base.digest(p)} for n,p in FILES.items()},
        'guards':{str(p):base.digest(p) for p in guards if p.exists()},'dependencies':dependencies,
        'verified_imports':count,'embedded_animation_bytes':resource,'sources':checks['sources'],
        'checks':base.digest(OUT/'checks.json'),'cache_files':checks['cache_files'],'installer':base.digest(Path(__file__))}
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Ready: four binaries/symbols, {count} resolved imports, {len(plan["cache_files"])} checked shaders; cloud/DATA/config preserved')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert base.digest(Path(__file__))==plan['installer'] and base.digest(OUT/'checks.json')==plan['checks']
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    for name,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/name)==h,name
    before={};after={}
    for name,source in FILES.items():
        target=base.safe(GAME/name,GAME);before[target]=target.read_bytes();after[target]=source.read_bytes()
        assert base.digest(target)==plan['files'][name]['before'] and base.digest(source)==plan['files'][name]['after']
    cache=base.safe(base.cache_path(),base.cache_path());cache.mkdir(parents=True,exist_ok=True)
    created=[];written=[]
    try:
        for name,h in plan['cache_files'].items():
            source=base.safe(OUT/'probe/manifest_cache'/name,OUT);assert base.digest(source)==h
            target=base.safe(cache/name,cache)
            if not target.exists():
                with target.open('xb') as stream:stream.write(source.read_bytes())
                created.append((target,h))
            assert base.digest(target)==h
        for path,data in after.items():written.append(path);path.write_bytes(data)
        for path,data in after.items():assert path.read_bytes()==data,path
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
        base.verify_resource(GAME/'bin/freelancer.exe')
    except BaseException:
        for path in reversed(written):path.write_bytes(before[path])
        for target,h in created:
            base.safe(target,cache);assert base.digest(target)==h;target.unlink()
        raise
    before.clear();after.clear()
    plan.update(installed=True,new_shader_cache_entries=len(created));PLAN.write_text(json.dumps(plan,indent=2))
    plan['removed_bytes']=base.cleanup()+cleanup.cleanup_probes()
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed/hash-verified four files; added {len(created)} shaders without clearing cache; removed {plan["removed_bytes"]/1024**2:.1f} MiB staging; no game launch')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
