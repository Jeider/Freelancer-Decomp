// Freelancer Decomp: a reimplementation of the Freelancer (2003) game client and engine,
// faithful to the behaviour of the original game.
// This file was reconstructed by reverse engineering the binaries of Freelancer 1.1,
// developed by Digital Anvil.
// Author: Giperion.

// Volumetric nebula, pass 2: the composite (port-only; freelancer.exe Client/nebula_volume.cpp).
// Upsamples the reduced-resolution ray-march result (nebula_volume.hlsl: rgb in-scattered
// light, HDR on an FP16 target; a transmittance) onto the back buffer with blending
// ONE, SRCALPHA:
//   back buffer = scene * a + tonemap(rgb * exposure).
// Only the volume's own light is tonemapped; the scene behind it is attenuated, not remapped.
// With an 8-bit ray-march target (and in the debug views) the ray march already wrote
// display values and Tonemap.y is 0 (plain clamp).
// Depth-aware: where the four nearest low-resolution samples see about the same depth as this
// pixel it filters bilinearly; across a depth edge (a ship against the fog) it takes the
// sample whose depth matches best, so no fog halo bleeds over silhouettes.
// Drawn once per nebula, farthest first; a far nebula drawn in the background pass (before the
// opaque scene, Upsample.w) filters plainly.
// See docs/re/rp9.md, "Volumetric nebula".

#include "nebula_volume.hlsli"

// s0: the INTZ scene depth (point, clamp). s1: the ray-march target (linear, clamp).
sampler2D SceneDepth : register(s0);
sampler2D Volume : register(s1);

float4 ProjZ : register(c0);       // projection z/w rows (RPExLinearDepth)
float4 LowSize : register(c1);     // ray-march target: width, height, 1/width, 1/height
float4 Upsample : register(c2);    // xy half a full-res texel, z relative depth threshold,
                                   // w 1 = no depth test (drawn before the opaque scene: plain
                                   // bilinear)
float4 Tonemap : register(c3);     // x exposure, y mode (0 clamp, 1 Reinhard luma, 2 ACES),
                                   // z Reinhard white
float4 ViewRect : register(c4);
float4 ProjInv : register(c5);
float4 CamRow[3] : register(c6);
float4 StarGlow[3] : register(c9); // camera-relative world centre, inverse radius
float4 StarWeight : register(c12); // xyz sprite weight, w minimum transmission
float4 StarDistance : register(c13);
float4 FarSphere[4] : register(c14); // depthless far planets: centre, centre^2 - radius^2
float4 VisibilityFade : register(c18); // start/inverse width in metres, exterior strength
float4 FadeZoneCentre : register(c19); // xyz centre, w bound radius squared in zone space
float4 FadeZoneRow[3] : register(c20);
float4 SimpleFogColour : register(c23); // original [Fog] color, no radiance amplification

FFullscreenVertex VSMain(float3 Position : POSITION, float2 TexCoord : TEXCOORD0)
{
    return RPExFullscreenVS(Position, TexCoord);
}

float LinearDepthAt(float2 Uv)
{
    return RPExLinearDepth(tex2Dlod(SceneDepth, float4(Uv, 0.0, 0.0)).r, ProjZ);
}

