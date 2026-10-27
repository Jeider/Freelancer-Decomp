// Deterministic, bounded, short-range contact AO. No history, lighting edits or UVs.
sampler2D Depth:register(s14);
row_major float4x4 InvProjection:register(c0);
float4 ImageSize:register(c4); // inverse width/height, width/height
float4 Viewport:register(c5); // x,y,width,height in pixels
float4 Control:register(c6); // viewport minZ,maxZ,radius,strength
float4 Project:register(c7); // projection Y scale
float3 Position(float2 U,float D) {
 float2 N=((U*ImageSize.zw-Viewport.xy)/Viewport.zw)*float2(2,-2)+float2(-1,1);
 float Z=(D-Control.x)/max(Control.y-Control.x,1e-6);
 float4 P=mul(float4(N,Z,1),InvProjection);return P.xyz/max(abs(P.w),1e-6)*sign(P.w);
}
float4 PSMain(float2 U:TEXCOORD0):COLOR0 {
 float D=tex2D(Depth,U).r;if(D>=Control.y-1e-6 || D<Control.x)return 1;
 float3 P=Position(U,D);
 float2 X=float2(ImageSize.x,0),Y=float2(0,ImageSize.y);
 float3 R=Position(U+X,tex2D(Depth,U+X).r)-P,L=P-Position(U-X,tex2D(Depth,U-X).r);
 float3 T=Position(U+Y,tex2D(Depth,U+Y).r)-P,B=P-Position(U-Y,tex2D(Depth,U-Y).r);
 float3 Dx=dot(R,R)<dot(L,L) ? R:L,Dy=dot(T,T)<dot(B,B) ? T:B;
 float3 Cross=cross(Dx,Dy);float Norm=dot(Cross,Cross);if(Norm<1e-16)return 1;
 float3 N=Cross*rsqrt(Norm);if(dot(N,-P)<0)N=-N;
 // Local, restrained contact: half the previous radius avoids broad dark halos.
 float Radius=Control.z,Pixels=clamp(Radius*abs(Project.x)*Viewport.w*.5/max(abs(P.z),.01),1,32);
 float2 Directions[8]={float2(1,0),float2(.7071,.7071),float2(0,1),float2(-.7071,.7071),
                      float2(-1,0),float2(-.7071,-.7071),float2(0,-1),float2(.7071,-.7071)};
 float Occlusion=0;
 [unroll] for(int I=0;I<8;++I) [unroll] for(int J=1;J<=4;++J) {
  float2 S=U+Directions[I]*(Pixels*(J/4.0))*ImageSize.xy;
  float2 Pixel=S*ImageSize.zw;
  float Sd=tex2D(Depth,S).r;float3 Delta=Position(S,Sd)-P;float Len=length(Delta);
  float Valid=all(Pixel>=Viewport.xy+.5) && all(Pixel<Viewport.xy+Viewport.zw-.5) && Sd<Control.y-1e-6;
  float Facing=saturate((dot(N,Delta)/max(Len,1e-5)-.12)*2);
  Occlusion+=Valid*Facing*saturate(1-Len/Radius)*smoothstep(.005,.025,Len);
 }
 // Default .32 caps darkening at 32%, even in dense contacts. Broader
 // normalization softens sparse sampling around small tabletop objects.
 return 1-min(saturate(Control.w),.45)*saturate(Occlusion/8);
}
