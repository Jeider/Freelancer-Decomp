// Format/mipmap conversion and real D3D9 tiled alpha preview, no new shader.
#include <windows.h>
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
#include <cstring>
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
struct V{float x,y,z,w;DWORD colour;float u,v;};
int main(int argc,char** argv){
 const bool web=argc>1 && !strcmp(argv[1],"--web");
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 HWND w=CreateWindowA("STATIC","membrane DDS check",WS_POPUP,0,0,1024,768,0,0,GetModuleHandle(0),0);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 1;
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=1024;pp.BackBufferHeight=768;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 const char* names[]={"outer-v3","inner-v2","energy-v1"};
 if(web){names[0]="web-outer-v1";names[1]="web-inner-v1";}
 for(int i=0;i<(web?2:3);++i){char path[512];sprintf(path,"assets/nomad_membranes/%s.png",names[i]);
  IDirect3DTexture9* t=nullptr;UINT size=i==2?2048:1024;
  Check(D3DXCreateTextureFromFileExA(d,path,size,size,0,0,D3DFMT_DXT5,D3DPOOL_MANAGED,D3DX_FILTER_TRIANGLE|(web?0:D3DX_FILTER_MIRROR),D3DX_FILTER_BOX|(web?0:D3DX_FILTER_MIRROR),0,nullptr,nullptr,&t));
  sprintf(path,"src/obj/nomad_membrane/%s.dds",names[i]);Check(D3DXSaveTextureToFileA(path,D3DXIFF_DDS,t,nullptr));
  printf("%s %ux%u DXT5 %u mip levels\n",path,size,size,t->GetLevelCount());
  d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE|D3DFVF_TEX1);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ZENABLE,FALSE);d->SetRenderState(D3DRS_LIGHTING,FALSE);
  d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_MODULATE);d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);d->SetTextureStageState(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);
  d->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_SELECTARG1);d->SetTextureStageState(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);d->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
  d->SetSamplerState(0,D3DSAMP_ADDRESSU,web?D3DTADDRESS_WRAP:D3DTADDRESS_MIRROR);d->SetSamplerState(0,D3DSAMP_ADDRESSV,web?D3DTADDRESS_WRAP:D3DTADDRESS_MIRROR);
  for(auto state:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})d->SetSamplerState(0,state,D3DTEXF_LINEAR);
  d->Clear(0,nullptr,D3DCLEAR_TARGET,0xff151d28,1,0);Check(d->BeginScene());
  // Contrast stripes show whether generated alpha actually exposes the background.
  d->SetTexture(0,nullptr);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
  for(int x=0;x<1024;x+=64){DWORD c=(x/64)%2?0xff182c42:0xff66625c;V q[]={{float(x)-.5f,-.5f,0,1,c,0,0},{float(x+64)-.5f,-.5f,0,1,c,1,0},{float(x)-.5f,767.5f,0,1,c,0,1},{float(x+64)-.5f,767.5f,0,1,c,1,1}};Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(V)));}
  d->SetTexture(0,t);d->SetRenderState(D3DRS_ALPHABLENDENABLE,i<2);d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
  d->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_MODULATE);d->SetTextureStageState(0,D3DTSS_ALPHAARG2,D3DTA_TFACTOR);d->SetRenderState(D3DRS_TEXTUREFACTOR,web?0xccffffff:(i==0?0x99ffffff:0xffffffff));
  V q[]={{-.5f,-.5f,0,1,0xffffffff,0,0},{1023.5f,-.5f,0,1,0xffffffff,2,0},{-.5f,767.5f,0,1,0xffffffff,0,2},{1023.5f,767.5f,0,1,0xffffffff,2,2}};
  Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(V)));Check(d->EndScene());
  IDirect3DSurface9* rt=nullptr;Check(d->GetRenderTarget(0,&rt));sprintf(path,"src/obj/nomad_membrane/%s-tiled-gpu.png",names[i]);Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,rt,nullptr,nullptr));rt->Release();d->SetTexture(0,nullptr);t->Release();
 }
 d->Release();api->Release();DestroyWindow(w);puts("PASS DDS conversion and native tiled alpha draws");
}
