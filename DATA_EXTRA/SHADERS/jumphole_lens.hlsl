// World-space turbulent cloud. Box faces are only integration boundaries.
float4 ViewRow[3]:register(c0);
float4 ProjectionRow[4]:register(c3);
float4 Remap:register(c7);
float4 WorldRow[3]:register(c8);
float4 VertexDepth:register(c11);
float4 VertexState:register(c12);
struct Vertex { float3 Position:POSITION0; float4 Color:COLOR0; float2 UV:TEXCOORD0; };
struct Interp { float4 Position:POSITION0; float3 Local:TEXCOORD0; float4 Bounds:TEXCOORD1; float3 View:TEXCOORD2; float3 Normal:TEXCOORD3; };
Interp VSMain(Vertex In)
{
    Interp Out;float4 P=float4(In.Position,1);
    float4 W=float4(dot(P,WorldRow[0]),dot(P,WorldRow[1]),dot(P,WorldRow[2]),1);
    float4 V=float4(dot(W,ViewRow[0]),dot(W,ViewRow[1]),-dot(W,ViewRow[2]),1);
    float4 C=float4(dot(V,ProjectionRow[0]),dot(V,ProjectionRow[1]),dot(V,ProjectionRow[2]),dot(V,ProjectionRow[3]));
    Out.Bounds=C.w*1.00001+float4(C.xy,-C.xy);
    C.xy=C.xy*Remap.xy+Remap.zw*C.w;
    // Proxy exit faces may lie beyond a nebula's far plane while visible cloud is nearer.
    // Geometry depth is unused: preserve coverage and clamp integration against scene depth.
    C.z=C.w*.5;
    Out.Position=C;Out.Local=In.Position;Out.View=V.xyz;
    Out.Normal=sign(In.Color.rgb-.5)*step(.4,abs(In.Color.rgb-.5));
    return Out;
}
float4 State:register(c0); // seconds modulo96, opening, ripple, gain
float4 Target:register(c1); // inverse dimensions, refraction strength
float4 CameraBounds:register(c2);
float4 Depth:register(c3);
float4 Eye:register(c4);
float4 Phases:register(c5); // activation envelope/age01, entry strength/age01
float4 Palette:register(c7); // linear RGB multiplier, neutral=(1,1,1,0)
float4 IngressCamera:register(c6); // tan(horizontal half FOV), tan(vertical half FOV)
sampler2D SceneColor:register(s0);
sampler2D SceneDepth:register(s1);
sampler3D Noise:register(s2);
float SceneDistance(float2 UV)
{
    float D=tex2Dlod(SceneDepth,float4(UV,0,0)).r;
    if(D>=.99999994) return 1e8;
    if(D>Depth.w+.00000012) return 0;
    float Z=saturate((D-Depth.z)/max(Depth.w-Depth.z,.000001));
    return Depth.x*Depth.y/max(Depth.y-Z*(Depth.y-Depth.x),.001);
}
float2 Interval(Interp In,float2 UV,out float3 Ray,out float ViewCos)
{
    clip(In.Bounds);
    // Exit faces give unique coverage outside and inside the proxy.
    clip(-dot(In.Normal,Eye.xyz-In.Local));
    float3 Delta=In.Local-Eye.xyz;float Length=max(length(Delta),.001);
    Ray=Delta/Length;ViewCos=max(In.View.z/Length,.0001);
    float3 SafeRay=(step(0,Ray)*2-1)*max(abs(Ray),.00001);
    float3 A=(-float3(560,500,500)-Eye.xyz)/SafeRay;
    float3 B=(float3(560,500,500)-Eye.xyz)/SafeRay;
    float3 Near=min(A,B),Far=max(A,B);
    float Start=max(max(Near.x,Near.y),max(Near.z,0));
    float Finish=min(min(Far.x,Far.y),Far.z);
    float Scene=SceneDistance(UV);
    // Nearby hull/cockpit pixels remain untouched, including inside the cloud.
    if(Scene<200) Finish=Start;
    Finish=min(Finish,max(0,Scene-2)/ViewCos);
    return float2(Start,max(Start,Finish));
}
float4 Cloud(float3 P)
{
    float T=State.x/32; // triple speed; all drift frequencies still close at 96 seconds
    float3 Q=P/1100+T*float3(1,-1,1);
    float4 Broad=tex3Dlod(Noise,float4(Q,0));
    float4 WarpField=tex3Dlod(Noise,float4(Q*2+(Broad.bgr-.5)*.28,0));
    float3 Distorted=P+float3(Broad.g-.5,Broad.b-.5,Broad.r-.5)*220+(WarpField.gbr-.5)*85;
    Distorted.xy*=1+State.y*.16+Phases.z*.18;
    float4 Mid=tex3Dlod(Noise,float4(Distorted/500+T*float3(-2,1,2),0));
    float Fine=tex3Dlod(Noise,float4(Distorted/210+T*float3(3,2,-1),0)).a;
    float Detail=tex3Dlod(Noise,float4((Distorted+(Mid.gbr-.5)*32)/85+T*float3(-2,3,1),0)).r;
    float3 L0=(Distorted-float3(-120,65,-35))/float3(320,270,300);
    float3 L1=(Distorted-float3(175,-95,100))/float3(240,300,240);
    float3 L2=(Distorted-float3(45,210,-130))/float3(240,190,260);
    float Mass=exp2(-dot(L0,L0)*1.8)+exp2(-dot(L1,L1)*2.2)*.85+exp2(-dot(L2,L2)*2)*.6;
    float Boundary=1-smoothstep(.72,1,length(P/float3(550,490,490)));
    float Structure=smoothstep(.32,.63,Mid.r*.65+Broad.r*.35+(Fine-.5)*.13+(Detail-.5)*.10);
    float Density=saturate(Mass*.85-.08)*Structure*Boundary;
    // An irregular cleft breaks up the outer cloud as the channel activates.
    float Cleft=exp2(-pow((P.x+(Mid.g-.5)*170+P.y*.34)/65,2)-pow((P.y-25)/240,2));
    Density*=1-Cleft*State.y*.88;
    // Broad billows and diffuse internal illumination, not iso-surface filaments.
    float Fold=smoothstep(.25,.70,Mid.r*.50+Broad.g*.35+Detail*.15);
    float Spark=smoothstep(.34,.70,Mid.g*.50+Broad.b*.30+Fine*.12+Detail*.08);
    return float4(Density,Fold,Spark,Cleft);
}
// Two ragged mouths converge along the object's local Z axis into a deep narrow neck.
// Every sample is world anchored: orbiting the hole reveals the side of the channel.
// The scalar fields describe volumes, not an iris painted on the proxy surface.
float4 Vortex(float3 P,float4 CloudField)
{
    float Z=sqrt(P.z*P.z+25);
    float Along=saturate(Z/430);
    float2 Centre=float2(25*sin(P.z*.006),18*sin(P.z*.009+1.3));
    float2 Cross=P.xy-Centre;
    float Radius=length(Cross);
    float Angle=atan2(Cross.y,Cross.x+.0001);
    float Clock=State.x*(6.283185307/32);
    // Integer harmonics close both the angular seam and the 96-second clock wrap.
    // Increasing phase carries the spiral folds from each mouth towards the neck.
    float Swirl=sin(Angle+Z*.010+Clock*2);
    float Ragged=sin(Angle*2+P.z*.008)*25+(CloudField.y-.5)*80;
    float Channel=105+210*Along*Along+State.y*(10+Along*22)+(Ragged+Swirl*20)*Along;
    Channel*=1-Phases.z*.14;
    float SignedWall=Radius-Channel;
    float Axial=1-smoothstep(340,470,Z);
    float Width=58+CloudField.y*44;
    float Wall=exp2(-SignedWall*SignedWall/(Width*Width))*Axial;
    // The wide outer billows must not fill the inner passage with their Gaussian tail.
    Wall*=smoothstep(-62,-12,SignedWall);
    float Streams=.35+CloudField.y*.65;
    // Clear a continuous passage in the surrounding cloud. Its interior absorbs the
    // background most strongly at the far neck, while the sloping walls remain readable.
    float Hollow=(1-smoothstep(-24,52,SignedWall))*Axial;
    float Neck=exp2(-P.z*P.z/65000);
    float Core=(1-smoothstep(Channel*.38,Channel*.84,Radius))*Neck;
    return float4(Wall*(.35+Streams*.60),Streams,Hollow,Core);
}
float4 PSLens(Interp In,float2 Pixel:VPOS):COLOR0
{
    float2 UV=(Pixel+.5)*Target.xy;
    float3 Ray;float ViewCos;float2 Range=Interval(In,UV,Ray,ViewCos);
    float4 Base=tex2Dlod(SceneColor,float4(UV,0,0));
    if(Range.y<=Range.x || State.w<=0) return Base;
    // Refraction shares the optics entrance cap; the side/back cloud is light only.
    float3 MouthEye=Eye.xyz-float3(0,0,-240);
    float Front=smoothstep(.18,.60,-MouthEye.z/max(length(MouthEye),.001));
    float Hit=(-240-Eye.z)/max(Ray.z,.00001);
    if(Front<=0 || Ray.z<=0 || Hit<=0 || Hit<Range.x || Hit>Range.y) return Base;
    float3 P=Eye.xyz+Ray*Hit;
    float3 Liquid=tex3Dlod(Noise,float4(P/180+State.x/32*float3(1,-2,1),0)).rgb-.5;
    float Aperture=1-smoothstep(.72,1.06,length(P.xy)/145+Liquid.r*.10);
    if(Aperture<=0) return Base;
    float4 F=Cloud(P);
    float4 N=tex3Dlod(Noise,float4(P/600+State.x/32*float3(1,-1,2),0));
    float Edge=min(min(UV.x-CameraBounds.x,CameraBounds.z-UV.x),min(UV.y-CameraBounds.y,CameraBounds.w-UV.y));
    float2 Offset=(N.gb-.5)*Target.z*(.6+State.y*.5)*State.w*Front*Aperture*smoothstep(0,.025,Edge);
    Offset*=1+Phases.x*1.4+Phases.z*3.5;
    Offset*=float2(Target.x/max(Target.y,.000001),1);
    float2 Candidate=clamp(UV+Offset,CameraBounds.xy,CameraBounds.zw);
    float ProtectedFront=max(200,Hit*ViewCos+2);
    float Source=min(SceneDistance(Candidate+Target.xy),SceneDistance(Candidate-Target.xy));
    Source=min(Source,SceneDistance(Candidate+float2(Target.x,-Target.y)));
    Source=min(Source,SceneDistance(Candidate+float2(-Target.x,Target.y)));
    if(Source<ProtectedFront) return Base;
    float4 Result=tex2Dlod(SceneColor,float4(Candidate,0,0));
    Result.rgb*=1-F.w*State.y*.20*State.w*Front*Aperture;
    return lerp(Base,Result,Front*Aperture);
}
float4 IntegrateCloud(float3 Ray,float2 Range,uniform bool Ingress)
{
    if(Range.y<=Range.x || State.w<=0) return 0;
    float Step=(Range.y-Range.x)/64;
    float3 Light=0;float Transmission=1;
    [loop] for(int I=0;I<64;++I)
    {
        float3 P=Eye.xyz+Ray*(Range.x+(I+.5)*Step);
        float4 F=Cloud(P);
        float4 Funnel=Vortex(P,F);
        // A broad irregular pressure front lives in the volume, never on a screen quad.
        float WaveDistance=length(P*float3(1,.88,.94))+(F.y-.5)*140;
        float WaveDelta=(WaveDistance-(35+Phases.y*600))/95;
        // The separate activation wave has already passed when the player enters.
        float Activation=Ingress ? 0 : exp2(-WaveDelta*WaveDelta)*Phases.x;
        // Entry travels through the actual local-Z passage, exposing a bright smoky wake.
        float JetZ=(P.z-(-450+Phases.w*1000))/165;
        float JetRadius=length(P.xy+float2(F.y-.5,F.z-.5)*95);
        float Jet=exp2(-JetZ*JetZ)*(1-smoothstep(70,230,JetRadius))*Phases.z;
        float CloudDensity=F.x*(1-Funnel.z*.98)*.70;
        float WallDensity=Funnel.x*(.80+State.y*.20);
        CloudDensity*=1+Activation*.9;
        WallDensity*=1+Activation*.65;
        float DarkDensity=Funnel.w*(.42+State.y*.35)*(1-Jet*.72);
        float JetDensity=Jet*(.18+F.z*.38);
        float Density=CloudDensity+WallDensity+DarkDensity+JetDensity;
        float Alpha=1-exp2(-Density*Step*.010);
        // Two light-side density probes approximate attenuation within a billow. The
        // soft fill is retained in shadow, while small folds catch ice-blue scattered light.
        float3 LightQ=P/500+State.x/32*float3(-2,1,2);
        float NearLight=tex3Dlod(Noise,float4(LightQ+float3(-.06,.09,-.07),0)).r;
        float FarLight=tex3Dlod(Noise,float4(LightQ+float3(-.16,.24,-.18),0)).r;
        float Shadow=exp2(-max(0,NearLight-F.y)*3.5-max(0,FarLight-F.y)*2.0);
        float Scattering=.30+Shadow*.90;
        float3 Colour=lerp(float3(.015,.040,.065),float3(.12,.28,.40),F.y);
        Colour+=F.z*float3(.08,.24,.34)*(.35+State.y*.35);
        Colour*=Scattering;
        Colour+=Activation*(.3+F.z)*float3(.35,.58,.75);
        // The cloud's sloping wall is brightly lit at its ragged mouth and falls into
        // blue shadow down the neck. Emission fills billows rather than tracing lines.
        float MouthLight=.35+.80*smoothstep(50,340,abs(P.z));
        float3 WallColour=lerp(float3(.055,.20,.31),float3(.55,.78,.96),Funnel.y);
        WallColour+=F.z*float3(.38,.45,.50)*(.55+State.y*.35);
        WallColour*=MouthLight*(1+State.y*.20);
        WallColour*=Scattering;
        WallColour+=State.z*F.y*float3(.23,.32,.40);
        WallColour+=Activation*(.7+F.z)*float3(.90,1.15,1.35);
        WallColour+=Jet*F.z*float3(.40,.75,1.0);
        // Pale ice-blue highlights retain detail instead of clipping into flat cyan fire.
        float Peak=max(WallColour.r,max(WallColour.g,WallColour.b));
        WallColour=lerp(WallColour,Peak*float3(.84,.94,1),smoothstep(.65,1.4,Peak)*.35);
        WallColour/=max(1,Peak/(1.30+Activation*1.7+Jet*.7));
        float3 DarkColour=float3(.002,.009,.018);
        float3 JetColour=lerp(float3(.10,.32,.56),float3(.85,1.12,1.35),F.z)*(1.6+Shadow*.70);
        Colour=(Colour*CloudDensity+WallColour*WallDensity+DarkColour*DarkDensity+JetColour*JetDensity)/max(Density,.0001);
        Light+=Transmission*Alpha*Colour;
        Transmission*=1-Alpha;
    }
    return float4(Light*(State.w*Palette.rgb),(1-Transmission)*State.w);
}
float4 PSGlow(Interp In,float2 Pixel:VPOS):COLOR0
{
    float2 UV=(Pixel+.5)*Target.xy;
    float3 Ray;float ViewCos;float2 Range=Interval(In,UV,Ray,ViewCos);
    return IntegrateCloud(Ray,Range,false);
}

