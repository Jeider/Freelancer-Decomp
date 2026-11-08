float4 View[3]:register(c0);
float4 Projection[4]:register(c3);
float4 Remap:register(c7);
float4 VertexDepth:register(c8);
float4 Model[3]:register(c9); // part -> ship-relative world coordinates
float4 Centre:register(c12); // ship centre in view coordinates, bounding radius
float4 Motion:register(c13); // time (96s periodic), cloak fraction, strength, per-ship phase
struct Vertex {float3 P:POSITION0;float3 N:NORMAL0;};
struct Interp {float4 P:POSITION0;float3 V:TEXCOORD0;float3 N:TEXCOORD1;float3 Q:TEXCOORD2;float4 Clip:TEXCOORD3;};
Interp VSMain(Vertex In)
{
    Interp O;float4 P=float4(In.P,1);
    float3 Q=float3(dot(P,Model[0]),dot(P,Model[1]),dot(P,Model[2]));
    float3 Domain=Q/max(Centre.w,1);
    float T=frac(Motion.x/96)*6.283185307,C=saturate(Motion.y);
    float Pulse=4*C*(1-C);
    // Independent travelling waves shear the silhouette in all three directions.
    float3 Wave=sin(Domain.yzx*float3(9,11,8)+Domain.zxy*3+T*float3(48,-64,80)+Motion.w);
    Q+=Wave*Centre.w*(.004+.018*Pulse)*C*Motion.z;
    float3 V=float3(dot(Q,View[0].xyz),dot(Q,View[1].xyz),-dot(Q,View[2].xyz))+Centre.xyz;
    float3 N=float3(dot(In.N,Model[0].xyz),dot(In.N,Model[1].xyz),dot(In.N,Model[2].xyz));
    O.N=float3(dot(N,View[0].xyz),dot(N,View[1].xyz),-dot(N,View[2].xyz));
    float4 VP=float4(V,1);
    float4 H=float4(dot(VP,Projection[0]),dot(VP,Projection[1]),dot(VP,Projection[2]),dot(VP,Projection[3]));
    O.Clip=H.w*1.00001+float4(H.xy,-H.xy);
    H.xy=H.xy*Remap.xy+Remap.zw*H.w;
    H.z=H.z*(VertexDepth.w-VertexDepth.z)+H.w*VertexDepth.z;
    O.P=H;O.V=V;O.Q=Domain;return O;
}
float4 State:register(c0); // time, cloak, inverse target width/height
float4 Optics:register(c1); // strength, visibility, radius, phase
float4 Depth:register(c2); // near, far, scene depth partition
float4 Bounds:register(c3);
sampler2D SceneDepth:register(s0);
sampler2D SceneColor:register(s1);
float Visible(float2 UV,float Z)
{
    float D=tex2Dlod(SceneDepth,float4(clamp(UV,Bounds.xy,Bounds.zw),0,0)).r;
    if(D>Depth.w+.00000012&&D<.99999994)return 0;
    float Unit=saturate((D-Depth.z)/max(Depth.w-Depth.z,.000001));
    float Scene=D>=.99999994?1e8:Depth.x*Depth.y/max(Depth.y-Unit*(Depth.y-Depth.x),.001);
    // A small bias permits the partially visible hull during the native fade.
    float Bias=max(.15,Optics.z*.025);
    return saturate((Scene-Z+Bias)/max(.15,Bias*.5));
}
float4 PSMain(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Clip);
    float Facing=dot(normalize(In.N),-normalize(In.V));
    clip(Facing-.001);
    float2 UV=(Pixel+.5)*State.zw;
    clip(float4(UV-Bounds.xy,Bounds.zw-UV));
    float C=saturate(State.y),Pulse=4*C*(1-C),T=frac(State.x/96)*6.283185307;
    float2 Flow=float2(sin(In.Q.y*16+In.Q.z*7+T*64+Optics.w),
                      cos(In.Q.x*13-In.Q.z*9-T*48+Optics.w));
    Flow+=.35*float2(cos(In.Q.z*31+T*112),sin(In.Q.y*27-T*96));
    float Edge=smoothstep(0,.16,Facing);
    float Coverage=C*(.38+.5*Pulse)*Edge*Optics.y*Visible(UV,In.V.z);
    if(Coverage<.001||Optics.x<=0)return 0;
    float2 Border=min(UV-Bounds.xy,Bounds.zw-UV)/State.zw;
    float Pixels=(5+9*Pulse)*Optics.x*(Bounds.w-Bounds.y)/(1080*State.w);
    float2 Offset=(Flow+In.N.xy*.3)*State.zw*Pixels*C*smoothstep(0,5,min(Border.x,Border.y));
    float2 Candidate=clamp(UV+Offset,Bounds.xy,Bounds.zw);
    // Check the full linear-sampling footprint: do not drag nearer ships across the silhouette.
    float Source=min(Visible(Candidate+State.zw,In.V.z),Visible(Candidate-State.zw,In.V.z));
    Source=min(Source,Visible(Candidate+float2(State.z,-State.w),In.V.z));
    Source=min(Source,Visible(Candidate+float2(-State.z,State.w),In.V.z));
    if(Source<.999)return 0;
    return float4(tex2Dlod(SceneColor,float4(Candidate,0,0)).rgb*Coverage,Coverage);
}
