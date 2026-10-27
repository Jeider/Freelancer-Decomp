// GPU checks for the exterior tinted-glass branch of the production shader.
#include "RP9ShaderCache.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
static void Require(bool b,const char* m){if(!b){printf("FAIL: %s\n",m);exit(3);}}
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
static std::string Read(const char* path){FILE*f=fopen(path,"rb");Require(f!=nullptr,path);std::string s;
 char b[4096];size_t n;while((n=fread(b,1,sizeof(b),f)))s.append(b,n);fclose(f);return s;}
static std::vector<unsigned char> Compile(std::string s,const char* entry,const char* profile){
 std::vector<unsigned char> code;std::string errors;bool hit=false,stored=false;
 Check(Rp9ShaderCache::Compile(s,nullptr,entry,profile,0,&code,&errors,&hit,&stored));return code;}
struct Vertex{float x,y,z,nx,ny,nz,u,v;};
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX);
 HWND window=CreateWindowA("STATIC","glass fixture",WS_POPUP,0,0,64,64,0,0,GetModuleHandle(0),0);
 auto*api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");IDirect3DDevice9*d=nullptr;
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;
 pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 std::string source=Read("DATA_EXTRA/SHADERS/surface_material.hlsl");
 auto v=Compile(source,"VSMain","vs_3_0"),p=Compile("#define SURFACE_NO_SHADOW 1\n"+source,"PSMain","ps_3_0");
 IDirect3DVertexShader9*vs=nullptr;IDirect3DPixelShader9 *ps=nullptr,*old=nullptr;
 Check(d->CreateVertexShader((DWORD*)v.data(),&vs));Check(d->CreatePixelShader((DWORD*)p.data(),&ps));
 // Optional local pre-edit snapshot enables exact non-glass regression checks.
 FILE*baseline=fopen("src/obj/ship_glass/before.hlsl","rb");if(baseline){fclose(baseline);
  auto b=Compile("#define SURFACE_NO_SHADOW 1\n"+Read("src/obj/ship_glass/before.hlsl"),"PSMain","ps_3_0");
  Check(d->CreatePixelShader((DWORD*)b.data(),&old));}
 D3DXMATRIX id;D3DXMatrixIdentity(&id);float vc[68]={},pc[97*4]={};
 for(int i=0;i<4;++i)memcpy(vc+i*16,&id,64);
 pc[3]=.8f;pc[4]=pc[5]=pc[6]=.15f;pc[12]=pc[13]=pc[14]=.04f;pc[15]=.8f;
 pc[28]=pc[29]=3;pc[31]=-1;memcpy(pc+32,&id,64);
 pc[300]=1.35f;pc[301]=.9f;pc[302]=.8f;pc[303]=1;
 pc[377]=1;pc[378]=1.5f;pc[379]=.65f;
 Vertex q[]={{-1,-1,.5,0,0,-1,0,1},{-1,1,.5,0,0,-1,0,0},
             {1,-1,.5,0,0,-1,1,1},{1,1,.5,0,0,-1,1,0}};
 d->SetVertexShader(vs);d->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1);
 d->SetRenderState(D3DRS_ZENABLE,0);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
 d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA);d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA);
 IDirect3DSurface9 *rt=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&rt));
 Check(d->CreateOffscreenPlainSurface(64,64,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,0));
 auto render=[&](IDirect3DPixelShader9*shader,bool blend=false,DWORD bg=0xff000000){
  Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,blend));Check(d->Clear(0,0,D3DCLEAR_TARGET,bg,1,0));Check(d->BeginScene());
  Check(d->SetPixelShader(shader));Check(d->SetVertexShaderConstantF(0,vc,17));Check(d->SetPixelShaderConstantF(0,pc,97));
  Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,q,sizeof(Vertex)));Check(d->EndScene());Check(d->GetRenderTargetData(rt,read));
  D3DLOCKED_RECT l;Check(read->LockRect(&l,0,D3DLOCK_READONLY));std::vector<DWORD>r;
  for(int y=0;y<64;++y)for(int x=0;x<64;++x)r.push_back(((DWORD*)((char*)l.pBits+y*l.Pitch))[x]);read->UnlockRect();return r;};
 auto delta=[](std::vector<DWORD>const&a,std::vector<DWORD>const&b){unsigned worst=0;
  for(unsigned i=0;i<a.size();++i)for(int shift:{0,8,16,24})worst=(std::max)(worst,unsigned(abs(int((a[i]>>shift)&255)-int((b[i]>>shift)&255))));return worst;};
 const float colours[][3]={{.1451f,.2196f,.3059f},{.2431f,.2745f,.2392f}};
 for(unsigned ship=0;ship<2;++ship){
  memcpy(pc,colours[ship],12);pc[377]=1;
  for(int angle:{0,75}){
   const float a=angle*3.14159265f/180;for(auto&v:q){v.nx=std::sin(a);v.nz=-std::cos(a);}
   auto now=render(ps);unsigned alpha=now[2080]>>24;
   printf("%s %d degrees: opacity %.1f%%\n",ship?"rh_elite":"li_elite",angle,alpha/2.55);
   Require(alpha>=83 && alpha<=125,"tinted exterior glass stays partially transparent");
   if(!angle){Require(alpha<=90,"front-facing canopy stays near 33 percent opacity");
    if(!ship)Require((now[2080]&255)>((now[2080]>>16)&255)+15,"Liberty blue tint preserved");
    else Require(((now[2080]>>8)&255)>=((now[2080]>>16)&255),"Rheinland green tint preserved");
    if(old)Require((render(old)[2080]>>24)+20<alpha,"old near-invisible glass replaced");}
   else Require(alpha>=91,"grazing glass becomes denser");
   auto dark=render(ps,true),bright=render(ps,true,0xffffffff);
   for(int shift:{0,8,16}){int transmission=int((bright[2080]>>shift)&255)-int((dark[2080]>>shift)&255);
    Require(transmission>0 && transmission<=172,"glass transmits at most two thirds of the background contrast");}
  }
 }
 for(auto&v:q){v.nx=0;v.nz=0;}Require((render(ps)[2080]>>24)>=83,"glass without vertex normals retains opacity");
 for(auto&v:q)v.nz=-1;
 if(old)for(unsigned style=0;style<2;++style){pc[377]=0;pc[376]=float(style);
  Require(delta(render(old),render(ps))<=1,"hull and cockpit shader output unchanged");}
 // Greenhouse is a separate profile: transparent panes, opaque painted ribs.
 auto greenhouseCode=Compile("#define SURFACE_GREENHOUSE 1\n#define SURFACE_NO_SHADOW 1\n"+source,"PSMain","ps_3_0");
 IDirect3DPixelShader9*greenhouse=nullptr;Check(d->CreatePixelShader((DWORD*)greenhouseCode.data(),&greenhouse));
 IDirect3DTexture9*panel=nullptr;Check(d->CreateTexture(1,1,1,0,D3DFMT_A8R8G8B8,D3DPOOL_MANAGED,&panel,0));
 auto panelColour=[&](DWORD colour){D3DLOCKED_RECT l;Check(panel->LockRect(0,&l,0,0));*(DWORD*)l.pBits=colour;panel->UnlockRect(0);};
 d->SetTexture(0,panel);pc[16]=1;pc[28]=pc[29]=4;pc[376]=0;pc[377]=2;pc[0]=pc[1]=pc[2]=pc[3]=1;
 panelColour(0x61808080);auto pane=render(greenhouse);unsigned paneAlpha=pane[2080]>>24;
 Require(paneAlpha>=90 && paneAlpha<=100,"greenhouse optical density reduced by 33 percent from doubled preset");
 Require(abs(int(pane[2080]&255)-int((pane[2080]>>16)&255))<=8 &&
         abs(int((pane[2080]>>8)&255)-int((pane[2080]>>16)&255))<=8,"greenhouse uses pale neutral grey glazing");
 for(auto&v:q){v.nx=.9962f;v.nz=-.0872f;}
 auto edge=render(greenhouse);Require((edge[2080]>>24)>paneAlpha+25,"greenhouse edge becomes more reflective and opaque");
 for(auto&v:q){v.nx=0;v.nz=-1;}
 panelColour(0xffc0c0c0);Require((render(greenhouse)[2080]>>24)==255,"greenhouse structural ribs stay opaque");
 pc[377]=1;panelColour(0x61808080);Require((render(ps)[2080]>>24)+20<paneAlpha,"greenhouse and ship glass retain separate density");
 d->SetTexture(0,nullptr);panel->Release();greenhouse->Release();
 printf("Greenhouse front pane opacity %.1f%%; opaque frame and denser edge verified\n",paneAlpha/2.55);
 puts("PASS: production SM3 glass opacity, tint, angle, blended transmission, normal fallback and non-glass regression");
 d->SetVertexShader(nullptr);d->SetPixelShader(nullptr);read->Release();rt->Release();vs->Release();ps->Release();if(old)old->Release();
 d->Release();api->Release();DestroyWindow(window);
}
