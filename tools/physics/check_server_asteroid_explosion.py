"""Run production client destroy/explosion/reap bodies against controlled effect sinks."""
import os
from pathlib import Path
import subprocess
from check_gravity import function

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'src/obj/server_asteroid_explosion_check'
STUB = r'''
#include <cassert>
#include <cstdio>
#include <vector>
#include "common_server_asteroid.h"
#define FDUMP(...) ((void)0)
struct Vector {float x=0,y=0,z=0;};
struct FMatrix {float v[9]={};};
struct Transform {FMatrix Rotation;Vector Translation;};
struct FTransform {FMatrix Rotation;struct {float X=0,Y=0,Z=0;} Translation;};
struct Body {bool collisions=true;void enable_collisions_r(bool on){collisions=on;}};
int deleted=0,unregistered=0,effects=0;
struct FClientGameobj {
    unsigned char Flags=0;unsigned type=SERVER_ASTEROID_TYPE;Body body;Body* Object=&body;
    FClientGameobj* ListNext=nullptr;Transform transform;int explosions=0;
    ~FClientGameobj(){++deleted;}
    void get_type(unsigned& out){out=type;}
    bool Slot158()const{return (Flags&1)!=0;}
    void Slot15c(bool);
    void Slot19c(int);
    void Slot1b0(Vector const*){++explosions;}
    Transform const& get_transform(){return transform;}
    Vector get_velocity(){return {};}
};
namespace Archetype {
struct FExplosionEffect {float Strength=0;struct {unsigned Id=1;bool IsEmpty()const{return Id==0;}} Fx;};
struct Explosion {std::vector<FExplosionEffect> Effects{{}};float InnardsDebrisNum=7,InnardsDebrisStartTime=0;unsigned Process=2;};
}
void* FindEffectArch(unsigned const*){return nullptr;}
void CliCreateEffectWorldOneShot(void*,FTransform const*,float const*,void*){++effects;}
struct Action_Explode {
    FClientGameobj* Gameobj;Archetype::Explosion* Arch;
    Vector Pos;float Elapsed=-1,PrevElapsed=-1,Lifetime=0;int debris=0,shatter=0;
    bool update(float);bool LifetimeEndedThisTick()const;bool DelayReachedThisTick(float)const;
    void SpawnInnardsDebris(){assert(!Gameobj->Slot158());++debris;}
    void Shatter(){++shatter;}
};
struct FGameobjList {FClientGameobj* First=nullptr;};
void ClientObjDb_Unregister(FClientGameobj*){++unregistered;}
'''
CHECK = r'''
int main(){
    // A received destruction starts the explosion and immediately drops collisions.
    for(float lifetime:{0.f,1.f}){
        auto* go=new FClientGameobj;
        go->Slot19c(1);assert(go->Flags==4&&!go->body.collisions&&go->explosions==1);
        Archetype::Explosion arch;Action_Explode action{go,&arch};action.Lifetime=lifetime;
        int initialEffects=effects;
        action.update(0); // Action_Explode::Create performs this call synchronously.
        assert(effects==initialEffects+1&&action.debris==1&&action.shatter==0);
        if(lifetime>0){
            assert(!go->Slot158());for(int i=0;i<4;++i)action.update(.25f);
        }
        assert(go->Slot158()&&!go->body.collisions&&effects==initialEffects+1);
        int before=deleted, removed=unregistered;FGameobjList list{go};ReapList(&list);
        assert(deleted==before+1&&unregistered==removed+1);
    }
    // process=none remains non-destructive for ordinary solars, old local rocks,
    // and non-death effects on a living server asteroid.
    for(unsigned type:{0x10u,0x40000000u,SERVER_ASTEROID_TYPE}){
        FClientGameobj go;go.type=type;
        if(type!=SERVER_ASTEROID_TYPE)go.Slot19c(1);
        Archetype::Explosion arch;Action_Explode action{&go,&arch};
        assert(!action.update(0));assert(!go.Slot158()&&go.body.collisions);
        assert(action.debris==1);
    }
    // Other explosion modes and silent streaming-out retain normal removal.
    for(unsigned process:{0u,1u}){
        FClientGameobj go;go.type=0x10;go.Slot19c(1);
        Archetype::Explosion arch;arch.Process=process;Action_Explode action{&go,&arch};
        action.update(0);assert(go.Slot158()&&action.shatter==(process==0?1:0));
    }
    FClientGameobj silent;silent.Slot19c(0);
    assert(silent.Slot158()&&!silent.body.collisions&&silent.explosions==0);
    puts("PASS: process=none server asteroid death, immediate collision shutdown, effects/debris before removal, zero/delayed lifetime, client reaping, legacy behavior");
}
'''


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    code = STUB
    for signature in ['void FClientGameobj::Slot15c(', 'void FClientGameobj::Slot19c(']:
        code += function('src/freelancer/Client/client_gameobj.cpp', signature)
    for signature in ['bool Action_Explode::LifetimeEndedThisTick(', 'bool Action_Explode::DelayReachedThisTick(', 'bool Action_Explode::update(']:
        code += function('src/freelancer/Client/client_explosion.cpp', signature)
    code += function('src/freelancer/Client/client_objdb.cpp', 'void ReapList(')
    (OUT/'check.cpp').write_text(code+CHECK)
    vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
    sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
    env = dict(os.environ)
    env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include', ROOT/'src/include'] +
                              [sdk/'Include'/version/x for x in ('ucrt', 'shared', 'um')])
    env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt', 'um')])
    subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                    '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
    subprocess.run([str(OUT/'check.exe')], cwd=OUT, check=True)


if __name__ == '__main__':
    main()
