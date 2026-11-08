#pragma once
// Initial optical-flow provider. Estimates current->previous displacement from
// unprocessed colour only; no feedback from the neural output. Native skeletal
// motion can replace this provider without changing the Feed transport.
static char const BaseNeuralShaders[] = R"hlsl(
cbuffer Params : register(b0) { uint Width, Height, Reset, Mode; float Strength; float3 Padding; };
Texture2D<float4> Current : register(t0);
Texture2D<float4> Previous : register(t1);
Texture2D<float> RawDepth : register(t2);
Texture2D<float4> Neural : register(t3);
RWTexture2D<float4> ColorOut : register(u0);
RWTexture2D<float> DepthOut : register(u1);
RWTexture2D<float2> MotionOut : register(u2);

[numthreads(8,8,1)] void CopyGuides(uint3 tid : SV_DispatchThreadID) {
    if (tid.x >= Width || tid.y >= Height) return;
    ColorOut[tid.xy] = Current.Load(int3(tid.xy,0));
    DepthOut[tid.xy] = Mode == 1 ? 0.5 : RawDepth.Load(int3(tid.xy,0));
}
float Luma(Texture2D<float4> tex, int2 p) {
    p = clamp(p,int2(0,0),int2(Width-1,Height-1));
    return dot(tex.Load(int3(p,0)).rgb,float3(0.2126,0.7152,0.0722));
}
float ErrorAt(int2 p, int2 shift) {
    float error = 0;
    [unroll] for(int y=-1;y<=1;y++) [unroll] for(int x=-1;x<=1;x++) {
        int2 offset=int2(x,y)*2;
        error+=abs(Luma(Current,p+offset)-Luma(Previous,p+shift+offset));
    }
    return error*(5.0/9.0) + 0.0001 * dot(float2(shift),float2(shift));
}
[numthreads(8,8,1)] void Flow(uint3 tid : SV_DispatchThreadID) {
    int2 p = int2(tid.xy)*4;
    if (p.x >= Width || p.y >= Height) return;
    int2 best = 0;
    if (Reset == 0 && Mode == 2) {
        float error = ErrorAt(p,0);
        // Preserve small character/camera motion: a 4-pixel coarse grid alone
        // can choose a distant look-alike before the fine search even starts.
        [loop] for (int y=-4;y<=4;y++) [loop] for (int x=-4;x<=4;x++) {
            int2 v=int2(x,y); float e=ErrorAt(p,v);
            if(e<error) {error=e;best=v;}
        }
        [loop] for (int y=-4;y<=4;y++) [loop] for (int x=-4;x<=4;x++) {
            int2 v=int2(x,y)*4; float e=ErrorAt(p,v);
            if(e<error) {error=e;best=v;}
        }
        int2 center=best;
        [loop] for (int y=-2;y<=2;y++) [loop] for (int x=-2;x<=2;x++) {
            int2 v=center+int2(x,y);float e=ErrorAt(p,v);
            if(e<error) {error=e;best=v;}
        }
        // Reject a poor match, including most disocclusions and animated lighting.
        if(error>0.25) best=0;
    }
    // The coarse search is only a seed. Never broadcast one integer vector to a
    // 4x4 block: that makes temporal reprojection jump on the block boundaries.
    [loop] for(int y=0;y<4;y++) [loop] for(int x=0;x<4;x++) {
        int2 q=p+int2(x,y); if(q.x>=Width||q.y>=Height) continue;
        float2 motion=0;
        if(Reset==0 && Mode==2) {
            int2 local=0; float error=ErrorAt(q,0);
            [loop] for(int dy=-1;dy<=1;dy++) [loop] for(int dx=-1;dx<=1;dx++) {
                int2 v=best+int2(dx,dy); float e=ErrorAt(q,v);
                if(e<error) {error=e;local=v;}
            }
            if(error<=0.25) {
                // Subpixel minimum of the matching cost in each direction.
                float2 lo=float2(ErrorAt(q,local-int2(1,0)),ErrorAt(q,local-int2(0,1)));
                float2 hi=float2(ErrorAt(q,local+int2(1,0)),ErrorAt(q,local+int2(0,1)));
                float2 curvature=lo+hi-2*error;
                float2 sub=clamp(.5*(lo-hi)/max(curvature,1e-5),-.5,.5);
                sub=curvature>1e-5?sub:float2(0,0);
                // Identical samples must remain exactly stationary.
                motion=error<1e-6?float2(local):float2(local)+sub;
            }
        }
        MotionOut[q]=motion;
    }
}
float4 Fullscreen(uint id : SV_VertexID) : SV_Position {
    float2 p=float2((id<<1)&2,id&2); return float4(p*float2(2,-2)+float2(-1,1),0,1);
}
float3 Linear(float3 c) {return lerp(c/12.92,pow(max((c+0.055)/1.055,0),2.4),step(0.04045,c));}
float3 Encoded(float3 c) {return lerp(c*12.92,1.055*pow(max(c,0),1.0/2.4)-0.055,step(0.0031308,c));}
float4 Composite(float4 pos : SV_Position) : SV_Target {
    int3 p=int3(pos.xy,0); float4 a=Current.Load(p),b=Neural.Load(p);
    if(Strength<=0) return a; // exact original pixels for the live A/B slider
    if(Mode==1) return b;
    return float4(Encoded(lerp(Linear(a.rgb),Linear(b.rgb),Strength)),a.a);
}
)hlsl";
