// Actual client replica and persistent placement updater, controlled engine I/O.
#include <algorithm>
#include <cassert>
#include <chrono>
#include <cstdio>
#include <map>
#include <set>
#include <unordered_set>
#include <unordered_map>
#include <vector>
#include "procedural_asteroid_client.h"
#include "procedural_asteroid_replica.h"
using DWORD=unsigned long;
struct Vector {float x=0,y=0,z=0;};
struct Quaternion {float w=1,x=0,y=0,z=0;};using FQuaternion=Quaternion;
struct FMatrix {Quaternion q;};
struct IObjInspect {};
struct FSpaceCamera {};
struct FClientGameobj:IObjInspect {unsigned id=0,drawResult=0xffff0004u;Vector pos;FMatrix matrix;
 unsigned* Slot188(unsigned* out,FSpaceCamera*,unsigned,void*,void*){*out=drawResult;return out;}
 unsigned get_id()const{return id;}bool Slot154()const{return false;}
 Vector const& get_position()const{return pos;}FMatrix const& get_orientation()const{return matrix;}};
struct MathEngine {void MatrixToQuaternion(Quaternion& q,FMatrix const& m){q=m.q;}} math;
MathEngine* Acquire3DMathEngine(){return &math;}
float frameDt=1.f/60;double GetClientFrameTimeRaw(){return frameDt;}
unsigned CreateID(char const* s){return !strcmp(s,"om15")?15:25;}
DWORD GetTickCount(){return 2000;}
unsigned GetPlayerConnectionId(){return 1;}
struct CHAT_ID {unsigned id;explicit CHAT_ID(unsigned n):id(n){}};
struct IChatServer {void SubmitChat(CHAT_ID,unsigned,void*,CHAT_ID,int){}};
IChatServer* G_ChatServer=nullptr;
FClientGameobj* ClientObjDb_FindObject(unsigned,int){return nullptr;}
bool FarRocksProceduralAvailable(){return true;}
#include "client_production.inl"
struct FZItemGameObject {IObjInspect* Object;unsigned LodWord=0;void Draw(FSpaceCamera*);};
#include "native_submit.inl"
using Buffer=std::vector<unsigned char>;
struct FMeshInstance {float CentreRadius[4]={},Rotation[4]={};unsigned Colour=0;};
struct Mesh {float SourceRadius=40;std::vector<FMeshInstance> Instances;std::vector<unsigned> RockIndices;
 size_t PlacementCapacity=0;Buffer* Placement=nullptr;};
struct FFarField {unsigned ZoneId=0,LocalRevision=0,RockCount=0;int LocalCell[3]={},TexCount=3;
 unsigned LocalMeshRevision=0,LocalCellRevision=0;
 bool bLocalCellValid=false,bFailed=false;double Anchor[3]={};float MaxRockRadius=40;
 struct LocalSlot {int model;size_t index;float position[3];};
 std::unordered_map<ProceduralAsteroids::Key,LocalSlot> LocalSlots;Mesh Meshes[4];
 struct Class {unsigned count;float radius;};std::vector<Class> Classes;};
int zoneChecks=0,fullBuilds=0;bool exclusion=false;
struct ZoneStub {unsigned GetId()const{return 25;}float GetImmersion(Vector const&){++zoneChecks;return 1;}} zoneStub;
struct FCliAsteroid {ZoneStub* Zone=&zoneStub;};
void ZoneRadii(ZoneStub*,float* p){p[0]=p[1]=p[2]=50000;}
void ZoneAxis(ZoneStub*,int k,double* p){for(int i=0;i<3;++i)p[i]=i==k?1:0;}
double Clamp01(double v){return std::clamp(v,0.,1.);}
bool CliAsteroidExcludesLocalMesh(FCliAsteroid const*,Vector const&,float){return exclusion;}
struct RuntimeHitchScope {RuntimeHitchScope(char const*,char const* s){if(!strcmp(s,"procedural asteroid cell build"))++fullBuilds;}};
constexpr int GR_OK=0;
struct Pipeline {int creates=0,updates=0;size_t bytes=0;
 int CreateExVertexBuffer(unsigned n,void const* p,Buffer** b){++creates;*b=new Buffer(n);memcpy((*b)->data(),p,n);return 0;}
 int UpdateExVertexBuffer(Buffer* b,unsigned offset,unsigned n,void const* p){++updates;bytes+=n;assert(offset+n<=b->size());memcpy(b->data()+offset,p,n);return 0;}
 void DestroyExVertexBuffer(Buffer* b){delete b;}} pipeline;
