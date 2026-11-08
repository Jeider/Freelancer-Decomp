// No ReShade, neural host or NVIDIA runtime: production color shader on native D3D9.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <d3d9.h>
#include <d3dx9.h>
#include <wrl/client.h>
#include <cstdio>
#include <cmath>
#include <cstdlib>
#include "ColorGradeShader.h"
using Microsoft::WRL::ComPtr;
void Check(HRESULT h){if(FAILED(h)){printf("FAIL HRESULT %08lx\n",h);exit(1);}}
float Clamp(float v){return v<0?0:v>1?1:v;}
DWORD Expected(DWORD pixel,int preset){
 if(!preset)return pixel;
 float c[3]={float((pixel>>16)&255)/255,float((pixel>>8)&255)/255,float(pixel&255)/255};
 float luma=.2126f*c[0]+.7152f*c[1]+.0722f*c[2];
 float tint[3]={};if(preset==2){tint[0]=.018f;tint[1]=.004f;tint[2]=-.014f;}
 if(preset==3){tint[0]=-.012f;tint[1]=.003f;tint[2]=.018f;}
 DWORD result=pixel&0xff000000;
 for(int i=0;i<3;i++){
  float v=Clamp(luma+(c[i]-luma)*(preset==1?1.06f:.98f));
  v+=(preset==1?.12f:.16f)*v*(1-v)*(2*v-1);
  v+=4*luma*(1-luma)*tint[i];result|=DWORD(lround(255*Clamp(v)))<<(16-i*8);
 }return result;
}
int main(){
 constexpr int W=128,H=64;
 WNDCLASSW wc={};wc.lpfnWndProc=DefWindowProcW;wc.hInstance=GetModuleHandleW(nullptr);wc.lpszClassName=L"ColorGradeProbe";
 RegisterClassW(&wc);HWND window=CreateWindowW(wc.lpszClassName,L"Color grading test",WS_POPUP,0,0,W,H,nullptr,nullptr,wc.hInstance,nullptr);
 ComPtr<IDirect3D9> api;api.Attach(Direct3DCreate9(D3D_SDK_VERSION));
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;pp.BackBufferWidth=W;pp.BackBufferHeight=H;
 ComPtr<IDirect3DDevice9> d;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 ComPtr<IDirect3DSurface9> target,read;ComPtr<IDirect3DTexture9> scene;
 Check(d->CreateRenderTarget(W,H,D3DFMT_A8R8G8B8,D3DMULTISAMPLE_NONE,0,FALSE,&target,nullptr));
 Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 Check(d->CreateTexture(W,H,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&scene,nullptr));
 DWORD pixels[W*H];for(int y=0;y<H;y++)for(int x=0;x<W;x++)pixels[y*W+x]=D3DCOLOR_ARGB(127,x*255/(W-1),y*255/(H-1),(x+y)*255/(W+H-2));
 pixels[W*H-1]=0x7fffffff;pixels[0]=0x7f000000;
 D3DLOCKED_RECT locked;Check(scene->LockRect(0,&locked,nullptr,0));
 for(int y=0;y<H;y++)memcpy(static_cast<char*>(locked.pBits)+y*locked.Pitch,pixels+y*W,W*4);scene->UnlockRect(0);
 ComPtr<ID3DXBuffer> code,errors;HRESULT h=D3DXCompileShader(ColorGradeShader,sizeof(ColorGradeShader)-1,nullptr,nullptr,"PSMain","ps_3_0",0,&code,&errors,nullptr);
 if(FAILED(h)&&errors)puts(static_cast<char*>(errors->GetBufferPointer()));Check(h);
 ComPtr<IDirect3DPixelShader9> ps;Check(d->CreatePixelShader(static_cast<DWORD*>(code->GetBufferPointer()),&ps));
 struct V{float x,y,z,w,u,v;};V quad[]={{-.5f,-.5f,0,1,0,0},{W-.5f,-.5f,0,1,1,0},{-.5f,H-.5f,0,1,0,1},{W-.5f,H-.5f,0,1,1,1}};
 d->SetRenderTarget(0,target.Get());d->SetDepthStencilSurface(nullptr);d->SetVertexShader(nullptr);d->SetFVF(D3DFVF_XYZRHW|D3DFVF_TEX1);
 d->SetRenderState(D3DRS_ZENABLE,FALSE);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
 d->SetRenderState(D3DRS_SRGBWRITEENABLE,FALSE);d->SetTexture(0,scene.Get());d->SetSamplerState(0,D3DSAMP_SRGBTEXTURE,FALSE);
 d->SetSamplerState(0,D3DSAMP_MINFILTER,D3DTEXF_POINT);d->SetSamplerState(0,D3DSAMP_MAGFILTER,D3DTEXF_POINT);
 for(int preset=0;preset<4;preset++){
  float constants[4]={float(preset),0,0,0};d->SetPixelShader(ps.Get());d->SetPixelShaderConstantF(1,constants,1);
  Check(d->BeginScene());Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(V)));Check(d->EndScene());
  Check(d->GetRenderTargetData(target.Get(),read.Get()));Check(read->LockRect(&locked,nullptr,D3DLOCK_READONLY));unsigned changed=0;
  for(int y=0;y<H;y++)for(int x=0;x<W;x++){
   DWORD pixel=*reinterpret_cast<DWORD*>(static_cast<char*>(locked.pBits)+y*locked.Pitch+4*x),expected=Expected(pixels[y*W+x],preset);
   for(int shift=0;shift<=24;shift+=8)if(abs(int((pixel>>shift)&255)-int((expected>>shift)&255))>1){printf("FAIL preset %d pixel %d,%d\n",preset,x,y);return 2;}
   changed+=pixel!=pixels[y*W+x];
  }read->UnlockRect();if(preset&&changed<1000)return 3;
  // Native UI added after color grading remains pixel-exact.
  D3DRECT ui={0,0,16,16};Check(d->Clear(1,&ui,D3DCLEAR_TARGET,0xffff00ff,1,0));
  Check(d->GetRenderTargetData(target.Get(),read.Get()));Check(read->LockRect(&locked,nullptr,D3DLOCK_READONLY));
  if(*static_cast<DWORD*>(locked.pBits)!=0xffff00ff)return 4;read->UnlockRect();
  printf("PASS native D3D9 preset %d, CPU reference, alpha, black/white endpoints and UI\n",preset);
 }
 HMODULE dxgi=GetModuleHandleW(L"dxgi.dll");
 if(GetModuleHandleW(L"fl_base_neural.addon32")||(dxgi&&GetProcAddress(dxgi,"ReShadeRegisterAddon")))return 5;
 DestroyWindow(window);puts("PASS color grading without ReShade or DLSS");
}
