// Standalone D3D9 validation of the production shader, LOD data, grouping and draw helper.
#include <windows.h>
#include <d3dx9.h>
#include <algorithm>
#include <chrono>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <set>
#include <string>
#include <vector>
#include "RP9MeshInstances.h"
#include "RP9ShaderManifest.h"
#include "../../src/include/procedural_asteroids.h"
#include "../../src/freelancer/Client/asteroid_lod_data.h"
#include "../../src/freelancer/Client/asteroid_lod_policy.h"
static void Require(bool v,char const* msg){if(!v){printf("FAIL %s\n",msg);exit(3);}}
static void Check(HRESULT h){if(FAILED(h)){printf("HRESULT %08lx\n",h);exit(2);}}
static void Set(float* p,int i,float a,float b,float c,float e){p+=i*4;p[0]=a;p[1]=b;p[2]=c;p[3]=e;}
using FRPExBuffer=IDirect3DVertexBuffer9;
using FMeshVertex=AsteroidLodData::Vertex;
struct FMeshInstance {float CentreRadius[4],Rotation[4];unsigned Colour;};
struct FMeshLod {std::vector<FMeshVertex> Vertices;std::vector<FMeshInstance> Instances,Scratch;
 FRPExBuffer* Geometry=nullptr,*Placement=nullptr;size_t Capacity=0;};
struct FMeshBatch {std::vector<FMeshVertex> Vertices;std::vector<FMeshInstance> Instances;
 FRPExBuffer* Geometry=nullptr,*Placement=nullptr;FMeshLod Lods[3];std::vector<unsigned char> LastLod;
 unsigned LodCellRevision=0;float SourceRadius=0;IDirect3DTexture9* Texture=nullptr;};
struct FFarField {FMeshBatch Meshes[3];unsigned LodRevision=~0u,LocalMeshRevision=1,LocalCellRevision=1;
 double LodPixels=0,LodCamera[3]={},Anchor[3]={};float FarDist=6000;int TexCount=3;};
constexpr HRESULT GR_OK=S_OK;
struct Pipeline {IDirect3DDevice9* d=nullptr;unsigned creates=0,updates=0;
 HRESULT CreateExVertexBuffer(unsigned bytes,void const* data,FRPExBuffer** b){++creates;
  auto h=d->CreateVertexBuffer(bytes,0,0,D3DPOOL_MANAGED,b,nullptr);if(FAILED(h))return h;
  void* p=nullptr;Check((*b)->Lock(0,bytes,&p,0));memcpy(p,data,bytes);Check((*b)->Unlock());return S_OK;}
 HRESULT UpdateExVertexBuffer(FRPExBuffer* b,unsigned offset,unsigned bytes,void const* data){++updates;
  void* p=nullptr;auto h=b->Lock(offset,bytes,&p,0);if(FAILED(h))return h;memcpy(p,data,bytes);return b->Unlock();}
 void DestroyExVertexBuffer(FRPExBuffer* b){b->Release();}
} pipeline;
namespace RenderEx {Pipeline* GetPipelineEx(){return &pipeline;}}
#include "../../src/freelancer/Client/asteroid_lod_batches.inl"
static void ReadQuery(IDirect3DQuery9* q,void* p,unsigned size){DWORD start=GetTickCount();HRESULT h;
 while((h=q->GetData(p,size,D3DGETDATA_FLUSH))==S_FALSE){Require(GetTickCount()-start<10000,"GPU timeout");Sleep(0);}Check(h);}