float4 FinishVolume(float4 Value, float2 Uv)
{
    // Never brighten the fog on a depth-writing object. Background shells do not need this
    // correction; they render before the solar sprites, planets and local nebulae.
    if ((StarWeight.w > 0.0 || VisibilityFade.y > 0.0) && Upsample.w < 0.5)
    {
        float2 ViewUv = (Uv - ViewRect.xy) / ViewRect.zw;
        float2 ViewXY = float2(ViewUv.x * 2.0 - 1.0, 1.0 - ViewUv.y * 2.0) * ProjInv.xy;
        float3 Dir = normalize(ViewXY.x * CamRow[0].xyz + ViewXY.y * CamRow[1].xyz - CamRow[2].xyz);
        float DeviceDepth = tex2Dlod(SceneDepth, float4(Uv, 0.0, 0.0)).r;
        float SceneT = DeviceDepth < 1.0 ? RPExLinearDepth(DeviceDepth, ProjZ) /
            max(abs(dot(Dir, CamRow[2].xyz)), 1.0e-4) : 1.0e30;
        [unroll] for (int I = 0; I < 4; ++I)
        {
            float B = dot(Dir, FarSphere[I].xyz);
            float D = B * B - FarSphere[I].w;
            float Hit = B - sqrt(max(D, 0.0));
            if (FarSphere[I].w < 1.0e29 && D >= 0.0 && Hit > 0.0)
                SceneT = min(SceneT, Hit);
        }
        if (VisibilityFade.y > 0.0 && Value.a < 0.99999)
        {
            float2 Span = NebulaZoneSpan(Dir, FadeZoneCentre.xyz, FadeZoneRow[0].xyz,
                FadeZoneRow[1].xyz, FadeZoneRow[2].xyz, FadeZoneCentre.w);
            float FogLength = max(min(Span.y, SceneT) - max(Span.x, 0.0), 0.0);
            // Ordinary linear distance fog: blend towards the authored fog colour.
            // Never divide by the current opacity or amplify a nearly clear sample:
            // that promoted sun scattering into bright asteroid silhouettes.
            float Fade = saturate((FogLength - VisibilityFade.x) * VisibilityFade.y) * VisibilityFade.z;
            Value.rgb = lerp(Value.rgb, SimpleFogColour.rgb, Fade);
            Value.a *= 1.0 - Fade;
        }
        if (StarWeight.w > 0.0 && DeviceDepth >= 1.0)
        {
        float3 Along = float3(dot(Dir, StarGlow[0].xyz), dot(Dir, StarGlow[1].xyz), dot(Dir, StarGlow[2].xyz));
        float3 Offset = sqrt(max(StarDistance.xyz * StarDistance.xyz - Along * Along, 0.0)) *
                        StarDistance.xyz / max(Along, 1.0e-3 * max(StarDistance.xyz, 1.0));
        float3 W = saturate((1.0 - Offset * float3(StarGlow[0].w, StarGlow[1].w, StarGlow[2].w)) * StarWeight.xyz);
        W *= Along > 0.0 ? 1.0 : 0.0;
        W *= StarDistance.xyz < SceneT ? 1.0 : 0.0;
        Value.a = lerp(Value.a, max(Value.a, StarWeight.w), max(max(W.x, W.y), W.z));
        }
    }
    return float4(RPExTonemap(Value.rgb * Tonemap.x, Tonemap.y, Tonemap.z), Value.a);
}

float4 PSComposite(float2 TexCoord : TEXCOORD0) : COLOR0
{
    // A far nebula drawn in the background pass (no opaque scene yet): nothing to keep apart.
    if (Upsample.w > 0.5)
        return FinishVolume(tex2Dlod(Volume, float4(TexCoord, 0.0, 0.0)), TexCoord);

    float Depth = LinearDepthAt(TexCoord);

    // The four low-resolution texels around this pixel.
    float2 Low = TexCoord * LowSize.xy - 0.5;
    float2 Base = floor(Low);
    float2 Frac = Low - Base;
    float2 Uv00 = (Base + float2(0.5, 0.5)) * LowSize.zw;
    float2 Uv10 = Uv00 + float2(LowSize.z, 0.0);
    float2 Uv01 = Uv00 + float2(0.0, LowSize.w);
    float2 Uv11 = Uv00 + LowSize.zw;

    // Their depths: the full-res texel each one was marched with (half a texel in).
    float D00 = LinearDepthAt(Uv00 + Upsample.xy);
    float D10 = LinearDepthAt(Uv10 + Upsample.xy);
    float D01 = LinearDepthAt(Uv01 + Upsample.xy);
    float D11 = LinearDepthAt(Uv11 + Upsample.xy);
    float4 Diff = abs(float4(D00, D10, D01, D11) - Depth) / max(Depth, 1.0e-3);
    float MaxDiff = max(max(Diff.x, Diff.y), max(Diff.z, Diff.w));

    if (MaxDiff < Upsample.z)
        return FinishVolume(tex2Dlod(Volume, float4(TexCoord, 0.0, 0.0)), TexCoord); // smooth: bilinear

    // Depth edge: the best-matching sample (read at its texel centre).
    float2 BestUv = Uv00;
    float Best = Diff.x;
    if (Diff.y < Best)
    {
        Best = Diff.y;
        BestUv = Uv10;
    }
    if (Diff.z < Best)
    {
        Best = Diff.z;
        BestUv = Uv01;
    }
    if (Diff.w < Best)
    {
        BestUv = Uv11;
    }
    return FinishVolume(tex2Dlod(Volume, float4(BestUv, 0.0, 0.0)), TexCoord);
}
