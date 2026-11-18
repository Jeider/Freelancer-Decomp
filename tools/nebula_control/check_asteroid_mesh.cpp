#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <fstream>
#include <set>
#include <string>
#include <vector>
#include "RP9MeshInstances.h"
#include "RP9ShaderManifest.h"
#include "../../src/freelancer/Client/nebula_asteroid_mesh.h"
static void Require(bool v,char const*s){if(!v){printf("FAIL %s\n",s);exit(3);}}
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
static void Set(float*p,int i,float a,float b,float c,float d){p+=i*4;p[0]=a;p[1]=b;p[2]=c;p[3]=d;}
struct Instance {float centre[4],rotation[4];DWORD colour;};
struct Model {IDirect3DVertexBuffer9*mesh=nullptr,*instances=nullptr;IDirect3DTexture9*texture=nullptr;unsigned vertices=0;float radius=0;std::vector<Instance> data;};
static void Upload(IDirect3DVertexBuffer9*b,void const*p,unsigned bytes){void*out=nullptr;Check(b->Lock(0,bytes,&out,0));memcpy(out,p,bytes);Check(b->Unlock());}
static void ReadQuery(IDirect3DQuery9*q,void*p,unsigned size){DWORD start=GetTickCount();HRESULT h;
 while((h=q->GetData(p,size,D3DGETDATA_FLUSH))==S_FALSE){Require(GetTickCount()-start<10000,"GPU timeout");Sleep(0);}Check(h);}
