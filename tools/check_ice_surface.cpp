// Hidden-device checks: real SM3 shader, opaque alpha/depth, native fog, layer
// parallax, frost, ordinary-surface regression, and the actual Tau31 CMP preview.
#include "RP9ShaderCache.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>

static void Require(bool ok,const char* message){if(!ok){printf("FAIL: %s\n",message);exit(3);}}
static void Check(HRESULT hr){if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);}}
static std::string Read(const char* path){FILE* f=fopen(path,"rb");Require(f!=nullptr,path);std::string s;
 char b[4096];size_t n;while((n=fread(b,1,sizeof(b),f)))s.append(b,n);fclose(f);return s;}
static std::vector<unsigned char> Compile(std::string s,const char* entry,const char* profile){
 std::vector<unsigned char> code;std::string errors;bool hit=false,stored=false;
 auto hr=Rp9ShaderCache::Compile(s,nullptr,entry,profile,0,&code,&errors,&hit,&stored);
 if(!errors.empty())puts(errors.c_str());Check(hr);printf("%s %s: %s, %zu bytes\n",entry,profile,hit?"HIT":"compiled",code.size());return code;}
struct Vertex{float x,y,z,nx,ny,nz,u,v;};
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 const int W=512,H=512;
 HWND window=CreateWindowA("STATIC","ice surface checks",WS_POPUP,0,0,W,H,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=W;pp.BackBufferHeight=H;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto source=Read("DATA_EXTRA/SHADERS/surface_material.hlsl");
 auto vsCode=Compile(source,"VSMain","vs_3_0");
 auto psCode=Compile("#define SURFACE_NO_SHADOW 1\n"+source,"PSMain","ps_3_0");
 auto oldCode=Compile("#define SURFACE_NO_SHADOW 1\n"+Read("src/obj/ice_surface_check/baseline.hlsl"),"PSMain","ps_3_0");
 // Compile and create every production variant, including full shadow sampling
 // and cube environments. Prefixes match RP9's menu warm-up byte for byte.
 auto instanced=Compile("#define SURFACE_INSTANCED 1\n"+source,"VSMain","vs_3_0");
 IDirect3DVertexShader9* ivs=nullptr;Check(d->CreateVertexShader((DWORD*)instanced.data(),&ivs));ivs->Release();
 for(const char* tier:{"","#define SURFACE_NO_SHADOW 1\n","#define SURFACE_LOW_DETAIL 1\n"})
  for(const char* cube:{"","#define SURFACE_ENV_CUBE 1\n"}){
   auto code=Compile(std::string(tier)+cube+source,"PSMain","ps_3_0");
   IDirect3DPixelShader9* candidate=nullptr;Check(d->CreatePixelShader((DWORD*)code.data(),&candidate));candidate->Release();
  }
 IDirect3DVertexShader9* vs=nullptr;IDirect3DPixelShader9 *ps=nullptr,*oldPs=nullptr;
 Check(d->CreateVertexShader((DWORD*)vsCode.data(),&vs));Check(d->CreatePixelShader((DWORD*)psCode.data(),&ps));
 Check(d->CreatePixelShader((DWORD*)oldCode.data(),&oldPs));
 IDirect3DTexture9 *base=nullptr,*layers=nullptr,*env=nullptr;
 Check(D3DXCreateTextureFromFileA(d,"src/obj/ice_surface_check/base.dds",&base));
 Check(D3DXCreateTextureFromFileA(d,"DATA_EXTRA/TEXTURES/ice_layers.dds",&layers));
 Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&env,nullptr));
 D3DLOCKED_RECT lock;Check(env->LockRect(0,&lock,nullptr,0));*(DWORD*)lock.pBits=0xff7693a8;env->UnlockRect(0);
 d->SetTexture(0,base);d->SetTexture(10,env);d->SetTexture(13,layers);
 for(int slot:{0,10,13})for(auto state:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})d->SetSamplerState(slot,state,D3DTEXF_LINEAR);
 d->SetVertexShader(vs);d->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1);
 d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE);
 d->SetRenderState(D3DRS_ZENABLE,TRUE);d->SetRenderState(D3DRS_ZWRITEENABLE,TRUE);d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
 IDirect3DSurface9 *rt=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&rt));
 Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 float pc[97*4]={},vc[68]={};D3DXMATRIX identity;D3DXMatrixIdentity(&identity);
 auto matrices=[&](){for(int i=0;i<4;++i)memcpy(vc+i*16,&identity,64);};matrices();
 pc[0]=pc[1]=pc[2]=pc[3]=1;pc[4]=pc[5]=pc[6]=.15f;
 pc[12]=pc[13]=pc[14]=.04f;pc[15]=.3f;pc[16]=1;pc[18]=.45f;pc[19]=1;
 pc[28]=pc[29]=4;pc[31]=-1;memcpy(pc+32,&identity,64);
 pc[51]=3;pc[52]=.4f;pc[53]=-.3f;pc[54]=1;
 pc[56]=pc[57]=pc[58]=.9f;pc[60]=pc[61]=pc[62]=.9f;
 pc[300]=1.35f;pc[301]=.9f;pc[302]=.8f;pc[303]=1;
 pc[385]=.09f;pc[386]=.65f;pc[387]=.22f;
 Vertex quad[]={{-1,-1,.5,0,0,-1,0,1},{-1,1,.5,0,0,-1,0,0},{1,-1,.5,0,0,-1,1,1},
 {1,-1,.5,0,0,-1,1,1},{-1,1,.5,0,0,-1,0,0},{1,1,.5,0,0,-1,1,0}};
 auto draw=[&](IDirect3DPixelShader9* shader,const Vertex* vertices,size_t count){
  Check(d->SetPixelShader(shader));Check(d->SetVertexShaderConstantF(0,vc,17));Check(d->SetPixelShaderConstantF(0,pc,97));
  Check(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,(UINT)(count/3),vertices,sizeof(Vertex)));};
 auto pixels=[&](){Check(d->GetRenderTargetData(rt,read));Check(read->LockRect(&lock,nullptr,D3DLOCK_READONLY));
  std::vector<DWORD> p(W*H);for(int y=0;y<H;++y)memcpy(p.data()+y*W,(char*)lock.pBits+y*lock.Pitch,W*4);read->UnlockRect();return p;};
 auto render=[&](IDirect3DPixelShader9* shader){Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff08101a,1,0));
  Check(d->BeginScene());draw(shader,quad,6);Check(d->EndScene());return pixels();};
 auto compare=[&](const std::vector<DWORD>& a,const std::vector<DWORD>& b){size_t changed=0;unsigned maxDelta=0;
  for(size_t i=0;i<a.size();++i){if(a[i]!=b[i])++changed;for(int s:{0,8,16,24})maxDelta=std::max(maxDelta,(unsigned)abs(int((a[i]>>s)&255)-int((b[i]>>s)&255)));}
  printf("changed pixels=%zu, max channel delta=%u\n",changed,maxDelta);return std::make_pair(changed,maxDelta);};
 for(float style:{0.f,1.f,2.f}){
  pc[376]=style==1?1.f:0.f;pc[377]=style==2?1.f:0.f;pc[378]=1.5f;pc[379]=.65f;pc[31]=5;
  auto before=render(oldPs),after=render(ps);Require(compare(before,after).second<=1,"ordinary/cockpit/glass regression");}
 puts("PASS: existing surfaces/cockpit/glass match HEAD within 1/255");pc[376]=pc[377]=0;pc[31]=-1;pc[18]=0;
 pc[384]=1;auto ice=render(ps);for(auto p:ice)Require((p>>24)==255,"ice is fully opaque");
 pc[384]=0;auto plain=render(ps);Require(compare(ice,plain).first>W*H/4,"ice profile changes the actual ice texture");pc[384]=1;
 pc[385]=0;auto noDepth=render(ps);pc[385]=.09f;Require(compare(noDepth,ice).first>W*H/10,"interior parallax is visible");
 pc[386]=0;auto bare=render(ps);pc[386]=1;auto frosted=render(ps);Require(compare(bare,frosted).first>W*H/10,"frost changes the finish");pc[386]=.65f;
 pc[23]=3;pc[20]=0;pc[21]=.1f;pc[24]=.1f;pc[25]=.2f;pc[26]=.3f;
 auto fog=render(ps);for(auto p:fog)Require(abs(int((p>>16)&255)-26)<=1 && abs(int((p>>8)&255)-51)<=1 && abs(int(p&255)-77)<=1 && (p>>24)==255,"native full fog and opaque alpha");
 puts("PASS: opaque alpha, internal parallax, frost and native fog");pc[23]=0;
 auto front=render(ps);Vertex rear[6];memcpy(rear,quad,sizeof(rear));for(auto& v:rear)v.z=.8f;
 pc[384]=0;pc[8]=1;pc[9]=0;pc[10]=1;Check(d->BeginScene());draw(ps,rear,6);Check(d->EndScene());
 Require(compare(front,pixels()).first==0,"rear geometry remains hidden by ice depth");puts("PASS: ice writes depth; rear object cannot leak through");
 pc[8]=pc[10]=0;pc[384]=1;
 auto meshBytes=Read("src/obj/ice_surface_check/mesh.bin");std::vector<Vertex> mesh(meshBytes.size()/sizeof(Vertex));memcpy(mesh.data(),meshBytes.data(),meshBytes.size());
 D3DXMATRIX rotation,world,normal,projection;D3DXMatrixRotationYawPitchRoll(&rotation,.65f,-.3f,0);
 world=rotation;world._43=3.2f;normal=rotation;D3DXMatrixPerspectiveFovLH(&projection,.9f,1,.1f,100);
 memcpy(vc,&world,64);memcpy(vc+16,&projection,64);memcpy(vc+32,&normal,64);memcpy(vc+48,&identity,64);
 pc[384]=0;
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff08101a,1,0));
 Check(d->BeginScene());draw(ps,mesh.data(),mesh.size());Check(d->EndScene());
 Check(D3DXSaveSurfaceToFileA("src/obj/ice_surface_check/legacy.png",D3DXIFF_PNG,rt,nullptr,nullptr));
 pc[384]=1;
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff08101a,1,0));
 Check(d->BeginScene());draw(ps,mesh.data(),mesh.size());Check(d->EndScene());
 Check(D3DXSaveSurfaceToFileA("src/obj/ice_surface_check/preview.png",D3DXIFF_PNG,rt,nullptr,nullptr));
 puts("PASS: rendered actual ice_ast_super.cmp with its original 4096px texture; preview.png saved");
 d->SetTexture(0,nullptr);d->SetTexture(10,nullptr);d->SetTexture(13,nullptr);d->SetVertexShader(nullptr);d->SetPixelShader(nullptr);
 read->Release();rt->Release();base->Release();layers->Release();env->Release();vs->Release();ps->Release();oldPs->Release();d->Release();api->Release();DestroyWindow(window);
}
