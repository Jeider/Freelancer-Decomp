row_major float4x4 Projection : register(c0);
struct VSIn { float3 Position:POSITION; float3 Normal:NORMAL; float4 Colour:TEXCOORD0; float2 UV:TEXCOORD1; float4 Axis:TEXCOORD2; float2 Radial:TEXCOORD3; };
struct VSOut { float4 Position:POSITION; float3 View:TEXCOORD0; float3 Normal:TEXCOORD1; float4 Colour:COLOR0; float2 UV:TEXCOORD2; float4 Axis:TEXCOORD3; float2 Radial:TEXCOORD4; };
VSOut VSMain(VSIn i)
{
    VSOut o;
    o.Position=mul(float4(i.Position,1),Projection);
    o.View=i.Position; o.Normal=i.Normal; o.Colour=i.Colour; o.UV=i.UV; o.Axis=i.Axis;
    o.Radial=i.Radial;
    return o;
}
float4 Style : register(c4); // core radius fraction, strength, source alpha, inside/outside sign
float4 Fog : register(c5);
float4 CameraFade : register(c6); // near plane, inverse trail fade distance (0 = disabled)
sampler2D Atlas : register(s0);

float4 PSMain(VSOut i):COLOR0
{
    float3 view=normalize(-i.View);
    float facing=dot(normalize(i.Normal),view);
    // One visible surface per tube; back walls must not double the brightness.
    // From inside, show the exit surface instead. Hardware supplies real depth.
    clip(facing*Style.w);
    // A cylinder's surface normal is perpendicular to its axis. Even at the
    // projected centre, N.V tends to zero when looking along the beam. Using it
    // directly as radial falloff erases the entire body, leaving only a ball.
    // Remove axial foreshortening only for the body. End faces have explicit
    // radial coordinates: no hemispherical bulb and no angle-amplified disc.
    float axial=dot(normalize(i.Axis.xyz),view);
    float transverse2=max(1e-6,1-axial*axial);
    float distance2=i.Axis.w>.5 ? saturate(dot(i.Radial,i.Radial)) :
        saturate(1-facing*facing/transverse2);
    float edge=1-smoothstep(.65,1,distance2);
    float core=exp(-distance2/max(Style.x*Style.x,1e-5));
    float halo=exp(-distance2*4)*edge;
    float4 atlas=tex2D(Atlas,i.UV);
    float3 tint=i.Colour.rgb*atlas.rgb;
    float peak=max(tint.r,max(tint.g,tint.b));
    float3 rgb=(tint*halo+lerp(tint,peak.xxx,.72)*core)*Style.y;
    rgb*=lerp(1,i.Colour.a*atlas.a,Style.z);
    // Per-fragment camera-space fade: only the part approaching the near plane
    // fades, not the entire trail. Fade additive RGB, including ONE/ONE effects.
    if(CameraFade.y>0)
        rgb*=smoothstep(0,1,(i.View.z-CameraFade.x)*CameraFade.y);
    float transmission=1;
    if(Fog.w>2.5) transmission=saturate((Fog.y-i.View.z)/max(Fog.y-Fog.x,.0001));
    else if(Fog.w>1.5) transmission=exp(-pow(i.View.z*Fog.z,2));
    else if(Fog.w>.5) transmission=exp(-i.View.z*Fog.z);
    return float4(max(0,rgb*transmission),0);
}
