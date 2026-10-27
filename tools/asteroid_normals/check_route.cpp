#include "RP9Ex.h"
#include "dacom_iids.h"
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <algorithm>
static void Require(bool ok,const char* message){if(!ok){printf("FAIL: %s\n",message);exit(3);}}
static void Check(HRESULT hr){if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);}}
struct TextureHandle{IDirect3DTexture9* Texture;unsigned long Extra;};
int main(int argc,char** argv){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 HWND window=CreateWindowA("STATIC","normal route",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto* pipe=new FDirectX9();pipe->Outer_=&pipe->Inner_; // initial owner + queried interface
 pipe->Device_=d;pipe->DeviceReady_=1;auto* e=pipe->Ex_;
 e->bSurfaceConfigRead=e->bSurfaceEnabled=e->bSurfaceLogged=e->bQualityConfigRead=true;
 e->bShadowConfigRead=e->bWeaponGlintConfigRead=true;e->ShadowResolution[0]=e->ShadowResolution[1]=4096;
 D3DMATERIAL9 material={};material.Diffuse=material.Ambient={1,1,1,.35f};Check(pipe->SetMaterial(&material));
 // This is the converted 0x252 dynamic-asteroid stream, not the source 0x112.
 pipe->StreamCache_.Fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_DIFFUSE|D3DFVF_TEX2;Check(d->SetFVF(pipe->StreamCache_.Fvf));
 D3DXMATRIX id;D3DXMatrixIdentity(&id);
 memcpy(pipe->Transforms_.World.Values,&id,64);memcpy(pipe->Transforms_.View.Values,&id,64);memcpy(pipe->Transforms_.Projection.Values,&id,64);
 for(int i=0;i<8;++i)memcpy(pipe->DeviceStates_.TextureTransforms[i].Values,&id,64);
 auto rs=[&](unsigned s,unsigned v){pipe->RenderStates_.MarkDirty(s,v);};
 auto tss=[&](unsigned s,unsigned t,unsigned v){auto& a=pipe->DeviceStates_.TextureStates[s][t];a.Value=v;a.bValid=1;};
 rs(D3DRS_LIGHTING,1);rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_AMBIENT,0xff808080);
 tss(0,D3DTSS_COLOROP,D3DTOP_MODULATE);tss(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);
 tss(0,D3DTSS_ALPHAOP,D3DTOP_MODULATE);tss(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);tss(0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE);
 tss(0,D3DTSS_TEXCOORDINDEX,0);tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
 TextureHandle base={},normal={};Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&base.Texture,nullptr));
 Check(D3DXCreateTextureFromFileA(d,"src/obj/asteroid_normals/normal.dds",&normal.Texture));
 pipe->DeviceStates_.TextureBindings[0]={&base,1,{}};Check(d->SetTexture(0,base.Texture));
 Require(!pipe->ExSurfaceBegin(),"ordinary no-env/no-shadow material stays native");
 IRPNormalSurface* surface=nullptr;Check(pipe->QueryInterface(Iids::RPNormalSurface,(void**)&surface));Require(surface!=nullptr,"optional normal interface");
 Check(surface->SetNormalSurface(&normal,.65f,.9f));
 Require(pipe->ExSurfaceBegin(),"actual dynamic DcDt layout activates normal map without env/shadow");
 float style[4]={},diffuse[4]={};Check(d->GetPixelShaderConstantF(97,style,1));Check(d->GetPixelShaderConstantF(0,diffuse,1));
 Require(style[0]==.65f && diffuse[3]==.35f,"normal strength and material alpha uploaded");
 IDirect3DBaseTexture9* bound=nullptr;Check(d->GetTexture(14,&bound));Require(bound==normal.Texture,"normal bound to s14");bound->Release();
 DWORD srgb=1;Check(d->GetSamplerState(14,D3DSAMP_SRGBTEXTURE,&srgb));Require(!srgb,"normal samples stay linear");pipe->ExSurfaceEnd();
 for(int tier:{1,2}){e->SurfaceDistanceTier=tier;Require(pipe->ExSurfaceBegin(),"far tier retains normal profile");pipe->ExSurfaceEnd();}e->SurfaceDistanceTier=0;
 rs(D3DRS_ALPHABLENDENABLE,1);rs(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);rs(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
 Require(pipe->ExSurfaceBegin(),"dynamic fade still uses normal map");pipe->ExSurfaceEnd();
 rs(D3DRS_DESTBLEND,D3DBLEND_ONE);Require(!pipe->ExSurfaceBegin(),"additive particles excluded");rs(D3DRS_ALPHABLENDENABLE,0);
 Check(surface->SetNormalSurface(nullptr,.65f,.9f));Require(!pipe->ExSurfaceBegin(),"scope reset leaves following material native");
 e->bSurfaceCockpit=true;Require(pipe->ExSurfaceBegin(),"following cockpit still works");
 Check(d->GetPixelShaderConstantF(97,style,1));Require(style[0]==0,"normal constant reset for following surface");pipe->ExSurfaceEnd();e->bSurfaceCockpit=false;
 Require(surface->SetNormalSurface(&normal,std::numeric_limits<float>::quiet_NaN(),.9f)==GR_INVALID_PARMS,"invalid strength rejected");
 Require(e->SurfaceNormalHandle==nullptr,"invalid input cannot change state");
 Check(surface->SetNormalSurface(&normal,.65f,.9f));e->bSurfaceEnabled=false;Require(!pipe->ExSurfaceBegin(),"surface feature off keeps legacy fallback");
 if(argc>1 && strcmp(argv[1],"--benchmark")==0)
 {
  // CPU route/state submission only: no geometry, texture lookup, or full game loop.
  // Rotate each object so the production normal-matrix cache cannot hide the cost.
  e->bSurfaceEnabled=true;
  D3DXMATRIX poses[64];
  for(int i=0;i<64;++i){D3DXMatrixRotationYawPitchRoll(&poses[i],i*.13f,i*.07f,0);poses[i]._43=8+i*.5f;}
  LARGE_INTEGER hz,start,end;QueryPerformanceFrequency(&hz);
  std::vector<double> samples[2];
  const int repeats=3000;
  for(int round=0;round<15;++round)for(int order=0;order<2;++order)
  {
   int mode=(round+order)%2;
   QueryPerformanceCounter(&start);
   for(int i=0;i<repeats;++i)
   {
    memcpy(pipe->Transforms_.World.Values,&poses[i%64],64);
    surface->SetNormalSurface(mode?&normal:nullptr,.65f,.9f);
    bool active=pipe->ExSurfaceBegin();
    Require(active==(mode!=0),"benchmark route eligibility");
    pipe->ExSurfaceEnd();surface->SetNormalSurface(nullptr,.65f,.9f);
   }
   QueryPerformanceCounter(&end);
   if(round>=3)samples[mode].push_back(double(end.QuadPart-start.QuadPart)*1e6/hz.QuadPart/repeats);
  }
  for(int mode=0;mode<2;++mode)
  {
   auto& values=samples[mode];std::sort(values.begin(),values.end());
   printf("CPU %s: median %.3f us/object; 90 objects %.3f ms; p10 %.3f us; p90 %.3f us\n",
      mode?"normal surface":"legacy eligibility",values[values.size()/2],values[values.size()/2]*.09,
      values[(values.size()-1)/10],values[(values.size()-1)*9/10]);
  }
 }
 pipe->ExReleaseAllGpu();Require(e->SurfaceNormalHandle==nullptr,"device teardown clears borrowed handle");
 puts("PASS: production RP9 dynamic FVF, optional interface, alpha fade, linear sampler, distance, reset, fallback, teardown");
 surface->Release();pipe->Device_=nullptr;pipe->DeviceReady_=0;delete pipe;
 d->SetTexture(0,nullptr);d->SetTexture(14,nullptr);base.Texture->Release();normal.Texture->Release();d->Release();api->Release();DestroyWindow(window);
}
