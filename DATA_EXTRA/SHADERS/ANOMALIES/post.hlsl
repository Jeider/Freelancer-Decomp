#include "common.hlsli"
sampler2D Source : register(s2);
sampler2D Bloom : register(s3);
// c3 = horizontal/vertical texel step, threshold, bloom amount.
float4 Post : register(c3);
float4 PSExtract(PixelIn i) : COLOR0 {
    float3 c=tex2D(Source,i.uv).rgb;
#if REALISTIC_LOOK
    // Exposure-aware soft knee: glare follows the camera, not a painted corona.
    float peak=max(c.r,max(c.g,c.b))*View.z;
    float knee=max(Post.z*.35,.001);
    float soft=clamp(peak-Post.z+knee,0,2*knee);
    float excess=max(peak-Post.z,soft*soft/(4*knee));
    return float4(c*max(excess,0)/max(peak,.001),1);
#else
    return float4(c*saturate((max(c.r,max(c.g,c.b))-Post.z)/max(.01,max(c.r,max(c.g,c.b)))),1);
#endif
}
float4 PSBlur(PixelIn i) : COLOR0 {
    float3 c=tex2D(Source,i.uv).rgb*.227027;
    c+=(tex2D(Source,i.uv+Post.xy*1.384615).rgb+tex2D(Source,i.uv-Post.xy*1.384615).rgb)*.316216;
    c+=(tex2D(Source,i.uv+Post.xy*3.230769).rgb+tex2D(Source,i.uv-Post.xy*3.230769).rgb)*.070270;
    return float4(c,1);
}
float4 PSResolve(PixelIn i) : COLOR0 {
    float3 x=max(0,(tex2D(Source,i.uv).rgb+tex2D(Bloom,i.uv).rgb*Post.w)*View.z);
    float3 c=saturate((x*(2.51*x+.03))/(x*(2.43*x+.59)+.14));
    return float4(pow(c,1/2.2),1);
}
