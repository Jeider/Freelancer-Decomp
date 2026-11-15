#include "nebula_composite.hlsl"
float4 ProbeVolume : register(c113);
float4 ProbeDistance : register(c114);
float4 PSCoreProbe(float2 uv : TEXCOORD0) : COLOR0
{
    return ApplyExclusionCoreHaze(ProbeVolume, ProbeDistance.x);
}
