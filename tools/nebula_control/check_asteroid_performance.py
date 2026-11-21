"""Compile production client + placement code with controlled engine fixtures."""
from pathlib import Path
import json,subprocess,hashlib
from check_asteroid_mesh import compiler_env,ROOT
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff/performance'
def main():
    probe=OUT/'client_probe';probe.mkdir(parents=True,exist_ok=True)
    source=ROOT/'src/freelancer/Client/procedural_asteroid_client.cpp'
    (probe/'client_production.inl').write_text('\n'.join(line for line in source.read_text().splitlines() if not line.startswith('#include')))
    draw=(ROOT/'src/freelancer/Client/space_scene_obj_draw.cpp').read_text()
    draw=draw[draw.index('    void FZItemGameObject::Draw('):draw.index('    int FZItemGameObject::Slot04()')]
    (probe/'native_submit.inl').write_text(draw)
    compiler,env=compiler_env()
    cmd=[str(compiler/'cl.exe'),'/nologo','/std:c++17','/O2','/MT','/EHsc','/W4',
         '/DFREELANCER_RP9','/I'+str(ROOT/'src/include'),'/I'+str(ROOT/'src/freelancer/Client'),'/I'+str(probe),
         str(ROOT/'tools/nebula_control/check_asteroid_performance.cpp'),'/Fecheck.exe']
    for name,args in [('build_client',cmd),('result_client',[str(probe/'check.exe')])]:
        result=subprocess.run(args,cwd=probe,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (OUT/(name+'.log')).write_bytes(result.stdout);print(result.stdout.decode(errors='replace'));result.check_returncode()
    files=['src/freelancer/Client/procedural_asteroid_client.cpp','src/freelancer/Client/procedural_asteroid_mesh.inl',
           'src/freelancer/Client/procedural_asteroid_client.h','src/freelancer/Client/client_objdb.cpp',
           'src/freelancer/Client/space_scene_obj_draw.cpp',
           'tools/nebula_control/check_asteroid_performance.cpp','tools/nebula_control/check_asteroid_performance.py']
    (OUT/'client_checks.json').write_text(json.dumps({'passed':True,'sources':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in files}},indent=2))
if __name__=='__main__':main()
