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
// Solid silhouettes write depth with an alpha cutout; small or fading ones only blend. A rock beyond
// the scene's far plane gets its clip depth clamped just in front of the cleared depth, so it
// draws over the sky only.

// -- vertex constants
float4 CamRel : register(c0);        // xyz camera - anchor (the vertex positions are relative to the anchor)
float4 ViewRow[3] : register(c1);    // view rotation rows in world axes: right, up, back
float4 Proj : register(c4);          // ScaleX, ScaleY, ProjA, ProjB
float4 Remap : register(c5);         // viewport remap: Sx, Sy, Bx, By (the pass viewport is the whole target)
float4 Lod : register(c6);           // far plane, pixels per unit at depth 1, min_pixels, 1 - 2^-22
float4 Range : register(c7);         // start, 1 / start_fade, far_dist - far_fade, 1 / far_fade
float4 RockPass : register(c8);      // x 0 solid / 1 soft, y solid_pixels

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

float4 Relief : register(c8);        // x relief strength (far_rocks_relief; 0 = off)

// Procedural rock relief, arithmetic only (no texture, no extra binding): lumps at three scales and a
// network of dark cracks as an analytic height field. Returns the height's gradient at P (rock-plane
// units) and a crack mask (1 on a crack).
float2 RockRelief(float2 P, float Seed, out float Crack)
{
    float2 A = P * 2.6 + Seed * 31.0;
    float2 B = P * 6.1 + float2(Seed * 17.0, 4.3);
    float2 C = P * 13.7 + float2(2.1, Seed * 23.0);
    float2 G = float2(cos(A.x) * sin(A.y), sin(A.x) * cos(A.y)) * 2.6;
    G += float2(cos(B.x) * sin(B.y), sin(B.x) * cos(B.y)) * (6.1 * 0.45);
    G += float2(cos(C.x) * sin(C.y), sin(C.x) * cos(C.y)) * (13.7 * 0.18);
    // Cracks: a warped sine's zero crossings, dark and a little recessed.
    float U = dot(P, float2(4.7, 3.1)) + 1.7 * sin(P.y * 3.3 + Seed * 9.0) + Seed * 20.0;
    float S = sin(U);
    Crack = saturate(1.0 - abs(S) * 7.0);
    G += float2(4.7, 3.1) * (-sign(S) * cos(U)) * (0.25 * Crack);
    return G;
}

