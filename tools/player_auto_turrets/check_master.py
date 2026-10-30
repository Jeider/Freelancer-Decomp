"""Exercise production master/ownership functions without touching a game or save."""
from pathlib import Path
import os
import subprocess
repo=Path(__file__).resolve().parents[2]
out=repo/'src/obj/auto_turret_master_check';out.mkdir(parents=True,exist_ok=True)
source=(repo/'src/freelancer/Client/player_auto_turrets.cpp').read_text()

def extract(text, signature):
    start=text.index(signature);end=text.index('{',start)+1;depth=1
    while depth:
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    return text[start:end]+'\n'

stub=r'''
#include <cassert>
#include <cstdio>
#include <algorithm>
#include <vector>
struct CEquip { bool active=true;bool IsActive()const{return active;} };
struct CEGun:CEquip { struct Name { char const* Value="hp01"; } name;
    Name const& GetParentHPName(){return name;} };
struct Equipment { CEquip* gun=nullptr;CEquip* FindByID(unsigned short){return gun;} };
struct CEqObj { Equipment EquipManager; };
struct IObjAffect {};
struct FClientEquippedObj:IObjAffect { CEqObj* Object=nullptr; };
struct Vector {};
bool single=true;bool SinglePlayer(){return single;}
unsigned GetPlayerConnectionId(){return 1;}
unsigned fires=0;
void CliShipFireWeaponsImpl(void*,unsigned short*,int,Vector const*,int,bool,bool* fired){++fires;*fired=true;}
namespace PlayerAutoTurrets {
enum class Mode { Manual, Hostiles };
enum class Status { Off, Ready };
struct MemberState { CEGun* identity=nullptr;bool selected=true,manual=false; };
std::vector<MemberState> members;
Mode mode=Mode::Hostiles;Status status=Status::Ready;
bool energyHold=false,automaticActivation=false,enabled=true,saved=true;
int owner=1;unsigned attacksReset=0,armed=0,released=0,memberWrites=0,reserve=35,savedReserve=35;
int Resolve(int v){return v;}int Player(){return 1;}
bool Enabled(){return enabled;}
void Reconcile(){}
void ResetAttacks(){++attacksReset;}
bool GetSavedAutoTurretsEnabled(bool){return saved;}
void SetSavedAutoTurretsEnabled(bool on){saved=on;}
void SetSavedAutoTurretReserve(unsigned value){savedReserve=value;}
struct Behavior { unsigned reservePercent; };
Behavior BehaviorFor(void*){return {savedReserve};}
MemberState* Find(CEquip const* equip){for(auto& m:members)if(m.identity==equip)return &m;return nullptr;}
CEGun* ResolveGun(MemberState& m){return m.identity;}
void Arm(MemberState& m){++armed;m.identity->active=true;}
void Release(MemberState& m){++released;m.identity->active=m.manual;}
void ResetAttack(MemberState&){++attacksReset;}
void SavePreference(char const*,unsigned){++memberWrites;}
'''
functions=''.join(extract(source,sig) for sig in ['bool Owns(', 'bool GroupActivation(',
    'bool ManualActive(', 'void ActivationChanged(', 'void SetMode(', 'Mode GetMode()',
    'unsigned ReservePercent()', 'void SetReservePercent(', 'bool Selected(', 'void ToggleMember('])
fire=extract((repo/'src/freelancer/Client/cli_projectile_fx.cpp').read_text(),'bool CliShipFireAutomatic(')
checks=r'''
int main(){
    using namespace PlayerAutoTurrets;
    CEGun a,b,c;a.active=true;b.active=false;c.active=true;
    members={{&a,true,false},{&b,true,true},{&c,false,true}};
    CEqObj ship;ship.EquipManager.gun=&a;FClientEquippedObj host;host.Object=&ship;Vector aim;
    assert(CliShipFireAutomatic(&host,1,aim)&&fires==1);
    for(int i=0;i<20;++i){
        SetMode(Mode::Manual);assert(GetMode()==Mode::Manual);
        assert(Owns(&a)&&Owns(&b)&&!Owns(&c));
        assert(Selected(0)&&Selected(1)&&!Selected(2));
        assert(a.active&&!b.active&&c.active);
        assert(!members[0].manual&&members[1].manual&&members[2].manual);
        assert(!CliShipFireAutomatic(nullptr,1,aim)); // Gate precedes any live-object access.
        SetMode(Mode::Hostiles);assert(GetMode()==Mode::Hostiles);
        assert(a.active&&!b.active&&c.active&&armed==0&&released==0&&memberWrites==0);
    }
    SetMode(Mode::Manual);
    assert(GroupActivation(&a,true)&&members[0].manual&&a.active);
    ActivationChanged(&b,false);assert(!members[1].manual&&!b.active);
    ToggleMember(2);assert(Selected(2)&&armed==1&&memberWrites==1);
    SetMode(Mode::Hostiles);assert(Selected(2)&&armed==1&&released==0);
    assert(CliShipFireAutomatic(&host,1,aim)&&fires==2);
    SetReservePercent(90);assert(ReservePercent()==90&&!energyHold);
    SetReservePercent(0);assert(ReservePercent()==0);
    SetReservePercent(999);assert(ReservePercent()==90);
    puts("PASS: master preserves activation/manual states and per-gun choices; paused fire blocked; groups and reserve");
}
'''
(out/'check.cpp').write_text(stub+functions+'}\n'+fire+checks)
vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk=Path('C:/Program Files (x86)/Windows Kits/10');v='10.0.26100.0';env=dict(os.environ)
env['INCLUDE']=';'.join(map(str,[vc/'include']+[sdk/'Include'/v/x for x in ('ucrt','shared','um')]))
env['LIB']=';'.join(map(str,[vc/'lib/x86']+[sdk/'Lib'/v/x/'x86' for x in ('ucrt','um')]))
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc','/MT','check.cpp','/Fecheck.exe'],cwd=out,env=env,check=True)
subprocess.run([str(out/'check.exe')],cwd=out,check=True)
