// RP9 reflective surface profile. Authored diffuse/envmap/specular/emissive and fog
// remain material inputs. No object-name or ship-only assumptions; no normal-map fiction.
// All lights and vertices use the same D3D view space, avoiding large world coordinates.
row_major float4x4 WorldView : register(c0);
row_major float4x4 Projection : register(c4);
row_major float4x4 NormalView : register(c8);
row_major float4x4 EnvironmentMatrix : register(c12);
float4 VertexModes : register(c16); // colour present, base UV index, env transform flags

struct SurfaceVertex
{
    float3 Position : POSITION0;
    float3 Normal : NORMAL0;
    float4 Colour : COLOR0;
    float2 Uv0 : TEXCOORD0;
    float2 Uv1 : TEXCOORD1;
    float2 Uv2 : TEXCOORD2;
#ifdef SURFACE_INSTANCED
    float4 InstanceWorld0 : TEXCOORD3;
    float4 InstanceWorld1 : TEXCOORD4;
    float4 InstanceWorld2 : TEXCOORD5;
    float4 InstanceWorld3 : TEXCOORD6;
    float4 InstanceNormal0 : TEXCOORD7;
    float4 InstanceNormal1 : TEXCOORD8;
    float4 InstanceNormal2 : TEXCOORD9;
    float4 InstanceNormal3 : TEXCOORD10;
#endif
};
struct SurfacePixel
{
    float4 Position : POSITION0;
    float3 ViewPosition : TEXCOORD0;
    float3 Normal : TEXCOORD1;
    float2 Uv : TEXCOORD2;
    float4 Colour : COLOR0;
};
SurfacePixel VSMain(SurfaceVertex In)
{
    SurfacePixel Out;
#ifdef SURFACE_INSTANCED
    float4 P=In.Position.x*In.InstanceWorld0+In.Position.y*In.InstanceWorld1+
             In.Position.z*In.InstanceWorld2+In.InstanceWorld3;
    Out.Normal=In.Normal.x*In.InstanceNormal0.xyz+In.Normal.y*In.InstanceNormal1.xyz+
               In.Normal.z*In.InstanceNormal2.xyz;
#else
    float4 P = mul(float4(In.Position, 1.0), WorldView);
    Out.Normal = mul(float4(In.Normal, 0.0), NormalView).xyz;
#endif
    Out.Position = mul(P, Projection);
    Out.ViewPosition = P.xyz;
    Out.Uv = VertexModes.y > 1.5 ? In.Uv2 : (VertexModes.y > 0.5 ? In.Uv1 : In.Uv0);
    Out.Colour = VertexModes.x > 0.5 ? In.Colour : float4(1.0, 1.0, 1.0, 1.0);
    return Out;
}

