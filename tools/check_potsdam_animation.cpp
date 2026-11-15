#include "dacom.h"
#include "dacom_iids.h"
#include "engine/engbase.h"
#include "dalib_core.h"
#include "readfile.h"
#include <cstdio>
#include <cstdlib>
#include <cmath>
namespace DALib { DALIB_API extern ICOManager* Dacom; DALIB_API extern IFileSystem* Data; }
static void need(bool yes,const char* msg){if(!yes){std::fprintf(stderr,"FAIL %s\n",msg);std::exit(1);}}
int main(int argc,char**argv){
    setvbuf(stdout,nullptr,_IONBF,0);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    need(argc==3 || argc==5,"ini, model and optional clip/rotor count required");
    const char* clip=argc==5?argv[3]:"Sc_potsdam_solar_rotation";
    int rotorCount=argc==5?std::atoi(argv[4]):3;
    DALib::Dacom=DACOM_Acquire();
    need(DALib::Dacom->SetINIConfig(argv[1],0)>=0,"DACOM init");
    DALib::OpenData(".");need(DALib::Data!=nullptr,"DOS filesystem");
    struct Desc {unsigned long size;const char* name;}desc={8,"Engine"};
    IEngine* engine=nullptr;
    need(DALib::Dacom->CreateInstance((AGGDESC*)&desc,(void**)&engine)>=0,"Engine");
    need(engine->LoadEngineComponents(nullptr)>=0,"Engine components");
    IAnimation2* anim=nullptr;
    need(engine->QueryInterface(Iids::Animation2,(void**)&anim)>=0,"Animation");
    engine->SetFilesystem(DALib::Data);
    IFileSystem* fs=nullptr;
    need(engine->CreateFileSystem(argv[2],(void**)&fs,nullptr)>=0 && fs,"CMP filesystem");
    FEngineName name={argv[2],DACOM_CRC::GetCRC32(argv[2])};
    void* arch=engine->CreateArchetypeHandle(&name,fs);
    need(arch && arch!=G_InvalidEngineHandle,"CMP archetype");
    void* instance=engine->CreateInstance(arch,nullptr);
    need(instance && instance!=G_InvalidEngineHandle,"CMP instance");
    fs->OpenNode("\\");
    void* script=anim->OpenScript(fs);
    need(script && script!=G_InvalidEngineHandle,"animation script");
    auto playback=anim->PlayScript(script,instance,clip,nullptr,nullptr);
    need(playback!=~0ul,"bound rotation clip");
    need(std::fabs(anim->GetScriptDuration(AsOpaqueDword(playback))-90)<.001,"90 second period");
    anim->EvalPlayback(playback,2,0,1,nullptr,AsOpaqueDword(1.f),AsOpaqueDword(1.f),nullptr);
    for(int frame=0;frame<=722;++frame){
        float time=frame*.125f;
        anim->MixerWalk((unsigned long)instance,frame ? .125f : 0);
        engine->UpdateInstance(instance,0,nullptr);
        void* child=G_InvalidEngineHandle;int count=0;
        while((child=engine->GetRelatedInstance(instance,1,child))!=G_InvalidEngineHandle){
            FEngineName childName={};engine->GetInstanceName(&childName,child);
            float* pos=engine->GetInstancePosition(child);float* rot=engine->GetInstanceOrientation(child);
            std::printf("POSE %.8g %s",time,childName.Text);
            for(int i=0;i<3;++i)std::printf(" %.9g",pos[i]);
            for(int i=0;i<9;++i)std::printf(" %.9g",rot[i]);
            std::puts("");++count;
        }
        need(count==rotorCount,"expected rotor instances");
    }
    std::puts("PASS native animation evaluation");
    return 0;
}
