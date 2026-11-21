// Opaque procedural decorations: native albedo, vertex Lambert lighting.
// This diagnostic material has no fog, coverage, relief or pixel lighting.
float4 CamRel : register(c0);
float4 ViewRow[3] : register(c1);
float4 Proj : register(c4);
float4 Remap : register(c5);
float4 Lod : register(c6);
float4 MeshSpin : register(c10);
float4 Ambient : register(c11);
float4 Sun : register(c12);
float4 SunView : register(c13);

struct Vertex {
    float3 Position : POSITION0;
    float3 Normal : NORMAL0;
    float2 Uv : TEXCOORD0;
    float4 CentreRadius : TEXCOORD1;
    float4 Rotation : TEXCOORD2;
    float4 Colour : COLOR0;
};
struct Interp {
    float4 Position : POSITION0;
    float2 Uv : TEXCOORD0;
    float3 Light : TEXCOORD1;
};
float3 Rotate(float3 v,float4 q) { return v+2.0*cross(q.xyz,cross(q.xyz,v)+q.w*v); }
Interp VSLite(Vertex In)
{
    Interp Out;
    float4 Q=In.Rotation;
    if(In.Colour.b>.5){
        float s=MeshSpin.x,c=MeshSpin.y;
        Q=float4(Q.x*c-Q.z*s,Q.y*c+Q.w*s,Q.z*c+Q.x*s,Q.w*c-Q.y*s);
    }
    float3 centre=In.CentreRadius.xyz-CamRel.xyz;
    float3 rel=centre+Rotate(In.Position*In.CentreRadius.w,Q);
    float3 v=float3(dot(rel,ViewRow[0].xyz),dot(rel,ViewRow[1].xyz),dot(rel,ViewRow[2].xyz));
    float depth=-v.z;
    Out.Position=float4(v.xy*Proj.xy,Proj.z*depth+Proj.w,depth);
    if(depth>Lod.x)Out.Position.z=depth*Lod.w;
    Out.Position.xy=Out.Position.xy*Remap.xy+Remap.zw*depth;
    if(-dot(centre,ViewRow[2].xyz)+In.CentreRadius.w<1)Out.Position=float4(0,0,-2,1);
    float3 n=Rotate(In.Normal,Q);
    n=float3(dot(n,ViewRow[0].xyz),dot(n,ViewRow[1].xyz),dot(n,ViewRow[2].xyz));
    Out.Light=(Ambient.rgb+Sun.rgb*saturate(dot(n,SunView.xyz)))*lerp(.85,1.1,In.Colour.r);
    Out.Uv=In.Uv;
    return Out;
}
float4 TexTint : register(c0);
sampler2D Albedo : register(s0);
float4 PSLite(Interp In) : COLOR0
{
    return float4(tex2D(Albedo,In.Uv).rgb*TexTint.rgb*In.Light,1);
}
