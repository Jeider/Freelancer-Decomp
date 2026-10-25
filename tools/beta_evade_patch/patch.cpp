// Freelancer Beta only. Addresses are RVAs from the two SHA256-locked images.
// No retail headers: the Beta class layouts differ from retail.
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include "verified_files.h"

using byte = unsigned char;
static byte *exe, *common;
static void *activeDrastic;
static void *activeEvade;
static bool requestingEvade;
static unsigned evadeUpdateDepth;
static bool installed;
static char logPath[MAX_PATH];
template<class T> static T& at(void* p, unsigned o) { return *reinterpret_cast<T*>(static_cast<byte*>(p)+o); }
template<class F> static F cf(unsigned rva) { return reinterpret_cast<F>(common+rva); }
template<class F> static F imp(unsigned rva) { return at<F>(exe,rva); }
using Method = void(__thiscall*)(void*);
using Request = void(__thiscall*)(void*,int,bool);
using Eval = int(__thiscall*)(void*,unsigned);
using Submit = bool(__thiscall*)(void*,const void*,const void*);
static Request originalRequest;

static void log(const char* s) {
    HANDLE f=CreateFileA(logPath,FILE_APPEND_DATA,FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_ALWAYS,FILE_ATTRIBUTE_NORMAL,nullptr);
    if(f!=INVALID_HANDLE_VALUE) { DWORD n; WriteFile(f,s,(DWORD)strlen(s),&n,nullptr); WriteFile(f,"\r\n",2,&n,nullptr); CloseHandle(f); }
}
static void* playerShip() {
    void* rw=reinterpret_cast<void*(__cdecl*)()>(exe+0x12B160)();
    if(!rw) return nullptr;
    void* ship=at<void*>(rw,0x10);
    return ship && (at<unsigned>(ship,0x4c)&0x503)==0x503 ? ship : nullptr;
}
static void* manager(void* ship) { return ship ? imp<void*(__thiscall*)(void*)>(0x1C043C)(ship) : nullptr; }
static void* behavior(void* mgr,int id) { return mgr ? at<void*>(mgr,0x164+id*4) : nullptr; }
static unsigned targetId(void* ship) {
    void* target=imp<void*(__thiscall*)(void*)>(0x1C03C8)(ship);
    if(!target) return 0;
    unsigned type=0;
    // Same Beta IObjInspect::get_type slot and ship mask as Trail evaluate.
    if(at<int(__thiscall*)(void*,unsigned*)>(at<void*>(target,0),0x84)(target,&type)!=0 ||
       !(type&0x7f0000) || (type&0x200000)) return 0;
    void* self=reinterpret_cast<void*(__cdecl*)()>(exe+0x12B160)();
    if(target==self) return 0;
    return at<unsigned(__thiscall*)(void*)>(at<void*>(target,0),0x20)(target);
}
static bool isPlayerBehavior(void* b,int id) { return b==behavior(manager(playerShip()),id); }
static bool canStart(void* ship,void* mgr) {
    if(!ship || !mgr || cf<bool(__thiscall*)(void*)>(0x52630)(ship)) return false;
    int current=at<int>(mgr,0xc0);
    // Conservative prototype: no interruption of docking, goto, formation,
    // lane docking or other autopilot sequences, even if their mask is open.
    return current==-1 || current==19 || current==5 || current==18;
}

// Only these two vtable entries change. The manager's outer mask/mission lock
// checks still execute, and NPCs retain the original EvalSkip result.
static int __fastcall evadeAvailable(void* b,void*,unsigned) {
    void* ship=playerShip();
    void* mgr=manager(ship);
    if(!canStart(ship,mgr) || b!=behavior(mgr,5)) return 2;
    return targetId(ship) ? 1 : 2;
}
static int __fastcall drasticAvailable(void* b,void*,unsigned) {
    void* ship=playerShip();void* mgr=manager(ship);
    return canStart(ship,mgr) && b==behavior(mgr,18) ? 1 : 2;
}

