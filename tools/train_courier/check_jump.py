"""Exercise the production resume operation through SP jump lifecycle races."""
from pathlib import Path
import subprocess
from check_orders import function,compiler_env

ROOT=Path(__file__).resolve().parents[2]
PREFIX=r'''
#include <cassert>
#include <cstdio>
struct Vector{};struct Matrix{};
struct CShip {unsigned Id=7,PhysicsSystemId=2,OwnerPlayer=0;void* BodyPtr=this;bool launching=false,jumping=false,member=true;Vector WorldPosition;Matrix Orientation;bool is_launching(){return launching;}bool is_jumping(){return jumping;}void SetOwnerPlayer(unsigned id){OwnerPlayer=id;}void set_hit_pts(float){}};
struct Courier {unsigned trailer=7,transitSystem=2,transitOwner=0;float transitHitpoints=100;bool inTransit=true;};
CShip cargo;CShip* coupled=nullptr;unsigned moves=0,joins=0,tailSystem=0;bool present=true,failJoin=false,failMove=false;
CShip* ship(unsigned id){return present && id==cargo.Id?&cargo:nullptr;}
namespace CmnTrain {
bool IsMember(CShip* s){return s->member;}
CShip* Trailer(CShip*){return coupled;}
bool RestoreCoupling(CShip*,CShip* t){++joins;if(failJoin)return false;coupled=t;return true;}
}
namespace pub {namespace SpaceObj {
int GetSystem(unsigned,unsigned& s){s=tailSystem;return s?0:-2;}
int Relocate(unsigned,unsigned s,Vector const&,Matrix const&){
    ++moves;if(failMove)return -2;tailSystem=s;cargo.PhysicsSystemId=s;cargo.BodyPtr=s?&cargo:nullptr;cargo.member=s!=0;return 0;
}
}}
'''
MAIN=r'''
int main(){
    Courier state;CShip loco;loco.Id=1;loco.launching=true;
    assert(resumeCourierCargo(state,&loco,2)==-1 && moves==0);
    loco.launching=false;loco.jumping=true;assert(resumeCourierCargo(state,&loco,2)==-1 && moves==0);
    loco.jumping=false;loco.BodyPtr=nullptr;assert(resumeCourierCargo(state,&loco,2)==-1 && moves==0);
    loco.BodyPtr=&loco;loco.PhysicsSystemId=1;assert(resumeCourierCargo(state,&loco,2)==-1 && moves==0);
    loco.PhysicsSystemId=2;
    loco.member=true;state.transitSystem=3;assert(resumeCourierCargo(state,&loco,2)==-2 && moves==0);state.transitSystem=2;
    failMove=true;assert(resumeCourierCargo(state,&loco,2)==-4 && state.inTransit);failMove=false;
    failJoin=true;assert(resumeCourierCargo(state,&loco,2)==-5 && state.inTransit && tailSystem==2);
    unsigned relocated=moves;failJoin=false;assert(resumeCourierCargo(state,&loco,2)==1 && !state.inTransit && moves==relocated);
    unsigned joined=joins;assert(resumeCourierCargo(state,&loco,2)==1 && moves==relocated && joins==joined);
    state.inTransit=true;assert(resumeCourierCargo(state,&loco,2)==1 && !state.inTransit && moves==relocated);
    state.inTransit=true;coupled=nullptr;cargo.BodyPtr=nullptr;cargo.member=false;
    assert(resumeCourierCargo(state,&loco,2)==1 && moves==relocated+2 && coupled==&cargo);
    state.inTransit=true;coupled=nullptr;present=false;assert(resumeCourierCargo(state,&loco,2)==-3 && state.inTransit);
    puts("PASS: no relocation during jump-in or missing/wrong-system physics; retry failed relocation/coupling; idempotent completion; rebuild premature physics; no new cargo spawned");
}
'''
def main():
    source=(ROOT/'src/Server/server_train_yard.cpp').read_text()
    out=ROOT/'src/obj/train_courier/jump';out.mkdir(parents=True,exist_ok=True)
    cpp=out/'jump.cpp';cpp.write_text(PREFIX+function(source,'int resumeCourierCargo(')+MAIN)
    compiler,env=compiler_env();exe=out/'jump.exe'
    subprocess.run([str(compiler/'cl.exe'),'/nologo','/std:c++17','/EHsc','/O2',str(cpp),'/Fo'+str(out/'jump.obj'),'/Fe'+str(exe)],cwd=out,env=env,check=True)
    subprocess.run([str(exe)],cwd=out,check=True)

if __name__=='__main__':main()
