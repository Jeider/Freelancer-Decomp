"""Isolated Server/Content relink retaining installed binaries' other features."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env,digest
OUT=ROOT/'src/obj/cloak_mission'
GAME=Path('D:/games/FL_MOD/bin')
SNAP=OUT/'snapshot/src'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    compiler,env=compiler_env()
    source_paths=['src/Content/MissionCnd.cpp','src/Content/MissionScript.cpp','src/Content/MissionCnd.h',
        'src/Server/IServerImpl.cpp','src/Server/server_gameobject.cpp','src/include/server_gameobject.h','src/include/common_server_controller.h']
    sources={p:digest(ROOT/p) for p in source_paths}
    for directory in ('include','Server','Content','IVP'):
        for p in (ROOT/'src'/directory).rglob('*.h'):
            dest=SNAP/p.relative_to(ROOT/'src');dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dest)
    for rel in source_paths:
        if rel.endswith('.cpp'):shutil.copy2(ROOT/rel,SNAP/Path(rel).relative_to('src'))
    # These actions are being built separately and are not in the installed Content
    # baseline. Keep that working-tree change intact, but do not partially link it.
    script=SNAP/'Content/MissionScript.cpp'
    script.write_text(''.join(line for line in script.read_text().splitlines(True)
        if '"Act_CacheShipAndSetLoadout"' not in line and '"Act_RestoreCachedShip"' not in line))
    records={}
    for project,baseline,tlog,names in [
        ('Server',ROOT/'bin/Server.dll',ROOT/'src/obj/Server/Release/Server.tlog',('IServerImpl','server_gameobject')),
        ('Content',ROOT/'src/obj/rpg_contacts/build_Release_1/bin/Content.dll',ROOT/'src/obj/rpg_contacts/build_Release_1/obj/Content.tlog',('MissionCnd','MissionScript'))]:
        assert digest(baseline)==digest(GAME/(project+'.dll')),project+' installed baseline changed'
        lines=(tlog/'CL.command.1.tlog').read_text(encoding='utf-16').splitlines()
        commands={Path(line[1:]).stem.lower():lines[i+1] for i,line in enumerate(lines) if line.startswith('^')}
        ll=(tlog/'link.command.1.tlog').read_text(encoding='utf-16').splitlines()
        starts=[i for i,line in enumerate(ll) if line.startswith('^')]+[len(ll)]
        blocks=[ll[a:b] for a,b in zip(starts,starts[1:])]
        blocks=[b for b in blocks if Path(re.search(r'/OUT:"([^"]+)"',b[1],re.I)[1]).resolve()==baseline.resolve()]
        assert len(blocks)==1,'Need exact baseline link record'
        ll=blocks[0]
        inputs=[Path(p) for p in ll[0][1:].split('|')]
        hashes={str(p):digest(p) for p in inputs}
        newer=[p for p in inputs if p.stat().st_mtime>baseline.stat().st_mtime]
        assert not newer,newer
        link='\n'.join(ll[1:])
        def compile_unit(name):
            command=commands[name.lower()]
            command=re.sub(r'/Fo"[^"]+"',lambda m:f'/Fo"{OUT/name}.obj"',command,flags=re.I)
            command=re.sub(r'/Fd"[^"]+"',lambda m:f'/Fd"{OUT/name}.pdb"',command,flags=re.I)
            command=re.sub(re.escape(str(ROOT/'src/include')),lambda m:str(SNAP/'include'),command,flags=re.I)
            command=re.sub(r'[^\s"]+\\'+re.escape(name)+r'\.CPP',lambda m:str(SNAP/project/(name+'.cpp')),command,flags=re.I)
            rsp=OUT/(name+'.rsp');rsp.write_text(command)
            log=OUT/(name+'.log')
            with log.open('wb') as stream:r=subprocess.run([str(compiler/'cl.exe'),'@'+str(rsp)],cwd=SNAP/project,env=env,stdout=stream,stderr=subprocess.STDOUT)
            if r.returncode:print(log.read_text(errors='replace')[-7000:])
            r.check_returncode();print('PASS compile',name,flush=True)
        def replace_obj(command,name):
            command,n=re.subn(r'"[^"\n]+[\\/]'+re.escape(name)+r'\.OBJ"',lambda m:f'"{OUT/name}.obj"',command,flags=re.I);assert n==1
            return command
        def link_dll(command,tag):
            for key,suffix in [('OUT','.dll'),('PDB','.pdb'),('IMPLIB','.lib'),('LTCGOUT','.iobj')]:
                command=re.sub('/'+key+r':"[^"]+"',lambda m:f'/{key}:"{OUT/tag}{suffix}"',command,flags=re.I)
            rsp=OUT/(tag+'_link.rsp');rsp.write_text(command)
            log=OUT/(tag+'_link.log')
            with log.open('wb') as stream:r=subprocess.run([str(compiler/'link.exe'),'@'+str(rsp)],cwd=ROOT/'src'/project,env=env,stdout=stream,stderr=subprocess.STDOUT)
            if r.returncode:print(log.read_text(errors='replace')[-7000:])
            r.check_returncode()
        if project=='Content':
            link=re.sub(r'(?i)(?<![\w/\\])SERVER\.LIB\b',lambda m:'"'+str(OUT/'Server.lib')+'"',link)
        for name in names:compile_unit(name);link=replace_obj(link,name)
        link_dll(link,project)
        assert all(digest(Path(p))==h for p,h in hashes.items()),'Concurrent link input change'
        records[project]={'before':digest(baseline),'after':digest(OUT/(project+'.dll')),'inputs':hashes}
        print('PASS isolated link',project,flush=True)
    assert all(digest(ROOT/p)==h for p,h in sources.items()),'Concurrent source change'
    (OUT/'build.json').write_text(json.dumps({'modules':records,'sources':sources},indent=2))

if __name__=='__main__':main()
