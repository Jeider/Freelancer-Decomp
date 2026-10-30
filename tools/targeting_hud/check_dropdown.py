"""Execute the complete production dropdown against recorded native UI boundaries."""
from pathlib import Path
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
CLIENT = ROOT / 'src/freelancer/Client'
OUT = ROOT / 'src/obj/dropdown_check'
OUT.mkdir(parents=True, exist_ok=True)


def source(name):
    return re.sub(r'^#(?:include|pragma)[^\n]*\n', '', (CLIENT / name).read_text(), flags=re.M)


def function(name, signature):
    text = (CLIENT / name).read_text()
    start = text.index(signature)
    body = text.index('{', start)
    depth = 1
    end = body + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end] + '\n'


stub = r'''
#include <algorithm>
#include <cassert>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <string>
#include <vector>
constexpr unsigned kWin3DActive=1,kWin3DVisible=2,kWin3DPickable=8;
constexpr unsigned long G_NnPaletteArgb_679bb0=0xffaabbcc,G_NnPaletteArgb_679ba4=0xffffff00;
struct FWin3DMouseEvent {int Field0,Field1;};
struct WinControl;
struct Win3D {
    Win3D *Parent=nullptr,*ChildHead=nullptr,*NextSibling=nullptr;
    Win3D* CaptureNext=nullptr;
    float Position[3]={},Offset[3]={},HalfExtents[3]={},Orientation[9]={1,0,0,0,1,0,0,0,1};
    unsigned char Flags=11;
    virtual ~Win3D();
    virtual WinControl* AsWinControl(){return nullptr;}
    virtual bool Create(Win3D*,void*){return true;}
    virtual void Draw(){}
    virtual bool MouseEvent(FWin3DMouseEvent const*){return false;}
    virtual bool KeyEvent(unsigned,unsigned char*){return false;}
    virtual bool Slot18(int){return false;}
    virtual intptr_t SetProperty(int,uintptr_t,uintptr_t){return 0;}
    virtual void SetPosition(float const* p){memcpy(Position,p,sizeof(Position));}
    virtual bool HitTest(float const*){return false;}
    virtual int GetHitPriority(){return 0;}
    bool IsDescendantOf(Win3D* p){return Parent&&(Parent==p||Parent->IsDescendantOf(p));}
    Win3D* GetParent(){return Parent;}
};
struct FWin3DListNode {Win3D* Payload;FWin3DListNode* Next;};
struct {FWin3DListNode* Head=nullptr;} G_Registry;
Win3D* G_CaptureHead=nullptr;
void Win3DPushCapture(Win3D*);
void Win3DRemoveCapture(Win3D*);
bool Win3DAnyCaptured();
bool capturesEmpty(){return G_CaptureHead==nullptr;}
Win3D::~Win3D(){
    Win3DRemoveCapture(this);
    while(ChildHead)delete ChildHead;
    if(Parent){auto** at=&Parent->ChildHead;while(*at&&*at!=this)at=&(*at)->NextSibling;if(*at)*at=NextSibling;}
    auto** at=&G_Registry.Head;while(*at&&(*at)->Payload!=this)at=&(*at)->Next;
    if(*at){auto* node=*at;*at=node->Next;delete node;}
}
void Win3DReparent(Win3D* c,Win3D* p){c->Parent=p;c->NextSibling=p->ChildHead;p->ChildHead=c;}
void Win3DRegister(Win3D* p){auto** at=&G_Registry.Head;while(*at)at=&(*at)->Next;*at=new FWin3DListNode{p,nullptr};}
class WireButtonControl;class NnTextControl;
struct WinControl:Win3D {
    bool bCaptured=false;
    float AttachPosition[3]={};
    WinControl* AsWinControl()override{return this;}
    intptr_t SetProperty(int msg,uintptr_t a,uintptr_t)override{if(msg==1)Flags=static_cast<unsigned char>(a==1?(Flags&~3u):(Flags|3u));return 1;}
    void SetPosition(float const* p)override{memcpy(Position,p,sizeof(Position));for(auto* c=ChildHead;c;c=c->NextSibling)c->SetPosition(Position);}
    void AddAttachOffset(float const* delta){for(int i=0;i<3;++i)AttachPosition[i]+=delta[i];}
    void SetOffset(float,float,float);
    void CaptureMouse(){if(!bCaptured){bCaptured=true;Win3DPushCapture(this);}}
    void ReleaseMouse(){bCaptured=false;Win3DRemoveCapture(this);}
    bool HitTest(float const* ray)override {
        float const z=Position[2]+Offset[2];if(z>=0||ray[2]>=0)return false;
        return std::abs(ray[0]*z/ray[2]-Position[0]-Offset[0])<=HalfExtents[0]&&
               std::abs(ray[1]*z/ray[2]-Position[1]-Offset[1])<=HalfExtents[1];
    }
    template<class... T>WinControl* CreateWireButtonControl(char const*,char const*,float const*,float const*,T...);
    template<class... T>WinControl* CreateTextControl(char const*,char const*,float const*,T...);
};
// Native meshless wire/text controls apply the parent's attachment offset;
// the base WinControl deliberately does not. Preferences moves by SetOffset.
struct AttachedControl:WinControl {
    void SetPosition(float const* p)override {
        float placed[3];for(int i=0;i<3;++i)placed[i]=p[i]+AttachPosition[i];
        WinControl::SetPosition(placed);
    }
};
class WireButtonControl:public AttachedControl {
public:
    unsigned char ButtonState=4,WireState=0;
    int SoundSlot=0,CommandId=0;std::string SoundName;
    bool MouseEvent(FWin3DMouseEvent const*)override;
    void Activate();
};
class NnTextControl:public AttachedControl {
public:
    float width=0;std::wstring text;unsigned long TextColour=0;
    void SetText(wchar_t const* p){text=p;}void SetWidth(float w){width=w;}
};
template<class... T>WinControl* WinControl::CreateWireButtonControl(char const*,char const*,float const* at,float const* half,T...){
    auto* c=new WireButtonControl;Win3DReparent(c,this);Win3DRegister(c);SetPosition(Position);
    memcpy(c->Offset,at,sizeof(c->Offset));memcpy(c->HalfExtents,half,sizeof(c->HalfExtents));return c;
}
template<class... T>WinControl* WinControl::CreateTextControl(char const*,char const*,float const* at,T...){
    auto* c=new NnTextControl;Win3DReparent(c,this);Win3DRegister(c);SetPosition(Position);memcpy(c->Offset,at,sizeof(c->Offset));return c;
}
constexpr double kOne=1.;
struct FVector {float X,Y,Z;};
struct FMatrix {float values[9];};
struct FSpaceCamera {float World[9]={1,0,0,0,1,0,0,0,1};} camera;
int cursorX=0,cursorY=0;
FSpaceCamera* Win3DGetCamera(){return &camera;}
void GetClientSoftwareCursor(int* x,int* y,void*){*x=cursorX;*y=cursorY;}
void Win3DScreenToNearPlane(FSpaceCamera*,FVector& out,float x,float y){out={x*.001f,y*.001f,-1};}
struct Math {void TransformMatrix(FVector& out,FMatrix const&,FVector const& in){out=in;}} math;
Math* WireMathEngine(){return &math;}
void NnUiPulseReset(){}void PlayOrRewindUiSoundSlot(unsigned){}
struct ID_String {unsigned Id;};
unsigned CreateID(char const*){return 0;}
void* LookupClientSoundArch(ID_String*){return nullptr;}
void PlayClientSoundArchIfIdle(void*,void*,void*){}void HudPostCommand(unsigned,int){assert(false);}
intptr_t TellParent(WinControl*,int);
enum {kWin3DBlend,kWin3DBlendSrcAlpha,kWin3DBlendInvSrcAlpha,kWin3DQuads,kWin3DTriangles};
std::vector<float> drawnY;
void Win3DFlushBeforeOverlayDraw(){}void Win3DBeginDraw(){}
void Win3DBindModelview(void*,float const* transform){assert(transform[11]==-1);}
void Win3DEnable(int){}void Win3DSetBlendFunc(int,int){}void Win3DBegin(int){}
void Win3DVertex3f(float,float y,float){drawnY.push_back(y);}
void Win3DEnd(){}void Win3DColor4ub(unsigned char,unsigned char,unsigned char,unsigned char){}
void Win3DColor4ubv(unsigned char const*){}void Win3DImmedBatchFlushAll(){}void UiOverlayPrepPipeline(){}
struct Owner:WinControl {
    unsigned changes=0;uintptr_t selected=999;Win3D* source=nullptr;
    WireButtonControl* field=nullptr;
    class NnDropdownPopup* popup=nullptr;
    intptr_t SetProperty(int,uintptr_t,uintptr_t)override;
};
'''
native = ''.join(function('win3d.cpp', signature) for signature in (
    'void Win3DPushCapture(', 'void Win3DRemoveCapture(', 'bool Win3DAnyCaptured(',
    'Win3D* Win3DPick(', 'Win3D* Win3DPickWithin('))
