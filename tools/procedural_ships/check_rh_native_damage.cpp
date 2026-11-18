#include "dacom.h"
#include "dacom_iids.h"
#include "engine/engbase.h"
#include "dalib_core.h"
#include "readfile.h"
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cmath>
#include <cstdarg>
namespace DALib { DALIB_API extern ICOManager* Dacom; DALIB_API extern IFileSystem* Data; }
static void __cdecl logDump(int,const char* fmt,...){va_list args;va_start(args,fmt);std::vfprintf(stderr,fmt,args);va_end(args);}
static void need(bool ok,const char* msg){if(!ok){std::fprintf(stderr,"FAIL %s\n",msg);std::exit(1);}}
static void* find(IEngine* e,void* parent,const char* name){
    void* it=G_InvalidEngineHandle;
    while((it=e->GetRelatedInstance(parent,1,it))!=G_InvalidEngineHandle){
        FEngineName n={};e->GetInstanceName(&n,it);
        if(n.Text && !std::strcmp(n.Text,name))return it;
        void* child=find(e,it,name);if(child!=G_InvalidEngineHandle)return child;
    }
    return G_InvalidEngineHandle;
}
int main(int argc,char**argv){
    setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    need(argc==3,"ini and CMP arguments");FDUMP=logDump;
    DALib::Dacom=DACOM_Acquire();need(DALib::Dacom->SetINIConfig(argv[1],0)>=0,"DACOM init");
    char loaded[MAX_PATH]={};GetModuleFileNameA(GetModuleHandleA("EngBase.dll"),loaded,MAX_PATH);
    std::printf("ENGBASE %s\n",loaded);
    DALib::OpenData(".");need(DALib::Data!=nullptr,"DOS filesystem");
    struct Desc{unsigned long size;const char* name;}desc={8,"Engine"};IEngine* e=nullptr;
    need(DALib::Dacom->CreateInstance((AGGDESC*)&desc,(void**)&e)>=0,"Engine");
    need(e->LoadEngineComponents(nullptr)>=0,"Engine components");IAnimation2* a=nullptr;
    need(e->QueryInterface(Iids::Animation2,(void**)&a)>=0,"Animation");e->SetFilesystem(DALib::Data);
    IFileSystem* fs=nullptr;need(e->CreateFileSystem(argv[2],(void**)&fs,nullptr)>=0&&fs,"CMP filesystem");
    FEngineName name={argv[2],DACOM_CRC::GetCRC32(argv[2])};void* arch=e->CreateArchetypeHandle(&name,fs);
    need(arch&&arch!=G_InvalidEngineHandle,"CMP archetype");fs->OpenNode("\\");void* script=a->OpenScript(fs);
    need(script&&script!=G_InvalidEngineHandle,"script");
    for(unsigned gone=0;gone<4;++gone){
        void* root=e->CreateInstance(arch,nullptr);need(root&&root!=G_InvalidEngineHandle,"instance");
        const char* owners[]={"Rh_port_wing_lod1","Rh_starboard_wing_lod1"};
        for(unsigned side=0;side<2;++side){
            void* wing=find(e,root,owners[side]);need(wing!=G_InvalidEngineHandle,"wing owner");
            if(gone&(1u<<side))e->DestroyInstance(wing);
        }
        auto playback=a->PlayScript(script,root,"Sc_launch extend",nullptr,nullptr);
        if(gone==3){
            need(playback==~0ul,"missing pair must reject playback");
            need(a->GetStoredDuration(playback)==-1.f,"invalid handle duration");
        }else{
            need(playback!=~0ul,"surviving wing playback");
            const float duration=a->GetScriptDuration(AsOpaqueDword(playback));need(duration>0,"duration");
            a->EvalPlayback(playback,0,0,1,nullptr,AsOpaqueDword(1.f),AsOpaqueDword(1.f),nullptr);
            for(unsigned frame=0;frame<=32;++frame){
                a->MixerWalk((unsigned long)root,frame?duration/32.f:0);e->UpdateInstance(root,0,nullptr);
                need(std::isfinite(a->GetStoredDuration(playback)),"finite playback clock");
            }
            a->DestroyScript(AsOpaqueDword(playback));
        }
        e->DestroyInstance(root);std::printf("PASS native CMP launch, missing mask %u\n",gone);
    }
    // Destroy an animated owner during playback, then ask time and restart safely.
    void* root=e->CreateInstance(arch,nullptr);
    auto playback=a->PlayScript(script,root,"Sc_launch extend",nullptr,nullptr);
    need(playback!=~0ul,"live playback");
    a->EvalPlayback(playback,0,0,1,nullptr,AsOpaqueDword(1.f),AsOpaqueDword(1.f),nullptr);
    a->MixerWalk((unsigned long)root,.1f);
    e->DestroyInstance(find(e,root,"Rh_port_wing_lod1"));
    a->MixerWalk((unsigned long)root,.1f);e->UpdateInstance(root,0,nullptr);
    need(std::isfinite(a->GetStoredDuration(playback)),"clock after live loss");
    e->DestroyInstance(find(e,root,"Rh_starboard_wing_lod1"));
    a->MixerWalk((unsigned long)root,.1f);e->UpdateInstance(root,0,nullptr);
    need(std::isfinite(a->GetStoredDuration(playback)),"clock after live pair loss");
    a->DestroyScript(AsOpaqueDword(playback));
    need(a->PlayScript(script,root,"Sc_launch extend",nullptr,nullptr)==~0ul,"restart after live pair loss");
    e->DestroyInstance(root);a->CloseScript(script);e->ReleaseHandle(arch);
    std::puts("PASS native live wing destruction and restart");return 0;
}
