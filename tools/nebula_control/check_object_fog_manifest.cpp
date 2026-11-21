#include "RP9ShaderStartup.h"
#include <cassert>
#include <set>
// Shader/device validation in a hidden window; no startup UI and no game.
static std::string CacheKey(Rp9Startup::FJob const&job,std::string const&directory){
 Rp9Startup::DirectoryInclude include(directory);ID3DXBuffer*expanded=nullptr,*errors=nullptr;
 HRESULT hr=D3DXPreprocessShader(job.Text.data(),(UINT)job.Text.size(),nullptr,job.UseInclude?&include:nullptr,&expanded,&errors);
 if(errors)errors->Release();if(FAILED(hr)||!expanded)return {};
 std::string text((char*)expanded->GetBufferPointer());expanded->Release();
 // Match the production cache's removal of process-specific #line paths.
 for(size_t at=text.find("#line");at!=std::string::npos;at=text.find("#line",at+5)){
  size_t end=text.find('\n',at),quote=text.find('"',at);
  if(quote!=std::string::npos && (end==std::string::npos || quote<end))text.erase(quote,(end==std::string::npos?text.size():end)-quote);
 }
 return Rp9ShaderCache::Key(text,job.Entry,job.Profile,Rp9ShaderCache::FlagsForSource(job.Text)|job.Flags);
}
int main(int argc,char**argv){
 if(argc!=3)return 2;setvbuf(stdout,nullptr,_IONBF,0);
 SetEnvironmentVariableA("FREELANCER_SHADER_CACHE_DIR",argv[2]);
 std::string directory=argv[1],error;std::vector<Rp9Startup::FJob> jobs;
 if(!Rp9Startup::Build(directory,jobs,error)){puts(error.c_str());return 2;}
#ifdef SURFACE_SCATTER_CHECK
 // Check affected production variants at every quality, including full shadows.
 jobs.clear();std::set<std::string> seen;
 for(int quality=0;quality<=3;++quality){std::vector<Rp9Startup::FJob> batch;
  if(!Rp9Startup::Build(directory,batch,error,quality,quality,quality))return 2;
  for(auto const&job:batch)if(job.Name=="surface_material.hlsl" || job.Name=="far_rocks.hlsl")
   if(seen.insert(job.Text+job.Entry+job.Profile).second)jobs.push_back(job);
 }
#endif
#if defined(ASTEROID_SPAWN_CHECK) && !defined(ASTEROID_FOG_COVERAGE_CHECK)
 jobs.clear();std::set<std::string> fadeSeen;
 for(int quality=0;quality<=3;++quality){std::vector<Rp9Startup::FJob> batch;
  if(!Rp9Startup::Build(directory,batch,error,quality,quality,quality))return 2;
  for(auto const&job:batch)if(job.Text.find("float4 ObjectCoverage : register(c109)")!=std::string::npos)
   if(fadeSeen.insert(job.Text+job.Entry+job.Profile).second)jobs.push_back(job);
 }
 if(jobs.size()!=56)return 5; // 14 opaque coverage variants at four qualities
#endif
 auto*api=Direct3DCreate9(D3D_SDK_VERSION);if(!api)return 2;
 HWND window=CreateWindowA("STATIC","fog shader check",WS_POPUP,0,0,32,32,nullptr,nullptr,GetModuleHandle(nullptr),nullptr);
 D3DPRESENT_PARAMETERS pp={};pp.Windowed=1;pp.SwapEffect=D3DSWAPEFFECT_DISCARD;pp.hDeviceWindow=window;
 pp.BackBufferWidth=pp.BackBufferHeight=32;pp.BackBufferFormat=D3DFMT_A8R8G8B8;IDirect3DDevice9*device=nullptr;
 if(FAILED(api->CreateDevice(0,D3DDEVTYPE_HAL,window,D3DCREATE_HARDWARE_VERTEXPROCESSING,&pp,&device)))return 2;
 for(unsigned pass=0;pass<2;++pass){unsigned hits=0,failed=0,previous=~0u;
  std::vector<Rp9Startup::Result> results;
  if(!Rp9Startup::Prepare(jobs,directory,results,[&](unsigned done,unsigned total){
   if(done!=previous){printf("pass %u: %u/%u\n",pass,done,total);previous=done;}return true;
  }))return 3;
  for(size_t i=0;i<jobs.size();++i){auto&job=jobs[i];auto&result=results[i];
   HRESULT hr=Rp9Startup::Validate(device,job,result);hits+=result.Hit;
   if(FAILED(hr) || (pass && !result.Hit)){
    printf("FAIL job %zu hr=%08lx prefix=%.240s\n%s\n",i,(unsigned long)hr,job.Text.c_str(),result.Message.c_str());++failed;
   }
   if(pass){std::string key=CacheKey(job,directory);std::vector<unsigned char> persisted;
    if(!Rp9ShaderCache::Load(key,&persisted) || persisted!=result.Code)return 4;
    printf("CACHE %s.bin\n",key.c_str());}
  }
  printf("PASS %u: %zu shaders, %u cache hits, %u failures\n",pass,jobs.size(),hits,failed);
  if(failed)return 3;
 }
 device->Release();api->Release();DestroyWindow(window);return 0;
}