// A brief transition through the actual volumetric passage, composited over the already
// running hyperspace tunnel. It uses the same smoke field and lighting as the world anomaly.
Interp VSIngress(Vertex In)
{
    Interp Out;
    Out.Position=float4(In.Position.xy*Remap.xy+Remap.zw,0,1);
    Out.Bounds=1.00001+float4(In.Position.xy,-In.Position.xy);
    Out.Local=0;Out.View=0;Out.Normal=0;
    return Out;
}
float IngressProtected(float2 UV,float NearThreshold)
{
    float D=tex2Dlod(SceneDepth,float4(UV,0,0)).r;
    // Only a near-depth predicate is needed for this virtual interior. Avoid four
    // full perspective reconstructions while retaining cockpit-partition protection.
    return (D<NearThreshold || (D>Depth.w+.00000012 && D<.99999994)) ? 1 : 0;
}
float4 PSIngress(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Bounds);
    float2 UV=(Pixel+.5)*Target.xy;
    float4 Base=tex2Dlod(SceneColor,float4(UV,0,0));
    float NearThreshold=Depth.z+(Depth.w-Depth.z)*(Depth.y-Depth.x*Depth.y/200)/max(Depth.y-Depth.x,.001);
    if(Phases.z<=0 || State.w<=0 || IngressProtected(UV,NearThreshold)>0) return Base;
    // Runtime rejects empty viewport dimensions before drawing this program.
    float2 Screen=(UV-CameraBounds.xy)/(CameraBounds.zw-CameraBounds.xy)*2-1;
    float3 Ray=normalize(float3(Screen.x*IngressCamera.x,-Screen.y*IngressCamera.y,1));
    // Ingress eye is on the channel axis, z=-360..400, and rays always face +Z.
    float3 Exit=float3(560,500,500-Eye.z)/max(abs(Ray),.00001);
    float2 Range=float2(0,max(0,min(min(Exit.x,Exit.y),Exit.z)));
    float4 Volume=IntegrateCloud(Ray,Range,true);
    float3 Sample=Eye.xyz+Ray*lerp(Range.x,Range.y,.45);
    float4 N=tex3Dlod(Noise,float4(Sample/480+State.x/32*float3(1,-1,2),0));
    float Edge=min(min(UV.x-CameraBounds.x,CameraBounds.z-UV.x),min(UV.y-CameraBounds.y,CameraBounds.w-UV.y));
    float2 Offset=(N.gb-.5)*Target.z*Phases.z*3.5*State.w*smoothstep(0,.035,Edge);
    Offset*=float2(Target.x/max(Target.y,.000001),1);
    float2 Candidate=clamp(UV+Offset,CameraBounds.xy,CameraBounds.zw);
    float Protected=IngressProtected(Candidate+Target.xy,NearThreshold)+IngressProtected(Candidate-Target.xy,NearThreshold);
    Protected+=IngressProtected(Candidate+float2(Target.x,-Target.y),NearThreshold);
    Protected+=IngressProtected(Candidate+float2(-Target.x,Target.y),NearThreshold);
    if(Protected>0) return Base;
    float4 Refracted=tex2Dlod(SceneColor,float4(Candidate,0,0));
    float Envelope=saturate(Phases.z);
    float3 Composite=Volume.rgb+Refracted.rgb*(1-saturate(Volume.a));
    return float4(lerp(Base.rgb,Composite,Envelope),Base.a);
}
