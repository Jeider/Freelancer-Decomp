#include "common.hlsli"
// Quality-first look development. Event.y selects a radiation/sensor composite.
// No game installation or ALE dependencies. All outputs remain linear HDR.
#ifndef EPIC_QUALITY
#define EPIC_QUALITY 2
#endif
#if EPIC_QUALITY >= 2
#define GR_PASSES 8
#define GR_STEP .0125
#define VOLUME_PASSES 4
#else
#define GR_PASSES 4
#define GR_STEP .022
#define VOLUME_PASSES 2
#endif

float fbm5(float3 p) {
    return noise(p)*.516+noise(p*2.01)*.258+noise(p*4.03)*.129+
           noise(p*8.09)*.0645+noise(p*16.21)*.03225;
}
float3 quietSky(float3 direction) {
    float3 c=sky(direction);
    float luminance=dot(c,float3(.2126,.7152,.0722));
    return lerp(luminance.xxx,c,.32);
}
// Three sampled Planck bands, white-balanced to 6500 K. Not a full CIE integral.
// B_nu(g*T) already contains the g^3 spectral radiance transformation; do not
// multiply by a second Doppler beaming term after shifting the temperature.
float3 thermalRGB(float kelvin) {
    float3 wavelength=float3(610,550,460);
    float3 refExponent=14387770/(wavelength*6500);
    float3 exponent=clamp(14387770/(wavelength*max(kelvin,600)),.01,60);
    return min((exp(refExponent)-1)/max(exp(exponent)-1,.0001),32000);
}
void transport(inout float3 radiance,inout float3 transmission,
               float3 emissivity,float3 extinction,float ds) {
    float3 sigma=max(extinction,0);
    float3 stepTransmission=exp(-sigma*ds);
    float3 integral=float3(sigma.x<1e-5?ds:(1-stepTransmission.x)/sigma.x,
                          sigma.y<1e-5?ds:(1-stepTransmission.y)/sigma.y,
                          sigma.z<1e-5?ds:(1-stepTransmission.z)/sigma.z);
    radiance+=transmission*max(emissivity,0)*integral;
    transmission*=stepTransmission;
}
float henyeyGreenstein(float cosine,float g) {
    return (1-g*g)/pow(max(1+g*g-2*g*cosine,.04),1.5);
}
float2 volumeInterval(float3 ro,float3 rd,float radius) {
    float b=dot(ro,rd),q=b*b-dot(ro,ro)+radius*radius;
    if(q<0) return float2(0,0);
    float root=sqrt(q);
    return float2(max(0,-b-root),max(0,-b+root));
}
