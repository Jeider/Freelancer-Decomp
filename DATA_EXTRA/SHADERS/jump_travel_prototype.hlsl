// Independent hyperspace prototype. No retail tunnel geometry, textures or UVs.
// Three analytic depth layers, six noise reads; no raymarch or screen feedback.
float4 Remap : register(c7);
struct Vertex { float3 P:POSITION0; float4 C:COLOR0; float2 UV:TEXCOORD0; };
struct Interp { float4 P:POSITION0; float2 UV:TEXCOORD0; };
Interp VSMain(Vertex V) { Interp O; O.P=float4(V.P.xy*Remap.xy+Remap.zw,0,1); O.UV=V.UV; return O; }
float4 Journey : register(c0); // continuous seconds, viewport aspect, 0 charge/1 flight/2 exit, phase progress
float4 Screen : register(c1); // target inverse size, camera near/far
float4 Depth : register(c2); // viewport depth range, protect scene geometry, reserved
sampler3D Noise : register(s0);
sampler2D SceneDepth : register(s1);
static const float PI=3.14159265359;
float Hash(float2 P) { return frac(sin(dot(P,float2(127.1,311.7)))*43758.5453); }
float Stars(float2 P,float Scale) {
    float2 G=P*Scale, Cell=floor(G), F=frac(G)-0.5;
    float H=Hash(Cell);float2 Offset=float2(Hash(Cell+17),Hash(Cell+31))-.5;
    float2 D=F-Offset*.65;
    return step(.976,H)*exp2(-dot(D,D)*900)*(.25+Hash(Cell+9));
}
float3 Space(float2 P) {
    float Band=exp2(-pow((P.y+P.x*.25-.12)*4,2));
    float3 C=float3(.002,.004,.009)+Band*float3(.008,.013,.024);
    return C+(Stars(P,55)+Stars(P,91)*.4)*float3(.65,.79,1);
}
// Each sector has one moving needle, with continuous birth/death outside view.
float Needles(float2 P,float Time,float Speed,float Count) {
    float A=atan2(P.y,P.x), R=length(P);
    float Sector=floor((A+PI)*(Count/(2*PI)));
    float H=Hash(float2(Sector,Count));
    float Theta=(Sector+.2+.6*H)*(2*PI/Count)-PI;
    float2 Dir=float2(cos(Theta),sin(Theta));
    float Along=dot(P,Dir), Across=abs(P.x*Dir.y-P.y*Dir.x);
    float Life=frac(Time*Speed*.26+H);
    float Head=.025+Life*Life*2.7;
    float Tail=max(.02,Head-(.015+Head*.21)*Speed);
    float Width=max(.0006+Head*.0012,min(fwidth(Across)*.7,.002));
    float Core=exp2(-Across*Across/(Width*Width));
    float Segment=smoothstep(Tail,Tail+.025,Along)*(1-smoothstep(Head,Head+.012,Along));
    return Core*Segment*smoothstep(0,.12,Life)*(1-smoothstep(.88,1,Life))*smoothstep(.06,.18,R);
}
float3 Hyperspace(float2 P,float Time) {
    float R=length(P);
    // Large-scale bends move slowly while longitudinal structures flow rapidly.
    float2 Bend=float2(sin(Time*.19),cos(Time*.16))*.022;
    P-=Bend*smoothstep(.05,.8,R);
    float3 Ray=normalize(float3(P,1));
    float Radial=max(length(Ray.xy),.025);
    float3 C=float3(.0015,.003,.009);
    [unroll] for(int I=0;I<3;++I) {
        float Layer=float(I);
        float Distance=(1.4+Layer*1.6)/Radial;
        float3 Q=Ray*Distance*float3(.30,.30,.13);
        Q.z-=Time*(.55+Layer*.21);
        float4 N=tex3Dlod(Noise,float4(Q*.42,0));
        float4 F=tex3Dlod(Noise,float4(Q*float3(.85,.85,.35)+(N.gbg-.5)*.8,0));
        float Angle=atan2(P.y,P.x);
        float Fold=sin(Angle*(3+I)+N.r*7+Q.z*.36+Layer*1.7);
        float Ridge=pow(saturate(1-abs(Fold)*(.65+F.r)),3);
        float Lace=pow(saturate(1-abs(F.r-.51)*14),3);
        float FarFade=smoothstep(.035,.20,R)*(1-smoothstep(55,110,Distance));
        float Glow=Ridge*(.12+Lace*.85)*(0.35+N.a)*FarFade;
        float3 Tint=lerp(float3(.035,.12,.24),float3(.40,.72,.92),Lace);
        Tint=lerp(Tint,float3(.20,.10,.39),saturate(N.b-.55)*.6);
        C+=Tint*Glow*(1.1-Layer*.24)*3.6;
    }
    // Broad atmospheric light has no uniform bright rim or opaque end cap.
    float Halo=exp2(-R*R/.07)-exp2(-R*R/.006);
    C+=float3(.018,.075,.13)*Halo;
    float Streak=Needles(P,Time,1.6,127)+Needles(P,Time+.7,1.1,73)*.45;
    C+=Streak*float3(.38,.70,.95)*.85;
    float Focal=exp2(-dot(P,P)/.00008)*.16;
    C+=float3(.65,.85,1)*Focal;
    return C/(1+C*.4);
}
float Protection(float2 Pixel) {
    if(Depth.z<.5)return 1;
    float D=tex2Dlod(SceneDepth,float4((Pixel+.5)*Screen.xy,0,0)).r;
    if(D>=.99999994)return 1;
    if(D>Depth.y+.00000012||D<Depth.x)return 0;
    float Z=saturate((D-Depth.x)/max(Depth.y-Depth.x,.000001));
    float Distance=Screen.z*Screen.w/max(Screen.w-Z*(Screen.w-Screen.z),.001);
    return smoothstep(150,500,Distance);
}
float4 Transition(float2 P) {
    float T=saturate(Journey.w), R=length(P);
    float3 C=Hyperspace(P,Journey.x);
    if(Journey.z<.5) {
        float Open=smoothstep(.55,1,T);
        float Radius=Open*2.4;
        float Mask=(1-smoothstep(Radius-.10,Radius+.10,R))*Open;
        float Charge=pow(T,4)*(1-Open);
        float Slit=exp2(-P.x*P.x/.00015-P.y*P.y/(.0004+.03*T*T));
        float Edge=exp2(-pow((R-Radius)/(.015+.04*Open),2))*sin(Open*PI);
        C=C*Mask+float3(.45,.72,1)*(Slit*Charge*1.6+Edge*.65);
        C+=Needles(P,Journey.x,pow(T,3)*1.4+.03,151)*T*float3(.25,.48,.75)*(1-Open);
        float Alpha=saturate(Mask+T*.16*(1-Mask));
        return float4(C,Alpha);
    }
    // The centre opens into the destination; the wake peels off at the periphery.
    float Radius=pow(T,.85)*2.5;
    float Mask=smoothstep(Radius-.12,Radius+.10,R)*(1-smoothstep(.72,1,T));
    float Edge=exp2(-pow((R-Radius)/.045,2))*sin(T*PI);
    return float4(C*Mask+Edge*float3(.22,.48,.70)*.55,Mask);
}
float4 PSMain(Interp In):COLOR0 {
    float2 P=(In.UV-.5)*float2(Journey.y,1);
    return float4(Hyperspace(P,Journey.x),1);
}
float4 PSTransition(Interp In,float2 Pixel:VPOS):COLOR0 {
    float2 P=(In.UV-.5)*float2(Journey.y,1);
    return Transition(P)*Protection(Pixel);
}
// Preview background only; not used by the game renderer.
float4 PSSpace(Interp In):COLOR0 {
    return float4(Space((In.UV-.5)*float2(Journey.y,1)),1);
}