namespace RenderEx {Pipeline* GetPipelineEx(){return &pipeline;}}
#include "procedural_asteroid_mesh.inl"
int main(){
 namespace P=ProceduralAsteroids;
 ProceduralAsteroidClientEnter(15);State.token=1;
 P::Packet packet;auto& h=packet.header;h.kind=P::Begin;h.system=15;h.zone=25;h.seed=802;h.models=3;h.epoch=1;h.token=1;
 auto send=[&](){assert(ProceduralAsteroidClientReceive(P::Channel,P::Bytes(packet),&packet));};
 send();h.kind=P::End;send();assert(State.ready);
 FCliAsteroid field;FFarField cache;double eye[3]={0,0,0};
 assert(UpdateLocalMeshes(&field,cache,eye));assert(cache.RockCount>7500&&pipeline.creates==3&&fullBuilds==1);
 auto resident=cache.RockCount;int z=zoneChecks,uploads=pipeline.updates;
 auto start=std::chrono::steady_clock::now();
 for(int i=0;i<600;++i){ProceduralAsteroidClientTick(15);assert(UpdateLocalMeshes(&field,cache,eye));}
 double idle=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/600;
 assert(fullBuilds==1&&zoneChecks==z&&pipeline.updates==uploads&&pipeline.creates==3);
 std::vector<FClientGameobj> bodies(700);unsigned i=0;
 h.kind=P::Delta;h.count=1;
 for(auto const& item:cache.LocalSlots){if(i==bodies.size())break;
  auto rock=P::Generate(item.first,h.seed,3);auto& b=bodies[i];b.id=++i;
  memcpy(&b.pos.x,rock.position,12);b.matrix.q={rock.rotation[3],rock.rotation[0],rock.rotation[1],rock.rotation[2]};
  ProceduralAsteroidClientObserve(&b);auto& e=packet.entries[0];e=P::Entry{};e.key=rock.key;e.object=b.id;e.flags=P::Active;
  memcpy(e.position,rock.position,12);memcpy(e.rotation,rock.rotation,16);++h.revision;h.clock=float(Clock);send();
 }
 ProceduralAsteroidClientTick(15);assert(UpdateLocalMeshes(&field,cache,eye));
 z=zoneChecks;uploads=pipeline.updates;start=std::chrono::steady_clock::now();
 for(int frame=0;frame<300;++frame){
  for(auto& b:bodies){auto& q=b.matrix.q;float r[4]={q.x,q.y,q.z,q.w};P::Spin(r,frameDt);q={r[3],r[0],r[1],r[2]};}
  ProceduralAsteroidClientTick(15);assert(UpdateLocalMeshes(&field,cache,eye));
 }
 double moving=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-start).count()/300;
 assert(fullBuilds==1&&zoneChecks==z&&pipeline.creates==3&&pipeline.updates-uploads==900);
 // A real pushed body moves the same visual slot, and updates spatial index once.
 auto& body=bodies[0];auto key=Objects.at(body.id);auto slot=cache.LocalSlots.at(key);
 assert(ProceduralAsteroidClientSpatialUpdate(&body,body.pos,40));
 assert(!ProceduralAsteroidClientSpatialUpdate(&body,body.pos,40));body.pos.x+=100;
 assert(ProceduralAsteroidClientSpatialUpdate(&body,body.pos,40));
 ProceduralAsteroidClientTick(15);assert(UpdateLocalMeshes(&field,cache,eye));
 auto& instance=cache.Meshes[slot.model].Instances[slot.index];assert(instance.CentreRadius[0]==body.pos.x);
 // Actual native queue callback takes over only after a successful mesh submit.
 assert(ProceduralAsteroidClientPhysical(&body)&&!ProceduralAsteroidClientOwns(&body));
 auto frame=[&](bool native){
  ProceduralAsteroidClientBeginVisuals();
  if(native)for(auto& b:bodies){FZItemGameObject node{&b};node.Draw(nullptr);}
  ProceduralAsteroidClientTick(15);assert(UpdateLocalMeshes(&field,cache,eye));
 };
 frame(true);assert(instance.CentreRadius[3]==0&&ProceduralAsteroidClientNativeVisual(key));
 auto generation=cache.LocalMeshRevision;uploads=pipeline.updates;z=zoneChecks;
 for(int f=0;f<120;++f){
  for(auto& b:bodies){auto& q=b.matrix.q;float rot[4]={q.x,q.y,q.z,q.w};P::Spin(rot,frameDt);q={rot[3],rot[0],rot[1],rot[2]};}
  frame(true);
 }
 assert(pipeline.updates==uploads&&cache.LocalMeshRevision==generation&&zoneChecks==z);
 // Culling/missing model restores even an unmoved proxy. Draw return codes are
 // the real native low/high-word contract, including signed high=-1.
 for(unsigned rejected:{0xffff0000u,0xffff0002u,0x00020004u}){
  body.drawResult=rejected;frame(true);assert(instance.CentreRadius[3]>0&&!ProceduralAsteroidClientNativeVisual(key));
  body.drawResult=0xffff0004u;frame(true);assert(instance.CentreRadius[3]==0);
 }
 frame(false);assert(instance.CentreRadius[3]>0&&instance.CentreRadius[0]==body.pos.x);
 frame(true);assert(instance.CentreRadius[3]==0);
 // Clock-only deltas do not recreate the recipe or placements.
 h.count=0;++h.revision;h.clock=float(Clock);send();assert(UpdateLocalMeshes(&field,cache,eye));assert(fullBuilds==1);
 // Suspend with arbitrary impact spin; preserve pose, keep rotating, then death removes slot.
 h.count=1;++h.revision;auto& e=packet.entries[0];e=P::Entry{};e.key=key;memcpy(e.position,&body.pos.x,12);
 auto q=body.matrix.q;e.rotation[0]=q.x;e.rotation[1]=q.y;e.rotation[2]=q.z;e.rotation[3]=q.w;
 e.stamp=h.clock;e.spin[0]=.1f;send();
 assert(ProceduralAsteroidClientOwns(&body)&&!ProceduralAsteroidClientPhysical(&body));
 frameDt=0;frame(true);frameDt=1.f/60;assert(instance.CentreRadius[3]>0);
 ProceduralAsteroidClientForget(&body);assert(!ProceduralAsteroidClientOwns(&body));
 auto r=P::Generate(key,h.seed,3);assert(ProceduralAsteroidClientResolve(25,r));assert(!memcmp(r.rotation,e.rotation,16));
 ProceduralAsteroidClientTick(15);assert(ProceduralAsteroidClientResolve(25,r));assert(memcmp(r.rotation,e.rotation,16));
 ++h.revision;e.flags=P::Dead;send();assert(UpdateLocalMeshes(&field,cache,eye));assert(instance.CentreRadius[3]==0);
 eye[0]=1001;assert(UpdateLocalMeshes(&field,cache,eye));assert(fullBuilds==2);
 for(auto& m:cache.Meshes)delete m.Placement;
 printf("PASS actual client/placement code: %u residents; stationary %.4f ms/frame, 700 rotating bodies %.4f ms/frame\n",resident,idle,moving);
 puts("PASS no cell rebuild, allocation or zone checks for rotations; 3 partial uploads/frame; push/spatial/suspend/spin/death/clock/cell transition");
 puts("PASS native submit takes over; culled native restores proxy; 700 native rotations cause zero proxy uploads/regroups; suspension recovers pose");
}
