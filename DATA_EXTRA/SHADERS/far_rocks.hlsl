#include "common.hlsli"
// Port-only far rocks: an asteroid field seen from afar as thousands of lit, textured rock impostors
// (vs_3_0 + ps_3_0). Each rock is one camera-facing quad (6 vertices of a triangle list, see
// far_rocks.cpp): the vertex shader builds the quad in view space, keeps it at least min_pixels
// wide (a smaller rock keeps that size and loses alpha by its area), fades it by distance and
// throws it away when it is off-limits. The pixel shader draws a lumpy sphere: an outline from two
// sine harmonics of the angle, a sphere normal with a bump, lit by the field's sun (N.L, computed
// once per field on the CPU) plus the system ambient. The surface colour is the diffuse texture of
// one of the field's dynamic asteroids (the rock carries one of up to four by its hash), sampled
// through the bumped sphere normal with a per-rock turn and offset, times that asteroid's tint.
// Everything fades in alpha (outline, distance, size): drawn alpha blended with the scene depth
// bound for the test only (no depth write, no clip, no dither), so nothing flickers. A rock beyond
// the scene's far plane gets its clip depth clamped just in front of the cleared depth, so it
// draws over the sky only.

// -- vertex constants
float4 CamRel : register(c0);        // xyz camera - anchor (the vertex positions are relative to the anchor)
float4 ViewRow[3] : register(c1);    // view rotation rows in world axes: right, up, back
float4 Proj : register(c4);          // ScaleX, ScaleY, ProjA, ProjB
float4 Remap : register(c5);         // viewport remap: Sx, Sy, Bx, By (the pass viewport is the whole target)
float4 Lod : register(c6);           // far plane, pixels per unit at depth 1, min_pixels, 1 - 2^-22
float4 Range : register(c7);         // start, 1 / start_fade, far_dist - far_fade, 1 / far_fade
float4 RockPass : register(c8);          // x 0 = the solid rocks, 1 = the soft dots; y solid_pixels

struct RockVertex
{
    float3 Position : POSITION0;
    float4 Colour : COLOR0;      // r: brightness jitter, g / b: the corner (0 / 1), a: texture index / 3
    float2 Rock : TEXCOORD0;     // radius (m), seed (0..1)
};

struct RockInterp
{
    float4 Position : POSITION0;
    float4 QFade : TEXCOORD0;    // xy: position in rock radii, z: radius in pixels, w: alpha
    float4 Info : TEXCOORD1;     // seed, texture index / 3, jitter, -
};

RockInterp VSMain(RockVertex In)
{
    RockInterp Out;
    float Radius = In.Rock.x;
    float3 Rel = In.Position - CamRel.xyz;
    float3 V = float3(dot(Rel, ViewRow[0].xyz), dot(Rel, ViewRow[1].xyz), dot(Rel, ViewRow[2].xyz));
    float Depth = -V.z;
    float Dist = length(Rel);
    float D = max(Depth, 1.0);
    // The distance fades thin the rock (alpha); a thinned rock is drawn with the soft ones,
    // without depth, so it does not hide what is behind it.
    float NearFade = saturate((Dist - Range.x) * Range.y);
    float FarFade = saturate(1.0 - (Dist - Range.z) * Range.w);
    NearFade = NearFade * NearFade * (3.0 - 2.0 * NearFade);
    FarFade = FarFade * FarFade * (3.0 - 2.0 * FarFade);
    float PxRadius = Radius * Lod.y / D;
    float MinPx = Lod.z;
    // A rock under min_pixels also fades by its area (a soft dot, so it does not shimmer).
    float Cover = PxRadius < MinPx ? (PxRadius / MinPx) * (PxRadius / MinPx) : 1.0;
    float Alpha = Cover * NearFade * FarFade;

    Out.Position = float4(0.0, 0.0, -2.0, 1.0);
    Out.QFade = float4(0.0, 0.0, 0.0, 0.0);
    Out.Info = float4(0.0, 0.0, 0.0, 0.0);
    // This pass's kind only: solid (at least solid_pixels and not fading: depth written) or
    // soft (smaller or fading).
    float Solid = PxRadius >= RockPass.y && Alpha >= 0.999 ? 1.0 : 0.0;
    [branch] if (Depth >= 1.0 && Alpha >= 1.0 / 255.0 && Solid != RockPass.x)
    {
        // The quad is 1.2 rock radii (or min_pixels * 1.2 wide when the rock is smaller); the
        // outline in the pixel shader fills it up to the rock radius, so the corner is q * 1.2.
        float2 Corner = In.Colour.gb * 2.0 - 1.0;
        float Quad = 1.2 * max(Radius, MinPx * D / Lod.y);
        V.xy += Corner * Quad;
        float4 P;
        P.x = V.x * Proj.x;
        P.y = V.y * Proj.y;
        P.z = Proj.z * Depth + Proj.w;
        P.w = Depth;
        if (Depth > Lod.x)
            P.z = P.w * Lod.w;
        P.xy = P.xy * Remap.xy + Remap.zw * P.w;
        Out.Position = P;
        Out.QFade = float4(Corner * 1.2, PxRadius, Alpha);
        Out.Info = float4(In.Rock.y, In.Colour.a, In.Colour.r, Solid);
    }
    return Out;
}

