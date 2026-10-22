row_major float4x4 ObjectToShadow : register(c0);
// alpha test enabled, alpha reference, diffuse alpha, depth sign (-1 = short-reach caster)
float4 Cutout : register(c4);
sampler2D ColourMap : register(s0);
struct ShadowPixel { float4 Position:POSITION0; float2 Uv:TEXCOORD0; float Depth:TEXCOORD1; };
ShadowPixel VSMain(float3 Position:POSITION0, float2 Uv:TEXCOORD0)
{
    ShadowPixel Out;
    Out.Position = mul(float4(Position,1),ObjectToShadow);
    Out.Depth = Out.Position.z;
    Out.Uv = Uv;
    return Out;
}
float4 PSMain(ShadowPixel In):COLOR0
{
    if (Cutout.x > 0.5) clip(tex2D(ColourMap,In.Uv).a * Cutout.z - Cutout.y);
    // The hardware depth buffer keeps the true depth; only the stored value carries
    // the caster's shadow reach (surface_material.hlsl ShadowDepth).
    return (In.Depth * Cutout.w).xxxx;
}
