"""Run the production missile collection with mocked live objects/database."""
import os
from pathlib import Path
import subprocess

repo = Path(__file__).resolve().parents[2]
out = repo / 'src/obj/radar_missiles_check'
out.mkdir(parents=True, exist_ok=True)
source = (repo / 'src/freelancer/Client/hud_radar.cpp').read_text()

def extract(signature):
    start = source.index(signature)
    end = source.index('{', start) + 1
    depth = 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]

stub = r'''
#include <cassert>
#include <cstdio>
#include <limits>
#include <vector>
#include "../../freelancer/Client/radar_symbols.h"
struct Vector {float x=0,y=0,z=0;};
struct Transform {Vector Translation;struct {float E[3][3]={{1,0,0},{0,1,0},{0,0,1}};} Rotation;};
struct CObject {enum {ClassGuided=0xa7};unsigned ObjectClass=ClassGuided;};
struct CGuided:CObject {unsigned owner=2;bool alive=true;
    bool is_alive()const{return alive;}unsigned get_owner()const{return owner;}};
struct IObjRW {CGuided* object=nullptr;unsigned id=0;int attitude=0,targetResult=0;
    IObjRW* target=nullptr;bool dying=false,targetable=true;float interference=0;Transform transform;
    CObject const* cobject(){return object;}bool is_dying(){return dying;}
    bool is_targetable(){return targetable;}float get_scanner_interference(){return interference;}
    Transform const& get_transform(){return transform;}
    Vector const& get_position(){return transform.Translation;}
    unsigned get_id(){return id;}int get_target(IObjRW*& result){result=target;return targetResult;}};
struct IObjDB {std::vector<IObjRW*> objects,owners;size_t cursor=0;int visits=0;
    IObjRW* GetNext(void* raw){
        struct Iter{void* cursor;void* head;unsigned mask;};auto* iter=static_cast<Iter*>(raw);
        assert(iter->mask==RadarSymbols::MissileMask);
        if(!iter->head){cursor=0;iter->head=this;}++visits;
        return cursor<objects.size()?objects[cursor++]:nullptr;}
    IObjRW* FindById(unsigned const* id){for(auto* o:owners)if(o->id==*id)return o;return nullptr;}};
struct CEScanner {struct Arch {float RadarRange=1000;} arch;
    Arch const* ScannerArch()const{return &arch;}};
int GetAttitudeClass(IObjRW*,IObjRW* owner){return owner?owner->attitude:0;}
'''
checks = r'''
int main(){
    RadarProjection::Layout layout;
    assert(RadarProjection::MakeLayout({0,0,1919,1079},.5f,.845f,.3f,.32f,.94f,layout));
    IObjRW player,enemy,ally,missile;player.id=1;enemy.id=2;enemy.attitude=-1;ally.id=3;ally.attitude=1;
    CGuided projectile;missile.object=&projectile;missile.id=10;missile.transform.Translation={100,0,0};
    IObjDB db;db.objects={&missile};db.owners={&player,&enemy,&ally};CEScanner scanner;Blip b;
    auto sample=[&](float phase=0.f,float range=1000.f){
        return MissileBlip(&missile,&db,&scanner,&player,nullptr,range,layout,phase,b);};
    assert(sample() && b.color==0xff4438u && !b.incoming);
    projectile.owner=3;assert(sample() && b.color==0x55f293u);
    projectile.owner=1;assert(sample() && b.color==0x55f293u);
    projectile.owner=999;assert(sample() && b.color==0xc1d8deu); // Owner gone/unknown.
    missile.target=&player;assert(sample() && b.incoming && b.color==0xff4438u);
    assert(sample(.3f) && b.color==0xffe35bu); // Warning survives missing owner.
    missile.target=&ally;assert(sample(.3f) && !b.incoming && b.color==0xc1d8deu);
    missile.target=&player;missile.targetResult=-3;assert(sample(.3f) && !b.incoming);
    missile.targetResult=0;missile.target=nullptr;
    assert(!sample(0,50)); // Zoom restricts displayed range.
    missile.interference=.95f;assert(!sample());
    missile.interference=1;assert(!sample());
    missile.interference=std::numeric_limits<float>::quiet_NaN();assert(!sample());
    missile.interference=0;assert(sample());
    missile.dying=true;assert(!sample());missile.dying=false;
    projectile.alive=false;assert(!sample());projectile.alive=true;
    missile.targetable=false;assert(!sample());missile.targetable=true;
    projectile.ObjectClass=0x27;assert(!sample());projectile.ObjectClass=CObject::ClassGuided;
    missile.object=nullptr;assert(!sample());missile.object=&projectile;
    missile.transform.Translation.x=std::numeric_limits<float>::infinity();assert(!sample());
    missile.transform.Translation={0,-100,0};assert(sample() && b.point.below);
    assert(MissileBlip(&missile,&db,&scanner,&player,&missile,1000,layout,0,b) && b.selected);
    // More missiles than native scanner slots; late incoming threats must still win.
    std::vector<IObjRW> contacts(600);db.objects.clear();
    for(unsigned i=0;i<contacts.size();++i){
        auto& m=contacts[i];m=missile;m.id=100+i;m.transform.Translation={float(600-i),0,0};
        db.objects.push_back(&m);
    }
    contacts[598].target=&player;contacts[598].transform.Translation.x=800;
    contacts[599].target=&player;contacts[599].transform.Translation.x=900;
    Blip output[258]={};output[0].color=123;output[257].color=456;
    assert(CollectMissiles(&db,&scanner,&player,&contacts[300],1000,layout,.3f,output+1,256)==256);
    assert(output[0].color==123 && output[257].color==456);
    std::sort(output+1,output+257,BlipBefore);
    assert(output[1].incoming && output[1].point.distanceSquared==800*800);
    assert(output[2].incoming && output[3].selected);
    assert(output[4].point.distanceSquared==9); // Nearest remaining missile (x=3).
    int const visits=db.visits;
    assert(!CollectMissiles(&db,&scanner,&player,nullptr,0,layout,0,output,256));
    assert(!CollectMissiles(nullptr,&scanner,&player,nullptr,1000,layout,0,output,256));
    assert(!CollectMissiles(&db,nullptr,&player,nullptr,1000,layout,0,output,256));
    assert(!CollectMissiles(&db,&scanner,&player,nullptr,1000,layout,0,output,0));
    assert(db.visits==visits);
    assert(CollectMissiles(&db,&scanner,&player,nullptr,1000,layout,0,output,1)==1 && output[0].incoming);
    db.objects.clear();assert(!CollectMissiles(&db,&scanner,&player,nullptr,1000,layout,0,output,256));
    puts("PASS: live missile ownership/retargeting, death, scanner/zoom, projection, 600 contacts, threat priority and bounded storage");
}
'''
code = stub + extract('struct Blip') + ';\n'
code += '\n'.join(extract(s) for s in ('bool BlipBefore(', 'bool MissileBlip(', 'int CollectMissiles('))
(out / 'check.cpp').write_text(code + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10'); version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(str(p) for p in [vc/'include'] + [sdk/'Include'/version/x for x in ('ucrt','shared','um')])
env['LIB'] = ';'.join(str(p) for p in [vc/'lib/x86'] + [sdk/'Lib'/version/x/'x86' for x in ('ucrt','um')])
subprocess.run([str(vc/'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX', '/EHsc', '/MT',
                'check.cpp', '/Fecheck.exe'], cwd=out, env=env, check=True)
subprocess.run([str(out/'check.exe')], cwd=out, check=True)