// -- pixel constants
float4 TexTint[4] : register(c0);    // rgb tint of dynamic texture i, w 1 when its texture is bound
float4 Fallback : register(c4);      // rgb albedo without a texture, w number of textures (0..4)
float4 AmbientLight : register(c5);  // rgb system ambient at the field, w lump (outline)
float4 SunLight : register(c6);      // rgb sun colour * sunlit * brightness, w bump (surface)
float4 SunView : register(c7);       // xyz unit vector rock -> sun in view space, w texture scale

sampler2D RockTex0 : register(s0);
sampler2D RockTex1 : register(s1);
sampler2D RockTex2 : register(s2);
sampler2D RockTex3 : register(s3);

float RockHash(float Seed, float K)
{
    return frac(sin(Seed * K + K * 0.618) * 43758.5453);
}

float4 PSMain(RockInterp In) : COLOR0
{
    float2 Q = In.QFade.xy;
    float PxRadius = In.QFade.z;
    float Seed = In.Info.x;
    float H1 = RockHash(Seed, 12.9898);
    float H2 = RockHash(Seed, 78.233);
    float H3 = RockHash(Seed, 37.719);
    float H4 = RockHash(Seed, 93.989);
    float H5 = RockHash(Seed, 45.164);

    // A fixed turn of the lump pattern and the texture (no spin).
    float Spin = Seed * 6.2832;
    float SinSpin, CosSpin;
    sincos(Spin, SinSpin, CosSpin);
    float2 Turned = float2(CosSpin * Q.x - SinSpin * Q.y, SinSpin * Q.x + CosSpin * Q.y);

    float Angle = atan2(Q.y, Q.x) + Spin;
    float Edge = 1.0 - AmbientLight.w * (0.5 + 0.3 * sin(3.0 * Angle + 6.28 * H1) + 0.2 * sin(5.0 * Angle + 6.28 * H2));
    float R = length(Q);
    float Cover = saturate((Edge - R) / max(fwidth(R), 1.0e-3));

    float2 Disc = Q / Edge;
    float3 N = float3(Disc, sqrt(saturate(1.0 - dot(Disc, Disc))));
    N.xy += SunLight.w * 0.3 * sin(Turned * 7.0 + 6.28 * H4) * cos(Turned.yx * 5.0 + 6.28 * H5);
    N = normalize(N);

    // The texture through the bumped sphere normal: turned by the rock's angle, a random offset
    // (the texture wraps), up to four textures sampled in uniform flow, one picked by the rock.
    float2 Uv = float2(CosSpin * N.x - SinSpin * N.y, SinSpin * N.x + CosSpin * N.y) * (0.5 * SunView.w) +
                float2(H4, H5);
    float2 UvDx = ddx(Uv);
    float2 UvDy = ddy(Uv);
    float Index = In.Info.y * 3.0;
    float3 Albedo = Fallback.rgb;
    [branch] if (Fallback.w > 0.5)
    {
        // One fetch per pixel, from the rock's own texture (explicit gradients: the pick varies
        // between rocks, so this is not uniform flow).
        if (Index < 0.5)
        {
            if (TexTint[0].w > 0.5)
                Albedo = tex2Dgrad(RockTex0, Uv, UvDx, UvDy).rgb * TexTint[0].rgb;
        }
        else if (Index < 1.5)
        {
            if (TexTint[1].w > 0.5)
                Albedo = tex2Dgrad(RockTex1, Uv, UvDx, UvDy).rgb * TexTint[1].rgb;
        }
        else if (Index < 2.5)
        {
            if (TexTint[2].w > 0.5)
                Albedo = tex2Dgrad(RockTex2, Uv, UvDx, UvDy).rgb * TexTint[2].rgb;
        }
        else if (TexTint[3].w > 0.5)
            Albedo = tex2Dgrad(RockTex3, Uv, UvDx, UvDy).rgb * TexTint[3].rgb;
    }
    Albedo *= lerp(0.85, 1.1, In.Info.z) * (0.9 + 0.2 * H3);

    float3 L = normalize(SunView.xyz);
    float Lit;
    [branch] if (PxRadius < 2.0)
    {
        // A speck: the sunlit share of a Lambert sphere seen at this phase angle.
        float A = acos(clamp(L.z, -1.0, 1.0));
        Lit = max((sin(A) + (3.14159265 - A) * cos(A)) / 3.14159265, 0.0);
    }
    else
    {
        float Mu0 = saturate(dot(N, L));
        float Mu = saturate(N.z);
        Lit = 0.7 * Mu0 + 0.3 * Mu0 / (Mu0 + Mu + 1.0e-3);
    }
    float Phase = 0.85 + 0.5 * pow(saturate(L.z), 6.0);
    float3 Colour = Albedo * (SunLight.rgb * (Lit * Phase) + AmbientLight.rgb);
    // Solid: a rock of at least min_pixels drops the pixels it covers less than half (its
    // antialiased rim stays), so its inside is opaque; a smaller one stays a soft dot.
    if (In.Info.w > 0.5) // a solid rock (the vertex shader's pass kind)
        clip(Cover - 0.5);
    return float4(saturate(Colour), Cover * In.QFade.w);
}