int main(int argc,char** argv){
 Require(argc==13,"shader dir, cache, three mesh/texture/radius triples, preview");setvbuf(stdout,nullptr,_IONBF,0);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9");IDirect3DDevice9* d=nullptr;
 HWND w=CreateWindowA("STATIC","asteroid LOD probe",WS_POPUP,0,0,1920,1080,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=1920;pp.BackBufferHeight=1080;
 pp.BackBufferFormat=D3DFMT_A8R8G8B8;pp.EnableAutoDepthStencil=1;pp.AutoDepthStencilFormat=D3DFMT_D24S8;
 Check(api->CreateDevice(0,D3DDEVTYPE_HAL,w,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&d));pipeline.d=d;
 D3DADAPTER_IDENTIFIER9 adapter={};Check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU: %s\n",adapter.Description);
 SetEnvironmentVariableA("FREELANCER_SHADER_CACHE_DIR",argv[2]);std::vector<Rp9Startup::FJob> jobs;std::string error;
 Require(Rp9Startup::Build(argv[1],jobs,error),error.c_str());
 IDirect3DVertexShader9* vs[2]={};IDirect3DPixelShader9* ps[2]={};unsigned compiled=0;
 for(auto const& job:jobs)if((job.Name=="far_rocks.hlsl"&&(!strcmp(job.Entry,"VSMesh")||!strcmp(job.Entry,"PSMesh")))||job.Name=="asteroid_simple.hlsl"){
  int k=job.Name=="asteroid_simple.hlsl"?1:0;std::vector<unsigned char> code;std::string msg;bool hit=false;
  auto h=Rp9Startup::Compile(job,argv[1],code,msg,hit);if(FAILED(h))puts(msg.c_str());Check(h);++compiled;
  ID3DXBuffer* disassembly=nullptr;Check(D3DXDisassembleShader((DWORD*)code.data(),FALSE,nullptr,&disassembly));
  std::ofstream listing(std::string(argv[2])+"/"+job.Entry+".txt");listing.write((char*)disassembly->GetBufferPointer(),disassembly->GetBufferSize());disassembly->Release();
  if(job.Profile[0]=='v')Check(d->CreateVertexShader((DWORD*)code.data(),&vs[k]));else Check(d->CreatePixelShader((DWORD*)code.data(),&ps[k]));
 }
 Require(compiled==4&&vs[0]&&vs[1]&&ps[0]&&ps[1],"old and minimal production shader pairs");
 FFarField field;
 for(int i=0;i<3;++i){auto& m=field.Meshes[i];unsigned n=0;std::ifstream f(argv[3+i*3],std::ios::binary);f.read((char*)&n,4);
  m.Vertices.resize(n);f.read((char*)m.Vertices.data(),n*sizeof(FMeshVertex));Require(f.good(),"source model bytes");
  auto* match=AsteroidLodData::Find(m.Vertices.data(),n*sizeof(FMeshVertex));Require(match==&AsteroidLodData::Models[i],"exact production mesh fingerprint selects baked LODs");
  auto original=m.Vertices[0].pos[0];m.Vertices[0].pos[0]+=.01f;
  Require(!AsteroidLodData::Find(m.Vertices.data(),n*sizeof(FMeshVertex)),"edited source safely rejects unrelated LODs");m.Vertices[0].pos[0]=original;
  double r2=0;for(auto const& v:m.Vertices){double a=0;for(float x:v.pos)a+=x*x;r2=(std::max)(r2,a);}
  m.SourceRadius=float(sqrt(r2));float inv=float(1./sqrt(r2));for(auto& v:m.Vertices)for(float& x:v.pos)x*=inv;
  Check(pipeline.CreateExVertexBuffer(n*32,m.Vertices.data(),&m.Geometry));
  for(int l=1;l<3;++l){auto& dest=m.Lods[l];auto const& src=match->levels[l-1];dest.Vertices.assign(src.vertices,src.vertices+src.count);
   for(auto& v:dest.Vertices)for(float& x:v.pos)x*=inv;Check(pipeline.CreateExVertexBuffer(src.count*32,dest.Vertices.data(),&dest.Geometry));}
  Check(D3DXCreateTextureFromFileA(d,argv[4+i*3],&m.Texture));
 }
 double eye[3]={30000,0,20000};float cellCentre[3]={30500,500,20500};
 ProceduralAsteroids::Around(cellCentre,ProceduralAsteroids::View+867,802,3,[&](auto const& rock){
  auto& m=field.Meshes[rock.model];FMeshInstance r={};memcpy(r.CentreRadius,rock.position,12);r.CentreRadius[3]=m.SourceRadius;
  memcpy(r.Rotation,rock.rotation,16);r.Colour=rock.colour|0xffff;m.Instances.push_back(r);
 });
 unsigned resident=0,nativeTriangles=0;for(auto& m:field.Meshes){resident+=unsigned(m.Instances.size());nativeTriangles+=unsigned(m.Instances.size()*m.Vertices.size()/3);
  Check(pipeline.CreateExVertexBuffer(unsigned(m.Instances.size()*36),m.Instances.data(),&m.Placement));}
 Require(PrepareLocalLods(field,eye,540),"production LOD grouping");
 auto validate=[&](){unsigned count=0;for(auto const& m:field.Meshes){std::multiset<std::string> expected,actual;
  for(auto const& r:m.Instances){double d2=0;for(int k=0;k<3;++k)d2+=pow(r.CentreRadius[k]-eye[k],2);
   if(r.CentreRadius[3]>0&&d2<=36000000)expected.emplace((char const*)&r,sizeof(r));}
  for(auto const& l:m.Lods)for(auto const& r:l.Instances){actual.emplace((char const*)&r,sizeof(r));++count;}
  Require(expected==actual,"all eligible instances exactly once, same pose, scale, texture and colour");}return count;};
 unsigned visible=validate();auto allocations=pipeline.creates,uploads=pipeline.updates;
 auto clock=std::chrono::steady_clock::now();for(int i=0;i<10000;++i)Require(PrepareLocalLods(field,eye,540),"stationary grouping");
 printf("PASS stationary LOD CPU %.6f ms/frame; no allocation/upload\n",std::chrono::duration<double,std::milli>(std::chrono::steady_clock::now()-clock).count()/10000);
 Require(allocations==pipeline.creates&&uploads==pipeline.updates,"no stationary GPU locks");
 eye[0]+=.00001;Require(PrepareLocalLods(field,eye,540),"subthreshold camera movement");Require(uploads==pipeline.updates,"no upload without a bucket change");eye[0]-=.00001;
 using AsteroidLod::Select;
 Require(Select(31*31,1,0)==0&&Select(33*33,1,1)==1&&Select(37*37,1,2)==0,"near LOD hysteresis and teleport");
 Require(Select(11*11,1,1)==1&&Select(13*13,1,2)==2&&Select(9*9,1,0)==2,"far LOD hysteresis");
 auto& instances=field.Meshes[0].Instances;
 auto it=std::find_if(instances.begin(),instances.end(),[&](auto const& r){double d2=0;for(int k=0;k<3;++k)d2+=pow(r.CentreRadius[k]-eye[k],2);return d2<25000000;});
 Require(it!=instances.end(),"visible death fixture");auto& changed=*it;auto saved=changed;changed.CentreRadius[3]=0;++field.LocalMeshRevision;
 Require(PrepareLocalLods(field,eye,540),"hidden/dead slot");Require(validate()+1==visible,"dead/excluded sample removed");changed=saved;++field.LocalMeshRevision;
 auto* backupGeometry=field.Meshes[0].Lods[2].Geometry;field.Meshes[0].Lods[2].Geometry=nullptr;++field.LocalMeshRevision;
 Require(PrepareLocalLods(field,eye,540),"missing geometry fallback");Require(field.Meshes[0].Lods[1].Instances.empty()&&field.Meshes[0].Lods[2].Instances.empty(),"unsupported model uses native geometry");validate();
 field.Meshes[0].Lods[2].Geometry=backupGeometry;++field.LocalMeshRevision;
 for(int i=0;i<60;++i){eye[0]+=3;Require(PrepareLocalLods(field,eye,540),"camera motion");validate();}
 eye[0]=30000;++field.LocalCellRevision;++field.LocalMeshRevision;Require(PrepareLocalLods(field,eye,540),"cell rebuild");Require(validate()==visible,"cell rebuild population");
 unsigned counts[3]={},lodTriangles=0;for(auto const& m:field.Meshes)for(int l=0;l<3;++l){auto n=unsigned(m.Lods[l].Instances.size());counts[l]+=n;lodTriangles+=n*unsigned((l?m.Lods[l].Vertices:m.Vertices).size()/3);}
 printf("PASS %u residents -> %u within 6 km, LOD populations %u/%u/%u, native submitted triangles %u -> %u\n",resident,visible,counts[0],counts[1],counts[2],nativeTriangles,lodTriangles);
 Require(counts[0]&&counts[1]&&counts[2]&&lodTriangles<nativeTriangles/3,"real triangle reduction, unchanged population");
 float v[56]={},p[48]={};Set(v,0,float(eye[0]),float(eye[1]),float(eye[2]),0);Set(v,1,1,0,0,0);Set(v,2,0,1,0,0);Set(v,3,0,0,1,0);
 Set(v,4,1080.f/1920,1,5000.f/4999,-5000.f/4999);Set(v,5,1,1,0,0);Set(v,6,5000,540,2,1-1.f/4194304);
 Set(v,7,0,1,4500,1.f/1500);Set(v,8,0,5,1,1);Set(v,10,0,1,1,0);
 Set(p,0,1,1,1,1);Set(p,5,80/255.f,40/255.f,0,0);Set(p,6,1,120/255.f,50/255.f,0);Set(p,7,.8f,0,.6f,1);Set(p,8,1,0,0,0);
 memcpy(v+44,p+20,48);
 Check(d->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));Check(d->SetRenderState(D3DRS_ZENABLE,1));Check(d->SetRenderState(D3DRS_ZWRITEENABLE,1));
 Check(d->SetRenderState(D3DRS_ZFUNC,D3DCMP_LESSEQUAL));Check(d->SetRenderState(D3DRS_ALPHABLENDENABLE,0));
 for(auto s:{D3DSAMP_MINFILTER,D3DSAMP_MAGFILTER,D3DSAMP_MIPFILTER})Check(d->SetSamplerState(0,s,D3DTEXF_LINEAR));
 FRp9MeshInstances renderer;IDirect3DSurface9 *target=nullptr,*read=nullptr;Check(d->GetRenderTarget(0,&target));Check(d->CreateOffscreenPlainSurface(1920,1080,D3DFMT_A8R8G8B8,D3DPOOL_SYSTEMMEM,&read,nullptr));
 const DWORD background=0xff181818;
 auto snapshot=[&](){Check(d->GetRenderTargetData(target,read));D3DLOCKED_RECT lock;Check(read->LockRect(&lock,nullptr,D3DLOCK_READONLY));std::vector<DWORD> pixels(1920*1080);
  for(int y=0;y<1080;++y)memcpy(pixels.data()+y*1920,(char*)lock.pBits+y*lock.Pitch,1920*4);Check(read->UnlockRect());return pixels;};
 auto draw=[&](int mode){Check(d->SetVertexShader(vs[mode?1:0]));Check(d->SetPixelShader(ps[mode?1:0]));
  Check(d->SetVertexShaderConstantF(0,v,14));Check(d->SetPixelShaderConstantF(0,p,12));
  for(auto& m:field.Meshes){Check(d->SetTexture(0,m.Texture));
   if(mode==0)Check(renderer.Draw(d,m.Geometry,m.Placement,unsigned(m.Vertices.size()),0,unsigned(m.Instances.size())));
   else for(int l=0;l<3;++l){auto& L=m.Lods[l];if(L.Instances.empty())continue;
    Check(renderer.Draw(d,mode==2&&l?L.Geometry:m.Geometry,L.Placement,unsigned(mode==2&&l?L.Vertices.size():m.Vertices.size()),0,unsigned(L.Instances.size())));}
  }};
 IDirect3DQuery9 *start=nullptr,*end=nullptr,*freq=nullptr,*disjoint=nullptr;
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&start));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMP,&end));
 Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPFREQ,&freq));Check(d->CreateQuery(D3DQUERYTYPE_TIMESTAMPDISJOINT,&disjoint));
 std::vector<double> timings[3];
 // Interleave variants to avoid measuring GPU clock drift as an optimization.
 for(int round=0;round<64;++round)for(int step=0;step<3;++step){int mode=(round+step)%3;
  Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());
  Check(disjoint->Issue(D3DISSUE_BEGIN));Check(start->Issue(D3DISSUE_END));draw(mode);
  Check(end->Issue(D3DISSUE_END));Check(disjoint->Issue(D3DISSUE_END));Check(freq->Issue(D3DISSUE_END));Check(d->EndScene());
  UINT64 a=0,b=0,hz=0;BOOL bad=1;ReadQuery(end,&b,8);ReadQuery(start,&a,8);ReadQuery(freq,&hz,8);ReadQuery(disjoint,&bad,4);
  if(round>=12&&!bad&&hz)timings[mode].push_back(double(b-a)*1000/hz);
 }
 for(int mode=0;mode<3;++mode){auto& t=timings[mode];Require(!t.empty(),"GPU timing samples");std::sort(t.begin(),t.end());
  printf("GPU mode %d: 1920x1080 median %.4f ms p95 %.4f ms\n",mode,t[t.size()/2],t[(t.size()-1)*95/100]);}
 auto render=[&](int mode){Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,1,0));Check(d->BeginScene());draw(mode);Check(d->EndScene());return snapshot();};
 auto frame=render(2);unsigned covered=0;for(auto c:frame)covered+=c!=background;Require(covered>3000,"dense LOD field visible");Require(frame==render(2),"stationary image stable");
 Check(d->Clear(0,nullptr,D3DCLEAR_TARGET|D3DCLEAR_ZBUFFER,background,0,0));Check(d->BeginScene());draw(2);Check(d->EndScene());
 for(auto c:snapshot())Require(c==background,"foreground depth occludes minimal shader");render(2);
 Check(D3DXSaveSurfaceToFileA(argv[12],D3DXIFF_PNG,target,nullptr,nullptr));
 // Compare silhouettes at the actual LOD thresholds over eight rotations.
 Set(v,0,0,0,0,0);Set(v,10,0,1,1,0);double worst=1;
 for(int model=0;model<3;++model)for(int level=1;level<3;++level)for(int angle=0;angle<8;++angle){
  for(auto& m:field.Meshes)for(auto& l:m.Lods)l.Instances.clear();auto& L=field.Meshes[model].Lods[level];
  FMeshInstance r={};r.CentreRadius[2]=-40*540.f/(level==1?28:12);r.CentreRadius[3]=40;r.Rotation[1]=sinf(angle*.392699f);r.Rotation[3]=cosf(angle*.392699f);r.Colour=0xff80ff00;
  L.Instances={r};Check(pipeline.UpdateExVertexBuffer(L.Placement,0,36,&r));auto reference=render(1);auto simplified=render(2);
  unsigned overlap=0,total=0;for(size_t i=0;i<reference.size();++i){bool a=reference[i]!=background,b=simplified[i]!=background;overlap+=a&&b;total+=a||b;}
  Require(total>50,"nonempty textured LOD at switching distance");double iou=double(overlap)/total;worst=(std::min)(worst,iou);
  Require(iou>.55,"LOD silhouette retains its source volume at the switching threshold");
 }
 printf("PASS all three models, two LOD thresholds, eight rotations: worst silhouette IoU %.3f\n",worst);
 // A contact sheet: native / middle / far, same native UVs and matched orientation.
 for(auto& m:field.Meshes)for(auto& l:m.Lods)l.Instances.clear();
 Set(v,0,0,0,0,0);Set(v,10,0,1,1,0);
 for(int model=0;model<3;++model)for(int level=0;level<3;++level){auto& m=field.Meshes[model];auto& L=m.Lods[level];
  FMeshInstance r={};r.CentreRadius[0]=float((level-1)*180);r.CentreRadius[1]=float((1-model)*125);r.CentreRadius[2]=-400;r.CentreRadius[3]=40;
  r.Rotation[3]=1;r.Colour=0xff80ffff;L.Instances={r};Check(pipeline.UpdateExVertexBuffer(L.Placement,0,36,&r));}
 render(2);std::string preview=std::string(argv[12])+".lods.png";Check(D3DXSaveSurfaceToFileA(preview.c_str(),D3DXIFF_PNG,target,nullptr,nullptr));
 puts("PASS production minimal shader and grouped LOD draws, stable image; game not launched");
 return 0;
}
