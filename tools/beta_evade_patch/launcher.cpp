#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdio.h>
#include <string>
#include "verified_files.h"

static void error(const wchar_t* text) { MessageBoxW(nullptr,text,L"Freelancer Beta Evade patch",MB_OK|MB_ICONERROR); }
static bool remoteCall(HANDLE process,LPTHREAD_START_ROUTINE fn,void* arg,DWORD& result) {
    HANDLE thread=CreateRemoteThread(process,nullptr,0,fn,arg,0,nullptr);
    if(!thread)return false;
    // No timeout/unload race: the game main thread remains suspended until this
    // deliberately short bootstrap finishes. No existing game is attached to.
    DWORD wait=WaitForSingleObject(thread,INFINITE);
    bool ok=wait==WAIT_OBJECT_0 && GetExitCodeThread(thread,&result);
    CloseHandle(thread);return ok;
}
int wmain(int argc,wchar_t** argv) {
    wchar_t path[MAX_PATH];GetModuleFileNameW(nullptr,path,MAX_PATH);
    wchar_t* slash=wcsrchr(path,L'\\'); if(!slash)return 1;*slash=0;
    std::wstring dir=path,game=dir+L"\\FreeLancer.exe",common=dir+L"\\Common.dll",dll=dir+L"\\beta_evade_patch.dll";
    if(!verifyFile(game.c_str(),kExeHash)||!verifyFile(common.c_str(),kCommonHash)) {
        fwprintf(stderr,L"Unsupported or missing Beta binaries. Nothing launched.\n");
        if(argc<2)error(L"Binary SHA256 check failed. This patch supports the inspected Freelancer Beta only.");return 2;
    }
    HMODULE local=LoadLibraryExW(dll.c_str(),nullptr,DONT_RESOLVE_DLL_REFERENCES);
    if(!local){if(argc<2)error(L"Cannot map beta_evade_patch.dll.");return 3;}
    auto init=GetProcAddress(local,"_BetaPatchInitialize@4");
    if(!init){FreeLibrary(local);return 4;}
    uintptr_t initRva=reinterpret_cast<uintptr_t>(init)-reinterpret_cast<uintptr_t>(local);
    FreeLibrary(local);
    if(argc==2 && wcscmp(argv[1],L"--verify")==0){puts("Beta SHA256 and patch export verified; no game launched.");return 0;}
    std::wstring command=L"\""+game+L"\" -w";
    STARTUPINFOW si={sizeof(si)};PROCESS_INFORMATION pi={};
    if(!CreateProcessW(game.c_str(),&command[0],nullptr,nullptr,FALSE,CREATE_SUSPENDED,nullptr,dir.c_str(),&si,&pi)){error(L"Could not launch Freelancer Beta.");return 5;}
    bool ok=false;DWORD module=0,status=0;
    size_t bytes=(dll.size()+1)*sizeof(wchar_t);
    void* remote=VirtualAllocEx(pi.hProcess,nullptr,bytes,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE);
    SIZE_T written=0;
    if(remote && WriteProcessMemory(pi.hProcess,remote,dll.c_str(),bytes,&written) && written==bytes) {
        auto load=reinterpret_cast<LPTHREAD_START_ROUTINE>(GetProcAddress(GetModuleHandleW(L"kernel32.dll"),"LoadLibraryW"));
        if(remoteCall(pi.hProcess,load,remote,module) && module) {
            ok=remoteCall(pi.hProcess,reinterpret_cast<LPTHREAD_START_ROUTINE>(uintptr_t(module)+initRva),nullptr,status) && status==1;
        }
    }
    if(remote)VirtualFreeEx(pi.hProcess,remote,0,MEM_RELEASE);
    // On bootstrap failure initialization rolls back its hooks. Leave a normal
    // vanilla Beta running; never kill an existing game or this new process.
    ResumeThread(pi.hThread);CloseHandle(pi.hThread);CloseHandle(pi.hProcess);
    if(!ok){wchar_t message[256];swprintf_s(message,L"Patch initialization failed (status %lu). Beta was resumed without the patch. See beta_evade_patch.log.",status);error(message);return 6;}
    return 0;
}
