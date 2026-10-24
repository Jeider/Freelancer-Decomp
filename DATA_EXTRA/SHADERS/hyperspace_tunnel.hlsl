// Shade the original gate-tunnel strips. All motion comes from their existing UV scroll.
float4 ViewRow[3] : register(c0);
float4 ProjectionRow[4] : register(c3);
float4 Remap : register(c7);
struct Vertex
{
    float3 Position : POSITION0;
    float4 Color : COLOR0;
    float2 UV : TEXCOORD0;
};
struct Interp
{
    float4 Position : POSITION0;
    float4 Color : COLOR0;
    float2 UV : TEXCOORD0;
    float4 CameraBounds : TEXCOORD1;
};
Interp VSMain(Vertex In)
{
    Interp Out;
    float4 World = float4(In.Position, 1.0);
    float4 View = float4(dot(World, ViewRow[0]), dot(World, ViewRow[1]),
                        -dot(World, ViewRow[2]), 1.0);
    Out.Position = float4(dot(View, ProjectionRow[0]), dot(View, ProjectionRow[1]),
                          dot(View, ProjectionRow[2]), dot(View, ProjectionRow[3]));
    // Ex passes use the full target viewport. Preserve the original camera clipping
    // before remapping into its letterboxed rectangle, including partially visible strips.
    // Tiny relative tolerance keeps boundary pixels from disappearing through interpolation
    // roundoff (D3D9 pixel centres lie on the viewport's top/left boundary).
    Out.CameraBounds = Out.Position.w * 1.00001 + float4(Out.Position.xy, -Out.Position.xy);
    Out.Position.xy = Out.Position.xy * Remap.xy + Remap.zw * Out.Position.w;
    Out.Color = In.Color;
    Out.UV = In.UV;
    return Out;
}
sampler2D TunnelTexture : register(s0);
sampler3D Noise : register(s1);
float4 LayerParams : register(c0); // x: original layer index (second uses premultiplied colour)
float N(float3 P) { return tex3D(Noise, P).r; }
float4 PSMain(Interp In) : COLOR0
{
    clip(In.CameraBounds);
    // Cylindrical coordinates close the angular seam even while the original U scrolls.
    // No elapsed-time offsets, screen-space noise, or independently moving shells.
    float Angle = In.UV.x * 6.28318530718;
    // Two spatial warp scales create folded flowing sheets rather than uniform spokes.
    // The original scrolling coordinates remain the only source of movement.
    float Curl = Angle + 0.24 * sin(In.UV.y * 1.7 + sin(Angle * 3.0));
    float3 P = float3(cos(Curl) * 0.17, sin(Curl) * 0.17, In.UV.y * 0.24);
    float3 Warp = float3(N(P * 0.7), N(P * 0.7 + 0.37), N(P * 0.7 + 0.71)) - 0.5;
    float3 Q = P + Warp * 0.14;
    float3 Fold = float3(N(Q * 1.3 + 0.19), N(Q * 1.3 + 0.53), N(Q * 1.3 + 0.83)) - 0.5;
    Q += Fold * 0.065;
    float Cloud = N(Q) * 0.65 + N(Q * 2.03 + 0.13) * 0.25 + N(Q * 4.07) * 0.10;
    float Density = smoothstep(0.30, 0.70, Cloud);
    float DetailFootprint = length(ddx(Q)) + length(ddy(Q));
    float DetailFade = 1.0 - smoothstep(0.012, 0.065, DetailFootprint);
    float Wisps = pow(saturate(1.0 - abs(Cloud - 0.53) * 9.0), 3.0) * DetailFade;
    // Cloud detail follows the original geometry, UV motion and endpoint fade.
    float Violet = smoothstep(0.09, 0.35, Fold.x) * 0.32;
    float3 Shadow = lerp(float3(0.008, 0.025, 0.085), float3(0.12, 0.035, 0.24), Violet);
    float3 Color = lerp(Shadow, float3(0.12, 0.43, 0.90), Density);
    Color += Wisps * float3(0.48, 0.72, 0.92);
    Color += pow(saturate(Density), 5.0) * float3(0.32, 0.36, 0.4);
    // Lose fine structure toward the vanishing point, into luminous blue depth haze.
    float DepthHaze = 1.0 - smoothstep(0.0, 0.22, In.Color.a);
    Color = lerp(Color, float3(0.18, 0.38, 0.68), DepthHaze * 0.55);
    // The original per-vertex palette includes layer colour and animated colour curves.
    // Recolour luminance instead of multiplying blue by green/red (which would go dark).
    float Peak = max(In.Color.r, max(In.Color.g, In.Color.b));
    float3 Tint = Peak > 0.001 ? In.Color.rgb / Peak : float3(1.0, 1.0, 1.0);
    float Luminance = dot(Color, float3(0.2126, 0.7152, 0.0722));
    Color = Luminance * (0.16 + Tint * 1.25);
    Color = saturate(Color / (1.0 + Color * 0.2));
    float Coverage = smoothstep(0.0, 0.20, In.Color.a);
    float Alpha = Coverage * (LayerParams.x < 0.5 ? 0.45 : 0.18 * Density + 0.05 * Wisps);
    // Match the original ONE/INVSRCALPHA blend of layer 1 without leaking light at the ends.
    return float4(LayerParams.x < 0.5 ? Color : Color * Alpha, Alpha);
}

