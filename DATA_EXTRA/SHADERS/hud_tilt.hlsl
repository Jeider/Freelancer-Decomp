#include "common.hlsli"
float4 Panel : register(c0); // pivot in pixels, cosine, perspective coefficient
float4 Surface : register(c1); // width, height, inverse width, inverse height
sampler2D Hud : register(s0);
FFullscreenVertex VSMain(float3 position : POSITION, float2 uv : TEXCOORD0)
{
    return RPExFullscreenVS(position, uv);
}
float4 PSMain(FFullscreenVertex input) : COLOR0
{
    float2 pixel = input.TexCoord * Surface.xy - 0.5;
    float dx = pixel.x - Panel.x;
    float denominator = Panel.z - Panel.w * dx;
    clip(denominator - 0.01);
    dx /= denominator;
    float2 source = float2(Panel.x + dx, Panel.y + (pixel.y - Panel.y) * (1 + Panel.w * dx));
    float2 uv = (source + 0.5) * Surface.zw;
    clip(uv); clip(1 - uv);
    return tex2D(Hud, uv);
}
