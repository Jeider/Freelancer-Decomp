// Art study: dense, roiling matter around an open passage. Not a fog overlay.
// Empty-space traversal plus a short dense volume integration. Art prototype,
// not a shipping GPU budget; no temporal noise/history or transparent wisps.
#ifndef MATTER_PARALLAX
#define MATTER_PARALLAX 0
#endif
#ifndef MATTER_LIGHT
#define MATTER_LIGHT 0
#endif
struct Vertex { float3 P:POSITION0; float4 C:COLOR0; float2 UV:TEXCOORD0; };
struct Interp { float4 P:POSITION0; float2 UV:TEXCOORD0; };
Interp VSMain(Vertex v) { Interp o;o.P=float4(v.P.xy,0,1);o.UV=v.UV;return o; }
sampler3D Noise:register(s1);
sampler2D OriginalFractures:register(s0); // actual jumptube5 from the game
sampler2D OriginalFlow:register(s2); // broad jumptube layer
float4 Params:register(c0); // y: material time; z: style; w: independent deformation rate
float4 TravelParams:register(c1); // x: independent camera travel clock (parallax mode)
float MatterTime() { return 3+(Params.y-3)*max(1,Params.w); }
float N(float3 p) {
    float3 q=p*32, cell=floor(q),f=frac(q);
    f=f*f*(3-2*f);
    return tex3Dlod(Noise,float4((cell+f+.5)/32,0)).r;
}
float3 Centre(float z) {
#if MATTER_PARALLAX
    // Slow, shallow bends; camera orientation stays fixed along the travel axis.
    return float3(.6*sin(z*.025),.25*sin(z*.031+.5),z);
#else
    return float3(1.4*sin(z*.08)+.6*sin(z*.21),.7*sin(z*.12+.5),z);
#endif
}
float2 MatterUV(float3 p,float layer) {
    float2 radial=p.xy-Centre(p.z).xy;
    float angle=atan2(radial.y,radial.x)/6.28318530718+.5;
    float curl=.018*sin(p.z*.48+angle*12.566+MatterTime()*.11);
    return float2(angle+curl+Params.y*lerp(-.018,.012,layer)+layer*.31,
                  p.z*.032+Params.y*lerp(.025,-.016,layer)+layer*.27);
}
float Field(float3 p) {
    float3 c=Centre(p.z);
    float2 xy=p.xy-c.xy;
    float twist=p.z*.11;
    float2 spun=float2(xy.x*cos(twist)-xy.y*sin(twist),xy.x*sin(twist)+xy.y*cos(twist));
    float3 q=float3(spun,p.z*.72);
    q+=.7*sin(q.yzx*1.15+float3(0,2,4)+MatterTime()*.27);
    float billow=N(q*.021)*.62+N(q*.047+.31)*.27+N(q*.10+.63)*.11;
    float radius=3.0+.22*sin(p.z*.43);
    // Density boundary has a real thickness/shape; all surface samples occlude
    // whatever lies behind them. Large smooth lobes, no alpha wisps or filaments.
    float field=radius-length(xy)+(billow-.5)*3.8;
#if MATTER_PARALLAX
    // Original texture displaces the density boundary in 3D. A coarse mip keeps
    // this actual relief smooth; finer levels supply shading in the volume.
    float height=tex2Dlod(OriginalFractures,float4(MatterUV(p,0),0,6.5)).r;
    field+=(height-.45)*.65;
#endif
    return field;
}
float3 Normal(float3 p) {
    const float2 e=float2(.025,-.025);
    return normalize(e.xyy*Field(p+e.xyy)+e.yyx*Field(p+e.yyx)+e.yxy*Field(p+e.yxy)+e.xxx*Field(p+e.xxx));
}
float4 PSMain(Interp i):COLOR0 {
#if MATTER_PARALLAX
    float travel=TravelParams.x*2.6;
#else
    float travel=Params.y*2.6;
#endif
    float3 eye=Centre(travel);
#if MATTER_PARALLAX
    float3 f=float3(0,0,1); // no yaw/pitch/roll oscillation tied to fast travel
#else
    float3 f=normalize(Centre(travel+.05)-eye);
#endif
    float3 right=normalize(cross(float3(0,1,0),f));
    float3 up=cross(f,right);
    float2 uv=(i.UV-.5)*float2(1.7777778,-1)*1.1547005;
    float3 ray=normalize(f+right*uv.x+up*uv.y);
#if MATTER_LIGHT
    // A source in tunnel space, beyond the visible folds. It follows the distant
    // centreline, rather than being a bright circle fixed to screen coordinates.
    float3 source=Centre(travel+52);
    float3 sourceVector=source-eye;
    float sourceDistance=length(sourceVector);
    float3 sourceDirection=sourceVector/sourceDistance;
    float sourceTransmission=1;
#endif
    float distance=.03;
    float hit=0;
    [loop]for(int step=0;step<128;++step){
        float gap=Field(eye+ray*distance);
        if(gap<(MATTER_PARALLAX?.90:.22)){hit=1;break;}
        distance+=clamp(gap*(MATTER_PARALLAX?.22:.32),.012,1.4);
        if(distance>65)break;
    }
    float3 color=float3(.006,.024,.052);
    if(hit>.5){
        float transmittance=1;
        float3 scattered=0;
        [loop]for(int sample=0;sample<28;++sample){
#if MATTER_LIGHT
            if(distance+sample*.09>sourceDistance)break;
#endif
            float3 p=eye+ray*(distance+sample*.09);
            float gap=Field(p);
            float density=(1-smoothstep(-.16,.22,gap))*10;
#if MATTER_PARALLAX
            float lod=max(1.5,log2(max((distance+sample*.09)*.8,1)));
            float fracture=tex2Dlod(OriginalFractures,float4(MatterUV(p,0),0,lod)).r;
            float nearFracture=tex2Dlod(OriginalFractures,float4(MatterUV(p,1),0,lod)).r;
            // A separate, broken front layer sits 0.55 units inside the main
            // wall. Ray integration gives genuine relative parallax/occlusion;
            // opposing UV advection makes the two layers slide past each other.
            float membrane=(1-smoothstep(.10,.30,abs(gap-.55)))*smoothstep(.12,.65,nearFracture)*5;
            float body=density;
            density+=membrane;
            float relief=(fracture*body+nearFracture*membrane)/max(density,.001);
#endif
            float3 light=normalize(Centre(p.z+4)-p);
            float lightGap=Field(p+light*.65);
            float diffuse=saturate((lightGap-gap)/.65*.65+.3);
            float shadow=exp2(-max(0,-lightGap)*2.1);
            float inner=N(p*.042+.41);
            float3 lit=float3(.10,.18,.30)*(.3+shadow*.3);
            lit+=float3(.32,.46,.60)*diffuse*shadow;
            lit+=float3(.008,.065,.12)*inner*inner;
#if MATTER_LIGHT
            // Incoming light grows deeper in the passage, while the existing
            // local density shading retains the dark sides of nearby folds.
            float incoming=8/(8+length(source-p));
            lit+=float3(.24,.42,.58)*incoming*diffuse*shadow;
#endif
            lit*=.82+.32*N(p*.16);
#if MATTER_PARALLAX
            // Texture shading belongs to each sampled depth, so it bends,
            // shades and disappears with the material instead of floating atop.
            lit*=lerp(.62,1.38,smoothstep(.025,.85,relief));
            lit+=float3(.012,.026,.035)*smoothstep(.50,.88,relief)*diffuse;
#endif
            lit=lerp(lit,float3(.006,.024,.052),1-exp2(-distance*.022));
            float alpha=1-exp2(-density*.09);
            scattered+=transmittance*alpha*lit;
            transmittance*=1-alpha;
            if(transmittance<.008)break;
        }
        color=scattered+transmittance*color;
#if MATTER_LIGHT
        sourceTransmission=transmittance;
#endif
        color=1-exp2(-color*2.25);
    }
#if MATTER_PARALLAX
    float luminance=dot(color,float3(.2126,.7152,.0722));
    float contrast=pow(smoothstep(.09,.67,luminance),1.6);
    color=lerp(float3(.001,.004,.012),float3(.28,.63,.78),contrast);
    color+=smoothstep(.74,.97,contrast)*float3(.21,.15,.09);
#else
    if(Params.z>1.5){
        float3 p=eye+ray*distance;
        float2 radial=p.xy-Centre(p.z).xy;
        float angle=atan2(radial.y,radial.x)/6.28318530718+.5;
        float2 uv=float2(angle-Params.y*.018,p.z*.032+Params.y*.025);
        // Project the real original layers onto the matter, not onto the screen.
        // The narrow axial fractures sharpen the lobes without replacing their
        // density or making new neon lines. Filter remote detail at its footprint.
        float lod=max(1,log2(max(distance*.8,1)));
        float fractures=tex2Dlod(OriginalFractures,float4(uv,0,lod)).r;
        float flow=tex2Dlod(OriginalFlow,float4(uv*float2(1,.67)+float2(Params.y*.03,.21),0,max(0,lod-2))).r;
        float luminance=dot(color,float3(.2126,.7152,.0722));
        float relief=lerp(.83,1.15,fractures);
        relief*=lerp(.97,1.03,flow);
        luminance*=lerp(1,relief,hit);
        float contrast=pow(smoothstep(.11,.66,luminance),1.55);
        // Quieter colour: contrast now comes mainly from the inherited texture.
        color=lerp(float3(.001,.004,.012),float3(.28,.63,.78),contrast);
        color+=smoothstep(.72,.96,contrast)*float3(.21,.15,.09);
    }else if(Params.z>.5){
        // Keep the density and lighting structure; grade the material itself.
        // Dark navy gaps and saturated cyan crests echo the original tunnel.
        float luminance=dot(color,float3(.2126,.7152,.0722));
        float contrast=pow(smoothstep(.10,.62,luminance),1.35);
        color=lerp(float3(.0005,.002,.012),float3(.04,.65,.95),contrast);
        color+=smoothstep(.72,.96,contrast)*float3(.23,.15,.04);
    }
#endif
#if MATTER_LIGHT
    float alignment=saturate(dot(ray,sourceDirection));
    float angularRadius2=max(0,1-alignment*alignment);
    float core=exp2(-angularRadius2/.00035)*3.2;
    float halo=exp2(-angularRadius2/.0024)*.85;
    float aura=exp2(-angularRadius2/.010)*.12;
    float3 glow=core*float3(1,.95,.86)+halo*float3(.28,.68,1)+aura*float3(.10,.36,.62);
    // The same integrated material opacity occludes the core and its halo.
    // The soft roll-off prevents a clipped white disk swallowing the texture.
    color=1-(1-color)*exp2(-glow*sourceTransmission);
#endif
    return float4(color,1);
}
