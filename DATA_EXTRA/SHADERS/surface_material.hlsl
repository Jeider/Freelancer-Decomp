// RP9 reflective surface profile. Authored diffuse/envmap/specular/emissive and fog
// remain material inputs. The explicitly selected ice profile adds authored packed layers.
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
#if defined(SURFACE_NOMAD) || defined(SURFACE_ROCK)
    float4 DetailUv : TEXCOORD3;
#endif
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
#ifdef SURFACE_NOMAD
    Out.DetailUv=float4(VertexModes.w>1.5?In.Uv1:In.Uv0,VertexModes.w>2.5?In.Uv2:In.Uv0);
#endif
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
float4 ShadowPlanetControl : register(c62); // x planet count, y near moving-caster map valid, z eclipse reach, w eclipse sun angle
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
float4 CockpitRelief : register(c106); // x: cockpit panel relief strength (0 = off; only set in the cockpit pass)
// x far-map texel size; y shadow reach of casters stored with a negative depth (NPC ships);
// z simple receiver (one bilinear comparison instead of PCSS); w the far static map is valid.
float4 ShadowExtra : register(c95);
// Explicit opaque crystal profile: enabled, parallax depth, frost coverage, back-light gain.
float4 IceStyle : register(c96);
sampler2D IceLayers : register(s13); // RGB independent fractures at three depths; A frost
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
        // Static receivers use the existing detailed maps only close to the
        // camera (120..150m at the default near radius). This preserves the
        // player's silhouette on a nearby station without upgrading distant
        // station pixels or NPC hulls to the expensive player filter budget.
        float LocalFade=ShadowControl.x>2.5 ? smoothstep(ShadowRange.z*0.4,ShadowRange.z*0.5,Distance) : 0;
        float NearFade=max(smoothstep(0.80,0.98,Extent),LocalFade);
        bool NearValid=ShadowControl.x>1.5 && NearFade<1 && Near.z>0 && Near.z<1;
        float Inner=1,Outer=1;
        [branch] if(NearValid)
            Inner=ShadowCompare(ShadowNearMap,ShadowNearLiveMap,ShadowPlanetControl.y>0.5,Near,ShadowRange.z,ShadowBias.x,
                                ShadowDepthSpan.x,ShadowControl.y,NearDerivatives,Samples,Simple);
        [branch] if(!NearValid || NearFade>0)
            Outer=ShadowCompare(ShadowFarMap,ShadowStaticMap,ShadowExtra.w>0.5,Far,ShadowRange.w,
                                ShadowBias.y,ShadowDepthSpan.y,ShadowExtra.x,FarDerivatives,Samples,Simple);
        if(NearValid) Outer=lerp(Inner,Outer,NearFade);
        Visibility=lerp(Outer,1.0,smoothstep(ShadowControl.z,ShadowControl.w,Distance));
    }
    [loop] for(int I=0;I<8;++I)
    {
        if(I>=ShadowPlanetControl.x) break;
        float3 ToPlanet=ShadowPlanets[I].xyz-Position;
        // A negative radius is the planet_eclipses caster: it reaches ShadowPlanetControl.z metres
        // with a penumbra from the sun's angular radius (ShadowPlanetControl.w).
        bool Eclipse=ShadowPlanets[I].w<0;
        float Radius=abs(ShadowPlanets[I].w);
        float Reach=Eclipse ? ShadowPlanetControl.z : ShadowRange.x;
        float SurfaceDistance=length(ToPlanet)-Radius;
        if(SurfaceDistance>=Reach) continue;
        float Along=dot(ToPlanet,-ShadowSunRay.xyz);
        if(Along<=0) continue;
        float Perpendicular=sqrt(max(dot(ToPlanet,ToPlanet)-Along*Along,0));
        float Edge=Eclipse ? max(0.05,Along*ShadowPlanetControl.w) : 0.0;
        if(Perpendicular>=Radius+Edge) continue;
        float Gap=Along-sqrt(max(Radius*Radius-min(Perpendicular*Perpendicular,Radius*Radius),0));
        if(!Eclipse) Edge=max(0.05,Gap*ShadowFilter.x);
        float Occlusion=Eclipse ?
            (1.0-smoothstep(Radius-Edge,Radius+Edge,Perpendicular))*(Gap<Reach ? 1.0 : 0.0) :
            (1.0-smoothstep(Radius-Edge,Radius,Perpendicular))*ShadowOcclusion(Gap,0,ShadowRange.x);
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

#ifdef SURFACE_NOMAD
sampler2D NomadDetail : register(s1);
float4 DetailModes : register(c97); // colour operation, UV set, transform, present
row_major float4x4 DetailMatrix : register(c98);

// Uses the identical vertex transform as the colour pass, with no texture work.
float4 PSNomadDepth(SurfacePixel In) : COLOR0 { return 0; }

float NomadHeight(float2 uv,float2 gx,float2 gy)
{
    // The authored surface supplies the principal cavities; the periodic atlas
    // adds raised connective folds without replacing the texture's structure.
    float stone=dot(tex2Dgrad(DiffuseMap,uv,gx,gy).rgb,float3(.299,.587,.114));
    return saturate(stone*.8+tex2Dgrad(IceLayers,uv,gx,gy).b*.35);
}

float4 PSNomad(SurfacePixel In)
{
    const bool Skin=IceStyle.x>2.5;
    float3 N=SafeNormal(In.Normal),V=SafeNormal(-In.ViewPosition);
    float3 dx=ddx(In.ViewPosition),dy=ddy(In.ViewPosition);
    float2 ux=ddx(In.Uv),uy=ddy(In.Uv);
    float determinant=ux.x*uy.y-ux.y*uy.x;
    float handed=determinant<0?-1:1;
    float3 tangent=(dx*uy.y-dy*ux.y)*handed;
    tangent-=N*dot(N,tangent);
    float valid=(abs(determinant)>1.e-10 && dot(tangent,tangent)>1.e-12)?1:0;
    if(valid<.5) tangent=cross(abs(N.y)<.9?float3(0,1,0):float3(1,0,0),N);
    tangent=SafeNormal(tangent);
    float3 bitangent=SafeNormal(cross(N,tangent))*handed;
    float2 uv=In.Uv,originalUv=uv;
    float2 gradX=ux,gradY=uy;
    float2 detailUv=DetailModes.y>1.5?In.DetailUv.zw:(DetailModes.y>.5?In.DetailUv.xy:originalUv);
    if(DetailModes.z>.5) detailUv=mul(float4(detailUv,0,1),DetailMatrix).xy;
    float2 detailDx=ddx(detailUv),detailDy=ddy(detailUv);
    float4 detailTexel=1;
    if(DetailModes.w>.5) detailTexel=tex2Dgrad(NomadDetail,detailUv,detailDx,detailDy);
    // Only the authored ET/additive layer on the interior drives living tissue.
    // Bt detail, exterior stone, Dyson panels and alpha silhouettes stay stable.
    const bool Living=Skin && DetailModes.w>.5 && DetailModes.x>6.5 && DetailModes.x<7.5;
    // Tunnel skin02 ET is deliberately dim (90th-percentile luminance ~0.037).
    // Calibrate the envelope to that authored range, not a white emissive mask.
    float tissue=Living?smoothstep(.006,.065,dot(detailTexel.rgb,float3(.299,.587,.114))):0;
    float phase=frac(IceStyle.w/16)*6.283185307+originalUv.y*12.566370614+originalUv.x*6.283185307;
    float contraction=sin(phase),crest=pow(saturate(.5+.5*sin(phase*2)),3);
    float2 motion=float2(sin(phase),cos(phase))*.0045*tissue*valid;
    uv+=motion;
    float breathing=1+.20*tissue*contraction;
#ifndef SURFACE_NOMAD_LIGHT
    // Bounded parallax occlusion in the original UV chart, with explicit gradients.
    // Silhouette/collision geometry is untouched. No discard or shader-depth output.
    float relief=lerp(.035,.075,Skin)*IceStyle.y*valid*breathing;
    float2 shift=float2(dot(V,tangent),dot(V,bitangent))/max(abs(dot(V,N)),.3)*relief;
    float2 stepUv=shift/12;
    float layer=0,height=1-NomadHeight(uv,gradX,gradY);
    [loop] for(int k=0;k<12;++k) {
        if(layer>=height) break;
        uv-=stepUv;layer+=1.0/12;
        height=1-NomadHeight(uv,gradX,gradY);
    }
    float2 previous=uv+stepUv;
    float before=1-NomadHeight(previous,gradX,gradY)-(layer-1.0/12);
    float after=height-layer;
    uv=lerp(uv,previous,saturate(-after/max(before-after,.0001)));
#endif
    float4 reliefMap=tex2Dgrad(IceLayers,uv,gradX,gradY);
    const float2 texel=float2(.002,0);
    float2 authoredSlope=float2(
        dot(tex2Dgrad(DiffuseMap,uv-texel,ux,uy).rgb-tex2Dgrad(DiffuseMap,uv+texel,ux,uy).rgb,float3(.299,.587,.114)),
        dot(tex2Dgrad(DiffuseMap,uv-texel.yx,ux,uy).rgb-tex2Dgrad(DiffuseMap,uv+texel.yx,ux,uy).rgb,float3(.299,.587,.114)));
    float2 slope=((reliefMap.rg*2-1)*lerp(.28,.7,Skin)+authoredSlope*3.5)*IceStyle.y*valid*breathing;
    float3 mapped=SafeNormal(float3(slope,sqrt(max(.08,1-dot(slope,slope)))));
    N=SafeNormal(tangent*mapped.x+bitangent*mapped.y+N*mapped.z);
    float4 texelColour=tex2Dgrad(DiffuseMap,uv,ux,uy);
    if(Living) texelColour.a=tex2Dgrad(DiffuseMap,originalUv,ux,uy).a;
    float4 base=MaterialDiffuse*(Surface.y>.5?In.Colour:1);
    float4 albedo=texelColour*base;
    if(BaseOps.x<2.5) albedo.rgb=texelColour.rgb;
    else if(BaseOps.x<3.5) albedo.rgb=base.rgb;
    else if(BaseOps.x>4.5) albedo.rgb*=2;
    if(BaseOps.y<2.5) albedo.a=texelColour.a;
    else if(BaseOps.y<3.5) albedo.a=base.a;
    else if(BaseOps.y>4.5) albedo.a*=2;
    float3 authoredEmission=0;
    // ET keeps its authored colour and never goes dark. Move RGB gently with the
    // tissue while retaining the original alpha: no breathing holes or mask crawl.
    if(DetailModes.w>.5) {
        float3 detail=detailTexel.rgb;
        albedo.a*=detailTexel.a;
        if(DetailModes.x<6.5) albedo.rgb*=detail*(DetailModes.x<4.5?1:(DetailModes.x<5.5?2:4));
        else if(DetailModes.x<7.5) {
            if(Living) detail=tex2Dgrad(NomadDetail,detailUv+motion,detailDx,detailDy).rgb;
            authoredEmission=detail*(Living?(0.90+.16*(.5+.5*contraction)+.14*crest):1);
        }
        else albedo.rgb=saturate(albedo.rgb+detail-.5);
    }
    float cavities=lerp(.65,1,smoothstep(.12,.6,reliefMap.b));
    float rough=Skin?lerp(.15,.32,reliefMap.b):lerp(.38,.78,reliefMap.b);
    float variance=max(dot(ddx(N),ddx(N)),dot(ddy(N),ddy(N)));
    float a2=max(pow(rough,4)+variance*.2,.0005);
    float NoV=max(saturate(dot(N,V)),.04);
    float3 colour=albedo.rgb*MaterialAmbient.rgb*cavities,shine=0;
#ifdef SURFACE_NO_SHADOW
    const float visibility=1;
#else
    float visibility=SolarVisibility(In.ViewPosition,SafeNormal(In.Normal));
#endif
    [loop] for(int i=0;i<8;++i) {
        if(i>=Surface.w) break;
        SurfaceLight light=Lights[i];bool sun=light.PositionType.w>2.5;
        float3 delta=light.PositionType.xyz-In.ViewPosition;
        float distance=length(delta);
        float3 L=sun?SafeNormal(-light.DirectionRange.xyz):delta/max(distance,.0001);
        float attenuation=sun?1:rcp(max(dot(light.AttenuationInner.xyz,float3(1,distance,distance*distance)),.0001));
        if(!sun){attenuation*=distance<light.DirectionRange.w?1:0;
            if(light.PositionType.w>1.5) attenuation*=pow(saturate((dot(-L,SafeNormal(light.DirectionRange.xyz))-light.SpecularOuter.w)/max(light.AttenuationInner.w-light.SpecularOuter.w,.0001)),max(light.DiffuseFalloff.w,.000001));}
        if(sun && dot(SafeNormal(light.DirectionRange.xyz),ShadowSunRay.xyz)>.98) attenuation*=visibility;
        float nl=saturate(dot(N,L)),wrap=Skin?saturate((dot(N,L)+.16)/1.16):nl;
        colour+=albedo.rgb*light.DiffuseFalloff.rgb*wrap*attenuation*cavities;
        float3 H=SafeNormal(L+V);
        float nh=saturate(dot(N,H)),vh=saturate(dot(V,H));
        float spec=GgxDistribution(nh,a2)*nl/(4*max(nl,.12)*NoV+.15);
        float3 fresnel=Fresnel(vh,Skin?.055:.035);
        float coat=Skin?pow(nh,96)*1.1:pow(nh,24)*.12;
        shine+=light.SpecularOuter.rgb*(spec*fresnel+coat)*attenuation;
    }
    float3 room=max(.98-saturate(colour),.025);
    colour+=room*(1-exp(-shine/room));
    // Sparse coloured vascular accent only indoors; rock/bone exterior stays solid.
    float pulse=.75+.25*sin(IceStyle.w*.39269908+originalUv.x*9+originalUv.y*6);
    if(Skin) colour+=float3(.10,.32,.22)*reliefMap.a*IceStyle.z*pulse;
    colour+=authoredEmission+MaterialEmission.rgb;
    if(Fog.w>.5){float z=FogColour.w>.5?length(In.ViewPosition):abs(In.ViewPosition.z);
        float keep=Fog.w>2.5?saturate((Fog.y-z)/max(Fog.y-Fog.x,.0001)):(Fog.w>1.5?exp(-pow(z*Fog.z,2)):exp(-z*Fog.z));
        colour=lerp(FogColour.rgb,colour,keep);}
    return float4(colour,albedo.a);
}
#endif

#ifdef SURFACE_SHIP_NORMALS
sampler2D ShipNormalMap : register(s13); // DXT5nm: X in alpha, Y in green
float4 ShipNormalStyle : register(c97); // strength, fade start/end, max tangent slope
float3 ShipReliefNormal(SurfacePixel In, float3 N)
{
    float3 Dx=ddx(In.ViewPosition),Dy=ddy(In.ViewPosition);
    float2 Ux=ddx(In.Uv),Uy=ddy(In.Uv);
    float Fade=1.0-smoothstep(ShipNormalStyle.y,ShipNormalStyle.z,length(In.ViewPosition));
    // A large station can straddle the range boundary. Distant pixels skip the
    // normal texture and tangent construction. Gradients stay outside the branch.
    [branch] if(Fade<=0.0 || ShipNormalStyle.x<=0.0) return N;
    float Det=Ux.x*Uy.y-Ux.y*Uy.x;
    float3 T=Dx*Uy.y-Dy*Ux.y;
    T*=Det<0 ? -1.0 : 1.0;
    T-=N*dot(T,N);
    if(abs(Det)<1.e-12 || dot(T,T)<1.e-12) return N;
    T=normalize(T);
    float3 B=normalize(cross(N,T))*(Det<0 ? -1.0 : 1.0);
    float2 XY=tex2Dgrad(ShipNormalMap,In.Uv,Ux,Uy).ag*2.0-1.0;
    float Z=sqrt(max(1.0-dot(XY,XY),0.0625));
    float2 Slope=XY/Z*ShipNormalStyle.x*Fade;
    Slope*=min(1.0,ShipNormalStyle.w/max(length(Slope),0.0001));
    return normalize(N+T*Slope.x+B*Slope.y);
}
#endif

#ifdef SURFACE_ROCK
// Asteroids and debris. Relief that needs no authored normal map: the texture's own light/dark
// structure is read as height (dark = recess), and a shared tiling rock map adds lumps, chips
// and grit at two scales. The strength is deliberately high; slopes are capped, not softened.
sampler2D RockDetail : register(s13); // RG slope, B height, A cavity (linear)
float4 RockStyle : register(c102);  // detail strength, fade start, fade end, tiling
float4 RockStyle2 : register(c103); // macro strength, scrap (1) / rock (0), radius in metres, finish gain
float4 RockStyle3 : register(c104); // deepest parallax shift in metres (0 = none)
float4 RockLod : register(c105); // quality limits in metres: full, no macro relief, large lumps only, simplest (RockStyle.y: out)
// The material's own stage 1 (an asteroid's detail map: MODULATE2X over the base): the same
// registers the nomad shader reads, c97 mode and c98..101 the texture transform, s1 the texture.
sampler2D NomadDetail : register(s1);
float4 DetailModes : register(c97); // colour operation, UV set, transform, present
row_major float4x4 DetailMatrix : register(c98);
// Applies stage 1 to the albedo. Ux/Uy: UV derivatives of the unshifted chart; Uv: the parallax-shifted one.
float4 RockApplyDetail(SurfacePixel In,float4 Albedo,float2 Uv,float2 Ux,float2 Uy,float4 DDx,float4 DDy)
{
    [branch] if(DetailModes.w<=0.5) return Albedo;
    float2 DUv=Uv,Gx=Ux,Gy=Uy;
    if(DetailModes.y>1.5) {DUv=In.DetailUv.zw;Gx=DDx.zw;Gy=DDy.zw;}
    else if(DetailModes.y>0.5) {DUv=In.DetailUv.xy;Gx=DDx.xy;Gy=DDy.xy;}
    if(DetailModes.z>0.5)
    {
        DUv=mul(float4(DUv,0,1),DetailMatrix).xy;
        Gx=mul(float4(Gx,0,0),DetailMatrix).xy;
        Gy=mul(float4(Gy,0,0),DetailMatrix).xy;
    }
    float4 Detail=tex2Dgrad(NomadDetail,DUv,Gx,Gy);
    float Op=DetailModes.x;
    if(Op<6.5) Albedo.rgb*=Detail.rgb*(Op<4.5 ? 1.0 : (Op<5.5 ? 2.0 : 4.0));
    else if(Op<7.5) Albedo.rgb+=Detail.rgb;
    else Albedo.rgb=saturate(Albedo.rgb+Detail.rgb-0.5);
    Albedo.a*=Detail.a;
    return Albedo;
}
static const float3 RockLuma=float3(0.299,0.587,0.114);
// Height of the rock at a UV: 1 = the crest, 0 = the floor of a recess. Dark texture and the detail
// map's low parts are deep; a negative macro strength (rock_pits) turns it inside out.
float RockHeightAt(float2 Uv,float2 Gx,float2 Gy)
{
    float L=dot(tex2Dgrad(DiffuseMap,Uv,Gx,Gy).rgb,RockLuma);
    float D1=tex2Dgrad(RockDetail,Uv*RockStyle.w,Gx*RockStyle.w,Gy*RockStyle.w).b;
    float D2=tex2Dgrad(RockDetail,Uv*(RockStyle.w*3.7)+float2(0.31,0.17),Gx*(RockStyle.w*3.7),Gy*(RockStyle.w*3.7)).b;
    float H=saturate(L*0.5+D1*0.35+D2*0.15);
    return RockStyle2.x<0.0 ? 1.0-H : H;
}

// Parallax occlusion: the surface is read where the eye ray meets the height field, so recesses
// have depth and crests overlap the ground behind them, in the object's own UV chart. Bounded
// steps, explicit gradients, no discard and no depth output; the silhouette is untouched.
float2 RockParallax(SurfacePixel In,float3 N,float3 V)
{
    float Dist=length(In.ViewPosition);
    float3 Dx=ddx(In.ViewPosition),Dy=ddy(In.ViewPosition);
    float2 Ux=ddx(In.Uv),Uy=ddy(In.Uv);
    float Det=Ux.x*Uy.y-Ux.y*Uy.x;
    float Sign=Det<0 ? -1.0 : 1.0;
    float3 Tu=(Dx*Uy.y-Dy*Ux.y)*Sign;
    float3 Tv=(Dy*Ux.x-Dx*Uy.x)*Sign;
    float InvDet=1.0/max(abs(Det),1.e-30);
    float MetresPerUv=max(min(length(Tu),length(Tv))*InvDet,1.e-4);
    float3 T=Tu-N*dot(Tu,N);
    float Near=1.0-smoothstep(RockStyle.y*0.35,RockStyle.y*1.1,Dist);
    [branch] if(Near<=0.02 || abs(Det)<1.e-30 || dot(T,T)<1.e-4*dot(Tu,Tu) || RockStyle.x==0.0 || RockStyle3.x<=0.0) return In.Uv;
    T=normalize(T);
    float3 B=normalize(cross(N,T))*Sign;
    // Depth in metres, from the object's size, as far as the UV chart can show it.
    // Without an object radius (a rock texture on a station) the UV chart's own size stands in.
    // Real relief is a few metres whatever the rock's size: a boulder's pits, not a moon's mountains.
    float Size=RockStyle2.z>0.5 ? RockStyle2.z : MetresPerUv*0.5;
    float DepthMetres=min(abs(RockStyle2.x)*Size*0.05,RockStyle3.x)*lerp(1.0,1.3,RockStyle2.y);
    // The shift is a vector in the surface plane, in metres, turned into UV through the chart's own
    // axes (Pu, Pv: metres per UV unit along each), so a stretched chart cannot blow it up.
    float3 Pu=Tu*InvDet,Pv=Tv*InvDet;
    float Guu=dot(Pu,Pu),Gvv=dot(Pv,Pv),Guv=dot(Pu,Pv);
    float GramDet=max(Guu*Gvv-Guv*Guv,1.e-20);
    // Grazing angles stretch the shift into streaks: the divisor stays well away from zero.
    float3 Eye=(V-N*dot(V,N))/max(dot(V,N),0.45);
    float2 Rhs=float2(dot(Pu,Eye),dot(Pv,Eye));
    float2 Shift=float2(Gvv*Rhs.x-Guv*Rhs.y,Guu*Rhs.y-Guv*Rhs.x)/GramDet*(DepthMetres*Near);
    // Never more than a few percent of the chart, whatever the mesh.
    Shift*=min(1.0,0.03/max(max(abs(Shift.x),abs(Shift.y)),1.e-6));
    const int Steps=16;
    float2 StepUv=Shift/Steps;
    float Layer=0.0,Depth=1.0-RockHeightAt(In.Uv,Ux,Uy);
    float2 Uv=In.Uv;
    [loop] for(int K=0;K<Steps;++K)
    {
        if(Layer>=Depth) break;
        Uv-=StepUv;Layer+=1.0/Steps;
        Depth=1.0-RockHeightAt(Uv,Ux,Uy);
    }
    float2 Prev=Uv+StepUv;
    float Before=1.0-RockHeightAt(Prev,Ux,Uy)-(Layer-1.0/Steps);
    float After=Depth-Layer;
    return lerp(Uv,Prev,saturate(-After/max(Before-After,0.0001)));
}

// Ux, Uy: the UV derivatives of the unshifted coordinates (the parallax moves In.Uv per pixel).
float3 RockReliefNormal(SurfacePixel In,float3 N,float4 Texel,float2 Ux,float2 Uy,out float Cavity)
{
    Cavity=1;
    float Distance=length(In.ViewPosition);
    float Fade=1.0-smoothstep(RockStyle.y,RockStyle.z,Distance);
    float3 Dx=ddx(In.ViewPosition),Dy=ddy(In.ViewPosition);
    // Gradients are taken outside the branch; samples inside it use explicit ones.
    // A negative strength (and macro strength) turns the relief inside out: pits instead of ridges.
    [branch] if(Fade<=0.0 || RockStyle.x==0.0) return N;
    float Det=Ux.x*Uy.y-Ux.y*Uy.x;
    float Sign=Det<0 ? -1.0 : 1.0;
    float3 Tu=(Dx*Uy.y-Dy*Ux.y)*Sign;      // world metres per unit of U (before the divide below)
    float3 Tv=(Dy*Ux.x-Dx*Uy.x)*Sign;
    // Up close the derivative frame is tiny (centimetres per pixel, UV in millionths), so these limits are
    // relative: an absolute 1e-12 threw the whole relief away near the surface.
    float InvDet=1.0/max(abs(Det),1.e-30);
    float LenU=max(length(Tu)*InvDet,1.e-4),LenV=max(length(Tv)*InvDet,1.e-4);
    float3 T=Tu-N*dot(Tu,N);
    if(abs(Det)<1.e-30 || dot(T,T)<1.e-4*dot(Tu,Tu)) return N;
    T=normalize(T);
    float3 B=normalize(cross(N,T))*Sign;
    // Quality by distance (RockLod, metres, scaled up for big rocks). The look up close is the one the
    // second tier used to have (one scale of detail plus the texture's own relief; the two-scale first tier
    // is gone); past rock_lod_macro the texture's relief stops, past rock_lod_coarse only large lumps
    // remain, then the simplest normals out to the far limit, then nothing. Every tier crossfades into the
    // next, so no line shows where they meet. (RockLod.x is kept for the config key; it changes nothing.)
    float wCoarse=smoothstep(RockLod.z*0.8,RockLod.z*1.2,Distance)*(1.0-smoothstep(RockLod.w*0.8,RockLod.w*1.2,Distance));
    float wFar=smoothstep(RockLod.w*0.8,RockLod.w*1.2,Distance);
    float wMid=saturate(1.0-wCoarse-wFar);
    float wMacro=1.0-smoothstep(RockLod.y*0.8,RockLod.y*1.2,Distance);
    float2 Slope=0;
    float CavityMap=0;
    [branch] if(wMid>0.002)
    {
        [branch] if(RockStyle2.y>0.5)
        {
            // Scrap: the original first tier, a fine grain at two scales: an ordinary, slightly coarse
            // surface, not the big crumbly lumps (the second scale turns so tiles do not line up).
            float2 Uv1=In.Uv*RockStyle.w,Uv2=In.Uv*(RockStyle.w*3.7)+float2(0.31,0.17);
            float4 D1=tex2Dgrad(RockDetail,Uv1,Ux*RockStyle.w,Uy*RockStyle.w);
            float4 D2=tex2Dgrad(RockDetail,Uv2,Ux*RockStyle.w*3.7,Uy*RockStyle.w*3.7);
            Slope+=wMid*((D1.rg*2.0-1.0)*RockStyle.x+(D2.rg*2.0-1.0)*(0.35*RockStyle.x));
            CavityMap+=wMid*D1.a;
        }
        else
        {
            float Scale=RockStyle.w*0.35;
            float4 D=tex2Dgrad(RockDetail,In.Uv*Scale+float2(0.57,0.11),Ux*Scale,Uy*Scale);
            Slope+=wMid*(D.rg*2.0-1.0)*(0.9*RockStyle.x);
            CavityMap+=wMid*D.a;
        }
    }
    [branch] if(wCoarse>0.002)
    {
        float Scale=RockStyle.w*0.08;
        float4 D=tex2Dgrad(RockDetail,In.Uv*Scale+float2(0.23,0.71),Ux*Scale,Uy*Scale);
        Slope+=wCoarse*(D.rg*2.0-1.0)*(0.8*RockStyle.x);
        CavityMap+=wCoarse*D.a;
    }
    // The last tier, out to the far limit: the simplest normals, one sample of the very large lumps.
    [branch] if(wFar>0.002)
    {
        float Scale=RockStyle.w*0.025;
        float4 D=tex2Dgrad(RockDetail,In.Uv*Scale+float2(0.83,0.37),Ux*Scale,Uy*Scale);
        Slope+=wFar*(D.rg*2.0-1.0)*(0.7*RockStyle.x);
        CavityMap+=wFar*D.a;
    }
    float L0=dot(Texel.rgb,RockLuma);
    // Macro relief from the authored texture: the slope of its luminance over the surface, in the
    // texture's own contrast per texel (one step E of the UV chart), the same on a boulder and on a
    // mountain-sized rock. Per axis, with no correction for how the chart is stretched: a squeezed axis
    // (a steep face) must not be amplified into noise. Only near: it needs two more reads.
    float2 Macro=0;
    [branch] if(wMacro>0.002)
    {
        float E=1.0/384.0;
        float Lu=dot(tex2Dgrad(DiffuseMap,In.Uv+float2(E,0),Ux,Uy).rgb,RockLuma)-L0;
        float Lv=dot(tex2Dgrad(DiffuseMap,In.Uv+float2(0,E),Ux,Uy).rgb,RockLuma)-L0;
        Macro=float2(Lu,Lv)*(3.0*RockStyle2.x)*wMacro;
        Macro*=min(1.0,1.4/max(length(Macro),1.e-4));
    }
    float Aniso=min(LenU,LenV)/max(max(LenU,LenV),1.e-4);
    // A light safety net only: a chart squeezed below about a tenth of its other axis fades the relief.
    float Guard=smoothstep(0.03,0.15,Aniso);
    Slope+=Macro;
    Slope*=Fade*Guard;
    // Up to ~67 degrees: steep and readable, not a wall of noise.
    Slope*=min(1.0,2.4/max(length(Slope),1.e-4));
    // Crevices take less light: the map's cavity channel and the texture's own dark spots.
    Cavity=lerp(1.0,lerp(0.50,1.0,CavityMap)*lerp(0.72,1.0,saturate(L0*1.8)),Fade*Guard*(1.0-0.6*wCoarse-0.9*wFar));
    return normalize(N-(T*Slope.x+B*Slope.y));
}
#endif

// Cockpit panel relief: the texture's own dark seams read as grooves (no map and no tangent channel; the
// derivative frame of the UV chart). Dx, Dy and Ux, Uy are taken by the caller outside any branch.
float3 CockpitReliefNormal(SurfacePixel In,float3 N,float4 Texel,float3 Dx,float3 Dy,float2 Ux,float2 Uy)
{
    float Det=Ux.x*Uy.y-Ux.y*Uy.x;
    float Sign=Det<0 ? -1.0 : 1.0;
    float3 Tu=(Dx*Uy.y-Dy*Ux.y)*Sign;
    float3 T=Tu-N*dot(Tu,N);
    if(abs(Det)<1.e-30 || dot(T,T)<1.e-4*dot(Tu,Tu)) return N;
    T=normalize(T);
    float3 B=normalize(cross(N,T))*Sign;
    const float3 Luma=float3(0.299,0.587,0.114);
    float L0=dot(Texel.rgb,Luma);
    float E=1.0/512.0;
    float Lu=dot(tex2Dgrad(DiffuseMap,In.Uv+float2(E,0),Ux,Uy).rgb,Luma)-L0;
    float Lv=dot(tex2Dgrad(DiffuseMap,In.Uv+float2(0,E),Ux,Uy).rgb,Luma)-L0;
    float2 Slope=float2(Lu,Lv)*(8.0*CockpitRelief.x);
    Slope*=min(1.0,1.2/max(length(Slope),1.e-4));
    return normalize(N-(T*Slope.x+B*Slope.y));
}

float4 PSMain(SurfacePixel In) : COLOR0
{
#ifdef SURFACE_NOMAD
    return PSNomad(In);
#else
#if defined(SURFACE_GREENHOUSE)
    const bool Cockpit=false,Glass=true,Ice=false,Greenhouse=true;
#elif defined(SURFACE_LOW_DETAIL) || defined(SURFACE_SHIP_NORMALS) || defined(SURFACE_ROCK)
    const bool Cockpit=false,Glass=false,Ice=false,Greenhouse=false;
#else
    bool Cockpit=MaterialStyle.x>0.5,Glass=MaterialStyle.y>0.5;
    const bool Greenhouse=false;
    bool Ice=IceStyle.x>0.5;
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
#ifdef SURFACE_SHIP_NORMALS
    N=ShipReliefNormal(In,N);
#endif
#ifdef SURFACE_ROCK
    // Everything below, texture and relief alike, is read at the parallax-shifted UV.
    float2 RockUx=ddx(In.Uv),RockUy=ddy(In.Uv);
    float4 RockDDx=ddx(In.DetailUv),RockDDy=ddy(In.DetailUv);
    In.Uv=RockParallax(In,N,V);
#endif
    float NoV = max(dot(N, V), 1.0e-4);
#ifdef SURFACE_ROCK
    float4 T = Surface.x > 0.5 ? tex2Dgrad(DiffuseMap, In.Uv, RockUx, RockUy) : 1.0;
#else
    float4 T = Surface.x > 0.5 ? tex2D(DiffuseMap, In.Uv) : 1.0;
#endif
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
#ifdef SURFACE_ROCK
    {
        // Shadow visibility above used the geometric normal; only shading follows the relief.
        float RockCavity;
        // The authored detail layer first (it is part of the colour), then the relief and cavities.
        Albedo=RockApplyDetail(In,Albedo,In.Uv,RockUx,RockUy,RockDDx,RockDDy);
        N=RockReliefNormal(In,N,T,RockUx,RockUy,RockCavity);
        NoV=max(dot(N,V),1.0e-4);
        Albedo.rgb*=RockCavity;
    }
#endif
    {
        // The cockpit's panels get relief too, a little stronger than the fighter hull (cockpit_relief).
        // Gradients are taken here, outside the branch; glass and lit instruments are left alone.
        float3 CpDx=ddx(In.ViewPosition),CpDy=ddy(In.ViewPosition);
        float2 CpUx=ddx(In.Uv),CpUy=ddy(In.Uv);
        [branch] if(Cockpit && CockpitRelief.x>0.0 && dot(MaterialEmission.rgb,float3(1,1,1))<0.05)
        {
            N=CockpitReliefNormal(In,N,T,CpDx,CpDy,CpUx,CpUy);
            NoV=max(dot(N,V),1.0e-4);
        }
    }

#ifndef SURFACE_LOW_DETAIL
    float Frost=0.0,IceCracks=0.0;
    [branch] if(Ice)
    {
        // Derivative frame respects mirrored UVs and needs no tangent channel in
        // the original XYZ/N/UV CMP. All patterns stay attached to the UV surface.
        float3 Dx=ddx(In.ViewPosition),Dy=ddy(In.ViewPosition);
        float2 Ux=ddx(In.Uv),Uy=ddy(In.Uv);
        float Det=Ux.x*Uy.y-Ux.y*Uy.x;
        float Sign=Det<0 ? -1.0 : 1.0;
        float3 It=(Dx*Uy.y-Dy*Ux.y)*Sign;
        It-=N*dot(N,It);
        if(dot(It,It)<1.e-12) It=cross(abs(N.y)<0.9 ? float3(0,1,0) : float3(1,0,0),N);
        It=SafeNormal(It);
        float3 Ib=SafeNormal(cross(N,It))*Sign;
        float2 ViewUv=float2(dot(V,It),dot(V,Ib))/max(dot(V,N),0.35);
        // The original asteroid repeats its diffuse UVs roughly four times.
        // A half-rate crystal field gives broad readable fractures, not glitter.
        float2 Uv=In.Uv*0.5;
        // Offset only the submerged layers, not the surface crust. TextureGrad
        // avoids unstable implicit gradients after the uniform material branch.
        float2 Gx=Ux*0.5,Gy=Uy*0.5;
        float4 Skin=tex2Dgrad(IceLayers,Uv,Gx,Gy);
        float2 Shift=ViewUv*IceStyle.y;
        float A=tex2Dgrad(IceLayers,Uv-Shift*0.30,Gx,Gy).r;
        float B=tex2Dgrad(IceLayers,Uv-Shift*0.68,Gx,Gy).g;
        float C=tex2Dgrad(IceLayers,Uv-Shift,Gx,Gy).b;
        // Frost occupies discrete cloudy islands, leaving most cleavage clear.
        // A broad midpoint mask would turn every face into blue rough stone.
        Frost=smoothstep(0.50,0.70,Skin.a)*IceStyle.z;
        IceCracks=saturate(A*0.62+B*0.33+C*0.18);
        float Grain=saturate(dot(T.rgb,float3(0.299,0.587,0.114)));
        float3 Deep=lerp(float3(0.045,0.18,0.28),T.rgb*float3(0.70,0.90,1.0),0.38);
        float3 Interior=lerp(Deep,float3(0.48,0.76,0.86),IceCracks*(1.0-Frost*0.7));
        Albedo.rgb=lerp(Interior,float3(0.57,0.67,0.70)*(0.80+0.20*Grain),Frost)*Base.rgb;
        // Fine surface cleavage, separate from the three submerged crack layers.
        float Hx=tex2Dgrad(IceLayers,Uv+float2(1.0/512.0,0),Gx,Gy).r-Skin.r;
        float Hy=tex2Dgrad(IceLayers,Uv+float2(0,1.0/512.0),Gx,Gy).r-Skin.r;
        N=SafeNormal(N-(It*Hx+Ib*Hy)*lerp(1.3,0.28,Frost));
        NoV=max(dot(N,V),1.e-4);
    }
    float3 FinishStyle=SurfaceFinish.w>0.5 ? SurfaceFinish.xyz : float3(1.35,0.9,0.8);
    if(Ice) FinishStyle=float3(0.90,0.32,0.0); // no metal brushing on crystal ice
    bool Reflective=(BaseOps.w>=0 && Surface.z>0) || Cockpit || Glass || Ice;
    if(Cockpit) FinishStyle*=MaterialStyle.w;
    float PanelGloss=saturate(dot(T.rgb,float3(0.299,0.587,0.114)));
    float FinishMask=lerp(0.35,1.0,PanelGloss);
    float Roughness = Reflective ? clamp(MaterialSpecular.w*lerp(1.12,0.88,PanelGloss),0.24,1.0) : MaterialSpecular.w;
    if(Cockpit) Roughness=clamp(Roughness,0.32,0.65);
    if(Glass) Roughness=Greenhouse ? lerp(0.20,0.52,smoothstep(0.60,0.94,T.a)) : 0.24;
    if(Ice) Roughness=lerp(0.18,0.78,Frost);
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
                // Keep RP9's near-zero falloff for legacy hard-edged spotlights.
                Attenuation *= pow(Cone, max(Light.DiffuseFalloff.w, 1.0e-6));
            }
        }
        float NoL = saturate(dot(N, L));
