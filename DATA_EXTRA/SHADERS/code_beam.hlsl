// One atlas lookup, one additive pass. TEXCOORD1 carries beam-local animation coordinates.
// Authored vertex colours/brightness and atlas head/trail profiles remain authoritative.
row_major float4x4 WorldView : register(c0);
row_major float4x4 Projection : register(c4);
struct VSIn { float3 Position : POSITION; float4 Colour : COLOR0; float2 UV : TEXCOORD0; float4 Flow : TEXCOORD1; };
struct VSOut {
    float4 Position : POSITION;
    float4 Colour : COLOR0;
    float2 UV : TEXCOORD0;
    float ViewZ : TEXCOORD1;
    float4 Flow : TEXCOORD2;
};
VSOut VSMain(VSIn In)
{
    VSOut Out;
    float4 View = mul(float4(In.Position, 1), WorldView);
    Out.Position = mul(View, Projection);
    Out.ViewZ = View.z;
    Out.Colour = In.Colour;
    Out.UV = In.UV;
    Out.Flow = In.Flow;
    return Out;
}
sampler2D BeamAtlas : register(s0);
float4 Style : register(c0); // periodic animation phase, enhancement strength, ripple amplitude, unused
float4 Fog : register(c1);   // start, end, density, mode: none/exp/exp2/linear
float4 PSMain(VSOut In) : COLOR0
{
    const float Tau = 6.283185307;
    float Head = step(0.5, In.UV.x);
    float Motion = saturate(Style.z / 0.045) * saturate(Style.y);
    float Time = Style.x;
    float Phase = In.Flow.w;
    float HeadV = floor(min(In.UV.y, 0.99999) * 2.0) * 0.5 + 0.25;
    float2 HeadUV = float2((In.UV.x - 0.75) * 4.0, (In.UV.y - HeadV) * 4.0);
    float Spin = (Time * 0.5 + Phase) * Tau;
    float S, C;
    sincos(Spin, S, C);
    float Pulse = sin((Time * 2.0 + Phase) * Tau);
    float2 Rotated = float2(HeadUV.x*C - HeadUV.y*S, HeadUV.x*S + HeadUV.y*C);
    // Rotate and breathe the actual head profile inside its authored bounds. Trail UVs
    // never move between atlas cells; authored black/disabled heads remain invisible.
    Rotated /= 0.88 + 0.10 * Pulse;
    float2 AnimatedHeadUV = float2(0.75, HeadV) + clamp(Rotated, -0.999, 0.999) * 0.25;
    float2 SampleUV = lerp(In.UV, AnimatedHeadUV, Head * Motion);
    float4 Sample = tex2D(BeamAtlas, SampleUV);
    float3 Atlas = Sample.rgb;
    float Mask = saturate(max(Atlas.r, max(Atlas.g, Atlas.b)));
    // Left half = trails; right half = star/ball heads. Keep the authored atlas shapes,
    // but separate a narrow hot filament from the broad, coloured optical mantle.
    float M2 = Mask * Mask;
    float M4 = M2 * M2;
    float Core = lerp(M4 * M2 * Mask, M4, Head);
    float Mantle = sqrt(Mask) * (0.75 + 0.25 * Mask) * (1.0 - 0.35 * Core);
    // Do not magnify the 16-bit source atlas's darkest quantisation steps into a box.
    Mantle *= smoothstep(0.0, 0.12, Mask);
    float HeadBoundary = 1.0 - smoothstep(0.55, 1.0, dot(HeadUV, HeadUV));
    Mantle *= lerp(1.0, HeadBoundary, Head);
    // Flow is continuous across the spear/bolt's different atlas UV segments. Local +Z
    // points down the tail. Constant-phase packets travel toward +Z as time advances.
    float Along = In.Flow.z;
    float Side = In.Flow.x + In.Flow.y;
    float Travel = Along * 9.0 - Time * 2.0 + Phase;
    float Warp = sin((Along * 3.0 - Time + Phase) * Tau + Side * 2.0);
    float Cells = 0.5 + 0.5 * sin(Travel * Tau + Warp * 2.2 + Side * 4.0)
                                * sin(Side * 7.0 - Warp * 2.0 + (Time + Phase) * Tau);
    float Strand = saturate(1.0 - abs(Side - Warp * 0.40) * 4.0);
    Strand *= Strand;
    float Packets = saturate(0.5 + 0.5 * sin((Along * 17.0 - Time * 4.0 + Phase) * Tau + Warp));
    Packets = Packets * Packets * Packets;
    float Resolved = saturate(1.0 - fwidth(Along * 17.0) * 2.0 - fwidth(Side * 7.0));
    float FlowAmount = Motion * Resolved * (1.0 - Head);
    // Strong changes inside the mantle, but a continuous core: no blinking whole shots.
    Mantle *= lerp(1.0, 0.30 + Cells * 1.25, FlowAmount);
    float Filaments = FlowAmount * (0.70 * Strand + 0.55 * Packets) * Mantle;
    Core *= lerp(1.0, 0.82 + 0.24 * Cells, FlowAmount);
    // Expanding rings inside the rotating head, independently phased per projectile.
    float HeadResolved = saturate(1.0 - fwidth(length(HeadUV) * 3.0) * 2.0);
    float Ring = 0.5 + 0.5 * sin(length(HeadUV) * 19.0 - (Time * 3.0 + Phase) * Tau);
    Mantle *= lerp(1.0, 0.65 + 0.80 * Ring, Head * Motion * HeadResolved);
    Core *= lerp(1.0, 0.94 + 0.18 * Pulse, Head * Motion);
    // Retain both authored vertex colour and tinted custom atlases. Zero brightness
    // stays zero, including photon presets whose separate head is deliberately off.
    float3 Tint = In.Colour.rgb * (Atlas / max(Mask, 0.0001));
    float Peak = max(Tint.r, max(Tint.g, Tint.b));
    float3 HotTint = lerp(Tint, Peak.xxx, lerp(0.68, 0.80, Head));
    float3 Artistic = Tint * Mantle + HotTint * (0.85 * Core + Filaments);
    float3 Colour = max(0.0, lerp(Atlas * In.Colour.rgb, Artistic, Style.y));
    float Transmission = 1.0;
    if (Fog.w > 2.5)
        Transmission = saturate((Fog.y - In.ViewZ) / max(Fog.y - Fog.x, 0.0001));
    else if (Fog.w > 1.5)
        Transmission = exp(-pow(max(In.ViewZ, 0.0) * Fog.z, 2.0));
    else if (Fog.w > 0.5)
        Transmission = exp(-max(In.ViewZ, 0.0) * Fog.z);
    // Additive light fades to black in fog; never add a fog-coloured polygon footprint.
    // ONE/ONE ignores alpha for RGB blending, but the game's alpha test still uses it.
    // Preserve the original MODULATE alpha, including any authored cutout in the atlas.
    return float4(Colour * Transmission, Sample.a * In.Colour.a);
}
