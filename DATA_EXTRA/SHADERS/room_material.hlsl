// Room-only materials. Existing UVs, texture layers, alpha, fog and authored lights.
row_major float4x4 WorldView:register(c0), Projection:register(c4), NormalView:register(c8);
row_major float4x4 TexMatrix0:register(c12), TexMatrix1:register(c16);
float4 VertexMode:register(c20), VertexColour:register(c21);
float4 BoneRows[192]:register(c24);
row_major float4x4 View:register(c216);
struct Vertex {
 float3 P:POSITION0; float3 N:NORMAL0; float4 C:COLOR0; float4 S:COLOR1;
 float2 U0:TEXCOORD0; float2 U1:TEXCOORD1; float2 U2:TEXCOORD2;
 float3 W:BLENDWEIGHT0; float4 B:BLENDINDICES0;
};
struct Pixel {
 float4 P:POSITION0; float3 V:TEXCOORD0; float3 N:TEXCOORD1;
 float2 U0:TEXCOORD2; float2 U1:TEXCOORD3; float4 C:COLOR0; float4 S:COLOR1;
};
Pixel MakeVertex(Vertex I,float3 P,float3 N) {
 Pixel O;O.P=mul(float4(P,1),Projection);O.V=P;O.N=N;
 float2 U0=VertexMode.x>1.5 ? I.U2 : VertexMode.x>.5 ? I.U1 : I.U0;
 float2 U1=VertexMode.y>1.5 ? I.U2 : VertexMode.y>.5 ? I.U1 : I.U0;
 O.U0=VertexMode.z>.5 ? mul(float4(U0,1,0),TexMatrix0).xy : U0;
 O.U1=VertexMode.w>.5 ? mul(float4(U1,1,0),TexMatrix1).xy : U1;
 O.C=VertexColour.x>.5 ? I.C : 1;O.S=VertexColour.y>.5 ? I.S : 0;return O;
}
Pixel VSMain(Vertex I) {return MakeVertex(I,mul(float4(I.P,1),WorldView).xyz,mul(float4(I.N,0),NormalView).xyz);}
float3 BoneTransform(float4 P,int Bone) {
 int B=clamp(Bone,0,63)*3;return float3(dot(P,BoneRows[B]),dot(P,BoneRows[B+1]),dot(P,BoneRows[B+2]));
}
Pixel VSSkin(Vertex I) {
 float4 W=float4(I.W,1-dot(I.W,float3(1,1,1)));float3 P=0,N=0;
 [unroll] for(int K=0;K<4;++K){P+=W[K]*BoneTransform(float4(I.P,1),(int)I.B[K]);N+=W[K]*BoneTransform(float4(I.N,0),(int)I.B[K]);}
 return MakeVertex(I,mul(float4(P,1),View).xyz,mul(float4(N,0),View).xyz);
}
sampler2D BaseMap:register(s0), DetailMap:register(s1), FinishMap:register(s14);
float4 MatDiffuse:register(c0), MatAmbient:register(c1), MatEmission:register(c2);
float4 MatSpecular:register(c3), Mode:register(c4), Fog:register(c5), FogColour:register(c6);
float4 Ops0:register(c7), Ops1:register(c8), Args:register(c9), Factor:register(c10);
float4 Profile:register(c11); // w: -1 interior, -.25 maximum clothing, 0 eyes/legacy, 1 native skin
struct Light {float4 PosType;float4 DirRange;float4 DiffFalloff;float4 SpecOuter;float4 AttInner;};
Light Lights[8]:register(c12);
float4 Sources:register(c52), AmbientLight:register(c53);
float4 Source(float4 Material,float Mode,Pixel I) {return Mode>1.5 ? I.S : Mode>.5 ? I.C : Material;}
float4 Arg(float Id,float4 T,float4 D,float4 C) {
 float Base=fmod(Id,16);float4 R=Base<.5 ? D : Base<1.5 ? C : Base<2.5 ? T : Factor;
 if(fmod(floor(Id/16),2)>.5)R=1-R;if(Id>=32)R=R.aaaa;return R;
}
float4 Op(float Id,float4 A,float4 B,float4 T,float4 D,float4 C) {
 if(Id<2.5)return A;if(Id<3.5)return B;if(Id<4.5)return A*B;
 if(Id<5.5)return 2*A*B;if(Id<6.5)return 4*A*B;if(Id<7.5)return A+B;
 if(Id<8.5)return A+B-.5;if(Id<9.5)return (A+B-.5)*2;if(Id<10.5)return A-B;
 if(Id<11.5)return A+B-A*B;if(Id<12.5)return lerp(B,A,D.a);
 if(Id<13.5)return lerp(B,A,T.a);if(Id<14.5)return lerp(B,A,Factor.a);
 if(Id<15.5)return A+B*(1-T.a);return lerp(B,A,C.a);
}
float4 Stage(float4 T,float4 D,float4 C,float4 Ops,float2 Alpha) {
 float4 R=Op(Ops.x,Arg(Ops.z,T,D,C),Arg(Ops.w,T,D,C),T,D,C);
 R.a=Ops.y<1.5 ? C.a : Op(Ops.y,Arg(Alpha.x,T,D,C),Arg(Alpha.y,T,D,C),T,D,C).a;
 return saturate(R);
}
float3 Perturb(float3 N,float3 P,float2 U,float2 XY) {
 float3 X=ddx(P),Y=ddy(P);float2 A=ddx(U),B=ddy(U);float Det=A.x*B.y-A.y*B.x;
 float3 T=X*B.y-Y*A.y,Q=Y*A.x-X*B.x;
 T-=N*dot(N,T);Q-=N*dot(N,Q);
 float Scale=rsqrt(max(max(dot(T,T),dot(Q,Q)),1e-16)),Sign=Det<0 ? -1 : 1;
 return abs(Det)>1e-12 ? normalize(N*sqrt(saturate(1-dot(XY,XY)))+(T*XY.x+Q*XY.y)*Scale*Sign) : N;
}
float4 PSMain(Pixel I):COLOR0 {
 float4 B=tex2D(BaseMap,I.U0),T=tex2D(DetailMap,I.U1);
 float4 F=Mode.z>.5 ? tex2D(FinishMap,I.U0) : float4(.5,.5,Profile.y,1);
 // Amplify tangent components with a bounded bend; retain a positive normal Z
 // even at the strongest generated edges.
 float2 XY=(F.xy*2-1)*Profile.x;
 float SkinProfile=saturate(Profile.w),Skin=SkinProfile*F.a;
 // Interior x12; clothing x6 after reducing exaggerated body relief by half.
 // Eyes and native faces do not inherit the clothing preset.
 float Interior=Profile.w<-.5 ? 1 : 0;
 float Clothing=Profile.w>=-.5 && Profile.w<-.125 ? 1 : 0;
 float Maximum=max(Interior,Clothing);
 XY*=lerp(lerp(3.0,1.6,SkinProfile),lerp(12.0,3.0,Clothing),Maximum);
 XY*=rsqrt(max(1.0,dot(XY,XY)/lerp(.64,.970,Maximum)));
 float3 N=Perturb(normalize(I.N),I.V,I.U0,XY),V=normalize(-I.V);
 // Keep cloth matte while making polished materials distinctly smoother.
 // Skin keeps its original average roughness and gets modest local variation.
 float Rough=clamp(lerp(.82+(F.b-.82)*lerp(1.45,3.0,Clothing),Profile.y+(F.b-Profile.y)*2,SkinProfile),.16,.95);
 float HighlightGain=lerp(lerp(3.0,1.6,SkinProfile),12.0,Clothing);
 float4 D=Source(MatDiffuse,Sources.x,I);float3 Diff=0,Spec=0;
 [loop] for(int K=0;K<8;++K) {
  if(K>=Mode.x)break;Light L=Lights[K];float3 To=L.PosType.xyz-I.V;
  float Dist=length(To);float3 Dir=L.PosType.w>2.5 ? normalize(-L.DirRange.xyz) : To/max(Dist,1e-6);
  float Att=1;
  if(L.PosType.w<2.5){Att=Dist<=L.DirRange.w ? rcp(max(dot(L.AttInner.xyz,float3(1,Dist,Dist*Dist)),1e-6)) : 0;
   if(L.PosType.w>1.5){float Cone=dot(-Dir,normalize(L.DirRange.xyz));Att*=pow(saturate((Cone-L.SpecOuter.w)/max(L.AttInner.w-L.SpecOuter.w,1e-5)),max(L.DiffFalloff.w,1e-6));}}
  float NdL=dot(N,Dir),NL=saturate(NdL);
  // Restrained wrap approximation, not a screen blur or full physical SSS.
  Diff+=L.DiffFalloff.rgb*Att*lerp(NL.xxx,saturate((NdL+.30)/1.30)*float3(1,.94,.90),Skin*.60);
  float3 H=normalize(Dir+V);float NH=saturate(dot(N,H)),NV=max(saturate(dot(N,V)),.01),VH=saturate(dot(V,H));
  float A=Rough*Rough,A2=A*A,Den=NH*NH*(A2-1)+1,Gk=(Rough+1)*(Rough+1)/8;
  float G=NV/(NV*(1-Gk)+Gk)*NL/(NL*(1-Gk)+Gk),Fr=.04+.96*pow(1-VH,5);
  Spec+=L.SpecOuter.rgb*Att*NL*(A2/(3.14159265*Den*Den)*G*Fr/max(4*NV*NL,.001))*Profile.z*HighlightGain;
 }
 float4 Lit=D;
 if(Mode.y>.5) Lit.rgb=saturate(D.rgb*Diff+Source(MatAmbient,Sources.y,I).rgb*AmbientLight.rgb+Source(MatEmission,Sources.z,I).rgb);
 else Lit=I.C;
 float4 R=Stage(B,Lit,Lit,Ops0,Args.xy);
 if(Mode.w>1.5)R=Stage(T,Lit,R,Ops1,Args.zw);
 if(Mode.y>.5)R.rgb+=min(Spec,lerp(lerp(.40,.26,SkinProfile),.65,Clothing))*(1-saturate(max(MatEmission.r,max(MatEmission.g,MatEmission.b))));
 float Distance=FogColour.w>.5 ? length(I.V) : abs(I.V.z),Visibility=1;
 if(Fog.w>2.5)Visibility=saturate((Fog.y-Distance)/max(Fog.y-Fog.x,.0001));
 else if(Fog.w>1.5)Visibility=exp(-pow(Distance*Fog.z,2));else if(Fog.w>.5)Visibility=exp(-Distance*Fog.z);
 R.rgb=lerp(FogColour.rgb,R.rgb,Visibility);return R;
}