#ifndef SURFACE_LOW_DETAIL
        if(Ice) NoL=saturate((dot(N,L)+0.22)/1.22); // shallow scattering around a lit cleavage
#endif
        if(Directional) SunFacing=max(SunFacing,NoL);
        if(Directional && dot(SafeNormal(Light.DirectionRange.xyz),ShadowSunRay.xyz)>0.98)
            Attenuation *= SunVisibility;
#ifndef SURFACE_LOW_DETAIL
        [branch] if(Ice)
        {
            // Bounded light-dependent translucency approximation, not emission
            // and not scene transparency. A thickness bake can refine this later.
            float Back=pow(saturate(dot(V,-L-N*0.28)),3.0)*saturate(-dot(N,L));
            float Transmission=IceStyle.w*(1.0-Frost)*(0.35+IceCracks*0.65);
            DiffuseLighting+=float3(0.12,0.39,0.50)*Light.DiffuseFalloff.rgb*
                (Back*Transmission*Attenuation);
        }
#endif
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
#ifdef SURFACE_ROCK
        Highlights += Attenuation * NoL * (Spec * 1.25 + Finish * (0.75 * RockStyle2.w)) * Light.SpecularOuter.rgb;
#else
        Highlights += Attenuation * NoL * (Spec * 1.25 + Finish * 0.75) * Light.SpecularOuter.rgb;
