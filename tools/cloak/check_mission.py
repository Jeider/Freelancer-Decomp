"""Execute production cloak conditions/queue with native Common equipment and INI parsing.

Only mission-label lookup, server ownership and controller delivery are fixtures;
the conditions, queue, observer body, ships, equipment and cooldowns are real code.
"""
from pathlib import Path
import subprocess
import sys
from build_mission import ROOT,OUT,compiler_env

def main():
    cnd=(ROOT/'src/Content/MissionCnd.cpp').read_text()
    methods=cnd[cnd.index('Cnd::Cnd('):cnd.index('// Cnd_BaseEnter / Cnd_BaseExit')]
    server=(ROOT/'src/Server/server_gameobject.cpp').read_text()
    queue=server[server.index('namespace\n{\nstruct CloakMissionQueue'):server.index('// DAT_06d8fb14')]
    observer=server[server.index('void SrvCloak::notify('):server.index('bool SrvCloak::update(')]
    fixture=(ROOT/'tools/cloak/test_mission.cpp').read_text()
    source=OUT/'test_mission.cpp'
    source.write_text(fixture.replace('// PRODUCTION_QUEUE',queue).replace('// PRODUCTION_OBSERVER',observer).replace('// PRODUCTION_CONDITIONS',methods))
    compiler,env=compiler_env()
    env['PATH']='D:/games/FL_MOD/bin;'+env['PATH']
    env['INCLUDE']+=';'+str(ROOT/'src/include')+';'+str(ROOT/'src/Content')
    env['LIB']+=';'+str(ROOT/'bin')
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2','/MD',
        '/DSERVER_EXPORTS','/D_ITERATOR_DEBUG_LEVEL=1','/D_CRT_SECURE_NO_WARNINGS',str(source),
        '/Fo'+str(OUT/'test_mission.obj'),'/Fe'+str(OUT/'test_mission.exe'),'/link','Common.lib','dacom.lib'],
        env=env,cwd=OUT,check=True)
    (OUT/'port.ini').write_text('[Equipment]\ninternal_classes=1\n')
    subprocess.run([str(OUT/'test_mission.exe')],env=env,cwd=OUT,check=True)

if __name__=='__main__':main()
