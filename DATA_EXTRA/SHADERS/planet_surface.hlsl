// Planet surface: the retail planet materials (DetailMapMaterial, Masked2DetailMapMaterial,
// IllumDetailMapMaterial) in one pass, with relief from the base texture and the detail maps,
// terrain shadows towards the terminator, a sun glint on water and the glow layer. View space,
// camera at the origin.
// Samplers: s0 the base map (Dt; alpha is the material's mask), s1 detail map 0, s2 detail map 1.
// The material has up to two surface layers: layer 0 (detail map 0; where the mask is black) and
// layer 1 (detail map 1 where the mask is white, Masked2DetailMapMaterial only). RP9 tells from the
// detail map names what each layer is (water, rock, ground, ice, clouds...).
row_major float4x4 WorldView : register(c0);
row_major float4x4 Projection : register(c4);

struct SurfacePixel
{
    float4 Position : POSITION0;
    float3 ViewPosition : TEXCOORD0;
    float3 ViewNormal : TEXCOORD1;
    float2 Uv : TEXCOORD2;
    float3 ObjectNormal : TEXCOORD3;
};

SurfacePixel VSMain(float3 Position : POSITION0, float3 Normal : NORMAL0, float2 Uv : TEXCOORD0)
{
    SurfacePixel Out;
    float4 P = mul(float4(Position, 1.0), WorldView);
    Out.Position = mul(P, Projection);
    Out.ViewPosition = P.xyz;
    Out.ViewNormal = mul(Normal, (float3x3)WorldView);
    Out.Uv = Uv;
    Out.ObjectNormal = Normal;
    return Out;
}

sampler2D BaseMap : register(s0);
sampler2D Detail0 : register(s1);
sampler2D Detail1 : register(s2);

float4 SunDirection : register(c0); // xyz towards the sun (view, unit), w terminator wrap
float4 SunColour : register(c1);    // rgb light diffuse * material diffuse
float4 Ambient : register(c2);      // rgb ambient + emissive
float4 Kind : register(c3);         // x mode (0 detail 2-pass, 1 masked, 2 illum, 3 detail), y gas giant side (1), z tile 0, w tile 1
float4 Water : register(c4);        // x glint strength, y glint roughness, z fresnel F0, w cloud luminance threshold
float4 Relief : register(c5);       // x base relief, y detail relief, zw base texel size (1/width, 1/height)
float4 Glow : register(c6);         // x glow strength, y night-only (0 retail: always, 1 night side only), z terrain shadows, w glow pulse
float4 Fog : register(c7);          // start, end, density, mode
float4 FogColour : register(c8);    // rgb, w range fog
float4 Layers : register(c9);       // x layer 0 water, y layer 0 relief, z layer 1 water, w layer 1 relief
float4 Elevation : register(c10);   // x layer 0 elevation, y layer 1 elevation (equal outside Masked2), z base luminance weight
float4 Gas : register(c11);         // x time (s, wrapped), y jet speed (rad/s), z eddy speed (rad/s per unit stream gradient)
float4 Storms[3] : register(c12);   // per vortex: longitude, latitude (object space, radians), radius (radians), spin (signed; 0 = none)
float4 Centre : register(c15);      // xyz planet centre (view), w seam band (uv) where the texture edges are softened
float4 GasStyle : register(c16);    // x eddy noise frequency, y unused, z animated (1), w flow period (s)
float4 Surface : register(c17);     // x airless (Lommel-Seeliger lighting), y ice sheen, z layer 0 ice, w layer 1 ice
float4 EclipseCaster : register(c18);  // eclipse: caster centre (view), radius
float4 EclipseSun : register(c19);     // eclipse: sun centre (view), radius
float4 EclipseControl : register(c20); // eclipse: x range behind the caster, y strength, w on
float4 Quality : register(c21); // screen-size fades: base relief, detail relief, gas eddies/storms, terrain shadows

static const float3 Luma = float3(0.299, 0.587, 0.114);

