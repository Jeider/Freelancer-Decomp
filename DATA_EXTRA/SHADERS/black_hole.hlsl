// RP9_SKIP_OPTIMIZATION: compiled without the D3DX optimiser (it takes minutes over this loop).
// Ray-marched Schwarzschild black hole with an accretion disc. Units are horizon
// radii in the host's local frame (disc plane = XZ, spin axis = +Y). The lensed
// background is the already-rendered scene colour; this pass writes final colour.
float4 Remap:register(c7);
struct Vertex { float3 Position:POSITION0; float4 Color:COLOR0; float2 UV:TEXCOORD0; };
struct Interp { float4 Position:POSITION0; float4 Bounds:TEXCOORD0; };
Interp VSMain(Vertex In)
{
    Interp Out;
    Out.Position=float4(In.Position.xy*Remap.xy+Remap.zw,0,1);
    Out.Bounds=1.00001+float4(In.Position.xy,-In.Position.xy);
    return Out;
}
float4 State:register(c0);  // time, exposure, max steps, lens strength
float4 Target:register(c1); // inverse width/height, bound radius, 0
float4 Bounds:register(c2); // viewport uv min/max
float4 Depth:register(c3);  // near, far, depth partition min/max
float4 Eye:register(c4);    // local eye / Rh, Rh
float4 Camera:register(c5); // tan half fov x/y, 0, view depth of centre
float4 LocalRow[3]:register(c6);
float4 Disk:register(c9);   // inner, outer, opacity, spin
float4 Look:register(c10);  // heat, doppler, jet, glow
float4 Tint:register(c11);  // rgb, brightness
float4 Extra:register(c13); // x texture (0 smooth .. 1 torn, grainy, red at the rim), y redness towards the rim, z swirl, w disc picture mix
float4 Volume:register(c14); // x disc thickness (half-height over radius), y haze, z spiral bands, w smoke (dense gas strokes)
float4 Dbg:register(c16);    // console "bh <bits>": x scene depth off, y one layer, z no second family / smoke, w no haze / vortices
float4 Dbg2:register(c17);   // x background not lensed, y the disc's opacity left close to the eye, z where it is gone entirely (Rh) (near fade)
float4 Beam:register(c15);   // x which axis side carries the inflow beam (+1 / -1, 0 = both), y visibility, zw near fade: gone / whole (Rh from the eye)
float4 Misc:register(c12);  // x radius (Rh) within which scene depth is the horizon model and ignored, y no scene depth, z style (1 = Nomad red), w jet width
sampler2D Scene:register(s0);
sampler2D SceneDepth:register(s1);
sampler3D Noise:register(s2);
sampler2D Half:register(s4);   // PSComposite: the reduced-resolution march (alpha 0 = nothing drawn there)
float4 Low:register(c18);      // PSComposite: that target's width, height, 1/width, 1/height
float4 Slab:register(c19);     // volumetric gas near the eye on the disc: x strength, y half-height (Rh), z reach from the eye (Rh)
sampler3D Ring:register(s3);   // the mod's disc picture (one slice): top-down, centre = the hole, edge = the outer rim
float DistanceAt(float2 UV)
{
    if(Misc.y>.5) return 1e8; // no scene depth available: everything is sky
    float D=tex2Dlod(SceneDepth,float4(UV,0,0)).r;
    if(D>=.99999994) return 1e8;
    if(D>Depth.w+.00000012) return 0;
    float Z=saturate((D-Depth.z)/max(Depth.w-Depth.z,.000001));
    return Depth.x*Depth.y/max(Depth.y-Z*(Depth.y-Depth.x),.001);
}
// The 64^3 noise volume, read with a smooth (cubic) blend between texels instead of the plain
// linear one: close up the fine bands stretch a texel over many pixels, and linear filtering
// shows its cells as little rectangles.
float Noise3(float3 P)
{
    float3 Q=P*(.13*64);
    float3 I=floor(Q), F=Q-I;
    F=F*F*(3-2*F);
    return tex3Dlod(Noise,float4((I+F+.5)/64,0)).r;
}
float3 Blackbody(float T)
{
    float3 C0=float3(.6,.05,0), C1=float3(1,.35,.05), C2=float3(1,.72,.35);
    float3 C3=float3(1,.95,.88), C4=float3(.8,.88,1);
    T=max(T,0);
    float3 C=lerp(C0,C1,saturate(T/.35));
    C=lerp(C,C2,saturate((T-.35)/.25));
    C=lerp(C,C3,saturate((T-.6)/.25));
    C=lerp(C,C4,saturate((T-.85)/.35));
    return C;
}
// Disc emission at crossing X seen along ray direction V. Returns rgb in E, alpha in return.
// Close to the eye the disc and its haze fade out, as a planetary ring's band does: on the ring
// plane the gas puffs of the ring the hole sits in (om13_active_chunks) take over there.
float NearFade(float3 X)
{
    float Dist=length(X-Eye.xyz);
    // Dbg2.y: what is left close to the eye; Dbg2.z: right at the eye (within it) nothing at all
    return Beam.w>Beam.z ? lerp(Dbg2.y,1,smoothstep(Beam.z,Beam.w,Dist))*smoothstep(Dbg2.z*.4,Dbg2.z,Dist) : 1;
}
float DiscEmission(float3 X,float3 V,float Layer,out float3 E)
{
    float Rc=length(X.xz);
    float Inner=Disk.x, Outer=Disk.y;
    float Window=smoothstep(Inner*.85,Inner*1.15,Rc)*(1-smoothstep(Outer*.6,Outer*1.1,Rc));
    float Xr=max(Rc/Inner,1.0001);
    float TProf=pow(Xr,-.75)*pow(max(1-sqrt(1/Xr),0),.25)/.49;
    float Beta=clamp(sqrt(.5/max(Rc-1,.5)),0,.7);
    float3 Tan=float3(-X.z,0,X.x)/max(Rc,.0001);
    float CosT=dot(Tan,-V);
    float Gamma=1/sqrt(1-Beta*Beta);
    float G=1/(Gamma*(1-Beta*CosT))*sqrt(max(1-1/max(Rc,1.0001),.05));
    float GEff=pow(max(G,.0001),Look.y);
    float Omega=Disk.w*.9*pow(max(Rc,.1),-1.5);
    float Phi=atan2(X.z,X.x);
    float A=Phi-Omega*State.x;
    float2 CS=float2(cos(A),sin(A));
    // Eddies: the gas pattern is looked up through a slowly turning warp, so streaks curl into
    // local whirls instead of only running round the hole.
    float Sw=Extra.z;
    float Nw1=Noise3(float3(CS*Rc*.55,Rc*.8+7.3+State.x*.05));
    float Nw2=Noise3(float3(CS*Rc*.55+3.1,Rc*.8+1.7-State.x*.05));
    float Aw=A+Sw*2.2*(Nw1-.5);
    Rc=Rc*(1+Sw*.35*(Nw2-.5));
    CS=float2(cos(Aw),sin(Aw));
    float N1=Noise3(float3(CS*Rc*.2,Rc*1.7));
    float N2=Noise3(float3(CS*Rc*.4,Rc*5.3));
    float Tx=Extra.x;
    float N3=Noise3(float3(CS*Rc*1.0,Rc*13.0));
    float Fil=lerp(.35+.9*N1+.55*N2*N2,.15+1.2*N1+.9*N2*N2,Tx)*lerp(1,.55+.9*N3,Tx);
    float Arms=.75+.25*sin(2*A+4*log(max(Rc,.1)));
    float Dens=Window*Fil*Arms;
    float Floor=lerp(.4,.12,Tx);
    [branch] if(Volume.z>0)
    {
        // The shape of the Nomad Legacy hole, built from scratch: tightly wound spiral bands of
        // gas with dark slits between them, streaked along their run; far out the bands break
        // into loose arcs. The spiral turns slowly as a whole so it never winds itself shut.
        float R0=length(X.xz);
        float As=Phi-Disk.w*.08*State.x+Layer*.1;
        float Lr=log(max(R0/Inner,1));
        float Edge=pow(1-abs(V.y),3); // 1 seen edge-on, ~0 from 30 degrees up: layers interleave only near edge-on (else they weave)
        float Q=38*Lr+2*As+1.3*N1+1.8*(Nw1-.5)+Layer*2.3*Edge; // each layer's bands fall between the others', not on top
        float Band=saturate((.5+.5*sin(Q)-(.32+.3*N2))*3.5);
        // A second, looser family wound at another pitch and turning at another speed: the two
        // slide over each other and cross, so the bands lose their regular order.
        float As2=Phi-Disk.w*.13*State.x;
        float Q2=24*Lr+As2+2.2*N2+2.4*(Nw2-.5)+Layer*1.1*Edge+3;
        float Band2=saturate((.5+.5*sin(Q2)-(.4+.3*N1))*3);
        Band=max(Band,Band2*.75*lerp(.35,1,Edge)*(1-Dbg.z));
        float Pk=Volume.w;
        [branch] if(Pk>0 && Dbg.z<.5)
        {
            // Smoke: dense brush strokes of gas, two octaves of noise stretched along the orbit
            // and carried round with it (inner gas runs faster), laid over and between the bands.
            float2 CSk=float2(cos(A),sin(A));
            float S1=Noise3(float3(CSk*R0*.25,Lr*14+1.3));
            float S2=Noise3(float3(CSk*R0*.45,Lr*40+2.3));
            float Smoke=saturate(S1*.75+S2*.55-.2);
            Band=lerp(Band,max(Band,Smoke*1.1),.75*Pk);
        }
        float2 CSs=float2(cos(As),sin(As));
        float Streak=.55+.6*Noise3(float3(CSs*R0*.3,R0*9.0));
        float U=saturate((R0-Inner)/max(Outer-Inner,.001));
        float Arc=lerp(1,smoothstep(.3,.62,Noise3(float3(CSs*1.4,R0*.35+5.1))),smoothstep(.35,.85,U));
        float Rim=exp(-pow((R0-Inner*1.1)/(Inner*.35),2));
        float Sp=Window*saturate(Band*Streak*Arc+Rim+.4*Volume.w*N2);
        Dens=lerp(Dens,Sp,Volume.z);
        Floor=lerp(Floor,.03,Volume.z);
    }
    float Temp=pow(max(TProf,0),1+.6*Tx)*Look.x*GEff;
    float Intensity=Tint.w*6*pow(max(TProf,0),1.6)*pow(GEff,3)*(Floor+Dens);
    E=Blackbody(Temp)*Tint.rgb*Intensity;
    // Contrast: hot gold and white inside, deep red and darker towards the rim.
    float URim=saturate((length(X.xz)-Inner)/max(Outer-Inner,.001));
    float Red=Extra.y*smoothstep(.08,.65,URim);
    E*=lerp(float3(1,1,1),float3(1.05,.30,.10)*(1-.35*URim),Red);
    if(Misc.z>.5)
    {
        // The Nomad Legacy hole (the mod's startup screen): a huge red vortex seen from above, broad
        // spiral arms of glowing gas, orange and yellow towards a white-hot rim round a small
        // black shadow. The arms are logarithmic spirals that the differential rotation winds on.
        float Lr=log(max(Rc,.1));
        float Sp=A+1.35*Lr;
        float2 SC=float2(cos(Sp),sin(Sp));
        float W1=Noise3(float3(SC*1.6,Lr*2.2));
        float W2=Noise3(float3(SC*4.1,Lr*6.5+3.1));
        float Arm=pow(saturate(.5+.5*sin(2*Sp+5*W1)),1.6);
        float Gas=saturate(.04+.95*Arm*(.4+.9*W2)+.25*W1*Arm);
        float Edge=smoothstep(Inner*.85,Inner*1.05,Rc)*(1-smoothstep(Outer*.45,Outer,Rc));
        float U=saturate((Rc-Inner)/max(Outer-Inner,.001));
        float3 Ramp=lerp(float3(4.2,3.4,2.2),float3(3.2,1.1,.22),saturate(U/.06));
        Ramp=lerp(Ramp,float3(1.8,.16,.035),saturate((U-.06)/.22));
        Ramp=lerp(Ramp,float3(.55,.025,.01),saturate((U-.28)/.6));
        float Rim=exp(-pow((Rc-Inner*1.05)/(Inner*.12),2));
        float Fall=pow(Inner/max(Rc,Inner),.55);
        float Beam=pow(GEff,1.2);
        E=(Ramp*(.12+1.3*Gas)*Fall+float3(4.5,4.0,3.4)*Rim*1.5)*Tint.rgb*Tint.w*Beam;
        return saturate(Disk.z*Edge*(.12+.95*Gas)+Rim*.9);
    }
    float Alpha=saturate(Disk.z*Dens*1.6);
    if(Extra.w>0)
    {
        // The mod's own disc picture laid on the disc plane (it turns rigidly, as the old effect
        // did): its red spiral bands and dark slits, lit by the same beaming and lensed the same way.
        float Rp=length(X.xz)/Outer*(1+Layer*.02);
        float Ap=Phi-Disk.w*.06*State.x+Layer*.12;
        float4 Pic=tex3Dlod(Ring,float4(.5+.5*Rp*float2(cos(Ap),sin(Ap)),.5,0));
        float3 Ep=Pic.rgb*Pic.rgb*3.2*Tint.rgb*Tint.w*pow(GEff,2);
        E=lerp(E,Ep,Extra.w);
        Alpha=lerp(Alpha,saturate(Pic.a*Disk.z*1.3),Extra.w);
    }
    return Alpha;
}
float4 PSMain(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Bounds);
    float2 UV=(Pixel+.5)*Target.xy;
    float4 Base=tex2Dlod(Scene,float4(UV,0,0));
    float2 Screen=(UV-Bounds.xy)/max(Bounds.zw-Bounds.xy,.000001)*2-1;
    float3 ViewRay=normalize(float3(Screen.x*Camera.x,-Screen.y*Camera.y,1));
    float3 D=float3(dot(ViewRay,LocalRow[0].xyz),dot(ViewRay,LocalRow[1].xyz),dot(ViewRay,LocalRow[2].xyz));
    float3 O=Eye.xyz;
    float Rb=Target.z;
    // Entry into the bounding sphere.
    float B=dot(O,D);
    float Disc=B*B-dot(O,O)+Rb*Rb;
    clip(Disc);
    float Root=sqrt(max(Disc,0));
    float TEntry=max(0,-B-Root);
    clip(-B+Root);
    // Scene depth as a straight-ray parameter in horizon radii.
    float SceneZ=Dbg.x>.5 ? 1e8 : DistanceAt(UV);
    float TScene=SceneZ/max(ViewRay.z,.0001)/Eye.w;
    float3 Unbent=O+D*TScene;
    if(dot(Unbent,Unbent)<Misc.x*Misc.x) TScene=1e8; // the old horizon sphere model itself (Misc.x = its radius in Rh, padded)
    clip(TScene-TEntry);

    float3 P=O+D*TEntry;
    float3 V=D;
    float3 L=0;
    float T=1;
    float S=TEntry;
    bool Captured=false, HitScene=false;
    float DGlow=1e3, DRing=1e3;
    float3 LTor=0; // the vortices, kept apart so they never show over the shadow
    int MaxSteps=(int)State.z;
    float Status=0; // 0 marching, 1 captured, 2 scene hit, 3 escaped
    [loop] for(int I=0;I<255;++I)
    {
        float R=length(P);
        float Ds=clamp(R*lerp(.06,.12,saturate((R-4)/6)),.015,2.5); // longer strides where the field is weak
        Status=R<1.0 ? 1 : (S>=TScene ? 2 : ((R>Rb*1.001 && dot(P,V)>0) ? 3 : 0));
        if(Status>0 || I>=MaxSteps || T<.003) break;
        Ds=min(Ds,max(TScene-S,.001));
        // Inside the gas slab near the eye the stride stays short enough to resolve its billows.
        if(Slab.x>0 && abs(P.y)<Slab.y*2.5 && length(P-O)<Slab.z) Ds=min(Ds,max(.15,Slab.y*.5));
        float H2=dot(cross(P,V),cross(P,V));
        float Fade=1-smoothstep(.55*Rb,Rb,R);
        float3 A=-1.5*H2*P/pow(max(R,.5),5)*State.w*Fade;
        float3 Vn=normalize(V+A*Ds);
        float3 Pn=P+Vn*Ds;
        // Disc crossings. With a thickness the disc is a stack of layers flaring with radius
        // (y = Off * Th * rho), each a little shifted in its pattern: bands get depth and parallax,
        // the mid-plane is the brightest.
        float RhoP=length(P.xz), RhoN=length(Pn.xz);
        // The layers spread only when the disc is seen near edge-on, where that gives it a body;
        // from higher up they close onto the mid-plane, or their shifted copies of the bands
        // overlap into a brick pattern. Closed, one layer draws the same at a quarter of the cost.
        float Th=Volume.x*smoothstep(.36,.12,abs(D.y));
        float Nl=(Th>.001 && Dbg.y<.5) ? 4 : 1;
        float ThFrac=Th/max(Volume.x,1e-6); // as the layers close, their pattern shifts and shading fade too: no seam where four become one
        [loop] for(int K=0;K<4;++K)
        {
            if(K>=Nl) break;
            float Off=Nl>1 ? (K-1.5)/1.5 : 0;
            float F0=P.y-Off*Th*RhoP, F1=Pn.y-Off*Th*RhoN;
            [branch] if(F0*F1<0)
            {
                float Tx=F0/(F0-F1+1e-6);
                // A layer is a cone (y = s k rho): its crossing with the step's segment, solved exactly
                // (a quadratic) -- linear interpolation of F is off by an amount that jumps from one
                // step to the next, which close up drew the layers as bricks.
                float Kc=Off*Th;
                [branch] if(abs(Kc)>1e-5)
                {
                    float3 Dd=Pn-P;
                    float K2=Kc*Kc;
                    float Qa=Dd.y*Dd.y-K2*dot(Dd.xz,Dd.xz);
                    float Qb=2*(P.y*Dd.y-K2*dot(P.xz,Dd.xz));
                    float Qc=P.y*P.y-K2*dot(P.xz,P.xz);
                    float Dq=sqrt(max(Qb*Qb-4*Qa*Qc,0));
                    float Ia=abs(Qa)>1e-8 ? .5/Qa : 0;
                    float T1=Ia!=0 ? (-Qb-Dq)*Ia : -Qc/Qb, T2=Ia!=0 ? (-Qb+Dq)*Ia : T1;
                    // the root inside the segment on the cone's own side of the plane
                    float Y1=(P.y+T1*Dd.y)*Kc, Y2=(P.y+T2*Dd.y)*Kc;
                    bool G1=T1>=0 && T1<=1 && Y1>=0, G2=T2>=0 && T2<=1 && Y2>=0;
                    Tx=G1 && (!G2 || abs(T1-Tx)<abs(T2-Tx)) ? T1 : (G2 ? T2 : Tx);
                }
                float3 X=lerp(P,Pn,Tx);
                float Rc=length(X.xz);
                [branch] if(Rc>=Disk.x*.85 && Rc<=Disk.y*1.1)
                {
                    float3 E;
                    float Al=DiscEmission(X,Vn,Off*ThFrac,E)*NearFade(X);
                    // With the eye inside the gas slab, the sheet seen at a grazing angle would draw a
                    // hard horizon wall: there it gives way to the slab's own soft volume.
                    float CamIn=Slab.x>0 ? 1-smoothstep(Slab.y,Slab.y*3,abs(O.y)) : 0;
                    Al*=lerp(1,smoothstep(.03,.35,abs(Vn.y)),CamIn);
                    Al=1-pow(1-Al,1/Nl);
                    L+=T*Al*E*(Nl>1 ? lerp(1,(1-.45*abs(Off))/.7,ThFrac) : 1); // the four layers average to the one
                    T*=1-Al;
                }
            }
        }
        float Rho=length(P.xz);
        // The disc as a volume close to the eye: where the sheet fades out near the eye (NearFade),
        // a slab of gas takes its place -- billows of two noise octaves riding the disc's Keplerian
        // orbit, coloured like the disc at that radius, lit from the hot centre (brighter looking
        // inwards: forward scattering) and dimming what lies behind them.
        [branch] if(Slab.x>0 && abs(P.y)<Slab.y*2.5 && Rho>Disk.x*.8 && Rho<Disk.y && length(P-O)<Slab.z)
        {
            float Prof=exp(-pow(P.y/Slab.y,2));
            float Ak=atan2(P.z,P.x)-Disk.w*.9*pow(max(Rho,.5),-1.5)*State.x;
            float2 Ck=float2(cos(Ak),sin(Ak));
            float G1=Noise3(float3(Ck*Rho*.45,P.y*1.6/Slab.y+Rho*.3));
            float G2=Noise3(float3(Ck*Rho*1.1+5.3,P.y*3.5/Slab.y+Rho*.9));
            float Gas=pow(saturate(G1*.95+G2*.6-.6),1.5); // sparse billows with clear gaps
            float Near=1-NearFade(P);                         // where the sheet has faded
            float Reach=1-smoothstep(Slab.z*.6,Slab.z,length(P-O));
            float Dn=Prof*Gas*Near/max(1-Dbg2.y,.05)*Reach*smoothstep(Disk.x*.8,Disk.x*1.1,Rho)*(1-smoothstep(Disk.y*.7,Disk.y,Rho))*Slab.x;
            float Ur=saturate((Rho-Disk.x)/max(Disk.y-Disk.x,.001));
            float3 Gc=lerp(float3(1.7,1.3,.85),float3(1.25,.22,.06),smoothstep(0,.55,Ur))*pow(Disk.x/Rho,1.1);
            float Phase=.35+1.4*pow(saturate(dot(V,-P/max(length(P),.001))),4);
            L+=T*Gc*Phase*Dn*Tint.w*Ds*.6;
            T*=exp(-Dn*Ds*.9);
        }
        // Polar inflow: smoke streams above and below the hole, on a cone wide at the hole that
        // narrows away from it, wound with spiral streaks that turn and pour in towards the hole; it melts into the disc's
        // glow near the plane and fades when the axis is seen end-on (from above it stays behind) (warm white near the
        // hole, orange further out). Look.z is the strength, Misc.w the funnel's width.
        [branch] if(Look.z>0 && Dbg.w<.5)
        {
            float Ay=abs(P.y), Lv=Disk.y*.9;
            float Rf=Misc.w*.6*(.35+.3*max(Lv-Ay,0))+Disk.x*2.5*exp(-Ay/2.2); // wide at the hole, narrowing away; at the disc it spreads out over it (and the lens bends that sheet round with the arc)
            // The cheap envelope first; the noise and the streaks only where it matters.
            float Env=exp(-pow(Rho/(Rf*1.1),2))*smoothstep(.3,2.2,Ay)*(1-smoothstep(Lv*.55,Lv,Ay))*(.6+1.3*exp(-Ay/(Lv*.25)))*lerp(1,.15,D.y*D.y);
            [branch] if(Ay>.5 && Ay<Lv && Rho<Rf*1.8 && Env*Look.z>.01)
            {
                // Smoke pouring into the hole: no lanes and no turning (blades read as a propeller),
                // just billows on the funnel's walls, stretched along the flow and sliding down it;
                // a slow third octave breaks the funnel into patches.
                float Ang=atan2(P.z,P.x);
                float2 CA=float2(cos(Ang),sin(Ang));
                float Sm1=Noise3(float3(CA*Rho*.7,Ay*.22+State.x*.9));
                float Sm2=Noise3(float3(CA*Rho*1.6+3.1,Ay*.55+State.x*1.6));
                float Patch=Noise3(float3(CA*Rho*.25+7.7,Ay*.08+State.x*.3));
                float Smoke=saturate(Sm1*.75+Sm2*.45-.25)*smoothstep(.25,.65,Patch);
                float Shell=.35+.65*exp(-pow((Rho-Rf*.6)/(Rf*.45),2));
                float Dn=Env*Shell*(.15+1.5*Smoke)*1.3;
                // Disc colours at the base, so the funnel pours into the disc's glow; warm white higher up.
                float Uh=saturate(Ay/(Lv*.7));
                float3 Ct=lerp(float3(1.7,.85,.32),float3(1.55,1.38,1.15),smoothstep(0,.35,Uh));
                Ct=lerp(Ct,float3(1.2,1.0,.85),smoothstep(.35,1,Uh));
                LTor+=T*Ct*Dn*Look.z*Tint.w*Ds*.5; // in front of what lies behind it (the arc), behind what lies before it
            }
        }
        // Haze: thin glowing gas round the disc, hot near the hole and red at the rim, so the
        // slits between the bands glow softly instead of being empty.
        [branch] if(Volume.y>0 && Dbg.w<.5 && Rho>Disk.x*.8 && Rho<Disk.y*1.1 && abs(P.y)<(Volume.x*Rho*1.6+.25)*2.2) // within 2.2 scale heights of the disc
        {
            float Hh=Volume.x*Rho*1.6+.25;
            float Ur=saturate((Rho-Disk.x)/max(Disk.y-Disk.x,.001));
            float Hz=exp(-pow(P.y/Hh,2))*smoothstep(Disk.x*.8,Disk.x*1.3,Rho)*(1-smoothstep(Disk.y*.5,Disk.y*1.1,Rho));
            Hz*=NearFade(P);
            Hz*=.55+.9*Noise3(float3(P.x*.1,P.z*.1,Rho*1.4+P.y*.8)+State.x*.02); // stretched along the orbit, no square cells
            float3 Hc=lerp(float3(1.6,1.2,.8),float3(1.2,.12,.04),smoothstep(0,.5,Ur))*pow(Disk.x/Rho,1.2);
            L+=T*Hc*Hz*Volume.y*Tint.w*Ds*.35;
            T*=exp(-Hz*Volume.y*Ds*.04);
        }
        DGlow=min(DGlow,length(float2(Rho-Disk.x*1.15,P.y)));
        DRing=min(DRing,abs(R-1.5));
        P=Pn; V=Vn; S+=Ds;
    }
    Captured=Status==1;
    if(!Captured) L+=LTor*lerp(.5,1,T); // never over the shadow; half as strong where the disc glows behind it
    HitScene=Status==2;
    float3 Bg;
    if(Captured) Bg=0;
    else if(HitScene) Bg=Base.rgb;
    else
    {
        float3 Vc=V.x*LocalRow[0].xyz+V.y*LocalRow[1].xyz+V.z*LocalRow[2].xyz;
        if(Vc.z>.02)
        {
            float2 Sc=float2(Vc.x/Vc.z/Camera.x,-Vc.y/Vc.z/Camera.y);
            float2 UvB=Bounds.xy+(Sc*.5+.5)*(Bounds.zw-Bounds.xy);
            bool Inside=all(UvB>=Bounds.xy) && all(UvB<=Bounds.zw);
            float2 Uc=clamp(UvB,Bounds.xy,Bounds.zw);
            float3 Sample=tex2Dlod(Scene,float4(Uc,0,0)).rgb;
            float Zs=DistanceAt(Uc);
            // Not a foreground object, and not the old horizon sphere model (never shown).
            bool Far=Zs>Camera.w-Rb*Eye.w*.5 && abs(Zs-Camera.w)>Misc.x*Eye.w*1.3;
            Bg=(Inside && Far && Dbg2.x<.5) ? Sample : Base.rgb;
        }
        else Bg=Base.rgb;
    }
    if(!Captured) L+=T*float3(1,.85,.6)*Look.w*Tint.w*.6*exp(-DRing*DRing/.0009);
    L+=float3(1,.55,.2)*Tint.rgb*Look.w*Tint.w*.35*exp(-DGlow/max(Disk.x*.6,.01));
    L=max(L,0);
    float3 Lt=1-exp(-L*State.y);
    float3 Out=Lt+T*Bg;
    Out=lerp(Base.rgb,Out,Beam.y); // close to the hole the picture gives way to the time-stop ring's gas
    return float4(Out,1);
}

