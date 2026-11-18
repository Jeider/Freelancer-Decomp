// Standalone D3D9 test of the real room vertex shader, without starting the game.
#include <windows.h>
#include <d3d9.h>
#include <d3dx9.h>
#include <algorithm>
#include <cmath>
#include <cstdio>
#include <fstream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

static void Require(bool value,const char* message){if(!value)throw std::runtime_error(message);}
static void Check(HRESULT hr){if(FAILED(hr)){char b[80];sprintf_s(b,"D3D HRESULT %08lx",hr);throw std::runtime_error(b);}}
static std::string Read(const char* path){std::ifstream f(path,std::ios::binary);Require(bool(f),"shader source missing");return {std::istreambuf_iterator<char>(f),{}};}
static ID3DXBuffer* Compile(const std::string& source,const char* entry,const char* profile){
 ID3DXBuffer* code=nullptr,*messages=nullptr;
 HRESULT hr=D3DXCompileShader(source.data(),(UINT)source.size(),nullptr,nullptr,entry,profile,0,&code,&messages,nullptr);
 if(messages){if(FAILED(hr))printf("%s\n",(char*)messages->GetBufferPointer());messages->Release();}Check(hr);return code;
}
struct Vertex{float p[3],w[3];DWORD bones;float n[3],uv[3][2];};
static float Difference(const std::vector<float>& a,const std::vector<float>& b){
 float d=0;for(size_t i=0;i<a.size();++i){if(!std::isfinite(a[i])||!std::isfinite(b[i]))return INFINITY;d=(std::max)(d,std::abs(a[i]-b[i]));}return d;
}

