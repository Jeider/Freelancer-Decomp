"""Exercise production counter logic and server storage, with a deterministic game facade."""
from pathlib import Path
import os
import subprocess

repo=Path(__file__).resolve().parents[2]
out=repo/'src/obj/action_counters_check'
out.mkdir(parents=True,exist_ok=True)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/version/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')]))
def run(source,name):
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT',
                    '/I'+str(repo/'src/include'),'/I'+str(repo/'src/Server'),str(source),'/Fe'+name+'.exe'],
                   cwd=out,env=env,check=True)
    subprocess.run([str(out/(name+'.exe'))],cwd=out,check=True)
run(repo/'tools/action_counters/check_core.cpp','core')
server=(repo/'src/Server/server_action_stats.cpp').read_text()
server=server[server.index('namespace ServerActionStats {'):]
(out/'server.cpp').write_text((repo/'tools/action_counters/server_fixture.h').read_text()+'\n'+server+'\n'+
                             (repo/'tools/action_counters/check_server.cpp').read_text())
run(out/'server.cpp','server')
values={}
for line in (out/'roundtrip.ini').read_text().splitlines():
    key,entry=line.split('=',1)
    assert key.strip()=='action_counter'
    name,value=entry.strip().split(',')
    assert name not in values
    values[name]=float(value)
assert values['inertia_seconds']==999.75
assert values['confirmed_buy_transactions']==1 and values['units_bought']==2
assert values['trade_credits_received']==70 and values['nanobots_used']==2
assert 'credited_kills' not in values  # Client cannot claim server counters.
print('PASS: independent parse of persisted named counters and fractional progress')
