// Player quantum corridor: a turbulent emissive volume and GPU light fragments.
float4 ViewRow[3] : register(c0);
float4 ProjectionRow[4] : register(c3);
float4 Remap : register(c7);
float4 LaneRow[3] : register(c8);
float4 VertexTravel : register(c11);
float4 VertexDepthRange : register(c12);
struct Vertex { float3 Position:POSITION0; float4 Color:COLOR0; float2 UV:TEXCOORD0; };
struct Interp
{
    float4 Position:POSITION0;
    float2 UV:TEXCOORD0;
    float4 CameraBounds:TEXCOORD1;
    float2 Radial:TEXCOORD2;
    float3 Local:TEXCOORD3;
    float3 Detail:TEXCOORD4; // fragment marker, lifetime envelope, random seed
    float3 Focus:TEXCOORD5; // flight axis in screen UV, positive W when facing it
};
Interp VSMain(Vertex In)
{
    Interp Out;
    float3 P = In.Position;
    Out.Detail = float3(0, 1, 0);
    [branch] if (In.Color.a < 0.5)
    {
        float Seed = In.Position.z;
        float Forward = 2600.0 - frac(Seed + VertexTravel.x * 0.5) * 3200.0;
        float2 Tangent = normalize(float2(-P.y, P.x));
        P.xy += Tangent * In.UV.x * (0.24 + Seed * 0.55);
        P.z = -Forward + In.UV.y * (12.0 + Seed * 45.0);
        Out.Detail = float3(1, smoothstep(-500.0, -150.0, Forward) *
            (1.0 - smoothstep(2100.0, 2550.0, Forward)), Seed);
    }
    float4 Local = float4(P, 1.0);
    float4 World = float4(dot(Local, LaneRow[0]), dot(Local, LaneRow[1]), dot(Local, LaneRow[2]), 1.0);
    float4 View = float4(dot(World, ViewRow[0]), dot(World, ViewRow[1]), -dot(World, ViewRow[2]), 1.0);
    Out.Position = float4(dot(View, ProjectionRow[0]), dot(View, ProjectionRow[1]),
                          dot(View, ProjectionRow[2]), dot(View, ProjectionRow[3]));
    Out.CameraBounds = Out.Position.w * 1.00001 + float4(Out.Position.xy, -Out.Position.xy);
    Out.Position.xy = Out.Position.xy * Remap.xy + Remap.zw * Out.Position.w;
    Out.Position.z = Out.Position.z * (VertexDepthRange.w - VertexDepthRange.z) +
                     VertexDepthRange.z * Out.Position.w;
    Out.UV = In.UV;
    Out.Local = P;
    float3 N = float3(In.Position.xy / 165.0, 0);
    float3 WorldN = float3(dot(N, LaneRow[0].xyz), dot(N, LaneRow[1].xyz), dot(N, LaneRow[2].xyz));
    Out.Radial = float2(dot(WorldN, ViewRow[0].xyz), -dot(WorldN, ViewRow[1].xyz));
    float3 AxisWorld = -float3(LaneRow[0].z, LaneRow[1].z, LaneRow[2].z);
    float4 AxisView = float4(dot(AxisWorld, ViewRow[0].xyz), dot(AxisWorld, ViewRow[1].xyz),
                           -dot(AxisWorld, ViewRow[2].xyz), 0);
    float4 AxisClip = float4(dot(AxisView, ProjectionRow[0]), dot(AxisView, ProjectionRow[1]),
                            dot(AxisView, ProjectionRow[2]), dot(AxisView, ProjectionRow[3]));
    float2 AxisNDC = AxisClip.xy / max(AxisClip.w, 0.001);
    Out.Focus = float3((AxisNDC * Remap.xy + Remap.zw) * float2(0.5, -0.5) + 0.5, AxisClip.w);
    return Out;
}

float4 Travel : register(c0); // distance/1600, seconds, envelope, legacy entrance pulse
float4 Palette : register(c1); // resolved gate-tunnel body colour, style enabled
float4 Warp : register(c2); // inverse target dimensions, refraction strength, reserved
float4 Bounds : register(c3); // camera UV min.xy / max.zw, texel centres
float4 DepthRange : register(c4); // near, far, viewport depth min/max
float4 Transition : register(c5); // entry age seconds, exit progress, stopping, reserved
float4 Style : register(c6); // accent RGB; 0 generic, 1 edge, 2 crow, 3 barrier, 4 walker, 5 dark
float4 Variation : register(c7); // fixed per-route noise offset XYZ and event phase
sampler2D SceneColor : register(s0);
sampler2D SceneDepth : register(s1);
sampler3D Noise : register(s2); // deterministic smooth periodic 64^3 RGBA

