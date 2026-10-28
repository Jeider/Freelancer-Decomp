#include "nebula_volume.hlsli"
// Port-only field dust: a faint lit dust volume filling an asteroid field's zone ellipsoid. The
// unresolved small debris between the far rocks (far_rocks.hlsl): a clumpy haze shaped by the field,
// brighter on its sun side, glowing when looking toward the sun through it, cut by a planet's shadow.
// One cheap analytic volume per field: the view ray against the zone ellipsoid, the exact optical
// depth of the smooth profile (1 - |q|^2) (closed form), modulated by a few noise samples (ratio
// estimator), single scattering with the light constant along the ray (taken at the chord midpoint).
// Pass 1 (PSMarch) runs at reduced resolution into its own target (premultiplied rgb, 1 - transmittance);
// pass 2 (PSComposite) upsamples it depth-aware onto the back buffer (ONE, INVSRCALPHA). Up to four
// fields per batch, nearest first within it; batches are composited farthest first.
// See docs/re/asteroid_far_look.md.

sampler2D SceneDepth : register(s0);
sampler3D Noise : register(s1); // R: density fBm 0..1 (percentile-normalised); one tile = 1.0
sampler2D Dust : register(s2);  // the composite's low-resolution march target

// March constants. Fields are 28 registers each, from c8 (the count in c6.x).
float4 ProjZ : register(c0);     // projection z/w rows (RPExLinearDepth)
float4 ViewRect : register(c1);  // the camera viewport in target UV: left, top, width, height
float4 ProjInv : register(c2);   // x 1/ScaleX, y 1/ScaleY, zw half a full-res texel
float4 CamRow[3] : register(c3); // view rotation rows (world axes)
float4 Header : register(c6);    // x field count
float4 SunSphere : register(c7); // xyz sun centre (camera-relative), w radius
float4 Field[112] : register(c8);
// per field (k = 28 * i):
//  +0 centre (camera-relative), w strength        +1..+3 rows (local axis / radius), w: reach 0, reach 1,
//  +4 sigma, edge, clump, steps                       thickness / Ry in unit space (0 = none)
//  +5 noise origin (tiles), w 1 / noise_scale     +6 coverage, softness, clear_radius, max_opacity
//  +7 colour, w brightness                        +8 sun colour, w ambient
//  +9 g, forward_weight, back, has sun            +10 / +11 caster 0 / 1 (camera-relative xyz, radius)
//  +12..+27 up to four exclusion ellipsoids: centre (w enabled), then three unit-space rows

// Composite constants (c0 ProjZ shared).
float4 LowSize : register(c1);   // march target: width, height, 1/width, 1/height
float4 Upsample : register(c2);  // xy half a full-res texel, z relative depth threshold

FFullscreenVertex VSMain(float3 Position : POSITION, float2 TexCoord : TEXCOORD0)
{
    return RPExFullscreenVS(Position, TexCoord);
}

// Fraction of the sun's disc left at P with a sphere in the way (umbra and penumbra); planet_ring.hlsl.
float SphereShadow(float3 P, float4 Caster)
{
    if (Caster.w <= 0.0)
        return 1.0;
    float3 ToCaster = Caster.xyz - P;
    float3 ToSun = SunSphere.xyz - P;
    float SunDistance = length(ToSun);
    float3 SunRay = ToSun / SunDistance;
    if (dot(ToCaster, SunRay) <= 0.0)
        return 1.0;
    float CasterDistance = length(ToCaster);
    float CasterAngle = asin(saturate(Caster.w / CasterDistance));
    float SunAngle = max(asin(saturate(SunSphere.w / SunDistance)), 1.0e-4);
    float Apart = acos(saturate(dot(ToCaster / CasterDistance, SunRay)));
    float Covered = 1.0 - smoothstep(abs(CasterAngle - SunAngle), CasterAngle + SunAngle, Apart);
    Covered *= min(1.0, (CasterAngle * CasterAngle) / (SunAngle * SunAngle));
    return 1.0 - Covered;
}