// Short launch overlay, driven by the existing jump-state clock, never wall-clock time.
// It disappears completely during cruise. No sampled scene colour or extra textures.
Interp VSLaunch(Vertex In)
{
    Interp Out;
    Out.Position = float4(In.Position.xy * Remap.xy + Remap.zw, 0.0, 1.0);
    Out.CameraBounds = 1.00001 + float4(In.Position.xy, -In.Position.xy);
    Out.Color = In.Color;
    Out.UV = In.UV;
    return Out;
}
float4 LaunchParams : register(c0); // build, burst, viewport aspect, post-entry progress
float4 TransitionStyle : register(c1); // exit mode, tunnel RGB tint
float LaunchHash(float X) { return frac(sin(X * 127.1 + 311.7) * 43758.5453); }
float LaunchStars(float2 P, float Build, float After, float Lanes, float Seed)
{
    float Radius = length(P);
    float Angle = atan2(P.y, P.x) / 6.28318530718 + 0.5;
    float Lane = floor(Angle * Lanes);
    float H = LaunchHash(Lane + Seed);
    float H2 = LaunchHash(Lane + Seed + 83.7);
    float Theta = ((Lane + 0.2 + H * 0.6) / Lanes - 0.5) * 6.28318530718;
    float2 Dir = float2(cos(Theta), sin(Theta));
    float Along = dot(P, Dir);
    float Across = abs(P.x * Dir.y - P.y * Dir.x);
    // Stable individual stars first gather toward the flight axis, then stretch outward.
    float Head = (0.10 + sqrt(H2) * 1.25) * (1.0 - Build * 0.22) + After * (1.8 + H);
    float Tail = max(0.035, Head - 0.003 - pow(Build, 5.0) * (0.18 + H * 0.68));
    float Pixel = max(length(float2(ddx(Across), ddy(Across))), 0.0005);
    float Width = 0.00065 + H * 0.0007;
    float FilterWidth = max(Width, Pixel * 0.7);
    float Core = exp2(-pow(Across / FilterWidth, 2.0)) * min(1.0, Width / FilterWidth);
    float Halo = exp2(-pow(Across / (FilterWidth * 3.5), 2.0)) * 0.14;
    float Edge = max(fwidth(Along), 0.001);
    float Segment = smoothstep(Tail - Edge, Tail + Edge, Along) *
                    (1.0 - smoothstep(Head - Edge, Head + Edge, Along));
    // A sparse star field appears immediately at jump-out, then fills in and stretches.
    float Gather = lerp(0.32, 1.0, smoothstep(H * 0.58, H * 0.58 + 0.22, Build));
    return (Core + Halo) * Segment * Gather * (0.5 + H2 * 0.5) *
           smoothstep(0.025, 0.08, Radius);
}
float4 ExitWave(float2 P, float T)
{
    float Radius = length(P);
    float Angle = atan2(P.y, P.x);
    // Expanding, softly folded wavefront: the centre clears first into normal space.
    float WaveRadius = 0.035 + 1.65 * pow(T, 0.72);
    float Fold = sin(Angle * 7.0 + T * 3.0) * sin(Angle * 11.0 - T * 2.0);
    float Width = 0.035 + T * 0.09;
    float D = Radius - WaveRadius - Fold * Width * 0.32;
    float Rim = exp2(-pow(D / Width, 2.0));
    float Echo = exp2(-pow((D + 0.11 + T * 0.08) / (Width * 1.5), 2.0)) * 0.28;
    float Glow = exp2(-Radius * Radius / (0.012 + T * 0.025)) * (1.0 - T);
    // Residual warp trails brake into points and disappear, rather than accelerating again.
    float Recede = 1.0 - smoothstep(0.0, 0.65, T);
    float Stars = LaunchStars(P, Recede, 0.0, 151.0, 3.0);
    Stars += LaunchStars(P, Recede, 0.0, 211.0, 117.0) * 0.65;
    Stars *= pow(1.0 - T, 3.0) * 0.40;
    float3 Tint = lerp(float3(1.0, 1.0, 1.0), saturate(TransitionStyle.yzw), 0.60);
    float3 Color = Tint * ((Rim + Echo) * 0.52 + Glow * 0.24 + Stars);
    float Envelope = smoothstep(0.0, 0.045, T) * (1.0 - smoothstep(0.35, 1.0, T));
    return float4(saturate(Color), Envelope);
}
float4 PSLaunch(Interp In) : COLOR0
{
    clip(In.CameraBounds);
    float2 P = (In.UV - 0.5) * float2(LaunchParams.z, 1.0);
    if (TransitionStyle.x > 0.5)
        return ExitWave(P, saturate(LaunchParams.x));
    float Build = saturate(LaunchParams.x);
    float Burst = saturate(LaunchParams.y);
    float After = saturate(LaunchParams.w);
    float Stars = LaunchStars(P, Build, After, 151.0, 3.0);
    Stars += LaunchStars(P, Build, After, 211.0, 117.0) * 0.8;
    Stars += LaunchStars(P, Build, After, 283.0, 259.0) * 0.6;
    Stars *= 1.0 - smoothstep(0.08, 0.90, After);
    float Radius = length(P);
    float Charge = pow(Build, 8.0) * (1.0 - After);
    float Glow = exp2(-Radius * Radius / (0.006 + Burst * 0.045));
    float RingRadius = 0.025 + After * 1.3;
    float Ring = exp2(-pow((Radius - RingRadius) / (0.025 + After * 0.14), 2.0));
    float3 Color = Stars * float3(0.73, 0.86, 1.0);
    Color += Glow * (Charge * 0.13 + Burst * 0.65) * float3(0.65, 0.84, 1.0);
    Color += Ring * Burst * 0.23 * float3(0.22, 0.55, 1.0);
    Color += Burst * float3(0.025, 0.045, 0.075);
    // Additive light veil: scene and ship remain readable through the brief burst.
    float Envelope = smoothstep(0.0, 0.035, Build) * (1.0 - smoothstep(0.7, 1.0, After));
    return float4(saturate(Color), Envelope);
}