// Visibility tuning preserves the detailed volume while leaving the world readable.
// Emission and absorption are separate: bright filaments need not hide the scenery.
static const float VolumeCoverage = 0.30;
static const float RefractionVisibility = 0.45;

float StyleIs(float Mode)
{
    return Palette.w * (1.0 - step(0.5, abs(Style.w - Mode)));
}

// Preserve light intensity and white highlights; direct RGB multiplication would
// lose orange/green styles underneath the original blue spectrum.
float3 StyleColor(float3 Original)
{
    float Peak = max(Original.r, max(Original.g, Original.b));
    float White = saturate(min(Original.r, min(Original.g, Original.b)) / max(Peak, 0.0001));
    float3 Tint = lerp(Palette.rgb, Style.rgb, saturate(White + Peak * 0.22));
    float3 Recolored = Peak * lerp(Tint, float3(1, 1, 1), White * White * White * 0.78);
    return lerp(Original, Recolored, Palette.w);
}

float3 FlowPosition(float3 P)
{
    // Integer frequency ratios preserve both CPU wraps (phase1024, time96).
    float T = frac(Travel.y / 96.0);
    float Edge = StyleIs(1), Walker = StyleIs(4), Dark = StyleIs(5);
    float3 Q = float3(P.xy * (1.0 + Edge * 0.15 + Dark * 0.10) / 950.0,
                     (-P.z / 6400.0 + frac(Travel.x / 4.0)) * (1.0 + Walker));
    return Q + T * float3(1, -1, 2) + Variation.xyz * Palette.w;
}
float4 SampleFlow(float3 P)
{
    float4 Large = tex3Dlod(Noise, float4(P, 0));
    float Crow = StyleIs(2), Barrier = StyleIs(3), Dark = StyleIs(5);
    float3 Q = P + (Large.gbg - 0.5) * (0.22 + Crow * 0.10 + Barrier * 0.06 - Dark * 0.06);
    float4 Middle = tex3Dlod(Noise, float4(Q * 2.0 + float3(0.17, 0.37, 0.61), 0));
    float Fine = tex3Dlod(Noise, float4(Q * float3(8, 8, 2) + 0.23, 0)).a;
    float Broad = 0.62 + Crow * 0.13 - Dark * 0.17;
    return float4(Large.r * Broad + Middle.r * (1.0 - Broad), Middle.a, Fine, Large.g - Large.b);
}

