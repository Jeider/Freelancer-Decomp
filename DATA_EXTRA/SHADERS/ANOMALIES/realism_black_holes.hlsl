#include "realism_common.hlsli"
#include "realism_gr.hlsli"
#ifndef VARIANT
#define VARIANT 2
#endif
float4 PSMain(PixelIn input) : COLOR0 {
    float3 ro,rd;camera(input.uv,ro,rd);
    float radius=length(ro);
    float impact=length(cross(ro,rd))/sqrt(max(1-1/radius,.001));
    float footprint=max(abs(ddx(impact))+abs(ddy(impact)),.001);
    float3 colour=0;
    int rays=1;
#if EPIC_QUALITY >= 2
    // Deterministic subpixel integration close to the critical capture curve.
    // 3*sqrt(3)/2 is b_critical in Schwarzschild-radius units.
    if(abs(impact-2.598076211)<footprint*2.5) rays=4;
#endif
    // A dynamic loop retains one copy of the integrator in SM3 bytecode.
    [loop] for(int k=0;k<rays;++k) {
        float2 offset=rays>1?float2((k%2)*.5-.25,(k/2)*.5-.25)*Frame.zw:float2(0,0);
        camera(input.uv+offset,ro,rd);
        colour+=traceSchwarzschild(ro,rd,VARIANT)/rays;
    }
    return float4(colour,1);
}
