// Planet atmosphere, a soft artistic model: a glow above the limb that fades out with height,
// and a haze over the planet that thickens towards the limb, both lit by the sun with a soft
// (wrapped) terminator and warmed near it. Drawn on the planet's atmosphere shell in view
// space, metres, camera at the origin. Blend ONE, INVSRCALPHA: colour is added, alpha veils
// the surface under the haze.
row_major float4x4 WorldView : register(c0);
row_major float4x4 Projection : register(c4);
float4 Inflate : register(c8); // xyz planet centre (view), w radius the shell vertices are pushed to

struct ShellPixel
{
    float4 Position : POSITION0;
    float3 ViewPosition : TEXCOORD0;
};

ShellPixel VSMain(float3 Position : POSITION0)
{
    ShellPixel Out;
    float3 P = mul(float4(Position, 1.0), WorldView).xyz;
    // The shell mesh is a polygonal sphere: push its vertices out to a radius a little beyond
    // the outer edge of the glow so the rasterised area covers it; pixels outside return nothing.
    P = Inflate.xyz + normalize(P - Inflate.xyz) * Inflate.w;
    Out.ViewPosition = P;
    Out.Position = mul(float4(P, 1.0), Projection);
    return Out;
}

float4 Planet : register(c0);       // xyz centre (view), w surface radius
float4 Shell : register(c1);        // x outer radius of the glow, y 1/(outer-surface), z radius of the drawn shell
float4 SunDirection : register(c2); // xyz towards the sun (view, unit), w brightness
float4 Colour : register(c3);       // rgb atmosphere colour (brightest channel 1)
float4 Haze : register(c4);         // x haze at the disc centre, y rim power, z glow falloff, w terminator wrap
float4 SunColour : register(c5);    // rgb light colour
float4 Look : register(c6);         // x forward scattering, y terminator warmth, z veil opacity
float4 ProjectionZ : register(c7);  // projection column z (clip z = dot(float4(P, 1), ProjectionZ))
float4 ProjectionW : register(c8);  // projection column w
float4 EclipseCaster : register(c9);  // eclipse: caster centre (view), radius
float4 EclipseSun : register(c10);     // eclipse: sun centre (view), radius
float4 EclipseControl : register(c11); // eclipse: x range behind the caster, y strength, w on

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

struct ShellOutput
{
    float4 Colour : COLOR0;
    float Depth : DEPTH0;
};

// The depth of a view-space point, so the shell is depth-tested where its light comes from
// (the surface under the haze, the limb for the glow), not where its polygon happens to be.
float DepthOf(float3 P)
{
    float4 H = float4(P, 1.0);
    return saturate(dot(H, ProjectionZ) / max(dot(H, ProjectionW), 1.0e-6));
}

float3 Lit(float3 Normal, float3 Ray, out float Light)
{
    // Wrapped diffuse: the atmosphere carries light a little past the terminator.
    float NoL = dot(Normal, SunDirection.xyz);
    Light = saturate((NoL + Haze.w) / (1.0 + Haze.w));
    // Sunset tint where the sun is low.
    float Low = saturate(1.0 - abs(NoL) * 3.0) * Look.y;
    float3 Tint = Colour.rgb * lerp(1.0, float3(1.0, 0.62, 0.38), Low);
    // Light scattered forward towards the viewer when looking past the planet at the sun.
    float Forward = Look.x * pow(saturate(dot(Ray, SunDirection.xyz)), 8.0) * saturate(NoL + 0.5);
    return Tint * SunColour.rgb * (Light + Forward) * SunDirection.w;
}

ShellOutput PSMain(ShellPixel In)
{
    float3 Camera = -Planet.xyz;               // camera relative to the planet centre
    float3 Ray = normalize(In.ViewPosition);
    float CameraHeight = length(Camera);
    float Surface = Planet.w, Outer = Shell.x;
    // One side of the shell per pixel, whatever the mesh winding and cull state: the half
    // facing the camera from outside the drawn shell, the far half from inside it (near the
    // surface that is the only half in view; its depth comes from DepthOf, not the polygon).
    float Facing = dot(In.ViewPosition - Planet.xyz, In.ViewPosition);
    clip(CameraHeight < Shell.z ? Facing : -Facing);
    ShellOutput Out;
    // The ray's closest approach to the centre (behind the camera: the camera itself).
    float Along = max(-dot(Camera, Ray), 0.0);
    float3 Closest = Camera + Ray * Along;
    float Miss = length(Closest);
    float Light;
    if (Miss < Surface)
    {
        // Over the planet: haze thickening towards the limb, where it meets the glow.
        float3 Hit = Camera + Ray * (Along - sqrt(Surface * Surface - Miss * Miss));
        float3 Normal = Hit / Surface;
        float Rim = pow(1.0 - saturate(dot(Normal, -Ray)), Haze.y);
        float Amount = lerp(Haze.x, 1.0, Rim);
        float HitDistance = Along - sqrt(Surface * Surface - Miss * Miss);
        float Sunlit = Eclipse(Ray * HitDistance);
        float3 C = Lit(Normal, Ray, Light) * Amount * Sunlit;
        Out.Colour = float4(C, Look.z * Amount * (0.35 + 0.65 * Light * Sunlit));
        // The planet mesh is a polygon sphere whose radius need not match Surface exactly: pull
        // the depth a little towards the camera so the haze is never hidden by the real surface
        // close up (a hard edge where the two cross); ships above the surface still cover it.
        Out.Depth = DepthOf(Ray * max(HitDistance * 0.98 - Surface * 0.005, HitDistance * 0.5));
        return Out;
    }
    // Beyond the limb: a glow fading with height, gone at the outer radius.
    float Height = (Miss - Surface) * Shell.y;
    clip(1.0 - Height);
    float Fade = 1.0 - Height;
    float Glow = exp(-Height * Haze.z) * Fade * Fade;
    Out.Colour = float4(Lit(Closest / Miss, Ray, Light) * Glow * Eclipse(Ray * max(Along, 1.0)), 0.0);
    // The closest approach in view space (camera at the origin; Closest is planet-relative);
    // behind the camera (looking away from the planet) a point just ahead of it.
    Out.Depth = DepthOf(Ray * max(Along, 1.0));
    return Out;
}
