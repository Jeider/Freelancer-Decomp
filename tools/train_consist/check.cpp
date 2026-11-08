// Exercise the real EngBase CMP loader and Common/IVP bodies without a renderer.
#include "../../src/Common/common_physys_internal.h"
#include "common_archetype.h"
#include "common_cequip.h"
#include "common_goods.h"
#include "../../src/Common/train_joint_math.h"
#include <cstdio>
#include <cstdlib>
#include <cmath>
#include <chrono>
#include <set>
#include <dbghelp.h>
#include "check_dock.h"
#pragma comment(lib,"dbghelp.lib")
using TrainJoint::V;
static void need(bool ok,const char* message) {if(!ok){std::fprintf(stderr,"FAIL: %s\n",message);std::exit(1);}}
static LONG WINAPI fault(EXCEPTION_POINTERS* e) {
    HMODULE module=nullptr;char name[MAX_PATH]={};
    GetModuleHandleExA(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS|GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
        reinterpret_cast<LPCSTR>(e->ExceptionRecord->ExceptionAddress),&module);
    GetModuleFileNameA(module,name,MAX_PATH);
    std::fprintf(stderr,"Exception %08lx in %s + %zx accessing %p\n",e->ExceptionRecord->ExceptionCode,name,
        reinterpret_cast<uintptr_t>(e->ExceptionRecord->ExceptionAddress)-reinterpret_cast<uintptr_t>(module),
        reinterpret_cast<void*>(e->ExceptionRecord->ExceptionInformation[1]));
    SymInitialize(GetCurrentProcess(),nullptr,TRUE);
    char buffer[sizeof(SYMBOL_INFO)+512]={};auto* symbol=reinterpret_cast<SYMBOL_INFO*>(buffer);
    symbol->SizeOfStruct=sizeof(SYMBOL_INFO);symbol->MaxNameLen=511;DWORD64 displacement=0;
    if(SymFromAddr(GetCurrentProcess(),reinterpret_cast<DWORD64>(e->ExceptionRecord->ExceptionAddress),&displacement,symbol))
        std::fprintf(stderr,"Symbol: %s + %llu\n",symbol->Name,displacement);
    for(unsigned i=0;i<32;++i) {
        DWORD address=reinterpret_cast<DWORD*>(e->ContextRecord->Esp)[i];
        if(SymFromAddr(GetCurrentProcess(),address,&displacement,symbol))
            std::fprintf(stderr,"Stack[%u]: %s + %llu\n",i,symbol->Name,displacement);
    }
    return EXCEPTION_EXECUTE_HANDLER;
}
static CObject* find(long parent,const char* name) {
    for(void* p=DALib::Engine->GetRelatedInstance((void*)parent,1,(void*)-1);p!=(void*)-1;
        p=DALib::Engine->GetRelatedInstance((void*)parent,1,p)) {
        FEngineName n;DALib::Engine->GetInstanceName(&n,p);
        if(n.Text && _stricmp(n.Text,name)==0)return static_cast<CObject*>(DALib::Engine->GetInstanceUserData(p));
        if(auto* r=find((long)p,name))return r;
    }
    return nullptr;
}
static V point(CObject* o,V p) {
    const Matrix& r=o->Orientation;
    return {o->WorldPosition.x+r.E[0][0]*p.x+r.E[0][1]*p.y+r.E[0][2]*p.z,
            o->WorldPosition.y+r.E[1][0]*p.x+r.E[1][1]*p.y+r.E[1][2]*p.z,
            o->WorldPosition.z+r.E[2][0]*p.x+r.E[2][1]*p.y+r.E[2][2]*p.z};
}
static V anchor(CObject* object,const char* name) {
    struct HP {unsigned type;Vector p;Matrix r;Vector axis;float min,max;};
    void* arch=DALib::Engine->GetInstanceArchetype((void*)object->EngineInstanceId);
    FHardpointKey key;key.Name=name;key.Crc=DACOM_CRC::GetCRC32(name);
    HP hp={};need(DALib::Hardpoint->GetHardpoint(arch,&key,&hp)!=0,"coupling hardpoint exists");
    DALib::Engine->ReleaseHandle(arch);return {hp.p.x,hp.p.y,hp.p.z};
}
struct Coupling {CObject* a;CObject* b;V front,rear;};
static double gap(const std::vector<Coupling>& links) {
    double g=0;
    for(const auto& j:links)g=(std::max)(g,(point(j.a,j.rear)-point(j.b,j.front)).length());
    return g;
}
static Vector vgame(V v) {return {(float)v.x,(float)v.y,(float)v.z};}
static void ray(CObject* head,CObject* wagon) {
    PhySys::RayHit hits[8];
    Vector a=vgame(point(wagon,{4.5,35,21})),b=vgame(point(wagon,{4.5,-35,21}));
    need(PhySys::FindRayIntersect(wagon,a,b,hits,8)>0,"ray hits moving wagon rail");
    need(PhySys::FindRayIntersect(head,a,b,hits,8)==0,"head collision does not contain wagons");
    a=vgame(point(wagon,{0,35,21}));b=vgame(point(wagon,{0,-35,21}));
    need(PhySys::FindRayIntersect(wagon,a,b,hits,8)==0,"wagon central opening remains empty");
}
int main(int argc,char** argv) {
    setvbuf(stdout,nullptr,_IONBF,0);SetUnhandledExceptionFilter(fault);
    SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
    for(double target:{-80.,0.,20.,80.})for(double speed:{-100.,-10.,0.,10.,100.}) {
        TrainJoint::Body b;b.velocity={10,3,-speed};b.omega={1,2,3};
        const double before=b.velocity.dot(b.velocity);
        TrainJoint::dampWagon(b,1./16,2,6,target);
        need(b.velocity.dot(b.velocity)<=before+1e-9,"wagon braking never creates linear energy");
        need(std::abs(b.velocity.z)<=std::abs(speed)+1e-9 && b.velocity.z*(-speed)>=0,"brakes cannot propel or reverse a wagon");
    }
    need(argc==4,"model directory, wagon count and normal/overload arguments");
    const int count=std::atoi(argv[2]);need(count>=1 && count<=20,"wagon count 1..20");
    const bool overload=std::strcmp(argv[3],"overload")==0;
    const bool upright=std::strcmp(argv[3],"upright")==0;
    const bool remote=std::strcmp(argv[3],"remote")==0;
    const bool handling=std::strcmp(argv[3],"handling")==0;
    const bool cruise=std::strcmp(argv[3],"cruise")==0;
    const bool docking=std::strcmp(argv[3],"docking")==0;
    const bool tail=std::strcmp(argv[3],"tail")==0 || cruise;
    if(cruise) {
        // FL_MOD/DATA/Constants.ini, rather than the DLL's retail defaults.
        EngineEquipConsts::CRUISING_SPEED=600;
        EngineEquipConsts::CRUISE_ACCEL_TIME=10;
        EngineEquipConsts::CRUISE_DRAG=600;
    }
    std::printf("Scenario: %s\n",argv[3]);
    need(DALib::Startup(nullptr,"check_dacom.ini"),"DALib startup");
    need(DALib::Engine && DALib::Hardpoint,"headless engine/hardpoints");
    DALib::OpenData(argv[1]);need(DALib::Data!=nullptr,"data filesystem");
    PhySys::Startup(1);
    auto* arch=new Archetype::Ship;
    arch->DaArchetype.Value="train_consist.cmp";
    auto* head=static_cast<CShip*>(CObject::Alloc(CObject::ClassShip));
    head->CObject::open(arch);
    need(arch->is_loaded(),"CMP loaded");
    need(arch->create_instance(head)!=-1,"CMP instance");
    std::puts("PASS: native CMP and SUR loaded");
    PhySys::CreateParms parms={};parms.Mass=500;parms.CollisionGroupId=1;parms.Type=2;
    parms.bHasInertia=1;parms.Inertia={600000,600000,600000};
    // CShip::update uses (hull + engine drag) / mass and angular drag / inertia.
    // Overload deliberately removes most engine drag to stress the joints.
    parms.LinearDamping=overload?PhySys::DEFAULT_LINEAR_DAMPING:3001.f/500;
    parms.AngularDamping[0]=parms.AngularDamping[1]=parms.AngularDamping[2]=900000.f/600000;
    strcpy_s(parms.Name,"train1");parms.bEnableCollisions=1;
    PhySys::BuildIVP_Real(head,parms);
    std::vector<CObject*> objects={head};std::vector<Coupling> links;
    std::set<IVP_Core*> cores={head->BodyPtr->core};
    for(int i=1;i<=count;++i) {
        char name[32];sprintf_s(name,"TrainWagon%02d",i);
        auto* wagon=find(head->EngineInstanceId,name);
        need(wagon && wagon->BodyPtr,"every wagon has a body");
        need(cores.insert(wagon->BodyPtr->core).second,"independent IVP cores");
        need(wagon->GolemController==nullptr && wagon->PhysicsControlMode==1,"wagon not welded or golem driven");
        need(std::abs(1/wagon->BodyPtr->core->InvMass-250)<.01,"wagon mass 250");
        links.push_back({objects.back(),wagon,anchor(wagon,"HpCoupleFront"),anchor(objects.back(),"HpCoupleRear")});
        objects.push_back(wagon);
    }
    auto* first=objects[1];auto* last=objects.back();
    std::printf("PASS: %d independent bodies; total bare mass %d; max rest gap %.5f\n",count+1,500+count*250,gap(links));
    need(gap(links)<.001,"rest anchors coincide");
    Vector center;
    need(PhySys::GetRadiusR(head,false,center)>count*40,"ship bounds include the last wagon");
    ray(head,last);
    std::puts("Creating cargo archetype");
    auto* podArch=new Archetype::CargoPod;
    podArch->DaArchetype.Value="pod_grey.3db";
    podArch->HpChild.Value="HpConnect";
    std::vector<CECargoPod*> pods;std::vector<CObject*> cargo;
    for(int i=0;i<count*2;++i) {
        auto* pod=new CECargoPod(head,(unsigned short)(i+1),podArch,false);
        char hp[32];sprintf_s(hp,"HpCargo%02d",i+1);
        need(pod->Connect(hp),"cargo pod connects to wagon");
        auto* body=pod->GetPhysicsOwner();
        need(body && body->BodyPtr && body->BodyPtr->core==objects[1+i/2]->BodyPtr->core,"cargo collision belongs to its wagon");
        pods.push_back(pod);cargo.push_back(body);
    }
    std::printf("PASS: %d physical cargo pods mounted on their own wagons\n",count*2);
    CEEngine* engine=nullptr;
    if(handling || tail || docking) {
        arch->LinearDrag=1;
        auto* engineArch=new Archetype::Engine;
        engineArch->ThrustMultiplier=240000;engineArch->LinearDrag=3000;
        engineArch->PowerDrawFactor=0;engineArch->ReverseFraction=.2f;engineArch->bIndestructible=true;
        engineArch->CruiseChargeTime=cruise?7.f:3.f;engineArch->CruisePowerUsage=0;
        engine=new CEEngine(head,100,engineArch,false);
        need(head->EquipManager.AddNewEquipment(engine) && engine->IsFunctioning(),"actual engine supplies handling test thrust");
    }
    if(docking) {
        DockHandle handle;handle.Object=head;
        arch->SteeringTorqueX=arch->SteeringTorqueY=190000;arch->SteeringTorqueZ=90000;
        arch->AngularDragX=arch->AngularDragY=arch->AngularDragZ=900000;
        head->Steering.EnableController();head->Steering.Activate(true);
        Matrix orientation(.6557591f,-.0813557f,.7505739f,-.00405345f,.9937832f,.1112589f,-.7549593f,-.0760015f,.6513526f);
        PhySys::BeamR(head,{38079.375f,-63.14478f,-9959.2295f},orientation,true);
        auto* manager=head->create_behavior_interface(&handle,0);
        auto* sys=manager->get_sys();
        auto* dock=static_cast<DockBehavior*>(manager->BehaviorDispatchTable[7]);
        need(dock!=nullptr,"real native docking behavior constructed");
        auto& spline=dock->SubObjectC;
        BaseIdea* idea=&spline;
        need(idea->SetContext(&handle,sys,manager),"real spline context");
        ICRSplineSegment segment;
        segment.P0={38562.371f,-8.41818f,-9405.839f};
        segment.P1={38379.301f,7.626945f,-9621.778f};
        segment.P2={38177.301f,125.f,-10138.523f};
        segment.P3={37301.379f,125.f,-11253.332f};
        segment.calculate_arclength();
        spline.Spline=&segment;spline.PersistedT=.8464072f;
        spline.LookaheadScale=13.3244486f;spline.SpeedNorm=segment.get_spline_length();
        spline.MaxSpeed15c=head->get_speed(1,ThrustEquipEngine);
        spline.Move.ArrivalRange=50;spline.Move.StopStyle=2;spline.Move.bKillEngineOffBearing=0;
        const V target={segment.P2.x,segment.P2.y,segment.P2.z};
        const double before=(point(head,{})-target).length();
        bool arrived=false;int steps=0;
        for(;steps<16*90;++steps) {
            sys->SelfTarget.bPosValid=0;
            const int result=idea->Update(1.f/16);
            PhySys::Update(1,1.f/16);head->update_tree();
            if(result==1){arrived=true;break;}
        }
        const double after=(point(head,{})-target).length();
        std::printf("Native final approach from live stuck pose: %.3f -> %.3f m, %.3f s; arrived %d\n",before,after,steps/16.0,arrived);
        // Spline completion is a heading-plane test, not the final 9.6 m lane
        // capture test. DockBehavior proceeds to its final approach after this.
        need(arrived && after<before*.5,"real docking spline exits the stuck approach stage");
        for(auto* pod:pods)delete pod;
        handle.Object=nullptr;
        head->Release();PhySys::Shutdown(1);
        return 0;
    }
    PhySys::AddToVelocity(head,{0,0,-80});
    if(remote)PhySys::RCBegin(head,head->WorldPosition,{0,0,-80},Quaternion{1,0,0,0},{0,0,0});
    double maximum=0,maximumAngle=0,allAngle=0,maxTilt=0,maxHeight=0,settledTilt=0;int worstStep=0;std::vector<double> timings;
    double releaseSpin=0,brakeSpeed=0,kickSpeed=0,minForward=1e9;
    double tailJoint=0,tailFold=0,tailSpin=0,tailSettled=0,cruiseSpeed=0,cruiseHeadSpin=0;
    double cruiseJoint=0,cruiseSpin=0,cruiseLateJoint=0,cruiseLateSpin=0;
    FILE* trace=nullptr;
    if(cruise) {
        fopen_s(&trace,"cruise.csv","w");need(trace!=nullptr,"cruise trace opens");
        std::fputs("time,head_speed,max_joint_deg,max_wagon_spin_deg_s,max_gap\n",trace);
    }
    if(handling) {
        fopen_s(&trace,"handling.csv","w");need(trace!=nullptr,"handling trace opens");
        std::fputs("time,throttle,head_forward,head_speed,head_spin_deg_s,tail_speed,max_gap,kinetic_energy\n",trace);
    }
    for(int step=0;step<16*180;++step) {
        if(tail) {
            const int stop=cruise?170:110;
            head->Throttle=step<16*stop?1.f:0.f;
            if(step>=16*5 && step<16*12)PhySys::AddToAngularVelocityOS(head,{0,.019791667f,0});
            if(step==16*15) {
                PhySys::AddToVelocity(last,{30,0,0});
                PhySys::AddToAngularVelocityOS(last,{0,.5f,0});
            }
            if(step==16*18)need(engine->EngageCruise(true,false),"tail test enters actual charging/cruise controller");
            if(cruise && step>=16*50 && step<16*58)PhySys::AddToAngularVelocityOS(head,{0,.008f,0});
            if(cruise && step>=16*70 && step<16*78)PhySys::AddToAngularVelocityOS(head,{0,-.008f,0});
            if(step==16*stop) {engine->EngageCruise(false,false);head->Throttle=0;}
            engine->Update(1.f/16,0);
            PhySys::SetDamping(head,(float)((engine->IsCruiseEngaged()?engine->GetCruiseDrag():engine->GetLinearDrag())+1)/500,{1.5f,1.5f,1.5f});
        }
        else if(handling) {
            head->Throttle=step<16*45?1.f:0.f;
            if(step>=16*5 && step<16*10)PhySys::AddToAngularVelocityOS(head,{0,.019791667f,0});
        }
        else if(remote) {
            // Real client dead reckoning moves the head by beam, not by core velocity.
            const double t=(std::min)(90.0,(step+1)/16.0);
            const double yaw=.35*std::sin(t*.13),pitch=.20*std::sin(t*.09),roll=.15*std::sin(t*.11);
            const double cy=std::cos(yaw*.5),sy=std::sin(yaw*.5),cx=std::cos(pitch*.5),sx=std::sin(pitch*.5),cz=std::cos(roll*.5),sz=std::sin(roll*.5);
            Quaternion q={(float)(cy*cx*cz+sy*sx*sz),(float)(cy*sx*cz+sy*cx*sz),
                          (float)(sy*cx*cz-cy*sx*sz),(float)(cy*cx*sz-sy*sx*cz)};
            PhySys::RCSet(head,{0,0,(float)(-80*t)},q,(step+1)/16.0);
        }
        else if(step<16*90) {
            // Nominal ge_t_engine_01 force: 240000 / head mass 500 * dt.
            Vector forward={-head->Orientation.E[0][2]*30,-head->Orientation.E[1][2]*30,-head->Orientation.E[2][2]*30};
            PhySys::AddToVelocity(head,forward);
            if(step>16*5)PhySys::AddToAngularVelocityOS(head,{(upright?.020f:.003f)*std::sin(step*.003f),.012f*std::sin(step*.002f),upright?.009f*std::sin(step*.004f):0});
        }
        if(!tail && step==16*(handling?60:100))PhySys::AddToVelocity(last,{30,10,0}); // large impulse at the tail
        auto started=std::chrono::steady_clock::now();
        PhySys::Update(1,1.f/16);
        // Match the render/animation hierarchy refresh that originally overwrote wagons.
        head->update_tree();
        timings.push_back(std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-started).count());
        double g=gap(links);
        if(tail) {
            auto yaw=[](CObject* a,CObject* b) {
                V right={a->Orientation.E[0][0],a->Orientation.E[1][0],a->Orientation.E[2][0]};
                V back={a->Orientation.E[0][2],a->Orientation.E[1][2],a->Orientation.E[2][2]};
                V other={b->Orientation.E[0][2],b->Orientation.E[1][2],b->Orientation.E[2][2]};
                return std::abs(std::atan2(right.dot(other),back.dot(other)))*180/3.14159265;
            };
            for(int i=(std::max)(1,count-4);i<=count;++i)tailJoint=(std::max)(tailJoint,yaw(objects[i-1],objects[i]));
            const double fold=yaw(objects[(std::max)(0,count-5)],last);
            if(cruise) {
                double joint=0,spin=0;
                for(int i=1;i<=count;++i) {
                    joint=(std::max)(joint,yaw(objects[i-1],objects[i]));
                    auto* c=objects[i]->BodyPtr->core;
                    spin=(std::max)(spin,V{c->RotSpeed.x,c->RotSpeed.y,c->RotSpeed.z}.length()*180/3.14159265);
                }
                if(step>=16*40 && step<16*170) {
                    cruiseJoint=(std::max)(cruiseJoint,joint);cruiseSpin=(std::max)(cruiseSpin,spin);
                }
                if(step>=16*130 && step<16*170) {
                    cruiseLateJoint=(std::max)(cruiseLateJoint,joint);cruiseLateSpin=(std::max)(cruiseLateSpin,spin);
                }
                Vector v=PhySys::GetVelocity(head);
                std::fprintf(trace,"%.4f,%.5f,%.5f,%.5f,%.6f\n",step/16.0,V{v.x,v.y,v.z}.length(),joint,spin,g);
            }
            tailFold=(std::max)(tailFold,fold);
            if(step>=16*60 && step<16*110)tailSettled=(std::max)(tailSettled,fold);
            if(step>=16*25 && step<16*110) {
                auto* c=last->BodyPtr->core;V w={c->RotSpeed.x,c->RotSpeed.y,c->RotSpeed.z};
                tailSpin=(std::max)(tailSpin,w.length()*180/3.14159265);
                auto* hc=head->BodyPtr->core;V hw={hc->RotSpeed.x,hc->RotSpeed.y,hc->RotSpeed.z};
                cruiseHeadSpin=(std::max)(cruiseHeadSpin,hw.length()*180/3.14159265);
                Vector v=PhySys::GetVelocity(head);cruiseSpeed=(std::max)(cruiseSpeed,V{v.x,v.y,v.z}.length());
            }
        }
        if(handling) {
            auto* hc=head->BodyPtr->core;
            const V hv={hc->Speed.x,hc->Speed.y,hc->Speed.z},hw={hc->RotSpeed.x,hc->RotSpeed.y,hc->RotSpeed.z};
            const V forward={-head->Orientation.E[0][2],-head->Orientation.E[1][2],-head->Orientation.E[2][2]};
            const double spin=hw.length()*180/3.14159265;
            double speed=0,energy=0;
            for(auto* object:objects) {
                auto* c=object->BodyPtr->core;
                V v={c->Speed.x,c->Speed.y,c->Speed.z};
                speed=(std::max)(speed,v.length());
                energy+=.5*v.dot(v)/c->InvMass;
                energy+=.5*(c->RotSpeed.x*c->RotSpeed.x/c->InvRotInertia.x+
                            c->RotSpeed.y*c->RotSpeed.y/c->InvRotInertia.y+
                            c->RotSpeed.z*c->RotSpeed.z/c->InvRotInertia.z);
            }
            if(step>=16*25 && step<16*45) {releaseSpin=(std::max)(releaseSpin,spin);minForward=(std::min)(minForward,hv.dot(forward));}
            if(step>=16*50 && step<16*55)brakeSpeed=(std::max)(brakeSpeed,speed);
            if(step>=16*65 && step<16*70)kickSpeed=(std::max)(kickSpeed,speed);
            auto* tc=last->BodyPtr->core;V tv={tc->Speed.x,tc->Speed.y,tc->Speed.z};
            std::fprintf(trace,"%.4f,%.2f,%.5f,%.5f,%.5f,%.5f,%.6f,%.4f\n",step/16.0,head->Throttle,hv.dot(forward),hv.length(),spin,tv.length(),g,energy);
        }
        if(g>maximum){maximum=g;worstStep=step;}
        double dot=0;for(int k=0;k<3;++k)dot+=head->Orientation.E[k][2]*first->Orientation.E[k][2];
        maximumAngle=(std::max)(maximumAngle,std::acos(TrainJoint::clamp(dot,-1,1))*180/3.14159265);
        for(const auto& j:links) {
            double cosine=0;for(int k=0;k<3;++k)cosine+=j.a->Orientation.E[k][2]*j.b->Orientation.E[k][2];
            allAngle=(std::max)(allAngle,std::acos(TrainJoint::clamp(cosine,-1,1))*180/3.14159265);
        }
        const V up={head->Orientation.E[0][1],head->Orientation.E[1][1],head->Orientation.E[2][1]};
        const V headCoupling=point(head,links.front().rear);
        for(size_t i=1;i<objects.size();++i) {
            auto* o=objects[i];
            const V wagonUp={o->Orientation.E[0][1],o->Orientation.E[1][1],o->Orientation.E[2][1]};
            const double tilt=std::acos(TrainJoint::clamp(up.dot(wagonUp),-1,1))*180/3.14159265;
            maxTilt=(std::max)(maxTilt,tilt);
            maxHeight=(std::max)(maxHeight,std::abs((point(o,links[i-1].front)-headCoupling).dot(up)));
            if(step>16*170)settledTilt=(std::max)(settledTilt,tilt);
        }
        if(step%480==0)std::printf("step %d gap %.4f pos %.2f %.2f %.2f\n",step,g,last->WorldPosition.x,last->WorldPosition.y,last->WorldPosition.z);
        if(!std::isfinite(g) || g>=3)std::printf("Unstable at step %d, max gap %.6f\n",step,g);
        need(std::isfinite(g) && g<3,"joint separation bounded during IVP flight");
    }
    double mean=0;for(double ms:timings)mean+=ms;mean/=timings.size();
    std::sort(timings.begin(),timings.end());
    std::printf("PASS: 180s / 16Hz; max gap %.5f at step %d, max head/wagon angle %.3f degrees\n",maximum,worstStep,maximumAngle);
    std::printf("Maximum angle across all couplings: %.3f degrees\n",allAngle);
    std::printf("Wagon/head up mismatch: max %.4f deg, settled %.4f deg; max vertical offset %.4f\n",maxTilt,settledTilt,maxHeight);
    std::printf("Physics + hierarchy CPU ms: mean %.4f, p95 %.4f, max %.4f\n",mean,timings[timings.size()*95/100],timings.back());
    if(tail) {
        if(cruise) {
            std::fclose(trace);
            std::printf("Cruise 600: joint %.3f deg, spin %.3f deg/s; settled joint %.3f deg, spin %.3f deg/s\n",cruiseJoint,cruiseSpin,cruiseLateJoint,cruiseLateSpin);
        }
        std::printf("Tail: last-five joint yaw %.3f deg, total fold %.3f deg, settled fold %.3f deg, spin after release %.3f deg/s; cruise speed %.3f\n",
                    tailJoint,tailFold,tailSettled,tailSpin,cruiseSpeed);
        std::printf("Cruise head spin after release: %.3f deg/s\n",cruiseHeadSpin);
        need(cruiseSpeed>150,"actual cruise accelerates the full train");
        if(cruise)need(cruiseSpeed>500 && cruiseLateJoint<2 && cruiseLateSpin<1,"game-speed cruise settles without sustained wagon oscillation");
        else need(tailJoint<18 && tailFold<40 && tailSettled<10 && tailSpin<4,"rear wagons follow without curling or persistent spin");
        head->EquipManager.Clear();engine=nullptr;
    }
    if(handling) {
        std::fclose(trace);
        std::printf("Handling: released steering spin %.4f deg/s, min forward speed %.4f, all-body speed 5s after brake %.4f, after tail kick %.4f\n",releaseSpin,minForward,brakeSpeed,kickSpeed);
        need(releaseSpin<1 && minForward>0,"released steering settles without tail reversing locomotive");
        need(brakeSpeed<1 && kickSpeed<1,"whole train brakes and damps tail impulse");
        auto forwardSpeed=[&]() {
            Vector v=PhySys::GetVelocity(head);
            return -(v.x*head->Orientation.E[0][2]+v.y*head->Orientation.E[1][2]+v.z*head->Orientation.E[2][2]);
        };
        auto drive=[&](float throttle,int seconds) {
            head->Throttle=throttle;
            for(int n=0;n<16*seconds;++n)PhySys::Update(1,1.f/16);
            return forwardSpeed();
        };
        const double full=drive(1,12),partial=drive(.3f,10),reverse=drive(-.5f,12),stopped=drive(0,6);
        std::printf("Throttle control: full %.3f, partial %.3f, reverse %.3f, stop %.3f\n",full,partial,reverse,stopped);
        need(full>50 && full<85 && partial>10 && partial<28 && reverse< -3 && reverse> -12 && std::abs(stopped)<1,
             "full/partial/reverse/stop commands brake without adding wagon thrust");
        drive(1,12);
        engine->Activate(false);
        PhySys::SetDamping(head,1.f/500,{1.5f,1.5f,1.5f}); // CShip::update after engine kill.
        const double coastBefore=forwardSpeed(),coastAfter=drive(0,8);
        std::printf("Engine kill: coast before %.3f, after 8s %.3f\n",coastBefore,coastAfter);
        need(coastAfter>coastBefore*.9,"engine kill preserves coasting instead of braking wagons");
        engine->Activate(true);PhySys::SetDamping(head,3001.f/500,{1.5f,1.5f,1.5f});
        need(std::abs(drive(0,6))<1,"re-enabling stopped engine brakes the train");
        head->EquipManager.Clear();engine=nullptr;
    }
    need(maximum<(overload?1.2:.3),"coupling stretch within scenario tolerance");
    need(maxTilt<6 && settledTilt<.2,"wagons stay upright relative to the locomotive");
    need(maximumAngle>1,"wagons actually articulate");
    if(remote)PhySys::RCEnd(head);
    // The mounted pod now occupies the frame's opening.
    for(int i=0;i<count*2;++i)need(cargo[i]->BodyPtr->core==objects[1+i/2]->BodyPtr->core,"pod remains on articulated wagon");
    std::puts("PASS: cargo collision follows the articulated wagon");
    // Beam through a jump; then rebuild in a new physics system as game transitions do.
    Matrix rotation=head->Orientation;
    PhySys::BeamR(head,{10000,2000,3000},rotation,true);
    std::printf("beam max gap %.5f\n",gap(links));
    PhySys::Update(1,1.f/16);
    need(gap(links)<1,"jump keeps train together");
    PhySys::UnMakePhysicalR(head);
    PhySys::Startup(2);parms.CollisionGroupId=2;
    PhySys::ReMakePhysicalR(head,parms,0);
    for(int i=0;i<count*2;++i)need(cargo[i]->BodyPtr->core==objects[1+i/2]->BodyPtr->core,"cargo stays with wagon after remake");
    for(int i=0;i<160;++i)PhySys::Update(2,1.f/16);
    need(gap(links)<.2,"recreated joints in new system");
    std::puts("PASS: teleport, unmake/remake and 10s in new system");
    head->bUsingTradelane=1;
    PhySys::AddToVelocity(head,{0,0,-2000});
    for(int i=0;i<80;++i)PhySys::Update(2,1.f/16);
    need(gap(links)<.2,"tradelane alignment");
    head->bUsingTradelane=0;
    for(int i=0;i<160;++i)PhySys::Update(2,1.f/16);
    need(gap(links)<.2,"tradelane exit");
    std::puts("PASS: lane mode and return to free flight");
    for(int i=0;i<16*25;++i)PhySys::Update(2,1.f/16);
    auto* impact=CObject::Alloc(CObject::ClassObject);
    impact->WorldPosition=vgame(point(last,{40,2,21}));
    PhySys::CreateParms ball={};ball.Mass=500;ball.CollisionGroupId=2;
    ball.bEnableCollisions=1;strcpy_s(ball.Name,"impact");
    PhySys::BuildIVP_Sphere(impact,3,ball);
    V toward=point(last,{-10,2,21})-point(last,{40,2,21});
    PhySys::AddToVelocity(impact,vgame(toward*(20/toward.length())));
    int contacts=0;double headResponse=0,collisionGap=0;
    for(int i=0;i<16*10;++i) {
        PhySys::Update(2,1.f/16);
        PhySys::CollisionEvent const *begin,*end;PhySys::GetCollisions(2,begin,end);
        contacts+=(int)(end-begin);
        Vector speed=PhySys::GetVelocity(head);
        headResponse=(std::max)(headResponse,std::sqrt(double(speed.x)*speed.x+speed.y*speed.y+speed.z*speed.z));
        collisionGap=(std::max)(collisionGap,gap(links));
    }
    std::printf("Ball impact: contacts %d, head response %.4f, max joint gap %.4f\n",contacts,headResponse,collisionGap);
    need(contacts>0 && headResponse>.01 && collisionGap<3,"actual contact transfers impulse through train");
    impact->Release();
    for(auto* pod:pods)delete pod; // CECargoPod destructor disconnects the physical attachment.
    head->Release();
    PhySys::Shutdown(1);PhySys::Shutdown(2);
    std::puts("PASS: body/controller destruction");
    return 0;
}
