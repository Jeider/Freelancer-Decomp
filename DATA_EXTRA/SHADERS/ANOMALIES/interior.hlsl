#include "common.hlsli"
// Fictional playable interior: a cathedral of captured light, NOT a prediction
// of the region behind a real event horizon. No physical escape route implied.
float4 PSMain(PixelIn input) : COLOR0 {
    float2 uv=(input.uv*2-1)*float2(Frame.y,-1);
    float roll=View.y+Frame.x*.035;
    float s,c; sincos(roll,s,c); uv=float2(c*uv.x-s*uv.y,s*uv.x+c*uv.y);
    float3 rd=normalize(float3(uv*.70,1));
    float3 ro=float3(.12*sin(Frame.x*.2),.12*cos(Frame.x*.3),Frame.x*.65);
    float3 light=0;float tr=1,t=.15;
    [loop] for(int k=0;k<148;++k) {
        float3 p=ro+rd*t;
        float z=p.z;
        p.xy-=float2(sin(z*.17),cos(z*.13))*.4;
        float r=length(p.xy),a=atan2(p.y,p.x);
        float radius=3.6+.45*sin(z*.55)+.2*sin(a*5+z*.12);
        float wall=gaussian((r-radius)/.30);
        float n=turbulence(float3(p.xy*3,z*.7));
        float braid=pow(.5+.5*cos(a*11-z*.65+Frame.x*.3),28);
        float hoops=gaussian(sin(z*1.35+sin(a*3)*.35)/.085);
        float fine=pow(.5+.5*sin(a*47+z*2+n*8),14);
        float density=wall*(.065+n*.1+braid*.8+hoops*.32+fine*.16);
        float mist=gaussian((r-radius*.91)/.8)*pow(n,3)*.09;
        float3 tint=lerp(float3(.16,.10,.8),float3(.025,.55,1.4),.5+.5*sin(z*.21+a*2));
        float3 color=tint*(.25+n)+float3(2.6,.60,.10)*(braid+hoops*.5);
        float ds=.055+t*.035;
        integrate(light,tr,color,density+mist,ds);
        t+=ds;
        if(tr<.004||t>65) break;
    }
    // Remaining transmission ends in darkness; no fake "exit star" at infinity.
    return float4(light,1);
}
