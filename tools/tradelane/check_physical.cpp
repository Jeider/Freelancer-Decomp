#define main ExistingTrainCheck
#include "../train_consist/check.cpp"
#undef main
#include "common_animdb.h"
#include "solar_animation.h"
#include "common_ini.h"

static bool hit(CObject* object, V local) {
    PhySys::RayHit hits[8];
    return PhySys::FindRayIntersect(object,vgame(point(object,{local.x,local.y,80})),
        vgame(point(object,{local.x,local.y,-80})),hits,8)>0;
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);SetUnhandledExceptionFilter(fault);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    need(argc==3,"DATA root and direct/attached mode");
    need(DALib::Startup(nullptr,"check_dacom.ini"),"startup");DALib::OpenData(argv[1]);PhySys::Startup(1);
    bool attached=strcmp(argv[2],"attached")==0;
    auto* arch=new Archetype::Solar;
    INI_Reader reader;char const config[]="[Solar]\nleft_ring_anim = Sc_activate left\nright_ring_anim = Sc_activate right\nphysical_ring_anim = true\n";
    need(reader.open_memory(config,sizeof(config)-1)&&reader.read_header(),"config reader");
    while(reader.read_value())need(arch->read(reader),"native solar accepts physical ring keys");
    SolarAnimation::RingConfig ringConfig;
    need(SolarAnimation::GetRingConfig(arch,ringConfig)&&!strcmp(ringConfig.Left,"Sc_activate left")&&!strcmp(ringConfig.Right,"Sc_activate right"),"native ring config retained without client companion");
    arch->DaArchetype.Value=attached?"SOLAR/DOCKABLE/tlr_root.3db":"SOLAR/DOCKABLE/tlr_legal_lod5.cmp";
    arch->Mass=10000;
    auto* solar=static_cast<CSolar*>(CObject::Alloc(CObject::ClassSolar));solar->CObject::open(arch);solar->Id=123;
    need(arch->is_loaded()&&arch->create_instance(solar)!=-1,"model loaded");
    DALib::Engine->UpdateInstance((void*)solar->EngineInstanceId,0,nullptr);
    PhySys::CreateParms p={};p.Mass=10000;p.CollisionGroupId=1;p.Type=1;p.bFlag1c=1;p.bEnableCollisions=1;
    p.LinearDamping=1e6f;p.AngularDamping[0]=p.AngularDamping[1]=p.AngularDamping[2]=1e6f;strcpy_s(p.Name,"tlr");
    PhySys::BuildIVP_Real(solar,p);
    CECargoPod* pod=nullptr;
    if(attached){
        auto* a=new Archetype::CargoPod;a->DaArchetype.Value="SOLAR/DOCKABLE/tlr_legal_lod5.cmp";a->HpChild.Value="HpRoot";a->Mass=1;
        pod=new CECargoPod(solar,1,a,false);need(pod->Connect("HpRoot"),"current attached CMP connects");
    }
    auto* left=find(solar->EngineInstanceId,"tlr2_lod1");auto* right=find(solar->EngineInstanceId,"tlr1_lod1");
    need(left&&right&&left!=right&&left->BodyPtr&&right->BodyPtr,"two distinct rotor collision bodies");
    Vector boundsCenter;need(solar->get_physical_radius_r(boundsCenter)>400,"parent bounds include rotating parts");
    printf("MODES %d %d\n",left->PhysicsControlMode,right->PhysicsControlMode);
    need(!hit(left,{0,0,0})&&!hit(right,{0,0,0}),"both passage centres are open");
    for(auto* rotor:{left,right}) {
        V sample{};bool found=false;
        for(int x=-240;x<=240&&!found;x+=5)for(int y=-240;y<=240&&!found;y+=5){
            if(x*x+y*y<180*180 || x*x+y*y>230*230)continue;
            if(hit(rotor,{double(x),double(y),0})&&hit(rotor,{double(x+2),double(y),0})&&hit(rotor,{double(x-2),double(y),0})){
                sample={double(x),double(y),0};found=true;
            }
        }
        need(found,"rotor has solid material to probe");
        auto const oldA=vgame(point(rotor,{sample.x,sample.y,80}));auto const oldB=vgame(point(rotor,{sample.x,sample.y,-80}));
        SolarAnimationCommand cmd;strcpy_s(cmd.Name,rotor==left?"Sc_activate left":"Sc_activate right");
        cmd.Serial=rotor==left?1:2;need(SolarAnimation::Play(solar,cmd),"server animation binds native physics parts");
        unsigned vacated=0;
        for(int i=0;i<420;++i){
            AnimDB::Update(1.f/60);PhySys::Update(1,1.f/60);solar->update_tree();
            need(hit(rotor,sample),"collision follows the animated rotor");
            need(!hit(rotor,{0,0,0}),"animation never seals passage centre");
            PhySys::RayHit hits[8];vacated+=PhySys::FindRayIntersect(rotor,oldA,oldB,hits,8)==0;
        }
        need(vacated>30,"collider vacates its old pose during rotation");
        printf("PASS rotor: moving solid, open centre, old pose vacated %u/420 frames\n",vacated);
    }
    // Removing frames must remove their static collision too.
    PhySys::RayHit hits[8];need(PhySys::FindRayIntersect(solar,{-400,-300,80},{-400,-300,-80},hits,8)==0,"removed perimeter has no parent collider");
    delete pod;
    solar->Release();
    puts("PASS native EngBase/Common/IVP: create, animate, collide, empty passages, teardown");
}
