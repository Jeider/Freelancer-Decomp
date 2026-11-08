// Execute production rpg_dialog.cpp with fake rendering/THN/Content boundaries.
#include <windows.h>
#include <cassert>
#include <cstdint>
#include <cstdlib>
#include <cstring>
#include <cstdio>
#include <string>
#include <vector>
#define FREELANCER_RPG_WORLD
#include "../../src/freelancer/Client/rpg_dialog_model.h"
#include "../../src/freelancer/Client/rpg_gesture_rotation.h"
struct RenderDisplayList {};
struct StyleNode { StyleNode(int){} void* Clone(){return nullptr;} };
struct TextNode {TextNode(wchar_t const*,int){} void* Clone(){return nullptr;}};
void RdlAppendNode(RenderDisplayList&,void*){}
struct Win3D {
    virtual ~Win3D()=default;
    virtual bool Create(Win3D*,void*){return true;}
    virtual intptr_t SetProperty(int,uintptr_t,uintptr_t){return 0;}
};
struct WinControl:Win3D {
    char const* ClassName="";int DrawLayer=0,DrawSubLayer=0;unsigned char Flags=3;
    void SetName(char const*){} void SetPosition(float const*){} void CaptureMouse(){}
};
struct RichTextWin:WinControl {void ClearContent(){}void AppendContent(RenderDisplayList&){}void SetNeverHit(bool){}};
RichTextWin* CreateRichTextWin(char const*,float,float,float const*,bool){static RichTextWin r[64];static int n=0;return &r[n++%64];}
WinControl* CreateWireButtonControl(char const*,char const*,float const*,float const*,int,int,int,int,int){static WinControl w[64];static int n=0;return &w[n++%64];}
void SetLetterboxTarget(float,float){} void SetClientMouseCursorDrawFlag(int){}
unsigned GetPlayerConnectionId(){return 1;}
struct ShipParkingStatus {unsigned BaseId=1;};
using ShipParkingStatusFn=int(*)(unsigned,ShipParkingStatus*);
constexpr int ParkingOk=0;
namespace Universe {struct Base {unsigned GetStridName()const{return 0;}};Base const* get_base(unsigned){return nullptr;}}
void GetIdsStringW(unsigned,wchar_t*,int){}
void GetIdsStringWWithRawFallback(unsigned,wchar_t*,int){}
char const* Language="en";
char const* PortVoice(){return Language;}char const* PortExeDirectory(){return "D:/test/bin/";}
struct Engine{};
int Stops=0,Acquires=0,Releases=0,Actions=0;
int EnglishVoiceMs=2000,RussianVoiceMs=15000;
struct Script {
    struct SoundEvent { int StartMs,EndMs; };
    std::vector<SoundEvent> SoundEvents;
    bool RpgBoundActors=false,RpgFragment=false;void* Mirror=nullptr;int Time=0,Duration=100;bool Torn=false;
    void Start(Engine*,char const* file,int,int,int,int,int,int,char const*,int,int){
        if(strstr(file,"\\gestures\\")) Duration=1000;
        else SoundEvents.push_back({150,150+(strstr(file,"\\ru\\")?RussianVoiceMs:EnglishVoiceMs)});
    }
    bool Update(int ms){Time+=ms;return Time>=Duration;}
    void Teardown(){if(!Torn){Torn=true;++Stops;}}
    void Pause(){}
};
struct FGfScriptSequence;
struct FGfScriptEntry {
    ::Script* Script=nullptr;::Engine* Engine=nullptr;char* ScriptFile=nullptr;int Frame=0;
    void Create(void*,FGfScriptSequence*){Script=new ::Script;}
    ~FGfScriptEntry(){delete Script;delete Engine;free(ScriptFile);}
};
struct FGfScriptSequence {
    struct MirrorType {void* First(){return this;}} Mirror;
    FGfScriptEntry Entries[1];int Current=0,Priority=0;char const* Name="spot";void* Room=this;
    FGfScriptSequence(){Entries[0].Script=new ::Script;}
};
int CameraSwitches=0;
struct CameraMock {
    void GetTransform(float* p){p[0]=42;}
    void GetFov(float*){} void GetNear(float*){} void GetFar(float*){}
    void SetTransform(float const* p){assert(p[0]==42);++CameraSwitches;}
    void SetFov(float*){} void SetNear(float*){} void SetFar(float*){}
};
struct Manager {CameraMock* FindCreatedEntity(int,char const*){static CameraMock camera;return &camera;}} G_GfScriptManager;
void* RoomControlPlayerCharacter(void* p){return p;}
void malloc_strcpy(char** p,char const* s){*p=_strdup(s);}
Engine* ThornScriptLoad(char const*){return new Engine;}
void GfScriptCharacterAnimations(Engine*,bool a){a?++Acquires:++Releases;}
void GfScriptTouchEntities(Engine*,bool){}
struct CharacterDb {void FlushQueuedScripts(){}};
CharacterDb* GetCharacterInfoDb(){static CharacterDb db;return &db;}
void RpgDialogClose(FGfScriptSequence*);
bool MissingFile=false;
DWORD FileAttributes(char const*){return MissingFile?INVALID_FILE_ATTRIBUTES:0;}
#define GetFileAttributesA FileAttributes
unsigned Begin(unsigned,unsigned){return 1;}
unsigned Start(unsigned){return 1;}
char const* Group(unsigned){return "rm0001";}
char const* GestureGroup(unsigned id){return id==2?"rm0201":"rm0001";}
char const* Fragment(unsigned,unsigned,int,unsigned){return "rm0001_frag0001";}
int Count(unsigned,unsigned node){return node==1?2:0;}
unsigned Choose(unsigned,unsigned,int,unsigned){++Actions;return 2;}
wchar_t const* Render(unsigned,unsigned,int,unsigned){return L"line";}
unsigned EscapeNode(unsigned,unsigned,unsigned){return 0;}
void End(unsigned){}
FARPROC Proc(HMODULE,char const* name){
    if(!strcmp(name,"RpgDialogBeginSession"))return reinterpret_cast<FARPROC>(Begin);
    if(!strcmp(name,"RpgDialogStart"))return reinterpret_cast<FARPROC>(Start);
    if(!strcmp(name,"RpgDialogSceneGroup"))return reinterpret_cast<FARPROC>(Group);
    if(!strcmp(name,"RpgDialogGestureGroup"))return reinterpret_cast<FARPROC>(GestureGroup);
    if(!strcmp(name,"RpgDialogFragment"))return reinterpret_cast<FARPROC>(Fragment);
    if(!strcmp(name,"RpgDialogChoiceCount"))return reinterpret_cast<FARPROC>(Count);
    if(!strcmp(name,"RpgDialogChoose"))return reinterpret_cast<FARPROC>(Choose);
    if(!strcmp(name,"RpgDialogRenderText"))return reinterpret_cast<FARPROC>(Render);
    if(!strcmp(name,"RpgDialogEscape"))return reinterpret_cast<FARPROC>(EscapeNode);
    if(!strcmp(name,"RpgDialogEndSession"))return reinterpret_cast<FARPROC>(End);
    return nullptr;
}
#define GetProcAddress Proc
#include "client.inc"
int main(){
    FGfScriptSequence owner;
    RpgDialogOpenTree(&owner,1);assert(Dialog && Dialog->Speaking && Dialog->Speech);
    Dialog->Choose(0);assert(!Actions && Dialog->PendingChoice==-1);
    assert(RpgDialogHandleKey(WM_KEYDOWN,VK_ESCAPE,0));assert(!Dialog->Speaking && !Actions);
    assert(CameraSwitches==1 && Dialog->GestureStep[0]==2 && Dialog->GestureStep[1]==0);
    auto* vendorGesture=Dialog->Gestures[0];
    assert(vendorGesture && !vendorGesture->Script->Torn);
    assert(RpgDialogHandleKey(WM_KEYDOWN,VK_ESCAPE,1u<<30));assert(!Dialog->Model.Done);
    RpgDialogHandleKey(WM_KEYUP,VK_ESCAPE,0);
    Dialog->Choose(0);assert(Dialog->Speaking && !Actions && Dialog->PendingChoice==0);
    RpgDialogHandleKey(WM_KEYDOWN,VK_ESCAPE,0);
    assert(Actions==1 && Dialog->Speaking && Dialog->NodeId==2);
    assert(Dialog->GestureStep[0]==2 && Dialog->GestureStep[1]==2);
    assert(Dialog->Gestures[0]==vendorGesture && !vendorGesture->Script->Torn);
    RpgDialogHandleKey(WM_KEYDOWN,VK_ESCAPE,1u<<30);
    assert(Dialog->Speaking && Actions==1);
    RpgDialogHandleKey(WM_KEYUP,VK_ESCAPE,0);
    RpgDialogUpdate(&owner,100);assert(!Dialog && !Owner && Actions==1);
    assert(Acquires==Releases && Stops==5);
    RpgDialogOpenTree(&owner,1);assert(Dialog->Speaking);
    RpgDialogUpdate(&owner,100);assert(!Dialog->Speaking && Dialog->Gestures[0]);
    RpgDialogUpdate(&owner,900);assert(!Dialog->Gestures[0]);
    RpgDialogUpdate(&owner,100);assert(Dialog->GestureStep[0]==2 && !Dialog->Gestures[0]);
    assert(Dialog->StartLine(-1));
    assert(Dialog->GestureStep[0]==3 && strstr(Dialog->Gestures[0]->ScriptFile,"vendor_03.thn"));
    RpgDialogClose(&owner);assert(!Dialog && Acquires==Releases);
    // A release after closing a terminal line cannot leak into the game's menu.
    RpgDialogOpenTree(&owner,1);RpgDialogUpdate(&owner,100);Dialog->Choose(1);
    RpgDialogUpdate(&owner,100);assert(Actions==2 && Dialog->Speaking);
    RpgDialogHandleKey(WM_KEYDOWN,VK_ESCAPE,0);RpgDialogUpdate(&owner,1);
    assert(!Dialog);assert(RpgDialogHandleKey(WM_KEYUP,VK_ESCAPE,0));
    MissingFile=true;RpgDialogOpenTree(&owner,1);assert(!Dialog->Speaking);
    Dialog->Choose(0);assert(Actions==3 && Dialog->Speaking && !Dialog->Speech);
    RpgDialogUpdate(&owner,2500);assert(!Dialog && Acquires==Releases);
    MissingFile=false;
    // Selection uses localized sound length, never the scene's facial tail.
    EnglishVoiceMs=14999;
    RpgDialogOpenTree(&owner,1);
    assert(strstr(Dialog->Gestures[0]->ScriptFile,"vendor_02.thn"));
    RpgDialogClose(&owner);
    Language="ru";
    RpgDialogOpenTree(&owner,1);
    assert(strstr(Dialog->Speech->ScriptFile,"\\ru\\"));
    assert(strstr(Dialog->Gestures[0]->ScriptFile,"vendor_01.thn"));
    // Even a long Trent line may only use FSTHIPB and CROSS/UNCROSS.
    unsigned const Allowed[] = {1,2,4,5,6,7,1};
    for(unsigned Step:Allowed) {
        Dialog->StartGesture(1,60000);
        char Name[32];sprintf_s(Name,"player_%02u.thn",Step+1);
        assert(strstr(Dialog->Gestures[1]->ScriptFile,Name));
        auto* WholeStep=Dialog->Gestures[1];
        Dialog->StartGesture(1,1000);assert(Dialog->Gestures[1]==WholeStep);
        Dialog->UpdateGestures(1000);
    }
    RpgDialogClose(&owner);assert(Acquires==Releases);
    assert(RpgGestureRotation::Next(3,false,14999)==4);
    assert(RpgGestureRotation::Next(3,false,15000)==3);
    assert(RpgGestureRotation::Next(0,false,0)==1);
    RpgDialogOpenTree(&owner,2);
    assert(strstr(Dialog->Speech->ScriptFile,"\\rm0001\\"));
    assert(strstr(Dialog->Gestures[0]->ScriptFile,"\\rm0201\\"));
    RpgDialogClose(&owner);assert(Acquires==Releases);
    puts("PASS: native duration/role gesture selection, RU/EN timing, CONV threshold, ordered CROSS/UNCROSS and uninterrupted steps");
    puts("PASS: production client speech, deferred exactly-once choice, natural completion, single-fragment Esc/repeats/release, teardown and missing-THN fallback");
}