// SphereShadow cut off beyond the caster's shadow reach, as SolarSunlitAt does (Gap = the distance
// along the sun ray from P past the caster's surface), smoothed over the last 20% of the reach.
float CasterSunlit(float3 P, float3 SunDir, float4 Caster, float Reach)
{
    if (Caster.w <= 0.0)
        return 1.0;
    float3 ToC = Caster.xyz - P;
    float Along = dot(ToC, SunDir);
    if (Along <= 0.0)
        return 1.0;
    float Perp2 = max(dot(ToC, ToC) - Along * Along, 0.0);
    float Gap = Along - sqrt(max(Caster.w * Caster.w - min(Perp2, Caster.w * Caster.w), 0.0));
    if (Gap > Reach)
        return 1.0;
    return lerp(SphereShadow(P, Caster), 1.0, smoothstep(0.8 * Reach, Reach, Gap));
}

float4 PSMarch(FFullscreenVertex In) : COLOR0
{
    float2 ViewUv = (In.TexCoord - ViewRect.xy) / ViewRect.zw;
    if (any(ViewUv < 0.0) || any(ViewUv > 1.0))
        return float4(0.0, 0.0, 0.0, 0.0);

    // The scene depth of the full-resolution texel this pixel stands for (the composite reads the same).
    float Device = tex2Dlod(SceneDepth, float4(In.TexCoord + ProjInv.zw, 0.0, 0.0)).r;

    // View ray: D3D view space at z = 1, then into world axes (the game's view looks down -z).
    float2 Ndc = float2(ViewUv.x * 2.0 - 1.0, 1.0 - ViewUv.y * 2.0);
    float2 ViewXY = Ndc * ProjInv.xy;
    float3 Dir = ViewXY.x * CamRow[0].xyz + ViewXY.y * CamRow[1].xyz - CamRow[2].xyz;
    float DirLength = length(Dir);
    Dir /= DirLength;
    float SceneT = Device < 1.0 ? RPExLinearDepth(Device, ProjZ) * DirLength : 1.0e30;

    float3 Rgb = 0.0;
    float T = 1.0;
    [unroll] for (int I = 0; I < 4; ++I)
    {
        [branch] if (I < Header.x && T > 0.003)
        {
            float4 Centre = Field[I * 28 + 0];
            float4 Row0 = Field[I * 28 + 1];
            float4 Row1 = Field[I * 28 + 2];
            float4 Row2 = Field[I * 28 + 3];
            float2 Span = NebulaZoneSpan(Dir, Centre.xyz, Row0.xyz, Row1.xyz, Row2.xyz, 1.0);
            float T0 = max(Span.x, 0.0);
            float T1 = min(Span.y, SceneT);
            [branch] if (T1 > T0)
            {
                float4 Shape = Field[I * 28 + 4];     // sigma, edge, clump, steps
                float4 NoiseO = Field[I * 28 + 5];    // origin (tiles), 1 / noise_scale
                float4 Cover = Field[I * 28 + 6];     // coverage, softness, clear_radius, max_opacity
                float ClearStart = 0.5 * Cover.z;
                float3 O = NebulaZoneLocal(float3(0.0, 0.0, 0.0), Centre.xyz, Row0.xyz, Row1.xyz, Row2.xyz);
                float3 L = float3(dot(Row0.xyz, Dir), dot(Row1.xyz, Dir), dot(Row2.xyz, Dir));
                float A = dot(L, L);

                // The exact optical depth integral of (1 - |q|^2) over the chord, taken about its
                // midpoint (the odd terms drop out and nothing cancels badly at long range).
                float Tm = 0.5 * (T0 + T1);
                float H = 0.5 * (T1 - T0);
                float3 Pm = O + L * Tm;
                float Integral = max(2.0 * H * (1.0 - dot(Pm, Pm)) - 2.0 * A * H * H * H / 3.0, 0.0);

                // A planetary ring (the CPU marks it with w = 2 in the last exclusion slot): a slab with
                // a hole, soft edges and clumps, not the ellipsoid's profile. The density is sampled
                // evenly along the chord, the optical depth is its mean times the chord.
                float4 RingMark = Field[I * 28 + 24];
                bool Ring = RingMark.w > 1.5;
                float Mean;
                [branch] if (Ring)
                {
                    Integral = T1 - T0;
                    float Sum = 0.0;
                    [loop] for (int Rk = 0; Rk < 8; ++Rk)
                    {
                        if (Rk >= Shape.w)
                            break;
                        float Tk = T0 + (Rk + 0.5) / Shape.w * (T1 - T0);
                        float3 Pk = O + L * Tk;
                        float R = length(Pk.xz);
                        float Radial = smoothstep(RingMark.x, RingMark.x + RingMark.y, R) *
                                       (1.0 - smoothstep(1.0 - RingMark.z, 1.0, R));
                        float N = tex3Dlod(Noise, float4(NoiseO.xyz + Dir * (Tk * NoiseO.w), 0.0)).r;
                        float F = (1.0 - Shape.z) + Shape.z * 2.0 * smoothstep(Cover.x - Cover.y, Cover.x + Cover.y, N);
                        float Slab = 1.0 - smoothstep(0.5 * Row2.w, Row2.w, abs(Pk.y));
                        Sum += Radial * Slab * F * smoothstep(ClearStart, Cover.z, Tk);
                    }
                    Mean = Sum / max(Shape.w, 1.0);
                }
                // The weighted mean of the modulation over the chord (ratio estimator): clump noise,
                // the slab, the clear zone round the camera, the edge exponent.
                else [branch] if (Shape.w > 0.5)
                {
                    float SumP = 0.0;
                    float SumPM = 0.0;
                    [loop] for (int K = 0; K < 8; ++K)
                    {
                        if (K >= Shape.w)
                            break;
                        // Stable midpoint quadrature. Screen-space IGN offsets exposed a
                        // diagonal grain pattern against bright sky; there is no temporal resolve.
                        float Tk = T0 + (K + 0.5) / Shape.w * (T1 - T0);
                        float3 Pk = O + L * Tk;
                        float P = saturate(1.0 - dot(Pk, Pk));
                        float N = tex3Dlod(Noise, float4(NoiseO.xyz + Dir * (Tk * NoiseO.w), 0.0)).r;
                        float F = (1.0 - Shape.z) + Shape.z * 2.0 * smoothstep(Cover.x - Cover.y, Cover.x + Cover.y, N);
                        float Slab = Row2.w > 0.0 ? 1.0 - smoothstep(0.6 * Row2.w, Row2.w, abs(Pk.y)) : 1.0;
                        float M = pow(max(P, 1.0e-4), Shape.y - 1.0) * Slab * F * smoothstep(ClearStart, Cover.z, Tk);
                        [loop] for (int E = 0; E < 4; ++E)
                        {
                            int Base = I * 28 + 12 + E * 4;
                            float4 Hole = Field[Base];
                            if (Hole.w < 0.5)
                                break;
                            float3 H = NebulaZoneLocal(Dir * Tk, Hole.xyz, Field[Base + 1].xyz,
                                                      Field[Base + 2].xyz, Field[Base + 3].xyz);
                            // Keep the interior clear; soften only outside the exclusion boundary.
                            M *= smoothstep(1.0, 1.1, length(H));
                        }
                        SumP += P;
                        SumPM += P * M;
                    }
                    Mean = SumPM / max(SumP, 1.0e-4);
                }
                else
                    Mean = smoothstep(ClearStart, Cover.z, Tm);

                float Tau = Shape.x * Integral * Mean;
                float Alpha = min(1.0 - exp(-Tau), Cover.w) * Centre.w;

                // Light at the chord midpoint.
                float3 Mid = Dir * Tm;
                float4 Colour = Field[I * 28 + 7];
                float4 SunCol = Field[I * 28 + 8];
                float4 Phase = Field[I * 28 + 9];     // g, forward_weight, back, has sun
                float3 Light = SunCol.rgb * 0.6;      // no sun: flat light
                [branch] if (Phase.w > 0.5)
                {
                    float3 SunDir = normalize(SunSphere.xyz - Mid);
                    float CosSun = dot(Dir, SunDir);
                    float PhaseValue = lerp(1.0, NebulaPhaseHG(CosSun, Phase.x), Phase.y) +
                                       Phase.z * pow(saturate(-CosSun), 6.0);
                    // The sun's light through the dust between the midpoint and the zone's edge.
                    float3 Mu = NebulaZoneLocal(Mid, Centre.xyz, Row0.xyz, Row1.xyz, Row2.xyz);
                    float3 Su = float3(dot(Row0.xyz, SunDir), dot(Row1.xyz, SunDir), dot(Row2.xyz, SunDir));
                    float SA = max(dot(Su, Su), 1.0e-12);
                    float SB = dot(Mu, Su);
                    float SC = dot(Mu, Mu) - 1.0;
                    float LSun = max((-SB + sqrt(max(SB * SB - SA * SC, 0.0))) / SA, 0.0);
                    float TSun = exp(-Shape.x * LSun * 0.5);
                    float Sunlit = CasterSunlit(Mid, SunDir, Field[I * 28 + 10], Row0.w) *
                                   CasterSunlit(Mid, SunDir, Field[I * 28 + 11], Row1.w);
                    Light = SunCol.rgb * (Sunlit * TSun * PhaseValue * Colour.w + SunCol.w);
                }
                Rgb += T * Alpha * Colour.rgb * Light;
                T *= 1.0 - Alpha;
            }
        }
    }
    return float4(Rgb, 1.0 - T);
}