// Beta's first 0x94 Personality bytes are EvadeDodge (0x58) + EvadeBreak
// (0x3c). Scope the pilot tuning to the player's synchronous AI invocation;
// original personality bytes are restored even across nested Slot3/Slot4 calls.
struct Profile {
    byte* dst; byte saved[0x94];
    explicit Profile(void* b):dst(static_cast<byte*>(at<void*>(b,0x24))+0xD80) {
        memcpy(saved,dst,sizeof saved);
        memset(dst,0,sizeof saved);
        auto f=[&](unsigned off,float v){at<float>(dst,off)=v;};
        f(0x00,1500); f(0x04,0.65f); f(0x08,0.35f);
        f(0x14,0.7853982f); f(0x18,0.15f); f(0x1c,0.3f); f(0x20,0.25f);
        f(0x24,0.55f); f(0x28,0.1f); f(0x2c,100); f(0x30,2.4f);
        f(0x34,0.6f); f(0x38,0.7f); f(0x3c,0.15f); f(0x40,1);
        for(unsigned o=0x48;o<=0x54;o+=4) f(o,1);
        f(0x58,1.0f); f(0x5c,1.0f); f(0x60,0.2f);
        for(unsigned o=0x68;o<=0x74;o+=4) f(o,1);
        f(0x78,0.2f); f(0x7c,0.8f); f(0x80,1); // sideways break
        f(0x8c,0.5f); f(0x90,150);
    }
    ~Profile(){memcpy(dst,saved,sizeof saved);}
};
static void __fastcall evadeStart(void* b,void*) {
    if((requestingEvade || b==activeEvade) && isPlayerBehavior(b,5)) { activeEvade=b;Profile p(b); cf<Method>(0x6A7B0)(b); }
    else cf<Method>(0x6A7B0)(b);
}
static void __fastcall evadeUpdate(void* b,void*) {
    if(b==activeEvade && isPlayerBehavior(b,5)) { Profile p(b); ++evadeUpdateDepth;cf<Method>(0x6A2B0)(b);--evadeUpdateDepth; }
    else cf<Method>(0x6A2B0)(b);
}
static void __fastcall evadeStop(void* b,void*) {
    cf<Method>(0x6AB30)(b);
    // Native update also calls stop/start for internal Dodge/Break phases.
    if(b==activeEvade && !evadeUpdateDepth) activeEvade=nullptr;
}
static void clearNudge(void* b) {
    float zero[3]={};
    void* affect=static_cast<byte*>(at<void*>(b,0x14))+4;
    at<void(__thiscall*)(void*,const float*)>(at<void*>(affect,0),8)(affect,zero);
}
static void __fastcall drasticStop(void* b,void*) {
    if(b==activeDrastic) { if(isPlayerBehavior(b,18)) clearNudge(b); activeDrastic=nullptr; log("DrasticEvade: exit cleanup."); }
    cf<Method>(0x6AF20)(b);
}
static void __fastcall drasticUpdate(void* b,void*) {
    cf<Method>(0x6AFA0)(b);
    if(b==activeDrastic && isPlayerBehavior(b,18) && at<unsigned>(b,0x10)!=1) clearNudge(b);
}
struct DirectiveInfo { unsigned kind,priority; int behavior; };
struct EvadeOp { unsigned vptr,type,unknown,target; };
struct DrasticOp { unsigned vptr,type,unknown,mode; float direction[3],duration; unsigned tail[4]; };
static_assert(sizeof(EvadeOp)==0x10 && sizeof(DrasticOp)==0x30,"Beta directive ABI");
static_assert(offsetof(DrasticOp,duration)==0x1c,"Beta duration offset");

static void __fastcall requestHook(void* hud,void*,int id,bool flag) {
    if(id!=5 && id!=18) { originalRequest(hud,id,flag); return; }
    void* ship=playerShip(); void* mgr=manager(ship);
    if(!mgr || cf<Eval>(0x76C70)(mgr,id)==2) { log("Request rejected by native availability/mission mask."); return; }
    DirectiveInfo info={1,0,id};
    bool submitted=false;
    if(id==5) {
        EvadeOp op={}; cf<Method>(0x7EA40)(&op); op.target=targetId(ship);
        if(!op.target) return;
        requestingEvade=true;
        submitted=cf<Submit>(0x769E0)(mgr,&info,&op);
        requestingEvade=false;
        if(submitted) activeEvade=behavior(mgr,5);
        log(submitted ? "Evade: submitted with selected target and scoped pilot profile." : "Evade: submission returned false.");
    } else {
        DrasticOp op={}; cf<Method>(0x7EAA0)(&op);
        op.mode=0; op.direction[0]=1.0f; op.duration=0.45f;
        // SetCurrentBehavior cleans the previous state, including the same ID.
        // Arm after that cleanup, before the next simulation update.
        submitted=cf<Submit>(0x769E0)(mgr,&info,&op);
        if(submitted) activeDrastic=behavior(mgr,18);
        log(submitted ? "DrasticEvade: submitted, rightward nudge for 0.45 seconds." : "DrasticEvade: submission returned false.");
    }
    // IDs 5/18 have no original local directive branch. Calling the original
    // preserves its exact SetManeuver notification, target and player client ID.
    if(submitted) originalRequest(hud,id,flag);
}

