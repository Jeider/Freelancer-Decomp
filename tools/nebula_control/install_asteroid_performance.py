"""Install verified asteroid CPU/buffer/spin changes and three convex SURs."""
from pathlib import Path
import importlib.util,json,os,sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
GAME=Path('D:/Games/FL_MOD')
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff/performance'
BUILD=OUT/'build';PLAN=OUT/'install.json'
base.OUT,base.BUILD=OUT,BUILD

def sources():
    result={GAME/'bin'/n:BUILD/'bin'/n for n in ('Server.dll','Server.pdb','RP9.dll','RP9.pdb','freelancer.exe','freelancer.pdb')}
    result[GAME/'DATA_EXTRA/SHADERS/far_rocks.hlsl']=ROOT/'DATA_EXTRA/SHADERS/far_rocks.hlsl'
    collision=json.loads((OUT/'collision/checks.json').read_text())
    for model in collision['models']:result[Path(model['target'])]=Path(model['staged'])
    gpu=json.loads((OUT/'checks.json').read_text())
    for name,h in gpu['cache_files'].items():
        p=OUT/'gpu_probe/cache'/name;assert base.digest(p)==h
        result[base.cache_path()/name]=p
    return result

def prepare():
    gpu=json.loads((OUT/'checks.json').read_text());assert gpu['passed'] and gpu['cpu']['passed'] and gpu['client']['passed']
    assert gpu['exclusions']==8
    files=sources();checked=dict(gpu['sources']);checks={}
    for name in ('checks.json','client_checks.json','buffer_checks.json','collision/checks.json'):
        p=OUT/name;report=json.loads(p.read_text());assert report['passed'];checked.update(report['sources']);checks[name]=base.digest(p)
    for name,h in checked.items():assert base.digest(ROOT/name)==h,name
    for name,h in gpu['binaries'].items():assert base.digest(BUILD/'bin'/name)==h
    for name,h in gpu['assets'].items():assert base.digest(Path(name))==h
    for model in json.loads((OUT/'collision/checks.json').read_text())['models']:
        assert base.digest(Path(model['target']))==model['original_sha256']
        assert base.digest(Path(model['staged']))==model['staged_sha256']
        assert base.digest(Path(model['model']))==model['model_sha256']
    dependencies,count=base.verify_imports(('Server.dll','RP9.dll','freelancer.exe'))
    # Reuse the previous installation's explicit preservation scope, refreshed to
    # the current installed state. Only the declared new targets are excluded.
    prior=json.loads((OUT.parent/'install.json').read_text())
    guards={n:base.digest(Path(n)) for n in prior['guards'] if Path(n) not in files and Path(n).exists()}
    targets={str(path):{'source':str(source),'before':base.digest(path) if path.exists() else None,'after':base.digest(source)}
             for path,source in files.items()}
    plan={'installed':False,'game_launched':False,'cache_cleared':False,'files':targets,'guards':guards,
          'dependencies':dependencies,'verified_imports':count,'sources':checked,'checks':checks,
          'embedded_animation_bytes':base.verify_resource(BUILD/'bin/freelancer.exe'),'installer':base.digest(Path(__file__))}
    PLAN.write_text(json.dumps(plan,indent=2));print(f'Ready: 6 binaries/symbols, far-rock shader, 3 SURs, {len(gpu["cache_files"])} additive cache entries; {count} imports')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert plan['installer']==base.digest(Path(__file__))
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h
    for name,h in plan['checks'].items():assert base.digest(OUT/name)==h
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h
    for name,h in plan['dependencies'].items():assert base.digest(GAME/'bin'/name)==h
    data_module=GAME/'Assets/Pythonlancer/tools/data_folder.py'
    spec=importlib.util.spec_from_file_location('asteroid_data_folder',data_module)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);data=module.DataFolder(root=GAME)
    before={};after={}
    cache=base.cache_path().resolve()
    for name,item in plan['files'].items():
        path=Path(name);base.safe(path,cache if path.resolve().is_relative_to(cache) else GAME)
        assert (base.digest(path) if path.exists() else None)==item['before']
        source=Path(item['source']);assert base.digest(source)==item['after']
        before[path]=path.read_bytes() if path.exists() else None;after[path]=source.read_bytes()
    def write(path,content):
        if path.is_relative_to(GAME/'DATA'):
            relative=path.relative_to(GAME/'DATA')
            if content is None:data.remove_data_file(relative)
            else:data.sync_data_file(relative,content)
        elif content is None:path.unlink(missing_ok=True)
        else:path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content)
    touched=[]
    try:
        for path,content in after.items():touched.append(path);write(path,content)
        for path,content in after.items():assert path.read_bytes()==content,path
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
        base.verify_resource(GAME/'bin/freelancer.exe')
    except BaseException:
        for path in reversed(touched):write(path,before[path])
        raise
    before.clear();after.clear();plan['installed']=True;PLAN.write_text(json.dumps(plan,indent=2))
    removed=base.cleanup()
    for directory in (OUT/'probe',OUT/'gpu_probe',OUT/'client_probe',OUT/'buffer_probe',OUT/'collision/probe'):
        for folder,dirs,names in os.walk(base.safe(directory,OUT),followlinks=False):
            for name in dirs:base.safe(Path(folder)/name,directory)
            for name in names:
                p=base.safe(Path(folder)/name,directory)
                if p.suffix.lower() in ('.exe','.obj','.pdb','.ilk','.lib','.exp','.bin','.texture','.dmp'):
                    state=p.stat();assert p.stat().st_mtime_ns==state.st_mtime_ns;p.unlink();removed+=state.st_size
    for item in json.loads((OUT/'collision/checks.json').read_text())['models']:
        p=base.safe(item['staged'],OUT/'collision');state=p.stat();p.unlink();removed+=state.st_size
    # Original SURs are retained as small, pinned source references for future editing.
    plan['removed_bytes']=removed;PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed and hash-verified; cleaned {removed/1024**2:.1f} MiB; kept source collision references; no game launch')

if __name__=='__main__':apply() if '--apply' in sys.argv else prepare()