float4 PSMain(Interp In, float2 Pixel:VPOS):COLOR0
{
    clip(In.CameraBounds);
    // Derivatives precede varying control flow (Shader Model3).
    float PixelFootprint = length(ddx(In.Local)) + length(ddy(In.Local));
    float FragmentAA = max(fwidth(In.UV.x), 0.04);
    [branch] if (In.Detail.x > 0.5)
    {
        float Across = In.UV.x / max(0.30, FragmentAA * 0.65);
        float Core = exp2(-Across * Across * 2.0) * min(1.0, 0.30 / (FragmentAA * 0.65));
        float Halo = exp2(-In.UV.x * In.UV.x * 4.0) * 0.15;
        float Along = pow(saturate(1.0 - abs(In.UV.y)), 0.65);
        float Energy = (Core + Halo) * Along * In.Detail.y * Travel.z;
        float3 C = lerp(float3(0.28, 0.72, 1.0), float3(0.85, 0.96, 1.0), In.Detail.z);
        // Walker's small warm glints have different phases per fragment, not a screen flash.
        float Ember = 1.0 + StyleIs(4) * 0.25 * pow(saturate(sin(
            (Travel.y / 96.0 * 32.0 + In.Detail.z * 3.0 + Variation.w) * 6.28318530718)), 6.0);
        return float4(StyleColor(C) * Energy * 0.85 * Ember, Energy * 0.08);
    }
    float3 Ray = normalize(In.Local);
    float Transverse = max(length(Ray.xy), 0.012);
    float FineFade = 1.0 - smoothstep(8.0, 65.0, PixelFootprint);
    float3 Accumulated = 0;
    float Transmission = 1;
    float Edge = StyleIs(1), Crow = StyleIs(2), Barrier = StyleIs(3);
    float Walker = StyleIs(4), Dark = StyleIs(5);
    // A short local swell every 12 seconds, offset per route. Only selected folds
    // brighten; volume opacity and background visibility never pulse with it.
    float Surge = pow(saturate(sin((Travel.y / 96.0 * 8.0 + Variation.w) * 6.28318530718)), 12.0);
    // Radial stratification integrates emission and absorption through 3D thickness.
    [loop] for (int I = 0; I < 16; ++I)
    {
        float R = 178.0 + (I + 0.5) * 27.0;
        float3 P = Ray * (R / Transverse);
        float3 Q = FlowPosition(P);
        float4 F = SampleFlow(Q);
        float Far = 1.0 - smoothstep(5000.0, 9400.0, abs(P.z));
        float Shell = smoothstep(178.0, 230.0, R) * (1.0 - smoothstep(480.0, 610.0, R));
        float Density = smoothstep(0.40, 0.63, F.x + (F.z - 0.5) * 0.055 * FineFade) * Shell * Far;
        float Alpha = 1.0 - exp2(-Density * min(27.0 / Transverse, 150.0) * 0.012);
        float LitSample = tex3Dlod(Noise, float4(Q + float3(0.025, -0.035, -0.045), 0)).r;
        float Lighting = saturate(0.48 + (LitSample - F.x) * 5.0);
        float Membrane = pow(saturate(1.0 - abs(F.x - 0.515) * (22.0 + Edge * 8.0 + Dark * 12.0 - Crow * 5.0)), 3.0);
        float Veins = pow(saturate(1.0 - abs(F.y - 0.52) * 15.0), 5.0) * Membrane * FineFade;
        float Fibres = pow(saturate((F.z - 0.43) * 3.4), 3.0) * FineFade;
        float3 Color = lerp(float3(0.003, 0.015, 0.045), float3(0.08, 0.55, 0.68), Lighting * Lighting) * 0.40;
        Color += Membrane * (0.40 + F.z * 0.55) * float3(0.20, 0.68, 0.78) * 0.60;
        Color += (Veins * 1.4 + Fibres * Membrane * 0.35) * float3(0.65, 0.92, 1.0) * 0.85;
        // Emerald branches, blue flowing curtains, silver interference sheets,
        // amber travelling knots, and graphite fractures share the same volume.
        float Branch = pow(saturate((F.y - 0.48) * 4.0), 3.0) * Membrane;
        float Packet = pow(saturate(sin((Q.z * 2.0 + Variation.w) * 6.28318530718)), 8.0);
        float Interference = 0.5 + 0.5 * sin((Q.z + Q.x * 2.0 - Q.y + Travel.y / 96.0 * 4.0) * 6.28318530718);
        float Accent = Edge * Branch * (0.12 + Surge * 0.38) + Crow * Membrane * Surge * 0.08;
        Accent += Barrier * Veins * Interference * 0.20;
        Accent += Walker * Packet * Membrane * (0.10 + Surge * 0.30);
        Accent += Dark * Branch * Surge * 0.38;
        Color += Accent * float3(0.60, 0.90, 1.0) * FineFade;
        Color *= 1.0 - Dark * 0.22;
        Color *= 1.35;
        Accumulated += Transmission * Alpha * Color;
        Transmission *= 1.0 - Alpha;
    }
    float Forward = smoothstep(0.0, 0.35, -Ray.z);
    float Slope = length(Ray.xy) / max(-Ray.z, 0.001);
    float3 FocusP = FlowPosition(Ray * min(850.0 / max(-Ray.z, 0.01), 9400.0));
    float4 Front = SampleFlow(FocusP);
    float Halo = exp2(-Slope * Slope / 0.035) * Forward;
    float Aperture = exp2(-pow((Slope - 0.22 - (Front.x - 0.5) * 0.22) / 0.055, 2.0));
    Aperture *= Forward * (0.18 + smoothstep(0.42, 0.65, Front.z) * 0.42);
    float Breakup = pow(saturate(1.0 - abs(Front.y - 0.5) * 18.0), 5.0);
    Accumulated += (Halo * 0.09 + Aperture * 0.16) * float3(0.10, 0.64, 0.92);
    Accumulated += Aperture * Breakup * 0.34 * float3(0.60, 0.92, 1.0);
    // Screen-oriented optical glare follows the projected flight axis, including turns.
    // Its wide halo is analytic, without a full-frame blur or feedback accumulation.
    float2 GlareUV = ((Pixel + 0.5) * Warp.xy - In.Focus.xy) * float2(Warp.y / max(Warp.x, 0.000001), 1);
    float R2 = dot(GlareUV, GlareUV);
    float HotCore = exp2(-R2 / 0.000035);
    float Bloom = exp2(-R2 / 0.0035) * 0.34 + exp2(-R2 / 0.018) * 0.075;
    float Flare = exp2(-abs(GlareUV.x) * 7.0 - abs(GlareUV.y) * 340.0) * 0.16;
    float Needle = exp2(-abs(GlareUV.x) * 4.0 - GlareUV.y * GlareUV.y / 0.0000015) * 0.08;
    Accumulated += step(0.0000001, Warp.x) * step(0.001, In.Focus.z) * (HotCore * float3(0.85, 1.05, 1.15) +
        Bloom * float3(0.15, 0.72, 0.90) + (Flare + Needle) * float3(0.58, 0.88, 1.0));
    float Opacity = max(1.0 - Transmission, Halo * 0.24);
    // One opening pressure wave and a collapsing exit wake, not periodic rings.
    float Opening = smoothstep(0.08, 0.22, Transition.x) *
                    (1.0 - smoothstep(0.38, 0.90, Transition.x)) * (1.0 - Transition.z);
    float OpeningRadius = 0.035 + pow(saturate((Transition.x - 0.10) / 0.70), 1.7) * 2.2;
    float OpeningEdge = exp2(-pow((Slope - OpeningRadius - (Front.x - 0.5) * 0.30) / 0.035, 2.0));
    OpeningEdge *= 0.30 + saturate((Front.y - 0.34) * 2.0);
    float Wake = sin(saturate(Transition.y) * 3.14159265) * Transition.z;
    Accumulated += Forward * Opening * (OpeningEdge * float3(0.48, 0.88, 1.0) + Halo * float3(0.18, 0.48, 0.70));
    Accumulated += Wake * Halo * float3(0.08, 0.36, 0.48);
    return float4(StyleColor(Accumulated) * Travel.z, saturate(Opacity) * VolumeCoverage * Travel.z);
}

