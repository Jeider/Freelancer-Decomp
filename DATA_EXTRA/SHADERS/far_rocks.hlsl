#include "common.hlsli"
// Port-only far rocks: an asteroid field seen from afar as thousands of lit rock impostors
// (vs_3_0 + ps_3_0). Each rock is one camera-facing quad (6 vertices of a triangle list, see
// far_rocks.cpp): the vertex shader builds the quad in view space, keeps it at least min_pixels
// wide (a smaller rock keeps that size and loses alpha by its area), fades it by distance and
// throws it away when it is off-limits. The pixel shader draws a lumpy sphere: an outline from two
// sine harmonics of the angle, a sphere normal with a bump, lit by the sun (dark and bright sides,
// opposition surge, a glint on a few rocks) and by the planets' shadow baked per rock. Drawn into
// the scene with the scene depth bound (depth test and write), so rocks occlude and are occluded
// without sorting. A rock beyond the scene's far plane gets its clip depth clamped just in front of
// the cleared depth, so it draws over the sky only. Production follow-up: an offline-baked impostor
// atlas instead of the procedural sphere.

// -- vertex constants
float4 CamRel : register(c0);    // xyz camera - anchor (the vertex positions are relative to the anchor), w time (s)
float4 ViewRow[3] : register(c1); // view rotation rows in world axes: right, up, back
float4 Proj : register(c4);      // ScaleX, ScaleY, ProjA, ProjB
float4 Remap : register(c5);     // viewport remap: Sx, Sy, Bx, By (the pass viewport is the whole target)
float4 Lod : register(c6);       // far plane, pixels per unit at depth 1, min_pixels, 1 - 2^-22
float4 Range : register(c7);     // start, 1 / start_fade, far_dist - far_fade, 1 / far_fade
float4 SunRel : register(c8);    // xyz sun - anchor, w 1 with a sun
float4 SpinInfo : register(c9);  // spin (rad/s, max per rock)

struct RockVertex
{
    float3 Position : POSITION0;
    float4 Colour : COLOR0;      // r, g: the corner (0 / 1), b: albedo mix, a: sunlit
    float2 Rock : TEXCOORD0;     // radius (m), seed (0..1)
};

struct RockInterp
{
    float4 Position : POSITION0;
    float4 QFade : TEXCOORD0;    // xy: position in rock radii, z: dither fade in, w: radius in pixels
    float4 Info : TEXCOORD1;     // seed, albedo mix, sunlit, alpha
    float4 Light : TEXCOORD2;    // xyz: direction to the sun (view), w: spin angle
};

RockInterp VSMain(RockVertex In)
{
    RockInterp Out;
    float Radius = In.Rock.x;
    float Seed = In.Rock.y;
    float3 Rel = In.Position - CamRel.xyz;
    float3 V = float3(dot(Rel, ViewRow[0].xyz), dot(Rel, ViewRow[1].xyz), dot(Rel, ViewRow[2].xyz));
    float Depth = -V.z;
    float Dist = length(Rel);
    float D = max(Depth, 1.0);
    float PxRadius = Radius * Lod.y / D;
    float MinPx = Lod.z;
    float Cover = PxRadius < MinPx ? (PxRadius / MinPx) * (PxRadius / MinPx) : 1.0;
    float NearFade = saturate((Dist - Range.x) * Range.y);
    float FarFade = saturate(1.0 - (Dist - Range.z) * Range.w);
    float Alpha = Cover * FarFade;

    Out.Position = float4(0.0, 0.0, -2.0, 1.0);
    Out.QFade = float4(0.0, 0.0, 0.0, 0.0);
    Out.Info = float4(0.0, 0.0, 0.0, 0.0);
    Out.Light = float4(0.0, 0.0, 1.0, 0.0);
    [branch] if (Depth >= 1.0 && NearFade > 0.0 && Alpha >= 1.0 / 255.0)
    {
        // The quad is 1.2 rock radii (or min_pixels * 1.2 wide when the rock is smaller); the
        // outline in the pixel shader fills it up to the rock radius, so the corner is q * 1.2.
        float2 Corner = In.Colour.rg * 2.0 - 1.0;
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

        float3 L = float3(0.0, 0.0, 1.0);
        if (SunRel.w > 0.5)
        {
            float3 ToSun = normalize(SunRel.xyz - In.Position);
            L = float3(dot(ToSun, ViewRow[0].xyz), dot(ToSun, ViewRow[1].xyz), dot(ToSun, ViewRow[2].xyz));
        }
        float Spin = Seed * 6.2832 + SpinInfo.x * (frac(Seed * 7.31) * 2.0 - 1.0) * CamRel.w;
        Out.QFade = float4(Corner * 1.2, NearFade, PxRadius);
        Out.Info = float4(Seed, In.Colour.b, In.Colour.a, Alpha);
        Out.Light = float4(L, Spin);
    }
    return Out;
}

