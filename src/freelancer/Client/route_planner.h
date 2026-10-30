#pragma once
#include "route_geometry.h"
namespace RoutePlanner {
bool BetaEnabled();
// All coordinates belong to the loaded system. An empty/failed plan is never
// replaced by an unchecked direct line. Endpoints are included only at the end.
bool Plan(RouteGeometry::V from,RouteGeometry::V to,std::vector<RouteGeometry::V>& points);
// Non-dockable object: end outside its bounds/atmosphere, keeping all hazards.
bool PlanApproach(RouteGeometry::V from,unsigned destination,std::vector<RouteGeometry::V>& points);
// Ends outside the full composite base. Native Dock owns the final approach.
bool PlanDock(RouteGeometry::V from,RouteGeometry::V center,unsigned destination,
              float range,std::vector<RouteGeometry::V>& points);
void Invalidate();
}
