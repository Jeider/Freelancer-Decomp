float4 Remap:register(c7);
struct Vertex {float3 P:POSITION0;float4 C:COLOR0;float2 UV:TEXCOORD0;};
struct Interp {float4 P:POSITION0;float4 Clip:TEXCOORD0;};
Interp VSMain(Vertex In)
{
    Interp Out;Out.P=float4(In.P.xy*Remap.xy+Remap.zw,0,1);
    Out.Clip=1.00001+float4(In.P.xy,-In.P.xy);return Out;
}
float4 State:register(c0); // simulation time modulo96, gain, inverse target W/H
float4 Bounds:register(c1); // cinematic viewport pixel-centre UV bounds
sampler2D Scene:register(s0);
float4 PSMain(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Clip);
    float2 UV=(Pixel+.5)*State.zw;
    clip(float4(UV-Bounds.xy,Bounds.zw-UV));
    float4 Base=tex2Dlod(Scene,float4(UV,0,0));
    if(State.y<=0)return Base;
    float2 P=(UV-Bounds.xy)/max(Bounds.zw-Bounds.xy,.000001);
    float T=State.x*(6.283185307/96);
    float2 Wave=float2(sin(P.y*6+P.x*2+T*24)+.35*sin(P.y*13-T*17),
                      sin(P.x*7-P.y*2-T*19)+.35*sin(P.x*12+T*13))/1.35;
    float Edge=min(min(P.x,1-P.x),min(P.y,1-P.y));
    // At most3.2 pixels per axis at1080p; no colour splitting, blur or camera motion.
    float Pixels=3.2*(Bounds.w-Bounds.y)/(1080*State.w);
    float2 Offset=Wave*State.zw*Pixels*saturate(State.y)*smoothstep(0,.025,Edge);
    return tex2Dlod(Scene,float4(clamp(UV+Offset,Bounds.xy,Bounds.zw),0,0));
}
