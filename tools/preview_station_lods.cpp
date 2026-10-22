// Hidden-window D3D9 geometry preview; not an in-game screenshot.
#include <windows.h>
#include <d3d9.h>
#include <d3dx9.h>
#include <cstdio>
#include <vector>
#include <cassert>
#include <cstdint>
void check(HRESULT h){if(FAILED(h)){printf("D3D error %08lx\n",h);ExitProcess(1);}}
int main(int argc,char** argv){
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);assert(api);
 HWND w=CreateWindowA("STATIC","LOD geometry preview",WS_POPUP,0,0,32,32,0,0,GetModuleHandle(0),0);
 D3DPRESENT_PARAMETERS p={};p.Windowed=TRUE;p.SwapEffect=D3DSWAPEFFECT_DISCARD;
 p.BackBufferWidth=1536;p.BackBufferHeight=1024;p.BackBufferFormat=D3DFMT_A8R8G8B8;
 p.EnableAutoDepthStencil=TRUE;p.AutoDepthStencilFormat=D3DFMT_D24X8;
 IDirect3DDevice9* d=0;check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_SOFTWARE_VERTEXPROCESSING,&p,&d));
 check(d->Clear(0,0,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff18212b,1,0));
 d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_LIGHTING,TRUE);
 d->SetRenderState(D3DRS_AMBIENT,0xff505050);d->SetRenderState(D3DRS_NORMALIZENORMALS,TRUE);
 d->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1);
 D3DLIGHT9 light={};light.Type=D3DLIGHT_DIRECTIONAL;light.Direction={-.5f,-.6f,1};
 light.Diffuse={.8f,.8f,.8f,1};d->SetLight(0,&light);d->LightEnable(0,TRUE);
 D3DXMATRIX identity,proj;D3DXMatrixIdentity(&identity);d->SetTransform(D3DTS_WORLD,&identity);
 const char* prefix=argc>1 ? argv[1] : "src/obj/lod_preview";
 const char* output=argc>2 ? argv[2] : "bin/generated_station_lods/geometry_comparison.png";
 D3DXVECTOR3 center(0,0,0);float span=1;
 {
  char file[500];sprintf(file,"%s_0.vms",prefix);FILE* f=fopen(file,"rb");assert(f);
  fseek(f,0,SEEK_END);long len=ftell(f);rewind(f);std::vector<unsigned char>b(len);assert(fread(b.data(),1,len,f)==size_t(len));fclose(f);
  unsigned group=*(uint16_t*)(b.data()+8),count=*(uint16_t*)(b.data()+10),nv=*(uint16_t*)(b.data()+14);
  auto* v=(float*)(b.data()+16+12*group+2*count);
  D3DXVECTOR3 lo(v[0],v[1],v[2]),hi=lo;
  for(unsigned i=0;i<nv;i++)for(unsigned j=0;j<3;j++){if(v[i*8+j]<lo[j])lo[j]=v[i*8+j];if(v[i*8+j]>hi[j])hi[j]=v[i*8+j];}
  center=(lo+hi)*.5f;span=max(hi.x-lo.x,max(hi.y-lo.y,hi.z-lo.z));
 }
 D3DXMatrixOrthoLH(&proj,span*1.5f,span*1.5f,1,span*12);d->SetTransform(D3DTS_PROJECTION,&proj);
 check(d->BeginScene());
 for(int row=0;row<2;row++)for(int lod=0;lod<3;lod++){
  char file[500];sprintf(file,"%s_%d.vms",prefix,lod);FILE* f=fopen(file,"rb");assert(f);
  fseek(f,0,SEEK_END);long len=ftell(f);rewind(f);std::vector<unsigned char>b(len);assert(fread(b.data(),1,len,f)==size_t(len));fclose(f);
  auto u16=[&](int o){return *(uint16_t*)(b.data()+o);};auto u32=[&](int o){return *(uint32_t*)(b.data()+o);};
  D3DVIEWPORT9 viewport={DWORD(lod*512),DWORD(row*512),512,512,0,1};d->SetViewport(&viewport);
  D3DXVECTOR3 target=center,eye=center+(row ? D3DXVECTOR3(-1,.9f,1.6f) : D3DXVECTOR3(1,.9f,-1.5f))*span,up(0,1,0);
  D3DXMATRIX view;D3DXMatrixLookAtLH(&view,&eye,&target,&up);d->SetTransform(D3DTS_VIEW,&view);
  unsigned groups=u16(8),count=u16(10),index=16+groups*12,vertex=index+count*2;
  for(unsigned g=0;g<groups;g++){
   unsigned offset=16+12*g,mat=u32(offset),lo=u16(offset+4),hi=u16(offset+6),n=u16(offset+8);
   D3DMATERIAL9 m={};m.Diffuse={.4f+((mat>>16)&63)/180.f,.4f+((mat>>8)&63)/180.f,.4f+(mat&63)/180.f,1};
   m.Ambient=m.Diffuse;d->SetMaterial(&m);
   check(d->DrawIndexedPrimitiveUP(D3DPT_TRIANGLELIST,0,hi-lo+1,n/3,b.data()+index,D3DFMT_INDEX16,b.data()+vertex+lo*32,32));index+=n*2;
  }
 }
 check(d->EndScene());IDirect3DSurface9* surface=0;check(d->GetRenderTarget(0,&surface));
 check(D3DXSaveSurfaceToFileA(output,D3DXIFF_PNG,surface,0,0));
 surface->Release();d->Release();api->Release();DestroyWindow(w);puts("Saved geometry_comparison.png: LOD0/1/2, two camera angles");
}