// A planet eclipsing this one (port.ini planet_eclipses): the fraction of the sun left at a
// view-space point. The sun and the caster are discs in the sky of that point; where the caster
// covers the sun fully there is umbra, a soft penumbra where it covers part of it.
float Eclipse(float3 P)
{
    if (EclipseControl.w < 0.5)
        return 1.0;
    float3 ToCaster = EclipseCaster.xyz - P;
    float3 ToSun = EclipseSun.xyz - P;
    float SunDistance = length(ToSun);
    float3 SunRay = ToSun / SunDistance;
    float Along = dot(ToCaster, SunRay);
    if (Along <= 0.0 || Along > EclipseControl.x)
        return 1.0;
    float CasterDistance = length(ToCaster);
    float CasterAngle = asin(saturate(EclipseCaster.w / CasterDistance));
    float SunAngle = max(asin(saturate(EclipseSun.w / SunDistance)), 1.0e-4);
    float Apart = acos(saturate(dot(ToCaster / CasterDistance, SunRay)));
    float Covered = 1.0 - smoothstep(abs(CasterAngle - SunAngle), CasterAngle + SunAngle, Apart);
    // A caster smaller than the sun never hides all of it.
    Covered *= min(1.0, (CasterAngle * CasterAngle) / (SunAngle * SunAngle));
    return 1.0 - Covered * EclipseControl.y;
}

// The height field: the base map's luminance plus the layers' elevation through the mask (rock
// stands above sand and water, so mountains bulge even where the artist painted them dark).
float HeightOf(float4 Texel)
{
    return dot(Texel.rgb, Luma) * Elevation.z + lerp(Elevation.x, Elevation.y, Texel.a);
}

// Planet textures meet at their uv edges (sides and caps); keep every base sample half a texel
// inside so wrap filtering never pulls in the opposite edge.
// Coordinates outside 0..1 (a tiling layout) are left alone.
float2 Inside(float2 Uv)
{
    float2 Half = Relief.zw * 0.5;
    float2 InRange = step(0.0, Uv) * step(Uv, 1.0);
    return lerp(Uv, clamp(Uv, Half, 1.0 - Half), InRange);
}

// 0 on a uv edge (the 0 and 1 lines), 1 a seam band away from it.
float EdgeWeight(float2 Uv)
{
    float2 F = min(abs(Uv), abs(1.0 - Uv));
    return saturate(min(F.x, F.y) / max(Centre.w, 1.0e-5));
}

float Height(float2 Uv, float2 Dx, float2 Dy)
{
    return HeightOf(tex2Dgrad(BaseMap, Inside(Uv), Dx, Dy));
}

float Hash3(float3 P)
{
    return frac(sin(dot(P, float3(127.1, 311.7, 74.7))) * 43758.5453);
}

// Smooth 3D value noise (0..1).
float Noise3(float3 P)
{
    float3 I = floor(P), F = frac(P);
    float3 U = F * F * (3.0 - 2.0 * F);
    float A = lerp(Hash3(I), Hash3(I + float3(1, 0, 0)), U.x);
    float B = lerp(Hash3(I + float3(0, 1, 0)), Hash3(I + float3(1, 1, 0)), U.x);
    float C = lerp(Hash3(I + float3(0, 0, 1)), Hash3(I + float3(1, 0, 1)), U.x);
    float D = lerp(Hash3(I + float3(0, 1, 1)), Hash3(I + float3(1, 1, 1)), U.x);
    return lerp(lerp(A, B, U.y), lerp(C, D, U.y), U.z);
}

float3 DirectionOf(float2 LonLat)
{
    float C = cos(LonLat.y);
    return float3(C * cos(LonLat.x), sin(LonLat.y), C * sin(LonLat.x));
}