float BackgroundWeight(float2 UV)
{
    float D = tex2Dlod(SceneDepth, float4(UV, 0, 0)).r;
    if (D >= 0.99999994) return 1.0;
    if (D > DepthRange.w + 0.00000012) return 0.0;
    float Z = saturate((D - DepthRange.z) / max(DepthRange.w - DepthRange.z, 0.000001));
    float Distance = DepthRange.x * DepthRange.y / max(DepthRange.y - Z * (DepthRange.y - DepthRange.x), 0.001);
    return smoothstep(500.0, 1500.0, Distance);
}
float4 PSWarp(Interp In, float2 Pixel:VPOS):COLOR0
{
    clip(In.CameraBounds);
    float2 UV = (Pixel + 0.5) * Warp.xy;
    float4 Base = tex2Dlod(SceneColor, float4(UV, 0, 0));
    float Weight = BackgroundWeight(UV);
    [branch] if (Weight <= 0.0 || Travel.z <= 0.0 || Warp.z <= 0.0) return Base;
    float3 Ray = normalize(In.Local);
    float3 P = Ray * min(300.0 / max(length(Ray.xy), 0.015), 8000.0);
    float4 Flow = SampleFlow(FlowPosition(P));
    float Edge = min(min(UV.x - Bounds.x, Bounds.z - UV.x), min(UV.y - Bounds.y, Bounds.w - UV.y));
    float Fade = smoothstep(0.0, 0.035, Edge);
    float Lens = 0.32 + (Flow.x - 0.5) * 1.8;
    float2 Shear = In.Radial * Lens + float2(-In.Radial.y, In.Radial.x) * Flow.w * 0.65;
    float2 Offset = Shear * float2(Warp.x / Warp.y, 1) * Warp.z * RefractionVisibility * Travel.z * Fade;
    float2 Candidate = clamp(UV + Offset * Weight, Bounds.xy, Bounds.zw);
    float2 Texel = Warp.xy;
    float Source = min(BackgroundWeight(Candidate + Texel), BackgroundWeight(Candidate - Texel));
    Source = min(Source, BackgroundWeight(Candidate + float2(Texel.x, -Texel.y)));
    Source = min(Source, BackgroundWeight(Candidate + float2(-Texel.x, Texel.y)));
    [branch] if (Source < 0.999) return Base;
    return tex2Dlod(SceneColor, float4(Candidate, 0, 0));
}
