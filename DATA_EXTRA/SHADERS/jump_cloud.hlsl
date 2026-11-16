// Reference study: actively rolling blue clouds, broad luminous depth.
// Deterministic volume noise plus a baked cloud modulation layer; no retail textures.
struct Vertex { float3 P:POSITION0; float4 C:COLOR0; float2 UV:TEXCOORD0; };
struct Interp { float4 P:POSITION0; float2 UV:TEXCOORD0; };
Interp VSMain(Vertex v) { Interp o;o.P=float4(v.P.xy,0,1);o.UV=v.UV;return o; }
float4 ViewportRemap:register(c7);
Interp VSComposite(Vertex v) { Interp o;o.P=float4(v.P.xy*ViewportRemap.xy+ViewportRemap.zw,0,1);o.UV=v.UV;return o; }
sampler3D Noise:register(s1);
sampler2D CloudLayer:register(s0);
sampler2D SplinePath:register(s2);
float4 Animation:register(c0);
float4 Travel:register(c1);
float4 CameraEye:register(c2);
float4 CameraForward:register(c3);
float4 CameraRight:register(c4);
float4 CameraUp:register(c5);
float4 ViewParams:register(c6); // aspect, vertical ray span
float4 PrimaryTint:register(c7); // authored layer colour, including brightness
float4 AccentTint:register(c8);
float N(float3 p) {
    float3 q=p*32,cell=floor(q),f=frac(q);
    f=f*f*(3-2*f);
    return tex3Dlod(Noise,float4((cell+f+.5)/32,0)).r;
}
float3 Centre(float z) {
    // Cubic spline baked once into a filtered half-float path texture. Camera
    // uses the exact CPU spline; the dense table is only for volume samples.
    float2 p=tex2Dlod(SplinePath,float4((z+128)/16384+.5/8192,.5,0,0)).xy;
    return float3(p,z);
}
float Field(float3 p) {
    float t=Animation.y*.09;
    float depth=p.z-Travel.x*2.6;
    // Keep the near field exact. Distant axial detail grows with its footprint,
    // so increasingly long rays do not hop between tiny unresolved cloud lobes.
    float farDepth=max(0,depth-48);
    float shapeZ=p.z-farDepth+48*log2(1+farDepth/48)*.69314718;
    float2 v=p.xy-Centre(p.z).xy;
    // Keep the cross-section upright. Only the centreline changes direction;
    // cloud deformation must not turn the entire wall around the flight axis.
    float3 q=float3(v,shapeZ*.62);
    // Counter-moving domain warps roll the folds themselves, independently of
    // camera advance. Large, smooth lobes with a small eroded cloud detail.
    q+=.85*sin(q.yzx*.94+float3(0,2,4)+t*.8);
    q+=.23*sin(q.zxy*2.1+float3(1,3,0)-t*1.3);
    // Preserve the approved near clouds. Filter unresolved far turbulence toward
    // its mean instead of letting it sparkle around the vanishing point.
    float coarse=1-smoothstep(350,520,depth);
    float medium=1-smoothstep(180,400,depth);
    float detail=1-smoothstep(55,160,depth);
    float n=lerp(.5,N(q*.021),coarse)*.59+lerp(.5,N(q*.049+.31),medium)*.25+lerp(.5,N(q*.14+.63),detail)*.16;
    float angle=atan2(v.y,v.x);
    float folds=.38*sin(angle*5+.45*sin(shapeZ*.37))*sin(shapeZ*.23+t*.7);
    return 3.2-length(v)+(n-.5)*3.7+folds;
}
float4 PSMain(Interp i):COLOR0 {
    float travel=Travel.x*2.6;
    float3 eye=CameraEye.xyz;
    float2 uv=(i.UV-.5)*float2(ViewParams.x,-1)*ViewParams.y;
    // Anticipate the broad bend with a smoothed path tangent; world-up means
    // no banking/roll. This follows the spline without shaking the camera.
    float3 ray=normalize(CameraForward.xyz+CameraRight.xyz*uv.x+CameraUp.xyz*uv.y);
    float endDistance=240/ray.z;
    // Only diffuse depth colour: no endpoint sphere or screen-space halo.
    float3 primary=saturate(PrimaryTint.rgb),accent=saturate(AccentTint.rgb);
    float3 bodyTint=lerp(primary,accent,.45);
    float3 background=lerp(primary,accent,.12)*.04;
    float distance=.04;
    float firstDepth=240;
    float transmission=1;
    float3 scattered=0;
    // Share traversal across every cloud/gap. The former 200-step approach plus
    // 64-step integration stranded grazing rays in empty gaps after a thin fold,
    // exposing the dark clear colour as isolated flecks. Empty steps cost only
    // one field lookup; light and texture evaluation happen in matter only.
    [loop]for(int step=0;step<256;++step){
        if(distance>=endDistance||transmission<.006)break;
        float3 p=eye+ray*distance;
        float gap=Field(p);
        if(gap>=.32){
            distance+=clamp((gap-.3)*.26,.06,1.2)*max(1,distance/32);
            continue;
        }
        float density=(1-smoothstep(-.22,.32,gap))*5.8;
        if(density>.05)firstDepth=min(firstDepth,distance*ray.z);
        // Keep the nearby cloud's existing lighting and structure. A separate
        // distant fade extends the passage without changing the approved folds.
        float3 light=normalize(Centre(travel+24)-p);
        float towardLight=Field(p+light*.65);
        float diffuse=saturate((towardLight-gap)/.65*.7+.28);
        float shadow=exp2(-max(0,-towardLight)*2.2);
        float incoming=exp2(-length(Centre(travel+24)-p)*.055);
        float fine=N(p*.15+Animation.y*.0008);
        float3 lit=lerp(primary,accent,.2)*.06;
        lit+=bodyTint*.94*pow(diffuse,1.35)*shadow*(.45+incoming*1.5);
        lit+=accent*.13*incoming;
        lit*=.74+.35*fine+.12*N(p*.31);
        float depth=p.z-travel;
        float2 around=p.xy-Centre(p.z).xy;
        float angle=atan2(around.y,around.x)/6.28318530718+.5;
        // At current x2 playback: travel +29.12*.035, pan -16*.11.
        // Net -.7408 UV/s: opposite the forward flow.
        float2 layerUV=float2(angle,p.z*.035-Animation.y*.11);
        float layerLOD=max(0,log2(max(distance*.45,1)));
        float modulation=tex2Dlod(CloudLayer,float4(layerUV,0,layerLOD)).r;
        float layerStrength=1-smoothstep(65,180,depth);
        lit*=lerp(1,lerp(.72,1.30,smoothstep(.22,.75,modulation)),layerStrength);
        float fade=smoothstep(80,225,depth);
        density*=1-fade;
        lit=lerp(lit,background,fade);
        float nearStride=(.12+smoothstep(18,80,depth)*.55)*max(1,depth/80);
        float stride=gap>.42?clamp((gap-.3)*.24,nearStride,max(1.2,nearStride)):nearStride;
        float opacity=1-exp2(-density*stride);
        scattered+=transmission*opacity*lit;
        transmission*=1-opacity;
        distance+=stride;
    }
    #if JUMP_CLOUD_DIAGNOSTIC
    // Offline probe: integration distance, remaining transmission, first surface.
    return float4(saturate(distance/endDistance),transmission,saturate(firstDepth/120),1);
    #endif
    float3 color=scattered+transmission*background;
    // Distance haze blends unresolved remote folds into the same light field.
    // Unlike a flat end cap, this reaches each cloud at its own spatial depth.
    color=lerp(color,background,smoothstep(55,210,firstDepth)*.96);
    color=1-exp2(-color*2.6);
    return float4(color,1);
}

// Rendered before the ship. Native-resolution geometry is never downsampled.
float4 PSComposite(Interp i):COLOR0 { return float4(tex2D(CloudLayer,i.UV).rgb,1); }
