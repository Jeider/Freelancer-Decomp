#pragma once
#include "common_misc.h"
#include "port_config.h"
#include "star_sys.h"
#include "graphics_settings.h"

// Temporary, system-scoped art trial. The receiver scope is cleared after drawing.
inline unsigned NebulaFogShapeScope()
{
    static bool const Enabled = PortConfigInt("Render", "nebula_object_fog_shape_test", 1) != 0;
    static unsigned const System = CreateID("om15");
    return Enabled && GraphicsSettings::Get(GraphicsSettings::Nebulae)>=2 &&
        StarSysGetActiveSystemId() == System ? 512u : 0u;
}
