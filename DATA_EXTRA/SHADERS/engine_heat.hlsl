float4 View[3]:register(c0);
float4 Projection[4]:register(c3);
float4 Remap:register(c7);
float4 VertexDepth:register(c8);
struct Vertex {float3 P:POSITION0;float4 C:COLOR0;float2 UV:TEXCOORD0;};
struct Interp {
    float4 P:POSITION0;float4 C:COLOR0;float2 UV:TEXCOORD0;float Z:TEXCOORD1;
    float4 Clip:TEXCOORD2;float3 V:TEXCOORD3;float3 N:TEXCOORD4;
};
Interp VSMain(Vertex In)
{
    Interp O;float4 P=float4(In.P,1);
    float4 V=float4(dot(P,View[0]),dot(P,View[1]),-dot(P,View[2]),1);
    float3 N=In.C.rgb*2-1;
    O.N=float3(dot(N,View[0].xyz),dot(N,View[1].xyz),-dot(N,View[2].xyz));O.V=V.xyz;
    float4 C=float4(dot(V,Projection[0]),dot(V,Projection[1]),dot(V,Projection[2]),dot(V,Projection[3]));
    O.Clip=C.w*1.00001+float4(C.xy,-C.xy);
    C.xy=C.xy*Remap.xy+Remap.zw*C.w;
    C.z=C.z*(VertexDepth.w-VertexDepth.z)+C.w*VertexDepth.z;
    O.P=C;O.Z=V.z;O.C=In.C;O.UV=In.UV;return O;
}
float4 State:register(c0); // simulation time96, heat, inverse target W/H
float4 Unused:register(c1);
float4 Depth:register(c2); // near/far and scene partition
float4 Bounds:register(c3);
sampler2D SceneDepth:register(s0);
sampler2D SceneColor:register(s1);
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
    float U=In.UV.x,A=In.UV.y,T=State.x*(6.283185307/96),Seed=In.C.a*6.283185307;
    // Three overlapping scales of moving eddies; angular coordinates are seamless.
    float Noise=.55*sin(U*35+sin(A)*5-T*192+Seed)
               +.30*sin(U*69+cos(A)*7-T*288+Seed*2)
               +.15*sin(U*123+sin(A*3)*2-T*480+Seed*3);
    float2 Gradient=float2(ddx(Noise),ddy(Noise));
    float Facing=dot(normalize(In.N),-normalize(In.V));
    clip(In.Clip);clip(Facing-.001); // only the near shell, no double refraction
    float2 UV=(Pixel+.5)*State.zw;
    clip(float4(UV-Bounds.xy,Bounds.zw-UV));
    if(State.y<=0)return 0;
    float Mask=smoothstep(0,.09,U)*(1-smoothstep(.5,1,U))*smoothstep(0,.55,Facing);
    float Soft=DepthVisibility(UV,In.Z);
    float Coverage=.78*Mask*saturate(State.y)*Soft;
    if(Coverage<.001)return 0;
    float2 Edge=min(UV-Bounds.xy,Bounds.zw-UV)/State.zw;
    float Fade=smoothstep(0,4,min(Edge.x,Edge.y));
    Gradient*=rsqrt(max(dot(Gradient,Gradient),.000004));
    float Pixels=3.0*(Bounds.w-Bounds.y)/(1080*State.w);
    float2 Candidate=clamp(UV+Gradient*Noise*State.zw*Pixels*Mask*saturate(State.y)*Fade,Bounds.xy,Bounds.zw);
    float2 Step=State.zw;
    float Source=min(DepthVisibility(Candidate+Step,In.Z),DepthVisibility(Candidate-Step,In.Z));
    Source=min(Source,DepthVisibility(Candidate+float2(Step.x,-Step.y),In.Z));
    Source=min(Source,DepthVisibility(Candidate+float2(-Step.x,Step.y),In.Z));
    if(Source<.999)return 0; // never pull a nearer hull into the displaced sample
    return float4(tex2Dlod(SceneColor,float4(Candidate,0,0)).rgb*Coverage,Coverage);
}
