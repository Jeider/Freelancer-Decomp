// Included by common_obstacleavoidance.cpp: no ABI/layout changes.
#include "common_phyarch.h"
#include "solar_avoidance_geometry.h"

namespace {
enum class SolarSweep { Unsupported, Clear, Blocked };
SolarSweep RefineSolarSweep(IObjInspect* candidate,Vector const& from,Vector const& to,
                           float clearance,Vector& wall) {
    unsigned type=0;
    candidate->get_type(type);
    if((type & (0x10u|0x100u|0x4000u|0x8000u))==0) return SolarSweep::Unsupported;
    CObject const* object=candidate->cobject();
    if(!object || (object->ObjectClass & 0x303u)!=0x303u || !object->PhyPart || !object->PhyPart->Surface)
        return SolarSweep::Unsupported;
    Vector const& lo=object->PhyPart->ExtentsMin;
    Vector const& hi=object->PhyPart->ExtentsMax;
    if((std::max)(hi.x-lo.x,(std::max)(hi.y-lo.y,hi.z-lo.z))<800.f) return SolarSweep::Unsupported;
    Transform const& transform=candidate->get_transform();
    auto local=[&](Vector const& p) {
        double x=p.x-transform.Translation.x,y=p.y-transform.Translation.y,z=p.z-transform.Translation.z;
        Matrix const& r=transform.Rotation;
        return SolarAvoidanceGeometry::V{x*r.E[0][0]+y*r.E[1][0]+z*r.E[2][0],
            x*r.E[0][1]+y*r.E[1][1]+z*r.E[2][1],x*r.E[0][2]+y*r.E[1][2]+z*r.E[2][2]};
    };
    SolarAvoidanceGeometry::Query query{local(from),local(to),(std::max)(1.f,clearance)};
    SolarAvoidanceGeometry::walk(object->PhyPart->Surface->get_compact_ledge_tree_root(),query,
        [&](unsigned part) {return object->SurfaceManager==nullptr || object->part_to_inst(part)!=-1;});
    if(query.exhausted) return SolarSweep::Unsupported; // Conservative fallback, never a false clear.
    if(!query.hit) return SolarSweep::Clear;
    auto p=query.nearest.wall;
    Matrix const& r=transform.Rotation;
    wall={float(r.E[0][0]*p.x+r.E[0][1]*p.y+r.E[0][2]*p.z+transform.Translation.x),
          float(r.E[1][0]*p.x+r.E[1][1]*p.y+r.E[1][2]*p.z+transform.Translation.y),
          float(r.E[2][0]*p.x+r.E[2][1]*p.y+r.E[2][2]*p.z+transform.Translation.z)};
    return SolarSweep::Blocked;
}
}