native += function('wincontrol_base.cpp', 'void WinControl::SetOffset(')
native += function('wire_controls.cpp', 'intptr_t TellParent(')
native += function('wire_controls.cpp', 'bool WireButtonControl::MouseEvent(')
native += function('wire_controls.cpp', 'void WireButtonControl::Activate(')
checks = r'''
intptr_t Owner::SetProperty(int msg,uintptr_t a,uintptr_t b){
    if(msg==0x26&&reinterpret_cast<Win3D*>(a)==field){
        popup->Open(.18f,.12f,.23f,{L"Standard",L"Avoid obstacles"},int(selected==999?0:selected));return 1;
    }
    if(msg==0x3e){++changes;source=reinterpret_cast<Win3D*>(a);selected=b;return 1;}
    return WinControl::SetProperty(msg,a,b);
}
// Capture-first dispatch, matching the Win3D mouse-button route. Picking and
// press/release/activation use the production implementations above.
bool mouse(float x,float y,int state){
    cursorX=int(std::round(x*1000));cursorY=int(std::round(y*1000));
    float const ray[]={cursorX*.001f,cursorY*.001f,-1};FWin3DMouseEvent event{-1,state};
    for(auto* capture=G_CaptureHead;capture;){
        auto* next=capture->CaptureNext;auto* hit=Win3DPickWithin(capture,ray);
        if(hit&&hit->MouseEvent(&event))return true;
        if(hit!=capture&&capture->MouseEvent(&event))return true;
        capture=next;
    }
    auto* hit=Win3DPick(ray);return hit&&hit->MouseEvent(&event);
}
WireButtonControl* item(NnDropdownPopup* p,int index){
    std::vector<WireButtonControl*> buttons;
    for(auto* c=p->ChildHead;c;c=c->NextSibling)if(auto* b=dynamic_cast<WireButtonControl*>(c))
        if(b->Flags&kWin3DVisible)buttons.push_back(b);
    std::sort(buttons.begin(),buttons.end(),[](auto* a,auto* b){return a->Offset[1]>b->Offset[1];});
    assert(index<int(buttons.size()));return buttons[index];
}
void key(NnDropdownPopup* p,unsigned k){unsigned char down=2;assert(p->KeyEvent(k,&down));}
int main(){
    // Actual preferences construction: children are created at z=0, then the
    // whole window is moved to z=-1 through the parent's OFFSET, not Position.
    Owner owner;auto* p=CreateNnDropdownPopup(&owner);assert(p&&!p->IsOpen()&&capturesEmpty());
    owner.SetOffset(0,0,-1);
    std::vector<std::wstring> choices={L"No",L"Any contact",L"Enemy"};
    assert(!p->Open(.18f,.12f,.23f,{},0)&&capturesEmpty());
    std::vector<std::wstring> longList;
    for(int i=0;i<24;++i)longList.push_back(std::to_wstring(i));
    assert(p->Open(.18f,.12f,.23f,longList,0));
    key(p,0x23);key(p,0x0d);assert(owner.selected==23);
    p->Open(.18f,.12f,.23f,longList,23);
    p->SetProperty(0x26,reinterpret_cast<uintptr_t>(item(p,0)),0);assert(owner.selected==16);
    p->Open(.18f,.12f,.23f,longList,0);
    for(int i=0;i<40;++i)p->Slot18(-120);
    p->SetProperty(0x26,reinterpret_cast<uintptr_t>(item(p,7)),0);assert(owner.selected==23);
    p->Open(.18f,.12f,.23f,longList,23);
    for(int i=0;i<40;++i)p->Slot18(120);
    key(p,0x0d);assert(owner.selected==0);
    p->Open(.18f,.12f,.23f,longList,0);
    key(p,0x22);key(p,0x22);key(p,0x21);key(p,0x0d);assert(owner.selected==8);
    owner.changes=0;
    assert(p->Open(.18f,.12f,.23f,choices,2));
    assert(p->IsOpen()&&p->bCaptured&&G_CaptureHead==p&&owner.changes==0);
    drawnY.clear();p->Draw();assert(!drawnY.empty()&&drawnY.front()<.12f);
    auto* first=item(p,0);assert(first->Offset[1]<.12f);
    // Native hover notification, then Enter: no cycling through saved values.
    p->SetProperty(0x2c,reinterpret_cast<uintptr_t>(first),0);
    key(p,0x0d);assert(owner.changes==1&&owner.selected==0&&owner.source==p&&capturesEmpty());
    assert(p->Open(.18f,.05f,.23f,choices,0));key(p,0x28);key(p,0x0d);
    assert(owner.changes==2&&owner.selected==1);
    p->Open(.18f,.05f,.23f,choices,1);key(p,0x23);key(p,0x1b);
    assert(owner.changes==2&&!p->IsOpen()&&capturesEmpty());
    p->Open(.18f,.05f,.23f,choices,1);p->Slot18(-120);key(p,0x20);
    assert(owner.changes==3&&owner.selected==2);
    p->Open(.18f,.05f,.23f,choices,1);key(p,0x24);key(p,0x26);key(p,0x0d);
    assert(owner.changes==4&&owner.selected==0);
    p->Open(.18f,.05f,.23f,choices,1);auto* last=item(p,2);
    p->SetProperty(0x26,reinterpret_cast<uintptr_t>(last),0);
    assert(owner.changes==5&&owner.selected==2&&!p->IsOpen());
    // The outside click retains capture until release, preventing click-through.
    p->Open(.18f,.05f,.23f,choices,1);
    FWin3DMouseEvent down{-1,2},up{-1,1};
    assert(p->MouseEvent(&down)&&p->IsOpen()&&G_CaptureHead==p);
    assert(p->MouseEvent(&up)&&!p->IsOpen()&&capturesEmpty()&&owner.changes==5);
    // Bottom row opens upwards; all options stay inside the preferences panel.
    p->Open(.18f,-.23f,.23f,choices,2);
    drawnY.clear();p->Draw();assert(*std::min_element(drawnY.begin(),drawnY.end())>=-.265f);
    assert(item(p,2)->Offset[1]>-.23f);
    auto* held=item(p,0);held->ButtonState|=1;Win3DPushCapture(held);
    p->SetProperty(1,1,0);assert(capturesEmpty()&&!(held->ButtonState&1)&&!p->IsOpen());
    // Ignore stale item notifications after dismissal.
    p->SetProperty(0x26,reinterpret_cast<uintptr_t>(held),0);assert(owner.changes==5);
    p->Open(.18f,.05f,.23f,choices,0);delete p;assert(capturesEmpty()&&!owner.ChildHead);
    // Native WinControl::Destroy deletes children BEFORE the derived destructor.
    p=CreateNnDropdownPopup(&owner);p->Open(.18f,.05f,.23f,choices,0);
    while(p->ChildHead)delete p->ChildHead;
    delete p;assert(capturesEmpty()&&!owner.ChildHead);
    // Native click opens the list, then a separate press/release selects a row.
    // Also create after the owner's offset was already set (reopening settings).
    float const at[]={.295f,.1065f,0},half[]={.115f,.0145f,0};
    owner.field=static_cast<WireButtonControl*>(owner.CreateWireButtonControl("field","",at,half));
    owner.field->AttachPosition[2]=-1;owner.SetPosition(owner.Position);
    owner.popup=p=CreateNnDropdownPopup(&owner);
    assert(mouse(.295f,.1065f,2)&&!p->IsOpen());
    assert(mouse(.295f,.1065f,1)&&p->IsOpen()&&G_CaptureHead==p);
    p->Draw();
    auto* second=item(p,1);assert(second->Position[2]==-1);
    float const y=second->Offset[1];
    assert(mouse(.295f,y,2)&&p->IsOpen()&&G_CaptureHead==second);
    assert(mouse(.295f,y,1)&&!p->IsOpen()&&capturesEmpty());
    assert(owner.changes==6&&owner.selected==1);
    // Dragging off the opening field cancels, and a later ordinary click works.
    assert(mouse(.295f,.1065f,2));assert(mouse(0,.3f,1)&&!p->IsOpen());
    assert(mouse(.295f,.1065f,2));assert(mouse(.295f,.1065f,1)&&p->IsOpen());
    assert(mouse(0,.3f,2)&&p->IsOpen());assert(mouse(0,.3f,1)&&!p->IsOpen());
    assert(owner.changes==6&&capturesEmpty());
    puts("PASS: native wire-button press/release, picking and capture; preferences offset and visible popup depth; selection, drag-out, keyboard/wheel, dismissal, upward layout and teardown.");
}
'''
(OUT / 'check.cpp').write_text(stub + native + source('nn_dropdown.h') + source('nn_dropdown.cpp') + checks)
vc = Path('C:/Program Files/Microsoft Visual Studio/18/Community/VC/Tools/MSVC/14.51.36231')
sdk = Path('C:/Program Files (x86)/Windows Kits/10')
version = '10.0.26100.0'
env = dict(os.environ)
env['INCLUDE'] = ';'.join(map(str, [vc / 'include'] + [sdk / 'Include' / version / x for x in ('ucrt', 'shared', 'um')]))
env['LIB'] = ';'.join(map(str, [vc / 'lib/x86'] + [sdk / 'Lib' / version / x / 'x86' for x in ('ucrt', 'um')]))
subprocess.run([str(vc / 'bin/Hostx64/x86/cl.exe'), '/nologo', '/std:c++17', '/W4', '/WX',
                '/EHsc', '/MT', 'check.cpp', '/Fecheck.exe'], cwd=OUT, env=env, check=True)
subprocess.run([str(OUT / 'check.exe')], cwd=OUT, check=True)