struct MeshVertex
{
    float3 Position : POSITION0;
    float3 Normal : NORMAL0;
    float2 Uv : TEXCOORD0;
    float4 CentreRadius : TEXCOORD1;
    float4 Rotation : TEXCOORD2;
    float4 Colour : COLOR0;
};
struct MeshInterp
{
    float4 Position : POSITION0;
    float2 Uv : TEXCOORD0;
    float3 Normal : TEXCOORD1;
    float3 FadeJitterSolid : TEXCOORD2;
    float3 ToEye : TEXCOORD3;
};
// Shared by mesh debris and the resolved asteroid impostors. The unlit hemisphere
// receives ambient only; reversing the sun must not light the same surface equally.
float AsteroidDiffuse(float3 N, float3 L, float3 V)
{
    float Mu0 = saturate(dot(N, L));
    float Mu = saturate(dot(N, V));
    return 0.7 * Mu0 + 0.3 * Mu0 / (Mu0 + Mu + 1.0e-3);
}
float AsteroidPhase(float3 L, float3 V)
{
    float C = saturate(dot(L, V));
    float C2 = C * C;
    return 0.85 + 0.5 * C2 * C2 * C2;
}
float3 MeshRotate(float3 V, float4 Q)
{
    return V + 2.0 * cross(Q.xyz, cross(Q.xyz, V) + Q.w * V);
}
MeshInterp VSMesh(MeshVertex In)
{
    MeshInterp Out;
    float3 Centre = In.CentreRadius.xyz - CamRel.xyz;
    float Depth = -dot(Centre, ViewRow[2].xyz);
    float Dist = length(Centre);
    float Fade = smoothstep(0.0, 1.0, saturate((Dist - Range.x) * Range.y)) *
                 smoothstep(0.0, 1.0, saturate(1.0 - (Dist - Range.z) * Range.w));
    float PxRadius = In.CentreRadius.w * Lod.y / max(Depth, 1.0);
    Fade *= smoothstep(0.0, Lod.z, PxRadius); // fade subpixel geometry; never inflate it into a quad
    float Solid = Fade >= 0.999 ? 1.0 : 0.0;
    Out.Position = float4(0.0, 0.0, -2.0, 1.0);
    Out.Uv = In.Uv;
    float3 Normal = MeshRotate(In.Normal, In.Rotation);
    Out.Normal = float3(dot(Normal, ViewRow[0].xyz), dot(Normal, ViewRow[1].xyz), dot(Normal, ViewRow[2].xyz));
    Out.FadeJitterSolid = float3(Fade, In.Colour.r, Solid);
    Out.ToEye = float3(0.0, 0.0, 1.0);
    [branch] if (Depth + In.CentreRadius.w >= 1.0 && Fade >= 1.0 / 255.0 && Solid != RockPass.x)
    {
        float3 Rel = Centre + MeshRotate(In.Position * In.CentreRadius.w, In.Rotation);
        float3 V = float3(dot(Rel, ViewRow[0].xyz), dot(Rel, ViewRow[1].xyz), dot(Rel, ViewRow[2].xyz));
        float D = -V.z;
        Out.ToEye = -V;
        Out.Position = float4(V.x * Proj.x, V.y * Proj.y, Proj.z * D + Proj.w, D);
        if (D > Lod.x) Out.Position.z = D * Lod.w;
        Out.Position.xy = Out.Position.xy * Remap.xy + Remap.zw * D;
    }
    return Out;
}
float4 PSMesh(MeshInterp In) : COLOR0
{
    float4 Sample = tex2D(RockTex0, In.Uv);
    float3 V = normalize(In.ToEye);
    float3 N = normalize(In.Normal);
    // Show either side of thin panels, but light only the side facing the viewer.
    N *= dot(N, V) < 0.0 ? -1.0 : 1.0;
    // Relief (see RockRelief): a tangent frame from the view position and UV derivatives; faded out
    // where a pixel spans more than a few metres of rock, since the detail would only shimmer there.
    float3 Pv = -In.ToEye;
    float3 Dx = ddx(Pv), Dy = ddy(Pv);
    float2 Ux = ddx(In.Uv), Uy = ddy(In.Uv);
    float ReliefW = Relief.x * (1.0 - smoothstep(2.0, 8.0, length(Dx)));
    float ReliefCrack = 0.0;
    [branch] if (ReliefW > 0.001)
    {
        float Det = Ux.x * Uy.y - Ux.y * Uy.x;
        float Sign = Det < 0.0 ? -1.0 : 1.0;
        float3 Tu = (Dx * Uy.y - Dy * Ux.y) * Sign;
        float3 T = Tu - N * dot(Tu, N);
        if (abs(Det) > 1.0e-30 && dot(T, T) > 1.0e-4 * dot(Tu, Tu))
        {
            T = normalize(T);
            float3 B = normalize(cross(N, T)) * Sign;
            float2 G = RockRelief(In.Uv * 9.0, In.FadeJitterSolid.y, ReliefCrack);
            N = normalize(N + (T * G.x + B * G.y) * (0.05 * ReliefW));
        }
    }
    float3 L = normalize(SunView.xyz);
    float Light = AsteroidDiffuse(N, L, V) * AsteroidPhase(L, V);
    float3 Albedo = TexTint[0].rgb * lerp(float3(1.0, 1.0, 1.0), Sample.rgb, TexTint[0].w) *
                    (1.0 - 0.35 * ReliefCrack * ReliefW);
    float3 Colour = Albedo * lerp(0.85, 1.1, In.FadeJitterSolid.y) *
                    (AmbientLight.rgb + SunLight.rgb * Light);
    float Alpha = lerp(1.0, Sample.a, TexTint[0].w) * In.FadeJitterSolid.x;
    if (In.FadeJitterSolid.z > 0.5) clip(Alpha - 0.5);
    return float4(saturate(Colour), Alpha);
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
    // Relief: a rock of a few pixels cannot show it, so it grows in with the rock's size (full from
    // about 14 pixels of radius). It bends the normal before the texture is read through it.
    float ReliefW = Relief.x * saturate((PxRadius - 4.0) * 0.1);
    float ReliefCrack = 0.0;
    [branch] if (ReliefW > 0.001)
    {
        float2 G = RockRelief(Turned, Seed, ReliefCrack);
        N = normalize(float3(N.xy + G * (0.05 * ReliefW), N.z));
    }

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
    Albedo *= lerp(0.85, 1.1, In.Info.z) * (0.9 + 0.2 * H3) * (1.0 - 0.35 * ReliefCrack * ReliefW);

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
        Lit = AsteroidDiffuse(N, L, float3(0.0, 0.0, 1.0));
    }
    float Phase = AsteroidPhase(L, float3(0.0, 0.0, 1.0));
    float3 Colour = Albedo * (SunLight.rgb * (Lit * Phase) + AmbientLight.rgb);
    // Solid: a rock of at least min_pixels drops the pixels it covers less than half (its
    // antialiased rim stays), so its inside is opaque; a smaller one stays a soft dot.
    if (In.Info.w > 0.5) // a solid rock (the vertex shader's pass kind)
        clip(Cover - 0.5);
    return float4(saturate(Colour), Cover * In.QFade.w);
}
