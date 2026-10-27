#pragma once
#include <windows.h>

// Optional client export: DLLs also work unchanged in FLServer and older clients.
using RuntimeHitchSink = void (__cdecl*)(const char*, const char*, LONGLONG, LONGLONG);
inline LONGLONG RuntimeHitchNow(){LARGE_INTEGER t;QueryPerformanceCounter(&t);return t.QuadPart;}
inline RuntimeHitchSink RuntimeHitchGetSink(){
 static auto sink=reinterpret_cast<RuntimeHitchSink>(GetProcAddress(GetModuleHandleW(nullptr),"FreelancerHitchEvent"));
 return sink;
}
class RuntimeHitchScope {
 const char* Category;const char* Resource;LONGLONG Start;double Threshold;bool Running;
public:
 RuntimeHitchScope(const char* category,const char* resource,double threshold=1.0)
  :Category(category),Resource(resource),Start(RuntimeHitchNow()),Threshold(threshold),Running(true){}
 RuntimeHitchScope(const RuntimeHitchScope&)=delete;
 RuntimeHitchScope& operator=(const RuntimeHitchScope&)=delete;
 void Stop(){
  if(!Running)return;Running=false;const auto end=RuntimeHitchNow();
  static const double scale=[](){LARGE_INTEGER f;QueryPerformanceFrequency(&f);return 1000.0/f.QuadPart;}();
  if((end-Start)*scale>=Threshold)if(auto sink=RuntimeHitchGetSink())sink(Category,Resource,Start,end);
 }
 ~RuntimeHitchScope(){Stop();}
};