struct Patch { void* dst; byte old[6]; size_t n; };
static Patch changes[12]; static unsigned changeCount;
static bool write(void* dst,const void* src,size_t n) {
    DWORD protect;
    if(!VirtualProtect(dst,n,PAGE_EXECUTE_READWRITE,&protect)) return false;
    memcpy(dst,src,n); FlushInstructionCache(GetCurrentProcess(),dst,n);
    DWORD unused; return VirtualProtect(dst,n,protect,&unused)!=0;
}
static bool patch(void* dst,const void* data,size_t n) {
    Patch& p=changes[changeCount++]; p.dst=dst;p.n=n;memcpy(p.old,dst,n);
    return write(dst,data,n);
}
static bool slot(unsigned rva,unsigned expected,void* hook) {
    void* dst=common+rva;
    if(at<void*>(dst,0)!=common+expected) return false;
    return patch(dst,&hook,4);
}
static void rollback() { while(changeCount) { Patch& p=changes[--changeCount];write(p.dst,p.old,p.n); } }

extern "C" __declspec(dllexport) DWORD WINAPI BetaPatchInitialize(void*) {
    if(installed) return 1;
    exe=reinterpret_cast<byte*>(GetModuleHandleW(nullptr));
    common=reinterpret_cast<byte*>(GetModuleHandleW(L"Common.dll"));
    if(!common) return 10;
    GetModuleFileNameA(nullptr,logPath,MAX_PATH); char* slash=strrchr(logPath,'\\');
    if(!slash) return 11; strcpy_s(slash+1,MAX_PATH-(slash+1-logPath),"beta_evade_patch.log");
    wchar_t path[MAX_PATH]; GetModuleFileNameW(nullptr,path,MAX_PATH);
    if(!verifyFile(path,kExeHash)) return 12;
    GetModuleFileNameW(reinterpret_cast<HMODULE>(common),path,MAX_PATH);
    if(!verifyFile(path,kCommonHash)) return 13;
    const byte expected[]={0x81,0xec,0xc0,0,0,0};
    if(memcmp(exe+0xBD7F0,expected,6)) return 14;
    const byte hudExpected[]={0x83,0xf8,0x12,0x75,0x08};
    if(memcmp(exe+0xBD04F,hudExpected,5) || exe[0xBCFBC]!=0x75 || exe[0xBCFBD]!=0x50) return 18;
    byte* trampoline=static_cast<byte*>(VirtualAlloc(nullptr,11,MEM_COMMIT|MEM_RESERVE,PAGE_READWRITE));
    if(!trampoline) return 15;
    memcpy(trampoline,expected,6);trampoline[6]=0xe9;
    at<int32_t>(trampoline,7)=int32_t((exe+0xBD7F6)-(trampoline+11));
    DWORD previous; if(!VirtualProtect(trampoline,11,PAGE_EXECUTE_READ,&previous)) return 16;
    FlushInstructionCache(GetCurrentProcess(),trampoline,11);
    originalRequest=reinterpret_cast<Request>(trampoline);
    byte jump[6]={0xe9,0,0,0,0,0x90};at<int32_t>(jump,1)=int32_t(reinterpret_cast<byte*>(&requestHook)-(exe+0xBD7F5));
    const byte showDrastic[]={0xe9,8,0,0,0};const byte keepOtherButtons=0xeb;
    if(!slot(0x143064,0x6A240,reinterpret_cast<void*>(&evadeAvailable)) ||
       !slot(0x1430DC,0x6A240,reinterpret_cast<void*>(&drasticAvailable)) ||
       !slot(0x143058,0x6A7B0,reinterpret_cast<void*>(&evadeStart)) ||
       !slot(0x14305C,0x6AB30,reinterpret_cast<void*>(&evadeStop)) ||
       !slot(0x143068,0x6A2B0,reinterpret_cast<void*>(&evadeUpdate)) ||
       !slot(0x1430D4,0x6AF20,reinterpret_cast<void*>(&drasticStop)) ||
       !slot(0x1430E0,0x6AFA0,reinterpret_cast<void*>(&drasticUpdate)) ||
       !patch(exe+0xBD7F0,jump,6) ||
       !patch(exe+0xBD04F,showDrastic,5) || !patch(exe+0xBCFBC,&keepOtherButtons,1)) {
        rollback();VirtualFree(trampoline,0,MEM_RELEASE);log("Initialization failed; changes rolled back.");return 17;
    }
    installed=true;log("Beta Evade patch installed in memory; original binaries unchanged.");return 1;
}
BOOL WINAPI DllMain(HINSTANCE,DWORD,LPVOID) { return TRUE; }
