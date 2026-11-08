#include "common_train.h"
#include "train_joint_math.h"
#include "common_physys_internal.h"
#include "common_archetype.h"
#include "common_csys.h"
#include "common_server.h"
#include "train_yard_bridge.h"
#include "../IVP/ivp_physics/ivp_simulation_unit.h"
#include "../IVP/ivp_utility/ivp_vhash.h"
#include <unordered_map>
#include <memory>
#include <cstring>
#include <map>
#include <array>
#include <set>

namespace CmnTrain {
namespace {
using namespace TrainJoint;
using namespace CmnPhySys;
struct Train;
void releaseSeparated();
std::unordered_map<EngineObject const*,Train*>& registry() {
    static auto* value=new std::unordered_map<EngineObject const*,Train*>;
    return *value;
}
V vec(Vector const& v) {return {v.x,v.y,v.z};}
V vec(IVP_U_Point const& v) {return {v.x,v.y,v.z};}
Vector game(V v) {return {(float)v.x,(float)v.y,(float)v.z};}
M matrix(IVP_U_Matrix3 const& m) {
    M r;
    for(int i=0;i<3;++i)r.axes[i]={m.rows[0].k[i],m.rows[1].k[i],m.rows[2].k[i]};
    return r;
}
const char* model(CObject const* o) {
    if(!o || !o->Archetype || !o->Archetype->DaArchetype.Value)return "";
    const char* p=o->Archetype->DaArchetype.Value;
    const char* name=p;
    for(;*p;++p)if(*p=='/' || *p=='\\')name=p+1;
    return name;
}
bool trailerModel(char const* name) {
    if(_stricmp(name,"train_wagons.cmp")==0)return true;
    if(strlen(name)!=19 || _strnicmp(name,"train_wagons_",13)!=0 ||
       _stricmp(name+15,".cmp")!=0)return false;
    const int count=(name[13]-'0')*10+name[14]-'0';
    return name[13]>='0' && name[13]<='2' && name[14]>='0' && name[14]<='9' && count>=1 && count<=20;
}
std::set<unsigned>& retired() {static auto* ids=new std::set<unsigned>;return *ids;}
bool trainModel(CObject const* o) {
    return _stricmp(model(o),"train_consist.cmp")==0 ||
           _stricmp(model(o),"train_locomotive.cmp")==0 ||
           trailerModel(model(o));
}
std::map<unsigned,unsigned>& connections() {
    static auto* value=new std::map<unsigned,unsigned>;
    return *value;
}
bool anchor(CObject* object,const char* name,V& out) {
    struct HP {unsigned type;Vector p;Matrix r;Vector axis;float min,max;};
    void* arch=DALib::Engine->GetInstanceArchetype((void*)object->EngineInstanceId);
    if(arch==(void*)-1)return false;
    FHardpointKey key;key.Name=name;key.Crc=DACOM_CRC::GetCRC32(name);
    HP hp={};
    bool ok=DALib::Hardpoint->GetHardpoint(arch,&key,&hp)!=0;
    DALib::Engine->ReleaseHandle(arch);
    out=vec(hp.p);return ok;
}
Body read(CObject* o) {
    IVP_Core* c=o->BodyPtr->core;
    Body b;
    IVP_U_Matrix pose;
    o->BodyPtr->get_m_world_f_object_AT(&pose);
    b.rotation=matrix(pose);
    b.position=vec(c->MWorldFCore.vv);
    b.originOffset=vec(pose.vv)-b.position;
    b.inertiaAxes=matrix(c->MWorldFCore);
    b.inverseInertia=vec(c->InvRotInertia);b.inverseMass=c->InvMass;
    if(!(c->Flags&0xc)) {
        b.velocity=vec(c->Speed)+vec(c->SpeedChange);
        b.omega=b.inertiaAxes.mul(vec(c->RotSpeed)+vec(c->RotSpeedChange));
    }
    return b;
}
void velocity(CObject* o,V linear,V angular,bool immediate=false) {
    IVP_Core* c=o->BodyPtr->core;
    // Set the pending velocity, preserving the current PSI's committed values.
    c->SpeedChange=game(linear-vec(c->Speed));
    c->RotSpeedChange=game(matrix(c->MWorldFCore).inv(angular)-vec(c->RotSpeed));
    // Controller callbacks run after IVP's async accumulator flush. Constraints
    // must affect this PSI, like IVP_Controller_Motion's direct speed correction.
    if(immediate)c->commit_speed_changes();
    o->BodyPtr->EnsureInSimulation();
    if(IsDriven(o))
        if(auto* remote=dynamic_cast<CRemotePhysicsController*>(o->GolemController))
            remote->m_Velocity=game(linear);
}
struct Train final:PhySys::Controller {
    std::vector<CObject*> objects;
    std::vector<Joint> joints;
    std::vector<Body> bodies;
    bool initial=true;
    bool parked=false;
    std::map<CObject*,std::array<char,8>> collisionGroups;
    CObject* releaseHead=nullptr;
    CObject* captureTail=nullptr;
    V captureStartPin,captureStagePin,captureEndPin,captureRear;
    IVP_U_Quat captureStartQ{},captureEndQ{};
    double captureTime=0,captureAlignTime=0;
    bool captureReady=false;
    V lastHead;
    std::vector<IVP_U_Quat> laneStart;
    double laneTime=0;
    void setCollisionGroups(char const* shared=nullptr) {
        for(auto const& item:collisionGroups)if(item.first->BodyPtr) {
            auto* c=item.first->BodyPtr->core;
            char const* group=shared?shared:item.second.data();
            for(int i=c->Objects.n_elems-1;i>=0;--i) {
                auto* shape=c->Objects.elems[i];
                shape->unlink_contact_points(true);
                std::memcpy(shape->name,group,8);
                shape->recheck_collision_filter();
            }
        }
    }
    void coupleCollisions(bool enabled) {
        if(enabled) {
            bool trailer=false;
            for(auto* o:objects)trailer|=IsTrailer(o);
            if(!IsLocomotive(objects[0]) || !trailer)return;
        }
        // Separate world ships need the same native collision-group tag while
        // joined, like the parts of a stock CMP. Collision remains on for the
        // surrounding world. Include every shape welded to each wagon core.
        setCollisionGroups(enabled?collisionGroups[objects[0]].data():nullptr);
        if(!enabled)releaseHead=nullptr;
    }
    void parking(bool enabled) {
        if(parked==enabled)return;
        // Solar's bFlag1c=1 produces core type 4 and object movement type 16.
        // Sleeping alone is insufficient: a contact would wake a normal ship.
        // Keep mass/inertia and all welded cargo shapes on their original cores.
        for(auto* object:objects)if(object->BodyPtr) {
            auto* c=object->BodyPtr->core;
            IVP_U_Matrix pose;object->BodyPtr->get_m_world_f_object_AT(&pose);
            FMatrix rotation;
            for(int i=0;i<3;++i)for(int j=0;j<3;++j)rotation.D[i][j]=pose.rows[i].k[j];
            FQuaternion q;Acquire3DMathEngine()->MatrixToQuaternion(q,rotation);
            IVP_U_Quat orientation;orientation.x=q.X;orientation.y=q.Y;orientation.z=q.Z;orientation.w=q.W;
            for(int i=c->Objects.n_elems-1;i>=0;--i)c->Objects.elems[i]->unlink_contact_points(true);
            // Fixed cores cache contacts in a hash table; dynamic cores use the
            // same slot for a single contact. Never reinterpret the old table.
            if((c->Flags&0xc)==4 && c->ObjectHashMap) {
                static_cast<IVP_VHash_Store*>(c->ObjectHashMap)->~IVP_VHash_Store();
                free(c->ObjectHashMap);c->ObjectHashMap=nullptr;
            }
            if(c->Flags&0x30)IVP_Environment_Dequeue_Core(c->Environment,c);
            c->freeze_simulation_core();
            if(enabled) {
                // Remove the wagon from the former train's awake simulation unit.
                // Otherwise waking the locomotive can also wake a fixed wagon.
                IVP_Simulation_Unit_Detach_Core(c->OwningSimUnit,c);
                auto* unit=new IVP_Simulation_Unit;
                unit->State=8;unit->Cores.Add(c);c->OwningSimUnit=unit;
                IVP_Simulation_Unit_Rebuild_Controller_Buckets(unit);
                c->Environment->sim_units_manager->add_sim_unit_to_manager(unit);
            }
            c->Flags=(c->Flags&~0xcu)|(enabled?4u:0u);
            for(int i=c->Objects.n_elems-1;i>=0;--i) {
                auto* shape=c->Objects.elems[i];
                shape->flags=(shape->flags&~0xffu)|(enabled?16u:8u);
                shape->recheck_ov_element_as_moving();
            }
            // Freeze stores the preceding PSI base pose. Preserve the current
            // interpolated pose instead, so detaching at speed never jumps back.
            object->BodyPtr->beam_object_to_new_position(&orientation,&pose.vv,1);
            // Also discard impulses accumulated while fixed before reattachment.
            c->Speed=c->SpeedChange=c->RotSpeed=c->RotSpeedChange=Vector{0,0,0};
        }
        parked=enabled;initial=false;
    }
    void core_is_going_to_be_deleted_event(IVP_Core* core) override {
        for(auto* object:objects)if(object->BodyPtr && object->BodyPtr->core==core){Forget(object);return;}
        Forget(objects[0]);
    }
    IVP_CONTROLLER_PRIORITY get_controller_priority() override {
        // Forces, golem corrections and contact impulses run before the couplings.
        return static_cast<IVP_CONTROLLER_PRIORITY>(50);
    }
    void inherit() {
        if(parked) {
            for(auto* object:objects) {
                auto* c=object->BodyPtr->core;
                c->Speed=c->SpeedChange=c->RotSpeed=c->RotSpeedChange=Vector{0,0,0};
            }
            return;
        }
        Body root=read(objects[0]);
        for(size_t i=1;i<objects.size();++i) {
            Body child=read(objects[i]);
            velocity(objects[i],root.velocity+root.omega.cross(child.position-root.position),root.omega);
        }
        initial=false;lastHead=root.position;
    }
    void align() {
        // Large position corrections (jumps) relocate the whole formation.
        Body root=read(objects[0]);
        IVP_U_Matrix pose;objects[0]->BodyPtr->get_m_world_f_object_AT(&pose);
        FMatrix rotation;
        for(int i=0;i<3;++i)for(int j=0;j<3;++j)rotation.D[i][j]=pose.rows[i].k[j];
        FQuaternion q;Acquire3DMathEngine()->MatrixToQuaternion(q,rotation);
        IVP_U_Quat iq;iq.x=q.X;iq.y=q.Y;iq.z=q.Z;iq.w=q.W;
        V parent=vec(pose.vv);
        for(size_t i=0;i<joints.size();++i) {
            V p=parent+root.rotation.mul(joints[i].anchorA-joints[i].anchorB);
            IVP_U_Point ip;ip.set((float)p.x,(float)p.y,(float)p.z);
            objects[i+1]->BodyPtr->beam_object_to_new_position(&iq,&ip,1);
            objects[i+1]->WorldPosition=game(p);
            std::memcpy(&objects[i+1]->Orientation,&rotation,sizeof(rotation));
            PhySys_UpdateJointedChildren(objects[i+1]->EngineInstanceId,objects[i+1]);
            velocity(objects[i+1],root.velocity+root.omega.cross(read(objects[i+1]).position-root.position),root.omega,true);
            parent=p;
        }
    }
    void guideLane(double dt) {
        if(!(dt>0 && dt<=.2))return;
        const Body root=read(objects[0]);
        IVP_U_Matrix headPose;objects[0]->BodyPtr->get_m_world_f_object_AT(&headPose);
        IVP_U_Quat headQ;headQ.set_from_matrix(&headPose);
        if(laneStart.empty()) {
            // Preserve the live bend on entry. Store rotations in the head's
            // frame so lane translation and steering cannot change the blend.
            laneTime=0;laneStart.resize(joints.size());
            for(size_t i=0;i<joints.size();++i) {
                IVP_U_Matrix pose;objects[i+1]->BodyPtr->get_m_world_f_object_AT(&pose);
                IVP_U_Quat q;q.set_from_matrix(&pose);
                laneStart[i].set_inv_mult_quat(&headQ,&q);
            }
        }
        const IVP_U_Quat identity={0,0,0,1};
        V parent=vec(headPose.vv),parentOmega=root.omega;
        V parentVelocity=root.pointVelocity(root.originOffset);
        M parentRotation=root.rotation;
        for(size_t i=0;i<joints.size();++i) {
            // A short wave from head to tail; zero blend speed at both ends.
            const double t=clamp((laneTime-.06*i)/4.0,0,1);
            const double blend=t*t*t*(10+t*(-15+6*t));
            const double rate=30*t*t*(1-t)*(1-t)/4.0;
            IVP_U_Quat relative,q;
            relative.set_interpolate_quat(&laneStart[i],&identity,(float)blend);
            q.set_mult_quat(&headQ,&relative);
            IVP_U_Matrix3 rotation,start;
            q.set_matrix(&rotation);laneStart[i].set_matrix(&start);
            const M next=matrix(rotation);
            const V angular=root.omega+root.rotation.mul(relativeAngle(matrix(start),M{}))*rate;
            const V rear=parentRotation.mul(joints[i].anchorA),front=next.mul(joints[i].anchorB);
            const V p=parent+rear-front;
            const V originVelocity=parentVelocity+parentOmega.cross(rear)-angular.cross(front);
            auto* wagon=objects[i+1];
            IVP_U_Point ip;ip.set((float)p.x,(float)p.y,(float)p.z);
            wagon->BodyPtr->beam_object_to_new_position(&q,&ip,1);
            wagon->WorldPosition=game(p);
            for(int row=0;row<3;++row)for(int col=0;col<3;++col)
                wagon->Orientation.E[row][col]=rotation.rows[row].k[col];
            PhySys_UpdateJointedChildren(wagon->EngineInstanceId,wagon);
            // Match anchor velocities, including the unfolding motion, so IVP
            // interpolation keeps the pins together between guided poses.
            velocity(wagon,originVelocity-angular.cross(read(wagon).originOffset),angular,true);
            parent=p;parentRotation=next;parentOmega=angular;parentVelocity=originVelocity;
        }
        laneTime+=dt;
    }
    void do_simulation_controller(IVP_Event_Sim* event,IVP_U_Vector<IVP_Core>*) override {
        releaseSeparated();
        if(initial)inherit();
        Body head=read(objects[0]);
        if(captureTail) {
            auto peer=registry().find(captureTail);
            auto* loco=static_cast<CShip*>(objects[0]);
            if(peer==registry().end() || captureTail->PhysicsSystemId!=loco->PhysicsSystemId ||
               loco->is_using_tradelane() || loco->is_cruise_active() || loco->is_launching()) {
                captureTail=nullptr;captureReady=false;return;
            }
            const double dt=event->delta_time;
            if(!(dt>0 && dt<=.2))return;
            captureTime+=dt;
            auto ease=[](double t){t=clamp(t,0,1);return t*t*t*(10+t*(-15+6*t));};
            const double turn=ease(captureTime/captureAlignTime);
            const double close=ease((captureTime-captureAlignTime)/3.5);
            IVP_U_Quat q;q.set_interpolate_quat(&captureStartQ,&captureEndQ,(float)turn);
            IVP_U_Matrix3 rotation;q.set_matrix(&rotation);M next=matrix(rotation);
            V pin=captureTime<captureAlignTime ?
                captureStartPin+(captureStagePin-captureStartPin)*turn :
                captureStagePin+(captureEndPin-captureStagePin)*close;
            V origin=pin-next.mul(captureRear);
            // Advance by velocity so IVP keeps render interpolation. No per-frame
            // teleport: both the turn and the final approach ease to zero speed.
            V offset=next.mul(head.rotation.inv(head.originOffset));
            V linear=(origin-offset-head.position)*(1/dt);
            V angular=relativeAngle(head.rotation,next)*(1/dt);
            velocity(objects[0],linear,angular,true);
            // Decide seating by the actual pin/rotation error, not the velocity
            // used to correct it. At large world coordinates the float pose's
            // sub-millimetre noise is amplified by interpolation and 1/dt; at
            // 144 fps the old .03 m/s test could wait forever at a seated pin.
            const V actualPin=head.position+head.originOffset+head.rotation.mul(captureRear);
            captureReady=captureTime>=captureAlignTime+3.5 &&
                (actualPin-captureEndPin).length()<.02 &&
                relativeAngle(head.rotation,next).length()<.002 && linear.length()<.25;
            lastHead=head.position;return;
        }
        const bool lane=(objects[0]->ObjectClass&CObject::ClassShip)==CObject::ClassShip &&
                         static_cast<CShip*>(objects[0])->is_using_tradelane();
        const bool correction=(head.position-lastHead).length()>100+head.velocity.length()*event->delta_time*3;
        lastHead=head.position;
        if(lane) {guideLane(event->delta_time);return;}
        if(!laneStart.empty()) {
            laneStart.clear();laneTime=0;
            // Scripted travel can drop the head from lane speed to normal
            // flight in one step. Transfer that speed change to the wagons,
            // preserving their current bend instead of a high-speed recoil.
            inherit();
        }
        if(correction && !IsTrailer(objects[0])) {align();return;}
        for(size_t i=0;i<objects.size();++i)bodies[i]=read(objects[i]);
        auto* ship=static_cast<CShip*>(objects[0]);
        const auto* engine=CEEngine::cast(ship->EquipManager.FindFirst(EquipTypeEngine));
        if(engine && engine->IsCruiseEngaged()) {
            const double speed=clamp((bodies[0].velocity.length()-80)/170,0,1);
            bodies[0].cruiseStability=speed*speed*(3-2*speed);
        }
        // Engine kill means coasting. Otherwise damp wagon sideslip, and brake
        // their longitudinal overspeed against the locomotive throttle command.
        // No forward thrust is applied to any wagon.
        if(!IsTrailer(objects[0]) && (!engine || engine->IsActive())) {
            double target=0,brake=0;
            if(engine && engine->IsControllerEnabled()) {
                target=ship->get_speed(ship->Throttle,engine->IsCruiseEngaged()?ThrustEquipCruise:ThrustEquipEngine);
                brake=clamp(objects[0]->BodyPtr->core->SpeedDamp,0,8);
                bodies[0].braking=std::abs(ship->Throttle)<1e-3;
            }
            const double lateral=std::abs(target)<1e-3?(std::max)(2.0,brake):2.0;
            for(size_t i=1;i<bodies.size();++i)
                dampWagon(bodies[i],event->delta_time,lateral,brake,target,1.5+4.5*tailWeight((int)i,(int)joints.size()));
        }
        // Remote head pose belongs to its existing remote-physics controller.
        if(objects[0]->GolemController) {bodies[0].inverseMass=0;bodies[0].inverseInertia={};}
        if(dynamic_cast<CRemotePhysicsController*>(objects[0]->GolemController)) {
            bodies[0].endPose=true;
            bodies[0].velocity={};bodies[0].omega={};
        }
        solve(bodies.data(),joints.data(),(int)joints.size(),event->delta_time,!IsTrailer(objects[0]));
        for(size_t i=0;i<objects.size();++i) {
            if(i==0 && objects[0]->GolemController)continue;
            velocity(objects[i],bodies[i].velocity,bodies[i].omega,true);
        }
    }
};
void releaseSeparated() {
    for(auto const& entry:registry()) {
        auto* t=entry.second;
        if(entry.first!=t->objects[0] || !t->releaseHead)continue;
        auto* head=t->releaseHead;
        auto approaching=registry().find(head);
        if(approaching!=registry().end() && approaching->second->captureTail==t->objects[0])continue;
        bool clear=registry().find(head)==registry().end();
        if(!clear) {
            V a,b;
            clear=!head->BodyPtr || head->PhysicsSystemId!=t->objects[0]->PhysicsSystemId;
            if(!clear && anchor(head,"HpCoupleRear",a) && anchor(t->objects[0],"HpCoupleFront",b)) {
                Body x=read(head),y=read(t->objects[0]);
                clear=(x.position+x.originOffset+x.rotation.mul(a)-y.position-y.originOffset-y.rotation.mul(b)).length()>=TrainYard::SpawnPinGap;
            }
        }
        // Closed coupling pins overlap geometrically. Only this pair remains
        // excluded until it has physically separated; all other hulls stay solid.
        if(clear)t->coupleCollisions(false);
    }
}
void collect(CObject* root,long instance,std::vector<CObject*>& wagons) {
    for(long child=PhySys_RelatedInstance(instance,1,-1);child!=-1;child=PhySys_RelatedInstance(instance,1,child)) {
        CObject* object=PhySys_InstanceObject(child);
        if(object && object!=root && IsWagon(object))wagons.push_back(object);
        collect(root,child,wagons);
    }
}
bool ship(CObject const* o) {return o && o->ObjectClass==CObject::ClassShip;}
Train* create(std::vector<CObject*> const& objects,bool inherit,
              std::map<CObject*,std::array<char,8>> const* groups=nullptr) {
    if(objects.empty() || objects.size()>21)return nullptr;
    std::unique_ptr<Train> t(new Train);
    t->objects=objects;t->bodies.resize(objects.size());t->initial=inherit;
    for(size_t i=0;i<objects.size();++i) {
        if(!objects[i]->BodyPtr)return nullptr;
        if(i==0)continue;
        Joint j;j.a=(int)i-1;j.b=(int)i;
        if(!anchor(objects[i-1],"HpCoupleRear",j.anchorA) ||
           !anchor(objects[i],"HpCoupleFront",j.anchorB))return nullptr;
        t->joints.push_back(j);
    }
    t->lastHead=read(objects[0]).position;
    if(IsLocomotive(objects[0]) || IsTrailer(objects[0])) {
        std::array<char,8> group={};
        for(auto* o:objects) {
            if(o->ObjectClass==CObject::ClassShip)std::memcpy(group.data(),o->BodyPtr->name,8);
            auto it=groups?groups->find(o):t->collisionGroups.end();
            t->collisionGroups[o]=groups && it!=groups->end()?it->second:group;
        }
    }
    for(CObject* o:objects)registry()[o]=t.get();
    t->coupleCollisions(true);
    if(IsTrailer(objects[0]))t->parking(true);
    else {
        for(size_t i=0;i+1<objects.size();++i)t->Cores.Add(objects[i]->BodyPtr->core);
        PhySys::Controller::Register(t.get(),objects.back());
    }
    if(IsLocomotive(objects[0]))static_cast<CShip*>(objects[0])->cache_physical_props();
    return t.release();
}
void erase(Train* t,bool restoreGroups=true) {
    if(restoreGroups)t->coupleCollisions(false);
    t->parking(false);
    for(CObject* member:t->objects)registry().erase(member);
    delete t;
}
void join(Train* a,Train* b) {
    auto* head=a->objects[0];auto* trailer=b->objects[0];
    V rear,front;
    const bool capture=anchor(head,"HpCoupleRear",rear) && anchor(trailer,"HpCoupleFront",front);
    const Body target=read(trailer);
    IVP_U_Matrix pose;trailer->BodyPtr->get_m_world_f_object_AT(&pose);
    std::vector<CObject*> members=a->objects;
    members.insert(members.end(),b->objects.begin(),b->objects.end());
    auto groups=a->collisionGroups;groups.insert(b->collisionGroups.begin(),b->collisionGroups.end());
    erase(a,false);erase(b,false);
    if(auto* joined=create(members,false,&groups))if(capture) {
        // Capture is positional: the player need not align pitch, yaw or roll.
        // Seat only the locomotive on the first wagon, after suppressing pair
        // collisions. Never feed a large angular mismatch into the whole chain.
        Matrix rotation;
        for(int i=0;i<3;++i)for(int j=0;j<3;++j)rotation.E[i][j]=pose.rows[i].k[j];
        PhySys::BeamR(head,game(vec(pose.vv)+target.rotation.mul(front-rear)),rotation,false);
        const Body seated=read(head);
        velocity(head,target.pointVelocity(seated.position-target.position),target.omega,true);
        joined->lastHead=seated.position;
        static_cast<CShip*>(head)->cache_physical_props();
    }
}
void split(Train* t) {
    std::vector<CObject*> a,b;
    bool tail=false;
    for(auto* o:t->objects) {
        if(IsTrailer(o))tail=true;
        (tail?b:a).push_back(o);
    }
    auto groups=t->collisionGroups;
    erase(t,false);create(a,false,&groups);
    if(auto* tail=create(b,false,&groups))tail->releaseHead=a[0];
}
}
bool IsLocomotive(CObject const* o) {return ship(o) && _stricmp(model(o),"train_locomotive.cmp")==0;}
bool IsTrailer(CObject const* o) {return ship(o) && trailerModel(model(o));}
void SetCouplable(unsigned id,bool enabled) {
    if(enabled) {retired().erase(id);return;}
    retired().insert(id);
    // A previously requested approach must not capture a newly delivered train.
    for(auto const& entry:registry()) {
        auto* t=entry.second;
        if(t->captureTail && static_cast<CShip*>(t->captureTail)->Id==id)
            CancelCoupling(t->objects[0]);
    }
}
bool IsDriven(CObject const* o) {
    auto it=registry().find(o);
    return IsTrailer(o) && it!=registry().end() && it->second->objects[0]!=o;
}
CObject* Trailer(CObject const* o) {
    auto it=registry().find(o);
    if(!IsLocomotive(o) || it==registry().end())return nullptr;
    for(auto* p:it->second->objects)if(IsTrailer(p))return p;
    return nullptr;
}
int CanCouple(CObject* a,CObject* b,float* distance) {
    if(!IsLocomotive(a) || !IsTrailer(b) || !a->BodyPtr || !b->BodyPtr || !IsMember(a) || !IsMember(b))return -1;
    if(retired().count(static_cast<CShip*>(b)->Id))return -8;
    if(Trailer(a) || IsDriven(b) || IsCoupling(a))return -2;
    for(auto const& item:registry())if(item.second->captureTail==b)return -2;
    if(a->PhysicsSystemId!=b->PhysicsSystemId)return -3;
    auto* locomotive=static_cast<CShip*>(a);
    if(locomotive->is_using_tradelane() || locomotive->is_cruise_active() || locomotive->is_launching())return -7;
    V localA,localB;
    if(!anchor(a,"HpCoupleRear",localA) || !anchor(b,"HpCoupleFront",localB))return -1;
    Body x=read(a),y=read(b);
    V ra=x.rotation.mul(localA)+x.originOffset,rb=y.rotation.mul(localB)+y.originOffset;
    double gap=(y.position+rb-x.position-ra).length();
    if(distance)*distance=(float)gap;
    if(gap>TrainYard::CaptureDistance)return -4;
    if((x.pointVelocity(ra)-y.pointVelocity(rb)).length()>2)return -5;
    return 1;
}
void Sync(CObject* o) {
    releaseSeparated();
    if(!IsLocomotive(o) || Trailer(o))return;
    auto active=registry().find(o);
    if(active!=registry().end() && active->second->captureTail && active->second->captureReady) {
        auto* tail=active->second->captureTail;
        active->second->captureTail=nullptr;active->second->captureReady=false;
        const int result=Couple(o,tail);
        // A late contact/impulse can fail Couple's final speed or distance
        // check. Keep the approach pending so the next PSI can settle it;
        // never silently leave two separate ships after reporting arrival.
        if(result==-4 || result==-5)active->second->captureTail=tail;
        return;
    }
    auto link=connections().find(static_cast<CShip*>(o)->Id);
    if(link==connections().end())return;
    auto a=registry().find(o);if(a==registry().end())return;
    for(auto const& item:registry()) {
        auto* b=const_cast<CObject*>(static_cast<CObject const*>(item.first));
        if(IsTrailer(b) && static_cast<CShip*>(b)->Id==link->second &&
           b->PhysicsSystemId==o->PhysicsSystemId && !IsDriven(b)) {
            join(a->second,item.second);return;
        }
    }
}
int Couple(CObject* a,CObject* b) {
    int result=CanCouple(a,b);if(result!=1)return result;
    connections()[static_cast<CShip*>(a)->Id]=static_cast<CShip*>(b)->Id;
    join(registry()[a],registry()[b]);
    return 1;
}
bool RestoreCoupling(CObject* a,CObject* b) {
    if(!IsLocomotive(a) || !IsTrailer(b) || !a->BodyPtr || !b->BodyPtr ||
       !IsMember(a) || !IsMember(b) || Trailer(a) || IsDriven(b) || IsCoupling(a) ||
       a->PhysicsSystemId!=b->PhysicsSystemId || retired().count(static_cast<CShip*>(b)->Id))return false;
    V rear,front;
    if(!anchor(a,"HpCoupleRear",rear) || !anchor(b,"HpCoupleFront",front))return false;
    IVP_U_Matrix pose;a->BodyPtr->get_m_world_f_object_AT(&pose);
    PhySys::BeamR(b,game(vec(pose.vv)+matrix(pose).mul(rear-front)),a->Orientation,false);
    connections()[static_cast<CShip*>(a)->Id]=static_cast<CShip*>(b)->Id;
    join(registry()[a],registry()[b]);
    return true;
}
int BeginCouple(CObject* a,CObject* b) {
    const int result=CanCouple(a,b);if(result!=1)return result;
    auto* t=registry()[a];auto* tail=registry()[b];
    V front;anchor(a,"HpCoupleRear",t->captureRear);anchor(b,"HpCoupleFront",front);
    IVP_U_Matrix start,end;
    a->BodyPtr->get_m_world_f_object_AT(&start);b->BodyPtr->get_m_world_f_object_AT(&end);
    t->captureStartQ.set_from_matrix(&start);t->captureEndQ.set_from_matrix(&end);
    t->captureStartPin=vec(start.vv)+matrix(start).mul(t->captureRear);
    t->captureEndPin=vec(end.vv)+matrix(end).mul(front);
    t->captureStagePin=t->captureEndPin-matrix(end).axes[2]*12;
    double angle=relativeAngle(matrix(start),matrix(end)).length();
    // Maximum eased angular speed is about 30 degrees/s; translation has its
    // own allowance. The last 12 m always take 3.5 s, with a soft stop.
    t->captureAlignTime=(std::max)(2.0,(std::max)(angle*1.875/.5235987756,
        (t->captureStagePin-t->captureStartPin).length()*1.875/6));
    t->captureTime=0;t->captureReady=false;t->captureTail=b;
    tail->releaseHead=a;tail->setCollisionGroups(t->collisionGroups[a].data());
    a->BodyPtr->EnsureInSimulation();return 1;
}
bool IsCoupling(CObject const* o) {
    auto it=registry().find(o);return it!=registry().end() && it->second->objects[0]==o && it->second->captureTail;
}
bool CancelCoupling(CObject* o) {
    if(!IsCoupling(o))return false;
    auto* t=registry()[o];t->captureTail=nullptr;t->captureReady=false;
    velocity(o,{}, {},true);releaseSeparated();return true;
}
bool Uncouple(CObject* o) {
    if(!IsLocomotive(o) || !Trailer(o))return false;
    unsigned id=static_cast<CShip*>(o)->Id;
    connections().erase(id);
    // Single-player client and server physics have separate copies in this DLL.
    std::vector<Train*> copies;
    for(auto const& item:registry())if(IsLocomotive(static_cast<CObject const*>(item.first)) &&
        static_cast<CShip const*>(item.first)->Id==id && Trailer(static_cast<CObject const*>(item.first)))
        copies.push_back(item.second);
    for(auto* t:copies)split(t);
    return true;
}
bool Bounds(CObject const* o,float& radius,Vector& center) {
    if(!IsLocomotive(o))return false;
    auto it=registry().find(o);if(it==registry().end())return false;
    center=o->WorldPosition;radius=0;
    for(auto* p:it->second->objects)if(p->BodyPtr)
        radius=(std::max)(radius,(float)((vec(p->WorldPosition)-vec(center)).length()+p->BodyPtr->get_upper_limit_radius()));
    return true;
}
bool IsWagon(CObject const* o) {
    if(!trainModel(o) || o->EngineInstanceId==-1)return false;
    FEngineName name;DALib::Engine->GetInstanceName(&name,(void*)o->EngineInstanceId);
    if(!name.Text || strlen(name.Text)!=12 || _strnicmp(name.Text,"TrainWagon",10)!=0)return false;
    const int number=(name.Text[10]-'0')*10+name.Text[11]-'0';
    return name.Text[10]>='0' && name.Text[10]<='9' && name.Text[11]>='0' && name.Text[11]<='9' && number>=1 && number<=20;
}
CObject* AttachmentOwner(CObject* requestedParent,CObject* child) {
    if(!trainModel(requestedParent) || !child || child->EngineInstanceId==-1)return requestedParent;
    // Equipment is owned by the ship, but its collision belongs to the wagon
    // containing the mounting hardpoint. Also works while ReMake builds the
    // instance tree, before the train controller is registered.
    for(void* p=DALib::Engine->GetInstanceParent((void*)child->EngineInstanceId);
        p!=(void*)-1;p=DALib::Engine->GetInstanceParent(p)) {
        auto* owner=static_cast<CObject*>(DALib::Engine->GetInstanceUserData(p));
        if(owner==requestedParent)break;
        if(IsWagon(owner) && owner->BodyPtr)return owner;
    }
    return requestedParent;
}
void ChildParms(CObject* object,PhySys::CreateParms& parms) {
    if(!IsWagon(object))return;
    parms.Mass=250;
    parms.bHasInertia=0;
    // The head supplies the game's flight drag; avoid multiplying it by wagon count.
    parms.LinearDamping=0;
    parms.AngularDamping[0]=parms.AngularDamping[1]=parms.AngularDamping[2]=.1f;
}
bool IsMember(CObject const* o) {return registry().find(o)!=registry().end();}
bool IsHead(CObject const* o) {
    auto it=registry().find(o);
    return it!=registry().end() && it->second->objects[0]==o;
}
float SteeringRadius(CObject const* object,float fallback) {
    // The articulated tail belongs in collision/selection bounds. A spline's
    // steering lookahead follows the locomotive, not a 900 m enclosing sphere:
    // extrapolating that far beyond a short docking spline can point astern.
    if(IsHead(object) && object->BodyPtr)return object->BodyPtr->get_upper_limit_radius();
    return fallback;
}
bool KeepPose(EngineObject const* o) {
    auto it=registry().find(o);
    return it!=registry().end() && it->second->objects[0]!=o;
}
void Prepare(CObject* o) {
    if(trainModel(o) && !o->BodyPtr)DALib::Engine->UpdateInstance((void*)o->EngineInstanceId,0,nullptr);
}
void Forget(CObject* o) {
    auto it=registry().find(o);
    if(it==registry().end())return;
    Train* t=it->second;
    for(auto const& entry:registry())if(entry.first==entry.second->objects[0] && entry.second->captureTail) {
        if(entry.second==t || std::find(t->objects.begin(),t->objects.end(),entry.second->captureTail)!=t->objects.end())
            CancelCoupling(entry.second->objects[0]);
    }
    std::vector<std::vector<CObject*>> groups;
    size_t removed=0;
    for(auto* member:t->objects) {
        if(ship(member))groups.emplace_back();
        groups.back().push_back(member);
        if(member==o)removed=groups.size()-1;
    }
    if(IsLocomotive(t->objects[0]))connections().erase(static_cast<CShip*>(t->objects[0])->Id);
    erase(t);
    releaseSeparated();
    // The other world object survives destruction/unloading of its partner.
    for(size_t i=0;i<groups.size();++i)if(i!=removed)create(groups[i],false);
}
void Build(CObject* root) {
    if(!trainModel(root) || root->ObjectClass!=CObject::ClassShip || !root->BodyPtr || IsMember(root))return;
    std::vector<CObject*> objects={root};
    collect(root,root->EngineInstanceId,objects);
    if(objects.size()<2 && !IsLocomotive(root))return;
    create(objects,true);
}
void InheritVelocity(CObject* root) {
    auto it=registry().find(root);
    if(it!=registry().end() && it->second->objects[0]==root)it->second->inherit();
}
}
