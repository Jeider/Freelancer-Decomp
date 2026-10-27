#include "realism_common.hlsli"
#include "realism_gr.hlsli"
// Exterior horizon approach. A view from *inside* an event horizon cannot be
// replaced by an invented glowing tunnel and then labelled physically realistic.
float4 PSMain(PixelIn input) : COLOR0 {
    float2 screen=(input.uv*2-1)*float2(Frame.y,-1);
    float radius=max(1.08,View.w-Frame.x*.035);
    float3 ro=rotateY(rotateX(float3(0,0,radius),-View.x),View.y);
    // Look tangentially across the horizon, keeping the capture boundary in view.
    float3 local=normalize(float3(1+screen.x*.65,screen.y*.65,-.18));
    float3 rd=rotateY(rotateX(local,-View.x),View.y);
    return float4(traceSchwarzschild(ro,rd,2),1);
}
