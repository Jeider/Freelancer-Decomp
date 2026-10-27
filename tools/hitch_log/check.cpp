#include "runtime_hitch_log.inl"
#include <thread>
#include <cassert>
int main(){
 BeginRuntimeHitchFrame();assert(RuntimeHitches::Active.load());
 assert(RuntimeHitchGetSink()!=nullptr);
 {RuntimeHitchScope frame("frame","fixture frame",0);Sleep(12);
  {RuntimeHitchScope sound("sound_load","voice,\"test\".wav",0);Sleep(5);}
 }
 std::thread t([](){RuntimeHitchScope texture("texture","worker.dds",0);Sleep(5);});t.join();
 HMODULE dll=LoadLibraryW(L"hitch_fixture.dll");assert(dll);
 auto run=reinterpret_cast<void(*)()>(GetProcAddress(dll,"RunFixture"));assert(run);run();FreeLibrary(dll);
 BeginRuntimeHitchFrame();
 Sleep(350); // Let the writer flush; inspect while it still owns the file.
 wchar_t path[MAX_PATH];swprintf_s(path,L"%s_0.csv",RuntimeHitches::Prefix);
 HANDLE reader=CreateFileW(path,GENERIC_READ,FILE_SHARE_READ|FILE_SHARE_WRITE|FILE_SHARE_DELETE,
                          nullptr,OPEN_EXISTING,0,nullptr);
 assert(reader!=INVALID_HANDLE_VALUE);
 char bytes[512];DWORD read=0;assert(ReadFile(reader,bytes,sizeof(bytes),&read,nullptr) && read>0);
 CloseHandle(reader);
 RuntimeHitches::Stop();
 assert(!RuntimeHitches::Worker && RuntimeHitches::Dropped.load()==0);
}
