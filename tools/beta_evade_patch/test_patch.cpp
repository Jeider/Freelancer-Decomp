// Native x86 ABI harness: real hook bodies, fake Beta memory/callbacks.
#include "patch.cpp"
#include <assert.h>
static byte shipMem[0x80],rwMem[0x20],mgrMem[0x200],navMem[0xE20];
static byte evadeMem[0x400],drasticMem[0x80],npcMem[0x400],npcNav[0xE20];
static byte targetMem[8],targetVtable[0x90],owner[16],affectVtable[16];
static int originalCalls,submitCalls,startCalls,updateCalls;
static unsigned lastTarget;
static bool haveTarget=true,finishDrastic=false;
static bool usingLane=false;
static unsigned targetType=0x10000;
static float lastNudge[3];
static void* __cdecl fakePlayer() {return rwMem;}
static void* __fastcall fakeManager(void*,void*) {return mgrMem;}
static void* __fastcall fakeTarget(void*,void*) {return haveTarget?targetMem:nullptr;}
static unsigned __fastcall fakeTargetId(void*,void*) {return 1234;}
static int __fastcall fakeTargetType(void*,void*,unsigned* type) {*type=targetType;return 0;}
static bool __fastcall fakeLane(void*,void*) {return usingLane;}
static void __fastcall fakeNudge(void*,void*,const float* v) {memcpy(lastNudge,v,sizeof lastNudge);}
static void __fastcall fakeStop(void*,void*) {}
static void __fastcall fakeEvadeStart(void* b,void*) {
    ++startCalls;
    if(b==evadeMem) {auto nav=at<void*>(b,0x24);assert(at<float>(nav,0xD84)==0.65f);assert(at<float>(nav,0xDB0)==2.4f);}
    else assert(at<float>(at<void*>(b,0x24),0xD84)==77.0f);
}
static void __fastcall fakeEvadeUpdate(void* b,void*) {
    ++updateCalls;assert(at<float>(at<void*>(b,0x24),0xDB0)==2.4f);
    evadeStart(b,nullptr); // nested RAII must restore outer profile first
    assert(at<float>(at<void*>(b,0x24),0xDB0)==2.4f);
}
static void __fastcall fakeDrasticUpdate(void* b,void*) {
    lastNudge[0]=finishDrastic?0.0f:1.0f;
    at<unsigned>(b,0x10)=finishDrastic?2:1;
}
static int __fastcall fakeEvaluate(void*,void*,unsigned id) {
    if(at<unsigned>(mgrMem,0xB8)&(2u<<id))return 2;
    if(at<byte>(mgrMem,0xBC) && at<int>(mgrMem,0xC0)!=(int)id)return 2;
    return id==5?evadeAvailable(evadeMem,nullptr,0):drasticAvailable(drasticMem,nullptr,0);
}
static void __fastcall fakeEvadeCtor(void* op,void*) {at<unsigned>(op,4)=10;}
static void __fastcall fakeDrasticCtor(void* op,void*) {at<unsigned>(op,4)=11;}
static bool __fastcall fakeSubmit(void*,void*,const DirectiveInfo* info,const void* raw) {
    ++submitCalls;assert(info->kind==1 && info->priority==0);
    if(at<int>(mgrMem,0xC0)==18)drasticStop(drasticMem,nullptr);
    if(at<int>(mgrMem,0xC0)==5)evadeStop(evadeMem,nullptr);
    at<int>(mgrMem,0xC0)=info->behavior;
    if(info->behavior==5) {
        auto op=static_cast<const EvadeOp*>(raw);assert(op->type==10);lastTarget=op->target;
        evadeStart(evadeMem,nullptr);
    } else {
        auto op=static_cast<const DrasticOp*>(raw);
        assert(op->type==11 && op->mode==0 && op->direction[0]==1 && op->direction[1]==0 && op->duration==0.45f);
    }
    return true;
}
static void __fastcall fakeOriginal(void*,void*,int id,bool) {
    ++originalCalls;
    if(id==19){if(at<int>(mgrMem,0xC0)==18)drasticStop(drasticMem,nullptr);if(at<int>(mgrMem,0xC0)==5)evadeStop(evadeMem,nullptr);at<int>(mgrMem,0xC0)=19;}
}
static void thunk(byte* address,void* fn) {address[0]=0xe9;at<int32_t>(address,1)=int32_t(static_cast<byte*>(fn)-(address+5));}
int main() {
    exe=static_cast<byte*>(VirtualAlloc(nullptr,0x200000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    common=static_cast<byte*>(VirtualAlloc(nullptr,0x200000,MEM_COMMIT|MEM_RESERVE,PAGE_EXECUTE_READWRITE));
    assert(exe && common);
    thunk(exe+0x12B160,reinterpret_cast<void*>(&fakePlayer));
    at<void*>(exe,0x1C043C)=reinterpret_cast<void*>(&fakeManager);
    at<void*>(exe,0x1C03C8)=reinterpret_cast<void*>(&fakeTarget);
    thunk(common+0x76C70,reinterpret_cast<void*>(&fakeEvaluate));
    thunk(common+0x769E0,reinterpret_cast<void*>(&fakeSubmit));
    thunk(common+0x7EA40,reinterpret_cast<void*>(&fakeEvadeCtor));
    thunk(common+0x7EAA0,reinterpret_cast<void*>(&fakeDrasticCtor));
    thunk(common+0x6A7B0,reinterpret_cast<void*>(&fakeEvadeStart));
    thunk(common+0x6A2B0,reinterpret_cast<void*>(&fakeEvadeUpdate));
    thunk(common+0x6AF20,reinterpret_cast<void*>(&fakeStop));
    thunk(common+0x6AB30,reinterpret_cast<void*>(&fakeStop));
    thunk(common+0x52630,reinterpret_cast<void*>(&fakeLane));
    thunk(common+0x6AFA0,reinterpret_cast<void*>(&fakeDrasticUpdate));
    originalRequest=reinterpret_cast<Request>(&fakeOriginal);
    at<void*>(rwMem,0x10)=shipMem;at<unsigned>(shipMem,0x4c)=0x503;
    at<void*>(mgrMem,0x164+5*4)=evadeMem;at<void*>(mgrMem,0x164+18*4)=drasticMem;
    at<void*>(evadeMem,0x24)=navMem;at<void*>(npcMem,0x24)=npcNav;
    at<void*>(targetMem,0)=targetVtable;at<void*>(targetVtable,0x20)=reinterpret_cast<void*>(&fakeTargetId);
    at<void*>(targetVtable,0x84)=reinterpret_cast<void*>(&fakeTargetType);
    at<void*>(drasticMem,0x14)=owner;at<void*>(owner,4)=affectVtable;at<void*>(affectVtable,8)=reinterpret_cast<void*>(&fakeNudge);
    memset(navMem+0xD80,0x5a,0x94);byte saved[0x94];memcpy(saved,navMem+0xD80,0x94);
    at<int>(mgrMem,0xC0)=19;
    haveTarget=false;assert(evadeAvailable(evadeMem,nullptr,0)==2);
    requestHook(nullptr,nullptr,5,false);assert(!submitCalls && !originalCalls);
    haveTarget=true;at<unsigned>(mgrMem,0xB8)=2u<<5;
    requestHook(nullptr,nullptr,5,false);assert(!submitCalls);
    at<unsigned>(mgrMem,0xB8)=0;at<byte>(mgrMem,0xBC)=1;at<int>(mgrMem,0xC0)=19;
    requestHook(nullptr,nullptr,18,false);assert(!submitCalls);
    at<byte>(mgrMem,0xBC)=0;
    usingLane=true;requestHook(nullptr,nullptr,18,false);assert(!submitCalls);usingLane=false;
    at<int>(mgrMem,0xC0)=2;requestHook(nullptr,nullptr,18,false);assert(!submitCalls);at<int>(mgrMem,0xC0)=19;
    targetType=1;requestHook(nullptr,nullptr,5,false);assert(!submitCalls);targetType=0x10000;
    requestHook(nullptr,nullptr,5,false);
    assert(submitCalls==1 && originalCalls==1 && lastTarget==1234 && startCalls==1);
    assert(memcmp(saved,navMem+0xD80,0x94)==0);
    evadeUpdate(evadeMem,nullptr);assert(updateCalls==1 && memcmp(saved,navMem+0xD80,0x94)==0);
    at<float>(npcNav,0xD84)=77;evadeStart(npcMem,nullptr);assert(at<float>(npcNav,0xD84)==77);
    assert(evadeAvailable(npcMem,nullptr,0)==2);
    requestHook(nullptr,nullptr,19,false);assert(activeEvade==nullptr);
    requestHook(nullptr,nullptr,18,false);assert(activeDrastic==drasticMem);
    drasticUpdate(drasticMem,nullptr);assert(lastNudge[0]==1);
    requestHook(nullptr,nullptr,19,false);assert(lastNudge[0]==0 && activeDrastic==nullptr);
    requestHook(nullptr,nullptr,18,false);requestHook(nullptr,nullptr,18,false);assert(activeDrastic==drasticMem);
    finishDrastic=true;drasticUpdate(drasticMem,nullptr);assert(lastNudge[0]==0);
    int calls=originalCalls;requestHook(nullptr,nullptr,13,true);assert(originalCalls==calls+1);
    // Patch transaction restores bytes and does not touch adjacent memory.
    byte old[6]={1,2,3,4,5,6},replacement[6]={6,5,4,3,2,1};memcpy(exe+16,old,6);
    assert(patch(exe+16,replacement,6));rollback();assert(memcmp(exe+16,old,6)==0);
    puts("PASS x86 hooks: native calling conventions, target ID, mask/lock rejection, scoped/nested player profile, NPC isolation, cancel/completion/repeat cleanup, original notification dispatch, rollback.");
    return 0;
}
