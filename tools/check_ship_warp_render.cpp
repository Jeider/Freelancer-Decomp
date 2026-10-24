// Standalone D3D9 HAL check of production ship-warp geometry and shaders.
#define NOMINMAX
#include <windows.h>
#include <d3dx9.h>
#include <vector>
#include <cstdio>
#include <cmath>
#include <algorithm>
#include "../src/freelancer/Client/ship_warp_mesh.h"
static IDirect3DDevice9* D;static IDirect3DSurface9 *RT,*CPU,*DS;
static IDirect3DTexture9 *Z,*SceneCopy;static IDirect3DVertexShader9* ScreenVS;static IDirect3DPixelShader9 *Warp,*Pattern,*DepthBackground,*HullDepth,*White;static bool CoverageOnly=false;static bool WarpOn=false,GlowOn=true,PatternOn=false;static int Marker=-1;static bool ProtectMarker=true;static IDirect3DVertexShader9* VS;static IDirect3DPixelShader9 *PS,*Solid;
static const int W=960,H=540;static float VC[36],PC[20];static std::vector<FShipWarpVertex> Mesh,Ship;
static void Check(HRESULT H){if(FAILED(H)){printf("FAIL HRESULT %08lx\n",H);exit(2);}}
static void Require(bool B,const char* S){printf("%s: %s\n",B?"PASS":"FAIL",S);if(!B)exit(3);}
static void Compile(){
 for(int I=0;I<3;++I){ID3DXBuffer *Code=nullptr,*Error=nullptr,*Asm=nullptr;HRESULT R=D3DXCompileShaderFromFileA("DATA_EXTRA/SHADERS/ship_warp.hlsl",nullptr,nullptr,I==2?"PSWarp":I?"PSMain":"VSMain",I?"ps_3_0":"vs_3_0",0,&Code,&Error,nullptr);if(Error){puts((char*)Error->GetBufferPointer());Error->Release();}Check(R);Check(D3DXDisassembleShader((DWORD*)Code->GetBufferPointer(),FALSE,nullptr,&Asm));FILE* F=fopen(I==2?"src/obj/ship_warp_check/warp.asm":I?"src/obj/ship_warp_check/ps.asm":"src/obj/ship_warp_check/vs.asm","wb");fwrite(Asm->GetBufferPointer(),1,Asm->GetBufferSize(),F);fclose(F);Asm->Release();if(I==2)Check(D->CreatePixelShader((DWORD*)Code->GetBufferPointer(),&Warp));else if(I)Check(D->CreatePixelShader((DWORD*)Code->GetBufferPointer(),&PS));else Check(D->CreateVertexShader((DWORD*)Code->GetBufferPointer(),&VS));Code->Release();}
 const char* Src="float4 main(float4 C:COLOR0):COLOR0{return C;}";ID3DXBuffer* Code=nullptr;Check(D3DXCompileShader(Src,UINT(strlen(Src)),nullptr,nullptr,"main","ps_3_0",0,&Code,nullptr,nullptr));Check(D->CreatePixelShader((DWORD*)Code->GetBufferPointer(),&Solid));Code->Release();
 auto Pixel=[](char const* Text,IDirect3DPixelShader9** Out){ID3DXBuffer* C=nullptr;Check(D3DXCompileShader(Text,UINT(strlen(Text)),nullptr,nullptr,"main","ps_3_0",0,&C,nullptr,nullptr));Check(D->CreatePixelShader((DWORD*)C->GetBufferPointer(),Out));C->Release();};
 const char* Screen="float4 main(float4 P:POSITION0):POSITION0{return P;}";Code=nullptr;Check(D3DXCompileShader(Screen,UINT(strlen(Screen)),nullptr,nullptr,"main","vs_3_0",0,&Code,nullptr,nullptr));Check(D->CreateVertexShader((DWORD*)Code->GetBufferPointer(),&ScreenVS));Code->Release();
 Pixel("float4 C:register(c0);float4 main(float2 P:VPOS):COLOR0{if(C.x>=0&&abs(P.x-C.x)<1.5)return float4(1,0,1,1);float V=fmod(floor(P.x/4)+floor(P.y/4),2);return float4(.06+V*.22,.08+V*.22,.11+V*.22,1);}",&Pattern);
 Pixel("float4 C:register(c0);float4 main(float2 P:VPOS):COLOR0{return C.x>=0&&abs(P.x-C.x)<1.5?C.w:C.z;}",&DepthBackground);
 Pixel("float4 main():COLOR0{return 1;}",&White);
 Pixel("float4 C:register(c2);float4 main(float Z:TEXCOORD1):COLOR0{return C.z+(C.w-C.z)*(C.y-C.x*C.y/Z)/(C.y-C.x);}",&HullDepth);

}
static FShipWarpPoint Eye;
static void Camera(bool Side){
 D3DXVECTOR3 E(Side?130.f:0,Side?48.f:18,Side?-65.f:-160),At(0,0,30),Up(0,1,0);Eye={E.x,E.y,E.z};D3DXMATRIX V,P;D3DXMatrixLookAtLH(&V,&E,&At,&Up);D3DXMatrixPerspectiveFovLH(&P,.8f,float(W)/H,1,1000);
 for(int R=0;R<3;++R)for(int C=0;C<4;++C)VC[R*4+C]=V.m[C][R]*(R==2?-1.f:1.f);
 for(int R=0;R<4;++R)for(int C=0;C<4;++C)VC[12+R*4+C]=P.m[C][R];VC[28]=VC[29]=1;VC[30]=VC[31]=0;VC[32]=1;VC[33]=1000;VC[34]=0;VC[35]=.9f;
 float Params[]={3,1,1.f/W,1.f/H,1,1,1,0,1,1000,0,.9f,.5f/W,.5f/H,1-.5f/W,1-.5f/H,1,1,1,0};memcpy(PC,Params,sizeof(Params));
}
static void Geometry(float Time){Mesh.clear();BuildShipWarpNose(Mesh,{0,0,-29},{1,0,0},{0,1,0},{0,0,1},4,Time,2);for(int Side=-1;Side<=1;Side+=2){FShipWarpPoint P[33];for(int I=0;I<33;++I){float T=float(I)/32;P[I]={Side*(17+T*T*10),std::sin(T*3)*2,14+T*150};}BuildShipWarpTrail(Mesh,P,33,Eye,.95f,Time,Side<0?.2f:.7f);}}
static void ShipGeometry(){using namespace ShipWarpMesh;auto V=[](float X,float Y,float Z){FShipWarpVertex A={{X,Y,Z},0xff6e2420,{0,0}};return A;};
 // A red angular fuselage and tapered wings provide a readable scale reference.
 Quad(Ship,V(-4,-3,-24),V(4,-3,-24),V(-7,-3,20),V(7,-3,20));
 Quad(Ship,V(-4,3,-24),V(-7,3,20),V(4,3,-24),V(7,3,20));
 Quad(Ship,V(-4,-3,-24),V(-7,-3,20),V(-4,3,-24),V(-7,3,20));
 Quad(Ship,V(4,-3,-24),V(4,3,-24),V(7,-3,20),V(7,3,20));
 Quad(Ship,V(-4,-3,-24),V(-4,3,-24),V(4,-3,-24),V(4,3,-24));
 for(int S=-1;S<=1;S+=2){Ship.push_back(V(S*4,1,-12));Ship.push_back(V(S*21,0,17));Ship.push_back(V(S*6,2,22));}
}

