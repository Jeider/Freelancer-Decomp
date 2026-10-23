#include "common.hlsli"
// Port-only space haze: one fullscreen pass of world-anchored gas at a few fixed distances
// ("shells") from the camera. Each pixel's view ray is sampled in a tileable 3D noise at every
// shell, front to back; nearer shells move faster than far ones when flying, so open space gets
// parallax and a sense of a medium for a fixed small cost (no sprites, no overdraw). A shell is
// hidden where the scene is nearer than it. Output is premultiplied (ONE / INVSRCALPHA).
sampler2D SceneDepth : register(s0);
sampler3D Noise : register(s1); // R: density fBm, G: colour mix fBm; one tile = 1.0

float4 ProjZ : register(c0);          // projection z/w rows (RPExLinearDepth)
float4 ViewRect : register(c1);       // the camera viewport in target UV: left, top, width, height
float4 ProjInv : register(c2);        // 1/ScaleX, 1/ScaleY
float4 CamRow[3] : register(c3);      // view rotation rows (world axes)
float4 ShellOrigin[4] : register(c6); // xyz: camera/scale + drift (tile units, wrapped), w: distance/scale
float4 ShellDist : register(c10);     // the shells' distances in metres (occlusion test)
float4 ColourA : register(c11);       // rgb, alpha of a fully covered shell
float4 ColourB : register(c12);       // rgb (mixed in by the G channel)
float4 Cover : register(c13);         // coverage, softness, detail, occlusion softness
float4 Lighting : register(c14);      // ambient, forward, forward power, has sun
float4 SunInfo : register(c15);       // direction to the sun (xyz), shell count
float4 SunClear : register(c16);      // x how much the gas thins toward the sun, y its power
float4 Flash : register(c17);         // rgb flicker colour * strength (0 = none), w time (s)
float4 FlashCells : register(c18);    // per shell: flicker spot cells per noise tile
float4 Character : register(c20);     // detail frequency, grain weight, grain frequency, billow
float4 FlashMore : register(c19);     // x share of spots that flicker, y gap (s), z duration (s),
                                      // w the flicker frame (a new random each)

FFullscreenVertex VSMain(float3 Position : POSITION, float2 Uv : TEXCOORD0)
{ return RPExFullscreenVS(Position, Uv); }

float4 PSMain(FFullscreenVertex In) : COLOR0
{
    float2 ViewUv = (In.TexCoord - ViewRect.xy) / ViewRect.zw;
    if (any(ViewUv < 0.0) || any(ViewUv > 1.0))
        return float4(0.0, 0.0, 0.0, 0.0);

    // View ray: D3D view space at z = 1, then into world axes (the game's view looks down -z).
    float2 Ndc = float2(ViewUv.x * 2.0 - 1.0, 1.0 - ViewUv.y * 2.0);
    float2 ViewXY = Ndc * ProjInv.xy;
    float3 Dir = ViewXY.x * CamRow[0].xyz + ViewXY.y * CamRow[1].xyz - CamRow[2].xyz;
    float DirLength = length(Dir);
    Dir /= DirLength;

    float Device = tex2Dlod(SceneDepth, float4(In.TexCoord, 0.0, 0.0)).r;
    float SceneT = Device < 1.0 ? RPExLinearDepth(Device, ProjZ) * DirLength : 1.0e30;

    float Light = 1.0;
    float Thin = 1.0;
    if (Lighting.w > 0.5)
    {
        float CosSun = dot(Dir, SunInfo.xyz);
        Thin = 1.0 - SunClear.x * pow(saturate(CosSun), SunClear.y);
        Light = Lighting.x + (1.0 - Lighting.x) * (0.5 + 0.5 * CosSun)
              + Lighting.y * pow(saturate(CosSun), Lighting.z);
    }

    float3 Rgb = 0.0;
    float T = 1.0;
    [unroll] for (int I = 0; I < 4; ++I)
    {
        if (I < SunInfo.w)
        {
            float3 Q = ShellOrigin[I].xyz + Dir * ShellOrigin[I].w;
            float4 N = tex3Dlod(Noise, float4(Q, 0.0));
            float Density = N.r;
            if (Cover.z > 0.0)
                Density = (Density + Cover.z * tex3Dlod(Noise, float4(Q * Character.x + 17.3, 0.0)).r)
                          / (1.0 + Cover.z);
            // Ridged (billow): drifts and ridges instead of round blobs.
            Density = lerp(Density, 1.0 - abs(2.0 * Density - 1.0), Character.w);
            // Grain: fine roughness about the mean, so the coverage stays where it was.
            [branch] if (Character.y > 0.0)
                Density += Character.y * (tex3Dlod(Noise, float4(Q * Character.z + 31.7, 0.0)).r - 0.5);
            float C = smoothstep(Cover.x - Cover.y, Cover.x + Cover.y, Density);
            float D = ShellDist[I];
            float Visible = saturate((SceneT - D) / (D * Cover.w));
            float A = ColourA.w * C * Visible * Thin;
            float3 Col = lerp(ColourA.rgb, ColourB.rgb, N.g) * Light;
            // Flicker, as retail's cloud puffs: a soft round spot per world-anchored cell (a share
            // of them) waits (0.8 .. 1.5) * gap on its own clock, then for the duration its light
            // is rand * rand, new every flicker frame.
            [branch] if (Flash.r + Flash.g + Flash.b > 0.0)
            {
                float3 Cell = Q * FlashCells[I];
                float3 Id = floor(Cell);
                float3 F = frac(Cell) - 0.5;
                float H1 = frac(sin(dot(Id, float3(12.9898, 78.233, 37.719)) + I * 7.13) * 43758.5453);
                float H2 = frac(H1 * 91.37 + 0.123);
                float H3 = frac(H1 * 53.11 + 0.71);
                float Period = FlashMore.y * (0.8 + 0.7 * H2) + FlashMore.z;
                float Age = fmod(Flash.w + H3 * Period, Period);
                if (H1 < FlashMore.x && Age < FlashMore.z)
                {
                    float R1 = frac(sin(dot(Id, float3(39.346, 11.135, 83.155)) + FlashMore.w * 1.731) * 43758.5453);
                    float R2 = frac(R1 * 71.37 + 0.37);
                    float Spot = saturate(1.0 - length(F) * 2.0);
                    Col += Flash.rgb * (R1 * R2 * Spot * Spot);
                }
            }
            Rgb += T * A * Col;
            T *= 1.0 - A;
        }
    }
    return float4(Rgb, 1.0 - T);
}
