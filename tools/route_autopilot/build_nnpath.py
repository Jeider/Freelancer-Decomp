"""Relink only player_route.cpp against the currently installed client baseline."""
from pathlib import Path
import json
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env,digest

OUT=ROOT/'src/obj/route_autopilot/nnpath'
GAME=Path('D:/Games/FL_MOD')
TLOG=ROOT/'src/obj/freelancer/Release/freelancer.tlog'


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    client=ROOT/'bin/freelancer.exe'
    assert digest(client)==digest(GAME/'bin/freelancer.exe'),'Installed client differs from link baseline'
    rows=(TLOG/'CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
    matches=[rows[i+1] for i,r in enumerate(rows) if r.startswith('^') and r.lower().endswith('\\player_route.cpp')]
    assert len(matches)==1
    command=matches[0]
    assert '/D FREELANCER_RPG_WORLD ' in command and '/D FREELANCER_PLAYER_FLIGHT_ACTIONS ' in command
    command=re.sub(r'/Fo"[^"]+"',lambda m:f'/Fo"{OUT/"player_route.obj"}"',command,flags=re.I)
    command=re.sub(r'/Fd"[^"]+"',lambda m:f'/Fd"{OUT/"compile.pdb"}"',command,flags=re.I)
    rows=(TLOG/'link.command.1.tlog').read_text(encoding='utf-16').splitlines()
    assert sum(r.startswith('^') for r in rows)==1
    link='\n'.join(rows[1:])
    inputs=[Path(p) for p in rows[0][1:].split('|')]
    inputs.extend(Path(p) for p in re.findall(r'"([^"\n]+\.res)"',link,re.I))
    assert all(p.stat().st_mtime<=client.stat().st_mtime for p in inputs),'Link inputs changed after baseline'
    hashes={str(p):digest(p) for p in inputs}
    # Bind libraries to the paths actually recorded by the original link.
    for p in inputs:
        if p.suffix.lower()=='.lib':
            link=re.sub(r'(?<![\w\\/])'+re.escape(p.name)+r'(?![\w])',lambda m:'"'+str(p)+'"',link,flags=re.I)
    for key,name in [('OUT','freelancer.exe'),('PDB','freelancer.pdb'),('IMPLIB','freelancer.lib'),('LTCGOUT','freelancer.iobj')]:
        link,n=re.subn(rf'/{key}:"[^"]+"',lambda m:f'/{key}:"{OUT/name}"',link,flags=re.I)
        assert n==1,key
    link,n=re.subn(r'"[^"\n]+[\\/]PLAYER_ROUTE\.OBJ"',lambda m:f'"{OUT/"player_route.obj"}"',link,flags=re.I)
    assert n==1
    compiler,env=compiler_env()
    for name,tool,text in [('compile','cl.exe',command),('link','link.exe',link)]:
        rsp=OUT/(name+'.rsp');rsp.write_text(text)
        log=OUT/(name+'.log')
        with log.open('wb') as stream:
            result=subprocess.run([str(compiler/tool),'@'+str(rsp)],cwd=ROOT/'src/freelancer',env=env,
                                  stdout=stream,stderr=subprocess.STDOUT)
        if result.returncode:print(log.read_text(errors='replace')[-10000:])
        result.check_returncode()
        print('PASS:',name,flush=True)
    assert all(digest(Path(p))==h for p,h in hashes.items()),'Concurrent baseline change'
    manifest={'files':{name:{'before':digest(GAME/'bin'/name),'after':digest(OUT/name)}
                       for name in ('freelancer.exe','freelancer.pdb')},
              'dependencies':{name:digest(GAME/'bin'/name) for name in ('Common.dll','Server.dll','Content.dll')},
              'inputs':hashes,'source':digest(ROOT/'src/freelancer/Client/player_route.cpp')}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2))


if __name__=='__main__':
    sys.stdout.reconfigure(errors='replace')
    main()
