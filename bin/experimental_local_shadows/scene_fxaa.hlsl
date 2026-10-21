// Spatial edge AA for the completed space scene. Submitted before the HUD.
sampler2D Scene : register(s0);
float4 PixelSize : register(c0);
float Luma(float3 C) {return dot(C,float3(0.299,0.587,0.114));}
float4 PSMain(float2 Uv:TEXCOORD0):COLOR0
{
    float2 P=PixelSize.xy;
    float4 Center=tex2Dlod(Scene,float4(Uv,0,0));
    float3 NW=tex2Dlod(Scene,float4(Uv+P*float2(-1,-1),0,0)).rgb;
    float3 NE=tex2Dlod(Scene,float4(Uv+P*float2( 1,-1),0,0)).rgb;
    float3 SW=tex2Dlod(Scene,float4(Uv+P*float2(-1, 1),0,0)).rgb;
    float3 SE=tex2Dlod(Scene,float4(Uv+P*float2( 1, 1),0,0)).rgb;
    float M=Luma(Center.rgb),A=Luma(NW),B=Luma(NE),C=Luma(SW),D=Luma(SE);
    float Low=min(M,min(min(A,B),min(C,D))),High=max(M,max(max(A,B),max(C,D)));
    if(High-Low<max(0.0312,High*0.063)) return Center;
    float2 Edge=float2(-(A+B-C-D),A+C-B-D);
    float Reduce=max((A+B+C+D)*0.03125,0.0078125);
    Edge=clamp(Edge/(min(abs(Edge.x),abs(Edge.y))+Reduce),-8,8)*P;
    float3 Inner=(tex2Dlod(Scene,float4(Uv-Edge/6,0,0)).rgb+
                  tex2Dlod(Scene,float4(Uv+Edge/6,0,0)).rgb)*0.5;
    float3 Wide=Inner*0.5+(tex2Dlod(Scene,float4(Uv-Edge*0.5,0,0)).rgb+
                           tex2Dlod(Scene,float4(Uv+Edge*0.5,0,0)).rgb)*0.25;
    float W=Luma(Wide);
    return float4(W<Low || W>High ? Inner : Wide,Center.a);
}
