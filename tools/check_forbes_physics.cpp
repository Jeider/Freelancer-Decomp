#define main OriginalTrainCheck
#include "train_consist/check.cpp"
#undef main
#include <fstream>
#include <sstream>
#include <unordered_set>
#include <cstdarg>
static void __cdecl logDump(int,const char* format,...) {va_list args;va_start(args,format);vfprintf(stderr,format,args);va_end(args);}
static void collect(long instance,std::set<CObject*>& objects) {
 auto* o=static_cast<CObject*>(DALib::Engine->GetInstanceUserData((void*)instance));
 if(o && o->BodyPtr)objects.insert(o);
 for(void* child=DALib::Engine->GetRelatedInstance((void*)instance,1,(void*)-1);child!=(void*)-1;
     child=DALib::Engine->GetRelatedInstance((void*)instance,1,child))collect((long)child,objects);
}
int main(int argc,char** argv) {
 _set_invalid_parameter_handler([](const wchar_t* expression,const wchar_t* function,const wchar_t* file,unsigned line,uintptr_t){fwprintf(stderr,L"INVALID %s %s %s:%u\n",expression?expression:L"",function?function:L"",file?file:L"",line);void* frames[32];unsigned count=CaptureStackBackTrace(0,32,frames,nullptr);SymInitialize(GetCurrentProcess(),nullptr,TRUE);for(unsigned i=0;i<count;++i){char b[sizeof(SYMBOL_INFO)+512]={};auto* sym=(SYMBOL_INFO*)b;sym->SizeOfStruct=sizeof(SYMBOL_INFO);sym->MaxNameLen=511;DWORD64 disp=0;if(SymFromAddr(GetCurrentProcess(),(DWORD64)frames[i],&disp,sym))fprintf(stderr,"%s + %llu\n",sym->Name,disp);}std::exit(3);});
 setvbuf(stdout,nullptr,_IONBF,0);SetUnhandledExceptionFilter(fault);
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 need(argc==3,"data root and fixture");
 need(DALib::Startup(nullptr,"check_dacom.ini"),"startup");DALib::OpenData(argv[1]);need(DALib::Data!=nullptr,"filesystem");need(DALib::Engine!=nullptr,"engine");PhySys::Startup(1);
 FDUMP=logDump;
 std::ifstream input(argv[2]);std::string line;std::vector<CSolar*> solars;
 struct Pod {unsigned owner;std::string model,child,mount;};std::vector<Pod> pods;
 std::ifstream podFile(std::string(argv[2])+".pods");Pod entry;
 while(podFile>>entry.owner>>entry.model>>entry.child>>entry.mount)pods.push_back(entry);
 unsigned id=1;auto start=std::chrono::steady_clock::now();
 while(std::getline(input,line)) {
  std::istringstream row(line);std::string path;float x,y,z;int expected,phantom;
  if(!(row>>path>>x>>y>>z>>expected>>phantom))continue;
  printf("OPEN %s\n",path.c_str());
  auto* arch=new Archetype::Solar;arch->DaArchetype.Value=path.c_str();arch->Mass=10000;arch->bPhantomPhysics=phantom!=0;
  auto* solar=static_cast<CSolar*>(CObject::Alloc(CObject::ClassSolar));solar->CObject::open(arch);solar->Id=id++;
  need(arch->is_loaded() && arch->create_instance(solar)!=-1,"model loaded");
  solar->WorldPosition={x,y,z};
  for(int r=0;r<3;++r)for(int c=0;c<3;++c){float v;if(row>>v)solar->Orientation.E[r][c]=v;}
  Vector rayA,rayB;bool ray=bool(row>>rayA.x>>rayA.y>>rayA.z>>rayB.x>>rayB.y>>rayB.z);
  DALib::Engine->UpdateInstance((void*)solar->EngineInstanceId,0,nullptr);
  PhySys::CreateParms p={};p.Mass=10000;p.CollisionGroupId=1;p.Type=1;p.bFlag1c=1;p.bEnableCollisions=1;
  p.LinearDamping=1e6f;p.AngularDamping[0]=p.AngularDamping[1]=p.AngularDamping[2]=1e6f;
  sprintf_s(p.Name,"u%u",solar->Id);
  printf("CREATE %s\n",path.c_str());PhySys::BuildIVP_Real(solar,p);
  std::set<CObject*> bodies;collect(solar->EngineInstanceId,bodies);
  printf("BODIES %zu expected %d\n",bodies.size(),expected);need(int(bodies.size())==expected,"independent collision bodies");
  if(phantom){Vector center;float radius=solar->get_physical_radius_r(center);printf("VISUAL_RADIUS %.3f\n",radius);need(radius>10,"client culling radius covers visual section");}
  if(ray){PhySys::RayHit hits[8];need(PhySys::FindRayIntersect(solar,rayA,rayB,hits,8)>0,"static collider blocks ray at original surface");}
  unsigned equipment=0;
  for(auto const& spec:pods)if(spec.owner==solar->Id){
   auto* arch=new Archetype::CargoPod;arch->DaArchetype.Value=spec.model.c_str();arch->HpChild.Value=spec.child.c_str();arch->Mass=10000;
   auto* pod=new CECargoPod(solar,++equipment,arch,false);
   need(pod->Connect(spec.mount.c_str()),"retained equipment connects to original hardpoint");
  }
  if(equipment)printf("RETAINED_PODS %u\n",equipment);
  solars.push_back(solar);
 }
 unsigned maxPool=0;
 for(int tick=0;tick<32;++tick){
  PhySys::Update(1,1.f/16);
  for(auto* solar:solars){solar->update_tree();std::set<CObject*> bodies;collect(solar->EngineInstanceId,bodies);
   for(auto* o:bodies){auto const& h=o->BodyPtr->hull_manager;
    need(h.PoolCount<=h.PoolCapacity,"pool not overflowed");maxPool=(std::max)(maxPool,unsigned(h.PoolCount));
   }
  }
 }
 printf("MAX_POOL %u\n",maxPool);need(maxPool<30000,"headroom below original growth overflow");
 for(auto it=solars.rbegin();it!=solars.rend();++it)(*it)->Release();
 printf("PASS: create, simulate, destroy; elapsed %.3f seconds\n",std::chrono::duration<double>(std::chrono::steady_clock::now()-start).count());
}

