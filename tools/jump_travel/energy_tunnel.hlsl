// Standalone art prototype: a new material, not a recolour of jumptube.
// Longitudinal electric fractures borrow the original's visual language.
float4 ViewRow[3] : register(c0);
float4 ProjectionRow[4] : register(c3);
float4 Remap : register(c7);
struct Vertex { float3 P:POSITION0; float4 C:COLOR0; float2 UV:TEXCOORD0; };
struct Interp { float4 P:POSITION0; float4 C:COLOR0; float2 UV:TEXCOORD0; float Depth:TEXCOORD1; };
Interp VSMain(Vertex v) {
    Interp o;
    float4 p=float4(v.P,1);
    float4 view=float4(dot(p,ViewRow[0]),dot(p,ViewRow[1]),-dot(p,ViewRow[2]),1);
    o.P=float4(dot(view,ProjectionRow[0]),dot(view,ProjectionRow[1]),dot(view,ProjectionRow[2]),dot(view,ProjectionRow[3]));
    o.C=v.C; o.UV=v.UV; o.Depth=view.z;
    return o;
}
sampler3D Noise:register(s1);
float4 Params:register(c0); // layer, simulation time
float NoiseAt(float a,float z,float scale) {
    return tex3D(Noise,float3(cos(a)*scale,sin(a)*scale,z)).r;
}
// Analytically filter narrow filaments at their projected pixel footprint.
float Line(float phase,float width) {
    float d=abs(sin(phase));
    float aa=max(fwidth(phase)*.65,.001);
    return (1-smoothstep(width,width+aa,d))*min(1,width/aa);
}
float4 PSMain(Interp i):COLOR0 {
    float layer=Params.x, t=Params.y;
    float a=i.UV.x*6.28318530718 + t*(layer>.5?-.22:.12);
    float z=i.UV.y + t*.42;
    // Periodic angular domain: no visible join in the cylindrical material.
    float curl=a+.23*sin(z*2.1+a*3)+.07*sin(z*6.3-a*5);
    float n=NoiseAt(curl,z*.12,.24);
    float n2=NoiseAt(curl+.12,z*.29,.61);
    float detail=NoiseAt(curl,z*.6,1.8);
    float fine=NoiseAt(curl+.3,z*1.05,3.6);
    float field=n*.64+n2*.25+detail*.11;
    float bend=(n-.5)*2.1+(n2-.5)*.42;
    // Irregular contour sheets, not equally spaced radial spokes. The narrow
    // luminous contour is attached to the edge of each broad plasma sheet.
    float ridge=abs(field-.52);
    float sheet=smoothstep(.32,.59,field);
    float halo=exp2(-ridge*ridge*2400);
    float aa=max(fwidth(field)*.6,.001);
    float core=(1-smoothstep(.006,.006+aa,ridge))*min(1,.006/aa);
    float veins=Line((field+detail*.13)*65,.08);
    float gate=smoothstep(.25,.65,n2+.12*sin(a*3-z));
    float tears=smoothstep(.25,.78,fine);
    float front=z*4.2 + sin(a*3)*1.1;
    float surge=pow(saturate(.5+.5*sin(front)),14);
    float arcs=Line(front+bend*2,.045)*sheet*gate;
    float threads=Line((field+fine*.07)*180,.07)*tears;
    // Cobalt folds, saturated cyan shoulders, small near-white discharge cores.
    // Keep genuine dark gaps between sheets, instead of a full-screen fog veil.
    float3 color=float3(.002,.006,.025);
    color+=sheet*float3(.025,.23,.6)*( .45+n2);
    color+=halo*float3(.025,.65,1.25)*(.55+gate);
    color+=core*float3(1.8,2.3,2.8)*(.35+gate+surge);
    color+=veins*sheet*float3(.07,.48,.9)*(.25+tears);
    color+=threads*float3(.1,.34,.52)*gate;
    color+=arcs*float3(.45,1.2,1.6)*(.4+surge);
    color+=surge*sheet*float3(.015,.18,.32)*gate;
    float depth=smoothstep(650,2700,i.Depth);
    color+=depth*float3(.012,.085,.14);
    // Local highlight roll-off keeps the light cores coloured at 8-bit output.
    color=1-exp2(-color*1.7);
    float fade=1-smoothstep(3100,4400,i.Depth);
    float alpha=layer<.5 ? fade : fade*saturate(sheet*.45+halo*.35+core*.7+arcs*.35);
    return float4(layer<.5?color:color*alpha,alpha);
}
