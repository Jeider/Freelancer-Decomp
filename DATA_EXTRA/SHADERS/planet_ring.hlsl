// Planet ring: the retail texture-panel band (zone ring, [Exterior] of solar\rings\*.ini) drawn as
// a lit layer of particles. View space, camera at the origin. Blend ONE, INVSRCALPHA.
// - The band's radius is exact per pixel (the mesh is a polygon of chords; the outer vertices
//   are pushed out so it covers the true annulus, pixels outside are clipped), so the shape
//   texture's radial profile has no facets close up.
// - Light: single scattering in a thin particle layer. The side facing the sun reflects; the
//   other side only shows light that came through, so dense bands go dark from behind and thin
//   ones glow. Seen at a grazing angle the layer thickens (more particles along the ray).
// - The planet's shadow, and the nearest other planet's, fall across the ring (umbra and
//   penumbra from the sun's size).
// - Approaching, the band fades out between Fade.x (far) and Fade.y (near) metres (the 2002
//   beta's [Exterior] fade_range).
row_major float4x4 WorldView : register(c0);
row_major float4x4 Projection : register(c4);
float4 RingCentreVs : register(c8); // xyz ring centre (view), w how far the outer vertices are pushed out (1/cos(pi/N))
float4 RingNormalVs : register(c9); // xyz ring normal (view), w the middle radius (inner vertices stay)

struct RingVertex
{
    float3 Position : POSITION0;
    float4 Colour : COLOR0;
    float2 Uv0 : TEXCOORD0;
    float2 Uv1 : TEXCOORD1;
};

struct RingPixel
{
    float4 Position : POSITION0;
    float3 ViewPosition : TEXCOORD0;
    float4 Colour : TEXCOORD1;
    float2 Uv0 : TEXCOORD2;
    float2 Uv1 : TEXCOORD3;
};

RingPixel VSMain(RingVertex In)
{
    RingPixel Out;
    float3 P = mul(float4(In.Position, 1.0), WorldView).xyz;
    float3 Offset = P - RingCentreVs.xyz;
    float Height = dot(Offset, RingNormalVs.xyz);
    float3 Radial = Offset - RingNormalVs.xyz * Height;
    if (length(Radial) > RingNormalVs.w)
        P = RingCentreVs.xyz + RingNormalVs.xyz * Height + Radial * RingCentreVs.w;
    Out.ViewPosition = P;
    Out.Position = mul(float4(P, 1.0), Projection);
    Out.Colour = In.Colour;
    Out.Uv0 = In.Uv0;
    Out.Uv1 = In.Uv1;
    return Out;
}

sampler2D ShapeMap : register(s0);

float4 Ring : register(c0);      // xyz ring centre (view), w inner radius
float4 RingNormal : register(c1); // xyz ring normal (view, unit), w outer radius
float4 SunSphere : register(c2);  // xyz sun centre (view), w radius
float4 PlanetSphere : register(c3); // xyz the ring's planet (view), w radius (0 = none)
float4 SunColour : register(c4);  // rgb sunlight
float4 Ambient : register(c5);    // rgb ambient light
float4 Shape : register(c6);      // the shape's texture rectangle: x U0, y U1, z V0 (outer edge), w V1 (inner edge)
float4 Fade : register(c7);       // x far, y near (metres from the camera), z unused, w forward scattering
float4 Look : register(c8);       // x brightness, y light through the unlit side, z opacity scale, w ring_debug piece + 1 (0 off)
float4 NeighbourSphere : register(c9); // xyz the nearest other planet (view), w radius (0 = none): it may shadow the ring too

// Fraction of the sun's disc left at P with a sphere in the way (umbra and penumbra).
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