// -- pixel constants
float4 ColourA : register(c0);   // rgb albedo, w brightness
float4 ColourB : register(c1);   // rgb albedo of the other end of the mix
float4 SunColour : register(c2); // rgb sunlight
float4 Ambient : register(c3);   // rgb fill light
float4 Glint : register(c4);     // x opposition surge, y share of rocks with a glint, z glint strength
float4 Shape : register(c5);     // x lump (outline), y bump (surface)

float RockIgn(float2 Pixel)
{
    return frac(52.9829189 * frac(dot(Pixel, float2(0.06711056, 0.00583715))));
}

float RockHash(float Seed, float K)
{
    return frac(sin(Seed * K + K * 0.618) * 43758.5453);
}

float4 PSMain(RockInterp In, float2 Vpos : VPOS) : COLOR0
{
    // The rock fades in at the near edge by a screen door: it is big there.
    clip(In.QFade.z - RockIgn(Vpos));

    float2 Q = In.QFade.xy;
    float Seed = In.Info.x;
    float Alpha = In.Info.w;
    float PxRadius = In.QFade.w;
    float H1 = RockHash(Seed, 12.9898);
    float H2 = RockHash(Seed, 78.233);
    float H3 = RockHash(Seed, 37.719);
    float H4 = RockHash(Seed, 93.989);
    float H5 = RockHash(Seed, 45.164);
    float H6 = RockHash(Seed, 63.731);

    float Spin = In.Light.w;
    float SinSpin, CosSpin;
    sincos(Spin, SinSpin, CosSpin);
    float2 Turned = float2(CosSpin * Q.x - SinSpin * Q.y, SinSpin * Q.x + CosSpin * Q.y);

    float Angle = atan2(Q.y, Q.x) + Spin;
    float Edge = 1.0 - Shape.x * (0.5 + 0.3 * sin(3.0 * Angle + 6.28 * H1) + 0.2 * sin(5.0 * Angle + 6.28 * H2));
    float R = length(Q);
    float Cover = saturate((Edge - R) / max(fwidth(R), 1.0e-3));
    clip(Cover * Alpha - 1.0 / 255.0);

    float3 L = normalize(In.Light.xyz);
    float3 N = float3(0.0, 0.0, 1.0);
    float Lit;
    [branch] if (PxRadius < 2.0)
    {
        // A speck: the sunlit share of a Lambert sphere seen at this phase angle.
        float A = acos(clamp(L.z, -1.0, 1.0));
        Lit = max((sin(A) + (3.14159265 - A) * cos(A)) / 3.14159265, 0.0);
    }
    else
    {
        float2 Disc = Q / Edge;
        N = float3(Disc, sqrt(saturate(1.0 - dot(Disc, Disc))));
        N.xy += Shape.y * 0.3 * sin(Turned * 7.0 + 6.28 * H4) * cos(Turned.yx * 5.0 + 6.28 * H5);
        N = normalize(N);
        float Mu0 = saturate(dot(N, L));
        float Mu = saturate(N.z);
        Lit = 0.7 * Mu0 + 0.3 * Mu0 / (Mu0 + Mu + 1.0e-3);
    }
    float Phase = 0.85 + Glint.x * pow(saturate(L.z), 6.0);

    float3 Albedo = lerp(ColourA.rgb, ColourB.rgb, In.Info.y) * (0.8 + 0.4 * H3);
    float3 Sun = SunColour.rgb * In.Info.z;
    float3 Colour = Albedo * (Sun * (Lit * Phase * ColourA.w) + Ambient.rgb);
    if (H6 < Glint.y)
        Colour += Sun * Glint.z * pow(saturate(dot(reflect(-L, N), float3(0.0, 0.0, 1.0))), 32.0);
    return float4(saturate(Colour), Cover * Alpha);
}
