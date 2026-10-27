// Real D3D9/SM3 checks and renders of the three actual ku_tgk asteroid meshes.
#include "RP9ShaderCache.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
static void Require(bool ok,const char* text){if(!ok){printf("FAIL: %s\n",text);exit(3);}}
static void Check(HRESULT hr){if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);}}
static std::string Read(const char* path){FILE* f=fopen(path,"rb");Require(f!=nullptr,path);std::string s;
 char b[4096];size_t n;while((n=fread(b,1,sizeof(b),f)))s.append(b,n);fclose(f);return s;}
static std::vector<unsigned char> Compile(std::string s,const char* entry,const char* profile){
 std::vector<unsigned char> code;std::string errors;bool hit=false,stored=false;
 auto hr=Rp9ShaderCache::Compile(s,nullptr,entry,profile,0,&code,&errors,&hit,&stored);
 if(!errors.empty())puts(errors.c_str());Check(hr);printf("%s %s: %s, %zu bytes\n",entry,profile,hit?"cache":"compiled",code.size());return code;}
struct Vertex{float x,y,z,nx,ny,nz,u,v;};
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 const int W=512,H=512;
 HWND window=CreateWindowA("STATIC","normal checks",WS_POPUP,0,0,W,H,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=W;pp.BackBufferHeight=H;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto source=Read("DATA_EXTRA/SHADERS/surface_material.hlsl");
 auto vsCode=Compile(source,"VSMain","vs_3_0");
 auto psCode=Compile("#define SURFACE_NO_SHADOW 1\n"+source,"PSMain","ps_3_0");
 auto oldCode=Compile("#define SURFACE_NO_SHADOW 1\n"+Read("src/obj/asteroid_normals/baseline.hlsl"),"PSMain","ps_3_0");
 auto instanced=Compile("#define SURFACE_INSTANCED 1\n"+source,"VSMain","vs_3_0");
 IDirect3DVertexShader9* ivs=nullptr;Check(d->CreateVertexShader((DWORD*)instanced.data(),&ivs));ivs->Release();
 for(const char* tier:{"","#define SURFACE_NO_SHADOW 1\n","#define SURFACE_LOW_DETAIL 1\n"})
  for(const char* cube:{"","#define SURFACE_ENV_CUBE 1\n"}){
   auto code=Compile(std::string(tier)+cube+source,"PSMain","ps_3_0");
   IDirect3DPixelShader9* candidate=nullptr;Check(d->CreatePixelShader((DWORD*)code.data(),&candidate));candidate->Release();}
 puts("PASS: all production shader variants compile and create on D3D9");
 IDirect3DVertexShader9* vs=nullptr;IDirect3DPixelShader9 *ps=nullptr,*oldPs=nullptr;
 Check(d->CreateVertexShader((DWORD*)vsCode.data(),&vs));Check(d->CreatePixelShader((DWORD*)psCode.data(),&ps));
 Check(d->CreatePixelShader((DWORD*)oldCode.data(),&oldPs));
 IDirect3DTexture9 *base=nullptr,*normal=nullptr,*ice=nullptr,*white=nullptr,*slope=nullptr;
 Check(D3DXCreateTextureFromFileA(d,"src/obj/asteroid_normals/base.dds",&base));
 Check(D3DXCreateTextureFromFileA(d,"src/obj/asteroid_normals/normal.dds",&normal));
 Require(normal->GetLevelCount()==11,"complete normal mip chain");
 Check(D3DXCreateTextureFromFileA(d,"DATA_EXTRA/TEXTURES/ice_layers.dds",&ice));
 Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&white,nullptr));
 Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&slope,nullptr));
 D3DLOCKED_RECT lock;Check(white->LockRect(0,&lock,nullptr,0));*(DWORD*)lock.pBits=0xffffffff;white->UnlockRect(0);
 Check(slope->LockRect(0,&lock,nullptr,0));*(DWORD*)lock.pBits=0xffcc80e6;slope->UnlockRect(0);
 d->SetTexture(0,base);d->SetTexture(10,white);d->SetTexture(13,ice);d->SetTexture(14,normal);
 for(int slot:{0,10,13,14})for(auto state:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})d->SetSamplerState(slot,state,D3DTEXF_LINEAR);
 d->SetVertexShader(vs);d->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1);
 d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
 d->SetRenderState(D3DRS_ZENABLE,TRUE);d->SetRenderState(D3DRS_ZWRITEENABLE,TRUE);
 IDirect3DSurface9 *rt=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&rt));
 Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 float pc[98*4]={},vc[68]={};D3DXMATRIX identity;D3DXMatrixIdentity(&identity);
 for(int i=0;i<4;++i)memcpy(vc+i*16,&identity,64);
 pc[0]=pc[1]=pc[2]=pc[3]=1;pc[4]=pc[5]=pc[6]=.15f;
 pc[12]=pc[13]=pc[14]=.04f;pc[15]=.9f;pc[16]=1;pc[19]=1;
 pc[28]=pc[29]=4;pc[31]=-1;memcpy(pc+32,&identity,64);
 pc[51]=3;pc[52]=.6f;pc[53]=-.3f;pc[54]=1;pc[56]=pc[57]=pc[58]=.7f;pc[60]=pc[61]=pc[62]=.7f;
 pc[300]=1.35f;pc[301]=.9f;pc[302]=.8f;pc[303]=1;
 pc[385]=.09f;pc[386]=.65f;pc[387]=.22f;
 Vertex quad[]={{-1,-1,.5,0,0,-1,0,1},{-1,1,.5,0,0,-1,0,0},{1,-1,.5,0,0,-1,1,1},
 {1,-1,.5,0,0,-1,1,1},{-1,1,.5,0,0,-1,0,0},{1,1,.5,0,0,-1,1,0}};
 auto pixels=[&](){Check(d->GetRenderTargetData(rt,read));Check(read->LockRect(&lock,nullptr,D3DLOCK_READONLY));
  std::vector<DWORD> p(W*H);for(int y=0;y<H;++y)memcpy(p.data()+y*W,(char*)lock.pBits+y*lock.Pitch,W*4);read->UnlockRect();return p;};
 auto render=[&](IDirect3DPixelShader9* shader,const Vertex* vertices,size_t count){
  Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff08101a,1,0));Check(d->BeginScene());
  Check(d->SetPixelShader(shader));Check(d->SetVertexShaderConstantF(0,vc,17));Check(d->SetPixelShaderConstantF(0,pc,98));
  Check(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,(UINT)(count/3),vertices,sizeof(Vertex)));Check(d->EndScene());return pixels();};
 auto delta=[&](const std::vector<DWORD>& a,const std::vector<DWORD>& b){size_t changed=0;unsigned worst=0;
  for(size_t i=0;i<a.size();++i){if(a[i]!=b[i])++changed;for(int s:{0,8,16,24})worst=std::max(worst,(unsigned)abs(int((a[i]>>s)&255)-int((b[i]>>s)&255)));}
  return std::make_pair(changed,worst);};
 for(int style=0;style<4;++style){
  pc[376]=style==1?1.f:0.f;pc[377]=style==2?1.f:0.f;pc[378]=1.5f;pc[379]=.65f;pc[384]=style==3?1.f:0.f;
  auto before=render(oldPs,quad,6),after=render(ps,quad,6);
  Require(delta(before,after).second<=1,"ordinary/cockpit/glass/ice regression");}
 puts("PASS: ordinary, cockpit, glass and ice unchanged within 1/255");pc[376]=pc[377]=pc[384]=0;
 auto plain=render(ps,quad,6);pc[388]=.65f;auto detailed=render(ps,quad,6);
 Require(delta(plain,detailed).first>W*H/2,"generated normal changes directional lighting");
 pc[3]=.25f;auto faded=render(ps,quad,6);for(auto p:faded)Require(abs(int(p>>24)-64)<=1,"normal-mapped alpha preserved");
 pc[23]=3;pc[20]=0;pc[21]=.1f;pc[24]=.1f;pc[25]=.2f;pc[26]=.3f;
 auto fog=render(ps,quad,6);for(auto p:fog)Require(abs(int((p>>16)&255)-26)<=1 && abs(int((p>>8)&255)-51)<=1 && abs(int(p&255)-77)<=1,"native fog retained");
 pc[23]=0;pc[3]=1;
 d->SetTexture(0,white);d->SetTexture(14,slope);pc[388]=1;pc[52]=-.8f;pc[53]=0;
 auto regular=render(ps,quad,6);Vertex mirrored[6];memcpy(mirrored,quad,sizeof(quad));for(auto& v:mirrored)v.u=1-v.u;
 auto mirror=render(ps,mirrored,6);Require((regular[W*H/2]&255)>(mirror[W*H/2]&255)+40,"mirrored U reverses tangent slope");
 for(auto& v:mirrored)v.u=v.v=0;auto degenerate=render(ps,mirrored,6);pc[388]=0;
 Require(delta(degenerate,render(ps,mirrored,6)).second<=1,"degenerate UVs retain geometric normal");
 puts("PASS: lighting, alpha, fog, mirrored and degenerate UVs");
 pc[388]=.65f;pc[19]=0;auto ambient=render(ps,quad,6);pc[0]=pc[1]=pc[2]=.15f;
 Require(delta(ambient,render(ps,quad,6)).second<=1,"planetary direct-light mask preserves ambient");
 pc[0]=pc[1]=pc[2]=1;pc[19]=1;
 d->SetTexture(0,base);d->SetTexture(14,normal);pc[52]=.6f;pc[53]=-.3f;
 for(char suffix:{'a','b','c'}){
  char path[200];sprintf(path,"src/obj/asteroid_normals/mesh_%c.bin",suffix);auto bytes=Read(path);
  std::vector<Vertex> mesh(bytes.size()/sizeof(Vertex));memcpy(mesh.data(),bytes.data(),bytes.size());
  for(int pose=0;pose<2;++pose){
   D3DXMATRIX rotation,world,projection;D3DXMatrixRotationYawPitchRoll(&rotation,.65f+pose*1.2f,-.3f,0);
   world=rotation;world._43=3.2f;D3DXMatrixPerspectiveFovLH(&projection,.9f,1,.1f,100);
   memcpy(vc,&world,64);memcpy(vc+16,&projection,64);memcpy(vc+32,&rotation,64);memcpy(vc+48,&identity,64);
   pc[388]=0;auto old=render(ps,mesh.data(),mesh.size());
   sprintf(path,"src/obj/asteroid_normals/%c_%d_before.png",suffix,pose);Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,rt,nullptr,nullptr));
   pc[388]=.65f;auto now=render(ps,mesh.data(),mesh.size());
   Require(delta(old,now).first>2000,"normal relief visible on rotated actual mesh");
   sprintf(path,"src/obj/asteroid_normals/%c_%d_after.png",suffix,pose);Check(D3DXSaveSurfaceToFileA(path,D3DXIFF_PNG,rt,nullptr,nullptr));
  }
 }
 puts("PASS: all three actual asteroid meshes, two rotations; before/after images saved");
 for(int slot:{0,10,13,14})d->SetTexture(slot,nullptr);d->SetVertexShader(nullptr);d->SetPixelShader(nullptr);
 read->Release();rt->Release();base->Release();normal->Release();ice->Release();white->Release();slope->Release();
 vs->Release();ps->Release();oldPs->Release();d->Release();api->Release();DestroyWindow(window);
}