#endif
        if(Reflective)
        {
            // A smooth top coat supplies the bright moving accent, while an
            // elongated satin lobe makes front-facing flat panels read as metal.
            float CoatRoughness=Glass ? 0.18 : lerp(0.27,0.18,PanelGloss);
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
    [branch] if(Ice)
    {
        float IceFresnel=0.025+0.975*pow(1.0-saturate(NoV),5.0);
        Colour=DiffuseLighting+Environment.rgb*Surface.z*(0.025+IceFresnel*0.40)*
            (1.0-Frost*0.75)*ReflectionLighting;
    }
    // A soft shoulder only on added gloss preserves the authored diffuse texture.
    // Bright source texels and emissive windows are not globally tone-mapped.
    if(BaseOps.w<0.0 && !Cockpit && !Glass && !Ice) Highlights=0.0;
    float GlassFresnel=0;
    [branch] if(Glass)
    {
        GlassFresnel=0.04+0.96*pow(1.0-saturate(NoV),5.0);
        // Authored envmaps are retained; materials without one get a restrained
        // smooth reflection band. No scene copy/refraction or extra render pass.
        float Band=pow(saturate(1.0-abs(R.y*0.75+0.15)),4.0);
        float3 GlassEnv=Surface.z>0 ? Environment.rgb :
            lerp(float3(0.05,0.07,0.10),float3(0.32,0.38,0.45),Band);
        float3 FrameColour=Colour;
        // Preserve the authored blue/green tint instead of almost discarding it.
        // Broad reflections and a darker grazing tint suggest thick laminated
        // glass; actual scene refraction/blur is deliberately not sampled here.
        float3 GlassTint=saturate(Albedo.rgb);
        Colour=GlassTint*lerp(0.72,0.46,GlassFresnel)+
            GlassEnv*lerp(float3(1,1,1),GlassTint,0.20)*
            (0.18+0.60*GlassFresnel)*MaterialStyle.z;
        Highlights*=MaterialStyle.z*1.35;
        [branch] if(Greenhouse)
        {
            // The original alpha distinguishes solid metal ribs from glazing.
            // Retain those ribs and the visible plants; only the panes get a
            // pale neutral tint, texture-anchored haze and broad coated reflection.
            float Frame=smoothstep(0.60,0.94,T.a);
            float Haze=saturate(dot(T.rgb,float3(0.299,0.587,0.114)));
            float3 Tint=lerp(float3(0.065,0.067,0.068),float3(0.115,0.118,0.120),Haze);
            float3 NeutralEnv=lerp(dot(GlassEnv,float3(0.299,0.587,0.114)).xxx,GlassEnv,0.20);
            float3 Pane=1.34*(Tint+NeutralEnv*
                (0.12+0.65*GlassFresnel)*MaterialStyle.z);
            Colour=lerp(Pane,FrameColour,Frame);
        }
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
    if(Ice) Alpha=1.0; // solid depth-writing hull, including the clear-looking parts
#ifndef SURFACE_LOW_DETAIL
    [branch] if(Glass)
    {
        float Shine=max(Highlights.r,max(Highlights.g,Highlights.b));
        // Authored Oc=.8 gives ~33% opacity face-on. Retain the tinted finish
        // with a modest increase in density toward the edges.
        Alpha=clamp(0.15+saturate(Albedo.a)*0.22+GlassFresnel*0.14+
                    saturate(Shine)*0.04,0.15,0.49);
        [branch] if(Greenhouse)
        {
            float Frame=smoothstep(0.60,0.94,T.a);
            float Haze=saturate(dot(T.rgb,float3(0.299,0.587,0.114)));
            float PaneAlpha=saturate(1.34*(0.24+GlassFresnel*0.26+Haze*0.05+saturate(Shine)*0.03));
            Alpha=lerp(PaneAlpha,Albedo.a,Frame);
        }
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
#endif
}
