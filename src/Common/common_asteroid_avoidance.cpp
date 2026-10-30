#include "common_asteroid_avoidance.h"
#include "asteroid_avoidance_math.h"
#include "common_iface.h"
#include "common_cobject.h"
#include "common_physys.h"
#include "common_server_asteroid.h"
#include <algorithm>
#include <vector>

bool FindServerAsteroidAvoidance(IObjRW* ship, unsigned system, Vector const& goal,
                                 Vector& point, float& scale) {
    if (!ship || !system) return false;
    CObject const* raw=ship->cobject();
    if (!raw || raw->ObjectClass!=CObject::ClassShip ||
        static_cast<CShip const*>(raw)->is_using_tradelane()) return false;
    Vector centre=ship->get_position();
    float shipRadius=0;
    shipRadius=raw->CObject::get_physical_radius_r(centre);
    Vector velocity=ship->get_velocity();
    float speed=std::sqrt(velocity.x*velocity.x+velocity.y*velocity.y+velocity.z*velocity.z);
    float reach=(std::min)(12000.0f,(std::max)(600.0f,speed*3.0f+shipRadius+1500.0f));
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
        rocks.push_back({vec(rockCentre),vec(object->get_velocity()),radius});
    }
    if (rocks.empty()) return false;
    Matrix const& orient=ship->get_orientation();
    AsteroidAvoidance::Result result;
    if (!AsteroidAvoidance::Choose(vec(centre),vec(velocity),vec(goal),
            {orient.E[0][0],orient.E[1][0],orient.E[2][0]},shipRadius,
            rocks.data(),static_cast<unsigned>(rocks.size()),result)) return false;
    float distance=(std::max)(200.0f,speed*2.0f);
    point=Vector{centre.x+static_cast<float>(result.direction.x)*distance,
                 centre.y+static_cast<float>(result.direction.y)*distance,
                 centre.z+static_cast<float>(result.direction.z)*distance};
    scale=static_cast<float>(result.speedScale);
    return true;
}
