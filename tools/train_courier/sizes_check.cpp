#define main ExistingTrainCheck
#include "../train_consist/check.cpp"
#undef main
#include "../../src/Common/common_train.h"
static CShip* vehicle(char const* model,unsigned id,float mass) {
    auto* arch=new Archetype::Ship;arch->DaArchetype.Value=model;
    auto* object=static_cast<CShip*>(CObject::Alloc(CObject::ClassShip));
    object->CObject::open(arch);object->Id=id;
    need(arch->is_loaded() && arch->create_instance(object)!=-1,"courier CMP loaded");
    PhySys::CreateParms p={};p.Mass=mass;p.CollisionGroupId=1;p.Type=2;
    p.bHasInertia=1;p.Inertia={100000,100000,100000};p.bEnableCollisions=0;
    p.LinearDamping=0;p.AngularDamping[0]=p.AngularDamping[1]=p.AngularDamping[2]=.1f;
    sprintf_s(p.Name,"tc%u",id);PhySys::BuildIVP_Real(object,p);
    need(object->BodyPtr!=nullptr,"courier SUR creates physics");return object;
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);SetUnhandledExceptionFilter(fault);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    need(argc==2,"courier model directory");
    need(DALib::Startup(nullptr,"check_dacom.ini"),"DALib startup");DALib::OpenData(argv[1]);PhySys::Startup(1);PhySys::Startup(2);
    for(unsigned n=2;n<=20;++n) {
        char model[48];std::snprintf(model,sizeof(model),"train_wagons_%02u.cmp",n);
        auto* loco=vehicle("train_locomotive.cmp",1000+n*2,500);
        auto* tail=vehicle(model,1001+n*2,250);
        need(CmnTrain::IsTrailer(tail),"variable length model is recognized as trailer");
        std::vector<Coupling> links={{loco,tail,anchor(tail,"HpCoupleFront"),anchor(loco,"HpCoupleRear")}};
        CObject* previous=tail;
        for(unsigned i=2;i<=n;++i) {
            char part[32];std::snprintf(part,sizeof(part),"TrainWagon%02u",i);
            auto* body=find(tail->EngineInstanceId,part);
            need(body && body->BodyPtr,"each wagon has a separate IVP body");
            links.push_back({previous,body,anchor(body,"HpCoupleFront"),anchor(previous,"HpCoupleRear")});previous=body;
        }
        PhySys::BeamR(loco,{1000,100,2000},EulerMatrix({12,30,25}),false);
        PhySys::AddToVelocity(loco,{0,0,-30});
        need(CmnTrain::RestoreCoupling(loco,tail),"restore a moving train after transfer");
        for(int i=0;i<32;++i){PhySys::Update(1,1.f/16);loco->update_tree();tail->update_tree();}
        need(CmnTrain::Trailer(loco)==tail && CmnTrain::IsDriven(tail),"restored group stays attached");
        need(CmnTrain::Uncouple(loco),"variable length consist detaches");
        PhySys::CreateParms tailParms{},locoParms{};
        // Real server transfer destroys the old IVP bodies and rebuilds them.
        tailParms.Mass=tail->get_mass();locoParms.Mass=loco->get_mass();
        tailParms.Type=locoParms.Type=2;
        tailParms.bHasInertia=locoParms.bHasInertia=1;
        tailParms.Inertia=PhySys::GetMomentOfInertia(tail);locoParms.Inertia=PhySys::GetMomentOfInertia(loco);
        PhySys::UnMakePhysicalR(tail);PhySys::UnMakePhysicalR(loco);
        tailParms.CollisionGroupId=locoParms.CollisionGroupId=2;
        // Match add_ship at an entirely different gate, after JumpInComplete.
        const Vector arrival={36020,-333,-25370};
        loco->WorldPosition=tail->WorldPosition=arrival;
        loco->Orientation=tail->Orientation=EulerMatrix({0,90,2});
        DALib::Engine->UpdateInstance((void*)loco->EngineInstanceId,0,nullptr);
        DALib::Engine->UpdateInstance((void*)tail->EngineInstanceId,0,nullptr);
        PhySys::ReMakePhysicalR(loco,locoParms,0);
        PhySys::ReMakePhysicalR(tail,tailParms,0);
        need(CmnTrain::RestoreCoupling(loco,tail),"couple after actual physics system transfer");
        loco->update_tree();tail->update_tree();
        need(gap(links)<.1,"all coupling pins seated immediately at destination gate");
        need((point(loco,{})-V{arrival.x,arrival.y,arrival.z}).length()<.1,"restoration keeps locomotive at completed arrival pose");
        for(int i=0;i<32;++i){PhySys::Update(2,1.f/16);loco->update_tree();tail->update_tree();}
        need(gap(links)<.2,"arrival consist stays seated after physics ticks");
        need(CmnTrain::Uncouple(loco),"detach after actual transfer");
        CmnTrain::SetCouplable(tail->Id,false);
        need(!CmnTrain::RestoreCoupling(loco,tail),"transfer cannot reattach a delivered group");
        CmnTrain::SetCouplable(tail->Id,true);
        tail->Release();loco->Release();
        std::printf("PASS: %u wagons, independent physics, transfer restoration, retirement\n",n);
    }
    PhySys::Shutdown(2);PhySys::Shutdown(1);
}
