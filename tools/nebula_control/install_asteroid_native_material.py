"""Install verified near-body rendering and enable the existing server handoff."""
from pathlib import Path
import json, os, re, sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff/native_material'
BUILD=OUT/'build';PLAN=OUT/'install.json'
base.OUT,base.BUILD=OUT,BUILD

def configuration(raw):
    match=re.search(rb'(?mi)^\[Render\][ \t]*\r?\n',raw);assert match
    following=re.search(rb'(?m)^\[',raw[match.end():])
    end=match.end()+following.start() if following else len(raw)
    section,count=re.subn(rb'(?mi)^(procedural_asteroid_decor_only[ \t]*=[ \t]*)1(?=[ \t;\r\n]|$)',
                         rb'\g<1>0',raw[match.end():end]);assert count==1
    result=raw[:match.end()]+section+raw[end:]
    assert len(result)==len(raw) and sum(a!=b for a,b in zip(raw,result))==1
    return result

def prepare():
    checks={name:json.loads((OUT/name).read_text()) for name in ('gpu_checks.json','client_checks.json','cpu_checks.json')}
    sources={}
    for check in checks.values():
        assert check['passed']
        for name,h in check['sources'].items():assert base.digest(ROOT/name)==h,name
        sources.update(check['sources'])
    gpu=checks['gpu_checks.json']
    for name,h in gpu['assets'].items():assert base.digest(Path(name))==h,name
    for name,h in gpu['binaries'].items():assert base.digest(BUILD/'bin'/name)==h,name
    old_server=json.loads((OUT.parent/'decor_only/install.json').read_text())
    for name in checks['cpu_checks.json']['sources']:
        assert old_server['sources'][name]==sources[name], 'Server source changed since installation: '+name
    for name in ('Server.dll','Server.pdb'):
        p=GAME/'bin'/name;assert base.digest(p)==old_server['files'][str(p)]['after'],p
    deps,count=base.verify_imports(('RP9.dll','freelancer.exe'))
    files={GAME/'bin'/name:BUILD/'bin'/name for name in gpu['binaries']}
    config=OUT/'port.ini';config.write_bytes(configuration((GAME/'bin/port.ini').read_bytes()));files[GAME/'bin/port.ini']=config
    previous=json.loads((OUT.parent.parent/'lod/install.json').read_text())
    guards={n:base.digest(Path(n)) for n in previous['guards'] if Path(n) not in files}
    for name in previous['files']:
        p=Path(name)
        if p not in files and p.resolve().is_relative_to(GAME.resolve()):guards[name]=base.digest(p)
    for name in ('Server.dll','Server.pdb'):guards[str(GAME/'bin'/name)]=base.digest(GAME/'bin'/name)
    guards.update(gpu['assets'])
    for shader in ('asteroid_simple.hlsl','surface_material.hlsl'):
        p=GAME/'DATA_EXTRA/SHADERS'/shader
        assert base.digest(p)==sources['DATA_EXTRA/SHADERS/'+shader],p
        guards[str(p)]=base.digest(p)
    plan={'installed':False,'game_launched':False,'cache_cleared':False,'sources':sources,'guards':guards,
        'dependencies':deps,'verified_imports':count,'checks':{n:base.digest(OUT/n) for n in checks},
        'files':{str(p):{'source':str(s),'before':base.digest(p),'after':base.digest(s)} for p,s in files.items()},
        'embedded_animation_bytes':base.verify_resource(BUILD/'bin/freelancer.exe'),'installer':base.digest(Path(__file__))}
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Ready: verified client/RP9 + symbols and one config byte; {count} imports; installed Server unchanged')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert base.digest(Path(__file__))==plan['installer']
    for name,h in plan['checks'].items():assert base.digest(OUT/name)==h,name
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    for name,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/name)==h,name
    before={};after={}
    for name,item in plan['files'].items():
        p=base.safe(Path(name),GAME);source=Path(item['source'])
        assert base.digest(source)==item['after'] and base.digest(p)==item['before'],p
        before[p]=p.read_bytes();after[p]=source.read_bytes()
    written=[]
    try:
        for p,data in after.items():written.append(p);p.write_bytes(data)
        for p,data in after.items():assert p.read_bytes()==data,p
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
        base.verify_resource(GAME/'bin/freelancer.exe')
    except BaseException:
        for p in reversed(written):p.write_bytes(before[p])
        raise
    before.clear();after.clear();plan['installed']=True;PLAN.write_text(json.dumps(plan,indent=2))
    removed=base.cleanup()
    for directory in (OUT/'probe',OUT/'client_probe',OUT/'gpu_probe'):
        for folder,dirs,names in os.walk(base.safe(directory,OUT),followlinks=False):
            for name in dirs:base.safe(Path(folder)/name,directory)
            for name in names:
                p=base.safe(Path(folder)/name,directory)
                if p.suffix.lower() in ('.exe','.dll','.obj','.pdb','.ilk','.lib','.exp','.bin','.texture'):
                    state=p.stat();assert state.st_mtime_ns==p.stat().st_mtime_ns;p.unlink();removed+=state.st_size
    plan['removed_bytes']=removed;PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed and hash-verified native asteroid handoff; cleaned {removed/1024**2:.1f} MiB; game not launched')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