float LinearDepthAt(float2 Uv)
{
    return RPExLinearDepth(tex2Dlod(SceneDepth, float4(Uv, 0.0, 0.0)).r, ProjZ);
}

// The depth-aware upsample of nebula_composite.hlsl: bilinear where the four low-resolution texels
// around this pixel see about the same depth; across a depth edge the best matching one.
float4 PSComposite(float2 TexCoord : TEXCOORD0) : COLOR0
{
    float Depth = LinearDepthAt(TexCoord);

    float2 Low = TexCoord * LowSize.xy - 0.5;
    float2 Base = floor(Low);
    float2 Uv00 = (Base + float2(0.5, 0.5)) * LowSize.zw;
    float2 Uv10 = Uv00 + float2(LowSize.z, 0.0);
    float2 Uv01 = Uv00 + float2(0.0, LowSize.w);
    float2 Uv11 = Uv00 + LowSize.zw;

    float D00 = LinearDepthAt(Uv00 + Upsample.xy);
    float D10 = LinearDepthAt(Uv10 + Upsample.xy);
    float D01 = LinearDepthAt(Uv01 + Upsample.xy);
    float D11 = LinearDepthAt(Uv11 + Upsample.xy);
    float4 Diff = abs(float4(D00, D10, D01, D11) - Depth) / max(Depth, 1.0e-3);
    float MaxDiff = max(max(Diff.x, Diff.y), max(Diff.z, Diff.w));

    if (MaxDiff < Upsample.z)
    {
        // Smooth: four bilinear taps around the pixel (about a 3x3 low-res tent) where each tap
        // sees this pixel's depth too. This smooths the reduced-resolution volume without
        // spreading its density across opaque depth edges.
        float2 R = LowSize.zw * 0.75;
        float4 TapDepth = float4(LinearDepthAt(TexCoord + float2(-R.x, -R.y)),
                                 LinearDepthAt(TexCoord + float2(R.x, -R.y)),
                                 LinearDepthAt(TexCoord + float2(-R.x, R.y)),
                                 LinearDepthAt(TexCoord + float2(R.x, R.y)));
        float4 TapDiff = abs(TapDepth - Depth) / max(Depth, 1.0e-3);
        if (max(max(TapDiff.x, TapDiff.y), max(TapDiff.z, TapDiff.w)) < Upsample.z)
            return 0.25 * (tex2Dlod(Dust, float4(TexCoord + float2(-R.x, -R.y), 0.0, 0.0)) +
                           tex2Dlod(Dust, float4(TexCoord + float2(R.x, -R.y), 0.0, 0.0)) +
                           tex2Dlod(Dust, float4(TexCoord + float2(-R.x, R.y), 0.0, 0.0)) +
                           tex2Dlod(Dust, float4(TexCoord + float2(R.x, R.y), 0.0, 0.0)));
        return tex2Dlod(Dust, float4(TexCoord, 0.0, 0.0));
    }

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
        BestUv = Uv11;
    return tex2Dlod(Dust, float4(BestUv, 0.0, 0.0));
}
