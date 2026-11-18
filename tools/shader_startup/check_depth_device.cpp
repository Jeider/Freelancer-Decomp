// Standalone probe of the installed D3D9 provider and RP9's actual depth selection.
#define NOMINMAX
#include <windows.h>
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include "depth_selection.inc"
static void Check(HRESULT hr,const char* what){if(FAILED(hr)){printf("FAIL %s: %08lx\n",what,hr);exit(2);}}
int main(int argc,char** argv){
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 if(argc!=2)return 1;
 HMODULE module=LoadLibraryExA(argv[1],nullptr,LOAD_WITH_ALTERED_SEARCH_PATH);
 if(!module){printf("FAIL load provider: %lu\n",GetLastError());return 1;}
 auto create=reinterpret_cast<IDirect3D9* (WINAPI*)(UINT)>(GetProcAddress(module,"Direct3DCreate9"));
 if(!create)return 1;IDirect3D9* api=create(D3D_SDK_VERSION);if(!api)return 1;
 D3DADAPTER_IDENTIFIER9 adapter={};Check(api->GetAdapterIdentifier(0,0,&adapter),"adapter");printf("Provider: %s\n",adapter.Description);
 D3DDISPLAYMODE mode={};Check(api->GetAdapterDisplayMode(0,&mode),"display");
 FDirectX9 pipe;pipe.D3d_=api;int z=32,s=0;
 D3DFORMAT chosen=pipe.PickDepthFormat(mode.Format,D3DFMT_A8R8G8B8,&z,&s);
 printf("RP9 selection: format=%u depth=%d stencil=%d sampled=%d\n",chosen,z,s,pipe.ExWantsIntzDepth(mode.Format,chosen));
 if(!pipe.ExWantsIntzDepth(mode.Format,chosen)){puts("FAIL RP9 selected an unsampleable depth format");return 4;}
 for(D3DFORMAT f:{D3DFMT_D32,D3DFMT_D24S8,D3DFMT_D24X8,kIntzFormat})
  printf("Format %08x surface=%08lx texture=%08lx match=%08lx\n",f,
   api->CheckDeviceFormat(0,D3DDEVTYPE_HAL,mode.Format,D3DUSAGE_DEPTHSTENCIL,D3DRTYPE_SURFACE,f),
   api->CheckDeviceFormat(0,D3DDEVTYPE_HAL,mode.Format,D3DUSAGE_DEPTHSTENCIL,D3DRTYPE_TEXTURE,f),
   api->CheckDepthStencilMatch(0,D3DDEVTYPE_HAL,mode.Format,D3DFMT_A8R8G8B8,f));
 HWND window=CreateWindowA("STATIC","depth check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 IDirect3DDevice9* dev=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&dev),"device");
 IDirect3DTexture9* depth=nullptr;IDirect3DSurface9 *surface=nullptr,*rt=nullptr,*read=nullptr;
 Check(dev->CreateTexture(64,64,1,D3DUSAGE_DEPTHSTENCIL,kIntzFormat,D3DPOOL_DEFAULT,&depth,nullptr),"INTZ texture");
 Check(depth->GetSurfaceLevel(0,&surface),"INTZ surface");Check(dev->SetDepthStencilSurface(surface),"bind INTZ");
 Check(dev->Clear(0,nullptr,D3DCLEAR_ZBUFFER,.0f,.375f,0),"clear INTZ");Check(dev->SetDepthStencilSurface(nullptr),"unbind depth");
 Check(dev->CreateRenderTarget(64,64,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&rt,nullptr),"colour");
 Check(dev->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr),"readback");
 Check(dev->SetRenderTarget(0,rt),"target");
 char const* shader="sampler2D depth:register(s0);float4 main():COLOR0{return float4(tex2Dlod(depth,float4(.5,.5,0,0)).rrr,1);}";
 ID3DXBuffer* code=nullptr;Check(D3DXCompileShader(shader,UINT(strlen(shader)),nullptr,nullptr,"main","ps_3_0",0,&code,nullptr,nullptr),"compile sample");
 IDirect3DPixelShader9* ps=nullptr;Check(dev->CreatePixelShader((DWORD*)code->GetBufferPointer(),&ps),"pixel shader");
 Check(dev->SetTexture(0,depth),"sample INTZ");dev->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_POINT);dev->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
 dev->SetRenderState(D3DRS_ZENABLE,FALSE);dev->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
 dev->SetPixelShader(ps);dev->SetFVF(D3DFVF_XYZRHW);float quad[]={-.5f,-.5f,0,1,63.5f,-.5f,0,1,-.5f,63.5f,0,1,63.5f,63.5f,0,1};
 Check(dev->BeginScene(),"begin");Check(dev->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,16),"sample draw");Check(dev->EndScene(),"end");
 Check(dev->GetRenderTargetData(rt,read),"read pixels");D3DLOCKED_RECT lock={};Check(read->LockRect(&lock,nullptr,D3DLOCK_READONLY),"lock");
 unsigned pixel=*reinterpret_cast<DWORD*>(static_cast<char*>(lock.pBits)+32*lock.Pitch+32*4);read->UnlockRect();
 printf("INTZ sample: %08x (expected RGB 5f/60)\n",pixel);bool ok=(pixel&255)>=95&&(pixel&255)<=96;
 puts(ok?"PASS depth texture clear and GPU sampling":"FAIL incorrect sampled depth");
 dev->SetTexture(0,nullptr);dev->SetPixelShader(nullptr);ps->Release();code->Release();read->Release();rt->Release();surface->Release();depth->Release();dev->Release();api->Release();DestroyWindow(window);FreeLibrary(module);
 return ok?0:3;
}
