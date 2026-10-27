// SMAA 1x High entry points. RP9 prepends SMAA/SMAA.hlsl with SMAA_HLSL_3,
// SMAA_PRESET_HIGH and SMAA_RT_METRICS = PixelSize. No temporal history/jitter.
sampler2D Input0 : register(s0);
sampler2D Input1 : register(s1);
sampler2D Input2 : register(s2);

float4 EdgesPS(float2 uv : TEXCOORD0) : COLOR0
{
    float4 offsets[3];
    SMAAEdgeDetectionVS(uv, offsets);
    return float4(SMAAColorEdgeDetectionPS(uv, offsets, Input0), 0, 0);
}

float4 WeightsPS(float2 uv : TEXCOORD0) : COLOR0
{
    float2 pixel;
    float4 offsets[3];
    SMAABlendingWeightCalculationVS(uv, pixel, offsets);
    return SMAABlendingWeightCalculationPS(uv, pixel, offsets,
                                          Input0, Input1, Input2, float4(0, 0, 0, 0));
}

float4 BlendPS(float2 uv : TEXCOORD0) : COLOR0
{
    float4 offset;
    SMAANeighborhoodBlendingVS(uv, offset);
    return SMAANeighborhoodBlendingPS(uv, offset, Input0, Input1);
}
