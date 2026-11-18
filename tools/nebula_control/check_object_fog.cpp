// Real RP9 route + D3D9 readback. Never launches the game.
#include "RP9Ex.h"
#include "dacom_iids.h"
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <cstdarg>
#include <crtdbg.h>
#include <algorithm>
#include <cmath>
#include <vector>
static void R(bool ok,const char* m){if(!ok){printf("FAIL: %s\n",m);exit(3);}}
static void Check(HRESULT h,int line){if(FAILED(h)){printf("HRESULT %08lx at line %d\n",h,line);exit(2);}}
#define C(call) Check((call),__LINE__)
static void __cdecl Dump(int,const char* format,...){va_list a;va_start(a,format);vprintf(format,a);va_end(a);puts("");}
struct Handle{IDirect3DTexture9* Texture=nullptr;unsigned long Extra=0;};
struct V{float x,y,z,nx,ny,nz,u,v;};
static DWORD bits(float f){DWORD d;memcpy(&d,&f,4);return d;}
int main(int argc,char**argv){
 R(argc==2,"preview filename required");setvbuf(stdout,nullptr,_IONBF,0);
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 FDUMP=&Dump;_set_abort_behavior(0,_WRITE_ABORT_MSG|_CALL_REPORTFAULT);
 for(int t:{_CRT_WARN,_CRT_ERROR,_CRT_ASSERT}){_CrtSetReportMode(t,_CRTDBG_MODE_FILE);_CrtSetReportFile(t,_CRTDBG_FILE_STDERR);}
 HWND w=CreateWindowA("STATIC","fog fixture",WS_POPUP,0,0,900,600,0,0,GetModuleHandle(0),0);
 auto*a=Direct3DCreate9(D3D_SDK_VERSION);R(a!=nullptr,"D3D9 available");IDirect3DDevice9*d=nullptr;
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=900;pp.BackBufferHeight=600;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 C(a->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto*p=new FDirectX9();p->Outer_=&p->Inner_;p->Device_=d;p->DeviceReady_=1;auto*e=p->Ex_;
 e->bSurfaceConfigRead=true;e->bSurfaceEnabled=true;
 D3DXMATRIX id;D3DXMatrixIdentity(&id);
 memcpy(p->Transforms_.World.Values,&id,64);memcpy(p->Transforms_.View.Values,&id,64);memcpy(p->Transforms_.Projection.Values,&id,64);
 d->SetTransform(D3DTS_WORLD,&id);d->SetTransform(D3DTS_VIEW,&id);d->SetTransform(D3DTS_PROJECTION,&id);
 for(int i=0;i<8;++i)memcpy(p->DeviceStates_.TextureTransforms[i].Values,&id,64);
 auto rs=[&](unsigned s,unsigned v){p->RenderStates_.MarkDirty(s,v);C(d->SetRenderState((D3DRENDERSTATETYPE)s,v));};
 auto tss=[&](unsigned s,unsigned t,unsigned v){auto&x=p->DeviceStates_.TextureStates[s][t];x.Value=v;x.bValid=1;C(d->SetTextureStageState(s,(D3DTEXTURESTAGESTATETYPE)t,v));};
 rs(D3DRS_LIGHTING,1);rs(D3DRS_ALPHABLENDENABLE,0);rs(D3DRS_AMBIENT,0xff502800);
 rs(D3DRS_CULLMODE,D3DCULL_NONE);rs(D3DRS_ZENABLE,0);rs(D3DRS_COLORVERTEX,0);rs(D3DRS_SPECULARENABLE,0);
 rs(D3DRS_FOGENABLE,1);rs(D3DRS_FOGTABLEMODE,D3DFOG_LINEAR);rs(D3DRS_FOGVERTEXMODE,D3DFOG_NONE);
 rs(D3DRS_RANGEFOGENABLE,0);rs(D3DRS_FOGCOLOR,0xff965a14);rs(D3DRS_FOGSTART,bits(0));rs(D3DRS_FOGEND,bits(1));
 tss(0,D3DTSS_COLOROP,D3DTOP_MODULATE);tss(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);tss(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);
 tss(0,D3DTSS_ALPHAOP,D3DTOP_MODULATE);tss(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);tss(0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE);
 tss(0,D3DTSS_TEXCOORDINDEX,0);tss(0,D3DTSS_TEXTURETRANSFORMFLAGS,0);tss(1,D3DTSS_COLOROP,D3DTOP_DISABLE);tss(2,D3DTSS_COLOROP,D3DTOP_DISABLE);
 D3DMATERIAL9 mat={};mat.Diffuse={.8f,.7f,.6f,.7f};mat.Ambient={.8f,.7f,.6f,1};C(p->SetMaterial(&mat));
 Handle base;C(d->CreateTexture(4,4,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&base.Texture,0));
 D3DLOCKED_RECT lock;C(base.Texture->LockRect(0,&lock,0,0));
 for(int y=0;y<4;++y)for(int x=0;x<4;++x)((DWORD*)((char*)lock.pBits+y*lock.Pitch))[x]=0xbfa0c080;
 base.Texture->UnlockRect(0);p->DeviceStates_.TextureBindings[0]={&base,1,{}};C(d->SetTexture(0,base.Texture));
 D3DLIGHT9 light={};light.Type=D3DLIGHT_DIRECTIONAL;light.Direction={-.8f,0,.6f};light.Diffuse={1,.47f,.20f,1};
 C(p->SetLight(nullptr,&light));C(p->SetLightEnable(nullptr,1));C(p->LightManager_.Flush(d));
 const unsigned fvf=D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1;p->StreamCache_.Fvf=fvf;C(d->SetFVF(fvf));
 V q[]={{-.8f,-.8f,.5f,0,0,-1,0,1},{-.8f,.8f,.5f,0,0,-1,0,0},{.8f,-.8f,.5f,0,0,-1,1,1},{.8f,.8f,.5f,0,0,-1,1,0}};
 IDirect3DSurface9*target=nullptr,*read=nullptr;C(d->GetRenderTarget(0,&target));
 C(d->CreateOffscreenPlainSurface(900,600,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,0));
 auto sample=[&](){C(d->GetRenderTargetData(target,read));C(read->LockRect(&lock,0,D3DLOCK_READONLY));
  DWORD out=((DWORD*)((char*)lock.pBits+300*lock.Pitch))[450];read->UnlockRect();return out;};
 auto render=[&](unsigned flags,bool expected){
  p->ExSurfaceRelease();C(p->SetLocalShadowReceiver(flags));C(d->Clear(0,0,D3DCLEAR_TARGET,0xff000000,1,0));C(d->BeginScene());
  const bool active=p->ExSurfaceBegin();R(active==expected,"expected material route");
  C(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(V)));if(active)p->ExSurfaceEnd();C(d->EndScene());return sample();};
 auto delta=[](DWORD a,DWORD b){int m=0;for(int i=0;i<3;++i)m=(std::max)(m,abs(int((a>>(i*8))&255)-int((b>>(i*8))&255)));return m;};
 for(float keep:{1.f,.5f,0.f}){
  rs(D3DRS_FOGSTART,bits(keep-.5f));rs(D3DRS_FOGEND,bits(keep+.5f));
  const DWORD before=render(256,false),after=render(768,true);
  printf("Transmission %.1f native=%08lx trial=%08lx delta=%d\n",keep,before,after,delta(before,after));
  R((before>>24)==(after>>24),"authored alpha unchanged");
  if(keep==.5f)R(delta(before,after)>=5,"partial fog shows form shading");else R(delta(before,after)<=2,"clear and opaque fog endpoints unchanged");
 }
 rs(D3DRS_FOGSTART,bits(0));rs(D3DRS_FOGEND,bits(1));
 DWORD lit=0,dark=0;
 for(int side=0;side<2;++side){for(auto&v:q){v.nx=side?-.8f:.8f;v.nz=side?.6f:-.6f;}
  DWORD native=render(256,false),trial=render(768,true);
  printf("Face %d native=%08lx trial=%08lx\n",side,native,trial);
  R((native>>24)==(trial>>24),"face alpha unchanged");
  if(side){dark=trial;R(((trial>>16)&255)<((native>>16)&255),"opposite fog face darkens");}
  else {lit=trial;R(((trial>>16)&255)>((native>>16)&255),"sunward fog face brightens");}
 }
 // Opaque unscoped plain materials keep the native path. Alpha and fog-off draws do too.
 render(0,false);R(!e->bNebulaFogShape,"scope cleared after object");
 rs(D3DRS_FOGENABLE,0);render(768,false);rs(D3DRS_FOGENABLE,1);
 rs(D3DRS_ALPHABLENDENABLE,1);render(768,false);rs(D3DRS_ALPHABLENDENABLE,0);
 render(16|512,true);R(e->SurfaceDistanceTier==2,"far distance tier retains cheap trial");
 render(512,true);float constants[8]={};C(d->GetPixelShaderConstantF(107,constants,2));R(constants[0]>0 && constants[2]==1,"near native material retains cheap lighting");
 e->bWeaponGlintReceiver=true;e->WeaponGlintReceiverMask=1;
 render(512,true);C(d->GetPixelShaderConstantF(107,constants,2));R(constants[0]>0 && constants[2]==0,"existing enhanced shader receives trial");
 render(0,true);C(d->GetPixelShaderConstantF(107,constants,2));R(constants[0]==0 && constants[1]==0 && constants[2]==0,"next enhanced object has neutral trial constants");
 render(512,true);C(d->GetPixelShaderConstantF(107,constants,2));e->bWeaponGlintReceiver=false;e->WeaponGlintReceiverMask=0;
 // A light rotated in world space and the inverse view rotation must cancel.
 const float keyX=constants[4],keyY=constants[5],keyZ=constants[6];
 D3DXMATRIX rotation;D3DXMatrixRotationZ(&rotation,1.f);
 memcpy(p->Transforms_.View.Values,&rotation,64);C(d->SetTransform(D3DTS_VIEW,&rotation));
 const auto oldDirection=light.Direction;light.Direction={oldDirection.x*cosf(1.f),-oldDirection.x*sinf(1.f),oldDirection.z};
 C(p->SetLight(nullptr,&light));C(p->LightManager_.Flush(d));render(768,true);C(d->GetPixelShaderConstantF(107,constants,2));
 R(fabsf(constants[4]-keyX)<.0001f && fabsf(constants[5]-keyY)<.0001f && fabsf(constants[6]-keyZ)<.0001f,"fog light follows the view transform");
 memcpy(p->Transforms_.View.Values,&id,64);C(d->SetTransform(D3DTS_VIEW,&id));light.Direction=oldDirection;
 C(p->SetLight(nullptr,&light));C(p->LightManager_.Flush(d));
 C(p->SetLightEnable(nullptr,0));C(p->LightManager_.Flush(d));render(768,true);C(d->GetPixelShaderConstantF(107,constants,2));
 R(constants[0]==0 && constants[1]==0 && constants[2]==1,"no sun: neutral fog, no new material gloss");
 C(p->SetLightEnable(nullptr,1));C(p->LightManager_.Flush(d));
 e->bSurfaceEnabled=false;render(768,false);e->bSurfaceEnabled=true;
 // Synthetic curved surface: equal depth isolates the fog treatment, independent of density.
 std::vector<V> sphere;
 auto vertex=[](float ring,float angle){float x=sinf(ring)*cosf(angle),y=sinf(ring)*sinf(angle),z=-cosf(ring);return V{x*.78f,y*.78f,.5f,x,y,z,(x+1)*.5f,(y+1)*.5f};};
 for(int r=0;r<32;++r)for(int s=0;s<96;++s){float r0=r*1.570796327f/32,r1=(r+1)*1.570796327f/32,a0=s*6.283185307f/96,a1=(s+1)*6.283185307f/96;
  for(V v:{vertex(r0,a0),vertex(r1,a0),vertex(r1,a1),vertex(r0,a0),vertex(r1,a1),vertex(r0,a1)})sphere.push_back(v);}
 p->ExSurfaceRelease();C(d->Clear(0,0,D3DCLEAR_TARGET,0xff965a14,1,0));C(d->BeginScene());
 for(int row=0;row<2;++row)for(int col=0;col<3;++col){
  D3DVIEWPORT9 vp={DWORD(col*300),DWORD(row*300+28),300,270,0,1};C(d->SetViewport(&vp));
  const float keep=.8f-.3f*col;rs(D3DRS_FOGSTART,bits(keep-.5f));rs(D3DRS_FOGEND,bits(keep+.5f));
  C(p->SetLocalShadowReceiver(row?768:256));bool active=p->ExSurfaceBegin();R(active==(row==1),"preview route");
  C(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,(UINT)sphere.size()/3,sphere.data(),sizeof(V)));if(active)p->ExSurfaceEnd();p->ExSurfaceRelease();
 }
 D3DVIEWPORT9 full={0,0,900,600,0,1};C(d->SetViewport(&full));
 ID3DXFont*font=nullptr;C(D3DXCreateFontA(d,20,0,FW_NORMAL,1,FALSE,DEFAULT_CHARSET,OUT_DEFAULT_PRECIS,DEFAULT_QUALITY,DEFAULT_PITCH,"Arial",&font));
 for(int row=0;row<2;++row)for(int col=0;col<3;++col){char title[80];sprintf_s(title,"%s  |  fog %d%%",row?"OMEGA-15 TRIAL":"NATIVE",20+30*col);
  RECT rect={col*300+12,row*300+6,(col+1)*300,row*300+30};font->DrawTextA(nullptr,title,-1,&rect,DT_LEFT|DT_NOCLIP,0xffffffff);}
 C(d->EndScene());C(D3DXSaveSurfaceToFileA(argv[1],D3DXIFF_PNG,target,nullptr,nullptr));
 puts("PASS: object fog route, readback, endpoints, alpha, scope, far tier, light transform and fallbacks");
 return 0;
}
