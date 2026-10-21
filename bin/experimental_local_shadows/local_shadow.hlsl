row_major float4x4 ObjectToShadow : register(c0);
float4 Cutout : register(c4); // alpha test enabled, alpha reference, diffuse alpha
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
    return In.Depth.xxxx;
}
