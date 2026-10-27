// Per-object, world-space vertical silhouette. No room light or UV edits.
row_major float4x4 World:register(c0), TopProjection:register(c4), TexMatrix:register(c8);
float4 TextureMode:register(c12);
float4 BoneRows[192]:register(c24);
struct Vertex { float3 P:POSITION0; float3 W:BLENDWEIGHT0; float4 B:BLENDINDICES0;
 float2 U0:TEXCOORD0; float2 U1:TEXCOORD1; float2 U2:TEXCOORD2; };
struct Pixel { float4 P:POSITION0; float D:TEXCOORD0; float2 U:TEXCOORD1; };
Pixel Make(Vertex I,float3 P) {
 Pixel O; O.P=mul(float4(P,1),TopProjection); O.D=O.P.z;
 float2 U=TextureMode.x>1.5 ? I.U2 : TextureMode.x>.5 ? I.U1 : I.U0;
 O.U=TextureMode.y>.5 ? mul(float4(U,1,0),TexMatrix).xy : U; return O;
}
Pixel VSMain(Vertex I) { return Make(I,mul(float4(I.P,1),World).xyz); }
Pixel VSSkin(Vertex I) {
 float4 W=float4(I.W,1-dot(I.W,float3(1,1,1))); float3 P=0;
 [unroll] for(int K=0;K<4;++K) {
  int B=clamp((int)I.B[K],0,63)*3; float4 V=float4(I.P,1);
  P+=W[K]*float3(dot(V,BoneRows[B]),dot(V,BoneRows[B+1]),dot(V,BoneRows[B+2]));
 }
 return Make(I,P);
}
sampler2D Base:register(s0);
float4 Alpha:register(c0);
float4 PSMain(Pixel I):COLOR0 {
 if(Alpha.x>.5) clip(tex2D(Base,I.U).a*Alpha.z-Alpha.y);
 return I.D.xxxx;
}
sampler2D SceneDepth:register(s14), Shadow:register(s15);
row_major float4x4 InvViewProjection:register(c0), ShadowProjection:register(c4);
float4 Image:register(c8), Viewport:register(c9), Control:register(c10);
// Control: minZ,maxZ,map texel size,strength. Projection is world-space.
float4 ApplyPS(float2 U:TEXCOORD0):COLOR0 {
 float D=tex2D(SceneDepth,U).r;
 if(D>=Control.y-1e-6 || D<Control.x) return 1;
 float2 N=((U*Image.zw-Viewport.xy)/Viewport.zw)*float2(2,-2)+float2(-1,1);
 float4 W=mul(float4(N,(D-Control.x)/max(Control.y-Control.x,1e-6),1),InvViewProjection);
 W/=W.w; float3 P=mul(W,ShadowProjection).xyz;
 float2 S=P.xy*float2(.5,-.5)+.5;
 if(any(S<0) || any(S>1) || P.z<0) return 1;
 float Blocked=0,Weight=0;
 [unroll] for(int Y=-1;Y<=1;++Y) [unroll] for(int X=-1;X<=1;++X) {
  float2 Q=S+float2(X,Y)*Control.z*1.5;
  float Z=tex2D(Shadow,Q).r, Gap=P.z-Z;
  float K=(X==0 ? 2:1)*(Y==0 ? 2:1);
  float Valid=all(Q>=0) && all(Q<=1) && Z<.9999 && Gap>.0015;
  Blocked+=K*Valid*(1-smoothstep(.5,2.0,Gap)); Weight+=K;
 }
 return 1-Control.w*Blocked/Weight;
}
