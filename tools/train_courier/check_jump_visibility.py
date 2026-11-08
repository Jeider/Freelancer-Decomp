"""Run the real SP destroy/create handlers with courier suspend/resume.

The physics harness alone cannot see this failure: DESTROYOBJECT changes the
shared CShip's owner, so the server later suppresses its CREATESHIP packet.
Only transport, physics and the client wrapper's disposal are stubbed here.
"""
from pathlib import Path
import subprocess
from check_orders import function, compiler_env

ROOT = Path(__file__).resolve().parents[2]
PREFIX = r'''
#include <cassert>
#include <cstdio>
#include <cstring>
#include <cmath>
#define FDUMP(...) ((void)0)
struct Vector{};struct Matrix{};
struct CSimple {
    unsigned OwnerPlayer=0;void* ObjectDb=nullptr;
    float hitpoints=10431;
    float get_hit_pts(){return hitpoints;}
    void set_hit_pts(float value){hitpoints=value;}
    void SetOwnerPlayer(unsigned p){OwnerPlayer=p;}
    void connect(void* db){ObjectDb=db;}
};
struct CShip:CSimple {
    unsigned Id=55,PhysicsSystemId=1;void* BodyPtr=this;
    bool jumping=false;Vector WorldPosition;Matrix Orientation;
    bool is_launching(){return false;}bool is_jumping(){return jumping;}
    unsigned pods=20,goods=1000;
};
CShip cargo,loco;
bool clientVisible=true,removePending=false;
unsigned creates=0,tracked=0;
int clientDb,serverDb;
struct FClientGameobj {
    CShip* Object=&cargo;
    void SetOwnerPlayer(unsigned p){Object->SetOwnerPlayer(p);}
    virtual void Slot19c(int type){assert(type==0);removePending=true;}
};
struct FClientSimpleGameobj:FClientGameobj {void Slot19c(int type) override;} clientCargo;
struct FServerDestroyObjectInfo {unsigned ObjectId,Field_0x04;};
struct CShipCreateInfo {int VibeOtherGroupId=0;};
struct Observer {unsigned PlayerId=1;unsigned char bShipGone=0;};
struct GameObject {
    CSimple* csimple(){return &cargo;}
    bool is_destroyed(){return false;}
    unsigned get_id(){return cargo.Id;}
} serverCargo;
struct Player {int rep_vibe=42;} Players[2];
bool SinglePlayer(){return true;}
bool IsPlayerShipId(unsigned id){return id==loco.Id;}
unsigned GetPlayerConnectionId(){return 1;}
void* GetClientObjDb(){return &clientDb;}
CShip* NarrowGameobj(FClientGameobj* go,int){return go->Object;}
CShip* NarrowObject(FClientGameobj* go,int){return go->Object;}
FClientGameobj* ClientObjDb_FindObject(unsigned id,int){return clientVisible&&id==cargo.Id?&clientCargo:nullptr;}
void ReqPlayerHullStatusRetail(float){assert(false);}
void SpaceAppArmDeathCamera(){assert(false);}
void ClientObjDb_Unregister(FClientGameobj*){assert(false);}
void SystemPlayerView_AddTrackedObject(Observer*,GameObject*){++tracked;}
struct IClientImpl {
    void SendServerDestroyObject(unsigned,const FServerDestroyObjectInfo&);
    void SendServerCreateShip(unsigned player,CShipCreateInfo&){
        assert(player==1 && cargo.OwnerPlayer==0);
        ++creates;clientVisible=true;removePending=false;
    }
} client;
IClientImpl* g_pClientInterface=&client;
'''
WORLD = r'''
struct Courier {
    unsigned trailer=55,transitSystem=0,transitOwner=0;
    float transitHitpoints=0;
    bool inTransit=false;int transitStatus=0;
};
CShip* coupled=&cargo;
CShip* ship(unsigned id){return id==cargo.Id?&cargo:nullptr;}
namespace CmnTrain {
CShip* Trailer(CShip*){return coupled;}
bool Uncouple(CShip*){coupled=nullptr;return true;}
bool RestoreCoupling(CShip*,CShip* tail){coupled=tail;return true;}
}
unsigned cargoSystem=1;
namespace pub {namespace SpaceObj {
int GetSystem(unsigned,unsigned& out){out=cargoSystem;return 0;}
int Relocate(unsigned id,unsigned system,Vector const&,Matrix const&){
    assert(id==cargo.Id);
    if(!system){
        // remove_ship sends the real SP DESTROYOBJECT handler. The client
        // removes its wrapper before the arrival heartbeat, as in the report.
        client.SendServerDestroyObject(1,{id,0});
        assert(removePending && cargo.OwnerPlayer==1);
        clientVisible=false;removePending=false;cargo.ObjectDb=nullptr;
    }else{
        // GameObject::enter_system skips connect for an SP player-owned object.
        if(!cargo.OwnerPlayer)cargo.connect(&serverDb);
        Observer view;CShipCreateInfo info;
        SystemPlayerView_CreateShipForPlayer(&view,&info,&serverCargo);
    }
    cargoSystem=system;cargo.PhysicsSystemId=system;
    cargo.BodyPtr=system?&cargo:nullptr;return 0;
}
}}
'''
MAIN = r'''
int main(){
    loco.Id=28;loco.OwnerPlayer=1;loco.PhysicsSystemId=2;
    // Reproduce exactly the observed invisible-but-physically-attached state.
    pub::SpaceObj::Relocate(55,0,{},{});
    pub::SpaceObj::Relocate(55,2,{},{});
    assert(!clientVisible && cargo.OwnerPlayer==1 && !cargo.ObjectDb);
    assert(cargo.hitpoints==0); // The real virtual Slot19c, missed by the old stub.
    assert(creates==0 && tracked==0 && CmnTrain::Trailer(&loco)==&cargo);
    // Fresh job, then repeated real lifecycle transfers through both systems.
    cargo.OwnerPlayer=0;cargo.ObjectDb=&serverDb;clientVisible=true;cargoSystem=1;cargo.hitpoints=10431;
    Courier state;
    for(unsigned jump=0;jump<4;++jump){
        unsigned destination=jump%2?1:2;
        const float expectedHull=10431.f-jump*.25f;cargo.hitpoints=expectedHull;
        assert(suspendCourierCargo(state,&loco,destination));
        assert(state.inTransit && state.transitOwner==0 && cargo.OwnerPlayer==1);
        assert(cargo.hitpoints==0 && state.transitHitpoints==expectedHull);
        assert(!clientVisible && !CmnTrain::Trailer(&loco));
        loco.PhysicsSystemId=destination;loco.jumping=true;
        assert(resumeCourierCargo(state,&loco,destination)==-1 && !clientVisible);
        loco.jumping=false;
        assert(resumeCourierCargo(state,&loco,destination)==1);
        assert(!state.inTransit && cargo.OwnerPlayer==0 && cargo.ObjectDb==&serverDb);
        assert(clientVisible && creates==jump+1 && tracked==jump+1);
        assert(CmnTrain::Trailer(&loco)==&cargo && state.trailer==55);
        assert(cargo.hitpoints==expectedHull && cargo.pods==20 && cargo.goods==1000);
        assert(resumeCourierCargo(state,&loco,destination)==1 && creates==jump+1);
    }
    cargo.hitpoints=0;assert(!suspendCourierCargo(state,&loco,2) && !state.inTransit);
    puts("PASS: real DESTROYOBJECT, virtual Slot19c and CREATESHIP reproduce zero HP and invisible cargo; four jumps preserve exact damaged hull and restore client visibility; dead cargo cannot be revived");
}
'''

def main():
    server = (ROOT/'src/Server/server_train_yard.cpp').read_text()
    observer = (ROOT/'src/Server/server_classes.cpp').read_text()
    client = (ROOT/'src/freelancer/Client/client_iclient_space.cpp').read_text()
    gameobj = (ROOT/'src/freelancer/Client/client_gameobj.cpp').read_text()
    code = PREFIX + function(gameobj, 'void FClientSimpleGameobj::Slot19c(')
    code += function(client, 'void IClientImpl::SendServerDestroyObject(')
    code += function(observer, 'void SystemPlayerView_CreateShipForPlayer(') + WORLD
    code += function(server, 'bool suspendCourierCargo(')
    code += function(server, 'int resumeCourierCargo(') + MAIN
    out = ROOT/'src/obj/train_courier/jump_visibility'
    out.mkdir(parents=True, exist_ok=True)
    cpp = out/'visibility.cpp';cpp.write_text(code)
    compiler, env = compiler_env();exe = out/'visibility.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',
        str(cpp),'/Fo'+str(out/'visibility.obj'),'/Fe'+str(exe)],cwd=out,env=env,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)

if __name__ == '__main__':
    main()
