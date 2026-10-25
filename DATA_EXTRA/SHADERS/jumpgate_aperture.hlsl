// Jumpgate: concentric plasma rings or alternate travelling energy toroids, plus exit cap.
// Object-space metres, -Z approach. HpFX2=-490, HpFX4=-101, HpFX7=300.
// A depth-clipped lens followed by premultiplied volume light; no ALE or billboards.
float4 Remap:register(c7);
struct Vertex { float3 Position:POSITION0; float4 Color:COLOR0; float2 UV:TEXCOORD0; };
struct Interp { float4 Position:POSITION0; float4 Clip:TEXCOORD0; };
Interp VSMain(Vertex In)
{
    Interp Out;
    Out.Position=float4(In.Position.xy*Remap.xy+Remap.zw,0,1);
    Out.Clip=1.00001+float4(In.Position.xy,-In.Position.xy);
    return Out;
}
float4 State:register(c0); // simulation time, activation age, gain, optics enable
float4 Target:register(c1); // reciprocal target size, refraction strength
float4 Bounds:register(c2); // viewport pixel centres
float4 Depth:register(c3); // near, far, partition min/max
float4 Eye:register(c4); // object-local camera
float4 Camera:register(c5); // inverse projection scale xy, projection centre zw
float4 LocalRow[3]:register(c6); // +Z view ray -> object local
float4 Portal:register(c9); // authored jump-out HP xyz, circular aperture radius
float4 PortalRow[3]:register(c10); // solar-local -> hardpoint-local rotation
float4 Plasma:register(c13); // jg_bubble hardpoint position + emitter (0,0,8), gain
float4 Rings:register(c14); // original mean radii 130/190, signed angular speeds
float4 TunnelTint:register(c15); // shared upcoming tunnel palette RGB, recolour enable
sampler2D Scene:register(s0);
sampler2D SceneDepth:register(s1);
sampler3D Noise:register(s2);
static const float Pi=3.14159265359;
float SceneZ(float2 UV)
{
    float D=tex2Dlod(SceneDepth,float4(UV,0,0)).r;
    if(D>=.99999994) return 1e8;
    if(D>Depth.w+.00000012) return 0;
    float Z=saturate((D-Depth.z)/max(Depth.w-Depth.z,.000001));
    return Depth.x*Depth.y/max(Depth.y-Z*(Depth.y-Depth.x),.001);
}
float Footprint(float2 UV)
{
    return min(min(SceneZ(UV+Target.xy),SceneZ(UV-Target.xy)),
        min(SceneZ(UV+float2(Target.x,-Target.y)),SceneZ(UV+float2(-Target.x,Target.y))));
}
float3 Flow(float3 P)
{
    float3 Drift=float3(State.x/48,-State.x/64,-State.x/32);
    float3 A=tex3Dlod(Noise,float4(P/160+Drift,0)).rgb;
    float3 B=tex3Dlod(Noise,float4(P/51-Drift*2,0)).gbr;
    return (A*.72+B*.28)-.5;
}
float2 Box(float3 O,float3 R)
{
    float3 Safe=lerp(-1,1,step(0,R))*max(abs(R),.00001);
    float3 A=(float3(-245,-245,-505)-O)/Safe;
    float3 B=(float3(245,245,345)-O)/Safe;
    float3 Near=min(A,B),Far=max(A,B);
    return float2(max(0,max(Near.x,max(Near.y,Near.z))),min(Far.x,min(Far.y,Far.z)));
}
float3 LocalToView(float3 N)
{
    return N.x*LocalRow[0].xyz+N.y*LocalRow[1].xyz+N.z*LocalRow[2].xyz;
}
float3 ToPortal(float3 P)
{
    return float3(dot(P,PortalRow[0].xyz),dot(P,PortalRow[1].xyz),dot(P,PortalRow[2].xyz));
}
float4 PSLens(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Clip);
    float2 UV=(Pixel+.5)*Target.xy;
    float4 Base=tex2Dlod(Scene,float4(UV,0,0));
    if(State.z<=0) return Base;
    float2 Screen=(UV-Bounds.xy)/max(Bounds.zw-Bounds.xy,.000001)*2-1;
    float3 ViewRay=normalize(float3((Screen.x-Camera.z)*Camera.x,(-Screen.y-Camera.w)*Camera.y,1));
    float3 Ray=float3(dot(ViewRay,LocalRow[0].xyz),dot(ViewRay,LocalRow[1].xyz),dot(ViewRay,LocalRow[2].xyz));
    float2 Span=Box(Eye.xyz,Ray);
    float Z=SceneZ(UV);
    Span.x=max(Span.x,Depth.x/max(ViewRay.z,.0001));
    Span.y=min(Span.y,min(Depth.y,max(0,Z-1.5))/max(ViewRay.z,.0001));
    if(Span.y<=Span.x) return Base;
    float Ready=smoothstep(2.8,5.2,State.y);
    float Charge=smoothstep(0,.7,State.y);
    float3 Result=Base.rgb;

    // Exact authored HP plane. Curvature is optical only, like the jumphole core:
    // camera orbit changes the reflection, never the position or circular aperture.
    float3 PortalRay=ToPortal(Ray);
    float3 PortalEye=ToPortal(Eye.xyz-Portal.xyz);
    float Denom=abs(PortalRay.z)>.0001 ? PortalRay.z : (PortalRay.z<0?-.0001:.0001);
    float Hit=-PortalEye.z/Denom;
    float3 P=Eye.xyz+Ray*Hit;
    float2 Cap=ToPortal(P-Portal.xyz).xy/max(1,Portal.w);
    float R=length(Cap);
    float Face=smoothstep(.02,.16,abs(PortalRay.z));
    if(Ready>0 && State.w>0 && R<1.10 && Hit>Span.x && Hit<Span.y && Face>0) {
        float3 Liquid=Flow(P)*.7;
        float3 Normal=normalize(float3(Cap*.78,-sqrt(max(.12,1-dot(Cap,Cap)*.60))));
        Normal=normalize(Normal+Liquid*.22);
        float3 SolarNormal=Normal.x*PortalRow[0].xyz+Normal.y*PortalRow[1].xyz+Normal.z*PortalRow[2].xyz;
        float3 NV=LocalToView(SolarNormal);
        float3 Reflected=reflect(ViewRay,NV);
        float2 Mirror=Reflected.xy/(1+abs(Reflected.z));
        float2 Centre=(Bounds.xy+Bounds.zw)*.5;
        float2 Candidate=Centre+float2(Mirror.x,-Mirror.y)*(Bounds.zw-Bounds.xy)*.46;
        Candidate+=Liquid.gb*Target.z;
        Candidate=clamp(Candidate,Bounds.xy+Target.xy,Bounds.zw-Target.xy);
        float Aperture=1-smoothstep(.965,1.025,R);
        float Edge=smoothstep(0,.025,min(min(UV.x-Bounds.x,Bounds.z-UV.x),min(UV.y-Bounds.y,Bounds.w-UV.y)));
        float Mask=Aperture*Ready*State.z*Face*Edge;
        float Facing=saturate(abs(dot(Normal,PortalRay)));
        float Fresnel=pow(1-Facing,3);
        float3 Reflection=Base.rgb;
        // The same folded screen-environment reflection as the jumphole core.
        // Do not sample the player's foreground silhouette or nearer gate doors.
        if(Footprint(Candidate)>max(200,Hit*ViewRay.z)+2)
            Reflection=tex2Dlod(Scene,float4(Candidate,0,0)).rgb;
        Reflection+=float3(.035,.055,.085)*(1+Fresnel*2);
        Result=lerp(Result,Reflection,Mask);

        // A dense pearl lip with a gold outer corona and moving broken filaments.
        float Ripple=Liquid.r*.025+sin(R*43-State.x*2.4+Liquid.g*5)*.004;
        float D=R-1+Ripple;
        float Core=exp(-D*D/0.00022);
        float Inner=exp(-(D+.035)*(D+.035)/.0015);
        float Corona=exp(-D*D/.006)*(1-smoothstep(1.05,1.10,R));
        float2 A=Cap/max(R,.001);
        float Arc=.65+.35*sin(A.x*9+A.y*6+State.x*2+Liquid.b*9);
        float3 Rim=float3(1,.89,.68)*Core*2.6+
            float3(.38,.62,1)*Inner*.42+float3(1,.48,.10)*Corona*.5;
        Result+=Rim*Arc*Ready*State.z*Face;
    }
    return float4(Result,Base.a);
}
// Fixed toroidal volume, with material coordinates advected around its axis.
// Opposite signed phases move every noise scale and hot knot together, so rotation
// reads as circulating plasma instead of unrelated flickering.
float2 PlasmaRing(float3 P,float Radius,float Phase,float Seed)
{
    if(Radius<=0) return 0;
    float C=cos(Phase),S=sin(Phase);
    float2 Q=float2(C*P.x+S*P.y,-S*P.x+C*P.y)/Radius;
    float3 Coord=float3(Q*1.6,P.z/90)+Seed;
    float3 N=tex3Dlod(Noise,float4(Coord,0)).rgb;
    float Fine=tex3Dlod(Noise,float4(Coord*3.7+float3(3,1,5),0)).r;
    float R=length(P.xy)-Radius;
    // Twice the cross-section, preserving the two authored centreline radii.
    float Twist=(N.g-.5)*16;
    float Core=exp(-(R-Twist)*(R-Twist)/340-P.z*P.z/256);
    float Halo=exp(-R*R/1240-P.z*P.z/720);
    float2 A=Q/max(length(Q),.001);
    float Harmonic=A.x*(4*A.x*A.x-3); // cos(3 theta), rotating in material space
    float Knot=pow(saturate(.5+.5*Harmonic),5);
    float Filament=pow(saturate(1-abs(N.r-.5+(.5-Fine)*.32)*5),8);
    float Body=Core*(.28+N.b*.55+Filament*.7+Knot*.48);
    return float2(Body,Halo*(.08+Fine*.13));
}
float4 PSMain(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Clip);
    if(State.z<=0 || Plasma.w<=0) return 0;
    float2 UV=(Pixel+.5)*Target.xy;
    float2 Screen=(UV-Bounds.xy)/max(Bounds.zw-Bounds.xy,.000001)*2-1;
    float3 ViewRay=normalize(float3((Screen.x-Camera.z)*Camera.x,(-Screen.y-Camera.w)*Camera.y,1));
    float3 Ray=float3(dot(ViewRay,LocalRow[0].xyz),dot(ViewRay,LocalRow[1].xyz),dot(ViewRay,LocalRow[2].xyz));
    // Clip a shallow volume at the original two shell emitters, not a camera plane.
    float3 Origin=Eye.xyz-Plasma.xyz;
    float3 Safe=lerp(-1,1,step(0,Ray))*max(abs(Ray),.00001);
    float3 A=(float3(-280,-280,-80)-Origin)/Safe;
    float3 B=(float3(280,280,80)-Origin)/Safe;
    float3 Near=min(A,B),Far=max(A,B);
    float2 Span=float2(max(0,max(Near.x,max(Near.y,Near.z))),min(Far.x,min(Far.y,Far.z)));
    float Z=SceneZ(UV);
    Span.x=max(Span.x,Depth.x/max(ViewRay.z,.0001));
    Span.y=min(Span.y,min(Depth.y,max(0,Z-1.5))/max(ViewRay.z,.0001));
    if(Span.y<=Span.x) return 0;
    float Gain=smoothstep(.05,1.1,State.y)*State.z*Plasma.w;
    float Step=(Span.y-Span.x)/64;
    float3 Light=0;
    float Transmission=1;
    [loop] for(int I=0;I<64;++I) {
        float3 P=Origin+Ray*(Span.x+(I+.5)*Step);
        float2 Inner=PlasmaRing(P,Rings.x,State.x*Rings.z,0);
        float2 Outer=PlasmaRing(P,Rings.y,State.x*Rings.w,7);
        float Body=Inner.x+Outer.x;
        float Halo=Inner.y+Outer.y;
        float3 Emission=float3(1,.63,.18)*(Body*.65+Halo)+
            float3(.86,.93,1)*Body*Body*.8;
        // Half the volume density compensates the doubled depth; emission is 2x.
        Emission*=2;
        float Alpha=1-exp(-Body*Gain*Step*.003);
        Light+=Transmission*Emission*Gain*Step*.0275;
        Transmission*=1-Alpha;
    }
    return float4(Light,1-Transmission);
}

