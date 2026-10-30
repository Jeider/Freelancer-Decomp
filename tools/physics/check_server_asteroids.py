"""Compile production steering and observer lifecycle against controlled fixtures."""
import os
from pathlib import Path
import subprocess

from check_gravity import function

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'src/obj/server_asteroids_check'

STUB = r'''
#include <cassert>
#include <cmath>
#include <cstdio>
#include <vector>
#include <map>
#include "asteroid_avoidance_math.h"
#include "common_server_asteroid.h"
struct CEqObj {
    unsigned TypeBits=0x10;
    unsigned char FlagsA0=1;
    float CloakPercent=0;
    bool is_targetable() const;
};
struct CSimple {unsigned OwnerPlayer=0;};
struct GameObject {
    unsigned id=1,type=SERVER_ASTEROID_TYPE; CSimple simple;
    unsigned get_id(){return id;} unsigned get_type_bits(){return type;}
    CSimple* csimple(){return &simple;}
};
struct CSolarCreateInfo {unsigned Field_0xac=1;};
struct SystemTrackedObject {GameObject* Object=nullptr;bool bCreatedOnClient=false;};
struct SystemTrackedNode {SystemTrackedNode *Prev=this,*Next=this;SystemTrackedObject* Data=nullptr;};
struct Observer {
    unsigned PlayerId=1,bShipGone=0;
    struct List {SystemTrackedNode* Head=new SystemTrackedNode;unsigned Size=0;} Tracked;
    ~Observer(){auto* h=Tracked.Head;auto* n=h->Next;while(n!=h){auto* next=n->Next;delete n->Data;delete n;n=next;}delete h;}
};
bool single=false,visible=true;
bool SinglePlayer(){return single;}
bool SystemPlayerView_ShouldBeVisible(Observer*,GameObject*){return visible;}
struct FServerDestroyObjectInfo {unsigned ObjectId=0;unsigned char Field_0x04=0,Pad_0x05[3]={};};
struct Client {
    std::vector<unsigned> created,destroyed,kind;
    void SendServerCreateSolar(unsigned player,CSolarCreateInfo const&){created.push_back(player);}
    void SendServerDestroyObject(unsigned player,FServerDestroyObjectInfo const& m){destroyed.push_back(player);kind.push_back(m.Field_0x04);}
} client;
Client* g_pClientInterface=&client;
constexpr unsigned kSolarTypeBits=0xfdff;
SystemTrackedObject* SystemPlayerView_AddTrackedObject(Observer* v,GameObject* obj){
    auto* h=v->Tracked.Head;auto* n=new SystemTrackedNode;
    n->Data=new SystemTrackedObject{obj,single};n->Next=h;n->Prev=h->Prev;
    h->Prev->Next=n;h->Prev=n;++v->Tracked.Size;return n->Data;
}
SystemTrackedNode* SystemPlayerView_FindById(Observer* v,unsigned id){
    auto* h=v->Tracked.Head;for(auto* n=h->Next;n!=h;n=n->Next)if(n->Data->Object->id==id)return n;return nullptr;
}
'''

