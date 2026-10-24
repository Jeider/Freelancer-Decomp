float4 View[3]:register(c0);
float4 Projection[4]:register(c3);
float4 Remap:register(c7);
float4 VertexDepth:register(c8);
struct Vertex {float3 P:POSITION0;float4 C:COLOR0;float2 UV:TEXCOORD0;};
struct Interp {float4 P:POSITION0;float4 C:COLOR0;float2 UV:TEXCOORD0;float Z:TEXCOORD1;float4 Bounds:TEXCOORD2;};
Interp VSMain(Vertex In)
{
    Interp O;float4 P=float4(In.P,1);
    float4 V=float4(dot(P,View[0]),dot(P,View[1]),-dot(P,View[2]),1);
    float4 C=float4(dot(V,Projection[0]),dot(V,Projection[1]),dot(V,Projection[2]),dot(V,Projection[3]));
    O.Bounds=C.w*1.00001+float4(C.xy,-C.xy);
    C.xy=C.xy*Remap.xy+Remap.zw*C.w;
    // Ex passes reset viewport depth to [0,1]; preserve the caller's scene partition.
    C.z=C.z*(VertexDepth.w-VertexDepth.z)+C.w*VertexDepth.z;
    O.P=C;O.Z=V.z;O.C=In.C;O.UV=In.UV;return O;
}
float4 State:register(c0); // time96, intensity, inverse target width/height
float4 Tint:register(c1); // shared route/tunnel body RGB, mode0 lane /1 jump
float4 Depth:register(c2); // near/far/depth-range min/max
float4 Bounds:register(c3);
float4 Accent:register(c4); // shared accent RGB, palette enabled
sampler2D SceneDepth:register(s0);
sampler2D SceneColor:register(s1);
void ClipLaneTail(Interp In)
{
    // Keep the first quarter of the original long trail, including its original UVs
    // and vertex envelope. Neither the nose nor hyperjump trails are cropped.
    clip(In.C.g>.5 && Tint.w<.5 ? .25-In.UV.x : 1);
}
float LaneTrailEnvelope(Interp In)
{
    if(In.C.g<=.5 || Tint.w>=.5)return 1;
    // Fade only the ends of the retained quarter, keeping the full trail's UV scale.
    return smoothstep(0,.03,In.UV.x)*(1-smoothstep(.15,.25,In.UV.x));
}
float DepthVisibility(float2 UV,float EffectZ)
{
    float D=tex2Dlod(SceneDepth,float4(clamp(UV,Bounds.xy,Bounds.zw),0,0)).r;
    if(D>Depth.w+.00000012&&D<.99999994)return 0;
    float Z=saturate((D-Depth.z)/max(Depth.w-Depth.z,.000001));
    float Scene=D>=.99999994?1e8:Depth.x*Depth.y/max(Depth.y-Z*(Depth.y-Depth.x),.001);
    return saturate((Scene-EffectZ)/max(.35,EffectZ*.0006));
}
float4 PSMain(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Bounds);
    float2 UV=(Pixel+.5)*State.zw;
    clip(float4(UV-Bounds.xy,Bounds.zw-UV));
    ClipLaneTail(In);
    if(State.y<=0)return 0;
    float Soft=DepthVisibility(UV,In.Z);
    float Clock=State.x*(6.283185307/96);
    float Energy;
    if(In.C.g>.5)
    {
        float Skin=exp2(-In.UV.y*In.UV.y*7);
        float Knots=pow(.5+.5*sin(In.UV.x*45-Clock*576+In.C.b*12),5);
        float Fibre=.65+.35*sin(In.UV.x*93+In.UV.y*4-Clock*384+In.C.b*6);
        Energy=Skin*(.38+Knots*1.6)*Fibre;
    }
    else
    {
        float R2=dot(In.UV,In.UV);
        float Angle=atan2(In.UV.y,In.UV.x+.0001);
        float Core=exp2(-R2*65)*3.8;
        float Skin=exp2(-R2*6)*(1-smoothstep(.35,1,R2));
        float Folds=pow(.5+.5*sin(Angle*3+R2*18-Clock*288),3);
        Energy=Core+Skin*(.12+Folds*.45);
    }
    float Gain=Energy*In.C.r*max(0,State.y)*Soft*LaneTrailEnvelope(In);
    float3 Colour=lerp(float3(.035,.43,1),float3(.38,.88,1),saturate(Energy*.3));
    Colour=lerp(Colour,float3(.50,.85,1),Tint.w*.12);
    if(Accent.w>.5)
    {
        // Match the corridor's hue without multiplying warm/green palettes by blue.
        float Peak=max(Colour.r,max(Colour.g,Colour.b));
        float White=saturate(min(Colour.r,min(Colour.g,Colour.b))/max(Peak,.0001));
        float3 Route=lerp(Tint.rgb,Accent.rgb,saturate(White+Peak*.22));
        Colour=Peak*lerp(Route,float3(1,1,1),White*White*White*.78);
    }
    return float4(Colour*Gain,0); // additive ONE/ONE, no depth writes
}

float4 PSWarp(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Bounds);
    float2 UV=(Pixel+.5)*State.zw;
    clip(float4(UV-Bounds.xy,Bounds.zw-UV));
    // Derivatives are evaluated before divergent branches. The gradient projects the
    // local cap/ribbon normal onto the screen, following turns and side views.
    float2 DX=ddx(In.UV),DY=ddy(In.UV);
    // Refraction belongs to the bow cap only; trails are luminous geometry.
    if(In.C.g>.5)return 0;
    float Clock=State.x*(6.283185307/96);
    float R2=dot(In.UV,In.UV);
    float2 Direction=float2(dot(In.UV,DX),dot(In.UV,DY));
    float Mask=exp2(-R2*3)*(1-smoothstep(.65,1,R2));
    float Wave=sin(R2*16-Clock*192)*smoothstep(0,.06,R2);
    Direction*=rsqrt(max(dot(Direction,Direction),1e-10));
    float Soft=DepthVisibility(UV,In.Z);
    float Coverage=Mask*In.C.r*saturate(State.y)*Soft*.65;
    if(Coverage<.001)return 0;
    float2 Edge=min(UV-Bounds.xy,Bounds.zw-UV)/State.zw;
    float Fade=smoothstep(0,4,min(Edge.x,Edge.y));
    // Four pixels at 1080p; displacement is confined to the existing geometry.
    float2 Offset=Direction*State.zw*(.0037/State.w)*Wave*Mask*saturate(State.y)*Fade;
    float2 Candidate=clamp(UV+Offset,Bounds.xy,Bounds.zw);
    float2 T=State.zw;
    float Source=min(DepthVisibility(Candidate+T,In.Z),DepthVisibility(Candidate-T,In.Z));
    Source=min(Source,DepthVisibility(Candidate+float2(T.x,-T.y),In.Z));
    Source=min(Source,DepthVisibility(Candidate+float2(-T.x,T.y),In.Z));
    // Reject the linear-filter footprint if it would pull a nearer hull into the wake.
    if(Source<.999)return 0;
    return float4(tex2Dlod(SceneColor,float4(Candidate,0,0)).rgb*Coverage,Coverage);
}
