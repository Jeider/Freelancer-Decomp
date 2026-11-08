#pragma once
// Moderate SDR looks. Keep black/white endpoints and alpha; skin remains close to source.
static char const ColorGradeShader[]=R"hlsl(
sampler2D Scene:register(s0);
float4 Settings:register(c1);
float4 PSMain(float2 uv:TEXCOORD0):COLOR0 {
 float4 source=tex2D(Scene,uv);
 float preset=Settings.x;
 if(preset<.5)return source;
 float3 c=source.rgb;
 float luma=dot(c,float3(.2126,.7152,.0722));
 float saturation=preset<1.5?1.06:.98;
 c=lerp(luma.xxx,c,saturation);
 // Smooth contrast adjustment without clipping the low/high end of the scene.
 c=saturate(c);float contrast=preset<1.5?.12:.16;
 c+=contrast*c*(1-c)*(2*c-1);
 float envelope=4*luma*(1-luma);
 if(preset>1.5 && preset<2.5)c+=envelope*float3(.018,.004,-.014);
 if(preset>2.5)c+=envelope*float3(-.012,.003,.018);
 return float4(saturate(c),source.a);
})hlsl";