static std::vector<DWORD> Render(char const* Name,float Gain=1,float DepthValue=1,bool Bars=false){
 D3DVIEWPORT9 Viewport={0,0,W,H,0,1};
 float Quad[]={-1,-1,0,1, 1,-1,0,1, -1,1,0,1, 1,1,0,1};
 auto Screen=[&](IDirect3DPixelShader9* Shader){D->SetVertexShader(ScreenVS);D->SetPixelShader(Shader);D->SetFVF(D3DFVF_XYZW);D->SetRenderState(D3DRS_ZENABLE,FALSE);D->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);D->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);D->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);Check(D->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,Quad,16));};
 auto Hull=[&](IDirect3DPixelShader9* Shader,bool Write){D->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);D->SetVertexShader(VS);D->SetVertexShaderConstantF(0,VC,9);float Partition[]={1,1000,0,1};D->SetVertexShaderConstantF(8,Partition,1);D->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1);D->SetPixelShader(Shader);D->SetPixelShaderConstantF(0,PC,5);D->SetRenderState(D3DRS_ZENABLE,TRUE);D->SetRenderState(D3DRS_ZWRITEENABLE,Write);D->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);D->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);Check(D->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(Ship.size()/3),Ship.data(),sizeof(FShipWarpVertex)));};
 Check(D->SetRenderTarget(0,RT));Check(D->SetDepthStencilSurface(DS));D->SetViewport(&Viewport);Check(D->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff07111b,1,0));Check(D->BeginScene());
 float Setup[]={float(Marker),0,DepthValue,ProtectMarker?PC[10]+(PC[11]-PC[10])*(1000.f-1000.f/60)/999:1.f};D->SetPixelShaderConstantF(0,Setup,1);if(PatternOn)Screen(Pattern);
 Viewport.MinZ=VC[34];Viewport.MaxZ=VC[35];D->SetViewport(&Viewport);Hull(Solid,true);Check(D->EndScene());
 // Snapshot AFTER the opaque ship, outside BeginScene, matching production capture.
 IDirect3DSurface9* Copy=nullptr;Check(SceneCopy->GetSurfaceLevel(0,&Copy));Check(D->StretchRect(RT,nullptr,Copy,nullptr,D3DTEXF_NONE));Copy->Release();
 // Produce actual sampled hull depth in the same projection/partition, with optional
 // synthetic nearer stripe. No CPU-derived hull mask can hide a source-footprint bug.
 IDirect3DSurface9* DepthTarget=nullptr;Check(Z->GetSurfaceLevel(0,&DepthTarget));D->SetRenderTarget(0,DepthTarget);Viewport.MinZ=0;Viewport.MaxZ=1;D->SetViewport(&Viewport);Check(D->BeginScene());D->SetPixelShaderConstantF(0,Setup,1);Screen(DepthBackground);Viewport.MinZ=VC[34];Viewport.MaxZ=VC[35];D->SetViewport(&Viewport);if(DepthValue>=1)Hull(HullDepth,false);Check(D->EndScene());D->SetRenderTarget(0,RT);DepthTarget->Release();
 Viewport.MinZ=0;Viewport.MaxZ=1;D->SetViewport(&Viewport);Check(D->BeginScene());D->SetVertexShader(VS);D->SetVertexShaderConstantF(0,VC,9);D->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE|D3DFVF_TEX1);PC[1]=Gain;PC[13]=Bars?.2f:.5f/H;PC[15]=Bars?.8f:1-.5f/H;D->SetPixelShaderConstantF(0,PC,5);D->SetTexture(0,Z);D->SetTexture(1,SceneCopy);
 for(int I=0;I<2;++I){D->SetSamplerState(I,D3DSAMP_MINFILTER,I?D3DTEXF_LINEAR:D3DTEXF_POINT);D->SetSamplerState(I,D3DSAMP_MAGFILTER,I?D3DTEXF_LINEAR:D3DTEXF_POINT);D->SetSamplerState(I,D3DSAMP_ADDRESSU,D3DTADDRESS_CLAMP);D->SetSamplerState(I,D3DSAMP_ADDRESSV,D3DTADDRESS_CLAMP);}
 D->SetRenderState(D3DRS_ZENABLE,TRUE);D->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);D->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE);D->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE);
 for(int Pass=0;Pass<2;++Pass){if(Pass?!GlowOn:!WarpOn)continue;D->SetPixelShader(CoverageOnly?White:Pass?PS:Warp);D->SetRenderState(D3DRS_DESTBLEND,Pass?D3DBLEND_ONE:D3DBLEND_INVSRCALPHA);Check(D->DrawPrimitiveUP(D3DPT_TRIANGLELIST,UINT(Mesh.size()/3),Mesh.data(),sizeof(FShipWarpVertex)));}
 Check(D->EndScene());D->SetTexture(0,nullptr);D->SetTexture(1,nullptr);Check(D->GetRenderTargetData(RT,CPU));if(Name){char Path[200];sprintf(Path,"src/obj/ship_warp_check/%s.png",Name);Check(D3DXSaveSurfaceToFileA(Path,D3DXIFF_PNG,CPU,nullptr,nullptr));}
 D3DLOCKED_RECT L;Check(CPU->LockRect(&L,nullptr,D3DLOCK_READONLY));std::vector<DWORD> Pixels(W*H);for(int Y=0;Y<H;++Y)memcpy(Pixels.data()+Y*W,(char*)L.pBits+Y*L.Pitch,W*4);CPU->UnlockRect();return Pixels;
}
static int Changes(std::vector<DWORD>const&A,std::vector<DWORD>const&B){int N=0;for(size_t I=0;I<A.size();++I)N+=A[I]!=B[I];return N;}
int main(){CreateDirectoryA("src/obj/ship_warp_check",nullptr);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);auto* API=Direct3DCreate9(D3D_SDK_VERSION);Require(API!=nullptr,"D3D9 available");HWND Window=CreateWindowA("STATIC","warp check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);D3DPRESENT_PARAMETERS PP={};PP.Windowed=TRUE;PP.SwapEffect=D3DSWAPEFFECT_DISCARD;PP.BackBufferWidth=64;PP.BackBufferHeight=64;PP.BackBufferFormat=D3DFMT_A8R8G8B8;Check(API->CreateDevice(0,D3DDEVTYPE_HAL,Window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&PP,&D));D3DADAPTER_IDENTIFIER9 Adapter;API->GetAdapterIdentifier(0,0,&Adapter);printf("GPU: %s\n",Adapter.Description);Compile();Check(D->CreateRenderTarget(W,H,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&RT,nullptr));Check(D->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&CPU,nullptr));Check(D->CreateDepthStencilSurface(W,H,D3DFMT_D24S8,D3DMULTISAMPLE_NONE,0,TRUE,&DS,nullptr));Check(D->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&Z,nullptr));Check(D->CreateTexture(W,H,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&SceneCopy,nullptr));ShipGeometry();
 for(int Partition=0;Partition<2;++Partition)for(int Side=0;Side<2;++Side){Camera(Side!=0);VC[34]=PC[10]=Partition?.1f:0;VC[35]=PC[11]=Partition?1.f:.9f;Geometry(3);auto Base=Render("base",0),Lit=Render(Side?"side":"front");Require(Changes(Base,Lit)>30,"small nose and ion trails are visible at ship scale");Require(Changes(Lit,Render(nullptr))==0,"paused rendering is exact");Require(Changes(Base,Render("depth_blocked",1,0))==0,"foreground depth completely occludes emission");if(!Partition)Require(Changes(Base,Render(nullptr,1,.95f))==0,"cockpit depth partition completely occludes emission");auto Bars=Render("bars",1,1,true);int Leaks=0;for(int Y=0;Y<H;++Y)if(Y<H*.2f-2||Y>H*.8f+2)for(int X=0;X<W;++X)Leaks+=Bars[Y*W+X]!=Base[Y*W+X];Require(Leaks==0,"viewport bounds clip emission");
 bool Finite=true;for(auto const& V:Mesh)for(float F:V.Position)Finite=Finite&&std::isfinite(F);Require(Finite,"all production mesh positions finite");Geometry(0);PC[0]=0;auto Zero=Render(nullptr);Geometry(96);PC[0]=96;Require(Changes(Zero,Render(nullptr))<20,"geometry and shader animation close at96seconds");Geometry(3.2f);PC[0]=3.2f;Require(Changes(Lit,Render(nullptr))>20,"flow animation visibly advances");
 // An extra trail deliberately behind the fuselage proves hardware depth remains active.
 Mesh.clear();FShipWarpPoint Behind[]={{0,0,70},{0,0,150}};BuildShipWarpTrail(Mesh,Behind,2,Eye,2,3,0);auto Occluded=Render(nullptr);int HullLeaks=0;for(size_t I=0;I<Base.size();++I)if(Base[I]==0xff6e2420)HullLeaks+=Occluded[I]!=Base[I];Require(HullLeaks==0,"ship hull occludes rear emission with read-only hardware depth");}
 for(int Partition=0;Partition<2;++Partition){Camera(false);VC[34]=PC[10]=Partition?.1f:0;VC[35]=PC[11]=Partition?1.f:.9f;Mesh.clear();BuildShipWarpNose(Mesh,{0,0,-22},{1,0,0},{0,1,0},{0,0,1},.5f,3);auto Bare=Render(nullptr,0);Require(Changes(Bare,Render(nullptr))==0,"near-coincident nose behind hull is occluded across Ex depth reset");}

 // New palette output must follow the route, not blue multiplied by a warm tint.
 Camera(true);Geometry(3);WarpOn=false;GlowOn=true;auto PaletteBase=Render(nullptr,0);
 for(int Palette=0;Palette<2;++Palette){float Body[3]={Palette?1.f:.15f,Palette?.5f:1.f,Palette?.05f:.2f},Accent[3]={Palette?1.f:.45f,Palette?.8f:1.f,Palette?.2f:.55f};for(int I=0;I<3;++I){PC[4+I]=Body[I];PC[16+I]=Accent[I];}PC[19]=1;auto Coloured=Render(Palette?"palette_amber":"palette_green");double RGB[3]={};for(size_t I=0;I<Coloured.size();++I)for(int C=0;C<3;++C)RGB[C]+=std::max(0,int((Coloured[I]>>(16-C*8))&255)-int((PaletteBase[I]>>(16-C*8))&255));Require(Palette?(RGB[0]>RGB[1]&&RGB[1]>RGB[2]):(RGB[1]>RGB[0]&&RGB[1]>RGB[2]),"actual glow pixels match green/amber route palette");}
 for(int Partition=0;Partition<2;++Partition)for(int Side=0;Side<2;++Side){Camera(Side!=0);VC[34]=PC[10]=Partition?.1f:0;VC[35]=PC[11]=Partition?1.f:.9f;Geometry(3);PatternOn=true;WarpOn=true;GlowOn=false;Marker=-1;
 auto Base=Render(nullptr,0);auto Refracted=Render(Side?"refraction_side":"refraction_front");Require(Changes(Base,Refracted)>20,"local space refraction visibly bends patterned scene after opaque ship capture");WarpOn=false;Require(Changes(Base,Render(nullptr))==0,"zero intensity refraction is exact identity");GlowOn=true;CoverageOnly=true;auto Coverage=Render(nullptr);CoverageOnly=false;GlowOn=false;WarpOn=true;int Outside=0;for(size_t I=0;I<Base.size();++I)if(Coverage[I]==Base[I])Outside+=Refracted[I]!=Base[I];Require(Outside==0,"refraction leaves every pixel outside actual geometry coverage unchanged");
 Require(Changes(Refracted,Render(nullptr))==0,"refraction pause is pixel exact");PC[0]=3.15f;Require(Changes(Refracted,Render(nullptr))>20,"refraction evolves without rebuilding geometry");PC[0]=3;
 Require(Changes(Base,Render(nullptr,1,0))==0,"refraction rejects nearer scene depth");if(!Partition)Require(Changes(Base,Render(nullptr,1,.95f))==0,"refraction protects cockpit partition");
 auto Bars=Render("refraction_bars",1,1,true);int Leaks=0;for(int Y=0;Y<H;++Y)if(Y<H*.2f-2||Y>H*.8f+2)for(int X=0;X<W;++X)Leaks+=Bars[Y*W+X]!=Base[Y*W+X];Require(Leaks==0,"refraction preserves viewport bars");
 int MaxDelta=-1;for(int I=0;I<W*H;++I){int Delta=abs(int(Refracted[I]&255)-int(Base[I]&255));if(Delta>MaxDelta){MaxDelta=Delta;Marker=I%W;}}auto MarkedBase=Render(nullptr,0),Marked=Render("refraction_foreground_footprint");int Smear=0,ChangedForeground=0;for(size_t I=0;I<Marked.size();++I){auto Magenta=[](DWORD C){return int((C>>16)&255)>int((C>>8)&255)+30&&int(C&255)>int((C>>8)&255)+30;};if(Magenta(MarkedBase[I]))ChangedForeground+=Marked[I]!=MarkedBase[I];else Smear+=Magenta(Marked[I]);}Require(ChangedForeground==0&&Smear==0,"displaced linear source footprint never imports nearer magenta hull strip");ProtectMarker=false;auto Unprotected=Render(nullptr);int ControlSmear=0;for(size_t I=0;I<Unprotected.size();++I){auto Magenta=[](DWORD C){return int((C>>16)&255)>int((C>>8)&255)+30&&int(C&255)>int((C>>8)&255)+30;};ControlSmear+=!Magenta(MarkedBase[I])&&Magenta(Unprotected[I]);}printf("Source-footprint negative-control smear pixels: %d\n",ControlSmear);Require(ControlSmear>0,"source-footprint test actually crosses magenta source when its depth is removed");ProtectMarker=true;Marker=-1;
 GlowOn=true;Render(Side?"combined_side":"combined_front");}
 std::vector<FShipWarpVertex> Narrow,Wide;BuildShipWarpNose(Narrow,{0,0,0},{1,0,0},{0,1,0},{0,0,1},4,3,1);BuildShipWarpNose(Wide,{0,0,0},{1,0,0},{0,1,0},{0,0,1},4,3,2);bool Correct=Narrow.size()==Wide.size();for(size_t I=0;I<Narrow.size();++I)Correct=Correct&&fabs(Wide[I].Position[0]-2*Narrow[I].Position[0])<.00001f&&fabs(Wide[I].Position[1]-2*Narrow[I].Position[1])<.00001f&&Wide[I].Position[2]==Narrow[I].Position[2];Require(Correct,"nose WidthScale2 doubles transverse size without changing apex depth or vertex count");
 puts("PASS all ship warp checks");return 0;}
