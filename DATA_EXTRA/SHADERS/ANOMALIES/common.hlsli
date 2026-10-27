// Standalone D3D9 / SM3 experiments. Linear HDR throughout; see tools/space_anomalies.
// c0 = time, aspect, 1/width, 1/height; c1 = inclination, yaw, exposure, distance.
// c2 = flare amount, reserved, reserved, reserved.
float4 Frame : register(c0);
float4 View : register(c1);
float4 Event : register(c2);
sampler2D SkyMap : register(s0); // linear equirectangular RGB; U wrap, V clamp
sampler3D NoiseMap : register(s1); // periodic smooth noise; wrap XYZ, linear
static const float PI = 3.14159265359;
struct VertexIn { float4 position : POSITION0; float2 uv : TEXCOORD0; };
struct PixelIn { float4 position : POSITION0; float2 uv : TEXCOORD0; };
PixelIn VSMain(VertexIn v) {
    PixelIn o; o.position = v.position;
    o.position.xy += float2(-Frame.z, Frame.w) * o.position.w;
    o.uv = v.uv; return o;
}
float3 rotateX(float3 p, float a) {
    float s, c; sincos(a, s, c); return float3(p.x, c*p.y-s*p.z, s*p.y+c*p.z);
}
float3 rotateY(float3 p, float a) {
    float s, c; sincos(a, s, c); return float3(c*p.x+s*p.z, p.y, -s*p.x+c*p.z);
}
void camera(float2 uv, out float3 ro, out float3 rd) {
    float2 p = (uv*2-1)*float2(Frame.y,-1);
    ro = rotateY(rotateX(float3(0,0,View.w),-View.x), View.y);
    rd = rotateY(rotateX(normalize(float3(p*.50,-1)),-View.x),View.y);
}
float noise(float3 p) { return tex3Dlod(NoiseMap,float4(p*.13,0)).r; }
float turbulence(float3 p) { return noise(p)*.65+noise(p*2.03)*.25+noise(p*4.07)*.1; }
float3 sky(float3 d) {
    d=normalize(d);
    float2 uv=float2(atan2(d.z,d.x)/(2*PI)+.5, acos(clamp(d.y,-1,1))/PI);
    return tex2Dlod(SkyMap,float4(uv,0,0)).rgb;
}
float sphereHit(float3 ro,float3 rd,float radius) {
    float b=dot(ro,rd),q=b*b-dot(ro,ro)+radius*radius;
    if(q<0) return 1e5;
    float t=-b-sqrt(q); return t>0?t:1e5;
}
float gaussian(float x) { return exp(-x*x); }
// Front-to-back emission/absorption: stable for any positive step length.
void integrate(inout float3 light,inout float transmission,float3 emission,float density,float ds) {
    float a=1-exp(-max(density,0)*ds);
    light+=transmission*a*emission; transmission*=1-a;
}