// s0 is fixed-function stage 0 (the base texture). The environment and shadow maps use
// samplers 8..10, which fixed-function rendering never touches, so they stay bound.
sampler2D DiffuseMap : register(s0);
#ifdef SURFACE_ENV_CUBE
samplerCUBE EnvironmentMap : register(s10);
#else
sampler2D EnvironmentMap : register(s10);
#endif
float4 MaterialDiffuse : register(c0);
float4 MaterialAmbient : register(c1);
float4 MaterialEmission : register(c2);
float4 MaterialSpecular : register(c3); // rgb dielectric F0, w perceptual roughness
float4 Surface : register(c4); // base texture present, vertex colour, env strength, light count
float4 Fog : register(c5); // start, end, density, mode
float4 FogColour : register(c6); // rgb, w range fog
float4 BaseOps : register(c7); // stage0 colour/alpha ops; env transform flag, env colour op
row_major float4x4 PixelEnvironmentMatrix : register(c8);
struct SurfaceLight
{
    float4 PositionType;
    float4 DirectionRange;
    float4 DiffuseFalloff;
    float4 SpecularOuter;
    float4 AttenuationInner;
};
SurfaceLight Lights[8] : register(c12);
row_major float4x4 ShadowNear : register(c52);
row_major float4x4 ShadowFar : register(c56);
float4 ShadowControl : register(c60); // enabled receiver, near-map texel size, fade start/end
float4 ShadowSunRay : register(c61);
float4 ShadowPlanetControl : register(c62); // x planet count, y near moving-caster map valid
float4 ShadowRange : register(c63); // length, fade start, near/far map world widths
float4 ShadowPlanets[8] : register(c64);
float4 ShadowFilter : register(c72); // tan(angular radius), search/filter samples, strength
float4 ShadowBias : register(c73); // near/far world texel size, bias scale
float4 ShadowDepthSpan : register(c74); // near/far orthographic depth spans, metres
float4 SurfaceFinish : register(c75); // highlight strength, clear coat, brushed finish, valid
float4 ShadowQuality : register(c76); // full-quality distance, adaptive enabled, low search/filter taps
float4 WeaponGlintControl : register(c77); // count, strength, inverse radius squared, camera range squared
struct WeaponGlint {float4 Position;float4 Colour;};
WeaponGlint WeaponGlints[8] : register(c78);
float4 MaterialStyle : register(c94); // cockpit, glass, glass strength, cockpit finish
// x far-map texel size; y shadow reach of casters stored with a negative depth (NPC ships);
// z simple receiver (one bilinear comparison instead of PCSS); w the far static map is valid.
float4 ShadowExtra : register(c95);
sampler2D ShadowNearMap : register(s8);
sampler2D ShadowFarMap : register(s9);
// Stations (the cached far map, same projection as ShadowFarMap, which then holds only
// moving casters). Kept apart so a ship above a station cannot replace the station's
// depth and cut a lit hole into its shadow where the ship is beyond its shadow reach.
sampler2D ShadowStaticMap : register(s11);
// The near map's moving casters (ships, asteroids; ShadowPlanetControl.y), kept apart from the
// near map's stations for the same reason.
sampler2D ShadowNearLiveMap : register(s12);

