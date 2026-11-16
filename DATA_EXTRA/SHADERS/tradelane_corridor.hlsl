#define BAND_MODE 4
#define BAND_COUNT 5.0
#define BAND_LOW 0.2
#define BAND_HIGH 0.65
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
    float ViewDepth:TEXCOORD6;
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
    // This volume is centred on the camera. Cancelling large world translations
    // on the GPU loses sub-metre precision and makes the depth edge swim in flight.
    float3 World = float3(dot(P, LaneRow[0].xyz), dot(P, LaneRow[1].xyz), dot(P, LaneRow[2].xyz));
    float4 View = float4(dot(World, ViewRow[0].xyz), dot(World, ViewRow[1].xyz), -dot(World, ViewRow[2].xyz), 1.0);
    Out.ViewDepth = View.z;
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
float4 Warp : register(c2); // inverse target dimensions, refraction strength, sampled depth available
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
    // Integer frequency ratios preserve both CPU wraps (phase144, time1440).
    float T = frac(Travel.y / 96.0);
    float Edge = StyleIs(1), Walker = StyleIs(4), Dark = StyleIs(5);
    float3 Q = float3(P.xy * (1.0 + Edge * 0.15 + Dark * 0.10) / 950.0,
                     (-P.z / 6400.0 + frac(Travel.x / 4.0)) * (1.0 + Walker));
    return Q + T * float3(1, -1, 2) + Variation.xyz * Palette.w;
}
float3 OuterTubePosition(float3 P)
{
    // Stretch only the repeating longitudinal pattern, not the circumference
    // or radial thickness. Folds fill the whole tube, with fourfold spacing.
    // Divide the distance clock too, retaining the original forward velocity.
    float T=frac(Travel.y/96.0);
    float Edge=StyleIs(1), Walker=StyleIs(4), Dark=StyleIs(5);
    float3 Q=float3(P.xy*(1.0+Edge*.15+Dark*.10)/950.0,
                   (-P.z/25600.0+frac(Travel.x/16.0))*(1.0+Walker));
    return Q+T*float3(1,-1,2)+Variation.xyz*Palette.w;
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

// Scene depth is view-axis distance, not ray length. Respect the world's viewport
// partition: the other partition belongs to foreground/cockpit rendering.
float SceneDistance(float2 UV)
{
    if (Warp.w < 0.5) return 1.0e8;
    float D = tex2Dlod(SceneDepth, float4(UV, 0, 0)).r;
    if (D >= 0.99999994) return 1.0e8;
    if (D > DepthRange.w + 0.00000012 || D < DepthRange.z) return 0.0;
    float Z = saturate((D - DepthRange.z) / max(DepthRange.w - DepthRange.z, 0.000001));
    return DepthRange.x * DepthRange.y / max(DepthRange.y - Z * (DepthRange.y - DepthRange.x), 0.001);
}


// Broad longitudinal sheets, the complete original tube and soft rings.
// World-depth clipping and transitions
// remain the same as the installed corridor. Camera never rolls.
float TradeLaneBand(float3 P,float4 F)
{
    float Angle=atan2(P.y,P.x);
    float Drift=sin(-P.z*.00065+Travel.y*.42)*.75+(F.w)*1.2;
    #if BAND_MODE == 4
    // Screen Y is inverted: increasing the sampled angle moves the material
    // clockwise on screen. Sixteen degrees/second; the camera stays fixed.
    Angle+=fmod(Travel.y,22.5)*.279252680;
    Drift=sin(-P.z*.00065)*.75+F.w*.7;
    #endif
    float Wave=.5+.5*cos(Angle*BAND_COUNT+Drift);
    float Band=smoothstep(BAND_LOW,BAND_HIGH,Wave);
    float Modulation=(.62+.38*sin(-P.z*.002+frac(Travel.x*.5)*6.28318530718+Angle*2.0))*(.35+.65*smoothstep(.22,.70,F.y));
    #if BAND_MODE == 3
    float Packet=.5+.5*cos((-P.z/1700.0+Travel.x*1600.0/1700.0)*6.28318530718+sin(Angle*5)*2.0);
    Band*=smoothstep(.23,.55,Packet);
    #endif
    return Band*Modulation;
}
float3 TradeLaneRings(float3 Ray,float SceneRay)
{
    float3 Color=0;
    #if BAND_MODE == 4
    if(Ray.z>=-.01)return 0;
    float Slope=length(Ray.xy)/(-Ray.z);
    // Same travel speed, half the spacing: .4 rings/s at 1440m/s.
    // Reduce before scaling: 2.25 is exactly representable, even near the CPU
    // wrap. Scaling the large travel phase first visibly quantized the rings.
    float Phase=frac(fmod(Travel.x,2.25)/2.25+.3);
    [loop]for(int Ring=0;Ring<6;++Ring){
        float Forward=(Ring+1-Phase)*7200.0;
        if(Forward>=9400.0)break;
        float Distance=Forward/(-Ray.z);
        float Visibility=smoothstep(60.0,240.0,Forward)*(1-smoothstep(6000.0,9400.0,Forward))*smoothstep(0.0,120.0,SceneRay-Distance);
        if(Visibility<=0)continue;
        float3 P=Ray*Distance;
        float4 F=SampleFlow(FlowPosition(P));
        float Angle=atan2(P.y,P.x);
        float Radius=340.0+sin(Angle*9.0)*4.0+F.w*10.0;
        // One quarter of the previously widened cross-section; same radius.
        float Width=.75*sqrt(65.0*65.0+130.0*130.0*Slope*Slope);
        float Section=(length(P.xy)-Radius)/Width;
        float Body=1-smoothstep(.35,1.25,abs(Section));
        // Continuous textured body again; half the previous emission/visibility
        // multiplier (.5 -> .25), without adding opaque absorption to the world.
        float Lobes=.82+.18*cos(Angle*9.0+F.w*1.2);
        float Texture=.65+.35*smoothstep(.22,.70,F.y);
        float Rounded=.65+.35*sqrt(saturate(1-Section*Section));
        float3 Tint=lerp(float3(.015,.13,.25),float3(.16,.48,.62),saturate(.35+F.x*.65));
        Color+=Tint*Body*Lobes*Texture*Rounded*Visibility*1.15*.25;
    }
    #endif
    return Color;
}

float4 ShadeCorridor(Interp In, float2 Pixel, int LayerCount)
{
    clip(In.CameraBounds);
    // Derivatives precede varying control flow (Shader Model3).
    float PixelFootprint = length(ddx(In.Local)) + length(ddy(In.Local));
    float FragmentAA = max(fwidth(In.UV.x), 0.04);
    float SceneZ = SceneDistance((Pixel + 0.5) * Warp.xy);
    [branch] if (In.Detail.x > 0.5)
    {
        float Across = In.UV.x / max(0.30, FragmentAA * 0.65);
        float Core = exp2(-Across * Across * 2.0) * min(1.0, 0.30 / (FragmentAA * 0.65));
        float Halo = exp2(-In.UV.x * In.UV.x * 4.0) * 0.15;
        float Along = pow(saturate(1.0 - abs(In.UV.y)), 0.65);
        float Energy = (Core + Halo) * Along * In.Detail.y * Travel.z *
            smoothstep(0.0, 20.0, SceneZ - In.ViewDepth);
        float3 C = lerp(float3(0.28, 0.72, 1.0), float3(0.85, 0.96, 1.0), In.Detail.z);
        // Walker's small warm glints have different phases per fragment, not a screen flash.
        float Ember = 1.0 + StyleIs(4) * 0.25 * pow(saturate(sin(
            (Travel.y / 96.0 * 32.0 + In.Detail.z * 3.0 + Variation.w) * 6.28318530718)), 6.0);
        return float4(StyleColor(C) * Energy * 0.85 * Ember, Energy * 0.08);
    }
    float3 Ray = normalize(In.Local);
    float SceneRay = SceneZ * length(In.Local) / max(In.ViewDepth, 0.001);
    [branch] if (SceneRay <= 178.0) return 0;
    float Transverse = max(length(Ray.xy), 0.012);
    if(LayerCount==0)
    {
        // Standard: one textured shell plus the same streaks and soft rings.
        // No radial volume integration. Scene-depth fade still protects objects.
        float Distance=340.0/Transverse;
        float3 P=Ray*Distance;
        float Visibility=(1-smoothstep(5000.0,9400.0,abs(P.z)))*smoothstep(0.0,120.0,SceneRay-Distance);
        float4 F=SampleFlow(FlowPosition(P));
        float Band=TradeLaneBand(P,F)*Visibility;
        float3 Tint=lerp(float3(.015,.13,.25),float3(.16,.48,.62),saturate(.35+F.x*.65));
        float3 Color=Tint*Band*.70+TradeLaneRings(Ray,SceneRay);
        return float4(StyleColor(Color)*Travel.z,Band*.12*Travel.z);
    }
    float FineFade = 1.0 - smoothstep(8.0, 65.0, PixelFootprint);
    float3 Accumulated = 0;
    float Transmission = 1;
    float3 BackdropAccumulated=0;
    float BackdropTransmission=1;
    const float BackdropStrength=1.0;
    const float SheetStrength=.70;
    float Edge = StyleIs(1), Crow = StyleIs(2), Barrier = StyleIs(3);
    float Walker = StyleIs(4), Dark = StyleIs(5);
    // A short local swell every 12 seconds, offset per route. Only selected folds
    // brighten; volume opacity and background visibility never pulse with it.
    float Surge = pow(saturate(sin((Travel.y / 96.0 * 8.0 + Variation.w) * 6.28318530718)), 12.0);
    // Radial stratification integrates emission and absorption through 3D thickness.
    float LayerStride=432.0/LayerCount;
    [loop] for (int I = 0; I < LayerCount; ++I)
    {
        float R = 178.0 + (I + 0.5) * LayerStride;
        float3 P = Ray * (R / Transverse);
        float Far = 1.0 - smoothstep(5000.0, 9400.0, abs(P.z));
        float Remaining = SceneRay - R / Transverse;
        // Later radial layers are farther away too. Reject them before noise fetches.
        [branch] if (Remaining <= 0.0 || Far <= 0.0) break;
        float3 Q = FlowPosition(P);
        float4 F = SampleFlow(Q);
        float4 SheetFlow=F;
        float SheetLitSample=tex3Dlod(Noise,float4(Q+float3(.025,-.035,-.045),0)).r;
        float SheetLighting=saturate(.48+(SheetLitSample-F.x)*5.0);
        Q=OuterTubePosition(P);
        F=SampleFlow(Q);
        float Shell = smoothstep(178.0, 230.0, R) * (1.0 - smoothstep(480.0, 610.0, R));
        float Density = smoothstep(0.40, 0.63, F.x + (F.z - 0.5) * 0.055 * FineFade) * Shell * Far *
            smoothstep(0.0, 120.0, Remaining);
        float BackdropAlpha=1.0-exp2(-Density*min(LayerStride/Transverse,2400.0/LayerCount)*0.012);
        float Band=TradeLaneBand(P,SheetFlow);
        Density=(Band*(.65+.35*SheetFlow.x))*Shell*Far*smoothstep(0.0,120.0,Remaining);
        float Alpha = 1.0 - exp2(-Density * min(LayerStride / Transverse, 2400.0/LayerCount) * 0.012);
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
        // Full original volume, brightness and circumferential coverage.
        BackdropAccumulated+=BackdropTransmission*BackdropAlpha*Color*1.35;
        BackdropTransmission*=1-BackdropAlpha;
        float3 BandColor=lerp(float3(.015,.13,.25),float3(.16,.48,.62),saturate(.35+SheetFlow.x*.65));
        Color=BandColor*Band*(.65+SheetLighting*.7);
        Color *= 1.35;
        Accumulated += Transmission * Alpha * Color;
        Transmission *= 1.0 - Alpha;
    }
    // Scale premultiplied sheet colour and its final opacity together, leaving
    // the background and ring strengths independent of the 30% sheet reduction.
    float SheetOpacity=(1-Transmission)*SheetStrength;
    Accumulated=Accumulated*SheetStrength+BackdropAccumulated*BackdropStrength*(1-SheetOpacity*VolumeCoverage);
    float Forward = smoothstep(0.0, 0.35, -Ray.z);
    Accumulated+=TradeLaneRings(Ray,SceneRay);
    float3 Volume = Accumulated;
    float FocusDistance = min(850.0 / max(-Ray.z, 0.01), 9400.0);
    float FocusVisibility = smoothstep(0.0, 350.0, SceneRay - FocusDistance);
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
    float Opacity = max(SheetOpacity+(1-SheetOpacity)*(1-BackdropTransmission)*BackdropStrength, Halo * 0.24 * FocusVisibility);
    // One opening pressure wave and a collapsing exit wake, not periodic rings.
    float Opening = smoothstep(0.08, 0.22, Transition.x) *
                    (1.0 - smoothstep(0.38, 0.90, Transition.x)) * (1.0 - Transition.z);
    float OpeningRadius = 0.035 + pow(saturate((Transition.x - 0.10) / 0.70), 1.7) * 2.2;
    float OpeningEdge = exp2(-pow((Slope - OpeningRadius - (Front.x - 0.5) * 0.30) / 0.035, 2.0));
    OpeningEdge *= 0.30 + saturate((Front.y - 0.34) * 2.0);
    float Wake = sin(saturate(Transition.y) * 3.14159265) * Transition.z;
    Accumulated += Forward * Opening * (OpeningEdge * float3(0.48, 0.88, 1.0) + Halo * float3(0.18, 0.48, 0.70));
    Accumulated += Wake * Halo * float3(0.08, 0.36, 0.48);
    Accumulated = Volume + (Accumulated - Volume) * FocusVisibility;
    return float4(StyleColor(Accumulated) * Travel.z, saturate(Opacity) * VolumeCoverage * Travel.z);
}

// Constant arguments compile to separate programs; Standard eliminates the
// volume loop entirely. Only the selected entry is created during game loading.
float4 PSStandard(Interp In,float2 Pixel:VPOS):COLOR0 { return ShadeCorridor(In,Pixel,0); }
float4 PSLow(Interp In,float2 Pixel:VPOS):COLOR0 { return ShadeCorridor(In,Pixel,4); }
float4 PSMedium(Interp In,float2 Pixel:VPOS):COLOR0 { return ShadeCorridor(In,Pixel,8); }
float4 PSMain(Interp In,float2 Pixel:VPOS):COLOR0 { return ShadeCorridor(In,Pixel,16); }

// Compatibility entry point: refraction is disabled in the client too.
float4 PSWarp(Interp In, float2 Pixel:VPOS):COLOR0
{
    clip(In.CameraBounds);
    return tex2Dlod(SceneColor,float4((Pixel+.5)*Warp.xy,0,0));
}