int main(int argc,char**argv){
 Require(argc==13,"shader dir, cache, three mesh/texture/radius triples, preview");setvbuf(stdout,nullptr,_IONBF,0);
 int cell[3]={30,0,20},next[3]={31,0,20};std::vector<NebulaAsteroidMesh::Rock> rocks,moved;
 auto begin=std::chrono::steady_clock::now();
 NebulaAsteroidMesh::Generate(cell,3,[&](auto const&r){rocks.push_back(r);});
 double buildMs=std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-begin).count();
 NebulaAsteroidMesh::Generate(next,3,[&](auto const&r){moved.push_back(r);});
 auto identity=[](auto const&r){return std::string((char const*)&r,sizeof(r));};
 std::set<std::string> oldSet,newSet;for(auto const&r:rocks)oldSet.insert(identity(r));for(auto const&r:moved)newSet.insert(identity(r));
 Require(NebulaAsteroidMesh::Cell(-.1)==-1,"negative coordinate cells");Require(rocks.size()<8192 && rocks.size()>1000,"bounded dense population");
 unsigned stable=0;
 for(auto const&r:rocks){double d2=0;for(int k=0;k<3;++k){double d=r.position[k]-(k==0?31000.0:(k==1?500.0:20500.0));d2+=d*d;}
  if(d2<4350.0*4350.0){Require(newSet.count(identity(r))!=0,"cell crossing retains visible rocks");++stable;}
  double norm=0;for(float v:r.rotation)norm+=v*v;Require(std::abs(norm-1)<.00001,"unit world orientation");}
 printf("PASS world-fixed grid: %zu residents, %u overlap identities, %.3f ms generation\n",rocks.size(),stable,buildMs);
 auto*api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");IDirect3DDevice9*d=nullptr;
 HWND w=CreateWindowA("STATIC","asteroid mesh probe",WS_POPUP,0,0,1920,1080,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=1920;pp.BackBufferHeight=1080;
 pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.EnableAutoDepthStencil=1;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
 Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));
 D3DADAPTER_IDENTIFIER9 adapter={};Check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU: %s\n",adapter.Description);
 SetEnvironmentVariableA("FREELANCER_SHADER_CACHE_DIR",argv[2]);std::vector<Rp9Startup::FJob> jobs;std::string error;
 Require(Rp9Startup::Build(argv[1],jobs,error),error.c_str());IDirect3DVertexShader9*vs=nullptr;IDirect3DPixelShader9*ps=nullptr;
 unsigned checked=0;
 for(auto const&job:jobs)if(job.Name=="far_rocks.hlsl"){
  std::vector<unsigned char> code;std::string msg;bool hit=false;auto h=Rp9Startup::Compile(job,argv[1],code,msg,hit);
  if(FAILED(h))puts(msg.c_str());Check(h);
  if(job.Profile[0]=='v'){IDirect3DVertexShader9*s=nullptr;Check(d->CreateVertexShader((DWORD*)code.data(),&s));if(!strcmp(job.Entry,"VSMesh"))vs=s;else s->Release();}
  else {IDirect3DPixelShader9*s=nullptr;Check(d->CreatePixelShader((DWORD*)code.data(),&s));if(!strcmp(job.Entry,"PSMesh"))ps=s;else s->Release();}
  ++checked;
 }
 Require(vs&&ps&&checked==4,"all four production far-rock shader variants");Check(d->SetVertexShader(vs));Check(d->SetPixelShader(ps));
 Model models[3];unsigned triangles=0;
 for(int i=0;i<3;++i){auto&m=models[i];std::ifstream f(argv[3+i*3],std::ios::binary);f.read((char*)&m.vertices,4);
  Require(f.good()&&m.vertices>0&&m.vertices%3==0,"source mesh");std::vector<float> v(m.vertices*8);f.read((char*)v.data(),v.size()*4);Require(f.good(),"mesh bytes");
  m.radius=float(atof(argv[5+i*3]));Check(d->CreateVertexBuffer(m.vertices*32,0,0,D3DPOOL_MANAGED,&m.mesh,nullptr));Upload(m.mesh,v.data(),m.vertices*32);
  Check(D3DXCreateTextureFromFileA(d,argv[4+i*3],&m.texture));
  for(auto const&r:rocks)if(r.model==i){Instance a={};for(int k=0;k<3;++k)a.centre[k]=r.position[k];a.centre[3]=m.radius*r.scale;memcpy(a.rotation,r.rotation,16);a.colour=r.colour|0xff00;m.data.push_back(a);}
  triangles+=unsigned(m.data.size())*m.vertices/3;
  Check(d->CreateVertexBuffer(unsigned(m.data.size()*sizeof(Instance)),0,0,D3DPOOL_MANAGED,&m.instances,nullptr));Upload(m.instances,m.data.data(),unsigned(m.data.size()*sizeof(Instance)));
 }
 float v[40]={},p[48]={};Set(v,0,30500,500,20500,0);Set(v,1,1,0,0,0);Set(v,2,0,1,0,0);Set(v,3,0,0,1,0);
 Set(v,4,1080.f/1920,1,5000.f/4999,-5000.f/4999);Set(v,5,1,1,0,0);Set(v,6,5000,540,2,1-1.f/4194304);
 Set(v,7,NebulaAsteroidMesh::Near,1/NebulaAsteroidMesh::NearFade,NebulaAsteroidMesh::Far-NebulaAsteroidMesh::FarFade,1/NebulaAsteroidMesh::FarFade);
 Set(v,9,200,2700,1,.55f);Set(p,0,1,1,1,1);Set(p,5,80/255.f,40/255.f,0,0);Set(p,6,1,120/255.f,50/255.f,0);
 Set(p,7,.8f,0,.6f,1);Set(p,8,1,0,0,0);Set(p,9,200,2700,1,.55f);Set(p,10,150/255.f,90/255.f,20/255.f,.12f);Set(p,11,.8f,0,.6f,0);
 Check(d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));Check(d->SetRenderState(D3DRS_ZENABLE,1));Check(d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL));
 Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,1));Check(d->SetRenderState(D3DRS_SRCBLEND,D3DBLEND_SRCALPHA));Check(d->SetRenderState(D3DRS_DESTBLEND,D3DBLEND_INVSRCALPHA));
 for(auto s:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})Check(d->SetSamplerState(0,s,D3DTEXF_LINEAR));
 FRp9MeshInstances renderer;IDirect3DSurface9*target=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&target));Check(d->CreateOffscreenPlainSurface(1920,1080,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 const DWORD background=0xff965a14;
 bool local=true;
 auto draw=[&](bool single){Check(d->SetPixelShaderConstantF(0,p,12));Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,local?0:1));for(int pass=0;pass<(local?1:2);++pass){Set(v,8,float(pass),5,1,local?1.f:0.f);Check(d->SetVertexShaderConstantF(0,v,10));Check(d->SetRenderState(D3DRS_ZWRITEENABLE,pass==0));
  for(int i=0;i<(single?1:3);++i){auto&m=models[i];Check(d->SetTexture(0,m.texture));Check(renderer.Draw(d,m.mesh,m.instances,m.vertices,0,single?1:unsigned(m.data.size())));}}};
 auto pixels=[&](){Check(d->GetRenderTargetData(target,read));D3DLOCKED_RECT l;Check(read->LockRect(&l,nullptr,D3DLOCK_READONLY));unsigned n=0;
  for(int y=0;y<1080;++y)for(int x=0;x<1920;++x)if((((DWORD*)((char*)l.pBits+y*l.Pitch))[x]&0xffffff)!=(background&0xffffff))++n;read->UnlockRect();return n;};
 for(int test=0;test<4;++test){Instance a={};a.centre[0]=v[0];a.centre[1]=v[1];a.centre[2]=v[2]-(test==0?500.f:test==1?1900.f:3000.f);a.centre[3]=models[0].radius;a.rotation[3]=1;a.colour=0xff80ff00;
  Upload(models[0].instances,&a,sizeof(a));p[38]=v[38]=test==3?0.f:1.f;Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());draw(true);Check(d->EndScene());unsigned count=pixels();
  printf("Readback %d: %u pixels\n",test,count);Require((test==0||test==2)?count==0:count>20,"near/fog disappearance and ordinary mesh fallback");}
 // Fixed geometry, fade only: every surviving pixel writes depth and the mask
 // grows monotonically. Repeating a frame must not change a single pixel.
 auto snapshot=[&](){Check(d->GetRenderTargetData(target,read));D3DLOCKED_RECT l;Check(read->LockRect(&l,nullptr,D3DLOCK_READONLY));std::vector<DWORD> out(1920*1080);
  for(int y=0;y<1080;++y)memcpy(out.data()+y*1920,(char*)l.pBits+y*l.Pitch,1920*4);read->UnlockRect();return out;};
 Instance fading={};fading.centre[0]=v[0];fading.centre[1]=v[1];fading.centre[2]=v[2]-1900;fading.centre[3]=180;fading.rotation[3]=1;
 p[38]=v[38]=0;std::vector<DWORD> previous;unsigned previousCount=0;
 for(int opacity:{0,16,32,64,128,192,224,254,255}){
  fading.colour=0xff800000|(opacity<<8);Upload(models[0].instances,&fading,sizeof(fading));
  auto renderFade=[&](){Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());draw(true);Check(d->EndScene());};
  renderFade();auto current=snapshot();unsigned count=pixels();Require(count>=previousCount,"fade coverage is monotonic");
  if(!previous.empty())for(size_t i=0;i<current.size();++i)if(previous[i]!=background)Require(current[i]==previous[i],"existing samples do not brighten at fade threshold");
  renderFade();Require(current==snapshot(),"stationary fade has no temporal flicker");
  if(opacity==128){
   // A far fullscreen plane may fill uncovered samples only. This catches the
   // former soft pass, whose faded mesh left no depth for the fog composite.
   struct Screen{float x,y,z,w;DWORD color;};Screen quad[]={{-.5f,-.5f,.99999f,1,0xff00ff00},{1919.5f,-.5f,.99999f,1,0xff00ff00},{-.5f,1079.5f,.99999f,1,0xff00ff00},{1919.5f,1079.5f,.99999f,1,0xff00ff00}};
   Check(d->SetVertexShader(nullptr));Check(d->SetPixelShader(nullptr));Check(d->SetFVF(D3DFVF_XYZRHW|D3DFVF_DIFFUSE));Check(d->SetRenderState(D3DRS_LIGHTING,0));
   Check(d->SetTexture(0,nullptr));Check(d->SetTextureStageState(0,D3DTSS_COLOROP,D3DTOP_SELECTARG1));Check(d->SetTextureStageState(0,D3DTSS_COLORARG1,D3DTA_DIFFUSE));
   Check(d->BeginScene());Check(d->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,quad,sizeof(Screen)));Check(d->EndScene());auto behind=snapshot();
   for(size_t i=0;i<current.size();++i)Require(current[i]==background?behind[i]==0xff00ff00:behind[i]==current[i],"fade colour/depth coverage agree");
   Check(d->SetVertexShader(vs));Check(d->SetPixelShader(ps));
  }
  printf("Fade %d/255: %u covered pixels\n",opacity,count);previous=std::move(current);previousCount=count;
 }
 Require(previousCount>2000,"large source mesh fade fixture");puts("PASS stable monotonic fade, solid-threshold continuity, depth coverage and repeated frames");
 local=false;Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());draw(true);Check(d->EndScene());Require(pixels()>2000,"ordinary two-pass mesh path retained");local=true;
 Upload(models[0].instances,models[0].data.data(),unsigned(models[0].data.size()*sizeof(Instance)));p[38]=v[38]=1;
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,0,0));Check(d->BeginScene());draw(false);Check(d->EndScene());Require(pixels()==0,"foreground depth occludes far meshes");
 IDirect3DQuery9 *start=nullptr,*end=nullptr,*freq=nullptr,*disjoint=nullptr;
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&start));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&end));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&freq));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&disjoint));
 std::vector<double> times;
 for(int frame=0;frame<40;++frame){Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());Check(disjoint->Issue(D3DISSUE_BEGIN));Check(start->Issue(D3DISSUE_END));draw(false);
  Check(end->Issue(D3DISSUE_END));Check(disjoint->Issue(D3DISSUE_END));Check(freq->Issue(D3DISSUE_END));Check(d->EndScene());UINT64 a=0,b=0,hz=0;BOOL bad=1;
  ReadQuery(end,&b,8);ReadQuery(start,&a,8);ReadQuery(freq,&hz,8);ReadQuery(disjoint,&bad,4);if(frame>=8&&!bad&&hz)times.push_back(double(b-a)*1000/hz);}
 Require(!times.empty(),"GPU timing samples");std::sort(times.begin(),times.end());unsigned visible=pixels();Require(visible>5000,"dense scene is visible");
 printf("PASS GPU: %zu instances, %u triangles/pass, %u changed pixels; one pass at 1920x1080 median %.3f ms p95 %.3f ms\n",rocks.size(),triangles,visible,times[times.size()/2],times[(times.size()-1)*95/100]);
 // Last argument is the preview path; the nine asset arguments precede it.
 Check(D3DXSaveSurfaceToFileA(argv[12],D3DXIFF_PNG,target,nullptr,nullptr));
 return 0;
}
