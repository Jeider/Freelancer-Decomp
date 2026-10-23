#include "common.hlsli"
sampler2D SceneDepth : register(s0);
float4 Sun : register(c0); // viewport UV, source radius in height units, strength
float4 Tint : register(c1); // RGB, width/height
float4 SourceDepth : register(c2); // solar front depth, world viewport max depth

FFullscreenVertex VSMain(float3 Position : POSITION,float2 Uv : TEXCOORD0)
{ return RPExFullscreenVS(Position,Uv); }

float Sky(float2 Uv)
{
    // The viewport border is not an occluder. Never clamp an out-of-view
    // solar sample onto geometry at the edge of the depth texture.
    if(any(Uv<0) || any(Uv>1)) return 1;
    float Depth=tex2Dlod(SceneDepth,float4(Uv,0,0)).r;
    if(Depth>=0.99999994) return 1; // cleared sky
    if(Depth>SourceDepth.y+0.00000012) return 0; // cockpit depth partition
    return step(SourceDepth.x,Depth); // only geometry in front of the sun blocks
}
float4 PSMain(FFullscreenVertex In) : COLOR0
{
    float2 Delta=In.TexCoord-Sun.xy;
    float2 Metric=Delta*float2(Tint.w,1);
    float Distance=length(Metric);
    // A moderate reach, wider for a bigger disc (giants glow wider, dwarfs stay compact): enough
    // background glow for the shafts cut by geometry to read. Never brighten opaque hulls or the
    // cockpit itself.
    float Envelope=saturate(1-Distance/(0.35+3.0*Sun.z));
    [branch] if(Envelope<=0 || Sky(In.TexCoord)<0.5) return 0;
    float Sum=0;
    // Integrate the visible solar disc along the radial line. Different rays
    // sample different silhouettes, rather than using one binary sun query.
    [loop] for(int I=0;I<64;++I)
    {
        float T=(I+0.5)/64.0;
        float2 Uv=In.TexCoord-Delta*T;
        float2 R=(Uv-Sun.xy)*float2(Tint.w,1);
        float Disc=exp2(-dot(R,R)/max(Sun.z*Sun.z,0.000004)*2);
        Sum+=Disc*Sky(Uv);
    }
    // No spokes of its own: a soft glow, and shafts where something stands in front of the
    // disc. The star's spikes are its own [spines], drawn by the retail path.
    // Restrained, but bright enough behind geometry for its shafts to show.
    float Rays=Sum*(1.0/64.0)*Envelope*Envelope*Sun.w*0.5;
    return float4(Tint.rgb*Rays,0);
}

