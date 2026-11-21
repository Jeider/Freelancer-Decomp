"""Install/collect a bounded diagnostic renderer; no game launch or shader changes."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/fog_coverage/physical_order/trace'
BUILD=OUT/'build'
GAME=Path('D:/Games/FL_MOD/bin')
PLAN=OUT/'capture_install.json'
CONFIG=GAME/'port.ini'
TAIL=b'\r\n[Diagnostics]\r\nasteroid_fog_capture = 1\r\n'
FILES=('RP9.dll','RP9.pdb')
sys.path.insert(0,str(ROOT/'tools/shader_startup'))
import install_animation as base
base.OUT,base.BUILD=OUT,BUILD

def digest(data):return hashlib.sha256(data).hexdigest()

def prepare():
    report=OUT/'capture_checks.json'
    check=json.loads(report.read_text());assert check['passed']
    assert check['header']==base.digest(ROOT/'src/RP9/RP9FogCapture.h')
    config=CONFIG.read_bytes();assert b'[Diagnostics]' not in config and b'asteroid_fog_capture' not in config
    dependencies,count=base.verify_imports(('RP9.dll',))
    guards={str(GAME/name):base.digest(GAME/name) for name in ('freelancer.exe','freelancer.pdb','Common.dll','Server.dll','Content.dll')}
    for name in ('nebula_volume.hlsl','nebula_composite.hlsl','surface_material.hlsl','far_rocks.hlsl'):
        path=GAME.parent/'DATA_EXTRA/SHADERS'/name
        guards[str(path)]=base.digest(path)
    plan={'files':{name:{'before':base.digest(GAME/name),'after':base.digest(BUILD/'bin'/name)} for name in FILES},
          'config_before':digest(config),'config_after':digest(config+TAIL),'guards':guards,
          'sources':{name:base.digest(ROOT/name) for name in ('src/RP9/RP9FogCapture.h','src/RP9/RP9.cpp','src/RP9/RP9Ex.cpp')},
          'checks':base.digest(report),'dependencies':dependencies,'verified_imports':count,
          'installer':base.digest(Path(__file__)),'shader_changes':False,'game_launched':False,'installed':False}
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Ready: RP9.dll/PDB, {count} verified imports; opt-in capture only, client/shaders protected')

def apply():
    base.idle();plan=json.loads(PLAN.read_text());assert not plan['installed']
    assert base.digest(Path(__file__))==plan['installer']
    assert base.digest(OUT/'capture_checks.json')==plan['checks']
    for name,h in plan['sources'].items():assert base.digest(ROOT/name)==h,name
    for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    for name,h in plan['dependencies'].items():assert base.digest(GAME/name)==h,name
    config=CONFIG.read_bytes();assert digest(config)==plan['config_before']
    before={};after={}
    for name in FILES:
        path=base.safe(GAME/name,GAME)
        before[path]=path.read_bytes();after[path]=(BUILD/'bin'/name).read_bytes()
        assert digest(before[path])==plan['files'][name]['before']
        assert digest(after[path])==plan['files'][name]['after']
    before[CONFIG]=config;after[CONFIG]=config+TAIL
    written=[]
    try:
        for path,data in after.items():
            written.append(path);path.write_bytes(data)
        for path,data in after.items():assert path.read_bytes()==data,path
        for name,h in plan['guards'].items():assert base.digest(Path(name))==h,name
    except BaseException:
        for path in reversed(written):path.write_bytes(before[path])
        raise
    before.clear();after.clear()
    plan['installed']=True
    PLAN.write_text(json.dumps(plan,indent=2))
    plan['removed_bytes']=base.cleanup()
    for name in ('capture.exe','capture.obj'):
        path=base.safe(OUT/'capture_probe'/name,OUT/'capture_probe')
        if path.exists():
            info=path.stat();assert path.stat().st_mtime_ns==info.st_mtime_ns
            path.unlink();plan['removed_bytes']+=info.st_size
    PLAN.write_text(json.dumps(plan,indent=2))
    print(f'Installed and verified RP9 + diagnostic switch; shaders/client unchanged; cleaned {plan["removed_bytes"]/1024**2:.1f} MiB')

def collect():
    from PIL import Image
    plan=json.loads(PLAN.read_text());assert plan['installed']
    folder=Path(os.environ['LOCALAPPDATA'])/'Freelancer-Decomp/Diagnostics/asteroid_fog_capture'
    report=folder/'capture.txt'
    assert report.stat().st_mtime>PLAN.stat().st_mtime,'No new capture after installation'
    lines=report.read_text().splitlines();assert len(lines)==6 and all('HRESULT=00000000' in line for line in lines),lines
    dest=OUT/'frames';dest.mkdir(exist_ok=True)
    for frame in range(2):
        for stage in ('opaque','volume','present'):
            name=f'{frame}_{stage}.png';source=folder/name
            with Image.open(source) as im:im.verify()
            (dest/name).write_bytes(source.read_bytes())
    (dest/'capture.txt').write_bytes(report.read_bytes())
    data=CONFIG.read_bytes()
    assert data.endswith(TAIL),'Configuration edited; restore only diagnostic key manually'
    updated=data[:-len(TAIL)]
    assert CONFIG.read_bytes()==data
    try:
        CONFIG.write_bytes(updated);assert CONFIG.read_bytes()==updated
    except BaseException:
        CONFIG.write_bytes(data);raise
    plan['collected']=True;plan['diagnostic_config_restored']=True
    PLAN.write_text(json.dumps(plan,indent=2))
    print('Collected six matching-stage images and restored diagnostic setting; no rendering changes')

if __name__=='__main__':
    if '--apply' in sys.argv:apply()
    elif '--collect' in sys.argv:collect()
    else:prepare()