// The march at reduced resolution, brought up to the screen: the four nearest low-resolution
// texels, weighted bilinearly and by whether they were drawn at all (alpha), while the full-
// resolution pixel decides for itself whether an object in front hides the hole -- so the
// edges of ships and rocks before it stay sharp.
float4 PSComposite(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Bounds);
    float2 UV=(Pixel+.5)*Target.xy;
    float2 Screen=(UV-Bounds.xy)/max(Bounds.zw-Bounds.xy,.000001)*2-1;
    float3 ViewRay=normalize(float3(Screen.x*Camera.x,-Screen.y*Camera.y,1));
    float3 D=float3(dot(ViewRay,LocalRow[0].xyz),dot(ViewRay,LocalRow[1].xyz),dot(ViewRay,LocalRow[2].xyz));
    float3 O=Eye.xyz;
    float Rb=Target.z;
    float B=dot(O,D);
    float Disc=B*B-dot(O,O)+Rb*Rb;
    clip(Disc);
    float Root=sqrt(max(Disc,0));
    float TEntry=max(0,-B-Root);
    clip(-B+Root);
    float SceneZ=Dbg.x>.5 ? 1e8 : DistanceAt(UV);
    float TScene=SceneZ/max(ViewRay.z,.0001)/Eye.w;
    float3 Unbent=O+D*TScene;
    if(dot(Unbent,Unbent)<Misc.x*Misc.x) TScene=1e8;
    clip(TScene-TEntry);
    float2 L=UV*Low.xy-.5;
    float2 C0=floor(L), F=L-C0;
    float2 U0=(C0+.5)*Low.zw;
    float4 A=tex2Dlod(Half,float4(U0,0,0));
    float4 Bx=tex2Dlod(Half,float4(U0+float2(Low.z,0),0,0));
    float4 Cy=tex2Dlod(Half,float4(U0+float2(0,Low.w),0,0));
    float4 Dxy=tex2Dlod(Half,float4(U0+Low.zw,0,0));
    float4 W=float4((1-F.x)*(1-F.y),F.x*(1-F.y),(1-F.x)*F.y,F.x*F.y)*float4(A.a,Bx.a,Cy.a,Dxy.a);
    float Sum=dot(W,1);
    clip(Sum-1e-4);
    float3 Rgb=(A.rgb*W.x+Bx.rgb*W.y+Cy.rgb*W.z+Dxy.rgb*W.w)/Sum;
    return float4(Rgb,1);
}
