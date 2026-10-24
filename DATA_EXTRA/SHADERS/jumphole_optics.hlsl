// Additional optics for the scoped jumphole. All colour comes from the current
// scene; the mirror is a screen-space environment approximation, not a cubemap.
float4 Remap:register(c7);
struct Vertex { float3 Position:POSITION0; float4 Color:COLOR0; float2 UV:TEXCOORD0; };
struct Interp { float4 Position:POSITION0; float4 Bounds:TEXCOORD0; };
Interp VSOpticsScreen(Vertex In)
{
    Interp Out;
    Out.Position=float4(In.Position.xy*Remap.xy+Remap.zw,0,1);
    Out.Bounds=1.00001+float4(In.Position.xy,-In.Position.xy);
    return Out;
}
Interp VSOpticsWorld(Vertex In) { return VSOpticsScreen(In); }
float4 State:register(c0); // time96, opening, activation, entry
float4 Target:register(c1); // inverse width/height, refraction, gain
float4 Bounds:register(c2);
float4 Depth:register(c3); // near, far, depth partition min/max
float4 Eye:register(c4); // local eye, mirror radius
float4 Camera:register(c5); // tan half FOV x/y, optics bound radius (600), mirror strength
float4 LocalRow[3]:register(c6); // camera(+Z forward) to local rotation
float4 ShipBounds:register(c9); // UV centre, ellipse radii
float4 Palette:register(c11); // linear RGB multiplier for the subtle mirror glint
float4 Ship:register(c10); // view depth, half depth band, authorized strength, progress
sampler2D Scene:register(s0);
sampler2D SceneDepth:register(s1);
sampler3D Noise:register(s2);
float DistanceAt(float2 UV)
{
    float D=tex2Dlod(SceneDepth,float4(UV,0,0)).r;
    if(D>=.99999994) return 1e8;
    if(D>Depth.w+.00000012) return 0;
    float Z=saturate((D-Depth.z)/max(Depth.w-Depth.z,.000001));
    return Depth.x*Depth.y/max(Depth.y-Z*(Depth.y-Depth.x),.001);
}
float FootprintMin(float2 UV)
{
    return min(min(DistanceAt(UV+Target.xy),DistanceAt(UV-Target.xy)),
        min(DistanceAt(UV+float2(Target.x,-Target.y)),DistanceAt(UV+float2(-Target.x,Target.y))));
}
float EdgeFade(float2 UV)
{
    return smoothstep(0,.025,min(min(UV.x-Bounds.x,Bounds.z-UV.x),min(UV.y-Bounds.y,Bounds.w-UV.y)));
}
float2 Sphere(float3 Ray,float Radius)
{
    float B=dot(Eye.xyz,Ray);
    float D=B*B-dot(Eye.xyz,Eye.xyz)+Radius*Radius;
    float Root=sqrt(max(0,D));
    return D>0 ? float2(max(0,-B-Root),max(0,-B+Root)) : 0;
}
float4 PSOpticsWorld(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Bounds);
    float2 UV=(Pixel+.5)*Target.xy;
    float4 Base=tex2Dlod(Scene,float4(UV,0,0));
    if(Target.w<=0) return Base;
    float SceneZ=DistanceAt(UV);
    if(SceneZ<200) return Base;
    float2 Screen=(UV-Bounds.xy)/max(Bounds.zw-Bounds.xy,.000001)*2-1;
    float3 ViewRay=normalize(float3(Screen.x*Camera.x,-Screen.y*Camera.y,1));
    float3 Ray=float3(dot(ViewRay,LocalRow[0].xyz),dot(ViewRay,LocalRow[1].xyz),dot(ViewRay,LocalRow[2].xyz));
    float2 Span=Sphere(Ray,max(1,Camera.z));
    Span.y=min(Span.y,max(0,SceneZ-2)/max(ViewRay.z,.0001));
    if(Span.y<=Span.x) return Base;
    float3 Result=Base.rgb;
    // A curved optical surface belongs to the entrance throat, not a mirror ball.
    // Only the local -Z approach can see it; its visibility dies before a side view.
    float3 MouthEye=Eye.xyz-float3(0,0,-240);
    float Front=smoothstep(.18,.60,-MouthEye.z/max(length(MouthEye),.001));
    float Hit=(-240-Eye.z)/max(Ray.z,.00001);
    if(Front>0 && Ray.z>0 && Hit>0 && Hit*ViewRay.z+2<SceneZ)
    {
        float3 P=Eye.xyz+Ray*Hit;
        float2 Cap=P.xy/max(1,Eye.w);
        float Radius=length(Cap);
        float3 Liquid=tex3Dlod(Noise,float4(P/180+State.x/32*float3(1,-2,1),0)).rgb-.5;
        float Aperture=1-smoothstep(.72,1.06,Radius+Liquid.r*.10);
        float3 N=normalize(float3(Cap*.78,-sqrt(max(.12,1-dot(Cap,Cap)*.60))));
        N=normalize(N+Liquid*(.20+State.z*.16));
        float3 NCam=N.x*LocalRow[0].xyz+N.y*LocalRow[1].xyz+N.z*LocalRow[2].xyz;
        float3 Reflected=reflect(ViewRay,NCam);
        // Fold the rear hemisphere into the available screen environment. Liquid
        // facets are sampled in object space, so camera orbit cannot drag the field.
        float2 Mirror=Reflected.xy/(1+abs(Reflected.z));
        float2 Centre=(Bounds.xy+Bounds.zw)*.5;
        float2 Candidate=Centre+float2(Mirror.x,-Mirror.y)*(Bounds.zw-Bounds.xy)*.46;
        Candidate+=Liquid.gb*Target.z*(1+State.z);
        Candidate=clamp(Candidate,Bounds.xy+Target.xy,Bounds.zw-Target.xy);
        float Protect=max(200,Hit*ViewRay.z);
        if(Aperture>0 && FootprintMin(Candidate)>=Protect)
        {
            float3 Reflection=tex2Dlod(Scene,float4(Candidate,0,0)).rgb;
            float Facing=saturate(abs(dot(N,Ray)));
            float Fresnel=pow(1-Facing,3);
            float Mask=Aperture*Front*smoothstep(0,.16,Facing)*saturate(Camera.w*Target.w)*EdgeFade(UV);
            Reflection=Reflection+float3(.018,.035,.052)*Palette.rgb*(1+Fresnel*2);
            Result=lerp(Result,Reflection,Mask);
        }
    }
    return float4(Result,Base.a);
}
float ShipMember(float Z)
{
    return (Z>0 && abs(Z-Ship.x)<=max(Ship.y,1)) ? 1 : 0;
}
float4 PSOpticsShip(Interp In,float2 Pixel:VPOS):COLOR0
{
    clip(In.Bounds);
    float2 UV=(Pixel+.5)*Target.xy;
    float4 Base=tex2Dlod(Scene,float4(UV,0,0));
    if(Ship.z<=0 || Target.w<=0) return Base;
    float2 Ellipse=(UV-ShipBounds.xy)/max(ShipBounds.zw,.000001);
    float Mask=1-smoothstep(.65,1,dot(Ellipse,Ellipse));
    if(Mask<=0) return Base;
    float Z=DistanceAt(UV);
    if(Z<=0 || Z<Ship.x-max(Ship.y,1)) return Base; // cockpit and nearer occluders
    float Strength=saturate(Ship.z)*saturate(Target.w)*Mask*EdgeFade(UV);
    float2 Centre=(Bounds.xy+Bounds.zw)*.5;
    float2 ToCentre=Centre-ShipBounds.xy;
    float2 Direction=length(ToCentre)>.001 ? normalize(ToCentre) : float2(0,-1);
    float2 Relative=UV-ShipBounds.xy;
    // Inverse mapping moves both silhouette edges; displaced background erases the
    // previous edge rather than retaining an undeformed duplicate underneath.
    float Along=dot(Relative,Direction);
    float2 Candidate=UV-Direction*Along*Strength*.32-ToCentre*Strength*.055;
    float4 N=tex3Dlod(Noise,float4(Ellipse*.35,State.x/32+Ship.w,0));
    Candidate+=(N.gb-.5)*ShipBounds.zw*Strength*.14;
    Candidate=clamp(Candidate,Bounds.xy+Target.xy,Bounds.zw-Target.xy);
    float Source=DistanceAt(Candidate);
    float Footprint=FootprintMin(Candidate);
    if(Footprint<=0 || Footprint<Ship.x-max(Ship.y,1)) return Base;
    if(ShipMember(Z)+ShipMember(Source)<.5) return Base;
    // Context guarantees the player-only transit draw; the tight depth band also
    // prevents tunnel/background pixels outside the displaced silhouette changing.
    return tex2Dlod(Scene,float4(Candidate,0,0));
}
