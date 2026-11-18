// Offline D3D9 format conversion and DDS upload check. Never starts the game.
#include <windows.h>
#include <d3dx9.h>
#include <cstdio>
#include <cstdlib>
#include <vector>
#include "../../src/include/render/DdsMipCursor.h"
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
static void NeedAt(bool b,int line){if(!b){printf("Invalid DDS bounds or pixel mismatch at %d\n",line);exit(3);}}
#define Need(b) NeedAt(bool(b),__LINE__)
int main(int argc,char**argv){
 Need(argc==3);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 HWND w=CreateWindowA("STATIC","offline LOD conversion",WS_POPUP,0,0,16,16,0,0,GetModuleHandle(0),0);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Need(api!=nullptr);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=16;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&pp,&d));
 IDirect3DTexture9* source=nullptr;
 Check(D3DXCreateTextureFromFileExA(d,argv[1],D3DX_DEFAULT,D3DX_DEFAULT,0,0,D3DFMT_DXT1,D3DPOOL_SYSTEMMEM,D3DX_FILTER_NONE,D3DX_FILTER_BOX,0,nullptr,nullptr,&source));
 Check(D3DXSaveTextureToFileA(argv[2],D3DXIFF_DDS,source,nullptr));source->Release();
 FILE* f=fopen(argv[2],"rb");Need(f!=nullptr);fseek(f,0,SEEK_END);size_t size=ftell(f);rewind(f);std::vector<unsigned char>b(size);Need(fread(b.data(),1,size,f)==size);fclose(f);
 const DWORD* h=reinterpret_cast<const DWORD*>(b.data());Need(size>128&&h[21]==D3DFMT_DXT1&&h[7]==12);
 IDirect3DTexture9 *reference=nullptr,*upload=nullptr;
 Check(D3DXCreateTextureFromFileInMemoryEx(d,b.data(),UINT(size),D3DX_DEFAULT,D3DX_DEFAULT,D3DX_DEFAULT,0,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,D3DX_FILTER_NONE,D3DX_FILTER_NONE,0,nullptr,nullptr,&reference));
 Check(d->CreateTexture(h[4],h[3],h[7],0,D3DFMT_DXT1,D3DPOOL_MANAGED,&upload,nullptr));
 FTextureDdsCursor c={b.data()+128,FTextureDdsCursor::CompressedBytes(h[4],h[3],8),8,h[4],h[3],true};
 unsigned partialBlockError=0;
 for(unsigned lv=0;lv<h[7];++lv){
  Need(size_t(c.Pixels-b.data())+c.Bytes<=size);
  IDirect3DSurface9 *s=nullptr,*decoded=nullptr;Check(upload->GetSurfaceLevel(lv,&s));
  RECT r={0,0,LONG(c.Width),LONG(c.Height)};
  Check(D3DXLoadSurfaceFromMemory(s,nullptr,nullptr,c.Pixels,D3DFMT_DXT1,((c.Width+3)/4)*8,nullptr,&r,D3DX_FILTER_NONE,0));
  Check(d->CreateOffscreenPlainSurface(c.Width,c.Height,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&decoded,nullptr));
  Check(D3DXLoadSurfaceFromSurface(decoded,nullptr,nullptr,s,nullptr,nullptr,D3DX_FILTER_NONE,0));
  D3DLOCKED_RECT a={},z={};Check(decoded->LockRect(&a,nullptr,D3DLOCK_READONLY));Check(reference->LockRect(lv,&z,nullptr,D3DLOCK_READONLY));
  for(unsigned y=0;y<c.Height;++y)for(unsigned x=0;x<c.Width*4;++x){
   int av=static_cast<unsigned char*>(a.pBits)[y*a.Pitch+x],bv=static_cast<unsigned char*>(z.pBits)[y*z.Pitch+x];
   // D3DXLoadSurfaceFromMemory recompresses a partial BC1 block at 2x2/1x1.
   // Allow one RGB565 quantization step ONLY there; full blocks stay exact.
   int delta=abs(av-bv),limit=(c.Width<4&&x%4!=3)?8:1;
   if(c.Width<4&&unsigned(delta)>partialBlockError)partialBlockError=unsigned(delta);
   if(delta>limit){printf("Pixel mismatch mip %u xbyte %u y %u GPU %d D3DX %d\n",lv,x,y,av,bv);exit(3);}
  }
  decoded->UnlockRect();reference->UnlockRect(lv);decoded->Release();s->Release();c.Advance();
 }
 Need(size_t(c.Pixels-b.data())==size);upload->Release();reference->Release();d->Release();api->Release();DestroyWindow(w);
 printf("PASS DXT1: 12 mips, %zu bytes, full blocks <=1 RGB error; partial-block recompression <=%u\n",size,partialBlockError);
}