// The longitude/latitude displacement of the storm vortices at one flow phase. Each storm is an
// oval in longitude/latitude (the object's y axis is the pole) twisted into a spiral and turning,
// fastest in the middle.
float2 StormOffset(float2 LonLat, float Phase)
{
    float2 Offset = 0.0;
    float CosLat = max(cos(LonLat.y), 0.2);
    [unroll] for (int I = 0; I < 3; ++I)
    {
        float4 S = Storms[I];
        [branch] if (S.z > 0.0 && S.w != 0.0)
        {
            float2 D = LonLat - S.xy;
            D.x -= 6.2831853 * round(D.x / 6.2831853);
            D.x *= CosLat; // local east-north metric
            float2 E = D / float2(S.z, S.z * 0.55);
            float W = exp(-dot(E, E) * 2.2);
            // A standing spiral plus the turning within the flow cycle.
            float Angle = S.w * W * (1.6 + 0.9 * (Phase - 0.5));
            float C = cos(Angle), Sn = sin(Angle);
            float2 R = float2(C * D.x - Sn * D.y, Sn * D.x + C * D.y);
            Offset += R - D;
        }
    }
    Offset.x /= CosLat;
    return Offset;
}

// How much of a storm covers the point: x the ring at the oval's edge, y the core.
float2 StormMask(float2 LonLat)
{
    float2 Mask = 0.0;
    float CosLat = max(cos(LonLat.y), 0.2);
    [unroll] for (int I = 0; I < 3; ++I)
    {
        float4 S = Storms[I];
        [branch] if (S.z > 0.0 && S.w != 0.0)
        {
            float2 D = LonLat - S.xy;
            D.x -= 6.2831853 * round(D.x / 6.2831853);
            D.x *= CosLat;
            float2 E = D / float2(S.z, S.z * 0.55);
            float R = sqrt(dot(E, E));
            float On = S.w != 0.0 ? 1.0 : 0.0;
            Mask.x += On * exp(-pow((R - 0.75) / 0.18, 2.0));
            Mask.y += On * exp(-R * R * 6.0);
        }
    }
    return saturate(Mask);
}

// The stream function of the eddies: noise on the sphere, slowly evolving.
float Stream(float3 Direction)
{
    return Noise3(Direction * GasStyle.x + float3(0.0, Gas.x * 0.002, 0.0));
}

// 1 inside a part, 0 on its uv edges: the deformation fades out there, so the seams between a
// gas giant's parts (sides and caps, each its own texture) stay exactly as painted.
float GasEnvelope(float2 Uv)
{
    float2 F = min(abs(Uv), abs(1.0 - Uv));
    return smoothstep(0.0, 0.18, min(F.x, F.y));
}

// A gas giant part: zonal jets (each latitude its own speed and sign), eddies (the curl of Stream:
// divergence-free, so they swirl) and the storm vortices, as a two-phase flow map in longitude/
// latitude (each phase displaces by the velocity times its age and restarts while the other is
// fully shown), mapped to uv through LonLatToUv and faded out towards the part's edges.
float4 GasGiantUv(float2 Uv, float2 Gx, float2 Gy, float3 On, float2 LonLat, float2x2 LonLatToUv)
{
    float T = Gas.x;
    float Period = GasStyle.w;
    float CosLat = max(cos(LonLat.y), 0.15);
    float2 Eddy = 0.0;
    [branch] if (Quality.z > 0.0)
    {
        float3 East = float3(-sin(LonLat.x), 0.0, cos(LonLat.x));
        float3 North = float3(-sin(LonLat.y) * cos(LonLat.x), cos(LonLat.y), -sin(LonLat.y) * sin(LonLat.x));
        const float E = 0.03;
        float Psi = Stream(On);
        float PsiE = Stream(normalize(On + East * E)) - Psi;
        float PsiN = Stream(normalize(On + North * E)) - Psi;
        Eddy = float2(PsiN, -PsiE) * (Gas.z / E) * Quality.z;
    }
    float Jet = 0.6 * sin(LonLat.y * 7.0) + 0.4 * cos(LonLat.y * 3.0 + 0.7);
    float2 Velocity = float2(Gas.y * Jet + Eddy.x / CosLat, Eddy.y);
    float Envelope = GasEnvelope(Uv);

    float PhaseA = frac(T / Period), PhaseB = frac(T / Period + 0.5);
    float2 A = Velocity * (PhaseA - 0.5) * Period;
    float2 B = Velocity * (PhaseB - 0.5) * Period;
    [branch] if (Quality.z > 0.0)
    {
        A += StormOffset(LonLat, PhaseA) * Quality.z;
        B += StormOffset(LonLat, PhaseB) * Quality.z;
    }
    float4 CA = tex2Dgrad(BaseMap, Inside(Uv - mul(LonLatToUv, A) * Envelope), Gx, Gy);
    float4 CB = tex2Dgrad(BaseMap, Inside(Uv - mul(LonLatToUv, B) * Envelope), Gx, Gy);
    return lerp(CA, CB, abs(PhaseA * 2.0 - 1.0));
}