// The golden-angle spiral. Each tap rotates the previous direction instead of
// evaluating sincos per tap.
static const float2 ShadowGolden=float2(-0.73736887,0.67549029);
float2 ShadowRotate(float2 Direction)
{
    return float2(Direction.x*ShadowGolden.x-Direction.y*ShadowGolden.y,
                  Direction.x*ShadowGolden.y+Direction.y*ShadowGolden.x);
}
// Map texels hold the caster depth; a negative value marks a caster whose shadow
// reaches only ShadowExtra.y metres (NPC ships), positive the full ShadowRange.x.
float ShadowDepth(sampler2D Map, float2 Uv, out float Reach)
{
    float Raw=tex2Dlod(Map,float4(Uv,0,0)).r;
    Reach=Raw<0 ? ShadowExtra.y : ShadowRange.x;
    return abs(Raw);
}
float ShadowOcclusion(float Gap, float Bias, float Reach)
{
    // Metres behind the nearest recorded surface, not distance from the camera.
    if(Gap<=Bias || Gap>=Reach) return 0;
    return 1.0-smoothstep(Reach*0.8,Reach,Gap);
}
float TapOcclusion(sampler2D Map, float2 Uv, float ReceiverDepth, float Bias, float DepthSpan)
{
    float Reach;
    return ShadowOcclusion((ReceiverDepth-ShadowDepth(Map,Uv,Reach))*DepthSpan,Bias,Reach);
}
// The darker of the two maps at one texel (Dual: the far map and the station map).
float DualOcclusion(sampler2D Map, sampler2D Extra, bool Dual, float2 Uv, float ReceiverDepth,
                    float Bias, float DepthSpan)
{
    float Occlusion=TapOcclusion(Map,Uv,ReceiverDepth,Bias,DepthSpan);
    [branch] if(Dual) Occlusion=max(Occlusion,TapOcclusion(Extra,Uv,ReceiverDepth,Bias,DepthSpan));
    return Occlusion;
}
float ShadowFilteredOcclusion(sampler2D Map, sampler2D Extra, bool Dual, float2 Uv, float ReceiverDepth,
                             float2 Gradient, float Bias, float DepthSpan, float Texel)
{
    // Interpolate comparison results, never raw depths across silhouettes.
    // Fractional texel motion then changes coverage continuously instead of
    // switching every disk sample between fully lit and fully shadowed.
    float2 Grid=Uv/Texel-0.5;
    float2 Base=(floor(Grid)+0.5)*Texel;
    float2 F=frac(Grid);
    float2 U0=Base,U1=Base+float2(Texel,0);
    float2 U2=Base+float2(0,Texel),U3=Base+Texel;
    float O0=DualOcclusion(Map,Extra,Dual,U0,ReceiverDepth+dot(Gradient,U0-Uv),Bias,DepthSpan);
    float O1=DualOcclusion(Map,Extra,Dual,U1,ReceiverDepth+dot(Gradient,U1-Uv),Bias,DepthSpan);
    float O2=DualOcclusion(Map,Extra,Dual,U2,ReceiverDepth+dot(Gradient,U2-Uv),Bias,DepthSpan);
    float O3=DualOcclusion(Map,Extra,Dual,U3,ReceiverDepth+dot(Gradient,U3-Uv),Bias,DepthSpan);
    return lerp(lerp(O0,O1,F.x),lerp(O2,O3,F.x),F.y);
}
float3 ShadowDerivatives(float3 Q)
{
    float2 Uv=Q.xy*float2(0.5,-0.5)+0.5;
    float2 Dx=ddx(Uv),Dy=ddy(Uv);
    float Zx=ddx(Q.z),Zy=ddy(Q.z);
    float Det=Dx.x*Dy.y-Dx.y*Dy.x;
    float2 Gradient=abs(Det)>1.e-12 ?
        float2(Zx*Dy.y-Zy*Dx.y,Dx.x*Zy-Dy.x*Zx)/Det : 0;
    return float3(Gradient,max(length(Dx),length(Dy))*0.5);
}
float ShadowCompare(sampler2D Map, sampler2D Extra, bool Dual, float3 Q, float WorldWidth,
                    float WorldTexel, float DepthSpan, float Texel, float3 Derivatives, float2 Samples,
                    bool Simple)
{
    float2 Uv=Q.xy*float2(0.5,-0.5)+0.5;
    float2 Gradient=Derivatives.xy;
    float Bias=max(0.03,WorldTexel*ShadowBias.z);
    // Surfaces facing away from the sun only modulate their faint reflection by
    // visibility, and simple (distant ship) receivers need no penumbra estimate.
    [branch] if(Simple)
        return 1.0-ShadowFilteredOcclusion(Map,Extra,Dual,Uv,Q.z,Gradient,Bias,DepthSpan,Texel);
    if(ShadowFilter.x<=0)
        return 1.0-DualOcclusion(Map,Extra,Dual,Uv,Q.z,Bias,DepthSpan);
    float SearchRadius=max(WorldTexel,ShadowRange.x*ShadowFilter.x)/WorldWidth;
    // Always include the central ray: a narrow nearby caster must not vanish
    // merely because none of the wider blocker-search disk taps hits it.
    float CenterReach;
    float CenterGap=(Q.z-ShadowDepth(Map,Uv,CenterReach))*DepthSpan;
    float CenterBlock=CenterGap>Bias && CenterGap<CenterReach ? 1 : 0;
    float DepthSum=CenterBlock*CenterGap,Blockers=CenterBlock;
    [branch] if(Dual)
    {
        CenterGap=(Q.z-ShadowDepth(Extra,Uv,CenterReach))*DepthSpan;
        if(CenterGap>Bias && CenterGap<CenterReach) {DepthSum+=CenterGap;Blockers+=1;}
    }
    float2 Direction=float2(1,0);
    float InverseSearch=1.0/Samples.x;
    [loop] for(int I=0;I<64;++I)
    {
        if(I>=Samples.x) break;
        float Weight=saturate(Samples.x-I);
        float2 Offset=Direction*(sqrt((I+0.5)*InverseSearch)*SearchRadius);
        Direction=ShadowRotate(Direction);
        float Reach;
        float Depth=ShadowDepth(Map,Uv+Offset,Reach);
        float Gap=(Q.z+dot(Gradient,Offset)-Depth)*DepthSpan;
        if(Gap>Bias && Gap<Reach) {DepthSum+=Gap*Weight;Blockers+=Weight;}
        [branch] if(Dual)
        {
            Gap=(Q.z+dot(Gradient,Offset)-ShadowDepth(Extra,Uv+Offset,Reach))*DepthSpan;
            if(Gap>Bias && Gap<Reach) {DepthSum+=Gap*Weight;Blockers+=Weight;}
        }
    }
    if(Blockers<1.e-4) return 1;
    float Radius=max(max(Texel*1.25,Derivatives.z),
                     DepthSum/Blockers*ShadowFilter.x/WorldWidth);
    float Occlusion=0;
    Direction=float2(1,0);
    float InverseFilter=1.0/Samples.y;
    [loop] for(int J=0;J<192;++J)
    {
        if(J>=Samples.y) break;
        float Weight=saturate(Samples.y-J);
        float2 Offset=Direction*(sqrt((J+0.5)*InverseFilter)*Radius);
        Direction=ShadowRotate(Direction);
        Occlusion+=Weight*ShadowFilteredOcclusion(Map,Extra,Dual,Uv+Offset,Q.z+dot(Gradient,Offset),Gradient,Bias,DepthSpan,Texel);
    }
    return 1.0-Occlusion/max(Samples.y,1);
}
float SolarVisibility(float3 Position, float3 Normal)
{
    if(ShadowControl.x<0.5) return 1.0;
    // Normal offset: look the receiver up a little above its own surface, by about a map
    // texel and more at grazing sun. A surface that is in the map itself (two-sided materials
    // draw the sun-facing side too) then never shadows itself into speckled acne.
    float Grazing=1.0+2.0*(1.0-saturate(-dot(Normal,ShadowSunRay.xyz)));
    float3 Far=mul(float4(Position+Normal*(ShadowBias.y*Grazing),1),ShadowFar).xyz;
    float Visibility=1;
    // Derivatives are evaluated uniformly; texture reads are only performed for
    // the selected cascade, except in the narrow cascade crossfade band.
    float3 Near=mul(float4(Position+Normal*(ShadowBias.x*Grazing),1),ShadowNear).xyz;
    float3 NearDerivatives=ShadowDerivatives(Near),FarDerivatives=ShadowDerivatives(Far);
    float Distance=length(Position);
    float Quality=ShadowQuality.y>0.5 ?
        1.0-smoothstep(ShadowQuality.x,ShadowQuality.x*2.0,Distance) : 1.0;
    float2 Samples=lerp(min(ShadowFilter.yz,ShadowQuality.zw),ShadowFilter.yz,Quality);
    Samples=max(Samples,1);
    // ShadowSunRay points away from the sun: a surface facing away from it receives no
    // sunlight, so no sun shadow can fall on it (after the uniform derivatives above).
    [branch] if(dot(Normal,ShadowSunRay.xyz)>=0) return 1.0;
    bool Simple=ShadowExtra.z>0.5;
    if(max(abs(Far.x),abs(Far.y))<0.995 && Far.z>0 && Far.z<1)
    {
        float Extent=max(abs(Near.x),abs(Near.y));
        bool NearValid=Extent<0.98 && Near.z>0 && Near.z<1;
        float Inner=1,Outer=1;
        [branch] if(NearValid)
            Inner=ShadowCompare(ShadowNearMap,ShadowNearLiveMap,ShadowPlanetControl.y>0.5,Near,ShadowRange.z,ShadowBias.x,
                                ShadowDepthSpan.x,ShadowControl.y,NearDerivatives,Samples,Simple);
        [branch] if(!NearValid || Extent>0.80)
            Outer=ShadowCompare(ShadowFarMap,ShadowStaticMap,ShadowExtra.w>0.5,Far,ShadowRange.w,
                                ShadowBias.y,ShadowDepthSpan.y,ShadowExtra.x,FarDerivatives,Samples,Simple);
        if(NearValid) Outer=lerp(Inner,Outer,smoothstep(0.80,0.98,Extent));
        Visibility=lerp(Outer,1.0,smoothstep(ShadowControl.z,ShadowControl.w,Distance));
    }
    [loop] for(int I=0;I<8;++I)
    {
        if(I>=ShadowPlanetControl.x) break;
        float3 ToPlanet=ShadowPlanets[I].xyz-Position;
        float Radius=ShadowPlanets[I].w;
        float SurfaceDistance=length(ToPlanet)-Radius;
        if(SurfaceDistance>=ShadowRange.x) continue;
        float Along=dot(ToPlanet,-ShadowSunRay.xyz);
        if(Along<=0) continue;
        float Perpendicular=sqrt(max(dot(ToPlanet,ToPlanet)-Along*Along,0));
        if(Perpendicular>=Radius) continue;
        float Gap=Along-sqrt(max(Radius*Radius-Perpendicular*Perpendicular,0));
        float Edge=max(0.05,Gap*ShadowFilter.x);
        float Occlusion=(1.0-smoothstep(Radius-Edge,Radius,Perpendicular))*ShadowOcclusion(Gap,0,ShadowRange.x);
        Visibility=min(Visibility,1.0-Occlusion);
    }
    return lerp(1.0,Visibility,ShadowFilter.w);
}

