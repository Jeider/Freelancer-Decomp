#include "dacom.h"
#include "dacom_iids.h"
#include "engine/engbase.h"
#include "dalib_core.h"
#include "readfile.h"
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <array>
#include <map>
#include <set>
#include <string>
namespace DALib { DALIB_API extern ICOManager* Dacom; DALIB_API extern IFileSystem* Data; }
static void need(bool yes,const char* message){if(!yes){std::fprintf(stderr,"FAIL %s\n",message);std::exit(1);}}
using Poses=std::map<std::string,std::array<float,12>>;
static void poses(IEngine* engine,void* instance,Poses& result,std::set<void*>& seen){
 if(!seen.insert(instance).second)return;
 FEngineName name={};engine->GetInstanceName(&name,instance);
 if(name.Text){auto& pose=result[name.Text];float* p=engine->GetInstancePosition(instance);float* r=engine->GetInstanceOrientation(instance);
  for(int i=0;i<3;++i)pose[i]=p[i];for(int i=0;i<9;++i)pose[i+3]=r[i];}
 void* child=G_InvalidEngineHandle;
 while((child=engine->GetRelatedInstance(instance,1,child))!=G_InvalidEngineHandle)poses(engine,child,result,seen);
}
int main(int argc,char**argv){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 need(argc>=4&&argc<=6,"ini, model, dock count, optional active side/layout");int ports=std::atoi(argv[3]);need(ports>=2&&ports<=8,"port count");
 int activeSide=argc>=5?std::atoi(argv[4]):1;
 bool shipping=argc==6&&std::string(argv[5])=="shipping";
 DALib::Dacom=DACOM_Acquire();need(DALib::Dacom->SetINIConfig(argv[1],0)>=0,"DACOM config");DALib::OpenData(".");
 struct Desc {unsigned long size;const char* name;}desc={8,"Engine"};IEngine* engine=nullptr;
 need(DALib::Dacom->CreateInstance((AGGDESC*)&desc,(void**)&engine)>=0,"engine");need(engine->LoadEngineComponents(nullptr)>=0,"components");
 IAnimation2* anim=nullptr;IHardpoint* hp=nullptr;
 need(engine->QueryInterface(Iids::Animation2,(void**)&anim)>=0,"animation interface");
 need(engine->QueryInterface(Iids::Hardpoint,(void**)&hp)>=0,"hardpoint interface");
 engine->SetFilesystem(DALib::Data);IFileSystem* fs=nullptr;
 need(engine->CreateFileSystem(argv[2],(void**)&fs,nullptr)>=0&&fs,"CMP filesystem");
 FEngineName name={argv[2],DACOM_CRC::GetCRC32(argv[2])};void* arch=engine->CreateArchetypeHandle(&name,fs);
 need(arch&&arch!=G_InvalidEngineHandle,"CMP archetype");fs->OpenNode("\\");void* script=anim->OpenScript(fs);
 need(script&&script!=G_InvalidEngineHandle,"scripts");
 for(int port=1;port<=ports;++port){
  void* instance=engine->CreateInstance(arch,nullptr);need(instance&&instance!=G_InvalidEngineHandle,"instance");
  void* hpArch=engine->GetInstanceArchetype(instance);
  for(auto suffix:{std::string("Mount")+char(64+port),std::string("Point")+char(64+port)+"01",std::string("Point")+char(64+port)+"02",std::string("Cam")+char(64+port)}){
   std::string text="HpDock"+suffix;FHardpointKey key={text.c_str(),DACOM_CRC::GetCRC32(text.c_str())};char buffer[0x48];
   if(!hp->GetHardpoint(hpArch,&key,buffer)){printf("MISSING %s\n",text.c_str());need(false,"dock hardpoint resolves");}
  }
  engine->ReleaseHandle(hpArch);
  std::string clip="Sc_open dock"+std::to_string(port);auto playback=anim->PlayScript(script,instance,clip.c_str(),nullptr,nullptr);
  need(playback!=~0ul,"front script bound");need(std::fabs(anim->GetScriptDuration(AsOpaqueDword(playback))-3.333333)<.001,"retail door duration");
  anim->EvalPlayback(playback,2,0,1,nullptr,AsOpaqueDword(1.f),AsOpaqueDword(1.f),nullptr);
  anim->MixerWalk((unsigned long)instance,0);engine->UpdateInstance(instance,0,nullptr);
  Poses before,after;std::set<void*> seen;poses(engine,instance,before,seen);
  for(int frame=0;frame<200;++frame){anim->MixerWalk((unsigned long)instance,1.f/60);engine->UpdateInstance(instance,0,nullptr);}
  seen.clear();poses(engine,instance,after,seen);need(before.size()==after.size(),"stable part count");
  for(int dock=1;dock<=ports;++dock)for(int side=1;side<=(shipping?1:2);++side)for(char leaf:{'a','b'}){
   std::string part=shipping ? "door"+std::to_string(dock)+"_"+leaf+"_lod1" : "D"+std::to_string(dock)+"_door"+std::to_string(side)+"_"+leaf+"_lod1";
   need(before.count(part)&&after.count(part),"all front/rear leaves exist");float change=0;
   for(int k=0;k<12;++k)change+=std::fabs(after[part][k]-before[part][k]);
   need((dock==port&&side==activeSide)?change>.5f:change<.001f,"only selected entrance leaves move");
  }
  printf("PASS dock %d: independent entrance animation (source side %d); other leaves stay closed\n",port,activeSide);
  engine->DestroyInstance(instance);
 }
 puts("PASS all native dock animations and approach hardpoints");return 0;
}
