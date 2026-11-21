"""Install verified distant asteroid material routing, preserving nebula and content."""
from pathlib import Path
import json
import re
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/material_lod'
BUILD=OUT/'build'
GAME=Path('D:/Games/FL_MOD')
PLAN=OUT/'install.json'
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
import install_asteroid_fog as cleanup
base.OUT,base.BUILD=OUT,BUILD
cleanup.OUT=OUT
FILES={'bin/RP9.dll':BUILD/'bin/RP9.dll','bin/RP9.pdb':BUILD/'bin/RP9.pdb',
       'DATA_EXTRA/SHADERS/surface_material.hlsl':ROOT/'DATA_EXTRA/SHADERS/surface_material.hlsl'}

def prepare():
    report=json.loads((OUT/'checks.json').read_text())
    assert report['passed'] and report['regression'] and report['manifest'] and not report['expect_bug']
    assert base.digest(BUILD/'bin/RP9.dll')==report['binary']
    for name,h in report['sources'].items():assert base.digest(ROOT/name)==h,name
    dependencies,count=base.verify_imports(('RP9.dll',))
    guarded=[GAME/'bin'/n for n in ('freelancer.exe','freelancer.pdb','Common.dll','Server.dll','Content.dll','port.ini')]
    guarded += [GAME/'DATA_EXTRA/VOLUMETRIC/volumetric.ini',GAME/'DATA/UNIVERSE/SYSTEMS_MOD/OMEGA15/om15.ini',
                GAME/'DATA/SOLAR/ASTEROIDS_MOD/GENERATED/om15_ast1_asteroids.ini']
    guarded += list((GAME/'DATA/SOLAR/NEBULA_MOD/GENERATED').glob('gen_om15_*_nebula.ini'))
    for root in (ROOT,GAME):
        guarded += [root/'DATA_EXTRA/SHADERS'/n for n in ('nebula_volume.hlsl','nebula_volume.hlsli','nebula_composite.hlsl','far_rocks.hlsl')]
    for name,h in report['cache_files'].items():
        assert re.fullmatch('[0-9a-f]{64}\\.bin',name) and base.digest(OUT/'probe/manifest_cache'/name)==h
    plan={'files':{n:{'before':base.digest(GAME/n),'after':base.digest(p)} for n,p in FILES.items()},
          'guards':{str(p):base.digest(p) for p in guarded},'dependencies':dependencies,'verified_imports':count,
          'sources':report['sources'],'checks':base.digest(OUT/'checks.json'),'cache_files':report['cache_files'],
          'installer':base.digest(Path(__file__)),'installed':False,'game_launched':False,'nebula_changed':False,'cache_cleared':False}
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Ready: three files, {count} resolved imports, {len(plan["cache_files"])} checked shader cache entries')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert base.digest(Path(__file__))==plan['installer']
    assert base.digest(OUT/'checks.json')==plan['checks']
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    for name,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/name)==h,name
    before={};after={}
    for name,source in FILES.items():
        target=base.safe(GAME/name,GAME);before[target]=target.read_bytes();after[target]=source.read_bytes()
        assert base.digest(target)==plan['files'][name]['before']
        assert base.digest(source)==plan['files'][name]['after']
    entries={}
    for name,h in plan['cache_files'].items():
        path=base.safe(OUT/'probe/manifest_cache'/name,OUT)
        assert base.digest(path)==h;entries[name]=(path.read_bytes(),h)
    cache=base.safe(base.cache_path(),base.cache_path());cache.mkdir(parents=True,exist_ok=True)
    created=[];written=[]
    try:
        for name,(data,h) in entries.items():
            target=base.safe(cache/name,cache)
            if not target.exists():
                with target.open('xb') as stream:stream.write(data)
                created.append((target,h))
            assert base.digest(target)==h
        for path,data in after.items():written.append(path);path.write_bytes(data)
        for path,data in after.items():assert path.read_bytes()==data,path
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    except BaseException:
        for path in reversed(written):path.write_bytes(before[path])
        for target,h in created:
            base.safe(target,cache);assert base.digest(target)==h;target.unlink()
        raise
    before.clear();after.clear();entries.clear()
    plan.update(installed=True,new_shader_cache_entries=len(created))
    PLAN.write_text(json.dumps(plan,indent=2))
    plan['removed_bytes']=base.cleanup()+cleanup.cleanup_probes()
    # Earlier phases of this same investigation left only standalone probe
    # binaries. Keep captured constants, PNGs, generated source and reports.
    trace=OUT.parent/'physical_order/trace/probe'
    candidates=[trace/n for n in ('replay.exe','replay.obj','replay.lib','replay.exp')]
    candidates += list((trace/'cache').glob('*.bin'))
    for path in candidates:
        base.safe(path,trace)
        if not path.exists():continue
        if path.parent.name=='cache':assert re.fullmatch('[0-9a-f]{64}\\.bin',path.name)
        info=path.stat();assert path.stat().st_mtime_ns==info.st_mtime_ns
        path.unlink();plan['removed_bytes']+=info.st_size
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed/hash-verified RP9.dll, symbols and surface shader; nebula/client/config unchanged; added {len(created)} cache entries; removed {plan["removed_bytes"]/1024**2:.1f} MiB staging')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