float3 Fresnel(float Cosine, float3 F0)
{
    return F0 + (1.0 - F0) * pow(1.0 - saturate(Cosine), 5.0);
}

float3 SafeNormal(float3 V)
{
    return V * rsqrt(max(dot(V, V), 1.0e-12));
}

float GgxDistribution(float NoH, float A2)
{
    float Denom = NoH * NoH * (A2 - 1.0) + 1.0;
    return A2 / max(3.14159265 * Denom * Denom, 1.0e-5);
}

float4 PSMain(SurfacePixel In) : COLOR0
{
#ifdef SURFACE_LOW_DETAIL
    const bool Cockpit=false,Glass=false;
#else
    bool Cockpit=MaterialStyle.x>0.5,Glass=MaterialStyle.y>0.5;
#endif
    float3 RawNormal=In.Normal;
    if(Glass && dot(RawNormal,RawNormal)<1.e-8)
        RawNormal=cross(ddx(In.ViewPosition),ddy(In.ViewPosition));
    float3 N = SafeNormal(RawNormal);
    float3 V = SafeNormal(-In.ViewPosition);
    if(Glass && dot(N,V)<0) N=-N;
#if defined(SURFACE_LOW_DETAIL) || defined(SURFACE_NO_SHADOW)
    const float SunVisibility=1.0;
#else
    float SunVisibility=SolarVisibility(In.ViewPosition,N);
#endif
    float NoV = max(dot(N, V), 1.0e-4);
    float4 T = Surface.x > 0.5 ? tex2D(DiffuseMap, In.Uv) : 1.0;
    float4 Vertex = Surface.y > 0.5 ? In.Colour : 1.0;
    float4 Base = MaterialDiffuse * Vertex;
    // Standard Dt stages: select texture / select diffuse / modulate / modulate2x.
    float4 Albedo = Base * T;
    if (BaseOps.x < 2.5) Albedo.rgb = T.rgb;
    else if (BaseOps.x < 3.5) Albedo.rgb = Base.rgb;
    else if (BaseOps.x > 4.5) Albedo.rgb *= 2.0;
    if (BaseOps.y < 2.5) Albedo.a = T.a;
    else if (BaseOps.y < 3.5) Albedo.a = Base.a;
    else if (BaseOps.y > 4.5) Albedo.a *= 2.0;

#ifndef SURFACE_LOW_DETAIL
    float3 FinishStyle=SurfaceFinish.w>0.5 ? SurfaceFinish.xyz : float3(1.35,0.9,0.8);
    bool Reflective=(BaseOps.w>=0 && Surface.z>0) || Cockpit || Glass;
    if(Cockpit) FinishStyle*=MaterialStyle.w;
    float PanelGloss=saturate(dot(T.rgb,float3(0.299,0.587,0.114)));
    float FinishMask=lerp(0.35,1.0,PanelGloss);
    float Roughness = Reflective ? clamp(MaterialSpecular.w*lerp(1.12,0.88,PanelGloss),0.24,1.0) : MaterialSpecular.w;
    if(Cockpit) Roughness=clamp(Roughness,0.32,0.65);
    if(Glass) Roughness=0.13;
    float NormalVariance=max(dot(ddx(N),ddx(N)),dot(ddy(N),ddy(N)));
    float A2 = max(pow(Roughness, 4.0)+NormalVariance*0.25, 1.0e-4);
    // Derive the brushing direction from authored UVs. No synthetic bump normals
    // or time-varying noise: the highlight stays attached to each hull panel.
    float3 DpX=ddx(In.ViewPosition),DpY=ddy(In.ViewPosition);
    float2 DuX=ddx(In.Uv),DuY=ddy(In.Uv);
    float3 Tangent=DpX*DuY.y-DpY*DuX.y;
    Tangent-=N*dot(N,Tangent);
    if(dot(Tangent,Tangent)<1.e-12)
        Tangent=cross(abs(N.y)<0.9 ? float3(0,1,0) : float3(1,0,0),N);
    Tangent=SafeNormal(Tangent);
    float3 Bitangent=SafeNormal(cross(N,Tangent));
    float K = (Roughness + 1.0) * (Roughness + 1.0) * 0.125;
#endif
    float3 DiffuseLighting = Albedo.rgb * MaterialAmbient.rgb;
    float3 Highlights = 0.0;
    float SunFacing = 0.0;
    [loop] for (int I = 0; I < 8; ++I)
    {
        if (I >= Surface.w) break;
        SurfaceLight Light = Lights[I];
        bool Directional = Light.PositionType.w > 2.5;
        float3 L;
        float Attenuation = 1.0;
        [branch] if(Directional)
            L=SafeNormal(-Light.DirectionRange.xyz);
        else
        {
            float3 ToLight=Light.PositionType.xyz-In.ViewPosition;
            float Distance=length(ToLight);
            L=ToLight/max(Distance,1.0e-4);
            Attenuation = rcp(max(dot(Light.AttenuationInner.xyz, float3(1.0, Distance, Distance * Distance)), 1.0e-4));
            Attenuation *= Distance < Light.DirectionRange.w ? 1.0 : 0.0;
            if (Light.PositionType.w > 1.5)
            {
                float Cone = saturate((dot(-L, SafeNormal(Light.DirectionRange.xyz)) - Light.SpecularOuter.w) /
                    max(Light.AttenuationInner.w - Light.SpecularOuter.w, 1.0e-4));
                Attenuation *= pow(Cone, max(Light.DiffuseFalloff.w, 1.0e-3));
            }
        }
        float NoL = saturate(dot(N, L));
        if(Directional) SunFacing=max(SunFacing,NoL);
        if(Directional && dot(SafeNormal(Light.DirectionRange.xyz),ShadowSunRay.xyz)>0.98)
            Attenuation *= SunVisibility;
        // Every lobe below is multiplied by NoL * Attenuation. Keep reflected
        // environment/ambient outside this loop; skip only zero-contribution light.
        [branch] if(NoL<=0 || Attenuation<=0) continue;
#ifdef SURFACE_LOW_DETAIL
        DiffuseLighting += Attenuation * NoL * Albedo.rgb * Light.DiffuseFalloff.rgb;
        // Medium-distance finish: one Blinn lobe with fixed integer powers.
        // No GGX, derivatives, tangent basis, coat, shadow taps or extra textures.
        if(BaseOps.w>=0 && Surface.z>0)
        {
            float NoH=saturate(dot(N,SafeNormal(V+L)));
            float H2=NoH*NoH,H4=H2*H2,H8=H4*H4,H16=H8*H8;
            float H32=H16*H16,H64=H32*H32;
            float Gloss=lerp(H16,H64,saturate(1.0-MaterialSpecular.w));
            float Gain=lerp(1.4,0.45,saturate(MaterialSpecular.w));
            Highlights+=Attenuation*NoL*Gloss*Gain*Light.SpecularOuter.rgb;
        }
#else
        float3 H = SafeNormal(V + L);
        float NoH = saturate(dot(N, H));
        float3 F = Fresnel(dot(V, H), MaterialSpecular.rgb);
        float D = GgxDistribution(NoH, A2);
        float G = (NoV / (NoV * (1.0 - K) + K)) * (NoL / (NoL * (1.0 - K) + K));
        float3 Spec = D * G * F / max(4.0 * NoV * NoL, 1.0e-4);
        // Broad finish plus a tighter gloss lobe: hull curvature remains readable
        // when the narrow solar highlight is outside the visible facets.
        float FinishRoughness = max(Roughness, 0.48);
        float FinishK = (FinishRoughness + 1.0) * (FinishRoughness + 1.0) * 0.125;
        float FinishG = (NoV / (NoV * (1.0 - FinishK) + FinishK)) *
                        (NoL / (NoL * (1.0 - FinishK) + FinishK));
        float3 Finish = GgxDistribution(NoH, pow(FinishRoughness, 4.0)) * FinishG *
            Fresnel(dot(V, H), float3(0.10, 0.10, 0.10)) / max(4.0 * NoV * NoL, 1.0e-4);
        DiffuseLighting += Attenuation * NoL * Albedo.rgb * (1.0 - F) * Light.DiffuseFalloff.rgb;
        Highlights += Attenuation * NoL * (Spec * 1.25 + Finish * 0.75) * Light.SpecularOuter.rgb;
        if(Reflective)
        {
            // A smooth top coat supplies the bright moving accent, while an
            // elongated satin lobe makes front-facing flat panels read as metal.
            float CoatRoughness=Glass ? 0.10 : lerp(0.27,0.18,PanelGloss);
            float CoatA2=max(pow(CoatRoughness,4.0)+NormalVariance*0.5,1.e-4);
            float CoatK=(CoatRoughness+1)*(CoatRoughness+1)*0.125;
            float CoatG=(NoV/(NoV*(1-CoatK)+CoatK))*(NoL/(NoL*(1-CoatK)+CoatK));
            float3 Coat=GgxDistribution(NoH,CoatA2)*CoatG*
                Fresnel(dot(V,H),float3(0.065,0.065,0.065))/max(4*NoV*NoL,1.e-4);
            float Ax=sqrt(0.14*0.14+NormalVariance*0.5);
            float Ay=sqrt(0.38*0.38+NormalVariance*0.5);
            float Ht=dot(H,Tangent),Hb=dot(H,Bitangent);
            float Ellipse=Ht*Ht/(Ax*Ax)+Hb*Hb/(Ay*Ay)+NoH*NoH;
            float BrushedD=rcp(max(3.14159265*Ax*Ay*Ellipse*Ellipse,1.e-5));
            float3 MetalTint=lerp(float3(1,1,1),saturate(Albedo.rgb),0.25);
            float3 Brushed=BrushedD*FinishG*Fresnel(dot(V,H),MetalTint*0.12)/max(4*NoV*NoL,1.e-4);
            // A deliberately stylised broad sweep keeps the lit face expressive
            // beyond the tiny mirror angle, especially on old flat hull meshes.
            float SatinRibbon=pow(NoH,12.0)*exp2(-12.0*Ht*Ht);
            float3 Satin=Brushed*1.75+MetalTint*(0.25*SatinRibbon);
            float3 Layered=(Coat*FinishStyle.y+Satin*FinishStyle.z)*FinishMask;
            Highlights+=Attenuation*NoL*Layered*Light.SpecularOuter.rgb;
        }
#endif
    }
    float3 R = reflect(-V, N);
    float4 EnvCoord = mul(float4(R, 1.0), PixelEnvironmentMatrix);
#ifdef SURFACE_ENV_CUBE
    // Native CUBE assets use all three components of the camera-space reflection
    // vector. Retain the material texture transform when it enables COUNT3.
    float3 EnvDirection = BaseOps.z > 0.5 ? EnvCoord.xyz : R;
    float4 Environment = Surface.z>0.0 ? texCUBE(EnvironmentMap, EnvDirection) : 1.0;
#else
    float2 EnvUv = BaseOps.z > 0.5 ? EnvCoord.xy : R.xy;
    if (BaseOps.z > 255.5) EnvUv /= max(abs(EnvCoord.z), 1.0e-4);
    float4 Environment = Surface.z>0.0 ? tex2D(EnvironmentMap, EnvUv) : 1.0;
#endif
    // Restore the authored envmap modulation underneath the modern lighting.
    // Native MODULATE2X maps use mid-grey as neutral, with bright regions making
    // the moving metallic bands that the original material relied on.
    float3 EnvBody = DiffuseLighting * Environment.rgb;
    if (BaseOps.w < 2.5) EnvBody = Environment.rgb;
    else if (BaseOps.w > 6.5) EnvBody = DiffuseLighting + Environment.rgb;
    else if (BaseOps.w > 5.5) EnvBody *= 4.0;
    else if (BaseOps.w > 4.5) EnvBody *= 2.0;
    float3 Colour = lerp(DiffuseLighting, EnvBody, saturate(Surface.z));
#ifdef SURFACE_LOW_DETAIL
    // Bounded highlight addition keeps the authored texture and windows legible.
    float3 HighlightRoom=max(0.94-saturate(Colour),0.015);
    Colour+=HighlightRoom*Highlights/(HighlightRoom+Highlights);
#else
    // A visible reflection across face-on panels as well as grazing edges.
    // This artistic finish is intentionally stronger than a strict dielectric.
    float3 Reflection = lerp(float3(0.18, 0.18, 0.18), float3(0.85, 0.85, 0.85),
                             Fresnel(NoV, MaterialSpecular.rgb));
    // Keep the moving envmap bands, but stop its constant grey floor from filling
    // the unlit side like another ambient light. A small reflection remains there.
    // Shadow dims the reflection in proportion to the direct sunlight (NoL): grazing and
    // unlit sides, where the reflection dominates, show no dark caster silhouettes.
    float ReflectionLighting=lerp(0.15,1.0,sqrt(SunFacing)) *
        lerp(1.0,lerp(0.20,1.0,SunVisibility),SunFacing);
    Colour += Environment.rgb * Reflection * Surface.z * (1.0 - 0.5 * Roughness) * ReflectionLighting;
    // A soft shoulder only on added gloss preserves the authored diffuse texture.
    // Bright source texels and emissive windows are not globally tone-mapped.
    if(BaseOps.w<0.0 && !Cockpit && !Glass) Highlights=0.0;
    float GlassFresnel=0;
    [branch] if(Glass)
    {
        GlassFresnel=0.04+0.96*pow(1.0-saturate(NoV),5.0);
        // Authored envmaps are retained; materials without one get a restrained
        // smooth reflection band. No scene copy/refraction or extra render pass.
        float Band=pow(saturate(1.0-abs(R.y*0.75+0.15)),6.0);
        float3 GlassEnv=Surface.z>0 ? Environment.rgb :
            lerp(float3(0.05,0.07,0.10),float3(0.32,0.38,0.45),Band);
        Colour=Albedo.rgb*0.10+GlassEnv*(0.08+0.75*GlassFresnel)*MaterialStyle.z;
        Highlights*=MaterialStyle.z*1.8;
    }
    Highlights*=FinishStyle.x;
    float3 HighlightRoom=max(0.94-saturate(Colour),0.015);
    Colour += HighlightRoom*(1.0-exp(-Highlights/HighlightRoom));
    // Cheap artistic plasma accent. No capsule, normalisation, pow/exp,
    // texture fetches or shadow calculations. CPU culls groups per receiver.
    [branch] if(WeaponGlintControl.x>0 && dot(In.ViewPosition,In.ViewPosition)<=WeaponGlintControl.w)
    {
        float3 WeaponGlow=0;
        [loop] for(int W=0;W<8;++W)
        {
            if(W>=WeaponGlintControl.x) break;
            float3 Delta=WeaponGlints[W].Position.xyz-In.ViewPosition;
            float Weight=saturate(1.0-dot(Delta,Delta)*WeaponGlintControl.z);
            float Facing=saturate(dot(N,Delta)*0.25);
            WeaponGlow+=WeaponGlints[W].Colour.rgb*(Weight*Weight*Facing);
        }
        WeaponGlow*=WeaponGlintControl.y;
        float Peak=max(WeaponGlow.r,max(WeaponGlow.g,WeaponGlow.b));
        Colour+=WeaponGlow/(1.0+Peak); // bounded, hue-preserving saturation
    }
#endif
    Colour += MaterialEmission.rgb;
    float Alpha=Albedo.a*Environment.a;
#ifndef SURFACE_LOW_DETAIL
    [branch] if(Glass)
    {
        float Shine=max(Highlights.r,max(Highlights.g,Highlights.b));
        Alpha=clamp(Albedo.a*0.22+GlassFresnel*0.55+saturate(Shine)*0.12,0.04,0.78);
    }
#endif
    float4 Result = float4(Colour, Alpha);
    if (Fog.w > 0.5)
    {
        float Z = FogColour.w > 0.5 ? length(In.ViewPosition) : abs(In.ViewPosition.z);
        float Keep = Fog.w > 2.5 ? saturate((Fog.y - Z) / max(Fog.y - Fog.x, 1.0e-4)) :
            (Fog.w > 1.5 ? exp(-pow(Z * Fog.z, 2.0)) : exp(-Z * Fog.z));
        Result.rgb = lerp(FogColour.rgb, Result.rgb, Keep);
    }
    return Result;
}
