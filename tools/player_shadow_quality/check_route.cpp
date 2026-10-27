#include "RP9Ex.h"
#include "RP9DeviceCallCache.h"
#include "dacom_iids.h"
#include "render/IRPSurfaceShader.h"
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <limits>
#include <algorithm>
static void Require(bool ok,const char* message){if(!ok){printf("FAIL: %s\n",message);exit(3);}}
static void Check(HRESULT hr){if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);}}
struct TextureHandle{IDirect3DTexture9* Texture;unsigned long Extra;};
int main(){
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
 D3DMATERIAL9 material={};material.Diffuse={1,1,1,1};material.Ambient={.1f,.1f,.1f,1};Check(pipe->SetMaterial(&material));
 // This is the converted 0x252 dynamic-asteroid stream, not the source 0x112.
 pipe->StreamCache_.Fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1;Check(d->SetFVF(pipe->StreamCache_.Fvf));
 D3DXMATRIX id;D3DXMatrixIdentity(&id);
 memcpy(pipe->Transforms_.World.Values,&id,64);memcpy(pipe->Transforms_.View.Values,&id,64);memcpy(pipe->Transforms_.Projection.Values,&id,64);
 for(int i=0;i<8;++i)memcpy(pipe->DeviceStates_.TextureTransforms[i].Values,&id,64);
 auto rs=[&](unsigned s,unsigned v){pipe->RenderStates_.MarkDirty(s,v);};
 auto tss=[&](unsigned s,unsigned t,unsigned v){auto& a=pipe->DeviceStates_.TextureStates[s][t];a.Value=v;a.bValid=1;};
 rs(D3DRS_LIGHTING,1);rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_AMBIENT,0xff808080);
 tss(0,D3DTSS_COLOROP,D3DTOP_MODULATE);tss(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);
 tss(0,D3DTSS_ALPHAOP,D3DTOP_MODULATE);tss(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);tss(0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE);
 tss(0,D3DTSS_TEXCOORDINDEX,0);tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
 TextureHandle base={};Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&base.Texture,nullptr));
 pipe->DeviceStates_.TextureBindings[0]={&base,1,{}};Check(d->SetTexture(0,base.Texture));
 e->ShadowResolution[0]=8192;e->ShadowResolution[1]=4096;
 e->ShadowSearchSamples=64;e->ShadowFilterSamples=192;
 e->ShadowWorldSearchSamples=16;e->ShadowWorldFilterSamples=32;
 // Compact test projections keep the normal-offset bias inside the unit cube.
 e->ShadowNearRadius=20;e->ShadowFarRadius=100;e->ShadowMaxLength=300;
 e->ShadowDepthSpan[0]=e->ShadowDepthSpan[1]=100;e->ShadowStrength=1;
 e->ShadowSunDirection[2]=1;e->bShadowAdaptiveQuality=false;e->ShadowLightAngle=0;
 memcpy(e->ShadowMatrices[0],&id,64);memcpy(e->ShadowMatrices[1],&id,64);
 for(auto& map:e->ShadowMaps) Check(d->CreateTexture(4,4,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,&map,nullptr));
 auto fill=[&](IDirect3DTexture9* map,float value){D3DLOCKED_RECT lock;Check(map->LockRect(0,&lock,nullptr,0));
  for(int y=0;y<4;++y)for(int x=0;x<4;++x)((float*)((char*)lock.pBits+y*lock.Pitch))[x]=value;Check(map->UnlockRect(0));};
 fill(e->ShadowMaps[0],.25f);fill(e->ShadowMaps[1],1);fill(e->ShadowMaps[2],1);e->ShadowReadyMask=7;
 D3DLOCKED_RECT lock;Check(base.Texture->LockRect(0,&lock,nullptr,0));*(DWORD*)lock.pBits=0xffffffff;base.Texture->UnlockRect(0);
 D3DLIGHT9 sun={};sun.Type=D3DLIGHT_DIRECTIONAL;sun.Direction={0,0,1};sun.Diffuse={.8f,.8f,.8f,1};
 Check(pipe->SetLight(nullptr,&sun));Check(pipe->SetLightEnable(nullptr,TRUE));
 pipe->LightManager_.Flush(d); // production Draw flushes requested lights before ExSurfaceBegin
 auto begin=[&](unsigned flags){Check(pipe->SetLocalShadowReceiver(flags));Require(pipe->ExSurfaceBegin(),"surface route active");};
 auto constant=[&](int reg,int lane){float v[4];Check(d->GetPixelShaderConstantF(reg,v,1));return v[lane];};
 begin(131);Require(e->bShadowReceiverIsPlayer && constant(60,0)==2,"player uses detailed near maps");
 Require(constant(4,3)==1,"test sun committed before draw");
 Require(constant(60,1)==1.f/8192 && constant(95,0)==1.f/4096,"player 8K / shared 4K texel sizes");
 Require(constant(72,1)==64 && constant(72,2)==192,"player full filter retained");
 IDirect3DBaseTexture9* bound=nullptr;Check(d->GetTexture(8,&bound));Require(bound==e->ShadowMaps[0],"player near texture bound");bound->Release();
 Check(d->GetTexture(12,&bound));Require(bound==e->ShadowMaps[2],"player moving-caster map bound");bound->Release();pipe->ExSurfaceEnd();
 for(unsigned flags:{1u,3u,35u,67u,129u}){
  const bool localStatic=(flags&2u)==0;
  begin(flags);Require(!e->bShadowReceiverIsPlayer && constant(60,0)==(localStatic?3:1),"static receivers opt into local near maps; NPCs stay far-only");
  Require(constant(72,1)==16 && constant(72,2)==32,"world filter capped");
  Check(d->GetTexture(8,&bound));Require(bound==(localStatic?e->ShadowMaps[0]:nullptr),"only static surfaces also bind near map");if(bound)bound->Release();
  Check(d->GetTexture(12,&bound));Require(bound==(localStatic?e->ShadowMaps[2]:nullptr),"nearby stations bind moving ship silhouettes");if(bound)bound->Release();
  if(flags==35)Require(constant(76,2)==8 && constant(76,3)==8,"NPC moderate tier retained");
  if(flags==67)Require(constant(95,2)==1,"NPC simple tier retained");
  pipe->ExSurfaceEnd();
 }
 e->ShadowSearchSamples=8;e->ShadowFilterSamples=16;begin(1);
 Require(constant(72,1)==8 && constant(72,2)==16,"world cap never raises user's lower settings");pipe->ExSurfaceEnd();
 e->ShadowSearchSamples=64;e->ShadowFilterSamples=192;
 // Render the production shader. Near map is dark, far map lit: player must see
 // the near shadow, as must nearby station pixels. NPCs must remain lit.
 struct Vertex{float x,y,z,nx,ny,nz,u,v;};
 Vertex quad[]={{-1,-1,.5,0,0,-1,0,1},{-1,1,.5,0,0,-1,0,0},{1,-1,.5,0,0,-1,1,1},
   {1,-1,.5,0,0,-1,1,1},{-1,1,.5,0,0,-1,0,0},{1,1,.5,0,0,-1,1,0}};
 d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ZENABLE,FALSE);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
 IDirect3DSurface9 *target=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&target));
 Check(d->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 auto render=[&](unsigned flags,unsigned px=32,unsigned py=32){Check(d->Clear(0,nullptr,D3DCLEAR_TARGET,0,1,0));Check(d->BeginScene());begin(flags);
  Check(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,2,quad,sizeof(Vertex)));pipe->ExSurfaceEnd();Check(d->EndScene());
  Check(d->GetRenderTargetData(target,read));Check(read->LockRect(&lock,nullptr,D3DLOCK_READONLY));
  unsigned color=((DWORD*)((char*)lock.pBits+py*lock.Pitch))[px];read->UnlockRect();return color&255;};
 unsigned player=render(131),station=render(1),npc=render(3);
 printf("Centre pixel: player %u, station %u, NPC %u\n",player,station,npc);
 Require(npc>player+80 && station==player,"GPU selects near shadows for player and nearby station, far for NPC");
 // The moving map carries ships separately from station geometry. Verify it
 // casts on the station even when both static near/far maps contain no blocker.
 fill(e->ShadowMaps[0],1);fill(e->ShadowMaps[2],.25f);
 Require(render(1)==station,"moving ship casts detailed shadow on nearby station");
 // Keep projections fixed while moving the test's radial cutoff across this
 // pixel. The default radii apply these same transitions at 120..150 metres.
 e->ShadowNearRadius=.4f;unsigned distant=render(1);
 Require(distant>station+80,"distant station pixels use shared far map");
 e->ShadowNearRadius=.555f;unsigned transition=render(1);
 Require(transition>station+10 && transition<distant-10,"station near/far transition is gradual");
 e->ShadowNearRadius=20;
 fill(e->ShadowMaps[2],1);fill(e->ShadowMaps[1],.25f);
 Require(render(3)<npc-80,"NPC far-map shadows still work");
 e->ShadowNearRadius=.4f;Require(render(1)<distant-80,"distant station far-map shadows still work");
 // A small ship-shaped moving depth footprint must retain nose/wings and
 // clear space between them on the station with soft filtering enabled.
 e->ShadowNearRadius=20;fill(e->ShadowMaps[1],1);
 pipe->ExSurfaceRelease();Rp9SetTexture(d,12,nullptr);e->ShadowMaps[2]->Release();e->ShadowMaps[2]=nullptr;
 Check(d->CreateTexture(64,64,1,0,D3DFMT_R32F,D3DPOOL_MANAGED,&e->ShadowMaps[2],nullptr));
 Check(e->ShadowMaps[2]->LockRect(0,&lock,nullptr,0));
 for(int y=0;y<64;++y)for(int x=0;x<64;++x){
  bool hull=x>=29 && x<=35 && y>=15 && y<=49,wing=x>=15 && x<=49 && y>=28 && y<=36;
  ((float*)((char*)lock.pBits+y*lock.Pitch))[x]=(hull||wing)?.25f:1.f;
 }
 e->ShadowMaps[2]->UnlockRect(0);e->ShadowResolution[0]=64;e->ShadowNearRadius=2;e->ShadowLightAngle=.5f;
 unsigned nose=render(1,32,20),wing=render(1,44,32),gap=render(1,44,20);
 printf("Station silhouette: nose %u, wing %u, clear gap %u\n",nose,wing,gap);
 Require(gap>nose+60 && gap>wing+60,"nearby station resolves ship nose, wing and silhouette gap");
 // Clear receiver state: no inheritance from the preceding player draw.
 Check(pipe->SetLocalShadowReceiver(0));Require(!e->bShadowReceiverIsPlayer && !e->bShadowReceiver,"receiver scope reset");
 // Greenhouse material selection must work without the ship-glass context,
 // and must not leak to arbitrary transparent materials after scope reset.
 e->bGlassShader=true;e->bSurfaceGlass=false;
 rs(D3DRS_ALPHABLENDENABLE,1);rs(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);rs(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
 Check(pipe->SetSurfaceShader(RPSurfaceGreenhouse,0,-1));begin(1);
 Require(constant(94,1)==2,"explicit greenhouse profile selects its own shader style");pipe->ExSurfaceEnd();
 Check(pipe->SetSurfaceShader(RPSurfaceAuto,0,-1));Require(!pipe->ExSurfaceBegin(),"greenhouse scope does not leak to other transparent materials");
 rs(D3DRS_ALPHABLENDENABLE,0);
 pipe->ExShadowRelease();Require(!e->ShadowMaps[0] && !e->ShadowMaps[1] && !e->ShadowMaps[2],"shadow teardown");
 puts("PASS: player 8K/full filter, nearby station silhouettes, radial fade, world budget, NPC tiers, scope reset, cleanup");
 read->Release();target->Release();pipe->ExReleaseAllGpu();pipe->Device_=nullptr;pipe->DeviceReady_=0;delete pipe;
 d->SetTexture(0,nullptr);base.Texture->Release();d->Release();api->Release();DestroyWindow(window);
}
