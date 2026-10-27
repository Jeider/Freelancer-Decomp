// GPU regression: a background halo may only touch pixels with clear depth.
#include <windows.h>
#include <d3d9.h>
#include <cassert>
#include <cstdio>
#include <cstdlib>
#include <initializer_list>
static void Check(HRESULT h){if(FAILED(h)){printf("D3D9 error %08lx\n",h);exit(2);}}
struct Vertex {float x,y,z;DWORD colour;};
int main(){
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 HWND w=CreateWindowA("STATIC","background halo check",WS_POPUP,0,0,64,64,0,0,GetModuleHandle(0),0);
 auto*api=Direct3DCreate9(D3D_SDK_VERSION);assert(api);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
 IDirect3DDevice9*d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 D3DMATRIX m={};m._11=m._22=m._33=m._44=1;
 for(auto t:{D3DTS_WORLD,D3DTS_VIEW,D3DTS_PROJECTION})Check(d->SetTransform(t,&m));
 Check(d->SetFVF(D3DFVF_XYZ|D3DFVF_DIFFUSE));
 Check(d->SetRenderState(D3DRS_LIGHTING,FALSE));Check(d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));
 Check(d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1));
 Check(d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE));
 auto quad=[&](float left,float right,float z,DWORD colour){
  Vertex q[]={{left,-1,z,colour},{left,1,z,colour},{right,-1,z,colour},{right,1,z,colour}};
  Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));
 };
 IDirect3DSurface9 *rt=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&rt));
 Check(d->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 auto sample=[&](int x){Check(d->GetRenderTargetData(rt,read));D3DLOCKED_RECT l;
  Check(read->LockRect(&l,nullptr,D3DLOCK_READONLY));DWORD c=((DWORD*)((char*)l.pBits+32*l.Pitch))[x];
  read->UnlockRect();return c&0xffffff;
 };
 for(float objectZ:{.1f,.7f,.999f}){
  D3DVIEWPORT9 vp={0,0,64,64,0,1};Check(d->SetViewport(&vp));
  Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff202020,1,0));Check(d->BeginScene());
  Check(d->SetRenderState(D3DRS_ZENABLE,TRUE));Check(d->SetRenderState(D3DRS_ZWRITEENABLE,TRUE));
  Check(d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESS));Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE));
  quad(-1,0,objectZ,0xff204080);
  // Production halo: depth range [1,1], LESS_EQUAL, no depth writes.
  vp.MinZ=vp.MaxZ=1;Check(d->SetViewport(&vp));
  Check(d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL));Check(d->SetRenderState(D3DRS_ZWRITEENABLE,FALSE));
  Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,TRUE));
  Check(d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_ONE));Check(d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_ONE));
  quad(-1,1,.3f,0xff604010);Check(d->EndScene());
  assert(sample(16)==0x204080); // Foreground colour is unchanged.
  assert(sample(48)==0x806030); // Background fog receives the glow.
  // Later geometry (cockpit/effects) must not be covered by the halo.
  vp.MinZ=0;Check(d->SetViewport(&vp));Check(d->BeginScene());
  Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE));quad(0,1,.9f,0xff309050);
  Check(d->EndScene());assert(sample(48)==0x309050);
 }
 puts("PASS: D3D9 background halo preserves near/far silhouettes; later foreground remains visible");
 read->Release();rt->Release();d->Release();api->Release();DestroyWindow(w);
}
