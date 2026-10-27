// Isolated pixel/geometry GPU cost, NOT full-game FPS. Pretransformed actual
// meshes in one VB remove per-object CPU submission stalls from GPU timestamps.
#include "RP9ShaderCache.h"
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <array>
static void Check(HRESULT hr){if(FAILED(hr)){printf("HRESULT %08lx\n",hr);exit(2);}}
static void Require(bool ok,const char* message){if(!ok){puts(message);exit(3);}}
static std::string Read(const char* path){FILE* f=fopen(path,"rb");Require(f!=nullptr,path);std::string s;char b[4096];size_t n;
 while((n=fread(b,1,sizeof(b),f)))s.append(b,n);fclose(f);return s;}
static std::vector<unsigned char> Compile(std::string s,const char* entry,const char* profile){
 std::vector<unsigned char> code;std::string errors;bool hit=false,stored=false;
 Check(Rp9ShaderCache::Compile(s,nullptr,entry,profile,0,&code,&errors,&hit,&stored));return code;}
template<class T> static void Query(IDirect3DQuery9* q,T& value){HRESULT hr;ULONGLONG start=GetTickCount64();
 while((hr=q->GetData(&value,sizeof(value),D3DGETDATA_FLUSH))==S_FALSE){Require(GetTickCount64()-start<10000,"GPU query timeout");Sleep(0);}Check(hr);}
