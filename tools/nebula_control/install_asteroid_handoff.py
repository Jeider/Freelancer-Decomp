"""Install the checked procedural asteroid client/server, preserving renderer, DATA and shader cache."""
from pathlib import Path
import json
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff'
BUILD=OUT/'build'
GAME=Path('D:/Games/FL_MOD')
PLAN=OUT/'install.json'
base.OUT,base.BUILD=OUT,BUILD
FILES={f'bin/{name}':BUILD/'bin'/name for name in ('Server.dll','Server.pdb','freelancer.exe','freelancer.pdb')}

def prepare():
    checks=json.loads((OUT/'checks.json').read_text())
    assert checks['passed'] and checks['cpu']['passed'] and checks['exclusions']==8
    assert len(checks['matching_models'])==3
    for name,h in checks['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in checks['binaries'].items():assert base.digest(BUILD/'bin'/name)==h,name
    for path,h in checks['assets'].items():assert base.digest(Path(path))==h,path
    dependencies,count=base.verify_imports(('Server.dll','freelancer.exe'))
    resource=base.verify_resource(BUILD/'bin/freelancer.exe')
    guards=[GAME/'bin'/name for name in ('Common.dll','Content.dll','RP9.dll','RP9.pdb','RemoteClient.dll','RemoteServer.dll',
             'port.ini','freelancer.ini','D3D9.dll','dgVoodoo.conf')]
    guards += [GAME/'DATA/UNIVERSE/universe.ini',GAME/'DATA/SOLAR/solararch.ini',GAME/'DATA/SOLAR/dasteroidarch.ini',
               GAME/'DATA_EXTRA/VOLUMETRIC/volumetric.ini']
    for system,folder in (('om15','OMEGA15'),('om7','OMEGA7'),('rh_stut','RH_STUTTGART')):
        guards += [GAME/f'DATA/UNIVERSE/SYSTEMS_MOD/{folder}/{system}.ini']
        guards += list((GAME/'DATA/SOLAR/NEBULA_MOD/GENERATED').glob(f'gen_{system}_*_nebula.ini'))
        guards += list((GAME/'DATA/SOLAR/ASTEROIDS_MOD/GENERATED').glob(f'{system}_*_asteroids.ini'))
    for root in (ROOT,GAME):
        guards += [root/'DATA_EXTRA/SHADERS'/name for name in ('far_rocks.hlsl','surface_material.hlsl','nebula_volume.hlsl',
                   'nebula_volume.hlsli','nebula_composite.hlsl')]
    guarded={str(p):base.digest(p) for p in guards if p.exists()}
    guarded.update(checks['assets'])
    plan={'installed':False,'game_launched':False,'cache_cleared':False,'nebula_changed':False,
          'files':{name:{'before':base.digest(GAME/name),'after':base.digest(path)} for name,path in FILES.items()},
          'guards':guarded,'dependencies':dependencies,'verified_imports':count,'embedded_animation_bytes':resource,
          'sources':checks['sources'],'checks':base.digest(OUT/'checks.json'),'installer':base.digest(Path(__file__))}
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Ready: client/Server + current symbols; {count} resolved imports; renderer, clouds, DATA, shader cache unchanged')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert base.digest(Path(__file__))==plan['installer'] and base.digest(OUT/'checks.json')==plan['checks']
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    for name,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/name)==h,name
    before={};after={};written=[]
    for name,source in FILES.items():
        target=base.safe(GAME/name,GAME);before[target]=target.read_bytes();after[target]=source.read_bytes()
        assert base.digest(target)==plan['files'][name]['before'] and base.digest(source)==plan['files'][name]['after']
    try:
        for path,data in after.items():written.append(path);path.write_bytes(data)
        for path,data in after.items():assert path.read_bytes()==data,path
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
        base.verify_resource(GAME/'bin/freelancer.exe')
    except BaseException:
        for path in reversed(written):path.write_bytes(before[path])
        raise
    before.clear();after.clear();plan['installed']=True;PLAN.write_text(json.dumps(plan,indent=2))
    removed=base.cleanup()
    for directory in (OUT/'probe',OUT/'gpu_probe'):
        # This task's standalone test products only. Validate links before descending.
        import os
        for folder,dirs,files in os.walk(base.safe(directory,OUT),followlinks=False):
            for name in dirs:base.safe(Path(folder)/name,directory)
            for name in files:
                path=base.safe(Path(folder)/name,directory)
                if path.suffix.lower() in ('.exe','.obj','.pdb','.ilk','.bin','.texture'):
                    state=path.stat();assert path.stat().st_mtime_ns==state.st_mtime_ns;path.unlink();removed+=state.st_size
    plan['removed_bytes']=removed;PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed and hash-verified four files; cleaned {removed/1024**2:.1f} MiB of build/test binaries; no game launch')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
