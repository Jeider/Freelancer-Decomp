// One bounded, nonblocking producer queue shared by client and instrumented DLLs.
// Included by client_tick_profile.cpp; no changes to any retail object layout.
#include "runtime_hitch_log.h"
#include <cstdio>
#include <cwchar>
#include <cstring>
#include <atomic>
#include <share.h>

namespace RuntimeHitches {
 struct Event {LONGLONG Start,End;DWORD Thread,Frame;char Category[32],Resource[320];};
 constexpr unsigned Capacity=4096;
 Event Queue[Capacity];unsigned Head=0,Tail=0;
 SRWLOCK Lock=SRWLOCK_INIT;
 std::atomic<bool> Active{false};std::atomic<DWORD> Frame{0};std::atomic<unsigned> Dropped{0};
 HANDLE Worker=nullptr,StopEvent=nullptr;LONGLONG Origin=0,Frequency=1,PreviousFrame=0;
 wchar_t Prefix[MAX_PATH]={};
 void Quoted(FILE*f,const char*s){fputc('"',f);for(;*s;++s){if(*s=='"')fputc('"',f);fputc(*s=='\r'||*s=='\n'?' ':*s,f);}fputc('"',f);}
 DWORD WINAPI WriteThread(void*){
  FILE*f=nullptr;unsigned part=0;long bytes=0;
  Event batch[128];bool stopping=false;
  do{
   stopping=WaitForSingleObject(StopEvent,250)==WAIT_OBJECT_0;
   for(;;){
    unsigned count=0;AcquireSRWLockExclusive(&Lock);
    while(Tail!=Head && count<128){batch[count++]=Queue[Tail];Tail=(Tail+1)%Capacity;}
    ReleaseSRWLockExclusive(&Lock);
    if(!count)break;
    if(!f || bytes>64*1024*1024){
     if(f)fclose(f);
     wchar_t path[MAX_PATH];swprintf_s(path,L"%s_%u.csv",Prefix,part++%3);
     // Secure fopen defaults to exclusive sharing on MSVC. Permit readers so
     // diagnostics can be inspected during play, without stopping the session.
     f=_wfsopen(path,L"wb",_SH_DENYNO);bytes=0;
     if(f)fputs("start_ms,end_ms,duration_ms,thread,frame,category,resource\n",f);
    }
    if(!f)continue;
    for(unsigned i=0;i<count;++i){const auto&e=batch[i];
     fprintf(f,"%.3f,%.3f,%.3f,%lu,%lu,",(e.Start-Origin)*1000.0/Frequency,
       (e.End-Origin)*1000.0/Frequency,(e.End-e.Start)*1000.0/Frequency,e.Thread,e.Frame);
     Quoted(f,e.Category);fputc(',',f);Quoted(f,e.Resource);fputc('\n',f);
    }
    bytes=ftell(f);
   }
   if(f){const auto dropped=Dropped.exchange(0);if(dropped)fprintf(f,"0,0,0,0,0,diagnostic,dropped_events=%u\n",dropped);fflush(f);}
  }while(!stopping);
  if(f)fclose(f);return 0;
 }
 void Start(){
  static bool tried=false;if(tried)return;tried=true;
  wchar_t disabled[8];if(GetEnvironmentVariableW(L"FREELANCER_HITCH_LOG",disabled,8) && disabled[0]==L'0')return;
  wchar_t folder[MAX_PATH];DWORD n=GetEnvironmentVariableW(L"LOCALAPPDATA",folder,MAX_PATH);
  if(!n || n>MAX_PATH-100)return;
  wcscat_s(folder,L"\\Freelancer-Decomp");CreateDirectoryW(folder,nullptr);
  wcscat_s(folder,L"\\Diagnostics");CreateDirectoryW(folder,nullptr);
  SYSTEMTIME t;GetLocalTime(&t);
  swprintf_s(Prefix,L"%s\\hitches_%04u%02u%02u_%02u%02u%02u_%lu",folder,t.wYear,t.wMonth,t.wDay,t.wHour,t.wMinute,t.wSecond,GetCurrentProcessId());
  LARGE_INTEGER freq;QueryPerformanceFrequency(&freq);Frequency=freq.QuadPart;Origin=RuntimeHitchNow();
  StopEvent=CreateEventW(nullptr,TRUE,FALSE,nullptr);if(!StopEvent)return;
  Worker=CreateThread(nullptr,0,WriteThread,nullptr,0,nullptr);
  if(!Worker){CloseHandle(StopEvent);StopEvent=nullptr;return;}
  Active=true;
 }
 void Stop(){
  Active=false;if(!Worker)return;
  SetEvent(StopEvent);WaitForSingleObject(Worker,INFINITE);
  CloseHandle(Worker);CloseHandle(StopEvent);Worker=StopEvent=nullptr;
 }
}
#pragma comment(linker,"/EXPORT:FreelancerHitchEvent=_FreelancerHitchEvent")
extern "C" void __cdecl FreelancerHitchEvent(const char* category,const char* resource,LONGLONG start,LONGLONG end){
 using namespace RuntimeHitches;if(!Active.load())return;
 Event e={start,end,GetCurrentThreadId(),Frame.load(),{}, {}};
 strncpy_s(e.Category,category?category:"",_TRUNCATE);strncpy_s(e.Resource,resource?resource:"",_TRUNCATE);
 if(!TryAcquireSRWLockExclusive(&Lock)){++Dropped;return;}
 unsigned next=(Head+1)%Capacity;
 if(next==Tail)++Dropped;else{Queue[Head]=e;Head=next;}
 ReleaseSRWLockExclusive(&Lock);
}
void BeginRuntimeHitchFrame(){
 using namespace RuntimeHitches;Start();if(!Active.load())return;
 const auto now=RuntimeHitchNow();++Frame;
 if(PreviousFrame && (now-PreviousFrame)*1000.0/Frequency>=16.0)
  FreelancerHitchEvent("frame_interval","includes previous tick, frame limiter and message pump",PreviousFrame,now);
 PreviousFrame=now;
}