CHECK = r'''
int main(){
    CEqObj contact;
    assert(contact.is_targetable()); // ordinary satellite
    contact.FlagsA0=0;assert(!contact.is_targetable());
    contact.FlagsA0=1;contact.CloakPercent=1;assert(!contact.is_targetable());
    contact.CloakPercent=.5f;assert(contact.is_targetable());
    contact.TypeBits=SERVER_ASTEROID_TYPE;
    assert(!contact.is_targetable());
    contact.CloakPercent=0;assert(!contact.is_targetable());
    puts("PASS: server asteroids untargetable, ordinary solar flags and cloak preserved");

    using namespace AsteroidAvoidance;
    assert(std::fabs(Contact({100,0,0},{-100,0,0},20,3)-.8)<1e-9);
    assert(!std::isfinite(Contact({100,0,0},{100,0,0},20,3)));
    assert(!std::isfinite(Contact({100,50,0},{-100,0,0},20,3)));
    assert(!std::isfinite(Contact({5,0,0},{10,0,0},20,3))); // separating overlap
    assert(Contact({0,0,0},{0,0,0},20,3)==0);
    Vec p{0,0,0},v{0,0,-100},goal{0,0,-2000},right{1,0,0};
    Rock rock{{0,0,-100},{0,0,0},20};Result result;
    assert(Choose(p,v,goal,right,10,&rock,1,result));
    assert(std::fabs(result.direction.x)+std::fabs(result.direction.y)>.1);
    assert(!std::isfinite(Contact(Sub(rock.position,p),Sub(rock.velocity,Mul(result.direction,100*result.speedScale)),40,3)));
    rock.position={200,0,-100};assert(!Choose(p,v,goal,right,10,&rock,1,result));
    rock.position={0,0,100};assert(!Choose(p,v,goal,right,10,&rock,1,result));
    rock.position={0,0,-100};rock.velocity={0,0,-200};assert(!Choose(p,v,goal,right,10,&rock,1,result));
    rock.position={100,0,-100};rock.velocity={-100,0,0};assert(Choose(p,v,goal,right,10,&rock,1,result));
    rock.position={0,0,-500};rock.velocity={0,0,0};
    assert(!Choose(p,v,{0,0,-50},right,10,&rock,1,result)); // beyond arrival point
    // Straight route with two rocks, then a finite response when all routes are blocked.
    Rock obstacles[]={{{0,0,-180},{0,0,0},25},{{90,0,-200},{0,0,0},35}};
    assert(Choose(p,v,goal,right,12,obstacles,2,result));
    for(auto const& r:obstacles)
        assert(!std::isfinite(Contact(Sub(r.position,p),Sub(r.velocity,Mul(result.direction,100*result.speedScale)),r.radius+22,3)));
    Rock enclosing{{0,0,0},{0,0,0},1000};
    assert(Choose(p,v,goal,right,10,&enclosing,1,result)&&Finite(result.direction));
    // A ship follows the steering requests through an isolated obstacle.
    rock={{0,0,-180},{0,0,0},20};p={0,0,0};v={0,0,-100};
    double closest=10000;
    for(int tick=0;tick<600;++tick){
        bool avoiding=Choose(p,v,goal,right,10,&rock,1,result);
        Vec target=avoiding?Mul(result.direction,100*result.speedScale):Mul(Unit(Sub(goal,p),{0,0,-1}),100);
        v=Add(v,Mul(Sub(target,v),.2));p=Add(p,Mul(v,.05));
        double distance=std::sqrt(Dot(Sub(rock.position,p),Sub(rock.position,p)));
        if(distance<closest)closest=distance;
    }
    assert(closest>30 && p.z<-1000);
    puts("PASS: predictive steering, crossing/receding rocks, clearance, destination, finite fallback and route simulation");

    // Real production observer notifier/destructor; separate player views.
    GameObject asteroid;CSolarCreateInfo info;
    Observer a,b,far;a.PlayerId=1;b.PlayerId=2;far.PlayerId=3;
    SystemPlayerView_CreateSolarForPlayer(&a,&info,&asteroid);
    SystemPlayerView_CreateSolarForPlayer(&b,&info,&asteroid);
    visible=false;SystemPlayerView_CreateSolarForPlayer(&far,&info,&asteroid);
    assert(client.created.empty()); // MP creation belongs to the observer update
    assert(a.Tracked.Size==1&&b.Tracked.Size==1&&far.Tracked.Size==1);
    a.Tracked.Head->Next->Data->bCreatedOnClient=true;
    b.Tracked.Head->Next->Data->bCreatedOnClient=true;
    assert(SystemPlayerView_OnObjectDestroyed(&a,&asteroid,1));
    assert(SystemPlayerView_OnObjectDestroyed(&b,&asteroid,1));
    assert(SystemPlayerView_OnObjectDestroyed(&far,&asteroid,1));
    assert((client.destroyed==std::vector<unsigned>{1,2}));
    assert((client.kind==std::vector<unsigned>{1,1}));
    assert(!a.Tracked.Size&&!b.Tracked.Size&&!far.Tracked.Size);
    assert(!SystemPlayerView_FindById(&far,asteroid.id)); // cannot create a dead rock later
    single=true;visible=true;Observer sp;
    SystemPlayerView_CreateSolarForPlayer(&sp,&info,&asteroid);
    assert(client.created.size()==1&&sp.Tracked.Head->Next->Data->bCreatedOnClient);
    assert(SystemPlayerView_OnObjectDestroyed(&sp,&asteroid,1));
    // An ordinary solar retains the original immediate-create path.
    single=false;asteroid.type=0x10;Observer normal;
    auto count=client.created.size();SystemPlayerView_CreateSolarForPlayer(&normal,&info,&asteroid);
    assert(client.created.size()==count+1&&normal.Tracked.Size==0);
    puts("PASS: two-client destruction fan-out, unseen-client removal, SP creation, ordinary solar behavior");
}
'''

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    code = STUB + function('src/Common/common_ceqobj.cpp', 'bool CEqObj::is_targetable() const')
    code += function('src/Server/server_classes.cpp', 'void SystemPlayerView_CreateSolarForPlayer(')
    code += function('src/Server/server_classes.cpp', 'bool SystemPlayerView_OnObjectDestroyed(')
    (OUT/'check.cpp').write_text(code+CHECK)
    vc=Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk=Path('C:/Program Files (x86)/Windows Kits/10');version='10.0.26100.0'
    env=dict(os.environ)
    env['INCLUDE']=';'.join(str(p) for p in [vc/'include',ROOT/'src/Common',ROOT/'src/include']+
                            [sdk/'Include'/version/x for x in ('ucrt','shared','um')])
    env['LIB']=';'.join(str(p) for p in [vc/'lib/x86']+[sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'),'/nologo','/std:c++17','/W4','/WX','/EHsc',
                    '/MT','check.cpp','/Fecheck.exe'],cwd=OUT,env=env,check=True)
    subprocess.run([str(OUT/'check.exe')],cwd=OUT,check=True)

if __name__=='__main__':main()
