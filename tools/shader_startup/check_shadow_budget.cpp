// Standalone allocation probe: the game's dgVoodoo, exact high-quality map sizes.
#define NOMINMAX
#include <windows.h>
#include <d3d9.h>
#include <dxgi.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
static void Check(HRESULT hr,const char* label){if(FAILED(hr)){printf("FAIL %s: %08lx\n",label,hr);exit(2);}}
int main(){
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);setvbuf(stdout,nullptr,_IONBF,0);
 IDXGIFactory* factory=nullptr;Check(CreateDXGIFactory(__uuidof(IDXGIFactory),(void**)&factory),"DXGI factory");
 IDXGIAdapter* physical=nullptr;Check(factory->EnumAdapters(0,&physical),"physical adapter");DXGI_ADAPTER_DESC desc={};
 Check(physical->GetDesc(&desc),"physical memory");printf("DXGI-reported VRAM (32-bit API, may be capped): %llu MiB\n",(unsigned long long)desc.DedicatedVideoMemory/1024/1024);
 physical->Release();factory->Release();
 HMODULE module=LoadLibraryA("D3D9.dll");if(!module)return 1;
 auto create=reinterpret_cast<IDirect3D9* (WINAPI*)(UINT)>(GetProcAddress(module,"Direct3DCreate9"));
 auto* api=create(D3D_SDK_VERSION);if(!api)return 1;
 D3DADAPTER_IDENTIFIER9 adapter={};Check(api->GetAdapterIdentifier(0,0,&adapter),"adapter");printf("Provider: %s\n",adapter.Description);
 HWND window=CreateWindowA("STATIC","shadow budget check",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 IDirect3DDevice9* dev=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&dev),"device");
 printf("D3D9 available before maps: %u MiB\n",dev->GetAvailableTextureMem()/1024/1024);
 unsigned nearSize=8192,farSize=4096;IDirect3DTexture9* maps[3]={};IDirect3DSurface9* depth=nullptr;
 HRESULT hr=S_OK;
 for(;;){
  for(unsigned i=0;i<2&&SUCCEEDED(hr);++i)hr=dev->CreateTexture(i?farSize:nearSize,i?farSize:nearSize,1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&maps[i],nullptr);
  if(SUCCEEDED(hr))hr=dev->CreateDepthStencilSurface(nearSize,nearSize,D3DFMT_D24S8,D3DMULTISAMPLE_NONE,0,FALSE,&depth,nullptr);
  if(SUCCEEDED(hr)||nearSize<=1024)break;
  printf("Allocation failed at %u/%u: %08lx\n",nearSize,farSize,hr);
  for(auto*& map:maps)if(map){map->Release();map=nullptr;}if(depth){depth->Release();depth=nullptr;}
  nearSize=nearSize/2<1024?1024:nearSize/2;farSize=farSize/2<1024?1024:farSize/2;hr=S_OK;
 }
 Check(hr,"base shadow maps");
 hr=dev->CreateTexture(nearSize,nearSize,1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&maps[2],nullptr);
 printf("Near moving-caster map: %08lx\n",hr);
 IDirect3DTexture9* station=nullptr;unsigned available=dev->GetAvailableTextureMem(),required=farSize*farSize*4u;
 bool cacheHeadroom=!available||available>=required+128u*1024u*1024u;
 printf("Static-cache headroom: %u MiB, permitted=%d\n",available/1024/1024,cacheHeadroom);
 HRESULT cache=cacheHeadroom?dev->CreateTexture(farSize,farSize,1,D3DUSAGE_RENDERTARGET,D3DFMT_R32F,D3DPOOL_DEFAULT,&station,nullptr):E_OUTOFMEMORY;
 bool full=nearSize==8192&&farSize==4096&&SUCCEEDED(hr)&&SUCCEEDED(cache);
 if(full){
  // Bind and clear every actual map, then reserve 512 MiB for other scene resources.
  for(auto* map:maps){IDirect3DSurface9* target=nullptr;Check(map->GetSurfaceLevel(0,&target),"map surface");Check(dev->SetRenderTarget(0,target),"map target");Check(dev->SetDepthStencilSurface(depth),"map depth");Check(dev->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xffffffff,1,0),"map clear");target->Release();}
  std::vector<IDirect3DTexture9*> scene;
  for(int i=0;i<8;++i){IDirect3DTexture9* t=nullptr;Check(dev->CreateTexture(4096,4096,1,D3DUSAGE_RENDERTARGET,D3DFMT_A8R8G8B8,D3DPOOL_DEFAULT,&t,nullptr),"scene headroom");scene.push_back(t);}
  printf("Available with full maps + 512 MiB scene reserve: %u MiB\n",dev->GetAvailableTextureMem()/1024/1024);
  for(auto* t:scene)t->Release();
 }
 printf("RESULT near=%u far=%u static=%d full=%d\n",nearSize,farSize,SUCCEEDED(cache)?1:0,full?1:0);
 dev->SetDepthStencilSurface(nullptr);if(station)station->Release();for(auto* map:maps)if(map)map->Release();if(depth)depth->Release();dev->Release();api->Release();DestroyWindow(window);FreeLibrary(module);
 return 0;
}