float4 PSMain(SurfacePixel In) : COLOR0
{
    // The analytic sphere normal: no facets, and no lighting step where side and cap meshes meet.
    float3 N = normalize(In.ViewPosition - Centre.xyz);
    float3 L = SunDirection.xyz;
    float3 V = normalize(-In.ViewPosition);
    float2 Uv = In.Uv;
    float2 Uv0 = Uv * Kind.z, Uv1 = Uv * Kind.w;

    float2 UvDx = ddx(Uv), UvDy = ddy(Uv);
    // Derivatives are evaluated before any dynamic flow control. Angular derivatives below
    // use the chain rule, so ordinary worlds need neither longitude/latitude nor its Jacobian.
    float3 ObjectDx = ddx(In.ObjectNormal), ObjectDy = ddy(In.ObjectNormal);
    float3 Dp1 = ddx(In.ViewPosition), Dp2 = ddy(In.ViewPosition);
    float2 LonLat = 0.0;
    float4 Base = 0.0;
    [branch] if (Kind.y > 0.5)
    {
        // Longitude/latitude of the point (object space, y the pole) and how uv changes with them
        // (J = dUv * inverse(dLonLat), from screen derivatives, whatever the part's uv layout).
        float3 On = normalize(In.ObjectNormal);
        LonLat = float2(atan2(On.z, On.x), asin(clamp(On.y, -1.0, 1.0)));
        [branch] if (GasStyle.z > 0.0)
        {
            float InvLength = rsqrt(max(dot(In.ObjectNormal, In.ObjectNormal), 1.0e-20));
            float3 OnDx = (ObjectDx - On * dot(On, ObjectDx)) * InvLength;
            float3 OnDy = (ObjectDy - On * dot(On, ObjectDy)) * InvLength;
            float InvPole = 1.0 / max(dot(On.xz, On.xz), 1.0e-12);
            float2 LlDx = float2((On.x * OnDx.z - On.z * OnDx.x) * InvPole, OnDx.y * sqrt(InvPole));
            float2 LlDy = float2((On.x * OnDy.z - On.z * OnDy.x) * InvPole, OnDy.y * sqrt(InvPole));
            float LlDet = LlDx.x * LlDy.y - LlDy.x * LlDx.y;
            float2x2 LonLatToUv = 0.0;
            if (abs(LlDet) > 1.0e-14)
            {
                float2x2 Inverse = float2x2(LlDy.y, -LlDy.x, -LlDx.y, LlDx.x) / LlDet;
                LonLatToUv = mul(float2x2(UvDx.x, UvDy.x, UvDx.y, UvDy.y), Inverse);
            }
            Base = GasGiantUv(Uv, UvDx, UvDy, On, LonLat, LonLatToUv);
        }
    }
    [branch] if (Kind.y <= 0.5 || GasStyle.z <= 0.0)
    {
        // Near a texture edge fade to a blurred version: two textures that do not quite match
        // meet as a soft gradient instead of a line.
        float Edge = EdgeWeight(Uv);
        Base = tex2Dgrad(BaseMap, Inside(Uv), UvDx, UvDy);
        float4 Soft = tex2Dlod(BaseMap, float4(Inside(Uv), 0, 4));
        Base = lerp(Soft, Base, Edge * Edge * (3.0 - 2.0 * Edge));
    }
    float2 Dx0 = UvDx * Kind.z, Dy0 = UvDy * Kind.z;
    float2 Dx1 = UvDx * Kind.w, Dy1 = UvDy * Kind.w;
    float3 D0 = tex2Dgrad(Detail0, Uv0, Dx0, Dy0).rgb * 2.0;
    float4 D1 = tex2Dgrad(Detail1, Uv1, Dx1, Dy1);
    D1.rgb *= 2.0;

    // Albedo as the retail passes combine it.
    float IsMasked = Kind.x > 0.5 && Kind.x < 1.5 ? 1.0 : 0.0;
    float IsIllum = Kind.x > 1.5 && Kind.x < 2.5 ? 1.0 : 0.0;
    float IsFullDetail = Kind.x > 2.5 ? 1.0 : 0.0; // DetailMapMaterial: Dt * 2Dm everywhere
    float3 Land = Base.rgb * D0;
    // DetailMap2Dm1Msk2PassMaterial: the detail fades out where the base alpha is high.
    float3 Albedo = lerp(Base.rgb * lerp(D0, 1.0, Base.a), Land, IsMasked + IsIllum + IsFullDetail);
    Albedo = lerp(Albedo, Base.rgb * D1.rgb, IsMasked * Base.a);
    [branch] if (Kind.y > 0.5 && Quality.z > 0.0)
    {
        // Storm ovals: a darker rim around a slightly brighter, warmer core.
        float2 Storm = StormMask(LonLat) * GasEnvelope(Uv) * Quality.z;
        Albedo *= (1.0 - 0.35 * Storm.x) * (1.0 + Storm.y * float3(0.25, 0.12, 0.0));
    }
    float W1 = IsMasked * Base.a, W0 = 1.0 - W1;

    // Clouds are painted into the base colour: bright and grey. Water must also look like water
    // (blue or teal, not sand), whatever its layer says.
    float Lum = dot(Base.rgb, Luma);
    float Chroma = max(Base.r, max(Base.g, Base.b)) - min(Base.r, min(Base.g, Base.b));
    float Cloud = saturate((Lum - Water.w) / 0.2) * saturate(1.0 - Chroma * 4.0);
    float Wet = saturate((Base.b - Base.r) * 6.0);
    float Sea = saturate(W0 * Layers.x + W1 * Layers.z) * Wet * (1.0 - Cloud);
    float LayerRelief = W0 * Layers.y + W1 * Layers.w;

    float3 Nr = N;
    float NoL = dot(N, L);
    float TerrainShadow = 1.0;
    // Gas has no solid surface. Skip all height/detail reads and normal construction for it,
    // and for small worlds whose relief has smoothly faded to zero.
    [branch] if (Kind.y <= 0.5 &&
        ((Relief.x != 0.0 && Quality.x > 0.0) || (Relief.y != 0.0 && Quality.y > 0.0)))
    {
        // Base relief: the base map's luminance as a height field, a 4-tap gradient spaced by the
        // pixel footprint, turned into a normal with a screen-derivative cotangent frame.
        float2 Texel = Relief.zw;
        float2 UvWidth = abs(UvDx) + abs(UvDy);
        float2 Footprint = max(UvWidth / Texel, 1.0);
        float Step = max(Footprint.x, Footprint.y);
        float2 Du = float2(Texel.x * Step, 0.0), Dv = float2(0.0, Texel.y * Step);
        float H0 = HeightOf(Base);
        float2 Duv1 = UvDx, Duv2 = UvDy;
        float3 Dp2Perp = cross(Dp2, N), Dp1Perp = cross(N, Dp1);
        float3 T = Dp2Perp * Duv1.x + Dp1Perp * Duv2.x;
        float3 B = Dp2Perp * Duv1.y + Dp1Perp * Duv2.y;
        float InvMax = rsqrt(max(max(dot(T, T), dot(B, B)), 1.0e-30));
        T *= InvMax;
        B *= InvMax;
        float SeamFade = EdgeWeight(Uv);
        // Magnified (a texel over two pixels) the base map's gradient steps texel by texel and the
        // shading turns blocky: fade the base relief out there and leave close-ups to the detail relief.
        float Magnified = saturate(max(UvWidth.x / Texel.x, UvWidth.y / Texel.y) * 2.0);
        float ReliefAmount = Relief.x * Quality.x * LayerRelief * (1.0 - Sea) * (1.0 - 0.7 * Cloud) * SeamFade * Magnified;
        [branch] if (Relief.x != 0.0 && Quality.x > 0.0)
        {
            float Gx = (Height(Uv + Du, UvDx, UvDy) - Height(Uv - Du, UvDx, UvDy)) / (2.0 * Step);
            float Gy = (Height(Uv + Dv, UvDx, UvDy) - Height(Uv - Dv, UvDx, UvDy)) / (2.0 * Step);
            Nr = normalize(N - ReliefAmount * (Gx * T + Gy * B));
        }

        // Detail relief: the layer's detail map luminance as fine bumps (screen-derivative bump
        // mapping), a fraction of a detail tile high, gone once the detail is smaller than a pixel.
        // Forward differences one pixel over, sampled at the same mip (ddx/ddy of Hd would be per
        // 2x2 quad and look blocky).
        [branch] if (Relief.y != 0.0 && Quality.y > 0.0)
        {
            float Hd = W0 * dot(D0, Luma) * 0.5 + W1 * dot(D1.rgb, Luma) * 0.5;
            float HdX = W0 * dot(tex2Dgrad(Detail0, Uv0 + Dx0, Dx0, Dy0).rgb, Luma) +
                        W1 * dot(tex2Dgrad(Detail1, Uv1 + Dx1, Dx1, Dy1).rgb, Luma);
            float HdY = W0 * dot(tex2Dgrad(Detail0, Uv0 + Dy0, Dx0, Dy0).rgb, Luma) +
                        W1 * dot(tex2Dgrad(Detail1, Uv1 + Dy1, Dx1, Dy1).rgb, Luma);
            float Det = dot(Dp1, Dp2Perp);
            float3 Grad = sign(Det) * ((HdX - Hd) * Dp2Perp + (HdY - Hd) * Dp1Perp);
            float WorldPerUv = length(Dp1) / max(length(Duv1), 1.0e-12);
            float TileWorld = WorldPerUv / max(W0 * Kind.z + W1 * Kind.w, 1.0e-3);
            float2 DetailWidth = abs(Dx0) + abs(Dy0);
            float DetailFade = saturate(2.0 - max(DetailWidth.x, DetailWidth.y) * 512.0);
            float DetailHeight = Relief.y * Quality.y * LayerRelief * (1.0 - Sea) * (1.0 - Cloud) * DetailFade * 0.004 * TileWorld * SeamFade;
            Nr = normalize(Nr * abs(Det) - DetailHeight * Grad);
        }

        // Terrain shadows: march the height field towards the sun; ridges shadow what lies behind
        // them, long near the terminator.
        [branch] if (Glow.z > 0.0 && Quality.w > 0.0 && Relief.x != 0.0 && Quality.x > 0.0)
        {
            float2 SunUv = float2(dot(L, T), dot(L, B));
            SunUv /= max(length(SunUv), 1.0e-4);
            float TanSun = NoL * rsqrt(max(1.0 - NoL * NoL, 1.0e-4));
            float ShadowStep = Step * 3.0;
            float Occlusion = 0.0;
            [unroll] for (int I = 1; I <= 4; ++I)
            {
                float Along = ShadowStep * I;
                float Above = ReliefAmount * (Height(Uv + SunUv * Texel * Along, UvDx, UvDy) - H0) - Along * TanSun;
                Occlusion = max(Occlusion, Above);
            }
            TerrainShadow = lerp(1.0, saturate(1.0 - Occlusion * Glow.z), Quality.w);
        }
    }

    // Lighting: the retail vertex lighting per pixel, a slightly wrapped terminator; the relief
    // only shades the day side.
    float IsGas = Kind.y > 0.5 ? 1.0 : 0.0;
    // Gas giants: a deep atmosphere carries light further past the terminator.
    float Wrap = lerp(SunDirection.w, 0.25, IsGas);
    float Flat = saturate((NoL + Wrap) / (1.0 + Wrap));
    float Bumped = saturate((dot(Nr, L) + Wrap) / (1.0 + Wrap)) * TerrainShadow;
    float Diffuse = lerp(Flat, Bumped, saturate(NoL * 4.0));
    // Airless bodies (Lommel-Seeliger, the Moon's law): brightness goes with cos(i)/(cos(i)+cos(e)),
    // so the lit disc stays flat out to the limb instead of darkening, and the terminator is sharp.
    float LsLight = saturate(dot(Nr, L));
    float LsView = max(dot(Nr, V), 0.05);
    float Lunar = min(2.0 * LsLight / (LsLight + LsView), 1.5) * TerrainShadow * saturate(NoL * 20.0);
    Diffuse = lerp(Diffuse, Lunar, Surface.x);
    float Sunlit = Eclipse(In.ViewPosition);
    Diffuse *= Sunlit;
    // Gas giants darken towards the limb (looking through more haze above the clouds).
    float NoVLimb = saturate(dot(N, V));
    Diffuse *= lerp(1.0, 0.45 + 0.55 * sqrt(NoVLimb), IsGas);
    float3 Result = Albedo * (SunColour.rgb * Diffuse + Ambient.rgb);

    // Sun glint on water (GGX, Schlick fresnel).
    float3 H = normalize(L + V);
    float NoH = saturate(dot(N, H));
    float A2 = Water.y * Water.y;
    float Den = NoH * NoH * (A2 - 1.0) + 1.0;
    float D = A2 / (3.14159265 * Den * Den);
    float F = Water.z + (1.0 - Water.z) * pow(1.0 - saturate(dot(V, H)), 5.0);
    float NoV = saturate(dot(N, V));
    Result += SunColour.rgb * (Sunlit * Water.x * Sea * D * F * saturate(NoL) / (4.0 * max(NoV, 0.2)));

    // Ice: a broad soft sheen on the relief normal (GGX, roughness 0.35, F0 0.04).
    float Ice = (W0 * Surface.z + W1 * Surface.w) * (1.0 - Sea);
    float3 Hr = normalize(L + V);
    float NoHr = saturate(dot(Nr, Hr));
    const float IceA2 = 0.35 * 0.35 * 0.35 * 0.35;
    float IceDen = NoHr * NoHr * (IceA2 - 1.0) + 1.0;
    float IceD = IceA2 / (3.14159265 * IceDen * IceDen);
    float IceF = 0.04 + 0.96 * pow(1.0 - saturate(dot(V, Hr)), 5.0);
    Result += SunColour.rgb * (Sunlit * Surface.y * Ice * IceD * IceF * saturate(dot(Nr, L)) / (4.0 * max(NoV, 0.2)));

    // Illum: the glow layer over the lit surface (retail: always; Glow.y fades it out on the day
    // side: city lights come on past the terminator, lava burns brighter at night). Lava pulses.
    float Night = saturate(-NoL * 4.0 + 0.2);
    float GlowAmount = IsIllum * Base.a * D1.a * Glow.x * lerp(1.0, Night, Glow.y);
    GlowAmount *= lerp(1.0, 0.75 + 0.25 * sin(Gas.x * 1.7 + Base.a * 25.0 + dot(Uv, float2(37.0, 23.0))), Glow.w);
    Result = lerp(Result, Base.rgb * D1.rgb, saturate(GlowAmount));

    if (Fog.w > 0.5)
    {
        float Z = FogColour.w > 0.5 ? length(In.ViewPosition) : abs(In.ViewPosition.z);
        float Keep = Fog.w > 2.5 ? saturate((Fog.y - Z) / max(Fog.y - Fog.x, 1.0e-4)) :
            (Fog.w > 1.5 ? exp(-pow(Z * Fog.z, 2.0)) : exp(-Z * Fog.z));
        Result = lerp(FogColour.rgb, Result, Keep);
    }
    return float4(Result, 1.0);
}
