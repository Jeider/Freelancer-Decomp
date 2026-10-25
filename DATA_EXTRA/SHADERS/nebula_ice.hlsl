// Tau37 frozen folds. Compile separately so other nebulae retain their shader path.
#define NEBULA_ICE 1
// Tau37 uses quiet frost emission; omit the four lightning cores to leave SM3 registers
// for the folded density and its shadow probes. Other nebulae retain point lightning.
#define NEBULA_POINT_LIGHTS 0
#include "nebula_volume.hlsl"