float4 PSMain(RingPixel In) : COLOR0
{
    float3 P = In.ViewPosition;
    float3 N = RingNormal.xyz;
    float3 Offset = P - Ring.xyz;
    float3 Radial = Offset - N * dot(Offset, N);
    float Across = (length(Radial) - Ring.w) / (RingNormal.w - Ring.w); // 0 inner edge, 1 outer
    clip(Across);
    clip(1.0 - Across);
    // Behind the ring's own planet: hidden, whatever the depth test. The pieces are sorted one by
    // one against the planet, and some are drawn after it with the depth test off.
    if (PlanetSphere.w > 0.0)
    {
        float Distance = length(P);
        float3 Ray = P / Distance;
        float Along = dot(Ray, PlanetSphere.xyz);
        float Radius = PlanetSphere.w * 0.995;
        float Gap = Along * Along - (dot(PlanetSphere.xyz, PlanetSphere.xyz) - Radius * Radius);
        if (Gap > 0.0)
        {
            float Hit = Along - sqrt(Gap);
            clip(Hit > 0.0 && Hit < Distance ? -1.0 : 1.0);
        }
    }

    // The band as retail combines it: shape x vertex colour (ini color, opacity) x detail x2.
    // The shape is a radial profile: sampled down the middle of its atlas rectangle (retail
    // alternates its two U edges per segment, and the neighbouring shapes bleed in as lines).
    float2 ShapeUv = float2((Shape.x + Shape.y) * 0.5, lerp(Shape.w, Shape.z, Across));
    float4 Band = tex2D(ShapeMap, ShapeUv) * In.Colour;
    // No detail map (its fine tile shimmered in the distance) and no grain in its place (it split
    // the band into stripes as the view moved). Rings authored with a detail map were tuned
    // through it: keep its average (ringdetail: x2 colour 0.525, alpha 0.237) so the band stays
    // as bright and as dense as the artist set it.
    if (Fade.z > 0.5)
        Band *= float4(0.525, 0.525, 0.525, 0.237);
    float Opacity = saturate(Band.a * Look.z);
    float3 Albedo = saturate(Band.rgb);

    // Optical depth straight through the layer; along the view ray it is that over |cos|.
    float Tau = -log(1.0 - min(Opacity, 0.995));
    float3 View = normalize(-P);
    float3 Light = normalize(SunSphere.xyz - P);
    float Mu = dot(N, View), Mu0 = dot(N, Light);
    float AMu = max(abs(Mu), 0.03), AMu0 = max(abs(Mu0), 0.03);
    float Alpha = 1.0 - exp(-Tau / AMu);

    // Single scattering: reflected on the lit side, diffusely transmitted on the other.
    float Scattered;
    if (Mu * Mu0 > 0.0)
        Scattered = AMu0 / (AMu0 + AMu) * (1.0 - exp(-Tau * (1.0 / AMu0 + 1.0 / AMu)));
    else
    {
        float Gap = AMu - AMu0;
        Scattered = abs(Gap) < 1.0e-3 ? Tau / AMu * exp(-Tau / AMu)
                                      : AMu0 / Gap * (exp(-Tau / AMu) - exp(-Tau / AMu0));
        Scattered *= Look.y;
    }
    // Phase: an opposition surge with the sun behind the camera, dust glowing forward when looking
    // towards the sun through the ring.
    float CosPhase = dot(Light, View);
    float Phase = 0.8 + 0.6 * pow(saturate(CosPhase), 6.0) + Fade.w * pow(saturate(-CosPhase), 8.0);

    float Sunlit = SphereShadow(P, PlanetSphere) * SphereShadow(P, NeighbourSphere);
    float3 Colour = Albedo * (SunColour.rgb * (Scattered * Phase * Sunlit * Look.x) + Ambient.rgb * Alpha);

    // TEMP port.ini ring_debug: each band piece in its own hue (Look.w = piece + 1).
    if (Look.w > 0.5)
    {
        float Hue = frac((Look.w - 1.0) / 8.0);
        float3 Tint = saturate(abs(frac(Hue + float3(0.0, 2.0 / 3.0, 1.0 / 3.0)) * 6.0 - 3.0) - 1.0);
        return float4(Tint * 0.5, 0.5);
    }

    // Fading out as the camera closes in.
    float Near = saturate((length(P) - Fade.y) / max(Fade.x - Fade.y, 1.0));
    Near = Near * Near * (3.0 - 2.0 * Near);
    return float4(Colour, Alpha) * Near;
}
