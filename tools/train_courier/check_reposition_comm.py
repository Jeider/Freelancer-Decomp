"""Run the production comm builder: pickup-base move followed by cargo/destination."""
from pathlib import Path
import subprocess
import sys
import ast
from check_orders import function
from dispatcher_en import clips,REPOSITION_FAMILIES
from prepare_reposition import patch_dispatcher,SOURCE
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env

def main():
    source=SOURCE.read_text(encoding='utf-8');assert patch_dispatcher(source)==source
    tree=ast.parse(source)
    actor=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='EngMaleDispatcher')
    method=next(n for n in actor.body if isinstance(n,ast.FunctionDef) and n.name=='get_lines')
    lines={n.args[0].value:n for n in ast.walk(method) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='L'}
    for code,text in clips(REPOSITION_FAMILIES):
        row=lines[code]
        assert ast.literal_eval(row.args[1])==text
        assert isinstance(row.args[2],ast.Attribute) and row.args[2].attr=='RuleDefaultNoProcess'
    assert 'list(super().get_lines())' in source
    production=(ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    code=r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <map>
#include <vector>
#define FDUMP(...) ((void)0)
unsigned CreateID(char const* name){static std::map<std::string,unsigned> ids;auto& id=ids[name];if(!id)id=unsigned(ids.size());return id;}
template<unsigned N>struct TString {char Data[N]{};};
TString<64> MakeVoiceLineName(char const* family,char const* suffix,unsigned){TString<64> r;std::snprintf(r.Data,64,"%s_01%s",family,suffix);return r;}
struct Costume {unsigned PartIds[4]{};};
struct Point {std::string voice;};
unsigned calls=0;std::vector<unsigned> sent;
namespace pub {
int TranslateGoodToMsgIdPrefix(unsigned,TString<64>& out){std::strcpy(out.Data,"gcs_gen_commodity_comm_basic_meds");return 0;}
namespace SpaceObj {int SendComm(unsigned,unsigned,unsigned,Costume*,unsigned,unsigned* ids,int count,int,float,bool){++calls;sent.assign(ids,ids+count);return 0;}}
}
struct Mission {
    struct {bool audio=true,repositionAudio=true;unsigned voice=CreateID("atc_leg_m01_new"),title=1;std::map<std::string,std::string> commodityVoices={{"comm_basic_meds","gcs_gen_commodity_comm_basic_meds"}};} config;
    std::string commodity="comm_basic_meds";Point source{"pickup_base"};
    unsigned PlayerId=1,questionComm=0,questionListener=0,boardingCommId=0,boardingCommListener=0;
    bool boardingSpoken=false;float boardingCommWait=0;
    unsigned ship(){return 9;}
'''+function(production,'void say(')+r'''
};
int main(){
    Mission m;Point destination{"delivery_base"};m.say("tc_reposition",&destination);
    assert(calls==1 && sent.size()==8);
    char const* expected[]={"tc_reposition_01+","pickup_base","tc_reposition_empty_01-","tc_order_01+",
      "gcs_gen_commodity_comm_basic_meds","tc_destination_01+","delivery_base","tc_collect_01-"};
    for(unsigned i=0;i<8;++i)assert(sent[i]==CreateID(expected[i]));
    m.config.repositionAudio=false;m.say("tc_reposition",&destination);
    assert(calls==2 && sent.size()==5 && sent[0]==CreateID("tc_order_01+"));
    m.config.repositionAudio=true;m.say("tc_next",&destination);
    assert(calls==3 && sent.size()==5 && sent[3]==CreateID("delivery_base"));
    m.say("tc_reposition",nullptr);assert(calls==3);
    puts("PASS: production comm uses pickup base then actual cargo/receiver; one 8-part sequence; 5-part fallback before recordings; no relocation speech for local pickup");
}
'''
    out=ROOT/'src/obj/train_courier/reposition_comm';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'comm.cpp';cpp.write_text(code,encoding='utf-8');compiler,env=compiler_env();exe=out/'comm.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2','/D_CRT_SECURE_NO_WARNINGS',
                    str(cpp),'/Fo'+str(out/'comm.obj'),'/Fe'+str(exe)],env=env,cwd=out,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)
    print('PASS: 20 additional English lines installed in super()-based dispatcher, RuleDefaultNoProcess, idempotent patch')

if __name__=='__main__':main()
