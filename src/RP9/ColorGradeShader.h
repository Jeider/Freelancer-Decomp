#pragma once
// Display-referred SDR. Black and alpha stay. Color casts are half-strength.
// Exposure and an S-curve do the contrast. No neighbor samples: a wide clarity
// tap ghosts hard edges against space.
// 1 is the source color with midtone luma contrast only: black, white and chroma
// stay, so highlights are not pushed into a burned color. 2 is darker, teal in
// the shadows and gold in the lights. 3 cools the balance.
static char const ColorGradeShader[]=R"hlsl(
sampler2D Scene:register(s0);
float4 Settings:register(c1);
float4 PSMain(float2 uv:TEXCOORD0):COLOR0 {
 float4 source=tex2D(Scene,uv);
 float preset=Settings.x;
 if(preset<.5)return source;
 float3 c=source.rgb;
 float luma=dot(c,float3(.2126,.7152,.0722));
 float exposure,contrast;
 float3 balance;
 if(preset<1.5){
  float y=luma+(luma-.5)*.65*(4*luma*(1-luma));
  c=y+(c-luma);
  return float4(saturate(c),source.a);
 }else if(preset<2.5){
  exposure=.94;contrast=.58;
  c=saturate(lerp(luma.xxx,c,1.32));
  balance=lerp(float3(.74,.95,1.175),float3(1.21,1.025,.71),saturate(luma*2.4));
 }else{
  exposure=.97;contrast=.52;
  c=lerp(luma.xxx,c,.56);
  balance=float3(.75,.86,1.24);
 }
 c*=exposure;
 c=lerp(c,c*c*(3-2*c),contrast);
 c*=balance;
 return float4(saturate(c),source.a);
})hlsl";