int main(int argc,char** argv){try{
 SetErrorMode(SEM_FAILCRITICALERRORS|SEM_NOGPFAULTERRORBOX|SEM_NOOPENFILEERRORBOX);
 Require(argc==3,"expected old and fixed shader source paths");
 const std::string old=Read(argv[1]),fixed=Read(argv[2]);
 HWND window=CreateWindowA("STATIC","UV regression",WS_POPUP,0,0,64,64,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 auto* api=Direct3DCreate9(D3D_SDK_VERSION);Require(api!=nullptr,"D3D9 unavailable");
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=TRUE;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.BackBufferWidth=pp.BackBufferHeight=64;pp.BackBufferFormat=D3DFMT_A8R8G8B8;
 IDirect3DDevice9* device=nullptr;Check(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device));
 D3DADAPTER_IDENTIFIER9 adapter={};Check(api->GetAdapterIdentifier(0,0,&adapter));printf("GPU: %s\n",adapter.Description);
 IDirect3DSurface9* target=nullptr,*read=nullptr;
 Check(device->CreateRenderTarget(64,64,D3DFMT_A32B32G32R32F,D3DMULTISAMPLE_NONE,0,FALSE,&target,nullptr));
 Check(device->CreateOffscreenPlainSurface(64,64,D3DFMT_A32B32G32R32F,D3DPOOL_SYSTEMMEM,&read,nullptr));
 Check(device->SetRenderTarget(0,target));Check(device->SetDepthStencilSurface(nullptr));
 Check(device->SetRenderState(D3DRS_ZENABLE,FALSE));Check(device->SetRenderState(D3DRS_CULLMODE,D3DCULL_NONE));
 Check(device->SetRenderState(D3DRS_ALPHABLENDENABLE,FALSE));
 D3DVERTEXELEMENT9 elements[]={
  {0,0,D3DDECLTYPE_FLOAT3,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_POSITION,0},
  {0,12,D3DDECLTYPE_FLOAT3,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_BLENDWEIGHT,0},
  {0,24,D3DDECLTYPE_UBYTE4,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_BLENDINDICES,0},
  {0,28,D3DDECLTYPE_FLOAT3,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_NORMAL,0},
  {0,40,D3DDECLTYPE_FLOAT2,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_TEXCOORD,0},
  {0,48,D3DDECLTYPE_FLOAT2,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_TEXCOORD,1},
  {0,56,D3DDECLTYPE_FLOAT2,D3DDECLMETHOD_DEFAULT,D3DDECLUSAGE_TEXCOORD,2},D3DDECL_END()};
 IDirect3DVertexDeclaration9* declaration=nullptr;Check(device->CreateVertexDeclaration(elements,&declaration));Check(device->SetVertexDeclaration(declaration));
 // Read back both selected UVs directly in FP32, before texture filtering or lighting.
 const char* diagnostic="float4 main(float2 a:TEXCOORD2,float2 b:TEXCOORD3):COLOR0{return float4(a,b);}";
 auto* pixelCode=Compile(diagnostic,"main","ps_3_0");IDirect3DPixelShader9* pixel=nullptr;
 Check(device->CreatePixelShader((DWORD*)pixelCode->GetBufferPointer(),&pixel));pixelCode->Release();Check(device->SetPixelShader(pixel));
 auto* finalPixel=Compile(fixed,"PSMain","ps_3_0");finalPixel->Release();
 D3DXMATRIX identity;D3DXMatrixIdentity(&identity);
 for(UINT offset:{0u,4u,8u,12u,16u,216u})Check(device->SetVertexShaderConstantF(offset,(float*)&identity,4));
 float colours[4]={};Check(device->SetVertexShaderConstantF(21,colours,1));
 float bones[24]={1,0,0,0, 0,1,0,0, 0,0,1,0, 1,0,0,.15f, 0,1,0,0, 0,0,1,0};Check(device->SetVertexShaderConstantF(24,bones,6));
 Vertex q[4]={};for(int i=0;i<4;++i){q[i].p[0]=(i&2)?.8f:-.8f;q[i].p[1]=(i&1)?.8f:-.8f;q[i].p[2]=.5f;
  q[i].w[0]=.6f;q[i].w[1]=.4f;q[i].bones=0x00000100;q[i].n[2]=-1;
  for(int k=0;k<3;++k){q[i].uv[k][0]=.07f+.13f*k+((i&2)?.3f:0);q[i].uv[k][1]=.02f+.17f*k+((i&1)?.2f:0);}}
 auto render=[&](IDirect3DVertexShader9* vs,const Vertex* vertices){
  Check(device->SetVertexShader(vs));Check(device->Clear(0,nullptr,D3DCLEAR_TARGET,0,1,0));Check(device->BeginScene());
  Check(device->DrawPrimitiveUP(D3DPT_TRIANGLESTRIP,2,vertices,sizeof(Vertex)));Check(device->EndScene());Check(device->GetRenderTargetData(target,read));
  D3DLOCKED_RECT lock;Check(read->LockRect(&lock,nullptr,D3DLOCK_READONLY));std::vector<float> values;
  for(int y=10;y<54;++y){auto* row=(float*)((char*)lock.pBits+y*lock.Pitch);values.insert(values.end(),row+10*4,row+54*4);}Check(read->UnlockRect());return values;
 };
 unsigned finiteCases=0,poisonCases=0,oldFailures=0;float finiteDelta=0,poisonDelta=0;
 for(auto entry:{"VSMain","VSSkin"}){
  auto* a=Compile(old,entry,"vs_3_0");auto* b=Compile(fixed,entry,"vs_3_0");IDirect3DVertexShader9* previous=nullptr,*next=nullptr;
  Check(device->CreateVertexShader((DWORD*)a->GetBufferPointer(),&previous));Check(device->CreateVertexShader((DWORD*)b->GetBufferPointer(),&next));a->Release();b->Release();
  for(int x=0;x<3;++x)for(int y=0;y<3;++y)for(int transforms=0;transforms<4;++transforms){
   float mode[4]={(float)x,(float)y,(transforms&1)?2.f:0.f,(transforms&2)?2.f:0.f};Check(device->SetVertexShaderConstantF(20,mode,1));
   D3DXMATRIX t0=identity,t1=identity;t0._11=1.7f;t0._22=.6f;t0._31=.12f;t0._32=.07f;t1._11=.8f;t1._22=1.4f;t1._31=.18f;t1._32=.09f;
   Check(device->SetVertexShaderConstantF(12,(float*)&t0,4));Check(device->SetVertexShaderConstantF(16,(float*)&t1,4));
   auto reference=render(previous,q),normal=render(next,q);float diff=Difference(reference,normal);Require(diff<.000002f,"finite UV/transform regression");finiteDelta=(std::max)(finiteDelta,diff);++finiteCases;
   for(int unused=0;unused<3;++unused){if(unused==x||unused==y)continue;
    for(float poison:{std::numeric_limits<float>::quiet_NaN(),std::numeric_limits<float>::infinity()}){
     Vertex invalid[4];memcpy(invalid,q,sizeof(q));invalid[2].uv[unused][0]=poison;
     auto was=render(previous,invalid),now=render(next,invalid);float broken=Difference(reference,was);diff=Difference(normal,now);
     if(!(broken<.000002f))++oldFailures;
     Require(diff<.000002f,"unused invalid UV contaminates selected channel");poisonDelta=(std::max)(poisonDelta,diff);++poisonCases;
    }
   }
  }
  previous->Release();next->Release();
 }
 Require(oldFailures>0,"negative control did not reproduce original defect");
 printf("PASS: finite cases=%u max_delta=%.9g; NaN/Inf cases=%u max_delta=%.9g; old failures=%u\n",finiteCases,finiteDelta,poisonCases,poisonDelta,oldFailures);
 Check(device->SetVertexShader(nullptr));Check(device->SetPixelShader(nullptr));pixel->Release();declaration->Release();target->Release();read->Release();device->Release();api->Release();DestroyWindow(window);return 0;
}catch(const std::exception& error){printf("FAIL: %s\n",error.what());return 1;}}
