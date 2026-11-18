"""Exercise the actual courier voice selection and comm builder in both languages."""
from pathlib import Path
import subprocess
import sys
from check_orders import function

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools/nebula_control'))
from build_asf_hq import compiler_env


def main():
    source = (ROOT/'src/Content/TrainCourier.cpp').read_text(encoding='utf-8')
    selection = source[source.index('char const* language=PortVoice();'):source.index('        if(!OpenContentDataIni("Missions\\\\TrainCourier\\\\catalog.ini"')]
    code = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
#include <map>
#define FDUMP(...) ((void)0)
unsigned CreateID(char const* s){static std::map<std::string,unsigned> ids;auto& id=ids[s];if(!id)id=unsigned(ids.size());return id;}
std::string languageSetting="ru";
char const* PortVoice(){return languageSetting.c_str();}
template<unsigned N>struct TString {char Data[N]{};};
TString<64> MakeVoiceLineName(char const* family,char const* suffix,unsigned){TString<64> r;std::snprintf(r.Data,64,"%s_01%s",family,suffix);return r;}
struct Costume {unsigned PartIds[4]{};};
struct Point {std::string voice;};
enum class CommResult {CANCELLED};
unsigned calls=0,sentVoice=0;std::vector<unsigned> sent;
namespace pub {
int TranslateGoodToMsgIdPrefix(unsigned,TString<64>& out){std::strcpy(out.Data,"gcs_gen_commodity_comm_basic_meds");return 0;}
namespace SpaceObj {int SendComm(unsigned,unsigned,unsigned voice,Costume*,unsigned,unsigned* ids,int count,int,float,bool){++calls;sentVoice=voice;sent.assign(ids,ids+count);return 0;}}
}
struct Config {
    bool audio=true,repositionAudio=true,evacuationAudio=true,composedAudio=true;
    unsigned voice=CreateID("atc_leg_m01_new"),voiceRu=CreateID("dispatcher01"),voiceEn=CreateID("atc_leg_m01_new"),title=1;
    std::map<unsigned,std::map<unsigned,bool>> unvoicedCargo;
    std::map<std::string,std::string> commodityVoices={{"comm_basic_meds","gcs_gen_commodity_comm_basic_meds"}};
    void select(){
''' + selection + r'''
    }
};
struct Mission {
    Config config;
    std::string commodity="comm_basic_meds";Point source{"pickup_base"};
    unsigned PlayerId=1,questionComm=0,questionListener=0,boardingCommId=0,boardingCommListener=0;
    bool boardingSpoken=false;float boardingCommWait=0;
    unsigned ship(){return 9;}
''' + function(source,'void say(') + r'''
};
void check(std::initializer_list<char const*> names){assert(sent.size()==names.size());unsigned i=0;for(auto name:names)assert(sent[i++]==CreateID(name));}
int main(){
    for(auto language:{"ru","en"}){
        languageSetting=language;Mission m;m.config.select();Point destination{"delivery_base"};
        unsigned expectedVoice=CreateID(!strcmp(language,"ru")?"dispatcher01":"atc_leg_m01_new");
        m.say("tc_pickup",&destination);
        assert(sentVoice==expectedVoice);
        check({"tc_order_01+","gcs_gen_commodity_comm_basic_meds","tc_destination_01+","delivery_base","tc_collect_01-"});
        m.say("tc_reposition",&destination);
        check({"tc_reposition_01+","pickup_base","tc_reposition_empty_01-","tc_order_01+","gcs_gen_commodity_comm_basic_meds","tc_destination_01+","delivery_base","tc_collect_01-"});
        m.config.unvoicedCargo[CreateID("dispatcher01")][CreateID("gcs_gen_commodity_comm_basic_meds")]=true;
        m.say("tc_pickup",&destination);
        if(!strcmp(language,"ru")) {
            check({"tc_destination_01+","delivery_base","tc_collect_01-"});
            m.say("tc_reposition",&destination);
            check({"tc_reposition_01+","pickup_base","tc_reposition_empty_01-","tc_destination_01+","delivery_base","tc_collect_01-"});
        } else check({"tc_order_01+","gcs_gen_commodity_comm_basic_meds","tc_destination_01+","delivery_base","tc_collect_01-"});
        for(auto family:{"tc_depart","tc_park"}){
            m.say(family,&destination);assert(sent.size()==2 && sent[1]==CreateID("delivery_base"));
            assert(sent[0]==CreateID((std::string(family)+"_01+").c_str()));
        }
        m.say("te_departed");check({"te_departed_01-"});assert(sentVoice==expectedVoice);
        unsigned before=calls;m.config.evacuationAudio=false;m.say("te_departed");assert(calls==before);
        m.config.audio=false;m.say("tc_board");assert(calls==before);
        m.config.audio=true;m.say("tc_pickup",nullptr);assert(calls==before);
    }
    languageSetting="ru";Config legacy;legacy.voiceRu=legacy.voiceEn=0;legacy.composedAudio=false;legacy.select();
    assert(legacy.voice==CreateID("atc_leg_m01_new") && legacy.composedAudio);
    legacy.voice=CreateID("dispatcher01");legacy.composedAudio=false;legacy.select();assert(!legacy.composedAudio);
    puts("PASS: RU/EN selection, joined cargo/destination/reposition, parking, post-exit voice, disabled/missing input, legacy fallback");
}
'''
    out=ROOT/'out/train_courier/audio_ru/checks'
    out.mkdir(parents=True,exist_ok=True)
    cpp=out/'languages.cpp';cpp.write_text(code,encoding='utf-8')
    compiler,env=compiler_env();exe=out/'languages.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/EHsc','/std:c++17',str(cpp),'/Fo'+str(out/'languages.obj'),'/Fe'+str(exe)],env=env,cwd=out,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)


if __name__=='__main__':
    main()
