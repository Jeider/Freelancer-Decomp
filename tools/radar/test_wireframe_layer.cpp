#include "dacom.h"
#include "render/mesh_iface.h"
#include <cassert>
#include <cstdint>
#include <cstdio>
#include <fstream>
#include <map>
#include <vector>
#include <string>
#include <cstring>

struct Transform {struct {float E[3][3]={{1,0,0},{0,1,0},{0,0,1}};} Rotation;struct {float x=0,y=0,z=0;} Translation;};
struct SolarArch {bool flag=true;bool GetRadarWireframe()const{return flag;}};
struct CObject {enum{ClassSolar=0x303};unsigned ObjectClass=ClassSolar;};
struct CSolar:CObject {SolarArch arch;SolarArch const* solararch()const{return &arch;}};
struct IObjRW {
    CSolar object;long index=1;bool dying=false;
    CObject const* cobject()const{return &object;}
    bool is_dying()const{return dying;}long get_index()const{return index;}
};
struct IObjDB {
    std::vector<IObjRW> contacts;
    IObjRW* GetNext(void* raw){
        struct Iter{void* cursor;void* head;unsigned mask;};auto* it=static_cast<Iter*>(raw);
        assert(it->mask==0xfdffu);auto i=reinterpret_cast<uintptr_t>(it->cursor);
        if(i==contacts.size())return nullptr;it->cursor=reinterpret_cast<void*>(i+1);return &contacts[i];
    }
};
static void* const G_InvalidEngineHandle=reinterpret_cast<void*>(intptr_t(-1));
struct Wire:IVMeshWire {
    std::vector<unsigned char> mesh,wire;unsigned long refs=1;
    GENRESULT DACOM_API QueryInterface(char const*,void** out)override{*out=this;AddRef();return 0;}
    unsigned long DACOM_API AddRef()override{return ++refs;}
    unsigned long DACOM_API Release()override{return --refs;}
    void* DACOM_API GetWireData()override{return wire.data();}
    int DACOM_API Draw()override{return 0;}
    void* DACOM_API GetMeshData()override{return mesh.data();}
};
struct EngineStub {
    Wire* wire=nullptr;bool available=true;
    float root[12]={1,0,0,0,1,0,0,0,1,0,0,0};
    float child[12]={1,0,0,0,1,0,0,0,1,0,0,0};
    int QueryInstance(void*,char const*,void** out){if(!available)return -1;*out=wire;wire->AddRef();return 0;}
    float* GetInstanceTransform(void* instance){return instance==reinterpret_cast<void*>(2)?child:root;}
    void* GetRelatedInstance(void* rootId,unsigned,void* cursor){
        return rootId==reinterpret_cast<void*>(1)&&cursor==G_InvalidEngineHandle?reinterpret_cast<void*>(2):G_InvalidEngineHandle;
    }
};
namespace DALib {EngineStub* Engine=nullptr;}
#define FDUMP(...) ((void)0)
#include "../../src/freelancer/Client/radar_wireframe.h"

int main(){
    std::ifstream list("fixtures.txt");std::string path;std::getline(list,path);assert(!path.empty());
    std::ifstream file(path,std::ios::binary);assert(file);
    unsigned sizes[2];file.read(reinterpret_cast<char*>(sizes),8);
    Wire wire;wire.mesh.resize(sizes[0]);wire.wire.resize(sizes[1]);
    file.read(reinterpret_cast<char*>(wire.mesh.data()),sizes[0]);file.read(reinterpret_cast<char*>(wire.wire.data()),sizes[1]);
    EngineStub engine;engine.wire=&wire;DALib::Engine=&engine;
    RadarWireframe::Layer layer;IObjDB db;db.contacts.resize(1);
    RadarProjection::Layout layout={500,400,200,.32f,.94f,100,700};Transform player;
    unsigned count=0;
    auto draw=[&](float,float,float,float,unsigned,float){++count;};
    layer.Draw(&db,player,1,20000,layout,1,draw);
    assert(count>0&&layer.cache.size()==1&&wire.refs==2);
    unsigned full=count;
    engine.child[9]=10000000;count=0;
    layer.Draw(&db,player,1,20000,layout,1,draw);
    assert(count*2==full); // Live child transform, not cached world coordinates.
    engine.child[9]=0;db.contacts.resize(300);count=0;
    layer.Draw(&db,player,1,20000,layout,1,draw);
    assert(count==300*full&&layer.cache.size()==1); // No 256/max_contacts cap.
    for(auto& contact:db.contacts)contact.object.arch.flag=false;
    count=0;layer.Draw(&db,player,1,20000,layout,1,draw);
    assert(count==0&&layer.cache.empty()&&wire.refs==1);
    db.contacts.resize(1);db.contacts[0].object.arch.flag=true;engine.available=false;
    count=0;layer.Draw(&db,player,1,20000,layout,1,draw);assert(count==0); // No wire: no mesh fallback.
    engine.available=true;layer.Draw(&db,player,1,20000,layout,1,draw);assert(!layer.cache.empty());
    db.contacts.clear();layer.Draw(&db,player,2,20000,layout,1,draw);
    assert(layer.cache.empty()&&wire.refs==1&&layer.system==2);
    puts("PASS: production layer draws 300 flagged solars without contact limits; opt-out, live child transforms, shared geometry cache, no fallback, system cleanup");
}
