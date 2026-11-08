#define main OriginalTrainCheck
#include "check.cpp"
#undef main
#include "../../src/Common/common_train.h"
#include "common_id.h"
#include "common_csys.h"
#include "train_yard_bridge.h"
static CShip* vehicle(char const* model,unsigned id,float mass) {
    auto* arch=new Archetype::Ship;arch->DaArchetype.Value=model;
    auto* object=static_cast<CShip*>(CObject::Alloc(CObject::ClassShip));
    object->CObject::open(arch);object->Id=id;
    need(arch->is_loaded() && arch->create_instance(object)!=-1,"yard CMP loaded");
    PhySys::CreateParms p={};p.Mass=mass;p.CollisionGroupId=1;p.Type=2;
    p.bHasInertia=1;p.Inertia={100000,100000,100000};p.bEnableCollisions=0;
    p.LinearDamping=0;p.AngularDamping[0]=p.AngularDamping[1]=p.AngularDamping[2]=.1f;
    sprintf_s(p.Name,"y%u",id);PhySys::BuildIVP_Real(object,p);
    need(object->BodyPtr!=nullptr,"yard physical body");return object;
}
static V speed(CObject* o) {auto v=PhySys::GetVelocity(o);return {v.x,v.y,v.z};}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);SetUnhandledExceptionFilter(fault);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    need(argc==2,"yard model directory");
    need(DALib::Startup(nullptr,"check_dacom.ini"),"DALib startup");DALib::OpenData(argv[1]);PhySys::Startup(1);
    char flagsFile[1024];sprintf_s(flagsFile,"%s/yard_flags.ini",argv[1]);
    Archetype::LoadShips(flagsFile,false,nullptr);
    auto flags=[](char const* name){auto* a=Archetype::GetShip(CreateID(name));need(a!=nullptr,"flag fixture loaded");return a;};
    need(flags("test_maneuver_default")->GetExtraManeuvers(),"fighters default to extra maneuvers");
    need(!flags("test_maneuver_capital")->GetExtraManeuvers(),"shiparch flag disables extra maneuvers");
    need(!flags("test_maneuver_inherited")->GetExtraManeuvers(),"shiparch inherit preserves flag");
    need(flags("test_maneuver_override")->GetExtraManeuvers(),"explicit true overrides inherited flag");
    flags("test_maneuver_override")->redefine(*flags("test_maneuver_capital"));
    need(!flags("test_maneuver_override")->GetExtraManeuvers(),"archetype reload preserves flag");
    std::puts("PASS: extra_maneuvers parsing, default, inheritance, override and reload");
    auto* loco=vehicle("train_locomotive.cmp",1001,500);
    auto* wagons=vehicle("train_wagons.cmp",1002,250);
    PhySys::BeamR(wagons,{0,0,25.37048f+TrainYard::SpawnPinGap},loco->Orientation,false);
    char gunsFile[1024];sprintf_s(gunsFile,"%s/yard_guns.ini",argv[1]);
    Archetype::LoadEquipment(gunsFile,false,nullptr);
    auto* gunArch=static_cast<Archetype::Gun*>(Archetype::GetEquipment(CreateID("co_train_turret01_mark01")));
    need(gunArch!=nullptr,"loaded actual train turret archetype");
    std::vector<CEGun*> guns;
    for(int i=1;i<=6;++i) {
        auto* gun=new CEGun(i==6?wagons:loco,static_cast<unsigned short>(100+i),gunArch,false);
        char hp[32];sprintf_s(hp,"HpTurret%02d",i);
        need(gun->Connect(hp) && gun->GetBarrelInfo(0),"six real turrets mount and have barrels");
        gun->Activate(true);guns.push_back(gun);
    }
    auto* podArch=new Archetype::CargoPod;podArch->DaArchetype.Value="pod_grey.3db";podArch->HpChild.Value="HpConnect";
    std::vector<CECargoPod*> pods;
    for(int i=0;i<40;++i) {
        auto* pod=new CECargoPod(wagons,(unsigned short)(i+1),podArch,false);
        char hp[32];sprintf_s(hp,"HpCargo%02d",i+1);
        need(pod->Connect(hp),"independent trailer owns cargo pods");pods.push_back(pod);
    }
    std::vector<CObject*> bodies={loco,wagons};std::vector<Coupling> links;
    for(int i=2;i<=20;++i) {char name[32];sprintf_s(name,"TrainWagon%02d",i);auto* child=find(wagons->EngineInstanceId,name);need(child!=nullptr,"trailer wagon exists");bodies.push_back(child);}
    for(int i=1;i<21;++i)links.push_back({bodies[i-1],bodies[i],anchor(bodies[i],"HpCoupleFront"),anchor(bodies[i-1],"HpCoupleRear")});
    loco->enable_collisions_r(true);wagons->enable_collisions_r(true);
    auto step=[&](int count) {for(int i=0;i<count;++i){
        CmnTrain::Sync(loco);
        PhySys::Update(1,1.f/16);loco->update_tree();wagons->update_tree();
        for(auto* body:bodies)body->CObject::update(1.f/16,0);
    }};
    step(2);
    for(auto* body:bodies)need(body->CollisionStateMgr->get_actual_collision_state(),"spawned hulls are solid without flying away");
    std::string originalTailGroup=PhySys::GetCollisionGroup(wagons);
    auto parkedPoses=[&] {
        std::vector<V> result;
        for(size_t i=1;i<bodies.size();++i)for(V p:{V{},V{0,20,0},V{0,0,20}})result.push_back(point(bodies[i],p));
        return result;
    };
    auto checkParked=[&](std::vector<V> const& before) {
        auto after=parkedPoses();double error=0;
        for(size_t i=0;i<after.size();++i)error=(std::max)(error,(after[i]-before[i]).length());
        std::printf("Parked pose error %.8f m\n",error);
        need(error<.001,"every parked wagon retains position and orientation");
    };
    auto spawnPoses=parkedPoses();
    // Includes the real ship-controller enable path, performed after body creation.
    wagons->enable_controllers();
    for(size_t i=1;i<bodies.size();++i) {
        PhySys::AddImpulseAtPoint(bodies[i],{7000,2000,9000},vgame(point(bodies[i],{8,5,20})));
        PhySys::AddToAngularVelocityOS(bodies[i],{1,2,3});
    }
    step(16*5);checkParked(spawnPoses);
    // A genuine IVP collision must hit an immovable wagon rather than pass through.
    auto* impact=CObject::Alloc(CObject::ClassObject);
    auto* last=bodies.back();impact->WorldPosition=vgame(point(last,{40,2,21}));
    PhySys::CreateParms ball={};ball.Mass=500;ball.CollisionGroupId=1;ball.Type=2;
    ball.bEnableCollisions=1;strcpy_s(ball.Name,"impact");PhySys::BuildIVP_Sphere(impact,3,ball);
    V toward=point(last,{0,2,21})-point(impact,{});
    PhySys::AddToVelocity(impact,vgame(toward*(20/toward.length())));
    int contacts=0;
    for(int i=0;i<16*4;++i){
        step(1);PhySys::CollisionEvent const *begin,*end;PhySys::GetCollisions(1,begin,end);
        contacts+=(int)(end-begin);
    }
    std::printf("Parked wagon impact: %d collision events\n",contacts);
    need(contacts>0,"solid collision with a parked wagon");checkParked(spawnPoses);impact->Release();
    float distance=0;need(CmnTrain::CanCouple(loco,wagons,&distance)==1,"aligned parked trailer may couple");
    need(distance>11.9 && distance<12.1,"larger spawn gap is inside capture distance");
    PhySys::BeamR(loco,{0,0,-2.9f},loco->Orientation,false);
    need(CmnTrain::CanCouple(loco,wagons)==1,"capture at 14.9 m");
    PhySys::BeamR(loco,{0,0,-3.1f},loco->Orientation,false);
    need(CmnTrain::CanCouple(loco,wagons)==-4,"reject beyond 15 m");
    PhySys::BeamR(loco,{0,0,0},loco->Orientation,false);
    PhySys::AddToVelocity(loco,{0,0,-3});need(CmnTrain::CanCouple(loco,wagons)==-5,"reject high closing speed");
    PhySys::AddToVelocity(loco,{0,0,3});
    PhySys::BeamR(loco,{50,0,0},loco->Orientation,false);need(CmnTrain::CanCouple(loco,wagons)==-4,"reject remote coupling");
    PhySys::BeamR(loco,{0,0,0},loco->Orientation,false);
    Matrix straight=loco->Orientation;
    // Capture from the side, above, upside down, backwards and a compound angle.
    // Approach at a permitted speed: seating must stop relative motion, not
    // launch the wagons or ask the angular solver to undo the initial mismatch.
    for(Vector angles:{Vector{0,90,0},Vector{70,0,0},Vector{0,0,180},Vector{0,180,0},Vector{45,125,65}}) {
        auto before=parkedPoses();
        Matrix turned=EulerMatrix(angles);
        PhySys::BeamR(loco,{0,0,0},turned,false);
        V rearOffset=point(loco,anchor(loco,"HpCoupleRear"))-point(loco,{});
        V front=point(wagons,anchor(wagons,"HpCoupleFront"));
        PhySys::BeamR(loco,vgame(front+V{8,6,-6}-rearOffset),turned,false);
        PhySys::AddToVelocity(loco,vgame(V{.5,0,0}-speed(loco)));
        need(CmnTrain::CanCouple(loco,wagons,&distance)==1 && distance>11 && distance<12,"capture accepts arbitrary orientation");
        V start=point(loco,{});
        need(CmnTrain::BeginCouple(loco,wagons)==1 && CmnTrain::IsCoupling(loco),"smooth capture begins");
        need((point(loco,{})-start).length()<.0001 && !CmnTrain::Trailer(loco),"begin capture does not teleport or join");
        need(CmnTrain::BeginCouple(loco,wagons)==-2,"duplicate approach rejected");
        int steps=0;double maxStep=0,peakApproach=0;
        while(CmnTrain::IsCoupling(loco) && steps<16*30) {
            V previous=point(loco,{});step(1);++steps;
            maxStep=(std::max)(maxStep,(point(loco,{})-previous).length());
            peakApproach=(std::max)(peakApproach,speed(loco).length());
            if(CmnTrain::IsCoupling(loco))for(size_t i=1;i<bodies.size();++i)
                need((bodies[i]->BodyPtr->core->Flags&0xc)==4,"wagons stay parked throughout approach");
        }
        need(CmnTrain::Trailer(loco)==wagons && steps>16*3 && steps<16*30,"smooth capture completes in bounded time");
        need(maxStep<1.5 && peakApproach<22,"smooth capture has no position jump or runaway speed");
        std::printf("Smooth approach %.2f s, largest step %.4f m, peak speed %.4f\n",steps/16.,maxStep,peakApproach);
        checkParked(before);need(gap(links)<.001,"smooth capture seats pins without moving wagons");
        need(speed(loco).length()<.001,"automatic capture matches parked wagon speed");
        for(int i=0;i<3;++i)for(int j=0;j<3;++j)
            need(std::abs(loco->Orientation.E[i][j]-wagons->Orientation.E[i][j])<.0001,"automatic capture matches wagon orientation");
        double peakSpeed=0;
        for(int i=0;i<32;++i){step(1);for(auto* body:bodies)peakSpeed=(std::max)(peakSpeed,speed(body).length());}
        need(peakSpeed<.05 && gap(links)<.01,"arbitrary-angle capture remains stable without impulses");
        std::printf("Capture angles %.0f %.0f %.0f: max speed %.6f gap %.6f\n",angles.x,angles.y,angles.z,peakSpeed,gap(links));
        need(CmnTrain::Uncouple(loco),"detach after automatic capture");
    }
    // Use the yard save's real world coordinates and orientation. At 42 km a
    // float position has millimetre-scale spacing, unlike the origin fixture.
    Vector savedTailPos=wagons->WorldPosition;Matrix savedTailRot=wagons->Orientation;
    Matrix spaceRotation=EulerMatrix({.0150823f,-27.5715f,-.0345308f});
    PhySys::BeamR(wagons,{42347.985657f,-.646790f,-4346.363017f},spaceRotation,false);
    for(float frameTime:{1.f/16,1.f/30,1.f/60,1.f/144,1.f/240})for(Vector angles:{Vector{.0150823f,-27.5715f,-.0345308f},Vector{45,125,65}}) {
    // ge_t_engine_01 drag 3000 + hull drag 1, mass 500; angular drag/inertia 900000/600000.
    PhySys::SetDamping(loco,6.002f,{1.5f,1.5f,1.5f});
    Matrix approachRotation=EulerMatrix(angles);
    PhySys::BeamR(loco,{0,0,0},approachRotation,false);
    V spaceFront=point(wagons,anchor(wagons,"HpCoupleFront"));
    V spaceRear=point(loco,anchor(loco,"HpCoupleRear"))-point(loco,{});
    PhySys::BeamR(loco,vgame(spaceFront-spaceRear+V{4,0,-10}),approachRotation,false);
    PhySys::AddToVelocity(loco,vgame(-speed(loco)));
    need(CmnTrain::BeginCouple(loco,wagons)==1,"begin approach at actual space coordinates");
    int spaceSteps=0;
    while(CmnTrain::IsCoupling(loco) && spaceSteps*frameTime<30){
        CmnTrain::Sync(loco);
        PhySys::Update(1,frameTime);loco->update_tree();wagons->update_tree();
        for(auto* body:bodies)body->CObject::update(frameTime,0);
        ++spaceSteps;
    }
    double spaceGap=(point(loco,anchor(loco,"HpCoupleRear"))-point(wagons,anchor(wagons,"HpCoupleFront"))).length();
    std::printf("Space capture at %.0f fps: %.2f s, joined %d, pin gap %.8f, speed %.8f\n",1/frameTime,spaceSteps*frameTime,CmnTrain::Trailer(loco)!=nullptr,spaceGap,speed(loco).length());
    need(CmnTrain::Trailer(loco)==wagons && spaceSteps*frameTime<30,"capture finalizes at the save's world position");
    need(CmnTrain::Uncouple(loco),"detach after space capture");
    }
    PhySys::SetDamping(loco,0,{.1f,.1f,.1f});
    PhySys::BeamR(wagons,savedTailPos,savedTailRot,false);
    PhySys::BeamR(loco,{0,0,0},straight,false);
    // An impulse between the last physics step and the game update must not
    // silently discard a finished approach when Couple rechecks closing speed.
    need(CmnTrain::BeginCouple(loco,wagons)==1,"begin finalization retry scenario");
    for(int i=0;i<16*8;++i) {
        PhySys::Update(1,1.f/16);loco->update_tree();wagons->update_tree();
        for(auto* body:bodies)body->CObject::update(1.f/16,0);
    }
    need(CmnTrain::IsCoupling(loco) && !CmnTrain::Trailer(loco),"joining waits for the game update");
    PhySys::AddToVelocity(loco,vgame(V{3,0,0}-speed(loco)));
    CmnTrain::Sync(loco);
    need(CmnTrain::IsCoupling(loco) && !CmnTrain::Trailer(loco),"late impulse retains pending approach");
    step(16*2);
    need(CmnTrain::Trailer(loco)==wagons,"approach settles and retries final join");
    need(CmnTrain::Uncouple(loco),"detach after finalization retry");
    std::puts("PASS: late impulse retries finalization without dropping the approach");
    PhySys::BeamR(loco,{0,0,0},straight,false);
    need(CmnTrain::BeginCouple(loco,wagons)==1,"begin cancellable approach");step(8);
    V cancelled=point(loco,{});
    need(CmnTrain::CancelCoupling(loco) && !CmnTrain::IsCoupling(loco) && !CmnTrain::Trailer(loco),"cancel keeps train separate");
    step(16);need((point(loco,{})-cancelled).length()<.01,"cancel stops the locomotive");
    PhySys::BeamR(loco,{0,0,0},straight,false);
    loco->bUsingTradelane=1;need(CmnTrain::CanCouple(loco,wagons)==-7,"reject scripted travel coupling");loco->bUsingTradelane=0;
    need(CmnTrain::Couple(loco,wagons)==1 && CmnTrain::Trailer(loco)==wagons,"join two world ships");
    for(size_t i=1;i<bodies.size();++i)need(!(bodies[i]->BodyPtr->core->Flags&0xc),"coupling restores dynamic cores");
    need(CmnTrain::Couple(loco,wagons)==-2,"duplicate coupling rejected");
    step(16*5);
    std::printf("Coupled settled gap %.6f\n",gap(links));
    for(size_t i=0;i<links.size();++i) {
        auto const& j=links[i];double d=(point(j.a,j.rear)-point(j.b,j.front)).length();
        if(d>.04)std::printf("link %u gap %.6f\n",static_cast<unsigned>(i),d);
    }
    need(gap(links)<.04,"coupled pins settle");
    for(auto* gun:guns) {
        gun->Update(1,0);
        Vector position=gun->GetBarrelPosWS(0),direction=gun->GetBarrelDirWS(0);
        Vector aim={position.x+direction.x*1000,position.y+direction.y*1000,position.z+direction.z*1000};
        need(gun->Fire(aim)==FireOk,"all six attached train turrets can fire");
    }
    std::puts("PASS: five locomotive turrets and last-wagon turret mount and fire");
    Vector center;need(PhySys::GetRadiusR(loco,false,center)>800,"coupled locomotive bounds include standalone trailer");
    for(int i=0;i<16*10;++i){PhySys::AddToVelocity(loco,{0,0,-2});step(1);}
    need(speed(wagons).z< -10 && gap(links)<.15,"locomotive tows independent trailer through joints");
    auto beforeHead=speed(loco);auto beforeDetach=parkedPoses();
    need(CmnTrain::Uncouple(loco) && !CmnTrain::Trailer(loco),"uncouple whole trailer");
    need((speed(loco)-beforeHead).length()<.0001 && speed(wagons).length()<.0001,"uncoupling stops wagons and preserves locomotive velocity");
    checkParked(beforeDetach);
    need(PhySys::GetRadiusR(loco,false,center)<100,"uncoupled bounds shrink to locomotive");
    PhySys::BeamR(loco,{1000,100,1000},loco->Orientation,false);loco->bUsingTradelane=1;step(16*2);loco->bUsingTradelane=0;
    checkParked(beforeDetach);
    need(originalTailGroup==PhySys::GetCollisionGroup(wagons),"separation restores independent wagon collisions");
    std::vector<Coupling> internal(links.begin()+1,links.end());need(gap(internal)<.15,"detached wagons stay coupled internally");
    // Return and align with the now stationary wagon group.
    V front=point(wagons,anchor(wagons,"HpCoupleFront"));
    V rearLocal=anchor(loco,"HpCoupleRear");
    loco->Orientation=wagons->Orientation;
    V rearOffset=point(loco,rearLocal)-point(loco,{});
    PhySys::BeamR(loco,vgame(front-rearOffset),wagons->Orientation,false);
    PhySys::AddToVelocity(loco,vgame(speed(wagons)-speed(loco)));
    CmnTrain::SetCouplable(wagons->Id,false);
    need(CmnTrain::CanCouple(loco,wagons)==-8 && CmnTrain::Couple(loco,wagons)==-8 &&
         CmnTrain::BeginCouple(loco,wagons)==-8,"delivered consist rejects all coupling paths");
    CmnTrain::SetCouplable(wagons->Id,true);
    need(CmnTrain::BeginCouple(loco,wagons)==1,"approach before delivery");
    CmnTrain::SetCouplable(wagons->Id,false);
    need(!CmnTrain::IsCoupling(loco),"delivery cancels an already pending approach");
    step(16);
    need(!CmnTrain::Trailer(loco),"late physics sync cannot recapture delivered wagons");
    CmnTrain::SetCouplable(wagons->Id,true);
    need(CmnTrain::Couple(loco,wagons)==1,"return and recouple");step(16*3);
    need(gap(links)<.15,"recoupled train stable");
    for(int i=0;i<20;++i){need(CmnTrain::Uncouple(loco),"repeat uncouple");need(CmnTrain::Couple(loco,wagons)==1,"repeat couple");step(1);}
    need(gap(links)<.15,"20 coupling cycles remain stable");
    // Enter a lane with a bent, coupled two-ship train, including all cargo.
    // Compare motion relative to the head so the lane's forward speed cannot
    // hide an instantaneous sideways snap of the tail.
    auto orientation=[](CObject* o) {
        TrainJoint::M r;
        for(int i=0;i<3;++i)r.axes[i]={o->Orientation.E[0][i],o->Orientation.E[1][i],o->Orientation.E[2][i]};
        return r;
    };
    for(float laneDuration:{6.f,.75f})for(float frameTime:{1.f/16,1.f/60,1.f/144}) {
        PhySys::BeamR(loco,{42348,0,-4346},straight,false);
        for(size_t i=1;i<bodies.size();++i) {
            Matrix r=EulerMatrix({0,(float)(4*(std::min)(i,size_t{5})),0});
            PhySys::BeamR(bodies[i],{0,0,0},r,false);
            const auto& j=links[i-1];
            V frontOffset=point(j.b,j.front)-point(j.b,{});
            PhySys::BeamR(j.b,vgame(point(j.a,j.rear)-frontOffset),r,false);
        }
        for(auto* b:bodies) {
            PhySys::AddToVelocity(b,vgame(-speed(b)));
            Vector spin=PhySys::GetAngularVelocityOS(b);
            PhySys::AddToAngularVelocityOS(b,{-spin.x,-spin.y,-spin.z});
        }
        auto frame=[&] {
            CmnTrain::Sync(loco);PhySys::Update(1,frameTime);
            loco->update_tree();wagons->update_tree();
            for(auto* b:bodies)b->CObject::update(frameTime,0);
        };
        loco->bUsingTradelane=1;
        PhySys::AddToVelocity(loco,{0,0,-2000});
        auto* tail=bodies.back();
        V tailBefore=point(tail,{})-point(loco,{});
        auto angleBefore=orientation(tail);
        frame();
        const double entryStep=((point(tail,{})-point(loco,{}))-tailBefore).length();
        const double entryAngle=TrainJoint::relativeAngle(angleBefore,orientation(tail)).length()*180/3.141592653589793;
        std::printf("Lane entry %.0f fps: tail step %.4f m, turn %.4f deg\n",1/frameTime,entryStep,entryAngle);
        need(entryStep<.15 && entryAngle<.1,"lane entry preserves the curved train pose");
        double maxGap=gap(links),maxStep=0,maxTurn=0;
        for(int i=1;i*frameTime<laneDuration;++i) {
            V previous=point(tail,{})-point(loco,{});auto rotation=orientation(tail);
            frame();
            maxStep=(std::max)(maxStep,((point(tail,{})-point(loco,{}))-previous).length());
            maxTurn=(std::max)(maxTurn,TrainJoint::relativeAngle(rotation,orientation(tail)).length());
            maxGap=(std::max)(maxGap,gap(links));
        }
        double finalAngle=TrainJoint::relativeAngle(orientation(loco),orientation(tail)).length()*180/3.141592653589793;
        std::printf("Lane settle: tail turn %.4f deg/frame, lateral speed %.3f, joint gap %.4f, final angle %.4f deg\n",maxTurn*180/3.141592653589793,maxStep/frameTime,maxGap,finalAngle);
        need(maxTurn<.03 && maxStep/frameTime<250 && maxGap<.2,"lane gently straightens without stretching joints");
        need(laneDuration<1?finalAngle>15:finalAngle<.1,"lane transition unfolds over time");
        loco->bUsingTradelane=0;
        PhySys::AddToVelocity(loco,vgame(-speed(loco)));
        const auto exitRotation=orientation(tail);
        frame();
        need(gap(links)<.2 && speed(tail).length()<1 &&
            TrainJoint::relativeAngle(exitRotation,orientation(tail)).length()<.01,
            "lane exit removes lane speed and preserves even a partially unfolded pose");
    }
    for(auto* gun:guns)delete gun;
    for(auto* pod:pods)delete pod;
    loco->Release();
    auto orphanPoses=parkedPoses();
    for(int i=0;i<32;++i){PhySys::Update(1,1.f/16);wagons->update_tree();}
    need(gap(internal)<.15,"trailer remains a train after locomotive destruction");
    checkParked(orphanPoses);
    auto* replacement=vehicle("train_locomotive.cmp",1003,500);
    V tailPin=point(wagons,anchor(wagons,"HpCoupleFront"));
    PhySys::BeamR(replacement,{0,0,0},wagons->Orientation,false);
    V replacementRear=point(replacement,anchor(replacement,"HpCoupleRear"))-point(replacement,{});
    PhySys::BeamR(replacement,vgame(tailPin-replacementRear+V{0,0,-8}),wagons->Orientation,false);
    need(CmnTrain::BeginCouple(replacement,wagons)==1,"approach may begin after previous locomotive destruction");
    wagons->Release();
    need(!CmnTrain::IsCoupling(replacement),"trailer destruction cancels an active approach");
    for(int i=0;i<16;++i){PhySys::Update(1,1.f/16);replacement->update_tree();}
    need(speed(replacement).length()<.01,"no stale approach controller after trailer destruction");
    replacement->Release();PhySys::Shutdown(1);
    std::puts("PASS: yard models, 40 pods, fixed parking under impulses and collisions, capture limits, towing, immediate parking on detach, recoupling, 20 cycles, locomotive destruction and cleanup");
}
