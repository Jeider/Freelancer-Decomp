#include "common.hlsli"
// Port-only solar corona: the sun's own light streaming off its disc, drawn in place of the
// heavy attached ALE (fx\mod\*_sun.ale). One additive fullscreen pass per visible sun, facing
// the player by construction. Streamers are 3D value noise over the direction around the disc
// (no seam at any angle) and the radius, drifting outwards and slowly evolving, so the crown
// never repeats. Geometry in front of the sun hides it, as it hides the depth rays.
sampler2D SceneDepth : register(s0);
float4 Sun : register(c0);         // viewport UV, disc radius (height units), strength
float4 Tint : register(c1);        // RGB, width/height
float4 SourceDepth : register(c2); // solar front depth, world viewport max depth
float4 Motion : register(c3);      // time (s), per-sun seed, reach (disc radii), streamer contrast

FFullscreenVertex VSMain(float3 Position : POSITION, float2 Uv : TEXCOORD0)
{ return RPExFullscreenVS(Position, Uv); }

float Sky(float2 Uv)
{
    float Depth = tex2Dlod(SceneDepth, float4(Uv, 0, 0)).r;
    if (Depth >= 0.99999994) return 1;
    if (Depth > SourceDepth.y + 0.00000012) return 0; // cockpit depth partition
    return step(SourceDepth.x, Depth);                 // only geometry in front of the sun hides it
}

float Hash(float3 P)
{
    P = frac(P * 0.1031);
    P += dot(P, P.yzx + 33.33);
    return frac((P.x + P.y) * P.z);
}

float Noise(float3 P)
{
    float3 I = floor(P), F = frac(P);
    float3 U = F * F * (3.0 - 2.0 * F);
    return lerp(lerp(lerp(Hash(I), Hash(I + float3(1, 0, 0)), U.x),
                     lerp(Hash(I + float3(0, 1, 0)), Hash(I + float3(1, 1, 0)), U.x), U.y),
                lerp(lerp(Hash(I + float3(0, 0, 1)), Hash(I + float3(1, 0, 1)), U.x),
                     lerp(Hash(I + float3(0, 1, 1)), Hash(I + float3(1, 1, 1)), U.x), U.y), U.z);
}

float4 PSMain(FFullscreenVertex In) : COLOR0
{
    float2 Metric = (In.TexCoord - Sun.xy) * float2(Tint.w, 1);
    float R = length(Metric) / max(Sun.z, 0.0005); // in disc radii
    [branch] if (R > Motion.z || R < 0.4) return 0;
    if (Sky(In.TexCoord) < 0.5) return 0;

    float2 Dir = Metric / max(length(Metric), 1e-6);
    float T = Motion.x * 0.05;
    float3 Seed = float3(Motion.y, Motion.y * 1.7, 0);
    // Streamers: fine angular structure, stretched along the radius, flowing out.
    float Flow = log2(R) * 1.4 - T * 0.8;
    float S = Noise(float3(Dir * 6.0, Flow) + Seed) * 0.6
            + Noise(float3(Dir * 13.0, Flow * 1.6 + 7.0) + Seed) * 0.3
            + Noise(float3(Dir * 27.0, Flow * 2.2 + 3.0 + T) + Seed) * 0.1;
    // Broad, slowly turning lobes: the crown is uneven and changes over minutes.
    float Lobes = Noise(float3(Dir * 2.0, T * 0.35) + Seed * 2.3);
    float Streamers = pow(saturate(S * (0.6 + 0.8 * Lobes)), Motion.w);

    // Grows out of the core with no gap (the glow is already white over the disc), falls off
    // away from the limb, and reaches zero at the edge of its reach.
    float Limb = smoothstep(0.4, 1.0, R);
    float Falloff = exp2(-max(R - 1.0, 0.0) * 2.6) * saturate(1.0 - (R - 1.0) / (Motion.z - 1.0));
    // Streamers ride on a faint even haze; near the limb they blend into it.
    float Glow = Limb * Falloff * (0.15 + 1.2 * Streamers * smoothstep(0.8, 1.3, R));
    return float4(Tint.rgb * Glow * Sun.w, 0);
}
