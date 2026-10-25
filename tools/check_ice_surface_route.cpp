// Exercise the real RP9 route with the exact one-stage DcDt layout used by
// ast_icecrystal2; shader-only tests cannot catch an eligibility fallback.
#include "RP9Ex.h"
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <new>
static void Require(bool ok,const char* message){if(!ok){printf("FAIL: %s\n",message);exit(3);}}
static void Check(HRESULT hr){if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);}}
struct TextureHandle{IDirect3DTexture9* Texture;unsigned long Extra;};
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 HWND window=CreateWindowA("STATIC","ice route",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto* pipe=new FDirectX9();pipe->Device_=d;pipe->DeviceReady_=1;auto* e=pipe->Ex_;
 e->bSurfaceConfigRead=e->bSurfaceEnabled=e->bSurfaceLogged=e->bQualityConfigRead=true;
 e->bShadowConfigRead=e->bWeaponGlintConfigRead=true;e->ShadowResolution[0]=e->ShadowResolution[1]=4096;
 D3DMATERIAL9 material={};material.Diffuse=material.Ambient={1,1,1,1};Check(pipe->SetMaterial(&material));
 pipe->StreamCache_.Fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1;Check(d->SetFVF(pipe->StreamCache_.Fvf));
 D3DXMATRIX id;D3DXMatrixIdentity(&id);
 memcpy(pipe->Transforms_.World.Values,&id,64);memcpy(pipe->Transforms_.View.Values,&id,64);memcpy(pipe->Transforms_.Projection.Values,&id,64);
 for(int i=0;i<8;++i)memcpy(pipe->DeviceStates_.TextureTransforms[i].Values,&id,64);
 auto rs=[&](unsigned s,unsigned v){pipe->RenderStates_.MarkDirty(s,v);};
 auto tss=[&](unsigned s,unsigned t,unsigned v){auto& a=pipe->DeviceStates_.TextureStates[s][t];a.Value=v;a.bValid=1;};
 rs(D3DRS_LIGHTING,1);rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_AMBIENT,0xff808080);
 // BindDcDtTables: MODULATE(texture,diffuse) for RGB and alpha; next stage disabled.
 tss(0,D3DTSS_COLOROP,D3DTOP_MODULATE);tss(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);
 tss(0,D3DTSS_ALPHAOP,D3DTOP_MODULATE);tss(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);tss(0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE);
 tss(0,D3DTSS_TEXCOORDINDEX,0);tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
 TextureHandle base={};Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&base.Texture,nullptr));
 pipe->DeviceStates_.TextureBindings[0]={&base,1,{}};Check(d->SetTexture(0,base.Texture));
 Require(!pipe->ExSurfaceBegin(),"ordinary no-env/no-shadow material stays on native path");
 Check(pipe->SetSurfaceShader(RPSurfaceIce,0,-1));
 Require(pipe->ExSurfaceBegin(),"actual ice DcDt activates without envmap or shadow");
 float style[4]={},surface[4]={};Check(d->GetPixelShaderConstantF(96,style,1));Check(d->GetPixelShaderConstantF(4,surface,1));
 Require(style[0]==1 && style[1]>.08f && surface[2]==0,"ice parameters sent; no invented environment");
 IDirect3DBaseTexture9* layers=nullptr;Check(d->GetTexture(13,&layers));Require(layers!=nullptr,"packed layers bound");layers->Release();pipe->ExSurfaceEnd();
 e->SurfaceDistanceTier=2;Require(pipe->ExSurfaceBegin(),"far ice keeps same colour profile");pipe->ExSurfaceEnd();e->SurfaceDistanceTier=0;
 e->bIceShader=false;Require(!pipe->ExSurfaceBegin(),"ice_shader=0 restores native path");
 Require(e->SurfaceRoughness==0 && e->SurfaceEnvironment==-1,"feature off preserves authored parameters");e->bIceShader=true;
 rs(D3DRS_ALPHABLENDENABLE,1);Require(!pipe->ExSurfaceBegin(),"transparent draw excluded");rs(D3DRS_ALPHABLENDENABLE,0);
 Check(pipe->SetSurfaceShader(RPSurfaceAuto,0,-1));Require(!pipe->ExSurfaceBegin(),"scope reset cannot affect following material");
 puts("PASS: real RP9 DcDt eligibility, c96/s13, no-env, far tier, feature-off, transparent exclusion, scope reset");
 pipe->ExReleaseAllGpu();Require(!e->IceLayers && !e->bIceTextureTried,"ice resources released and retry reset");
 pipe->Device_=nullptr;pipe->DeviceReady_=0;delete pipe;
 d->SetTexture(0,nullptr);d->SetTexture(13,nullptr);base.Texture->Release();d->Release();api->Release();DestroyWindow(window);
}