struct Vertex{D3DXVECTOR3 p,n;float u,v;};
int main(){
 setvbuf(stdout,nullptr,_IONBF,0);SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 const int W=1920,H=1080;
 HWND window=CreateWindowA("STATIC","normal GPU cost",WS_POPUP,0,0,W,H,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");
 D3DADAPTER_IDENTIFIER9 adapter={};Check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU: %s; %dx%d\n",adapter.Description,W,H);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=W;pp.BackBufferHeight=H;
 pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.EnableAutoDepthStencil=TRUE;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
 IDirect3DDevice9* d=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 auto source=Read("DATA_EXTRA/SHADERS/surface_material.hlsl");auto vsCode=Compile(source,"VSMain","vs_3_0");
 IDirect3DVertexShader9* vs=nullptr;Check(d->CreateVertexShader((DWORD*)vsCode.data(),&vs));
 IDirect3DPixelShader9* ps[2]={};
 for(int i=0;i<2;++i){auto code=Compile("#define SURFACE_NO_SHADOW 1\n"+(i?source:Read("src/obj/asteroid_normals/baseline.hlsl")),"PSMain","ps_3_0");
  Check(d->CreatePixelShader((DWORD*)code.data(),&ps[i]));}
 IDirect3DTexture9 *base=nullptr,*normal=nullptr;
 Check(D3DXCreateTextureFromFileA(d,"src/obj/asteroid_normals/base.dds",&base));
 Check(D3DXCreateTextureFromFileA(d,"src/obj/asteroid_normals/normal.dds",&normal));d->SetTexture(0,base);d->SetTexture(14,normal);
 for(int slot:{0,14})for(auto state:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})d->SetSamplerState(slot,state,D3DTEXF_LINEAR);
 d->SetFVF(D3DFVF_XYZ|D3DFVF_NORMAL|D3DFVF_TEX1);d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE);
 d->SetRenderState(D3DRS_ZENABLE,TRUE);d->SetRenderState(D3DRS_ZWRITEENABLE,TRUE);d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL);
 d->SetRenderState(D3DRS_LIGHTING,TRUE);d->SetRenderState(D3DRS_AMBIENT,0xff262626);d->SetRenderState(D3DRS_SPECULARENABLE,FALSE);
 d->SetRenderState(D3DRS_COLORVERTEX,FALSE);d->SetRenderState(D3DRS_DIFFUSEMATERIALSOURCE,D3DMCS_MATERIAL);
 d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_MODULATE);d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_TEXTURE);
 d->SetTextureStageState(0,D3DTSS_COLORARG2,D3DTA_DIFFUSE);d->SetTextureStageState(0,D3DTSS_ALPHAOP,D3DTOP_MODULATE);
 d->SetTextureStageState(0,D3DTSS_ALPHAARG1,D3DTA_TEXTURE);d->SetTextureStageState(0,D3DTSS_ALPHAARG2,D3DTA_DIFFUSE);
 d->SetTextureStageState(1,D3DTSS_COLOROP,D3DTOP_DISABLE);
 D3DMATERIAL9 material={};material.Diffuse=material.Ambient={1,1,1,1};d->SetMaterial(&material);
 D3DLIGHT9 light={};light.Type=D3DLIGHT_DIRECTIONAL;light.Direction={.6f,-.3f,1};light.Diffuse={.7f,.7f,.7f,1};d->SetLight(0,&light);d->LightEnable(0,TRUE);
 float pc[98*4]={},vc[68]={};D3DXMATRIX id,projection;D3DXMatrixIdentity(&id);D3DXMatrixPerspectiveFovLH(&projection,.9f,float(W)/H,.1f,100);
 memcpy(vc,&id,64);memcpy(vc+16,&projection,64);memcpy(vc+32,&id,64);memcpy(vc+48,&id,64);
 d->SetTransform(D3DTS_WORLD,&id);d->SetTransform(D3DTS_VIEW,&id);d->SetTransform(D3DTS_PROJECTION,&projection);
 d->SetVertexShaderConstantF(0,vc,17);
 pc[0]=pc[1]=pc[2]=pc[3]=1;pc[4]=pc[5]=pc[6]=.15f;pc[12]=pc[13]=pc[14]=.04f;pc[15]=.9f;pc[16]=1;pc[19]=1;
 pc[28]=pc[29]=4;pc[31]=-1;memcpy(pc+32,&id,64);pc[51]=3;pc[52]=.6f;pc[53]=-.3f;pc[54]=1;
 pc[56]=pc[57]=pc[58]=pc[60]=pc[61]=pc[62]=.7f;pc[300]=1.35f;pc[301]=.9f;pc[302]=.8f;pc[303]=1;
 std::vector<Vertex> models[3];
 for(int i=0;i<3;++i){char path[160];sprintf(path,"src/obj/asteroid_normals/mesh_%c.bin",'a'+i);auto bytes=Read(path);
  models[i].resize(bytes.size()/sizeof(Vertex));memcpy(models[i].data(),bytes.data(),bytes.size());}
 IDirect3DQuery9 *a=nullptr,*b=nullptr,*f=nullptr,*dj=nullptr,*occ=nullptr;
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&a));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&b));
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&f));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&dj));Check(d->CreateQuery(D3DQUERYTYPE_OCCLUSION,&occ));
 const char* modes[]={"native fixed-function","old surface shader","new surface, normal off","new surface, normal on"};
 for(int scene=0;scene<3;++scene){
  std::vector<Vertex> vertices;
  if(scene==2){Vertex quad[]={{{-1,-1,.5f},{0,0,-1},0,1},{{-1,1,.5f},{0,0,-1},0,0},{{1,-1,.5f},{0,0,-1},1,1},
    {{1,-1,.5f},{0,0,-1},1,1},{{-1,1,.5f},{0,0,-1},0,0},{{1,1,.5f},{0,0,-1},1,0}};vertices.assign(quad,quad+6);memcpy(vc+16,&id,64);d->SetTransform(D3DTS_PROJECTION,&id);}
  else for(int i=0;i<90;++i){D3DXMATRIX rotation;D3DXMatrixRotationYawPitchRoll(&rotation,i*.37f,i*.13f,.2f);
   float z=8,scale=(scene?160.f:60.f)*z/(H*projection._22);
   float x=((i%10+.5f)/10*2-1)*z/projection._11,y=((i/10+.5f)/9*2-1)*z/projection._22;
   for(auto v:models[i%3]){D3DXVec3TransformNormal(&v.p,&v.p,&rotation);D3DXVec3TransformNormal(&v.n,&v.n,&rotation);
    v.p=v.p*scale+D3DXVECTOR3(x,y,z);vertices.push_back(v);}}
  IDirect3DVertexBuffer9* vb=nullptr;Check(d->CreateVertexBuffer((UINT)vertices.size()*sizeof(Vertex),0,0,D3DPOOL_MANAGED,&vb,nullptr));
  void* data=nullptr;Check(vb->Lock(0,0,&data,0));memcpy(data,vertices.data(),vertices.size()*sizeof(Vertex));vb->Unlock();d->SetStreamSource(0,vb,0,sizeof(Vertex));
  d->SetVertexShaderConstantF(0,vc,17);
  auto setup=[&](int mode){d->SetVertexShader(mode?vs:nullptr);d->SetPixelShader(mode?ps[mode==1?0:1]:nullptr);
   pc[388]=mode==3?.65f:0;d->SetPixelShaderConstantF(0,pc,98);};
  auto draw=[&](){Check(d->DrawPrimitive(D3DPT_TRIANGLELIST,0,(UINT)vertices.size()/3));};
  setup(3);d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0);d->BeginScene();occ->Issue(D3DISSUE_BEGIN);draw();occ->Issue(D3DISSUE_END);d->EndScene();DWORD fragments=0;Query(occ,fragments);
  printf("SCENE %d: %s, %zu triangles, depth-passing fragments %.1f%% of screen\n",scene,scene==2?"fullscreen stress":scene?"90 large rocks":"90 small rocks",vertices.size()/3,100.*fragments/(W*H));
  const int repeats=30,rounds=17;std::vector<double> times[4];
  for(int round=0;round<rounds;++round)for(int order=0;order<4;++order){int mode=(order+round)%4;setup(mode);
   d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,0,1,0);d->BeginScene();draw(); // establish identical depth before timed repeated draws
   dj->Issue(D3DISSUE_BEGIN);a->Issue(D3DISSUE_END);
   for(int repeat=0;repeat<repeats;++repeat)draw();
   b->Issue(D3DISSUE_END);dj->Issue(D3DISSUE_END);f->Issue(D3DISSUE_END);d->EndScene();
   UINT64 start=0,end=0,hz=0;BOOL disjoint=TRUE;Query(b,end);Query(a,start);Query(f,hz);Query(dj,disjoint);
   if(round>=4 && !disjoint && hz && end>=start)times[mode].push_back(double(end-start)*1e6/hz/repeats);
  }
  for(int mode=0;mode<4;++mode){auto& t=times[mode];Require(t.size()>=8,"Insufficient valid samples");std::sort(t.begin(),t.end());
   printf("  %-26s median %.3f us; p10 %.3f us; p90 %.3f us\n",modes[mode],t[t.size()/2],t[(t.size()-1)/10],t[(t.size()-1)*9/10]);}
  d->SetStreamSource(0,nullptr,0,0);vb->Release();
 }
 puts("13 interleaved samples/mode, 30 draws/sample, warmed GPU. Geometry batched to isolate GPU cost; no frame-FPS claim.");
 a->Release();b->Release();f->Release();dj->Release();occ->Release();d->SetTexture(0,nullptr);d->SetTexture(14,nullptr);
 d->SetVertexShader(nullptr);d->SetPixelShader(nullptr);base->Release();normal->Release();vs->Release();ps[0]->Release();ps[1]->Release();d->Release();api->Release();DestroyWindow(window);
}