// Thin world-space trails follow the authored HpFX2 inflow toward the exit HP.
// Only ribbon width faces the eye; trajectory and travel speed are object-local.
float4 InflowRemap:register(c16);
struct InflowInterp {
    float4 Position:POSITION0;
    float2 UV:TEXCOORD0;
    float ViewZ:TEXCOORD1;
    float Fade:TEXCOORD2;
    float2 Material:TEXCOORD3;
};
InflowInterp VSInflow(Vertex In)
{
    InflowInterp Out;
    float3 V=LocalToView(In.Position-Eye.xyz);
    float2 XY=V.xy/Camera.xy+Camera.zw*V.z;
    Out.Position=float4(XY*InflowRemap.xy+InflowRemap.zw*V.z,
        Depth.y/(Depth.y-Depth.x)*(V.z-Depth.x),V.z);
    Out.UV=In.UV; Out.ViewZ=V.z; Out.Fade=In.Color.a; Out.Material=In.Color.rg;
    return Out;
}
float4 PSInflow(InflowInterp In,float2 Pixel:VPOS):COLOR0
{
    float2 UV=(Pixel+.5)*Target.xy;
    clip(float4(UV-Bounds.xy,Bounds.zw-UV));
    clip(SceneZ(UV)-In.ViewZ-1.5);
    float Cross=pow(saturate(1-abs(In.UV.x)),2);
    float Tail=sin(saturate(In.UV.y)*Pi);
    float Gain=smoothstep(.1,1.8,State.y)*State.z*In.Fade;
    float3 N=tex3Dlod(Noise,float4(In.UV.y*3,In.UV.x*.65,In.Material.y*11-State.x/3,0)).rgb;
    float Density=lerp(smoothstep(.25,.7,N.r),.7+.3*N.g,In.Material.x);
    float L=Cross*Tail*Gain*Density;
    float3 Mist=lerp(float3(.12,.28,.65),float3(.55,.78,1),Cross*N.b);
    float3 Spark=lerp(float3(.35,.60,1),float3(1,.92,.72),Cross);
    float3 Colour=lerp(Mist*.85,Spark*1.6,In.Material.x);
    // The tunnel recolours luminance with this same palette, preserving its hue
    // instead of multiplying the old blue mist into a dark green/red result.
    float3 Palette=.16+saturate(TunnelTint.rgb)*1.25;
    Palette/=max(dot(Palette,float3(.2126,.7152,.0722)),.001);
    Colour=lerp(Colour,dot(Colour,float3(.2126,.7152,.0722))*Palette,TunnelTint.w);
    return float4(Colour*L,0);
}

