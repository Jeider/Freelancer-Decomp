#pragma once
#include "common_misc.h"
#include "port_config.h"
#include "star_sys.h"
#include "graphics_settings.h"

// Temporary, system-scoped art trial. The receiver scope is cleared after drawing.
inline unsigned NebulaFogShapeScope()
{
    static bool const Enabled = PortConfigInt("Render", "nebula_object_fog_shape_test", 1) != 0;
    static unsigned const Systems[] = {CreateID("om15"), CreateID("om7"), CreateID("rh_stut")};
    unsigned const System = StarSysGetActiveSystemId();
    return Enabled && GraphicsSettings::Get(GraphicsSettings::Nebulae)>=2 &&
        (System==Systems[0] || System==Systems[1] || System==Systems[2]) ? 512u : 0u;
}

// Solid solar hulls, including NON_TARGETABLE structures and mining asteroids.
// Celestial bodies, jump-hole effects and waypoints have separate draw paths.
inline bool NebulaFogSolarHull(int ManagerKind, unsigned Type)
{
    return ManagerKind==2 && (Type & (0x0fu | 0x200u | 0x800u))==0;
}
