#pragma once
namespace Rp9Startup {
inline const char SoftParticleShader[] =
        "row_major float4x4 WorldView : register(c0);\n"
        "row_major float4x4 Proj : register(c4);\n"
        "struct FVsIn { float4 Pos : POSITION; float4 Col : COLOR0; float2 Uv : TEXCOORD0; };\n"
        "struct FVsOut { float4 Pos : POSITION; float4 Col : COLOR0; float2 Uv : TEXCOORD0;\n"
        "                float ViewZ : TEXCOORD1; };\n"
        "FVsOut VSMain(FVsIn In)\n"
        "{\n"
        "    FVsOut Out;\n"
        "    float4 V = mul(float4(In.Pos.xyz, 1.0), WorldView);\n"
        "    Out.Pos = mul(V, Proj);\n"
        "    Out.Col = In.Col;\n"
        "    Out.Uv = In.Uv;\n"
        "    Out.ViewZ = V.z;\n"
        "    return Out;\n"
        "}\n"
        "sampler2D Tex0 : register(s0);\n"
        "sampler2D SceneDepth : register(s1);\n"
        "float4 Fade : register(c0);     // 1 / fade distance, scale rgb too, colour op, alpha op\n"
        "float4 ProjZ : register(c1);    // depth = (x z + y) / (z z + w)\n"
        "float4 Screen : register(c2);   // 1 / depth width, 1 / depth height\n"
        "float4 Fog : register(c3);      // start, end, density, mode (0 none, 1 exp, 2 exp2, 3 linear)\n"
        "float4 FogColor : register(c4);\n"
        "float4 StageOp(float Op, float4 T, float4 D)\n"
        "{\n"
        "    return Op < 2.5 ? T : (Op < 3.5 ? D : T * D);\n"
        "}\n"
        "float4 PSMain(FVsOut In, float2 Pixel : VPOS) : COLOR\n"
        "{\n"
        "    float4 T = tex2D(Tex0, In.Uv);\n"
        "    float4 C = float4(StageOp(Fade.z, T, In.Col).rgb, StageOp(Fade.w, T, In.Col).a);\n"
        "    float Device = tex2D(SceneDepth, (Pixel + 0.5) * Screen.xy).r;\n"
        "    float Scene = abs((ProjZ.y - Device * ProjZ.w) / (Device * ProjZ.z - ProjZ.x));\n"
        "    float F = saturate((Scene - In.ViewZ) * Fade.x);\n"
        "    if (Fog.w > 0.5)\n"
        "    {\n"
        "        float K;\n"
        "        if (Fog.w > 2.5)\n"
        "            K = saturate((Fog.y - In.ViewZ) / max(Fog.y - Fog.x, 1.0e-4));\n"
        "        else if (Fog.w > 1.5)\n"
        "            K = exp(-(In.ViewZ * Fog.z) * (In.ViewZ * Fog.z));\n"
        "        else\n"
        "            K = exp(-In.ViewZ * Fog.z);\n"
        "        C.rgb = lerp(FogColor.rgb, C.rgb, saturate(K));\n"
        "    }\n"
        "    C.a *= F;\n"
        "    if (Fade.y > 0.5)\n"
        "        C.rgb *= F;\n"
        "    return C;\n"
        "}\n";
inline const char WindowedGammaShader[]=
            "sampler2D Scene : register(s0);\n"
            "float4 Curve : register(c1);\n"
            "float4 PSMain(float2 Uv : TEXCOORD0) : COLOR0\n"
            "{\n"
            "    float4 C = tex2D(Scene, Uv);\n"
            "    C.rgb = saturate(Curve.y + pow(saturate(Curve.z * C.rgb + Curve.w), Curve.x));\n"
            "    return C;\n"
            "}\n";
inline const char DriverWarmupShader[]="struct O{float4 p:POSITION;float4 c:COLOR0;float4 t0:TEXCOORD0;float4 t1:TEXCOORD1;float4 t2:TEXCOORD2;float4 t3:TEXCOORD3;float4 t4:TEXCOORD4;float4 t5:TEXCOORD5;float4 t6:TEXCOORD6;float4 t7:TEXCOORD7;}; O main(float3 p:POSITION,float2 uv:TEXCOORD0){O o;o.p=float4(p,1);o.c=1;o.t0=float4(uv,1,1);o.t1=o.t2=o.t3=o.t4=o.t5=o.t6=o.t7=o.t0;return o;}";
inline const char SupersampleShader[]=R"hlsl(
sampler2D Source:register(s0);
float4 Size:register(c0); // source W,H; source/native X,Y
float3 Linear(float3 c){return lerp(c/12.92,pow(max((c+.055)/1.055,0),2.4),step(.04045,c));}
float3 Encoded(float3 c){return lerp(c*12.92,1.055*pow(max(c,0),1./2.4)-.055,step(.0031308,c));}
float4 main(float2 pixel:VPOS):COLOR0 {
 float2 lo=floor(pixel)*Size.zw,hi=lo+Size.zw,first=floor(lo);
 float3 sum=0;float alpha=0;
 [unroll] for(int y=0;y<3;y++) [unroll] for(int x=0;x<3;x++) {
  float2 p=first+float2(x,y);
  float2 overlap=max(0,min(hi,p+1)-max(lo,p));float weight=overlap.x*overlap.y;
  float4 c=tex2Dlod(Source,float4((p+.5)/Size.xy,0,0));
  sum+=Linear(c.rgb)*weight;alpha+=c.a*weight;
 }
 float area=Size.z*Size.w;return float4(Encoded(sum/area),alpha/area);
})hlsl";

}
