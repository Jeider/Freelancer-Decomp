"""Run production procedural asteroid lifecycle/protocol code with controlled engine fixtures."""
from pathlib import Path
import importlib.util
import json
import hashlib
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'out/graphics_settings/nebula_asteroid_mesh/handoff'
sys.path.insert(0,str(ROOT/'tools'))
from build_asf_hq import compiler_env
spec=importlib.util.spec_from_file_location('legacy',ROOT/'tools/physics/check_server_asteroid_fields.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)

def replace(text,old,new):
    assert old in text,old
    return text.replace(old,new)

def main():
    probe=OUT/'probe';probe.mkdir(parents=True,exist_ok=True)
    stub=legacy.STUB
    stub=replace(stub,'unsigned id=7;','unsigned id=7,system=1;')
    stub=replace(stub,'} zone,excluded;','} zone,excluded,nebula,clearing;')
    stub=replace(stub,'get_zone(unsigned,char const* name){','get_zone(unsigned,char const* name){if(!strcmp(name,"nebula"))return &nebula;if(!strcmp(name,"clearing"))return &clearing;')
    stub=replace(stub,'GameObject* Server_LookupGameObject(unsigned id){','unsigned objectLookups=0;GameObject* Server_LookupGameObject(unsigned id){++objectLookups;')
    stub=replace(stub,'GetSystem()const{return 1;}','GetSystem()const{return system;}')
    stub=replace(stub,'struct System {char const*','struct System {unsigned id=1;char const*')
    stub=replace(stub,'GetId(){return 1;}','GetId(){return id;}')
    stub=replace(stub,'struct Player {unsigned ship_object_id=0;} Players[4];',
        'struct Player {unsigned ship_object_id=0,system_id=1;}; struct PlayerList {Player p[8];Player& operator[](unsigned id){return p[id];}bool is_valid(unsigned id){return id>0&&id<8;}} Players;')
    stub=replace(stub,'&&ci.Orientation.w==1','')
    # Retain exact quaternion in the controlled physics fixture.
    stub=replace(stub,'struct Matrix {float','struct Matrix {Quaternion q;float')
    stub=replace(stub,'void Server_MatrixToQuat(Quaternion&, Matrix const&){}','void Server_MatrixToQuat(Quaternion& q, Matrix const& m){q=m.q;}')
    stub=replace(stub,'objectsById[s->id]=s;', 's->raw.Orientation.q=ci.Orientation;objectsById[s->id]=s;')
    stub=replace(stub,'struct GameObject {','''
struct Watchable {std::shared_ptr<int> life=std::make_shared<int>(0);};
struct IObjRW:Watchable {};
struct BaseWatcher {Watchable const* pointer=nullptr;std::weak_ptr<int> life;
void set(Watchable const* p){pointer=p;life=p?p->life:std::weak_ptr<int>{};}
Watchable const* target()const{return life.expired()?nullptr:pointer;}};
struct GameObject:IObjRW {''')
    stub+='''
#include "procedural_asteroids.h"
int decorationsOnly=0;
int PortConfigInt(char const*,char const* key,int fallback){return !strcmp(key,"procedural_asteroid_decor_only")?decorationsOnly:fallback;}
using DWORD=unsigned long;
DWORD GetTickCount(){return 2000;}
struct CHAT_ID {unsigned Id;explicit CHAT_ID(unsigned id):Id(id){}};
std::vector<std::vector<unsigned char>> sent;
struct IChatClient {void SendCommonChatMsg(CHAT_ID,CHAT_ID,unsigned size,void const* p){
auto* bytes=static_cast<unsigned char const*>(p);sent.emplace_back(bytes,bytes+size);}} chat;
IChatClient* g_pChatClientInterface=&chat;
'''
    source=(ROOT/'src/Server/server_asteroid_fields.cpp').read_text()
    body='\n'.join(line for line in source.splitlines() if not line.startswith('#include') or 'server_procedural_asteroids.inl' in line)
    body=body.replace('#include "server_procedural_asteroids.inl"',(ROOT/'src/Server/server_procedural_asteroids.inl').read_text())
    checks=(ROOT/'tools/nebula_control/check_asteroid_handoff.cpp').read_text()
    old=legacy.CHECK.replace('int main(){','int LegacyMain(){').replace('\n}\n','\nreturn 0;\n}\n')
    (probe/'check.cpp').write_text(stub+body+old+checks)
    compiler,env=compiler_env()
    args=[str(compiler/'cl.exe'),'/nologo','/std:c++17','/O2','/EHsc','/MT','/W4','/WX','/wd4996',
        '/I'+str(ROOT/'src/include'),'check.cpp','/Fecheck.exe']
    for name,cmd in [('build_cpu',args),('result_cpu',[str(probe/'check.exe')])]:
        with (OUT/(name+'.log')).open('wb') as log:
            result=subprocess.run(cmd,cwd=probe,env=env,stdout=log,stderr=subprocess.STDOUT)
        print((OUT/(name+'.log')).read_text(errors='replace')[-7000:]);result.check_returncode()
    sources=['src/include/procedural_asteroids.h','src/include/procedural_asteroid_replica.h',
             'src/Server/server_asteroid_fields.cpp','src/Server/server_procedural_asteroids.inl']
    (OUT/'cpu_checks.json').write_text(json.dumps({'passed':True,'sources':{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in sources}},indent=2))

if __name__=='__main__':main()
