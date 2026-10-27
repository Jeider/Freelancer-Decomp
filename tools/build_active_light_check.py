from pathlib import Path
import runpy
h=runpy.run_path('tools/build_shadow_cache_check.py');f=h['function'];s=h['rp']
body=f(s,'unsigned int FDirectX9::ExCollectSurfaceLights(').replace('FDirectX9::','Collector::')
prefix=r'''
#include <windows.h>
#include <d3d9.h>
#include "../../src/RP9/RP9LightCompatibility.h"
#include <map>
#include <vector>
#include <cassert>
#include <cstring>
#include <cstdio>
struct FRp9LightRecord{bool bEnabled=false;const D3DLIGHT9* Data=nullptr;};
std::map<unsigned long,FRp9LightRecord> G_LightRecords;
std::vector<std::pair<unsigned long,FRp9LightRecord*>> G_SurfaceActiveLights;
bool G_SurfaceActiveLightsDirty=true;
struct State{std::map<unsigned long,D3DLIGHT9> SurfaceDirectLights;};
struct Collector{State E;State* Ex_=&E;unsigned ExCollectSurfaceLights(D3DLIGHT9*,unsigned);};
'''
main=r'''
int main(){
 Collector c;D3DLIGHT9 lights[20]={};
 for(unsigned i=0;i<20;i++){lights[i].Range=(float)i;G_LightRecords[i]={i%3==0,&lights[i]};}
 auto check=[&](){for(unsigned capacity=0;capacity<=8;capacity++){
  D3DLIGHT9 got[8]={},ref[8]={};unsigned n=0;
  for(auto const& item:G_LightRecords){if(n==capacity)break;if(!item.second.bEnabled)continue;
   if(item.second.Data)ref[n++]=Rp9CompatibleLight(*item.second.Data);else{auto it=c.E.SurfaceDirectLights.find(item.first);if(it!=c.E.SurfaceDirectLights.end())ref[n++]=Rp9CompatibleLight(it->second);}}
  unsigned actual=c.ExCollectSurfaceLights(got,capacity);assert(actual==n&&!memcmp(got,ref,n*sizeof(D3DLIGHT9)));
 }};
 check();check();lights[3].Range=12345;check();
 G_LightRecords[0].bEnabled=false;G_LightRecords[1].bEnabled=true;G_SurfaceActiveLightsDirty=true;check();
 G_LightRecords[3].Data=nullptr;c.E.SurfaceDirectLights[3]=lights[7];check();
 G_SurfaceActiveLightsDirty=true;G_LightRecords.erase(6);check();
 G_SurfaceActiveLightsDirty=true;G_LightRecords.clear();check();
 puts("PASS: active-light iteration matches original handle ordering and capacity; live data, direct lights, enable changes and deletion preserved");
}
'''
Path('src/obj/active_light_check.cpp').write_text(prefix+body+main)
