"""Isolated client relink on top of the installed field_fog build, preserving its inputs."""
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env,digest
OUT=ROOT/'src/obj/cloak_visual'
PREVIOUS=ROOT/'src/obj/field_fog'
SOURCES=('space_scene_obj_draw','render_ex','cloak_visual')


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    prior=json.loads((PREVIOUS/'build.json').read_text())
    installed=digest(Path('D:/games/FL_MOD/bin/freelancer.exe'))
    if installed!=prior['client']:
        previous=json.loads((OUT/'build.json').read_text())
        assert installed==previous['client'],'Installed client changed'
    assert all(digest(Path(p))==h for p,h in prior['inputs'].items()),'Original link input changed'
    assert digest(ROOT/'src/freelancer/Client/cli_asteroid.cpp')==prior['source'],'Field fix source changed'
    extra_obj=PREVIOUS/'cli_asteroid.obj';extra_hash=digest(extra_obj)
    compiler,env=compiler_env()
    files=[ROOT/f'src/freelancer/Client/{name}.cpp' for name in SOURCES]
    files+=[ROOT/'src/freelancer/Client/cloak_geometry.h',ROOT/'src/freelancer/Client/cloak_visual.h',ROOT/'DATA_EXTRA/SHADERS/cloak_refraction.hlsl']
    sources={str(p.relative_to(ROOT)):digest(p) for p in files}
    template=(PREVIOUS/'compile.rsp').read_text()
    link=(PREVIOUS/'link.rsp').read_text()
    for name in SOURCES:
        command=re.sub(r'/Fo"[^"]+"',lambda m:f'/Fo"{OUT/name}.obj"',template,flags=re.I)
        command=re.sub(r'/Fd"[^"]+"',lambda m:f'/Fd"{OUT/name}.pdb"',command,flags=re.I)
        command,count=re.subn(r'[^\s"]+CLI_ASTEROID\.CPP',lambda m:str(ROOT/f'src/freelancer/Client/{name}.cpp'),command,flags=re.I)
        assert count==1
        rsp=OUT/f'{name}.rsp';rsp.write_text(command)
        with (OUT/f'{name}.log').open('wb') as log:
            result=subprocess.run([str(compiler/'cl.exe'),'@'+str(rsp)],cwd=ROOT/'src/freelancer',env=env,stdout=log,stderr=subprocess.STDOUT)
        if result.returncode:print((OUT/f'{name}.log').read_text(errors='replace')[-7000:])
        result.check_returncode();print('PASS compile',name,flush=True)
        if name=='cloak_visual':link+=f'\n"{OUT/name}.obj"\n'
        else:
            link,count=re.subn(rf'"[^"\n]+[\\/]{name}\.OBJ"',lambda m:f'"{OUT/name}.obj"',link,flags=re.I)
            assert count==1
    for key,name in [('OUT','freelancer.exe'),('PDB','freelancer.pdb'),('IMPLIB','freelancer.lib'),('LTCGOUT','freelancer.iobj')]:
        link,count=re.subn(rf'/{key}:"[^"]+"',lambda m:f'/{key}:"{OUT/name}"',link,flags=re.I);assert count==1
    rsp=OUT/'link.rsp';rsp.write_text(link)
    with (OUT/'link.log').open('wb') as log:
        result=subprocess.run([str(compiler/'link.exe'),'@'+str(rsp)],cwd=ROOT/'src/freelancer',env=env,stdout=log,stderr=subprocess.STDOUT)
    if result.returncode:print((OUT/'link.log').read_text(errors='replace')[-7000:])
    result.check_returncode()
    assert digest(extra_obj)==extra_hash
    assert all(digest(Path(p))==h for p,h in prior['inputs'].items()),'Concurrent link input change'
    assert all(digest(ROOT/p)==h for p,h in sources.items()),'Concurrent source change'
    (OUT/'build.json').write_text(json.dumps({'baseline_client':installed,'client':digest(OUT/'freelancer.exe'),
        'sources':sources},indent=2))
    print('PASS isolated client link; installed field_fog and RPG inputs retained')


if __name__=='__main__':main()
