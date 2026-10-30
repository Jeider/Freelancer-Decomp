"""Exercise production key routing, mode selection and saved keymap migration."""
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/flight_action_hotkeys_check'


def extract(source, signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end] + '\n'


STUB = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <cstdlib>
#include <fstream>
#include <sstream>
#include <algorithm>
#include "player_flight_actions.h"
#include "menu_keymap_config.h"
bool feature=true,screen=false,letterbox=false,focus=false,blocked=false,dying=false;
bool launching=false,lane=false,cruise=false,capable=true,havePlayer=true;
struct IBehaviorManager {int CurrentBehaviorIndex=0x13;bool LockManeuversByte=false;} testBehavior;
struct CShip {
    IBehaviorManager* get_behavior_interface(){return &testBehavior;}
    bool is_launching(){return launching;}bool is_using_tradelane(){return lane;}
    bool is_cruise_active(){return cruise;}
} testShip;
struct IObjRW {bool is_dying(){return dying;}} obj;
CShip* HudShipOfObjRw(IObjRW* p){return p?&testShip:nullptr;}
IObjRW* GetPlayerObjRW(){return havePlayer?&obj:nullptr;}
bool HudIsMousePickBlocked(){return blocked;}
bool IsLetterboxVisible(){return letterbox;}
bool HudGetInputFocus(){return focus;}
bool& G_bNnScreenUp=screen;
struct Record {unsigned Modifiers=0;unsigned char Byte18=1,Byte19=0;} record;
Record* HudCommandRecord(){return &record;}
unsigned nativeCalls=0,begins=0;int lastAction=-1;
int HudDispatchCommand(unsigned,int){++nativeCalls;return 0;}
namespace FlightTelemetry {
enum class Origin {MappedInput};struct OriginScope{OriginScope(Origin){}};
void Input(unsigned,int,bool,bool,unsigned){}
}
namespace PlayerFlightActions {
enum Kind {SpiralClockwise,ReverseTurn,ReverseStrafe,GotoWeave,Count,None};
bool enabled(){return feature;}bool Enabled(){return feature;}
IObjRW* player(){return GetPlayerObjRW();}
bool supported(Kind,CShip*){return capable;}
void begin(Kind k){++begins;lastAction=k;}
}
std::list<FKeyCmd> GKeyCmds;
constexpr unsigned kKeyCmdNicknameCount=0xd3;
char const* const GKeyCmdNicknames[]={
#include "menu_keymap_nicknames.inc"
};
static_assert(sizeof(GKeyCmdNicknames)/sizeof(*GKeyCmdNicknames)==kKeyCmdNicknameCount);
FKeyCmd* FindKeyCmdByNicknameId(unsigned id){for(auto& c:GKeyCmds)if(c.NicknameId==id)return &c;return nullptr;}
unsigned ResolveNicknameId(char const* n){for(unsigned i=0;i<kKeyCmdNicknameCount;++i)if(!strcmp(n,GKeyCmdNicknames[i]))return i;return 0;}
#define MAX_PATH 260
void GetFileSysPath(char* out,char const* in,void*){strcpy(out,in);}
std::string trim(std::string s){auto a=s.find_first_not_of(" \t\r");if(a==std::string::npos)return {};return s.substr(a,s.find_last_not_of(" \t\r")-a+1);}
struct Section {std::string name;std::vector<std::pair<std::string,std::string>> values;};
struct INI_Reader {
    std::vector<Section> sections;int header=-1,value=-1;
    bool open(char const* path,bool){
        std::ifstream in(path);if(!in)return false;std::string line;
        while(std::getline(in,line)){
            line=trim(line.substr(0,line.find(';')));if(line.empty())continue;
            if(line.front()=='['&&line.back()==']')sections.push_back({line.substr(1,line.size()-2),{}});
            else if(!sections.empty()){auto eq=line.find('=');if(eq!=std::string::npos)sections.back().values.push_back({trim(line.substr(0,eq)),trim(line.substr(eq+1))});}
        }return true;
    }
    bool read_header(){value=-1;return ++header<static_cast<int>(sections.size());}
    bool is_header(char const* n){return sections[header].name==n;}
    bool read_value(){return ++value<static_cast<int>(sections[header].values.size());}
    bool is_value(char const* n){return sections[header].values[value].first==n;}
    char const* get_value_string(){return sections[header].values[value].second.c_str();}
};
bool ParseKeyValue(INI_Reader& r,FKeyBinding* b){
    std::string s=r.get_value_string();b->VirtualKey=std::atoi(s.c_str());
    b->Modifiers=s.find("CONTROL")!=s.npos?kKeyModControl:s.find("SHIFT")!=s.npos?kKeyModShift:s.find("ALT")!=s.npos?kKeyModAlt:0;
    return b->VirtualKey!=0;
}
'''

CHECK = r'''
int main(){
    using namespace PlayerFlightActions;
    for(int mode: {0x13,2,3,10,-1}){
        testBehavior.CurrentBehaviorIndex=mode;
        for(unsigned id=FirstCommand;id<FirstCommand+CommandCount;++id){
            unsigned old=begins;assert(DispatchKeyCommand(id,1));
            int expected=mode==0x13?static_cast<int>(id-FirstCommand):mode==2&&id==FirstCommand?3:-1;
            assert(begins==old+(expected>=0?1:0));if(expected>=0)assert(lastAction==expected);
        }
    }
    testBehavior.CurrentBehaviorIndex=2;
    unsigned old=begins;
    for(bool* gate:{&focus,&screen,&letterbox,&blocked,&dying,&launching,&lane,&testBehavior.LockManeuversByte}){
        *gate=true;DispatchKeyCommand(FirstCommand,1);assert(begins==old);*gate=false;
    }
    record.Byte19=1;DispatchKeyCommand(FirstCommand,1);assert(begins==old);record.Byte19=0;
    record.Byte18=0;DispatchKeyCommand(FirstCommand,1);assert(begins==old);record.Byte18=1;
    havePlayer=false;DispatchKeyCommand(FirstCommand,1);assert(begins==old);havePlayer=true;
    capable=false;DispatchKeyCommand(FirstCommand,1);assert(begins==old);capable=true;
    feature=false;DispatchKeyCommand(FirstCommand,1);assert(begins==old);feature=true;
    cruise=true;DispatchKeyCommand(FirstCommand,1);assert(begins==old+1); // F2 weave works in cruise.
    testBehavior.CurrentBehaviorIndex=0x13;DispatchKeyCommand(FirstCommand,1);assert(begins==old+1);cruise=false;
    assert(ResolveNicknameId("USER_PLAYER_EVADE")==FirstCommand);
    assert(ResolveNicknameId("USER_PLAYER_REVERSE_TURN")==FirstCommand+1);
    assert(ResolveNicknameId("USER_PLAYER_REVERSE_STRAFE")==FirstCommand+2);
    unsigned goToId=ResolveNicknameId("USER_MANEUVER_GOTO");
    GKeyCmds.push_back({goToId,1,1,kKeyCmdStateKeyDown,{}});
    for(unsigned i=0;i<CommandCount;++i)GKeyCmds.push_back({FirstCommand+i,KeyIdsBase+i,KeyIdsBase+i,kKeyCmdStateKeyDown,{}});
    for(unsigned i=0;i<CommandCount;++i)assert(FindKeyCmdByNicknameId(FirstCommand+i)->Bindings.empty());
    // An old user map keeps its controls; new actions remain unassigned.
    {std::ofstream f("legacy.ini");f<<"[KeyMap=1.1]\n[KeyCmd]\nnickname = USER_MANEUVER_GOTO\nkey = 49,CONTROL\n";}
    assert(LoadUserKeyMapIni("legacy.ini")==1);
    assert(FindKeyCmdByNicknameId(FirstCommand)->Bindings.empty());
    assert(FindKeyCmdByNicknameId(FirstCommand+1)->Bindings.empty());
    assert(FindKeyCmdByNicknameId(FirstCommand+2)->Bindings.empty());
    assert(FindKeyCmdByNicknameId(goToId)->Bindings[0].VirtualKey==49);
    // Rebinding and explicitly unbinding survive save/reload, including an empty command.
    FindKeyCmdByNicknameId(FirstCommand+1)->Bindings={{'K',kKeyModAlt}};
    FindKeyCmdByNicknameId(FirstCommand+2)->Bindings.clear();
    assert(SaveUserKeyMapIni("saved.ini"));
    assert(LoadUserKeyMapIni("saved.ini")==4);
    assert(FindKeyCmdByNicknameId(FirstCommand)->Bindings.empty());
    assert(FindKeyCmdByNicknameId(FirstCommand+1)->Bindings[0].VirtualKey=='K');
    assert(FindKeyCmdByNicknameId(FirstCommand+2)->Bindings.empty());
    puts("PASS: contextual freeflight/F2 routing; repeats, releases, UI focus, modal, death, launch, lane, cruise and disabled gates");
    puts("PASS: command IDs without auto-turrets, unassigned actions, old user controls preserved, saved rebind/unbind");
}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    actions = (ROOT / 'src/freelancer/Client/player_flight_actions.cpp').read_text()
    keymap = (ROOT / 'src/freelancer/Client/menu_keymap.cpp').read_text()
    code = STUB + '\nnamespace PlayerFlightActions {\n' + extract(actions, 'bool valid(') + extract(actions, 'bool Command(') + '}\n'
    for signature in ('bool DispatchKeyCommand(', 'int LoadUserKeyMapIni(', 'int SaveUserKeyMapIni('):
        code += extract(keymap, signature)
    (OUT / 'check.cpp').write_text(code + CHECK)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include', ROOT/'src/freelancer/Client'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')])
    env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo','/std:c++17','/W4','/WX','/wd4996','/EHsc','/MT',
                    '/DFREELANCER_PLAYER_FLIGHT_ACTIONS','check.cpp','/Fecheck.exe'], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT/'check.exe')], cwd=OUT, check=True)


if __name__ == '__main__':
    main()
