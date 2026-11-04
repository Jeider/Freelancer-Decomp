#include "common_asteroid_avoidance.h"
#include "asteroid_avoidance_math.h"
#include "common_iface.h"
#include "common_cobject.h"
#include "common_physys.h"
#include "common_server_asteroid.h"
#include <algorithm>
#include <map>
#include <vector>

namespace {
struct AvoidanceEntry {
    unsigned system=0;
    AsteroidAvoidance::Memory memory;
    unsigned strafeRockId=0;
    StrafeDir strafe=StrafeNone;
};
std::map<void const*,AvoidanceEntry> avoidanceEntries;

void ClearStrafe(void const* owner, IObjRW* ship) {
    if (!owner) return;
    auto found=avoidanceEntries.find(owner);
    if (found==avoidanceEntries.end()) return;
    AvoidanceEntry& entry=found->second;
    if (ship && entry.strafe!=StrafeNone) {
        StrafeDir current=StrafeNone;
        // Do not cancel a newer manual/AI strafe that replaced ours.
        if (ship->get_strafe_dir(current)!=0 || current==entry.strafe)
            ship->set_strafe_dir(StrafeNone);
    }
    entry.strafeRockId=0;
    entry.strafe=StrafeNone;
}

void UpdateStrafe(void const* owner, IObjRW* ship, Vector const& centre, float shipRadius,
                  std::vector<AsteroidAvoidance::Rock> const& rocks) {
    if (!owner) return;
    AvoidanceEntry& entry=avoidanceEntries[owner];
    AsteroidAvoidance::Rock const* nearest=nullptr;
    double nearestSurface=200.0;
    for (auto const& rock : rocks) {
        if (!AsteroidAvoidance::Finite(rock.position) || !std::isfinite(rock.radius) || rock.radius<=0)
            continue;
        double dx=rock.position.x-centre.x,dy=rock.position.y-centre.y,dz=rock.position.z-centre.z;
        double surface=std::sqrt(dx*dx+dy*dy+dz*dz)-rock.radius-shipRadius;
        if (surface<=nearestSurface) { nearestSurface=surface;nearest=&rock; }
    }
    if (!nearest) { ClearStrafe(owner,ship);return; }

    // Keep the chosen side until this rock is left behind; nearest-rock changes
    // may select a new maneuver, but crossing its centre cannot reverse it.
    if (entry.strafeRockId==nearest->id && entry.strafe!=StrafeNone) return;
    Matrix const& orient=ship->get_orientation();
    double dx=nearest->position.x-centre.x,dy=nearest->position.y-centre.y,dz=nearest->position.z-centre.z;
    double localX=dx*orient.E[0][0]+dy*orient.E[1][0]+dz*orient.E[2][0];
    double localY=dx*orient.E[0][1]+dy*orient.E[1][1]+dz*orient.E[2][1];
    StrafeDir direction;
    if (std::fabs(localX)>=std::fabs(localY)) {
        if (std::fabs(localX)<0.001) direction=(nearest->id&1)?StrafeLeft:StrafeRight;
        else direction=localX>0?StrafeLeft:StrafeRight;
    } else {
        direction=localY>0?StrafeDown:StrafeUp;
    }
    entry.strafeRockId=nearest->id;
    entry.strafe=direction;
    StrafeDir current=StrafeNone;
    if (ship->get_strafe_dir(current)!=0 || current!=direction)
        ship->set_strafe_dir(direction);
}
}

void ResetServerAsteroidAvoidance(void const* owner, IObjRW* ship) {
    if (!owner) return;
    ClearStrafe(owner,ship);
    avoidanceEntries.erase(owner);
}

bool FindServerAsteroidAvoidance(void const* owner, IObjRW* ship, unsigned system, Vector const& goal,
                                 Vector& point, float& scale) {
    if (!ship || !system) { ResetServerAsteroidAvoidance(owner,ship);return false; }
    CObject const* raw=ship->cobject();
    if (!raw || raw->ObjectClass!=CObject::ClassShip ||
        static_cast<CShip const*>(raw)->is_using_tradelane()) {
        ResetServerAsteroidAvoidance(owner,ship);
        return false;
    }
    Vector centre=ship->get_position();
    float shipRadius=0;
    shipRadius=raw->CObject::get_physical_radius_r(centre);
    Vector velocity=ship->get_velocity();
    float speed=std::sqrt(velocity.x*velocity.x+velocity.y*velocity.y+velocity.z*velocity.z);
    // Heading correction remains last-instant; the wider query is solely for
    // the separate 200 m surface-range strafe maneuver.
    float reach=(std::max)(shipRadius+350.0f,speed*0.35f+shipRadius+50.0f);
    std::vector<CObject*> candidates(64);
    int count;
    for (;;) {
        count=PhySys::FindSphereCollisions(system,centre,reach,candidates.data(),static_cast<int>(candidates.size()));
        if (count<static_cast<int>(candidates.size()) || candidates.size()>=4096) break;
        candidates.resize(candidates.size()*2);
    }
    std::vector<AsteroidAvoidance::Rock> rocks;
    auto vec=[](Vector v) { return AsteroidAvoidance::Vec{v.x,v.y,v.z}; };
    for (int i=0;i<count;++i) {
        CObject* object=candidates[i];
        if (!object || object->ObjectClass!=CObject::ClassSolar || object->PhysicsSystemId!=system ||
            !IsServerAsteroidType(static_cast<CSolar*>(object)->TypeBits) ||
            !PhySys::GetCollisionState(object)) continue;
        Vector rockCentre{};
        float radius=object->get_physical_radius_r(rockCentre);
        rocks.push_back({vec(rockCentre),vec(object->get_velocity()),radius,
                         static_cast<CSolar*>(object)->get_id()});
    }
    if (rocks.empty()) { ResetServerAsteroidAvoidance(owner,ship);return false; }

    AsteroidAvoidance::Memory localMemory;
    AsteroidAvoidance::Memory* memory=&localMemory;
    if (owner) {
        auto found=avoidanceEntries.find(owner);
        if (found!=avoidanceEntries.end() && found->second.system!=system)
            ResetServerAsteroidAvoidance(owner,ship);
        AvoidanceEntry& entry=avoidanceEntries[owner];
        if (!entry.system) entry.system=system;
        memory=&entry.memory;
        UpdateStrafe(owner,ship,centre,shipRadius,rocks);
    }
    Matrix const& orient=ship->get_orientation();
    AsteroidAvoidance::Result result;
    if (!AsteroidAvoidance::Choose(vec(centre),vec(velocity),vec(goal),
            {orient.E[0][0],orient.E[1][0],orient.E[2][0]},shipRadius,
            rocks.data(),static_cast<unsigned>(rocks.size()),result,memory)) {
        // No heading correction does not cancel an active close-range strafe.
        if (memory) *memory=AsteroidAvoidance::Memory{};
        return false;
    }
    float distance=(std::max)(300.0f,speed*2.5f);
    point=Vector{centre.x+static_cast<float>(result.direction.x)*distance,
                 centre.y+static_cast<float>(result.direction.y)*distance,
                 centre.z+static_cast<float>(result.direction.z)*distance};
    scale=static_cast<float>(result.speedScale);
    return true;
}
