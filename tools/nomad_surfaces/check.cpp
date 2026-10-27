// Real D3D9/SM3 renders and boundary regressions; no game installation writes.
#include "RP9ShaderCache.h"
#include "../../src/freelancer/Client/asteroid_frustum.h"
#include "../../src/include/render/NomadSurfacePolicy.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <random>
static void Need(bool ok,const char* s){if(!ok){printf("FAIL %s\n",s);exit(3);}}
static void Check(HRESULT hr){if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);}}
static std::string Read(const char* p){FILE* f=fopen(p,"rb");Need(f!=nullptr,p);std::string s;char b[4096];size_t n;while((n=fread(b,1,sizeof b,f)))s.append(b,n);fclose(f);return s;}
static std::vector<unsigned char> Compile(const std::string& s,const char* e,const char* p){std::vector<unsigned char> c;std::string errors;bool hit=false,stored=false;HRESULT h=Rp9ShaderCache::Compile(s,nullptr,e,p,0,&c,&errors,&hit,&stored);if(!errors.empty())puts(errors.c_str());Check(h);printf("%s %s %zu bytes\n",e,p,c.size());return c;}
struct V{float x,y,z,nx,ny,nz,u,v;};
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 // A visible witness point enclosed by a mesh sphere must never be rejected.
 std::mt19937 random(512);std::uniform_real_distribution<double> unit(0,1);
 for(int i=0;i<200000;++i){double tx=.25+unit(random)*3,ty=.2+unit(random),farDistance=15000,z=unit(random)*farDistance;
  double x=(unit(random)*2-1)*z*tx,y=(unit(random)*2-1)*z*ty,r=20+unit(random)*2500;
  double az=unit(random)*6.283185307,cz=unit(random)*2-1,sz=sqrt(1-cz*cz),dist=unit(random)*r;
  Need(AsteroidBoundsInFrustum(x+dist*sz*cos(az),y+dist*sz*sin(az),z+dist*cz,r,tx,ty,farDistance),"visible sphere witness culled");}
 Need(!AsteroidBoundsInFrustum(100,0,10,1,1,1,100),"reject outside right");
 Need(!AsteroidBoundsInFrustum(0,0,-20,1,1,1,100),"reject behind camera");
 Need(AsteroidBoundsInFrustum(11,0,10,2,1,1,100),"edge-straddling cube");
 Need(NomadSurfaceProfile("DETAILMAP_LAIR_SKIN01")==7 && NomadSurfaceProfile("detailmap_lair_rock01")==5 && NomadSurfaceProfile("nomad_glow")==0,"material identity policy");
 puts("PASS 200000 conservative frustum witnesses and explicit material identities");
 const int W=960,H=720;HWND window=CreateWindowA("STATIC","Nomad checks",WS_POPUP,0,0,W,H,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Need(api!=nullptr,"D3D9");D3DADAPTER_IDENTIFIER9 info={};api->GetAdapterIdentifier(0,0,&info);printf("GPU %s\n",info.Description);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=W;pp.BackBufferHeight=H;pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto source=Read("DATA_EXTRA/SHADERS/surface_material.hlsl"),baseline=Read("src/obj/nomad_surfaces/baseline/DATA_EXTRA/SHADERS/surface_material.hlsl");
 // Without the opt-in macro the compiler must produce identical old shader code.
 if(!getenv("NOMAD_QUICK")) for(const char* variant:{"","#define SURFACE_NO_SHADOW 1\n","#define SURFACE_LOW_DETAIL 1\n"}){
  auto a=Compile(std::string(variant)+source,"PSMain","ps_3_0"),b=Compile(std::string(variant)+baseline,"PSMain","ps_3_0");
  Need(a==b,"unrelated surface bytecode changed");}
 if(!getenv("NOMAD_QUICK")) puts("PASS unrelated surface bytecode identical to pre-change working tree");
 const std::string prefix="#define SURFACE_NOMAD 1\n";
 auto code=Compile(prefix+source,"VSMain","vs_3_0");IDirect3DVertexShader9* vs=nullptr;Check(d->CreateVertexShader((DWORD*)code.data(),&vs));
 IDirect3DPixelShader9 *ps[4]={},*depth=nullptr;
 for(int i=0;i<4;++i){code=Compile(prefix+(i>=2?"#define SURFACE_NOMAD_LIGHT 1\n":"")+(i%2?"#define SURFACE_NO_SHADOW 1\n":"")+source,"PSMain","ps_3_0");Check(d->CreatePixelShader((DWORD*)code.data(),&ps[i]));}
 code=Compile(prefix+"#define SURFACE_NOMAD_LIGHT 1\n#define SURFACE_NO_SHADOW 1\n"+source,"PSNomadDepth","ps_3_0");Check(d->CreatePixelShader((DWORD*)code.data(),&depth));
 IDirect3DTexture9 *textures[3]={},*layers=nullptr,*illum=nullptr;
 for(int i=0;i<3;++i)Check(D3DXCreateTextureFromFileA(d,(std::string("src/obj/nomad_surfaces/")+(i==0?"inside.dds":i==1?"outside.dds":"dyson.dds")).c_str(),&textures[i]));
 Check(D3DXCreateTextureFromFileA(d,"DATA_EXTRA/TEXTURES/nomad_layers.dds",&layers));Check(D3DXCreateTextureFromFileA(d,"src/obj/nomad_surfaces/illumination.dds",&illum));
 d->SetTexture(0,textures[0]);d->SetTexture(1,illum);d->SetTexture(13,layers);
 for(int s:{0,1,13})for(auto f:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})d->SetSamplerState(s,f,D3DTEXF_LINEAR);
 d->SetVertexShader(vs);d->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);d->SetRenderState(D3DRS_ZENABLE,TRUE);d->SetRenderState(D3DRS_ZWRITEENABLE,TRUE);d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
 IDirect3DSurface9 *rt=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&rt));Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 float vc[68]={},pc[102*4]={};D3DXMATRIX id;D3DXMatrixIdentity(&id);for(int i=0;i<4;++i)memcpy(vc+i*16,&id,64);vc[67]=1;
 pc[0]=pc[1]=pc[2]=pc[3]=1;pc[4]=pc[5]=pc[6]=.12f;pc[16]=1;pc[19]=1;pc[28]=pc[29]=4;pc[31]=-1;
 pc[51]=3;pc[52]=-.35f;pc[53]=.3f;pc[54]=1;pc[56]=.65f;pc[57]=.8f;pc[58]=.72f;pc[60]=pc[61]=pc[62]=1;
 pc[384]=3;pc[385]=1.15f;pc[386]=.32f;pc[388]=7;pc[391]=1;memcpy(pc+392,&id,64);
 V quad[]={{-1,-1,.5,0,0,-1,0,1},{-1,1,.5,0,0,-1,0,0},{1,-1,.5,0,0,-1,1,1},{1,-1,.5,0,0,-1,1,1},{-1,1,.5,0,0,-1,0,0},{1,1,.5,0,0,-1,1,0}};
 auto draw=[&](IDirect3DPixelShader9* shader,const V* v,size_t n){Check(d->SetPixelShader(shader));Check(d->SetVertexShaderConstantF(0,vc,17));Check(d->SetPixelShaderConstantF(0,pc,102));Check(d->DrawPrimitiveUP(D3DPT_TRIANGLELIST,(UINT)n/3,v,sizeof(V)));};
 auto pixels=[&](){Check(d->GetRenderTargetData(rt,read));D3DLOCKED_RECT l;Check(read->LockRect(&l,nullptr,D3DLOCK_READONLY));std::vector<DWORD> result(W*H);for(int y=0;y<H;++y)memcpy(result.data()+y*W,(char*)l.pBits+y*l.Pitch,W*4);read->UnlockRect();return result;};
 auto render=[&](IDirect3DPixelShader9* shader,const V* v,size_t n){Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff070d16,1,0));Check(d->BeginScene());draw(shader,v,n);Check(d->EndScene());return pixels();};
 auto changed=[&](const std::vector<DWORD>& a,const std::vector<DWORD>& b){size_t n=0;for(size_t i=0;i<a.size();++i)n+=a[i]!=b[i];return n;};
 auto save=[&](const char* name){Check(D3DXSaveSurfaceToFileA((std::string("src/obj/nomad_surfaces/")+name+".png").c_str(),D3DXIFF_PNG,rt,nullptr,nullptr));};
 auto wet=render(ps[1],quad,6);pc[385]=0;auto flat=render(ps[1],quad,6);Need(changed(wet,flat)>W*H/4,"strong relief visible");pc[385]=1.15f;
 pc[386]=0;pc[387]=0;auto organic0=render(ps[1],quad,6);pc[387]=4;auto organic4=render(ps[1],quad,6);
 Need(changed(organic0,organic4)>W*H/100,"ET tissue animates independently of added vascular glow");
 for(size_t i=0;i<organic0.size();++i)Need((organic0[i]>>24)==(organic4[i]>>24),"organic motion preserves alpha");
 pc[387]=1024;Need(changed(organic0,render(ps[1],quad,6))==0,"ET animation wraps continuously at renderer clock reset");
 for(int profile:{1,2,3}){pc[384]=(float)profile;pc[388]=D3DTOP_MODULATE2X;pc[387]=0;auto static0=render(ps[profile==2?3:1],quad,6);pc[387]=4;
  Need(changed(static0,render(ps[profile==2?3:1],quad,6))==0,"exterior, Dyson and Bt detail do not acquire ET animation");}
 pc[384]=3;pc[388]=7;pc[387]=0;pc[386]=.32f;
 puts("PASS ET animation, stable alpha, clock wrap and non-ET exclusion");
 pc[19]=0;pc[4]=pc[5]=pc[6]=0;pc[386]=0;auto glow=render(ps[1],quad,6);pc[391]=0;auto dark=render(ps[1],quad,6);Need(changed(glow,dark)>W*H/10,"authored illumination retained in darkness");
 pc[391]=1;pc[386]=.32f;pc[19]=1;pc[4]=pc[5]=pc[6]=.12f;
 pc[23]=3;pc[21]=.1f;pc[24]=.1f;pc[25]=.2f;pc[26]=.3f;auto fog=render(ps[1],quad,6);
 for(DWORD p:fog)Need(abs(int((p>>16)&255)-26)<=1 && abs(int((p>>8)&255)-51)<=1 && abs(int(p&255)-77)<=1,"native fog");pc[23]=0;
 pc[391]=0;pc[384]=2;d->SetTexture(0,textures[2]);auto front=render(ps[3],quad,6);V rear[6];memcpy(rear,quad,sizeof rear);for(auto& v:rear)v.z=.8f;
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0xff070d16,1,0));Check(d->BeginScene());d->SetRenderState(D3DRS_COLORWRITEENABLE,0);draw(depth,rear,6);draw(depth,quad,6);
 d->SetRenderState(D3DRS_COLORWRITEENABLE,15);d->SetRenderState(D3DRS_ZWRITEENABLE,FALSE);d->SetRenderState(D3DRS_ZFUNC,D3DCMP_EQUAL);
 pc[8]=1;draw(ps[3],rear,6);pc[8]=0;draw(ps[3],quad,6);Check(d->EndScene());Need(changed(front,pixels())==0,"depth prepass identical; hidden rear does not leak");d->SetRenderState(D3DRS_ZWRITEENABLE,TRUE);d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
 puts("PASS strong relief, authored illumination, fog, identical depth transform and hidden-layer rejection");
 // Float readback catches NaN/Inf that an 8-bit screenshot would silently hide.
 IDirect3DSurface9 *hdr=nullptr,*hdrRead=nullptr;
 Check(d->CreateRenderTarget(W,H,D3DFMT_A32B32G32R32F,D3DMULTISAMPLE_NONE,0,FALSE,&hdr,nullptr));
 Check(d->CreateOffscreenPlainSurface(W,H,D3DFMT_A32B32G32R32F,D3DPOOL_SYSTEMMEM,&hdrRead,nullptr));
 Check(d->SetRenderTarget(0,hdr));V special[6];
 for(int mode=0;mode<3;++mode){memcpy(special,quad,sizeof special);for(auto& v:special){if(mode==1)v.u=1-v.u;if(mode==2){v.u=v.v=0;v.nx=1;v.nz=0;}}
  pc[384]=3;pc[385]=2;Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0));Check(d->BeginScene());draw(ps[1],special,6);Check(d->EndScene());Check(d->GetRenderTargetData(hdr,hdrRead));D3DLOCKED_RECT l;Check(hdrRead->LockRect(&l,nullptr,D3DLOCK_READONLY));
  for(int y=0;y<H;++y){const float* row=(const float*)((char*)l.pBits+y*l.Pitch);for(int x=0;x<W*4;++x)Need(std::isfinite(row[x]),"finite HDR with mirrored/degenerate UV and grazing normal");}hdrRead->UnlockRect();}
 Check(d->SetRenderTarget(0,rt));hdr->Release();hdrRead->Release();puts("PASS finite float HDR: regular/mirrored/degenerate UV, grazing normals and maximum relief");
 // A curved material sample, explicitly a shader preview rather than an in-game screenshot.
 std::vector<V> panel;auto vertex=[](int x,int y){float u=x/96.f,v=y/64.f,a=(u-.5f)*1.25f;return V{sin(a)*2.35f,(.5f-v)*1.9f,(1-cos(a))*2.35f,-sin(a),0,-cos(a),u,v};};
 for(int y=0;y<64;++y)for(int x=0;x<96;++x){panel.push_back(vertex(x,y));panel.push_back(vertex(x,y+1));panel.push_back(vertex(x+1,y));panel.push_back(vertex(x+1,y));panel.push_back(vertex(x,y+1));panel.push_back(vertex(x+1,y+1));}
 D3DXMATRIX world,projection;D3DXMatrixRotationYawPitchRoll(&world,.25f,-.12f,0);memcpy(vc+32,&world,64);world._43=3.6f;D3DXMatrixPerspectiveFovLH(&projection,.72f,float(W)/H,.1f,100);memcpy(vc,&world,64);memcpy(vc+16,&projection,64);
 for(int i=0;i<3;++i){d->SetTexture(0,textures[i]);pc[384]=i==0?3.f:i==1?1.f:2.f;pc[391]=i==0?1.f:0.f;pc[385]=1.15f;render(ps[i==2?3:1],panel.data(),panel.size());save(i==0?"inside_wet":i==1?"outside_relief":"dyson_relief");
  if(i==0){pc[385]=0;render(ps[1],panel.data(),panel.size());save("inside_flat");pc[385]=1.15f;pc[52]=.6f;pc[53]=-.2f;render(ps[1],panel.data(),panel.size());save("inside_light_shift");pc[52]=-.35f;pc[53]=.3f;}}
 puts("PASS saved actual material texture previews");
 d->SetTexture(0,textures[0]);pc[384]=3;pc[391]=1;pc[388]=7;pc[385]=1.15f;
 CreateDirectoryA("src/obj/nomad_surfaces/motion",nullptr);
 for(int frame=0;frame<96;++frame){pc[387]=frame*(16.f/96);render(ps[1],panel.data(),panel.size());char name[64];sprintf(name,"motion/et_%03d",frame);save(name);}
 pc[387]=0;puts("PASS 96 real GPU animation frames saved (16-second cycle)");
 d->SetVertexShader(nullptr);d->SetPixelShader(nullptr);for(int s:{0,1,13})d->SetTexture(s,nullptr);for(auto* p:ps)p->Release();depth->Release();vs->Release();for(auto* t:textures)t->Release();illum->Release();layers->Release();rt->Release();read->Release();d->Release();api->Release();DestroyWindow(window);
}