float4 DonutSource:register(c16); // authored shooter + child offset; enable
float4 DonutPulse[5]:register(c17); // solar-local centre Z, age, seed, birth/death gain
float4 PSDonuts(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Clip);
    if(State.z<=0 || DonutSource.w<=0) return 0;
    float2 UV=(Pixel+.5)*Target.xy;
    float2 Screen=(UV-Bounds.xy)/max(Bounds.zw-Bounds.xy,.000001)*2-1;
    float3 ViewRay=normalize(float3((Screen.x-Camera.z)*Camera.x,(-Screen.y-Camera.w)*Camera.y,1));
    float3 Ray=float3(dot(ViewRay,LocalRow[0].xyz),dot(ViewRay,LocalRow[1].xyz),dot(ViewRay,LocalRow[2].xyz));
    float3 Origin=Eye.xyz-DonutSource.xyz;
    float3 Safe=lerp(-1,1,step(0,Ray))*max(abs(Ray),.00001);
    float3 A=(float3(-107,-107,-70)-Origin)/Safe;
    float3 B=(float3(107,107,1000)-Origin)/Safe;
    float3 Near=min(A,B),Far=max(A,B);
    float2 Span=float2(max(0,max(Near.x,max(Near.y,Near.z))),min(Far.x,min(Far.y,Far.z)));
    float Z=SceneZ(UV);
    Span.x=max(Span.x,Depth.x/max(ViewRay.z,.0001));
    Span.y=min(Span.y,min(Depth.y,max(0,Z-1.5))/max(ViewRay.z,.0001));
    if(Span.y<=Span.x) return 0;
    float Gain=smoothstep(.02,.85,State.y)*State.z;
    float Step=(Span.y-Span.x)/112;
    float3 Light=0;
    float Transmission=1;
    [loop] for(int I=0;I<112;++I) {
        float3 P=Eye.xyz+Ray*(Span.x+(I+.5)*Step);
        // Select the pulse ahead of its wake: ordinary nearest-centre selection
        // cuts a long tail halfway between two heads (spaced about 189 metres apart).
        float4 Pulse=DonutPulse[0];
        float Delta=P.z-Pulse.x;
        float Score=max(Delta,0)*4+max(-Delta,0);
        [unroll] for(int J=1;J<5;++J) {
            Delta=P.z-DonutPulse[J].x;
            float Candidate=max(Delta,0)*4+max(-Delta,0);
            if(Candidate<Score){Pulse=DonutPulse[J];Score=Candidate;}
        }
        float3 Q=float3(P.xy-DonutSource.xy,P.z-Pulse.x);
        float R=length(Q.xy);
        float2 Axis=Q.xy/max(R,.001);
        float Theta=atan2(Q.y,Q.x);
        float Phase=Pulse.y*2.4+Pulse.z*1.7;
        float C=cos(Phase),S=sin(Phase);
        float2 Around=float2(C*Axis.x+S*Axis.y,-S*Axis.x+C*Axis.y);
        float3 N=tex3Dlod(Noise,float4(float3(Around*2.4,Q.z/45)+Pulse.z*.31,0)).rgb;
        float Clots=saturate(N.g*2.6-.6);
        // ALE centreline radius ~101 m. The attached jump_ring.3db has only
        // 111.666 m clearance between its polygon edges; keep all light inside 107.
        float Radius=100.8908+2*sin(Theta*5-Phase)+2*(N.b-.5);
        float RadialWidth=R>Radius?6:13+5*Clots;
        float2 Cross=float2((R-Radius)/RadialWidth,
            (Q.z-5*sin(Theta*3+Phase))/(18+7*Clots));
        float Dist=dot(Cross,Cross);
        // The cross-section rolls as a vortex ring: cloudy knots move through the
        // body instead of drawing long parallel streaks around its circumference.
        float Roll=Pulse.y*5+Theta;
        float2 Swirl=float2(cos(Roll)*Cross.x-sin(Roll)*Cross.y,
            sin(Roll)*Cross.x+cos(Roll)*Cross.y);
        float3 Fine=tex3Dlod(Noise,float4(float3(Around*3+Swirl*.8,Pulse.z+Pulse.y*.8),0)).rgb;
        float Envelope=exp(-Dist*.95);
        float Clearance=1-smoothstep(102,107,R);
        float Body=Envelope*(.3+.75*smoothstep(.22,.78,Fine.r))*Clearance;
        float Halo=exp(-Dist*.65)*.035*Clearance;
        // A 240-metre wake rolls inward behind the moving head, never before its
        // birth point. Soft eddies break up the smoke without drawing parallel lines.
        float Behind=max(0,-Q.z);
        float Length=min(240,max(1,Pulse.y*425));
        float T=saturate(Behind/Length);
        float Curl=sin(Theta*3-Behind/65-Phase);
        float WakeRadius=Radius-6-22*T+6*Curl*T;
        float WakeWidth=14+10*T;
        float3 WakeNoise=tex3Dlod(Noise,float4(float3(Around*2.3+Swirl*.12,
            Behind/100+Pulse.z*.43-Pulse.y*.8),0)).rgb;
        float WakeFade=saturate(-Q.z/28)*pow(1-T,1.4);
        float Wake=exp(-pow((R-WakeRadius)/WakeWidth,2))*WakeFade*
            (.2+.85*smoothstep(.25,.7,WakeNoise.r))*.7*Clearance;
        float3 Cool=lerp(float3(.16,.35,.58),.16+TunnelTint.rgb*.55,.15*TunnelTint.w);
        float3 Warm=float3(.62,.79,.94);
        float3 Emission=Cool*(Body*.9+Wake*.65+Halo)+
            Warm*(Body*(.25+.45*Fine.g)+Wake*.15*WakeNoise.g);
        float LocalGain=Gain*Pulse.w;
        float Alpha=1-exp(-(Body+Wake*.6)*LocalGain*Step*.022);
        Light+=Transmission*Emission*LocalGain*Step*.055;
        Transmission*=1-Alpha;
    }
    // Compress hot cores before the LDR target clips away the moving clots.
    return float4(1-exp(-Light),1-Transmission);
}
