// Additive overlay only. The authored material is drawn normally beforehand.
// Original artwork is retained. Energy motion comes exclusively from MaterialAnim.
row_major float4x4 WorldView : register(c0);
row_major float4x4 Projection : register(c4);
row_major float4x4 NormalView : register(c8);
row_major float4x4 TextureMatrix : register(c12);
float4 VertexOptions : register(c16); // transformed UVs, vertex colour present
struct Input { float4 p:POSITION; float3 n:NORMAL; float2 uv:TEXCOORD0; float4 colour:COLOR0; };
struct Output {
    float4 p:POSITION;
    float2 uv:TEXCOORD0;
    float3 view:TEXCOORD1;
    float3 normal:TEXCOORD2;
    float3 local:TEXCOORD3;
    float alpha:TEXCOORD4;
};
Output VSMain(Input i) {
    Output o;
    float4 v=mul(float4(i.p.xyz,1),WorldView);
    o.p=mul(v,Projection); o.view=v.xyz;
    o.normal=mul(float4(i.n,0),NormalView).xyz;
    o.local=i.p.xyz;
    o.uv=VertexOptions.x>0.5 ? mul(float4(i.uv,0,1),TextureMatrix).xy : i.uv;
    o.alpha=VertexOptions.y>0.5 ? i.colour.a : 1;
    return o;
}
sampler2D Authored : register(s0);
float4 Effect : register(c0); // reserved (no extra clock), strength, membrane, opacity
float4 Texel : register(c1);
float4 Fog : register(c2); // start,end,density,mode
float4 Options : register(c3); // range fog, alpha uses texture, material tint unused
float4 PSMain(Output i):COLOR0 {
    float4 source=tex2D(Authored,i.uv);
    // Low-frequency colour spreads the glow across the original luminous shapes;
    // the centre alpha keeps authored holes open. No added texture/normal atlas.
    float3 soft=tex2Dbias(Authored,float4(i.uv,0,2)).rgb*0.4;
    soft+=tex2Dbias(Authored,float4(i.uv+Texel.xy,0,2)).rgb*0.15;
    soft+=tex2Dbias(Authored,float4(i.uv-Texel.xy,0,2)).rgb*0.15;
    soft+=tex2Dbias(Authored,float4(i.uv+float2(Texel.x,-Texel.y),0,2)).rgb*0.15;
    soft+=tex2Dbias(Authored,float4(i.uv+float2(-Texel.x,Texel.y),0,2)).rgb*0.15;
    float3 n=normalize(i.normal), v=normalize(-i.view);
    float rim=pow(1-saturate(abs(dot(n,v))),2.5);
    float3 glow;
    if(Effect.z>0.5) {
        // Sparse, stationary silk: only dense original fibres catch a little light.
        // The native material's lower Oc opens up the spaces between the fibres.
        float fibres=pow(saturate(source.a),4);
        glow=(source.rgb*0.10+float3(0.30,0.38,0.44)*rim*0.32)*fibres;
    } else {
        // Organic wet coat from the ORIGINAL moving artwork. Screen derivatives
        // follow MaterialAnim, avoiding a second unrelated wave/scroll animation.
        float height=dot(source.rgb,float3(0.299,0.587,0.114));
        float3 dpdx=ddx(i.view), dpdy=ddy(i.view);
        float3 r1=cross(dpdy,n), r2=cross(n,dpdx);
        float determinant=dot(dpdx,r1);
        float3 gradient=(r1*ddx(height)+r2*ddy(height))/max(abs(determinant),1e-8)*sign(determinant);
        gradient*=12;
        gradient*=min(1.0,0.55/max(length(gradient),1e-5));
        float3 wet=normalize(n-gradient);
        if(dot(wet,v)<0) wet=-wet;
        float3 halfVector=normalize(v+normalize(float3(-0.35,0.55,-0.76)));
        float specular=pow(saturate(dot(wet,halfVector)),28);
        float3 warmPearl=lerp(soft,float3(1.0,0.72,0.51),0.35);
        glow=soft*(0.22+0.20*rim)+warmPearl*specular*0.28;
    }
    glow*=Effect.y;
    float alpha=lerp(1,source.a,Options.y)*Effect.w*saturate(i.alpha);
    float distance=Options.x>0.5 ? length(i.view) : abs(i.view.z);
    float visibility=1;
    if(Fog.w>2.5) visibility=saturate((Fog.y-distance)/max(Fog.y-Fog.x,0.001));
    else if(Fog.w>1.5) visibility=exp(-pow(distance*Fog.z,2));
    else if(Fog.w>0.5) visibility=exp(-distance*Fog.z);
    return float4(glow*alpha*visibility,alpha);
}
